<script>
    import { fetchDocuments, updateDocumentStatus, deleteDocument } from './api.js';

    let documents = $state([]);
    let search = $state('');
    let filterType = $state('');
    let filterStatus = $state('');

    export async function refresh() {
        documents = await fetchDocuments(search, filterType, filterStatus);
    }

    // Initial load
    refresh();

    async function handleStatusChange(doc, newStatus) {
        await updateDocumentStatus(doc.id, newStatus);
        refresh();
    }

    async function handleDelete(id) {
        if(confirm('Are you sure you want to delete this document?')) {
            await deleteDocument(id);
            refresh();
        }
    }

    function handleSearch() {
        refresh();
    }
</script>

<div class="list-container">
    <div class="filters">
        <div class="search-box">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <input
                type="text"
                placeholder="Search documents..."
                bind:value={search}
                oninput={handleSearch}
            />
        </div>

        <select bind:value={filterType} onchange={handleSearch} class="filter-select">
            <option value="">All Types</option>
            <option value="plan">Plan</option>
            <option value="mail">Mail</option>
            <option value="other">Other</option>
        </select>

        <select bind:value={filterStatus} onchange={handleSearch} class="filter-select">
            <option value="">All Statuses</option>
            <option value="in_progress">In Progress</option>
            <option value="done">Done</option>
        </select>
    </div>

    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th class="text-right">Actions</th>
                </tr>
            </thead>
            <tbody>
                {#each documents as doc (doc.id)}
                    <tr>
                        <td class="font-medium">{doc.name}</td>
                        <td>
                            <span class="badge badge-type">{doc.type}</span>
                        </td>
                        <td>
                            <select
                                value={doc.status}
                                onchange={(e) => handleStatusChange(doc, e.target.value)}
                                class="status-select {doc.status}"
                            >
                                <option value="in_progress">In Progress</option>
                                <option value="done">Done</option>
                            </select>
                        </td>
                        <td class="text-gray">{doc.registration_date}</td>
                        <td class="text-right">
                            <button class="delete-btn" onclick={() => handleDelete(doc.id)} title="Delete">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                            </button>
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>

        {#if documents.length === 0}
            <div class="empty-state">
                <p>No documents found.</p>
            </div>
        {/if}
    </div>
</div>

<style>
    .list-container {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }
    .filters {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }
    @media (max-width: 640px) {
        .filters {
            flex-direction: column;
            gap: 0.75rem;
        }
        .search-box, .filter-select {
            width: 100%;
            min-width: 0;
        }
        .filter-select {
            box-sizing: border-box;
        }
    }
    .search-box {
        position: relative;
        flex-grow: 1;
        min-width: 200px;
    }
    .search-icon {
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        color: #94a3b8;
    }
    .search-box input {
        width: 100%;
        padding: 0.75rem 0.75rem 0.75rem 2.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        font-size: 0.95rem;
    }
    .filter-select {
        padding: 0.75rem 2rem 0.75rem 1rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background-color: white;
        font-size: 0.95rem;
        color: #475569;
        cursor: pointer;
    }

    .table-wrapper {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        overflow: hidden;
        border: 1px solid #e2e8f0;
        overflow-x: auto;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        min-width: 600px;
    }
    th, td {
        padding: 1rem 1.5rem;
        text-align: left;
        border-bottom: 1px solid #e2e8f0;
    }
    th {
        background-color: #f8fafc;
        font-weight: 600;
        color: #475569;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    tr:last-child td {
        border-bottom: none;
    }
    tr:hover {
        background-color: #f8fafc;
    }
    .font-medium {
        font-weight: 500;
        color: #1e293b;
    }
    .text-gray {
        color: #64748b;
        font-size: 0.9rem;
    }
    .text-right {
        text-align: right;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: capitalize;
    }
    .badge-type {
        background-color: #e0e7ff;
        color: #4338ca;
    }
    .status-select {
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
        border: none;
        appearance: none;
        cursor: pointer;
        text-transform: capitalize;
    }
    .status-select.in_progress {
        background-color: #fff7ed;
        color: #c2410c;
    }
    .status-select.done {
        background-color: #f0fdf4;
        color: #15803d;
    }

    .delete-btn {
        background-color: transparent;
        color: #ef4444;
        border: none;
        padding: 0.5rem;
        border-radius: 6px;
        cursor: pointer;
        transition: background-color 0.2s;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    .delete-btn:hover {
        background-color: #fee2e2;
    }

    .empty-state {
        padding: 3rem;
        text-align: center;
        color: #64748b;
    }
</style>
