<script>
    import { createJournalEntry } from './api.js';

    let { isOpen, close, documentId, documentName } = $props();
    let text = $state('');
    let type = $state('info');
    let author = $state('');
    let loading = $state(false);

    $effect(() => {
        if (isOpen) {
            author = localStorage.getItem('journal_author') || '';
            text = '';
            type = 'info';
        }
    });

    async function handleSubmit(e) {
        e.preventDefault();
        loading = true;
        if (author) localStorage.setItem('journal_author', author);

        try {
            await createJournalEntry({
                text,
                type,
                status: 'pending',
                author,
                document_id: documentId
            });
            close();
        } catch (err) {
            console.error(err);
            alert('Failed to create note');
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
            <h3>Add Note to {documentName}</h3>
            <button class="close-btn" onclick={close}>&times;</button>
        </div>

        <form onsubmit={handleSubmit} class="modal-body">
            <div class="form-group">
                <label for="author">Author</label>
                <input id="author" type="text" bind:value={author} placeholder="Your Name" />
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
                <textarea id="text" bind:value={text} required rows="4"></textarea>
            </div>

            <div class="actions">
                <button type="button" class="btn-secondary" onclick={close}>Cancel</button>
                <button type="submit" class="btn-primary" disabled={loading}>
                    {loading ? 'Saving...' : 'Add Note'}
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
    input, select, textarea {
        padding: 0.75rem;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        font-family: inherit;
        font-size: 1rem;
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
    .btn-primary { background: #3b82f6; color: white; }
    .btn-secondary { background: #f1f5f9; color: #475569; }
</style>
