<script>
    import { onMount } from 'svelte';
    import { updateTask, deleteTask, createTask } from './api.js';

    let { document, refresh } = $props();
    let tasks = $state(document.tasks || []);
    let filter = $state('hide_done'); // 'hide_done' | 'all' | 'pending'

    let newTaskName = $state('');
    let newTaskAssignee = $state('');

    onMount(() => {
        const savedAssignee = localStorage.getItem('task_assignee');
        if (savedAssignee) {
            newTaskAssignee = savedAssignee;
        }
    });

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
            if (filter === 'hide_done') return t.status !== 'done';
            if (filter === 'pending') return t.status === 'pending';
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
            // task.assignee = newAssignee; // Bind handles this
            await updateTask(task.id, { assignee: newAssignee });
        } catch (e) {
            console.error(e);
        }
    }

    async function handleDelete(id) {
        if (!confirm("Delete task?")) return;
        try {
            await deleteTask(id);
            // Remove from local list immediately for responsiveness
            tasks = tasks.filter(t => t.id !== id);
            refresh();
        } catch (e) {
            console.error(e);
        }
    }

    async function handleAdd(e) {
        e.preventDefault();
        if (!newTaskName) return;

        if (newTaskAssignee) {
            localStorage.setItem('task_assignee', newTaskAssignee);
        }

        try {
            const newTask = await createTask(document.id, {
                name: newTaskName,
                assignee: newTaskAssignee,
                status: 'planned'
            });
            tasks = [...tasks, newTask];
            newTaskName = '';
            // newTaskAssignee = ''; // Keep assignee for rapid entry? User asked to persist "last entered", implying keeping it or reloading it.
            // If we reload from storage on mount, we should probably keep it in the input too for multiple entries.
            refresh();
        } catch (e) {
            console.error(e);
        }
    }
</script>

<div class="embedded-tasks">
    <div class="tasks-header">
        <h4>Tasks</h4>
        <select bind:value={filter} class="filter-select">
            <option value="hide_done">Hide Done</option>
            <option value="all">Show All</option>
            <option value="pending">Show Pending</option>
        </select>
    </div>

    <div class="tasks-list">
        {#each filteredTasks as task (task.id)}
            <div class="task-row">
                <select
                    value={task.status}
                    onchange={(e) => handleStatusChange(task, e.target.value)}
                    class="status-select {task.status}"
                >
                    <option value="planned">Planned</option>
                    <option value="pending">Pending</option>
                    <option value="done">Done</option>
                </select>

                <span class="task-name {task.status === 'done' ? 'done-text' : ''}">{task.name}</span>

                <input
                    type="text"
                    class="assignee-input"
                    placeholder="Assignee"
                    bind:value={task.assignee}
                    onchange={() => handleAssigneeChange(task, task.assignee)}
                />

                <button class="delete-btn" onclick={() => handleDelete(task.id)} title="Delete Task">🗑</button>
            </div>
        {/each}

        {#if filteredTasks.length === 0}
            <div class="empty-tasks">
                {tasks.length > 0 ? "No tasks match filter." : "No tasks yet."}
            </div>
        {/if}
    </div>

    <form class="add-row" onsubmit={handleAdd}>
        <input type="text" placeholder="Add new task..." bind:value={newTaskName} class="add-name" />
        <input type="text" placeholder="Assignee" bind:value={newTaskAssignee} class="add-assignee" />
        <button type="submit" class="add-btn">+</button>
    </form>
</div>

<style>
    .embedded-tasks {
        border-top: 1px solid #f1f5f9;
        margin-top: 1rem;
        padding-top: 1rem;
    }
    .tasks-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }
    h4 {
        margin: 0;
        font-size: 0.95rem;
        color: #475569;
        font-weight: 600;
    }
    .filter-select {
        padding: 0.2rem 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-size: 0.8rem;
        color: #64748b;
    }

    .tasks-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }
    .task-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
    }
    .status-select {
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        border: 1px solid transparent;
        font-size: 0.75rem;
        cursor: pointer;
        width: 80px;
    }
    .status-select.planned { background: #e0e7ff; color: #3730a3; }
    .status-select.pending { background: #ffedd5; color: #9a3412; }
    .status-select.done { background: #dcfce7; color: #166534; }

    .task-name {
        flex-grow: 1;
        color: #334155;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .task-name.done-text {
        text-decoration: line-through;
        color: #94a3b8;
    }

    .assignee-input {
        width: 80px;
        padding: 0.15rem 0.3rem;
        border: 1px solid transparent;
        border-radius: 4px;
        font-size: 0.8rem;
        color: #64748b;
        background: transparent;
    }
    .assignee-input:hover, .assignee-input:focus {
        background: #f8fafc;
        border-color: #e2e8f0;
    }

    .delete-btn {
        background: none;
        border: none;
        color: #ef4444;
        cursor: pointer;
        font-size: 0.8rem;
        opacity: 0.5;
        padding: 0.2rem;
    }
    .delete-btn:hover {
        opacity: 1;
        background: #fee2e2;
        border-radius: 4px;
    }

    .empty-tasks {
        font-size: 0.85rem;
        color: #94a3b8;
        font-style: italic;
        padding: 0.5rem 0;
    }

    .add-row {
        display: flex;
        gap: 0.5rem;
    }
    .add-name {
        flex-grow: 1;
        padding: 0.3rem 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .add-assignee {
        width: 80px;
        padding: 0.3rem 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .add-btn {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        width: 24px;
        cursor: pointer;
        color: #475569;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .add-btn:hover {
        background: #e2e8f0;
    }
</style>
