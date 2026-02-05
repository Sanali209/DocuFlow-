<script>
    import { onMount } from "svelte";
    import { fetchMaterials, fetchAssignees } from "./api.js";
    import MaterialLibraryModal from "./MaterialLibraryModal.svelte";
    import AssigneeLibraryModal from "./AssigneeLibraryModal.svelte";

    let { isOpen, close, onSubmit, task = null } = $props();
    let name = $state("");
    let assignee = $state("");
    let materialId = $state(null);
    let gncFilePath = $state("");
    let loading = $state(false);
    let materials = $state([]);
    let assignees = $state([]);
    let isLibraryOpen = $state(false);
    let isAssigneeLibraryOpen = $state(false);

    async function loadMaterials() {
        materials = await fetchMaterials();
    }

    async function loadAssignees() {
        assignees = await fetchAssignees();
    }

    $effect(() => {
        if (isOpen) {
            console.log("TaskModal Opened. Task:", task);
            if (task) {
                // Edit Mode
                name = task.name;
                assignee = task.assignee || "";
                materialId =
                    task.material_id ||
                    (task.material ? task.material.id : null);
                gncFilePath = task.gnc_file_path || "";
            } else {
                // Add Mode
                assignee = localStorage.getItem("task_assignee") || "";
                name = "";
                materialId = null;
                gncFilePath = "";
            }
            loadMaterials();
            loadAssignees();
        }
    });

    async function handleSubmit(e) {
        e.preventDefault();
        if (!name) return;

        loading = true;
        try {
            if (assignee && !task) {
                // Only save default assignee on create
                localStorage.setItem("task_assignee", assignee);
            }
            await onSubmit({
                id: task ? task.id : undefined,
                name,
                assignee,
                material_id: materialId,
                gnc_file_path: gncFilePath,
            });
            close();
        } catch (err) {
            console.error(err);
            alert("Failed to add task");
        } finally {
            loading = false;
        }
    }

    function openLibrary() {
        isLibraryOpen = true;
    }

    function closeLibrary() {
        isLibraryOpen = false;
        loadMaterials(); // Reload materials after library is closed
    }

    function openAssigneeLibrary() {
        isAssigneeLibraryOpen = true;
    }

    function closeAssigneeLibrary() {
        isAssigneeLibraryOpen = false;
        loadAssignees();
    }
</script>

{#if isOpen}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="modal-overlay" onclick={close}>
        <div class="modal-content" onclick={(e) => e.stopPropagation()}>
            <div class="modal-header">
                <h3>{task ? "Edit Task" : "Add Task"}</h3>
                <button class="close-btn" onclick={close}>&times;</button>
            </div>

            <form onsubmit={handleSubmit} class="modal-body">
                <div class="form-group">
                    <label for="name">Task Name</label>
                    <input
                        id="name"
                        type="text"
                        bind:value={name}
                        placeholder="Enter task name..."
                        required
                        autofocus
                    />
                </div>

                <div class="form-group">
                    <label for="material">Material</label>
                    <div class="material-row">
                        <select
                            id="material"
                            bind:value={materialId}
                            class="material-select"
                        >
                            <option value={null}>-- No Material --</option>
                            {#each materials as material}
                                <option value={material.id}
                                    >{material.name}</option
                                >
                            {/each}
                        </select>
                        <button
                            type="button"
                            class="btn-library"
                            onclick={openLibrary}
                            title="Edit Material Library"
                        >
                            📚
                        </button>
                    </div>
                </div>

                <div class="form-group">
                    <label for="gnc_path">GNC File Path</label>
                    <input
                        id="gnc_path"
                        type="text"
                        bind:value={gncFilePath}
                        placeholder="e.g. Z:\Sidra\Part1.gnc"
                    />
                </div>

                {#if task && task.part_associations && task.part_associations.length > 0}
                    <div class="form-group">
                        <label>Associated Parts</label>
                        <div class="parts-list">
                            {#each task.part_associations as link}
                                <div class="part-item">
                                    <span
                                        class="part-name"
                                        title={link.part.name}
                                        >{link.part.name}</span
                                    >
                                    <span class="part-qty"
                                        >x{link.quantity}</span
                                    >
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}

                <div class="form-group">
                    <label for="assignee">Assignee</label>
                    <div class="material-row">
                        <select
                            id="assignee"
                            bind:value={assignee}
                            class="material-select"
                        >
                            <option value="">-- No Assignee --</option>
                            {#each assignees as asg}
                                <option value={asg.name}>{asg.name}</option>
                            {/each}
                        </select>
                        <button
                            type="button"
                            class="btn-library"
                            onclick={openAssigneeLibrary}
                            title="Edit Assignee Library"
                        >
                            👥
                        </button>
                    </div>
                </div>

                <div class="actions">
                    <button type="button" class="btn-secondary" onclick={close}
                        >Cancel</button
                    >
                    <button
                        type="submit"
                        class="btn-primary"
                        disabled={loading}
                    >
                        {loading
                            ? task
                                ? "Saving..."
                                : "Adding..."
                            : task
                              ? "Save Changes"
                              : "Add Task"}
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<MaterialLibraryModal isOpen={isLibraryOpen} close={closeLibrary} />
<AssigneeLibraryModal
    isOpen={isAssigneeLibraryOpen}
    close={closeAssigneeLibrary}
/>

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
    .btn-primary {
        background: #3b82f6;
        color: white;
    }
    .btn-secondary {
        background: #f1f5f9;
        color: #475569;
    }
    .material-row {
        display: flex;
        gap: 0.5rem;
    }
    .material-select {
        flex: 1;
        padding: 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-family: inherit;
        font-size: 0.9rem;
    }
    .btn-library {
        padding: 0.5rem;
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
        cursor: pointer;
        font-size: 1.2rem;
    }
    .btn-library:hover {
        background: #e2e8f0;
    }

    .parts-list {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        background: #f8fafc;
        padding: 0.5rem;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
        max-height: 150px;
        overflow-y: auto;
    }
    .part-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: white;
        padding: 0.25rem 0.5rem;
        border: 1px solid #f1f5f9;
        border-radius: 3px;
        font-size: 0.85rem;
    }
    .part-name {
        font-weight: 500;
        color: #334155;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 200px;
    }
    .part-qty {
        font-weight: 600;
        color: #166534;
        background: #dcfce7;
        padding: 0.1rem 0.4rem;
        border-radius: 10px;
        font-size: 0.75rem;
    }
</style>
