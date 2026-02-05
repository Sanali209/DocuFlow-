<script>
    import { onMount } from 'svelte';
    import { fetchDocuments, updateTask } from './api.js';
    import { setMenuActions, clearMenuActions } from "./appState.svelte.js";

    let documents = $state([]);
    let assigneeFilter = $state('');
    let loading = $state(false);

    onMount(() => {
        // Load assignee from localStorage
        assigneeFilter = localStorage.getItem('job_assignee') || '';
        if (assigneeFilter) {
            loadData();
        }

        setMenuActions([
            {
                label: "Job",
                items: [
                    { label: "Refresh", action: loadData }
                ]
            }
        ]);

        return () => {
            clearMenuActions();
        };
    });

    async function loadData() {
        if (!assigneeFilter.trim()) {
            documents = [];
            return;
        }

        loading = true;
        try {
            // Fetch all documents and filter on client side for now
            // For better performance, this should be server-side
            const allDocs = await fetchDocuments();
            
            // Filter to only documents with tasks for this assignee
            documents = allDocs
                .map(doc => ({
                    ...doc,
                    tasks: (doc.tasks || []).filter(t => 
                        t.assignee && 
                        t.assignee.toLowerCase().includes(assigneeFilter.toLowerCase()) &&
                        (t.status === 'pending' || t.status === 'planned')
                    )
                }))
                .filter(doc => doc.tasks.length > 0);
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    }

    function handleAssigneeChange() {
        localStorage.setItem('job_assignee', assigneeFilter);
        loadData();
    }

    async function markTaskDone(taskId) {
        try {
            await updateTask(taskId, { status: 'done' });
            await loadData();
        } catch (e) {
            console.error(e);
            alert('Failed to update task status');
        }
    }

    // Group tasks by document and material
    function getGroupedTasks(doc) {
        const tasks = doc.tasks || [];
        
        // Sort tasks: pending first, then planned
        const sortedTasks = [...tasks].sort((a, b) => {
            if (a.status === 'pending' && b.status !== 'pending') return -1;
            if (a.status !== 'pending' && b.status === 'pending') return 1;
            return 0;
        });

        // Group by material
        const byMaterial = {};
        sortedTasks.forEach(task => {
            const materialKey = task.material ? task.material.name : '(No Material)';
            if (!byMaterial[materialKey]) {
                byMaterial[materialKey] = [];
            }
            byMaterial[materialKey].push(task);
        });

        return byMaterial;
    }
</script>

<div class="job-view">
    <div class="assignee-filter">
        <label for="assignee">Assignee:</label>
        <input 
            id="assignee" 
            type="text" 
            bind:value={assigneeFilter}
            onchange={handleAssigneeChange}
            placeholder="Enter assignee name..."
        />
        <button class="btn-load" onclick={loadData} disabled={loading || !assigneeFilter.trim()}>
            {loading ? 'Loading...' : 'Load'}
        </button>
    </div>

    {#if loading}
        <div class="loading-state">Loading tasks...</div>
    {:else if !assigneeFilter.trim()}
        <div class="empty-state">Enter an assignee name above to view their tasks.</div>
    {:else if documents.length === 0}
        <div class="empty-state">No pending or planned tasks found for this assignee.</div>
    {:else}
        <div class="documents-list">
            {#each documents as doc (doc.id)}
                {@const groupedTasks = getGroupedTasks(doc)}
                
                <div class="doc-group">
                    <div class="doc-header">
                        <h3>{doc.name}</h3>
                        <span class="doc-badge {doc.type}">{doc.type}</span>
                    </div>

                    {#each Object.entries(groupedTasks) as [materialName, tasks]}
                        <div class="material-group">
                            <div class="material-header">
                                <span class="material-name">📦 {materialName}</span>
                                <span class="task-count">{tasks.length} task{tasks.length !== 1 ? 's' : ''}</span>
                            </div>

                            <div class="tasks-list">
                                {#each tasks as task (task.id)}
                                    <div class="task-row {task.status}">
                                        <div class="task-info">
                                            <span class="task-status-badge {task.status}">{task.status}</span>
                                            <button 
                                                class="btn-done"
                                                onclick={() => markTaskDone(task.id)}
                                                title="Mark as done"
                                            >
                                                ✓
                                            </button>
                                            <span class="task-name">{task.name}</span>
                                        </div>
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {/each}
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .job-view {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .assignee-filter {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .assignee-filter label {
        font-weight: 600;
        color: #475569;
        white-space: nowrap;
    }

    .assignee-filter input {
        flex: 1;
        padding: 0.6rem;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        font-size: 0.95rem;
    }

    .btn-load {
        padding: 0.6rem 1.5rem;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
        white-space: nowrap;
        font-size: 0.95rem;
    }

    .btn-load:hover:not(:disabled) {
        background: #2563eb;
    }

    .btn-load:disabled {
        background: #cbd5e1;
        cursor: not-allowed;
    }

    .loading-state,
    .empty-state {
        text-align: center;
        color: #94a3b8;
        padding: 3rem;
        background: white;
        border-radius: 8px;
    }

    .documents-list {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .doc-group {
        background: white;
        border-radius: 8px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }

    .doc-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #f1f5f9;
    }

    .doc-header h3 {
        margin: 0;
        font-size: 1.1rem;
        color: #1e293b;
        font-weight: 600;
        flex: 1;
    }

    .doc-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .doc-badge.plan { background-color: #dbeafe; color: #1e40af; }
    .doc-badge.mail { background-color: #fce7f3; color: #9d174d; }
    .doc-badge.other { background-color: #f3f4f6; color: #374151; }

    .material-group {
        margin-bottom: 1rem;
    }

    .material-group:last-child {
        margin-bottom: 0;
    }

    .material-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0.75rem;
        background: #f8fafc;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }

    .material-name {
        font-weight: 600;
        color: #475569;
        font-size: 0.9rem;
    }

    .task-count {
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: 500;
    }

    .tasks-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding-left: 1rem;
    }

    .task-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem;
        background: #f8fafc;
        border-radius: 6px;
        border-left: 3px solid #cbd5e1;
        transition: all 0.2s;
    }

    .task-row.pending {
        border-left-color: #f59e0b;
        background: #fffbeb;
    }

    .task-row.planned {
        border-left-color: #3b82f6;
        background: #eff6ff;
    }

    .task-row:hover {
        transform: translateX(4px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .task-info {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex: 1;
        flex-wrap: wrap;
    }

    .task-status-badge {
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        flex-shrink: 0;
    }

    .task-status-badge.pending {
        background: #fed7aa;
        color: #9a3412;
    }

    .task-status-badge.planned {
        background: #bfdbfe;
        color: #1e40af;
    }

    .task-name {
        color: #334155;
        font-size: 0.9rem;
        line-height: 1.4;
        word-break: break-word;
        flex: 1;
    }

    .btn-done {
        background: #10b981;
        color: white;
        border: none;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.85rem;
        font-weight: bold;
        flex-shrink: 0;
        transition: all 0.2s;
    }

    .btn-done:hover {
        background: #059669;
        transform: scale(1.05);
    }

    /* Mobile optimization */
    @media (max-width: 768px) {
        .assignee-filter {
            flex-direction: column;
            align-items: stretch;
            gap: 0.5rem;
        }

        .assignee-filter label {
            font-size: 0.9rem;
        }

        .assignee-filter input {
            width: 100%;
        }

        .doc-group {
            padding: 1rem;
        }

        .doc-header h3 {
            font-size: 1rem;
        }

        .material-header {
            padding: 0.4rem 0.6rem;
        }

        .material-name {
            font-size: 0.85rem;
        }

        .task-count {
            font-size: 0.7rem;
        }

        .tasks-list {
            padding-left: 0.5rem;
            gap: 0.4rem;
        }

        .task-row {
            padding: 0.6rem;
        }

        .task-info {
            gap: 0.5rem;
        }

        .task-status-badge {
            font-size: 0.65rem;
            padding: 0.15rem 0.4rem;
        }

        .task-name {
            font-size: 0.85rem;
        }

        .btn-done {
            padding: 0.25rem 0.5rem;
            font-size: 0.8rem;
        }
    }

    /* Extra small screens */
    @media (max-width: 480px) {
        .task-info {
            gap: 0.4rem;
        }

        .task-name {
            flex-basis: 100%;
        }
    }
</style>
