<script>
    import { fetchTasks, createTask, updateTask, deleteTask } from './api.js';

    let { isOpen, close, document } = $props();
    let tasks = $state([]);
    let loading = $state(false);

    let newTaskName = $state('');
    let newTaskAssignee = $state('');

    $effect(() => {
        if (isOpen && document) {
            loadTasks();
        }
    });

    async function loadTasks() {
        loading = true;
        try {
            tasks = await fetchTasks(document.id);
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    }

    async function handleAdd(e) {
        e.preventDefault();
        if (!newTaskName) return;
        try {
            await createTask(document.id, {
                name: newTaskName,
                assignee: newTaskAssignee,
                status: 'planned'
            });
            newTaskName = '';
            newTaskAssignee = ''; // Optional: keep assignee for next task?
            loadTasks();
        } catch (e) {
            console.error(e);
        }
    }

    async function handleStatusChange(task, newStatus) {
        try {
            // Optimistic update
            const oldStatus = task.status;
            task.status = newStatus;

            await updateTask(task.id, { status: newStatus });
            // Refresh to be sure
            // loadTasks();
        } catch (e) {
            console.error(e);
            loadTasks(); // Revert on error
        }
    }

    async function handleDelete(id) {
        if (!confirm("Delete task?")) return;
        try {
            await deleteTask(id);
            loadTasks();
        } catch (e) {
            console.error(e);
        }
    }
</script>

{#if isOpen}
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="modal-overlay" onclick={close}>
    <div class="modal-content" onclick={(e) => e.stopPropagation()}>
        <div class="modal-header">
            <h3>Tasks: {document?.name}</h3>
            <button class="close-btn" onclick={close}>&times;</button>
        </div>

        <div class="modal-body">
            <form class="add-form" onsubmit={handleAdd}>
                <input type="text" placeholder="New Task..." bind:value={newTaskName} required class="input-name"/>
                <input type="text" placeholder="Assignee" bind:value={newTaskAssignee} class="input-assignee"/>
                <button type="submit" class="btn-add">+</button>
            </form>

            <div class="task-list">
                {#if loading}
                    <p class="loading">Loading tasks...</p>
                {:else if tasks.length === 0}
                    <p class="empty">No tasks found.</p>
                {:else}
                    {#each tasks as task (task.id)}
                        <div class="task-item">
                            <select value={task.status} onchange={(e) => handleStatusChange(task, e.target.value)} class="status-select {task.status}">
                                <option value="planned">Planned</option>
                                <option value="pending">Pending</option>
                                <option value="done">Done</option>
                            </select>

                            <div class="task-details">
                                <span class="task-name {task.status === 'done' ? 'done-text' : ''}">{task.name}</span>
                                {#if task.assignee}
                                    <span class="task-assignee">@{task.assignee}</span>
                                {/if}
                            </div>

                            <button class="delete-btn" onclick={() => handleDelete(task.id)}>🗑</button>
                        </div>
                    {/each}
                {/if}
            </div>
        </div>
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
        max-width: 600px;
        max-height: 80vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
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
        color: #1e293b;
        font-size: 1.1rem;
    }
    .close-btn {
        background: none;
        border: none;
        font-size: 1.5rem;
        color: #64748b;
        cursor: pointer;
        padding: 0;
        line-height: 1;
    }
    .modal-body {
        padding: 1.25rem;
        overflow-y: auto;
    }

    .add-form {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .input-name {
        flex: 2;
        padding: 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
    }
    .input-assignee {
        flex: 1;
        padding: 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
    }
    .btn-add {
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        width: 36px;
        cursor: pointer;
        font-size: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .task-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    .task-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background: #f8fafc;
    }
    .status-select {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        border: 1px solid #cbd5e1;
        font-size: 0.8rem;
        cursor: pointer;
    }
    .status-select.planned { background: #e0e7ff; color: #3730a3; border-color: #c7d2fe; }
    .status-select.pending { background: #ffedd5; color: #9a3412; border-color: #fed7aa; }
    .status-select.done { background: #dcfce7; color: #166534; border-color: #bbf7d0; }

    .task-details {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }
    .task-name {
        font-weight: 500;
        color: #334155;
    }
    .task-name.done-text {
        text-decoration: line-through;
        color: #94a3b8;
    }
    .task-assignee {
        font-size: 0.75rem;
        color: #64748b;
    }
    .delete-btn {
        background: none;
        border: none;
        color: #ef4444;
        cursor: pointer;
        opacity: 0.6;
    }
    .delete-btn:hover {
        opacity: 1;
        background: #fee2e2;
        border-radius: 4px;
    }

    .empty, .loading {
        text-align: center;
        color: #64748b;
        font-style: italic;
    }
</style>
