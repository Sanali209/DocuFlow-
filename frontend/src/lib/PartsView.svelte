<script>
    import { onMount } from 'svelte';
    import { fetchParts } from './api';

    let parts = $state([]);
    let loading = $state(true);

    async function loadParts() {
        loading = true;
        try {
            parts = await fetchParts();
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    }

    onMount(loadParts);
</script>

<div class="view-container">
    <div class="header">
        <h2>Parts Library</h2>
    </div>

    {#if loading}
        <p>Loading parts...</p>
    {:else if parts.length === 0}
        <div class="empty-state">
            <p>No parts found in the library.</p>
            <p class="hint">Parts are automatically imported from the "Sidra" network folder.</p>
        </div>
    {:else}
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Registration</th>
                        <th>Name</th>
                        <th>Ver</th>
                        <th>Dimensions</th>
                        <th>Material</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {#each parts as part}
                        <tr>
                            <td class="font-mono">{part.registration_number}</td>
                            <td>{part.name}</td>
                            <td>
                                <span class="badge">{part.version}</span>
                            </td>
                            <td>{part.width.toFixed(1)} x {part.height.toFixed(1)}</td>
                            <td>{part.material ? part.material.name : '-'}</td>
                            <td>
                                <button class="action-btn">View</button>
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
    }
    h2 {
        margin: 0;
        font-size: 1.25rem;
        color: #1e293b;
    }
    .empty-state {
        padding: 3rem;
        text-align: center;
        color: #64748b;
    }
    .hint {
        font-size: 0.875rem;
        margin-top: 0.5rem;
    }
    .table-container {
        overflow-x: auto;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
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
    tr:last-child td {
        border-bottom: none;
    }
    .font-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        color: #0f172a;
        font-weight: 500;
    }
    .badge {
        background-color: #e2e8f0;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .action-btn {
        padding: 0.25rem 0.75rem;
        border: 1px solid #cbd5e1;
        background: white;
        border-radius: 4px;
        color: #475569;
        cursor: pointer;
        font-size: 0.875rem;
    }
    .action-btn:hover {
        background: #f8fafc;
        border-color: #94a3b8;
    }
</style>
