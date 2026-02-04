<script>
    import { onMount } from "svelte";
    import {
        updateTask,
        deleteTask,
        createTask,
        fetchAssignees,
    } from "./api.js";
    import TaskModal from "./TaskModal.svelte";
    import AssigneeLibraryModal from "./AssigneeLibraryModal.svelte";

    let { document, refresh, filterAssignee = "" } = $props();
    let tasks = $state(document.tasks || []);

    $effect(() => {
        tasks = document.tasks || [];
    });
    let filter = $state("hide_done"); // 'hide_done' | 'all' | 'pending'
    let isAddModalOpen = $state(false);
    let editingTask = $state(null);
    let groupByMaterial = $state(true); // Toggle for material grouping
    let assignees = $state([]);
    let isAssigneeLibraryOpen = $state(false);

    onMount(async () => {
        assignees = await fetchAssignees();
    });

    async function refreshAssignees() {
        assignees = await fetchAssignees();
    }

    // Sort tasks: pending/planned first, then done
    let sortedTasks = $derived(
        [...tasks].sort((a, b) => {
            if (a.status === "done" && b.status !== "done") return 1;
            if (a.status !== "done" && b.status === "done") return -1;
            return 0;
        }),
    );

    let filteredTasks = $derived(
        sortedTasks.filter((t) => {
            // Filter by status
            if (filter === "hide_done" && t.status === "done") return false;
            if (filter === "pending" && t.status !== "pending") return false;
            if (filter === "all") {
                // For 'all', only apply assignee filter if specified
                if (filterAssignee && filterAssignee.trim()) {
                    const assigneeLower = (t.assignee || "").toLowerCase();
                    const filterLower = filterAssignee.toLowerCase();
                    return assigneeLower.includes(filterLower);
                }
                return true;
            }

            // Filter by assignee if specified
            if (filterAssignee && filterAssignee.trim()) {
                const assigneeLower = (t.assignee || "").toLowerCase();
                const filterLower = filterAssignee.toLowerCase();
                if (!assigneeLower.includes(filterLower)) return false;
            }

            return true;
        }),
    );

    // Group tasks by material
    let groupedTasks = $derived(() => {
        if (!groupByMaterial) {
            return { "All Tasks": filteredTasks };
        }

        const groups = {};
        filteredTasks.forEach((task) => {
            const materialName = task.material
                ? task.material.name
                : "(No Material)";
            if (!groups[materialName]) {
                groups[materialName] = [];
            }
            groups[materialName].push(task);
        });

        // Sort groups: put "(No Material)" last
        const sortedGroups = {};
        const groupNames = Object.keys(groups).sort((a, b) => {
            if (a === "(No Material)") return 1;
            if (b === "(No Material)") return -1;
            return a.localeCompare(b);
        });

        groupNames.forEach((name) => {
            sortedGroups[name] = groups[name];
        });

        return sortedGroups;
    });

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
            tasks = tasks.filter((t) => t.id !== id);
            refresh();
        } catch (e) {
            console.error(e);
        }
    }

    async function handleTaskSubmit(taskData) {
        try {
            if (taskData.id) {
                // Update existing task
                const updatedTask = await updateTask(taskData.id, {
                    name: taskData.name,
                    assignee: taskData.assignee,
                    material_id: taskData.material_id,
                    gnc_file_path: taskData.gnc_file_path,
                });

                // Update local state
                tasks = tasks.map((t) =>
                    t.id === taskData.id ? { ...t, ...updatedTask } : t,
                );
                refresh();
            } else {
                // Create new task
                const newTask = await createTask(document.id, {
                    name: taskData.name,
                    assignee: taskData.assignee,
                    status: "planned",
                    material_id: taskData.material_id,
                    gnc_file_path: taskData.gnc_file_path,
                });
                tasks = [...tasks, newTask];
                refresh();
            }
        } catch (e) {
            console.error(e);
            throw e;
        }
    }

    function openAssigneeLibrary() {
        isAssigneeLibraryOpen = true;
    }

    function closeAssigneeLibrary() {
        isAssigneeLibraryOpen = false;
        refreshAssignees();
    }

    function openAddModal() {
        console.log("Opening Add Modal");
        editingTask = null;
        isAddModalOpen = true;
    }

    function openEditModal(task) {
        console.log("Opening Edit Modal for:", task);
        editingTask = task;
        isAddModalOpen = true;
    }
</script>

<div class="embedded-tasks">
    <div class="tasks-header">
        <h4>Tasks</h4>
        <div class="header-actions">
            <button
                class="group-toggle-btn"
                onclick={() => (groupByMaterial = !groupByMaterial)}
                title={groupByMaterial ? "Show flat list" : "Group by material"}
            >
                {groupByMaterial ? "📦" : "📋"}
            </button>
            <select bind:value={filter} class="filter-select">
                <option value="hide_done">Hide Done</option>
                <option value="all">Show All</option>
                <option value="pending">Pending</option>
            </select>
            <button class="add-task-btn" onclick={openAddModal}>+ Add</button>
        </div>
    </div>

    <div class="tasks-list">
        {#each Object.entries(groupedTasks()) as [materialName, tasksInGroup] (materialName)}
            {#if groupByMaterial && Object.keys(groupedTasks()).length > 1}
                <div class="material-group-header">
                    <span class="material-group-name">{materialName}</span>
                    <span class="material-group-count"
                        >({tasksInGroup.length})</span
                    >
                </div>
            {/if}

            {#each tasksInGroup as task (task.id)}
                <div class="task-item">
                    <div class="task-line-1">
                        <span
                            class="task-name {task.status === 'done'
                                ? 'done-text'
                                : ''}"
                            title={task.name}>{task.name}</span
                        >
                        <div class="task-right-group">
                            <select
                                value={task.status}
                                onchange={(e) =>
                                    handleStatusChange(
                                        task,
                                        e.currentTarget.value,
                                    )}
                                class="status-select {task.status}"
                            >
                                <option value="planned">Planned</option>
                                <option value="pending">Pending</option>
                                <option value="done">Done</option>
                            </select>
                            <div class="task-actions">
                                <button
                                    class="edit-btn"
                                    onclick={() => openEditModal(task)}
                                    title="Edit">✎</button
                                >
                                <button
                                    class="delete-btn"
                                    onclick={() => handleDelete(task.id)}
                                    title="Delete">×</button
                                >
                            </div>
                        </div>
                    </div>
                    <div class="task-line-2">
                        <div class="assignee-container">
                            <select
                                class="assignee-select"
                                value={task.assignee || ""}
                                onchange={(e) =>
                                    handleAssigneeChange(
                                        task,
                                        e.currentTarget.value,
                                    )}
                            >
                                <option value="">Assignee</option>
                                {#each assignees as asg}
                                    <option value={asg.name}>{asg.name}</option>
                                {/each}
                            </select>
                            <button
                                class="assignee-add-btn"
                                onclick={openAssigneeLibrary}
                                title="Manage Assignees">+</button
                            >
                        </div>
                        {#if task.material}
                            <span
                                class="material-badge"
                                title="Material: {task.material.name}"
                            >
                                📦 {task.material.name}
                            </span>
                        {/if}
                    </div>
                </div>
            {/each}
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
    close={() => (isAddModalOpen = false)}
    onSubmit={handleTaskSubmit}
    task={editingTask}
/>
<AssigneeLibraryModal
    isOpen={isAssigneeLibraryOpen}
    close={closeAssigneeLibrary}
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
    .group-toggle-btn {
        padding: 0.15rem 0.4rem;
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
        border-radius: 3px;
        font-size: 0.85rem;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.2s;
    }
    .group-toggle-btn:hover {
        background: #e2e8f0;
        color: #1e293b;
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
    .material-group-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 0.5rem;
        background: #f0fdf4;
        border-radius: 4px;
        margin-top: 0.5rem;
        border-left: 3px solid #166534;
    }
    .material-group-name {
        font-size: 0.8rem;
        font-weight: 600;
        color: #166534;
    }
    .material-group-count {
        font-size: 0.75rem;
        color: #16a34a;
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
    .task-right-group {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-shrink: 0;
    }
    .task-name.done-text {
        text-decoration: line-through;
        color: #94a3b8;
    }
    .task-actions {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    .edit-btn,
    .delete-btn {
        background: none;
        border: none;
        cursor: pointer;
        padding: 0;
        width: 18px;
        height: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        line-height: 1;
        opacity: 0.5;
    }
    .edit-btn {
        color: #3b82f6;
        font-size: 0.9rem;
    }
    .delete-btn {
        color: #ef4444;
        font-size: 1.1rem;
    }

    .edit-btn:hover {
        opacity: 1;
        background: #dbeafe;
        border-radius: 2px;
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
        width: 80px; /* Fixed width as requested */
        text-align: left;
    }
    .status-select.planned {
        background: #e0e7ff;
        color: #3730a3;
    }
    .status-select.pending {
        background: #ffedd5;
        color: #9a3412;
    }
    .status-select.done {
        background: #dcfce7;
        color: #166534;
    }

    .assignee-container {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        flex-grow: 1;
    }
    .assignee-select {
        flex-grow: 1;
        padding: 0.125rem 0.25rem;
        border: 1px solid #e2e8f0;
        border-radius: 2px;
        font-size: 0.7rem;
        color: #64748b;
        background: white;
        height: 20px;
    }
    .assignee-add-btn {
        background: none;
        border: 1px solid #e2e8f0;
        border-radius: 3px;
        color: #64748b;
        cursor: pointer;
        padding: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
    }
    .assignee-add-btn:hover {
        background: #f1f5f9;
        color: #3b82f6;
    }

    .material-badge {
        padding: 0.125rem 0.35rem;
        background: #f0fdf4;
        color: #166534;
        border-radius: 3px;
        font-size: 0.7rem;
        font-weight: 500;
        white-space: nowrap;
        flex-shrink: 0;
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
        .filter-select,
        .add-task-btn {
            font-size: 0.7rem;
            padding: 0.125rem 0.25rem;
        }
        .task-item {
            padding: 0.2rem;
        }
        .task-name {
            font-size: 0.75rem;
        }
        .status-select,
        .assignee-input {
            font-size: 0.65rem;
        }
    }
</style>
