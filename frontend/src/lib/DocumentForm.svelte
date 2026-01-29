<script>
    import { onMount } from 'svelte';
    import { createDocument, scanDocument, updateDocument, deleteAttachment, uploadFile } from './api.js';
    import TagInput from './TagInput.svelte';
    import ImagePreviewModal from './ImagePreviewModal.svelte';

    let { onDocumentCreated, onCancel, document = null } = $props();

    let name = $state(document?.name || '');
    let description = $state(document?.description || '');
    let type = $state(document?.type || 'plan');
    let status = $state(document?.status || 'in_progress');
    let registration_date = $state(document?.registration_date || '');
    let content = $state(document?.content || '');
    let author = $state(document?.author || '');
    let done_date = $state(document?.done_date || '');

    let attachments = $state(document?.attachments || []);
    let newAttachments = $state([]);
    let tags = $state(document?.tags?.map(t => t.name) || []);

    let isScanning = $state(false);
    let isUploading = $state(false);
    let scanError = $state('');
    let scanStatus = $state('');

    let previewAttachments = $state(null);

    onMount(() => {
        if (!document) {
            const savedAuthor = localStorage.getItem('doc_author');
            if (savedAuthor) author = savedAuthor;
        }
    });

    $effect(() => {
        if (status === 'done' && !done_date) {
            done_date = new Date().toISOString().split('T')[0];
        }
    });

    async function handleScanSelect(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        isScanning = true;
        scanError = '';

        try {
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                scanStatus = `Scanning file ${i + 1} of ${files.length}...`;

                const result = await scanDocument(file);

                if (result.name && !name) {
                    name = result.name;
                }

                const newContent = result.content || '';
                if (content && newContent) {
                    content += '\n\n---\n\n' + newContent;
                } else if (newContent) {
                    content = newContent;
                }

                if (result.attachment) {
                    newAttachments.push(result.attachment);
                }
            }
        } catch (err) {
            scanError = 'Failed to scan one or more documents. Please try again or enter details manually.';
            console.error(err);
        } finally {
            isScanning = false;
            scanStatus = '';
            e.target.value = '';
        }
    }

    async function handleAttachmentSelect(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        isUploading = true;
        try {
             for (const file of files) {
                const result = await uploadFile(file);
                // result format: { file_path: "/uploads/...", filename: "...", media_type: "..." }
                // Need to match Attachment structure
                newAttachments.push({
                    file_path: result.file_path,
                    filename: result.filename,
                    media_type: result.media_type
                });
            }
        } catch(e) {
            console.error("Upload failed", e);
            alert("Failed to upload attachment");
        } finally {
            isUploading = false;
            e.target.value = '';
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
            if (!confirm('Permanently delete this attachment?')) return;
            const att = attachments[index];
            try {
                await deleteAttachment(att.id);
                attachments.splice(index, 1);
            } catch (e) {
                console.error("Failed to delete attachment", e);
                alert("Failed to delete attachment");
            }
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();

        if (author) localStorage.setItem('doc_author', author);

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
            tags
        };

        if (document) {
            await updateDocument(document.id, docData);
        } else {
            await createDocument(docData);
        }

        if (!document) {
            name = '';
            description = '';
            type = 'plan';
            status = 'in_progress';
            registration_date = '';
            content = '';
            author = localStorage.getItem('doc_author') || '';
            done_date = '';
            newAttachments = [];
            tags = [];
        }

        onDocumentCreated();
    }
</script>

<div class="form-container">
    <h3>{document ? 'Edit Document' : 'New Document'}</h3>
    <form onsubmit={handleSubmit}>
        <div class="form-section upload-section">
            <h4>Files & Scanning</h4>
            <div class="upload-buttons">
                <div class="upload-btn-wrapper">
                    <button type="button" class="btn-outline">📄 Add Attachments</button>
                    <input type="file" multiple onchange={handleAttachmentSelect} title="Add Attachments (No Scan)" />
                </div>
                 <div class="upload-btn-wrapper">
                    <button type="button" class="btn-outline">🔍 Scan Documents (OCR)</button>
                    <input type="file" multiple accept="image/*,application/pdf" onchange={handleScanSelect} title="Scan (OCR)" />
                </div>
                 {#if attachments.length > 0 || newAttachments.length > 0}
                    <button type="button" class="btn-outline" onclick={openGallery}>📷 View Gallery</button>
                 {/if}
            </div>

             {#if isScanning}
                <p class="info-text">{scanStatus || 'Scanning... Please wait.'}</p>
            {/if}
            {#if isUploading}
                <p class="info-text">Uploading...</p>
            {/if}
            {#if scanError}
                <p class="error-text">{scanError}</p>
            {/if}

            {#if attachments.length > 0 || newAttachments.length > 0}
                <div class="attachments-list">
                    {#each attachments as att, i}
                        <div class="attachment-item">
                            <span class="file-name" title={att.filename}>{att.filename}</span>
                            <button type="button" class="remove-btn" onclick={() => handleRemoveAttachment(i, false)}>❌</button>
                        </div>
                    {/each}
                    {#each newAttachments as att, i}
                        <div class="attachment-item new">
                            <span class="file-name" title={att.filename}>(New) {att.filename}</span>
                            <button type="button" class="remove-btn" onclick={() => handleRemoveAttachment(i, true)}>❌</button>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>

        <div class="form-group">
            <label for="name">Name</label>
            <input id="name" type="text" bind:value={name} required placeholder="e.g. Project Alpha Specs" />
        </div>

        <div class="form-group">
            <label for="description">Description</label>
            <textarea id="description" bind:value={description} rows="3" placeholder="Brief description of the document..."></textarea>
        </div>

        <div class="form-group">
            <label for="tags">Tags</label>
            <TagInput bind:selectedTags={tags} />
        </div>

        <div class="form-group">
            <label for="content">Recognized Content (Markdown)</label>
            <textarea id="content" bind:value={content} rows="10" placeholder="Recognized document content will appear here..."></textarea>
        </div>

        <div class="row">
            <div class="form-group half">
                <label for="type">Type</label>
                <select id="type" bind:value={type}>
                    <option value="plan">Plan</option>
                    <option value="mail">Mail</option>
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

         <div class="row">
             <div class="form-group half">
                <label for="date">Registration Date</label>
                <input id="date" type="date" bind:value={registration_date} />
            </div>
            <div class="form-group half">
                <label for="done_date">Done Date</label>
                <input id="done_date" type="date" bind:value={done_date} disabled={status !== 'done'} />
            </div>
        </div>

        <div class="form-group">
            <label for="author">Author</label>
            <input id="author" type="text" bind:value={author} placeholder="Your Name" />
        </div>

        <div class="actions">
            <button type="button" class="btn-secondary" onclick={onCancel}>Cancel</button>
            <button type="submit" class="btn-primary">{document ? 'Save Changes' : 'Register Document'}</button>
        </div>
    </form>

    <ImagePreviewModal
        isOpen={!!previewAttachments}
        close={() => previewAttachments = null}
        attachments={previewAttachments || []}
    />
</div>

<style>
    .form-container h3 {
        margin-top: 0;
        margin-bottom: 1.5rem;
        color: #2c3e50;
    }
    .form-group {
        margin-bottom: 1.25rem;
    }
    .row {
        display: flex;
        gap: 1rem;
    }
    .half {
        flex: 1;
    }
    label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #555;
        font-size: 0.9rem;
    }
    input, select, textarea {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        box-sizing: border-box;
        font-size: 1rem;
        transition: border-color 0.2s;
        font-family: inherit;
    }
    input:focus, select:focus, textarea:focus {
        border-color: #3b82f6;
        outline: none;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    .actions {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        margin-top: 2rem;
    }
    button {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
        transition: background-color 0.2s;
    }
    .btn-primary {
        background-color: #3b82f6;
        color: white;
    }
    .btn-primary:hover {
        background-color: #2563eb;
    }
    .btn-secondary {
        background-color: #f1f5f9;
        color: #64748b;
    }
    .btn-secondary:hover {
        background-color: #e2e8f0;
    }
    .info-text {
        font-size: 0.85rem;
        color: #3b82f6;
        margin-top: 0.25rem;
    }
    .error-text {
        font-size: 0.85rem;
        color: #ef4444;
        margin-top: 0.25rem;
    }
    textarea {
        resize: vertical;
        line-height: 1.5;
    }

    .form-section {
        margin-bottom: 1.5rem;
        border: 1px solid #e2e8f0;
        padding: 1rem;
        border-radius: 8px;
        background: #f8fafc;
    }
    .form-section h4 {
        margin: 0 0 1rem 0;
        font-size: 0.95rem;
        color: #475569;
    }
    .upload-buttons {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-bottom: 1rem;
    }
    .upload-btn-wrapper {
        position: relative;
        overflow: hidden;
        display: inline-block;
    }
    .upload-btn-wrapper input[type=file] {
        position: absolute;
        left: 0;
        top: 0;
        opacity: 0;
        width: 100%;
        height: 100%;
        cursor: pointer;
    }
    .btn-outline {
        background: white;
        border: 1px solid #cbd5e1;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        color: #475569;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .btn-outline:hover {
        background: #f1f5f9;
        border-color: #94a3b8;
    }

    .attachments-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    .attachment-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: white;
        padding: 0.5rem;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
        font-size: 0.9rem;
    }
    .file-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 250px;
    }
    .attachment-item.new {
        border-style: dashed;
        border-color: #3b82f6;
    }
    .remove-btn {
        background: none;
        color: #ef4444;
        padding: 0 0.5rem;
        font-size: 0.8rem;
    }
    .remove-btn:hover {
        background: #fee2e2;
    }
</style>
