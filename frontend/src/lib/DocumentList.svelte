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
        if(confirm('Are you sure?')) {
            await deleteDocument(id);
            refresh();
        }
    }

    function handleSearch() {
        refresh();
    }

</script>

<div class="list-container">
    <h3>Documents</h3>

    <div class="filters">
        <input
            type="text"
            placeholder="Search by name..."
            bind:value={search}
            oninput={handleSearch}
        />

        <select bind:value={filterType} onchange={handleSearch}>
            <option value="">All Types</option>
            <option value="plan">Plan</option>
            <option value="mail">Mail</option>
            <option value="other">Other</option>
        </select>

        <select bind:value={filterStatus} onchange={handleSearch}>
            <option value="">All Statuses</option>
            <option value="in_progress">In Progress</option>
            <option value="done">Done</option>
        </select>
    </div>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Status</th>
                <th>Date</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {#each documents as doc (doc.id)}
                <tr>
                    <td>{doc.id}</td>
                    <td>{doc.name}</td>
                    <td>{doc.type}</td>
                    <td>
                        <select
                            value={doc.status}
                            onchange={(e) => handleStatusChange(doc, e.target.value)}
                            class={doc.status === 'done' ? 'status-done' : 'status-progress'}
                        >
                            <option value="in_progress">In Progress</option>
                            <option value="done">Done</option>
                        </select>
                    </td>
                    <td>{doc.registration_date}</td>
                    <td>
                        <button class="delete-btn" onclick={() => handleDelete(doc.id)}>Delete</button>
                    </td>
                </tr>
            {/each}
        </tbody>
    </table>

    {#if documents.length === 0}
        <p>No documents found.</p>
    {/if}
</div>

<style>
    .list-container {
        padding: 1rem;
    }
    .filters {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    input, select {
        padding: 0.5rem;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1rem;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
    }
    .status-done {
        color: green;
        font-weight: bold;
    }
    .status-progress {
        color: orange;
        font-weight: bold;
    }
    .delete-btn {
        background-color: #dc3545;
        color: white;
        border: none;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        cursor: pointer;
    }
    .delete-btn:hover {
        background-color: #c82333;
    }
</style>
