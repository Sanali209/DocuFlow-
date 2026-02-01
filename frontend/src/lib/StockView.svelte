<script>
    import { onMount } from 'svelte';
    import { fetchStock, createStockItem, deleteStockItem, fetchMaterials } from './api';

    let items = $state([]);
    let materials = $state([]);
    let loading = $state(true);
    let showAddForm = $state(false);

    // Form state
    let newItem = $state({
        material_id: '',
        width: 0,
        height: 0,
        quantity: 0,
        location: ''
    });

    async function loadData() {
        loading = true;
        try {
            const [stockData, matData] = await Promise.all([
                fetchStock(),
                fetchMaterials()
            ]);
            items = stockData;
            materials = matData;
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    }

    async function handleAdd() {
        if (!newItem.material_id) return;
        try {
            const created = await createStockItem(newItem);
            items = [...items, created];
            showAddForm = false;
            // Reset form
            newItem = { material_id: '', width: 0, height: 0, quantity: 0, location: '' };
        } catch (e) {
            alert("Failed to add stock item");
            console.error(e);
        }
    }

    async function handleDelete(id) {
        if (!confirm("Are you sure you want to delete this item?")) return;
        try {
            await deleteStockItem(id);
            items = items.filter(i => i.id !== id);
        } catch (e) {
            alert("Failed to delete item");
        }
    }

    onMount(loadData);
</script>

<div class="view-container">
    <div class="header">
        <h2>Stock Management</h2>
        <button class="primary-btn" onclick={() => showAddForm = !showAddForm}>
            {showAddForm ? 'Cancel' : 'Add Stock'}
        </button>
    </div>

    {#if showAddForm}
        <div class="form-panel">
            <h3>New Stock Item</h3>
            <div class="form-grid">
                <div class="field">
                    <label>Material</label>
                    <select bind:value={newItem.material_id}>
                        <option value="">Select Material...</option>
                        {#each materials as mat}
                            <option value={mat.id}>{mat.name}</option>
                        {/each}
                    </select>
                </div>
                <div class="field">
                    <label>Width (mm)</label>
                    <input type="number" bind:value={newItem.width} min="0" />
                </div>
                <div class="field">
                    <label>Height (mm)</label>
                    <input type="number" bind:value={newItem.height} min="0" />
                </div>
                <div class="field">
                    <label>Quantity</label>
                    <input type="number" bind:value={newItem.quantity} min="0" />
                </div>
                <div class="field">
                    <label>Location</label>
                    <input type="text" bind:value={newItem.location} placeholder="e.g. A-01" />
                </div>
                <div class="actions">
                    <button class="save-btn" onclick={handleAdd}>Save Item</button>
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
                            <td>{item.material ? item.material.name : 'Unknown'}</td>
                            <td>{item.width} x {item.height}</td>
                            <td>{item.quantity}</td>
                            <td>{item.reserved}</td>
                            <td>{item.location || '-'}</td>
                            <td>
                                <button class="delete-btn" onclick={() => handleDelete(item.id)}>Delete</button>
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
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        min-height: 400px;
    }
    .header {
        padding: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    h2 { margin: 0; font-size: 1.25rem; color: #1e293b; }

    .primary-btn {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
    }
    .primary-btn:hover { background-color: #2563eb; }

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
    label { font-size: 0.875rem; color: #64748b; font-weight: 500; }
    input, select {
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

    .table-container { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; }
    th, td {
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
    .delete-btn:hover { text-decoration: underline; }

    .empty-state, .loading { padding: 3rem; text-align: center; color: #64748b; }
</style>
