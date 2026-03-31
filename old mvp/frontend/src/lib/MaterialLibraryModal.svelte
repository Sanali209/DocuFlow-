<script>
    import { onMount } from "svelte";
    import { inventoryService } from "./stores/services.js";
    import { uiState } from "./stores/appState.svelte.js";

    let { isOpen, close } = $props();
    let materials = $state([]);
    let newMaterialName = $state("");
    let editingId = $state(null);
    let editingName = $state("");

    async function loadMaterials() {
        if (isOpen) {
            try {
                materials = await inventoryService.fetchMaterials();
            } catch (e) {
                console.error(e);
                uiState.addNotification("Failed to load materials", "error");
            }
        }
    }

    $effect(() => {
        loadMaterials();
    });

    async function handleAdd() {
        if (!newMaterialName.trim()) return;
        try {
            await inventoryService.createMaterial({
                name: newMaterialName.trim(),
            });
            newMaterialName = "";
            uiState.addNotification("Material added", "info");
            await loadMaterials();
        } catch (e) {
            console.error(e);
            uiState.addNotification("Failed to add material", "error");
        }
    }

    function startEdit(material) {
        editingId = material.id;
        editingName = material.name;
    }

    async function saveEdit() {
        if (!editingName.trim() || editingId === null) return;
        try {
            await inventoryService.updateMaterial(
                editingId,
                editingName.trim(),
            );
            editingId = null;
            editingName = "";
            uiState.addNotification("Material updated", "info");
            await loadMaterials();
        } catch (e) {
            console.error(e);
            uiState.addNotification("Failed to update material", "error");
        }
    }

    function cancelEdit() {
        editingId = null;
        editingName = "";
    }

    async function handleDelete(id) {
        if (!confirm("Delete this material?")) return;
        try {
            await inventoryService.deleteMaterial(id);
            uiState.addNotification("Material deleted", "info");
            await loadMaterials();
        } catch (e) {
            console.error(e);
            uiState.addNotification("Failed to delete material", "error");
        }
    }
</script>

{#if isOpen}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="modal-overlay" onclick={close}>
        <div class="modal-content" onclick={(e) => e.stopPropagation()}>
            <div class="modal-header">
                <h3>Material Library</h3>
                <button class="close-btn" onclick={close}>&times;</button>
            </div>

            <div class="modal-body">
                <div class="add-section">
                    <input
                        type="text"
                        bind:value={newMaterialName}
                        placeholder="New material name..."
                        onkeydown={(e) => e.key === "Enter" && handleAdd()}
                    />
                    <button class="btn-add" onclick={handleAdd}>Add</button>
                </div>

                <table class="materials-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each materials as material (material.id)}
                            <tr>
                                <td>
                                    {#if editingId === material.id}
                                        <input
                                            type="text"
                                            bind:value={editingName}
                                            class="edit-input"
                                            onkeydown={(e) => {
                                                if (e.key === "Enter")
                                                    saveEdit();
                                                if (e.key === "Escape")
                                                    cancelEdit();
                                            }}
                                        />
                                    {:else}
                                        {material.name}
                                    {/if}
                                </td>
                                <td>
                                    {#if editingId === material.id}
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
                                            onclick={() => startEdit(material)}
                                            title="Edit">✏️</button
                                        >
                                        <button
                                            class="btn-icon delete"
                                            onclick={() =>
                                                handleDelete(material.id)}
                                            title="Delete">🗑️</button
                                        >
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>

                {#if materials.length === 0}
                    <div class="empty-state">
                        No materials yet. Add one above.
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
    .materials-table {
        width: 100%;
        border-collapse: collapse;
    }
    .materials-table th,
    .materials-table td {
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #e2e8f0;
    }
    .materials-table th {
        background: #f8fafc;
        font-weight: 600;
        font-size: 0.85rem;
        color: #475569;
    }
    .materials-table td {
        font-size: 0.9rem;
        color: #334155;
    }
    .materials-table tr:last-child td {
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
