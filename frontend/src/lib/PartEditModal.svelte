<script>
    import { fetchMaterials } from "./api";

    let { show = $bindable(false), part = null, onsave } = $props();

    let materials = $state([]);
    let formData = $state({
        name: "",
        registration_number: "",
        width: 0,
        height: 0,
        material_id: null,
    });

    $effect(() => {
        if (show && part) {
            formData = {
                name: part.name || "",
                registration_number: part.registration_number || "",
                width: part.width || 0,
                height: part.height || 0,
                material_id: part.material_id || null,
            };
            loadMaterials();
        }
    });

    async function loadMaterials() {
        try {
            materials = await fetchMaterials();
        } catch (e) {
            console.error("Failed to load materials:", e);
        }
    }

    function close() {
        show = false;
    }

    function save() {
        if (onsave) {
            onsave(formData);
        }
        close();
    }
</script>

{#if show}
    <div class="modal-overlay" onclick={close}>
        <div class="modal" onclick={(e) => e.stopPropagation()}>
            <h2>Edit Part</h2>

            <div class="form">
                <div class="field">
                    <label for="name">Name</label>
                    <input id="name" type="text" bind:value={formData.name} />
                </div>

                <div class="field">
                    <label for="reg">Registration Number</label>
                    <input
                        id="reg"
                        type="text"
                        bind:value={formData.registration_number}
                    />
                </div>

                <div class="field">
                    <label for="width">Width (mm)</label>
                    <input
                        id="width"
                        type="number"
                        step="0.01"
                        bind:value={formData.width}
                    />
                </div>

                <div class="field">
                    <label for="height">Height (mm)</label>
                    <input
                        id="height"
                        type="number"
                        step="0.01"
                        bind:value={formData.height}
                    />
                </div>

                <div class="field">
                    <label for="material">Material</label>
                    <select id="material" bind:value={formData.material_id}>
                        <option value={null}>No Material</option>
                        {#each materials as mat}
                            <option value={mat.id}>{mat.name}</option>
                        {/each}
                    </select>
                </div>
            </div>

            <div class="actions">
                <button class="secondary" onclick={close}>Cancel</button>
                <button class="primary" onclick={save}>Save</button>
            </div>
        </div>
    </div>
{/if}

<style>
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .modal {
        background: white;
        padding: 24px;
        border-radius: 8px;
        width: 90%;
        max-width: 500px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    h2 {
        margin-top: 0;
        margin-bottom: 20px;
    }

    .form {
        display: flex;
        flex-direction: column;
        gap: 16px;
        margin-bottom: 24px;
    }

    .field {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    label {
        font-weight: 500;
        font-size: 14px;
    }

    input,
    select {
        padding: 8px 12px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
    }

    .actions {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
    }

    button {
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
    }

    .primary {
        background: #3b82f6;
        color: white;
    }

    .primary:hover {
        background: #2563eb;
    }

    .secondary {
        background: #e5e7eb;
        color: #374151;
    }

    .secondary:hover {
        background: #d1d5db;
    }
</style>
