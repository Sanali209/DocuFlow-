<script>
    import { onMount } from "svelte";
    import { settingService } from "./stores/services.js";

    let { isOpen, close } = $props();
    let assignees = $state([]);
    let newAssigneeName = $state("");
    let editingId = $state(null);
    let editingName = $state("");

    async function loadAssignees() {
        if (isOpen) {
            assignees = await settingService.fetchAssignees();
        }
    }

    $effect(() => {
        loadAssignees();
    });

    async function handleAdd() {
        if (!newAssigneeName.trim()) return;
        try {
            await settingService.createAssignee({
                name: newAssigneeName.trim(),
            });
            newAssigneeName = "";
            await loadAssignees();
        } catch (e) {
            console.error(e);
            alert("Failed to add assignee");
        }
    }

    function startEdit(assignee) {
        editingId = assignee.id;
        editingName = assignee.name;
    }

    async function saveEdit() {
        if (!editingName.trim() || editingId === null) return;
        try {
            await settingService.updateAssignee(editingId, editingName.trim());
            editingId = null;
            editingName = "";
            await loadAssignees();
        } catch (e) {
            console.error(e);
            alert("Failed to update assignee");
        }
    }

    function cancelEdit() {
        editingId = null;
        editingName = "";
    }

    async function handleDelete(id) {
        if (!confirm("Delete this assignee?")) return;
        try {
            await settingService.deleteAssignee(id);
            await loadAssignees();
        } catch (e) {
            console.error(e);
            alert("Failed to delete assignee");
        }
    }
</script>

{#if isOpen}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="modal-overlay" onclick={close}>
        <div class="modal-content" onclick={(e) => e.stopPropagation()}>
            <div class="modal-header">
                <h3>Assignee Library</h3>
                <button class="close-btn" onclick={close}>&times;</button>
            </div>

            <div class="modal-body">
                <div class="add-section">
                    <input
                        type="text"
                        bind:value={newAssigneeName}
                        placeholder="New assignee name..."
                        onkeydown={(e) => e.key === "Enter" && handleAdd()}
                    />
                    <button class="btn-add" onclick={handleAdd}>Add</button>
                </div>

                <table class="assignees-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each assignees as assignee (assignee.id)}
                            <tr>
                                <td>
                                    {#if editingId === assignee.id}
                                        <input
                                            type="text"
                                            bind:value={editingName}
                                            class="edit-input"
                                            autofocus
                                            onkeydown={(e) => {
                                                if (e.key === "Enter")
                                                    saveEdit();
                                                if (e.key === "Escape")
                                                    cancelEdit();
                                            }}
                                        />
                                    {:else}
                                        {assignee.name}
                                    {/if}
                                </td>
                                <td>
                                    {#if editingId === assignee.id}
                                        <button
                                            class="btn-icon"
                                            onclick={saveEdit}
                                            title="Save">✓</button
                                        >
                                        <button
                                            class="btn-icon"
                                            onclick={cancelEdit}
                                            title="Cancel">✕</button
                                        >
                                    {:else}
                                        <button
                                            class="btn-icon"
                                            onclick={() => startEdit(assignee)}
                                            title="Edit">✏️</button
                                        >
                                        <button
                                            class="btn-icon delete"
                                            onclick={() =>
                                                handleDelete(assignee.id)}
                                            title="Delete">🗑️</button
                                        >
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>

                {#if assignees.length === 0}
                    <div class="empty-state">
                        No assignees yet. Add one above.
                    </div>
                {/if}
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
        border-radius: 8px;
        width: 100%;
        max-width: 600px;
        max-height: 80vh;
        display: flex;
        flex-direction: column;
        margin: 1rem;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
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
        line-height: 1;
    }
    .modal-body {
        padding: 1rem;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .add-section {
        display: flex;
        gap: 0.5rem;
    }
    .add-section input {
        flex: 1;
        padding: 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .btn-add {
        padding: 0.5rem 1rem;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 500;
        cursor: pointer;
        font-size: 0.9rem;
    }
    .btn-add:hover {
        background: #2563eb;
    }
    .assignees-table {
        width: 100%;
        border-collapse: collapse;
    }
    .assignees-table th,
    .assignees-table td {
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #e2e8f0;
    }
    .assignees-table th {
        background: #f8fafc;
        font-weight: 600;
        font-size: 0.85rem;
        color: #475569;
    }
    .assignees-table td {
        font-size: 0.9rem;
        color: #334155;
    }
    .assignees-table tr:last-child td {
        border-bottom: none;
    }
    .edit-input {
        width: 100%;
        padding: 0.25rem 0.5rem;
        border: 1px solid #3b82f6;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .btn-icon {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 1rem;
        padding: 0.25rem;
        margin: 0 0.1rem;
        border-radius: 4px;
    }
    .btn-icon:hover {
        background: #f1f5f9;
    }
    .btn-icon.delete:hover {
        background: #fee2e2;
    }
    .empty-state {
        text-align: center;
        color: #94a3b8;
        padding: 2rem;
        font-size: 0.9rem;
    }
</style>
