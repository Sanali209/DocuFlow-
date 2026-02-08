<script>
    import { onMount } from "svelte";
    import { docService } from "./stores/services.js";
    import { uiState } from "./stores/appState.svelte.js";
    import TagInput from "./TagInput.svelte";
    import ImagePreviewModal from "./ImagePreviewModal.svelte";

    let { onDocumentCreated, onCancel, document = null } = $props();

    let name = $state("");
    let description = $state("");
    let type = $state("plan");
    let status = $state("in_progress");
    let registration_date = $state("");
    let content = $state("");
    let author = $state("");
    let done_date = $state("");
    let attachments = $state([]);
    let newAttachments = $state([]);
    let tags = $state([]);

    $effect(() => {
        if (document) {
            name = document.name || "";
            description = document.description || "";
            type = document.type || "plan";
            status = document.status || "in_progress";
            registration_date = document.registration_date || "";
            content = document.content || "";
            author = document.author || "";
            done_date = document.done_date || "";
            attachments = document.attachments || [];
            if (document.tags) {
                // handle tags mapping if needed, assuming tags is object list
                tags = document.tags.map((t) =>
                    typeof t === "string" ? t : t.name,
                );
            } else {
                tags = [];
            }
        } else {
            // Reset for new doc
            const savedAuthor =
                typeof localStorage !== "undefined"
                    ? localStorage.getItem("doc_author")
                    : "";
            if (savedAuthor) author = savedAuthor;
        }
    });

    let isUploading = $state(false);
    let isSaving = $state(false);
    let saveError = $state("");

    let previewAttachments = $state(null);

    onMount(() => {
        if (status === "unregistered") {
            status = "in_progress";
        }
        if (!document) {
            const savedAuthor = localStorage.getItem("doc_author");
            if (savedAuthor) author = savedAuthor;
        }
    });

    $effect(() => {
        if (status === "done" && !done_date) {
            done_date = new Date().toISOString().split("T")[0];
        }
    });

    async function handleAttachmentSelect(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        isUploading = true;
        try {
            for (const file of files) {
                const result = await docService.uploadFile(file);
                // result format: { file_path: "/uploads/...", filename: "...", media_type: "..." }
                // Need to match Attachment structure
                newAttachments.push({
                    file_path: result.file_path,
                    filename: result.filename,
                    media_type: result.media_type,
                });
            }
        } catch (e) {
            console.error("Upload failed", e);
            alert("Failed to upload attachment");
        } finally {
            isUploading = false;
            e.target.value = "";
        }
    }

    function openGallery() {
        // Combine existing and new for preview
        previewAttachments = [...attachments, ...newAttachments];
    }

    async function handleRemoveAttachment(index, isNew) {
        if (isNew) {
            newAttachments.splice(index, 1);
        } else {
            if (!confirm("Permanently delete this attachment?")) return;
            const att = attachments[index];
            try {
                await docService.deleteAttachment(att.id);
                attachments.splice(index, 1);
            } catch (e) {
                console.error("Failed to delete attachment", e);
                alert("Failed to delete attachment");
            }
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();

        isSaving = true;
        saveError = "";

        try {
            if (author) localStorage.setItem("doc_author", author);

            const docData = {
                name,
                description,
                type,
                status,
                registration_date: registration_date || undefined,
                content,
                author,
                done_date: done_date || undefined,
                attachments: newAttachments,
                tags,
            };

            if (document) {
                await docService.updateDocument(document.id, docData);
                uiState.addNotification("Document updated", "info");
            } else {
                await docService.createDocument(docData);
                uiState.addNotification("Document registered", "info");
            }

            if (!document) {
                name = "";
                description = "";
                type = "plan";
                status = "in_progress";
                registration_date = "";
                content = "";
                author = localStorage.getItem("doc_author") || "";
                done_date = "";
                newAttachments = [];
                tags = [];
            }

            onDocumentCreated();
        } catch (err) {
            console.error("Failed to save document:", err);
            saveError = "Failed to save document. Please try again.";
        } finally {
            isSaving = false;
        }
    }
</script>

<div class="form-container">
    <h3>{document ? "Edit Document" : "New Document"}</h3>
    <form onsubmit={handleSubmit}>
        <div class="form-section upload-section">
            <h4>Files & Scanning</h4>
            <div class="upload-buttons">
                <div class="upload-btn-wrapper">
                    <button type="button" class="btn-outline"
                        >📄 Add Attachments</button
                    >
                    <input
                        type="file"
                        multiple
                        onchange={handleAttachmentSelect}
                        title="Add Attachments (No Scan)"
                    />
                </div>

                {#if attachments.length > 0 || newAttachments.length > 0}
                    <button
                        type="button"
                        class="btn-outline"
                        onclick={openGallery}>📷 View Gallery</button
                    >
                {/if}
            </div>

            {#if isUploading}
                <p class="info-text">Uploading...</p>
            {/if}
            {#if saveError}
                <p class="error-text">{saveError}</p>
            {/if}

            {#if attachments.length > 0 || newAttachments.length > 0}
                <div class="attachments-list">
                    {#each attachments as att, i}
                        <div class="attachment-item">
                            <span class="file-name" title={att.filename}
                                >{att.filename}</span
                            >
                            <button
                                type="button"
                                class="remove-btn"
                                onclick={() => handleRemoveAttachment(i, false)}
                                >❌</button
                            >
                        </div>
                    {/each}
                    {#each newAttachments as att, i}
                        <div class="attachment-item new">
                            <span class="file-name" title={att.filename}
                                >(New) {att.filename}</span
                            >
                            <button
                                type="button"
                                class="remove-btn"
                                onclick={() => handleRemoveAttachment(i, true)}
                                >❌</button
                            >
                        </div>
                    {/each}
                </div>
            {/if}
        </div>

        <div class="form-group">
            <label for="name">Name</label>
            <input
                id="name"
                type="text"
                bind:value={name}
                required
                placeholder="e.g. Project Alpha Specs"
            />
        </div>

        <div class="form-group">
            <label for="description">Description</label>
            <textarea
                id="description"
                bind:value={description}
                rows="3"
                placeholder="Brief description of the document..."
            ></textarea>
        </div>

        <!-- Tasks Section -->
        {#if document?.tasks?.length > 0}
            <div class="form-section">
                <h4>Tasks ({document.tasks.length})</h4>
                <div class="task-list">
                    {#each document.tasks as task}
                        <details class="task-item">
                            <summary>
                                <span class="task-icon">⚙️</span>
                                <span class="task-name">{task.name}</span>
                                <span class="task-status-badge {task.status}"
                                    >{task.status}</span
                                >
                            </summary>
                            <div class="task-details">
                                <div class="task-meta">
                                    <div class="meta-item">
                                        <span class="label">Assignee:</span>
                                        <span
                                            >{task.assignee ||
                                                "Unassigned"}</span
                                        >
                                    </div>
                                    <div class="meta-item">
                                        <span class="label">Material:</span>
                                        <span
                                            >{task.material?.name ||
                                                "Unknown"}</span
                                        >
                                    </div>
                                    <div class="meta-item">
                                        <span class="label">GNC Path:</span>
                                        <span
                                            class="path"
                                            title={task.gnc_file_path}
                                            >{task.gnc_file_path || "N/A"}</span
                                        >
                                    </div>
                                </div>

                                <div class="linked-parts-section">
                                    <h5>
                                        Linked Parts ({task.parts?.length || 0})
                                    </h5>
                                    {#if task.parts?.length > 0}
                                        <ul class="parts-list">
                                            {#each task.parts as part}
                                                <li class="part-item-li">
                                                    <span class="part-name"
                                                        >{part.name}</span
                                                    >
                                                    <span class="part-reg"
                                                        >[{part.registration_number}]</span
                                                    >
                                                    {#if part.width || part.height}
                                                        <span class="part-dims"
                                                            >{Math.round(
                                                                part.width,
                                                            )} x {Math.round(
                                                                part.height,
                                                            )}</span
                                                        >
                                                    {/if}
                                                </li>
                                            {/each}
                                        </ul>
                                    {:else}
                                        <p class="no-parts">
                                            No linked parts found in GNC.
                                        </p>
                                    {/if}
                                </div>
                            </div>
                        </details>
                    {/each}
                </div>
            </div>
        {/if}

        <div class="form-group">
            <label for="tags">Tags</label>
            <TagInput bind:selectedTags={tags} />
        </div>

        <div class="form-group">
            <label for="content">Recognized Content (Markdown)</label>
            <textarea
                id="content"
                bind:value={content}
                rows="10"
                placeholder="Recognized document content will appear here..."
            ></textarea>
        </div>

        <div class="row">
            <div class="form-group half">
                <label for="type">Type</label>
                <select id="type" bind:value={type}>
                    <option value="plan">Plan</option>
                    <option value="mail">Mail</option>
                    <option value="order">Order</option>
                    <option value="other">Other</option>
                </select>
            </div>

            <div class="form-group half">
                <label for="status">Status</label>
                <select id="status" bind:value={status}>
                    <option value="in_progress">In Progress</option>
                    <option value="done">Done</option>
                </select>
            </div>
        </div>

        {#if document && type === "order"}
            <div class="form-group">
                <button
                    type="button"
                    class="btn-gnc"
                    onclick={() =>
                        (window.location.hash = `#/gnc?orderId=${document.id}`)}
                >
                    ✂️ Edit in GNC
                </button>
            </div>
        {/if}

        <div class="row">
            <div class="form-group half">
                <label for="date">Registration Date</label>
                <input id="date" type="date" bind:value={registration_date} />
            </div>
            <div class="form-group half">
                <label for="done_date">Done Date</label>
                <input
                    id="done_date"
                    type="date"
                    bind:value={done_date}
                    disabled={status !== "done"}
                />
            </div>
        </div>

        <div class="form-group">
            <label for="author">Author</label>
            <input
                id="author"
                type="text"
                bind:value={author}
                placeholder="Your Name"
            />
        </div>

        <div class="actions">
            <button type="button" class="btn-secondary" onclick={onCancel}
                >Cancel</button
            >
            <button
                type="submit"
                class="btn-primary"
                disabled={isSaving || isUploading}
            >
                {isSaving
                    ? "Saving..."
                    : document
                      ? "Save Changes"
                      : "Register Document"}
            </button>
        </div>
    </form>

    <ImagePreviewModal
        isOpen={!!previewAttachments}
        close={() => (previewAttachments = null)}
        attachments={previewAttachments || []}
    />
</div>

<style>
    .form-container h3 {
        margin-top: 0;
        margin-bottom: var(--spacing-lg);
        color: var(--color-text);
        font-family: var(--font-heading);
    }
    .form-group {
        margin-bottom: var(--spacing-md);
    }
    .row {
        display: flex;
        gap: var(--spacing-md);
    }
    .half {
        flex: 1;
    }
    label {
        display: block;
        margin-bottom: var(--spacing-xs);
        font-weight: 600;
        color: var(--color-text);
        font-size: 0.9rem;
    }
    input,
    select,
    textarea {
        width: 100%;
        padding: var(--spacing-sm) var(--spacing-md);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
        box-sizing: border-box;
        font-size: 1rem;
        transition:
            border-color var(--transition-fast),
            box-shadow var(--transition-fast);
        font-family: inherit;
        background-color: var(--color-surface);
        color: var(--color-text);
    }
    input:focus,
    select:focus,
    textarea:focus {
        border-color: var(--color-primary);
        outline: none;
        box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2);
    }
    .actions {
        display: flex;
        justify-content: flex-end;
        gap: var(--spacing-md);
        margin-top: var(--spacing-xl);
    }
    button {
        padding: var(--spacing-sm) var(--spacing-lg);
        border-radius: var(--radius-md);
        cursor: pointer;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
        transition: background-color var(--transition-fast);
    }
    .btn-primary {
        background-color: var(--color-primary);
        color: white;
    }
    .btn-primary:hover:not(:disabled) {
        background-color: #6d28d9;
    }
    .btn-primary:disabled {
        background-color: #ddd;
        cursor: not-allowed;
    }
    .btn-secondary {
        background-color: white;
        border: 1px solid var(--color-border);
        color: var(--color-text);
    }
    .btn-secondary:hover {
        background-color: var(--color-background);
        border-color: var(--color-text);
    }
    .btn-outline {
        border: 2px dashed var(--color-border);
        background: transparent;
        color: var(--color-text);
        width: 100%;
        padding: var(--spacing-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    .btn-outline:hover {
        border-color: var(--color-primary);
        color: var(--color-primary);
        background-color: var(--color-background);
    }
    .upload-btn-wrapper {
        position: relative;
        margin-bottom: var(--spacing-sm);
    }
    .upload-btn-wrapper input[type="file"] {
        position: absolute;
        left: 0;
        top: 0;
        opacity: 0;
        width: 100%;
        height: 100%;
        cursor: pointer;
    }
    .attachments-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .attachment-item {
        display: flex;
        align-items: center;
        background: var(--color-background);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
        border: 1px solid var(--color-border);
    }
    .attachment-item.new {
        background: #eef2ff;
        border-color: #c7d2fe;
    }
    .attachment-item .file-name {
        max-width: 150px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-right: 0.5rem;
    }
    .remove-btn {
        background: none;
        border: none;
        padding: 0;
        color: #999;
        font-size: 1rem;
        cursor: pointer;
        line-height: 1;
    }
    .remove-btn:hover {
        color: #ef4444;
    }
    .info-text {
        color: #666;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    .error-text {
        color: #ef4444;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }

    /* Task Styles */
    .form-section {
        margin-top: 2rem;
        border-top: 1px solid var(--color-border);
        padding-top: 1rem;
    }

    .form-section h4 {
        margin-bottom: 1rem;
        color: var(--color-text);
        font-family: var(--font-heading);
    }

    .task-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .task-item {
        border: 1px solid var(--color-border);
        border-radius: 6px;
        overflow: hidden;
    }

    .task-item summary {
        padding: 0.75rem;
        background: var(--color-background);
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 500;
        list-style: none; /* Hide default triangle in some browsers */
    }

    .task-item summary::-webkit-details-marker {
        display: none;
    }

    .task-name {
        flex: 1;
        color: var(--color-text);
    }

    .task-status-badge {
        font-size: 0.75rem;
        padding: 0.15rem 0.5rem;
        border-radius: 99px;
        text-transform: uppercase;
        font-weight: 700;
    }

    .task-status-badge.planned {
        background: #e0f2fe;
        color: #0369a1;
    }
    .task-status-badge.in_progress {
        background: #fef3c7;
        color: #b45309;
    }
    .task-status-badge.completed {
        background: #dcfce7;
        color: #15803d;
    }

    .task-details {
        padding: 1rem;
        border-top: 1px solid var(--color-border);
        background: var(--color-surface);
    }

    .task-meta {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }

    .meta-item {
        display: flex;
        flex-direction: column;
    }

    .meta-item .label {
        font-size: 0.75rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .meta-item .path {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: #666;
        font-family: monospace;
    }

    .linked-parts-section h5 {
        margin: 0 0 0.5rem 0;
        font-size: 0.9rem;
        color: #444;
    }

    .parts-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .part-item-li {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0;
        border-bottom: 1px solid #f0f0f0;
        font-size: 0.9rem;
    }

    .part-name {
        font-weight: 600;
        color: var(--color-text);
    }

    .part-reg {
        color: #666;
        font-family: monospace;
    }

    .part-dims {
        margin-left: auto;
        font-size: 0.8rem;
        background: #eee;
        padding: 0.1rem 0.4rem;
        border-radius: 4px;
        color: #555;
    }

    .no-parts {
        color: #999;
        font-style: italic;
        font-size: 0.9rem;
    }
    .btn-gnc {
        background-color: #059669;
        color: white;
        width: 100%;
        margin-top: 0.5rem;
        padding: 0.75rem;
    }
    .btn-gnc:hover {
        background-color: #047857;
    }
</style>
