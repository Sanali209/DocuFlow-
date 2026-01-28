<script>
    import { fetchDocuments, updateDocumentStatus, deleteDocument } from './api.js';
    import Modal from './Modal.svelte';
    import DocumentView from './DocumentView.svelte';
    import TaskModal from './TaskModal.svelte';

    let documents = $state([]);
    let search = $state('');
    let filterType = $state('');
    let filterStatus = $state('');
    let viewingDoc = $state(null);
    let taskDoc = $state(null);
    let sortBy = $state('registration_date');
    let sortOrder = $state('desc');
    let { onEdit } = $props();

    export async function refresh() {
        documents = await fetchDocuments(search, filterType, filterStatus, sortBy, sortOrder);
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

    function handleSort(field) {
        if (sortBy === field) {
            sortOrder = sortOrder === 'desc' ? 'asc' : 'desc';
        } else {
            sortBy = field;
            sortOrder = 'desc';
        }
        refresh();
    }

    function handleView(doc) {
        viewingDoc = doc;
    }

    function closeView() {
        viewingDoc = null;
    }

    function openTasks(doc) {
        taskDoc = doc;
    }

    function closeTasks() {
        taskDoc = null;
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

         <select value={sortBy} onchange={(e) => handleSort(e.target.value)} class="filter-select sort-select">
            <option value="registration_date">Sort by Date</option>
            <option value="name">Sort by Name</option>
            <option value="author">Sort by Author</option>
            <option value="status">Sort by Status</option>
            <option value="done_date">Sort by Done Date</option>
        </select>
         <button class="sort-order-btn" onclick={() => handleSort(sortBy)} title="Toggle Order">
            {sortOrder === 'desc' ? '↓' : '↑'}
        </button>
    </div>

    <div class="cards-wrapper">
        {#each documents as doc (doc.id)}
            <div class="card">
                <div class="card-header">
                     <div class="title-group">
                        <h3>{doc.name}</h3>
                        <span class="badge badge-type">{doc.type}</span>
                    </div>
                     <select
                        value={doc.status}
                        onchange={(e) => handleStatusChange(doc, e.target.value)}
                        class="status-select {doc.status}"
                    >
                        <option value="in_progress">In Progress</option>
                        <option value="done">Done</option>
                    </select>
                </div>

                {#if doc.description}
                    <div class="card-desc">
                        {doc.description}
                    </div>
                {/if}

                <div class="card-meta">
                    <div class="meta-item">
                        <span class="label">Author:</span>
                        <span class="value">{doc.author || '-'}</span>
                    </div>
                    <div class="meta-item">
                        <span class="label">Date:</span>
                        <span class="value">{doc.registration_date}</span>
                    </div>
                     {#if doc.done_date}
                        <div class="meta-item">
                            <span class="label">Done:</span>
                            <span class="value">{doc.done_date}</span>
                        </div>
                    {/if}
                </div>

                <div class="card-actions">
                     <button class="action-btn task-btn" onclick={() => openTasks(doc)} title="Tasks">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
                        Tasks
                    </button>
                    <button class="action-btn view-btn" onclick={() => handleView(doc)} title="View Content">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                        View
                    </button>
                    <button class="action-btn edit-btn" onclick={() => onEdit(doc)} title="Edit">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                        Edit
                    </button>
                    <button class="action-btn delete-btn" onclick={() => handleDelete(doc.id)} title="Delete">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        Delete
                    </button>
                </div>
            </div>
        {/each}

        {#if documents.length === 0}
            <div class="empty-state">
                <p>No documents found.</p>
            </div>
        {/if}
    </div>

    <Modal isOpen={!!viewingDoc} close={closeView} maxWidth="800px">
        <DocumentView document={viewingDoc} />
    </Modal>

    <TaskModal isOpen={!!taskDoc} close={closeTasks} document={taskDoc} />
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
        align-items: center;
    }
    @media (max-width: 768px) {
        .filters {
            flex-direction: column;
            gap: 0.75rem;
            align-items: stretch;
        }
        .search-box, .filter-select {
            width: 100%;
            min-width: 0;
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
        background-color: white;
        color: #1e293b;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .filter-select {
        padding: 0.75rem 2rem 0.75rem 1rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background-color: white;
        font-size: 0.95rem;
        color: #475569;
        cursor: pointer;
        flex-shrink: 0;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .sort-order-btn {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem;
        cursor: pointer;
        color: #475569;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }

    .cards-wrapper {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        gap: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
    }
    .title-group {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
    }
    .title-group h3 {
        margin: 0;
        font-size: 1.1rem;
        color: #1e293b;
        font-weight: 600;
    }

    .card-desc {
        color: #475569;
        font-size: 0.95rem;
        line-height: 1.5;
        /* Truncate multi-line if needed, but "multiline items" implies showing more */
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .card-meta {
        display: flex;
        gap: 1.5rem;
        font-size: 0.85rem;
        color: #64748b;
        border-top: 1px solid #f1f5f9;
        padding-top: 0.75rem;
        flex-wrap: wrap;
    }
    .meta-item {
        display: flex;
        gap: 0.25rem;
    }
    .meta-item .label {
        font-weight: 500;
    }

    .card-actions {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
        margin-top: auto;
        flex-wrap: wrap;
    }

    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
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
        font-size: 0.8rem;
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

    .action-btn {
        background-color: white;
        border: 1px solid #e2e8f0;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.85rem;
        font-weight: 500;
        color: #475569;
    }
    .action-btn:hover {
        background-color: #f8fafc;
        border-color: #cbd5e1;
    }

    .view-btn:hover { color: #3b82f6; background-color: #eff6ff; border-color: #bfdbfe; }
    .edit-btn:hover { color: #f59e0b; background-color: #fffbeb; border-color: #fde68a; }
    .delete-btn:hover { color: #ef4444; background-color: #fef2f2; border-color: #fecaca; }
    .task-btn:hover { color: #10b981; background-color: #ecfdf5; border-color: #a7f3d0; }

    .empty-state {
        padding: 3rem;
        text-align: center;
        color: #64748b;
    }
</style>
