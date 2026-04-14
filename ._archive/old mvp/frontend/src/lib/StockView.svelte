<script>
    import { onMount } from "svelte";
    import { inventoryService } from "./stores/services.js";
    import { uiState } from "./stores/appState.svelte.js";
    import { setMenuActions, clearMenuActions } from "./appState.svelte.js";

    let items = $state([]);
    let materials = $state([]);
    let loading = $state(true);
    let showAddForm = $state(false);

    // Form state
    let newItem = $state({
        material_id: "",
        width: 0,
        height: 0,
        quantity: 0,
        location: "",
    });

    async function loadData() {
        loading = true;
        try {
            const [stockData, matData] = await Promise.all([
                inventoryService.fetchStock(),
                inventoryService.fetchMaterials(),
            ]);
            items = stockData;
            materials = matData;
        } catch (e) {
            console.error(e);
            uiState.addNotification("Failed to load stock data", "error");
        } finally {
            loading = false;
        }
    }

    function toggleAddForm() {
        showAddForm = !showAddForm;
    }

    async function handleAdd() {
        if (!newItem.material_id) return;
        try {
            const created = await inventoryService.createStockItem(newItem);
            items = [...items, created];
            showAddForm = false;
            // Reset form
            newItem = {
                material_id: "",
                width: 0,
                height: 0,
                quantity: 0,
                location: "",
            };
            uiState.addNotification("Stock item added", "info");
        } catch (e) {
            console.error(e);
            uiState.addNotification("Failed to add stock item", "error");
        }
    }

    async function handleDelete(id) {
        if (!confirm("Are you sure you want to delete this item?")) return;
        try {
            await inventoryService.deleteStockItem(id);
            items = items.filter((i) => i.id !== id);
            uiState.addNotification("Stock item deleted", "info");
        } catch (e) {
            console.error(e);
            uiState.addNotification("Failed to delete item", "error");
        }
    }

    onMount(() => {
        loadData();
        setMenuActions([
            {
                label: "Stock",
                items: [
                    { label: "Add Stock", action: toggleAddForm },
                    { label: "Refresh", action: loadData },
                ],
            },
        ]);

        return () => {
            clearMenuActions();
        };
    });
</script>

<div class="view-container">
    <div class="header">
        <h2>Stock Management</h2>
    </div>

    {#if showAddForm}
        <div class="form-panel">
            <h3>New Stock Item</h3>
            <div class="form-grid">
                <div class="field">
                    <label for="stock-mat">Material</label>
                    <select id="stock-mat" bind:value={newItem.material_id}>
                        <option value="">Select Material...</option>
                        {#each materials as mat}
                            <option value={mat.id}>{mat.name}</option>
                        {/each}
                    </select>
                </div>
                <div class="field">
                    <label for="stock-width">Width (mm)</label>
                    <input
                        id="stock-width"
                        type="number"
                        bind:value={newItem.width}
                        min="0"
                    />
                </div>
                <div class="field">
                    <label for="stock-height">Height (mm)</label>
                    <input
                        id="stock-height"
                        type="number"
                        bind:value={newItem.height}
                        min="0"
                    />
                </div>
                <div class="field">
                    <label for="stock-qty">Quantity</label>
                    <input
                        id="stock-qty"
                        type="number"
                        bind:value={newItem.quantity}
                        min="0"
                    />
                </div>
                <div class="field">
                    <label for="stock-loc">Location</label>
                    <input
                        id="stock-loc"
                        type="text"
                        bind:value={newItem.location}
                        placeholder="e.g. A-01"
                    />
                </div>
                <div class="actions">
                    <button class="save-btn" onclick={handleAdd}
                        >Save Item</button
                    >
                </div>
            </div>
        </div>
    {/if}

    {#if loading}
        <p class="loading">Loading stock...</p>
    {:else if items.length === 0}
        <div class="empty-state">
            <p>No stock items found.</p>
        </div>
    {:else}
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Material</th>
                        <th>Dimensions</th>
                        <th>Qty</th>
                        <th>Reserved</th>
                        <th>Location</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {#each items as item}
                        <tr>
                            <td
                                >{item.material
                                    ? item.material.name
                                    : "Unknown"}</td
                            >
                            <td>{item.width} x {item.height}</td>
                            <td>{item.quantity}</td>
                            <td>{item.reserved}</td>
                            <td>{item.location || "-"}</td>
                            <td>
                                <button
                                    class="delete-btn"
                                    onclick={() => handleDelete(item.id)}
                                    >Delete</button
                                >
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>

<style>
    .view-container {
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        min-height: 400px;
    }
    .header {
        padding: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    h2 {
        margin: 0;
        font-size: 1.25rem;
        color: #1e293b;
    }

    .form-panel {
        background: #f8fafc;
        padding: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        align-items: end;
    }
    .field {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    label {
        font-size: 0.875rem;
        color: #64748b;
        font-weight: 500;
    }
    input,
    select {
        padding: 0.5rem;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        width: 100%;
    }
    .save-btn {
        background-color: #10b981;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        height: 38px;
        font-weight: 500;
    }

    .table-container {
        overflow-x: auto;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th,
    td {
        text-align: left;
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #f1f5f9;
    }
    th {
        font-weight: 600;
        color: #64748b;
        font-size: 0.875rem;
        background-color: #f8fafc;
    }
    .delete-btn {
        color: #ef4444;
        background: none;
        border: none;
        cursor: pointer;
        font-size: 0.875rem;
    }
    .delete-btn:hover {
        text-decoration: underline;
    }

    .empty-state,
    .loading {
        padding: 3rem;
        text-align: center;
        color: #64748b;
    }
</style>
