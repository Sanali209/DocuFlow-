<script>
    import { onMount } from 'svelte';
    import { updateTask, deleteTask, createTask } from './api.js';
    import TaskModal from './TaskModal.svelte';

    let { document, refresh, filterAssignee = '' } = $props();
    let tasks = $state(document.tasks || []);
    let filter = $state('hide_done'); // 'hide_done' | 'all' | 'pending'
    let isAddModalOpen = $state(false);

    // Sort tasks: pending/planned first, then done
    let sortedTasks = $derived(
        [...tasks].sort((a, b) => {
            if (a.status === 'done' && b.status !== 'done') return 1;
            if (a.status !== 'done' && b.status === 'done') return -1;
            return 0;
        })
    );

    let filteredTasks = $derived(
        sortedTasks.filter(t => {
            // Filter by status
            if (filter === 'hide_done' && t.status === 'done') return false;
            if (filter === 'pending' && t.status !== 'pending') return false;
            
            // Filter by assignee if specified
            if (filterAssignee && filterAssignee.trim()) {
                const assigneeLower = (t.assignee || '').toLowerCase();
                const filterLower = filterAssignee.toLowerCase();
                if (!assigneeLower.includes(filterLower)) return false;
            }
            
            return true;
        })
    );

    async function handleStatusChange(task, newStatus) {
        try {
            task.status = newStatus; // Optimistic update
            await updateTask(task.id, { status: newStatus });
            refresh(); // Refresh parent to update badges/counts
        } catch (e) {
            console.error(e);
        }
    }

    async function handleAssigneeChange(task, newAssignee) {
        try {
            await updateTask(task.id, { assignee: newAssignee });
        } catch (e) {
            console.error(e);
        }
    }

    async function handleDelete(id) {
        if (!confirm("Delete task?")) return;
        try {
            await deleteTask(id);
            tasks = tasks.filter(t => t.id !== id);
            refresh();
        } catch (e) {
            console.error(e);
        }
    }

    async function handleAddTask(taskData) {
        try {
            const newTask = await createTask(document.id, {
                name: taskData.name,
                assignee: taskData.assignee,
                status: 'planned'
            });
            tasks = [...tasks, newTask];
            refresh();
        } catch (e) {
            console.error(e);
            throw e;
        }
    }
</script>

<div class="embedded-tasks">
    <div class="tasks-header">
        <h4>Tasks</h4>
        <div class="header-actions">
            <select bind:value={filter} class="filter-select">
                <option value="hide_done">Hide Done</option>
                <option value="all">Show All</option>
                <option value="pending">Pending</option>
            </select>
            <button class="add-task-btn" onclick={() => isAddModalOpen = true}>+ Add</button>
        </div>
    </div>

    <div class="tasks-list">
        {#each filteredTasks as task (task.id)}
            <div class="task-item">
                <div class="task-line-1">
                    <span class="task-name {task.status === 'done' ? 'done-text' : ''}">{task.name}</span>
                    <button class="delete-btn" onclick={() => handleDelete(task.id)} title="Delete">×</button>
                </div>
                <div class="task-line-2">
                    <select
                        value={task.status}
                        onchange={(e) => handleStatusChange(task, e.target.value)}
                        class="status-select {task.status}"
                    >
                        <option value="planned">Planned</option>
                        <option value="pending">Pending</option>
                        <option value="done">Done</option>
                    </select>
                    <input
                        type="text"
                        class="assignee-input"
                        placeholder="Assignee"
                        bind:value={task.assignee}
                        onchange={() => handleAssigneeChange(task, task.assignee)}
                    />
                </div>
            </div>
        {/each}

        {#if filteredTasks.length === 0}
            <div class="empty-tasks">
                {tasks.length > 0 ? "No tasks match filter." : "No tasks yet."}
            </div>
        {/if}
    </div>
</div>

<TaskModal
    isOpen={isAddModalOpen}
    close={() => isAddModalOpen = false}
    onSubmit={handleAddTask}
/>

<style>
    .embedded-tasks {
        border-top: 1px solid #f1f5f9;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
    }
    .tasks-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
        gap: 0.5rem;
    }
    h4 {
        margin: 0;
        font-size: 0.85rem;
        color: #475569;
        font-weight: 600;
    }
    .header-actions {
        display: flex;
        gap: 0.25rem;
        align-items: center;
    }
    .filter-select {
        padding: 0.15rem 0.25rem;
        border: 1px solid #e2e8f0;
        border-radius: 3px;
        font-size: 0.75rem;
        color: #64748b;
    }
    .add-task-btn {
        padding: 0.15rem 0.5rem;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 3px;
        font-size: 0.75rem;
        cursor: pointer;
        font-weight: 500;
    }
    .add-task-btn:hover {
        background: #2563eb;
    }

    .tasks-list {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    .task-item {
        display: flex;
        flex-direction: column;
        gap: 0.125rem;
        padding: 0.25rem;
        background: #f8fafc;
        border-radius: 3px;
        border: 1px solid #e2e8f0;
    }
    .task-line-1 {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.25rem;
    }
    .task-name {
        flex-grow: 1;
        color: #334155;
        font-size: 0.8rem;
        line-height: 1.3;
        word-break: break-word;
    }
    .task-name.done-text {
        text-decoration: line-through;
        color: #94a3b8;
    }
    .delete-btn {
        background: none;
        border: none;
        color: #ef4444;
        cursor: pointer;
        font-size: 1.1rem;
        line-height: 1;
        opacity: 0.5;
        padding: 0;
        width: 18px;
        height: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .delete-btn:hover {
        opacity: 1;
        background: #fee2e2;
        border-radius: 2px;
    }

    .task-line-2 {
        display: flex;
        gap: 0.25rem;
        align-items: center;
    }
    .status-select {
        padding: 0.125rem 0.25rem;
        border-radius: 2px;
        border: 1px solid transparent;
        font-size: 0.7rem;
        cursor: pointer;
        flex-shrink: 0;
    }
    .status-select.planned { background: #e0e7ff; color: #3730a3; }
    .status-select.pending { background: #ffedd5; color: #9a3412; }
    .status-select.done { background: #dcfce7; color: #166534; }

    .assignee-input {
        flex-grow: 1;
        padding: 0.125rem 0.25rem;
        border: 1px solid transparent;
        border-radius: 2px;
        font-size: 0.7rem;
        color: #64748b;
        background: transparent;
    }
    .assignee-input:hover, .assignee-input:focus {
        background: #ffffff;
        border-color: #cbd5e1;
    }

    .empty-tasks {
        font-size: 0.75rem;
        color: #94a3b8;
        font-style: italic;
        padding: 0.25rem;
        text-align: center;
    }

    /* Mobile optimization */
    @media (max-width: 640px) {
        .embedded-tasks {
            margin-top: 0.25rem;
            padding-top: 0.25rem;
        }
        h4 {
            font-size: 0.8rem;
        }
        .tasks-header {
            margin-bottom: 0.25rem;
        }
        .filter-select, .add-task-btn {
            font-size: 0.7rem;
            padding: 0.125rem 0.25rem;
        }
        .task-item {
            padding: 0.2rem;
        }
        .task-name {
            font-size: 0.75rem;
        }
        .status-select, .assignee-input {
            font-size: 0.65rem;
        }
    }
</style>
