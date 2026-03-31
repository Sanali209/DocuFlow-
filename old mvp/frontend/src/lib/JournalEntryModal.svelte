<script>
    import { journalService, docService } from "./stores/services.js";

    let { isOpen, close, documentId, documentName, entry = null } = $props();
    let text = $state("");
    let type = $state("info");
    let author = $state("");
    let loading = $state(false);
    let attachments = $state([]);
    let isUploading = $state(false);

    $effect(() => {
        if (isOpen) {
            if (entry) {
                // Edit mode
                text = entry.text || "";
                type = entry.type || "info";
                author = entry.author || "";
                attachments = entry.attachments || [];
            } else {
                // Create mode
                author = localStorage.getItem("journal_author") || "";
                text = "";
                type = "info";
                attachments = [];
            }
        }
    });

    async function handleFileSelect(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        isUploading = true;
        try {
            for (const file of files) {
                const result = await docService.uploadFile(file);
                attachments.push({
                    file_path: result.file_path,
                    filename: result.filename,
                    media_type: result.media_type,
                });
            }
        } catch (err) {
            console.error("Upload failed", err);
            alert("Failed to upload attachment");
        } finally {
            isUploading = false;
            e.target.value = "";
        }
    }

    function removeAttachment(index) {
        attachments.splice(index, 1);
    }

    async function handleSubmit(e) {
        e.preventDefault();
        loading = true;
        if (author) localStorage.setItem("journal_author", author);

        try {
            const journalData = {
                text,
                type,
                status: entry?.status || "pending",
                author,
                document_id: documentId,
                attachments,
            };

            if (entry) {
                // Update existing entry
                await journalService.updateEntry(entry.id, journalData);
            } else {
                // Create new entry
                await journalService.createEntry(journalData);
            }

            // Dispatch custom event to notify other components
            window.dispatchEvent(new CustomEvent("journal-entries-updated"));
            close();
        } catch (err) {
            console.error(err);
            alert(entry ? "Failed to update note" : "Failed to create note");
        } finally {
            loading = false;
        }
    }
</script>

{#if isOpen}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="modal-overlay" onclick={close}>
        <div class="modal-content" onclick={(e) => e.stopPropagation()}>
            <div class="modal-header">
                <h3>{entry ? "Edit Note" : `Add Note to ${documentName}`}</h3>
                <button class="close-btn" onclick={close}>&times;</button>
            </div>

            <form onsubmit={handleSubmit} class="modal-body">
                <div class="form-group">
                    <label for="author">Author</label>
                    <input
                        id="author"
                        type="text"
                        bind:value={author}
                        placeholder="Your Name"
                    />
                </div>

                <div class="form-group">
                    <label for="type">Type</label>
                    <select id="type" bind:value={type}>
                        <option value="info">Info</option>
                        <option value="warning">Warning</option>
                        <option value="error">Error</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="text">Message</label>
                    <textarea id="text" bind:value={text} required rows="4"
                    ></textarea>
                </div>

                <div class="form-group">
                    <label for="attachments">Attachments</label>
                    <div class="file-upload-wrapper">
                        <input
                            id="attachments"
                            type="file"
                            multiple
                            onchange={handleFileSelect}
                            disabled={isUploading}
                        />
                        {#if isUploading}
                            <p class="upload-status">Uploading...</p>
                        {/if}
                    </div>
                    {#if attachments.length > 0}
                        <div class="attachments-list">
                            {#each attachments as att, i}
                                <div class="attachment-item">
                                    <span class="attachment-name"
                                        >{att.filename}</span
                                    >
                                    <button
                                        type="button"
                                        class="remove-btn"
                                        onclick={() => removeAttachment(i)}
                                        >×</button
                                    >
                                </div>
                            {/each}
                        </div>
                    {/if}
                </div>

                <div class="actions">
                    <button type="button" class="btn-secondary" onclick={close}
                        >Cancel</button
                    >
                    <button
                        type="submit"
                        class="btn-primary"
                        disabled={loading}
                    >
                        {loading
                            ? "Saving..."
                            : entry
                              ? "Update Note"
                              : "Add Note"}
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<style>
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }
    .modal-content {
        background: white;
        border-radius: 12px;
        width: 100%;
        max-width: 500px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
    }
    .modal-header {
        padding: 1.25rem;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .modal-header h3 {
        margin: 0;
        font-size: 1.1rem;
        color: #1e293b;
    }
    .close-btn {
        background: none;
        border: none;
        font-size: 1.5rem;
        color: #64748b;
        cursor: pointer;
        padding: 0;
    }
    .modal-body {
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .form-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    label {
        font-size: 0.9rem;
        font-weight: 500;
        color: #475569;
    }
    input,
    select,
    textarea {
        padding: 0.75rem;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        font-family: inherit;
        font-size: 1rem;
    }
    .file-upload-wrapper {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    .upload-status {
        font-size: 0.85rem;
        color: #64748b;
        margin: 0;
    }
    .attachments-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .attachment-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem;
        background: #f8fafc;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
    }
    .attachment-name {
        font-size: 0.9rem;
        color: #475569;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .remove-btn {
        background: none;
        border: none;
        color: #ef4444;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
    }
    .remove-btn:hover {
        background: #fee2e2;
    }
    .actions {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        margin-top: 1rem;
    }
    button {
        padding: 0.6rem 1.2rem;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
        border: none;
    }
    .btn-primary {
        background: #3b82f6;
        color: white;
    }
    .btn-secondary {
        background: #f1f5f9;
        color: #475569;
    }
</style>
