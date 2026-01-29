<script>
    import { onMount } from "svelte";
    import JournalEntryModal from "./JournalEntryModal.svelte";
    import {
        fetchJournalEntries,
        createJournalEntry,
        updateJournalEntry,
        deleteJournalEntry,
        uploadFile
    } from "./api.js";

    let entries = $state([]);
    let loading = $state(false);
    let editingEntry = $state(null);

    // Filters
    let filterType = $state("");
    let filterStatus = $state("");

    // New Entry Form
    let showForm = $state(false);
    let newEntryText = $state("");
    let newEntryType = $state("info");
    let newEntryAuthor = $state("");
    let newEntryAttachments = $state([]);

    async function loadEntries() {
        loading = true;
        try {
            entries = await fetchJournalEntries(filterType, filterStatus);
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    }

    onMount(() => {
        newEntryAuthor = localStorage.getItem("journal_author") || "";
        loadEntries();
        
        // Listen for journal entries created/updated from other components
        const handleJournalUpdated = () => {
            loadEntries();
        };
        window.addEventListener('journal-entries-updated', handleJournalUpdated);
        
        return () => {
            window.removeEventListener('journal-entries-updated', handleJournalUpdated);
        };
    });

    async function handleFileSelect(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        for (const file of files) {
            try {
                const result = await uploadFile(file);
                newEntryAttachments.push(result);
            } catch (err) {
                console.error("Upload failed", err);
                alert("Upload failed for " + file.name);
            }
        }
        e.target.value = '';
    }

    async function handleAdd() {
        if (!newEntryText && newEntryAttachments.length === 0) return;

        // Save author
        if (newEntryAuthor) {
            localStorage.setItem("journal_author", newEntryAuthor);
        }

        try {
            await createJournalEntry({
                text: newEntryText,
                type: newEntryType,
                status: "pending", // Default
                author: newEntryAuthor,
                attachments: newEntryAttachments
            });
            newEntryText = "";
            newEntryAttachments = [];
            showForm = false;
            loadEntries();
        } catch (e) {
            console.error("Failed to add entry", e);
        }
    }

    async function toggleStatus(entry) {
        const newStatus = entry.status === "pending" ? "done" : "pending";
        try {
            await updateJournalEntry(entry.id, { status: newStatus });
            loadEntries();
        } catch (e) {
            console.error(e);
        }
    }

    async function remove(id) {
        if (!confirm("Are you sure?")) return;
        try {
            await deleteJournalEntry(id);
            loadEntries();
        } catch (e) {
            console.error(e);
        }
    }

    function openEditModal(entry) {
        editingEntry = entry;
    }

    function closeEditModal() {
        editingEntry = null;
        loadEntries();
    }

    // React to filter changes
    $effect(() => {
        loadEntries();
    });
</script>

<div class="journal-container">
    <div class="toolbar">
        <div class="filters">
            <select bind:value={filterType} onchange={loadEntries}>
                <option value="">All Types</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
            </select>
            <select bind:value={filterStatus} onchange={loadEntries}>
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="done">Done</option>
            </select>
        </div>
        <button class="add-btn" onclick={() => (showForm = !showForm)}>
            {showForm ? "Cancel" : "+ New Entry"}
        </button>
    </div>

    {#if showForm}
        <div class="entry-form">
            <input
                type="text"
                placeholder="Author"
                bind:value={newEntryAuthor}
                class="author-input"
            />
            <select bind:value={newEntryType}>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
            </select>
            <textarea placeholder="Message..." bind:value={newEntryText}
            ></textarea>

            <div class="file-input-group">
                <input type="file" multiple onchange={handleFileSelect} />
                 {#if newEntryAttachments.length > 0}
                    <div class="attachments-preview">
                        {#each newEntryAttachments as att}
                            <span class="att-badge">{att.filename}</span>
                        {/each}
                    </div>
                {/if}
            </div>

            <button onclick={handleAdd}>Save</button>
        </div>
    {/if}

    <div class="entries-list">
        {#if loading}
            <p>Loading...</p>
        {:else if entries.length === 0}
            <p class="empty">No entries found.</p>
        {:else}
            {#each entries as entry}
                <div class="entry-card {entry.type} {entry.status}">
                    <div class="entry-header">
                        <span class="badge {entry.type}">{entry.type}</span>
                        <span class="author">{entry.author || "Unknown"}</span>
                        <span class="date">{entry.created_at}</span>

                        {#if entry.document_id}
                            <span class="doc-ref">Ref: Doc #{entry.document_id}</span>
                        {/if}

                        <div class="actions">
                            <button
                                class="edit-btn"
                                onclick={() => openEditModal(entry)}
                            >
                                ✏️ Edit
                            </button>
                            <button
                                class="status-btn"
                                onclick={() => toggleStatus(entry)}
                            >
                                {entry.status === "pending"
                                    ? "☑ Mark Done"
                                    : "↩ Reopen"}
                            </button>
                            <button
                                class="delete-btn"
                                onclick={() => remove(entry.id)}>🗑</button
                            >
                        </div>
                    </div>
                    <p class="text">{entry.text}</p>

                    {#if entry.attachments && entry.attachments.length > 0}
                        <div class="entry-attachments">
                             {#each entry.attachments as att}
                                  <div class="attachment-thumb">
                                        {#if att.media_type && att.media_type.startsWith('image/')}
                                            <a href={att.file_path} target="_blank">
                                                <img src={att.file_path} alt={att.filename} />
                                            </a>
                                        {:else}
                                            <a href={att.file_path} target="_blank">📄 {att.filename}</a>
                                        {/if}
                                  </div>
                             {/each}
                        </div>
                    {/if}
                </div>
            {/each}
        {/if}
    </div>
    
    <JournalEntryModal
        isOpen={!!editingEntry}
        close={closeEditModal}
        documentId={editingEntry?.document_id}
        documentName="Journal Entry"
        entry={editingEntry}
    />
</div>

<style>
    .journal-container {
        padding: 1rem;
        max-width: 800px;
        margin: 0 auto;
    }
    .toolbar {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .filters {
        display: flex;
        gap: 1rem;
    }
    select,
    input,
    textarea {
        padding: 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        font-family: inherit;
    }
    .add-btn {
        background: #0f172a;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        border: none;
        cursor: pointer;
    }
    .entry-form {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .file-input-group {
        border: 1px dashed #cbd5e1;
        padding: 0.5rem;
        border-radius: 6px;
    }
    .attachments-preview {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 0.5rem;
    }
    .att-badge {
        background: #e2e8f0;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .entries-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .entry-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 5px solid #ccc;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        transition: transform 0.1s;
    }
    .entry-card:hover {
        transform: translateY(-2px);
    }
    .entry-card.info {
        border-left-color: #3b82f6;
    }
    .entry-card.warning {
        border-left-color: #f59e0b;
    }
    .entry-card.error {
        border-left-color: #ef4444;
    }
    .entry-card.done {
        opacity: 0.6;
    }

    .entry-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.875rem;
        color: #64748b;
        flex-wrap: wrap;
    }
    .badge {
        text-transform: uppercase;
        font-size: 0.7rem;
        font-weight: bold;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        color: white;
    }
    .badge.info {
        background: #3b82f6;
    }
    .badge.warning {
        background: #f59e0b;
    }
    .badge.error {
        background: #ef4444;
    }

    .author {
        font-weight: 600;
        color: #1e293b;
    }

    .doc-ref {
        background: #f1f5f9;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        color: #475569;
    }

    .actions {
        margin-left: auto;
        display: flex;
        gap: 0.5rem;
    }

    .edit-btn,
    .status-btn,
    .delete-btn {
        background: none;
        border: 1px solid #e2e8f0;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.8rem;
    }
    .edit-btn:hover {
        background: #eff6ff;
        border-color: #bfdbfe;
    }
    .status-btn:hover {
        background: #f1f5f9;
    }
    .delete-btn {
        color: #ef4444;
        border-color: #fee2e2;
    }
    .delete-btn:hover {
        background: #fee2e2;
    }

    .text {
        color: #334155;
        line-height: 1.5;
        white-space: pre-wrap;
    }

    .entry-attachments {
        margin-top: 1rem;
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .attachment-thumb img {
        height: 60px;
        width: auto;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
    }
    .attachment-thumb a {
        color: #3b82f6;
        text-decoration: none;
        font-size: 0.9rem;
    }
</style>
