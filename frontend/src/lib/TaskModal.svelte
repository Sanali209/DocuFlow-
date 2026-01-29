<script>
    let { isOpen, close, onSubmit } = $props();
    let name = $state('');
    let assignee = $state('');
    let loading = $state(false);

    $effect(() => {
        if (isOpen) {
            assignee = localStorage.getItem('task_assignee') || '';
            name = '';
        }
    });

    async function handleSubmit(e) {
        e.preventDefault();
        if (!name) return;

        loading = true;
        try {
            if (assignee) {
                localStorage.setItem('task_assignee', assignee);
            }
            await onSubmit({ name, assignee });
            close();
        } catch (err) {
            console.error(err);
            alert('Failed to add task');
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
            <h3>Add Task</h3>
            <button class="close-btn" onclick={close}>&times;</button>
        </div>

        <form onsubmit={handleSubmit} class="modal-body">
            <div class="form-group">
                <label for="name">Task Name</label>
                <input id="name" type="text" bind:value={name} placeholder="Enter task name..." required autofocus />
            </div>

            <div class="form-group">
                <label for="assignee">Assignee</label>
                <input id="assignee" type="text" bind:value={assignee} placeholder="Enter assignee name..." />
            </div>

            <div class="actions">
                <button type="button" class="btn-secondary" onclick={close}>Cancel</button>
                <button type="submit" class="btn-primary" disabled={loading}>
                    {loading ? 'Adding...' : 'Add Task'}
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
        border-radius: 8px;
        width: 100%;
        max-width: 400px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        margin: 1rem;
    }
    .modal-header {
        padding: 1rem;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .modal-header h3 {
        margin: 0;
        font-size: 1rem;
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
        padding: 1rem;
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
        font-size: 0.85rem;
        font-weight: 500;
        color: #475569;
    }
    input {
        padding: 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-family: inherit;
        font-size: 0.9rem;
    }
    .actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    button {
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 500;
        cursor: pointer;
        border: none;
        font-size: 0.9rem;
    }
    .btn-primary { background: #3b82f6; color: white; }
    .btn-secondary { background: #f1f5f9; color: #475569; }
</style>
