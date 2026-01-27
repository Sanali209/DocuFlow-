<script>
    import { createDocument, scanDocument, updateDocument } from './api.js';

    let { onDocumentCreated, onCancel, document = null } = $props();

    let name = $state(document?.name || '');
    let type = $state(document?.type || 'plan');
    let status = $state(document?.status || 'in_progress');
    let registration_date = $state(document?.registration_date || '');
    let content = $state(document?.content || '');

    let isScanning = $state(false);
    let scanError = $state('');
    let scanStatus = $state('');

    async function handleFileSelect(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        isScanning = true;
        scanError = '';

        // If replacing content (e.g. initial scan), we might want to clear it,
        // but user might be appending.
        // Logic: If user selects files, we append to existing content?
        // Or should we ask?
        // For now, let's assume if it's "New Document" and content is empty, we fill it.
        // If content exists, we append.

        try {
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                scanStatus = `Scanning file ${i + 1} of ${files.length}...`;

                const result = await scanDocument(file);

                // If OCR found a name and we don't have one yet, use it.
                if (result.name && !name) {
                    name = result.name;
                }

                // Append content with separator if needed
                const newContent = result.content || '';
                if (content && newContent) {
                    content += '\n\n---\n\n' + newContent;
                } else if (newContent) {
                    content = newContent;
                }
            }
        } catch (err) {
            scanError = 'Failed to scan one or more documents. Please try again or enter details manually.';
            console.error(err);
        } finally {
            isScanning = false;
            scanStatus = '';
            // Clear input so same files can be selected again if needed
            e.target.value = '';
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();
        const docData = {
            name,
            type,
            status,
            registration_date: registration_date || undefined,
            content
        };

        if (document) {
            await updateDocument(document.id, docData);
        } else {
            await createDocument(docData);
        }

        // Reset form (though component might be destroyed)
        if (!document) {
            name = '';
            type = 'plan';
            status = 'in_progress';
            registration_date = '';
            content = '';
        }

        onDocumentCreated();
    }
</script>

<div class="form-container">
    <h3>{document ? 'Edit Document' : 'New Document'}</h3>
    <form onsubmit={handleSubmit}>
        <div class="form-group">
            <label for="scan">{document ? 'Scan Pages (Appends to Content)' : 'Scan Document(s)'}</label>
            <input id="scan" type="file" multiple accept="image/*,application/pdf" onchange={handleFileSelect} />
            {#if isScanning}
                <p class="info-text">{scanStatus || 'Scanning... Please wait.'}</p>
            {/if}
            {#if scanError}
                <p class="error-text">{scanError}</p>
            {/if}
        </div>

        <div class="form-group">
            <label for="name">Name</label>
            <input id="name" type="text" bind:value={name} required placeholder="e.g. Project Alpha Specs" />
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

         <div class="form-group">
            <label for="date">Registration Date</label>
            <input id="date" type="date" bind:value={registration_date} />
        </div>

        <div class="actions">
            <button type="button" class="btn-secondary" onclick={onCancel}>Cancel</button>
            <button type="submit" class="btn-primary">{document ? 'Save Changes' : 'Register Document'}</button>
        </div>
    </form>
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
</style>
