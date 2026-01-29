<script>
    import {
        fetchDocuments,
        updateDocumentStatus,
        deleteDocument,
        fetchFilterPresets,
        createFilterPreset,
        deleteFilterPreset,
        updateJournalEntry
    } from './api.js';
    import Modal from './Modal.svelte';
    import DocumentView from './DocumentView.svelte';
    import DocumentTasks from './DocumentTasks.svelte';
    import JournalEntryModal from './JournalEntryModal.svelte';
    import ImagePreviewModal from './ImagePreviewModal.svelte';
    import FilterModal from './FilterModal.svelte';
    import TagInput from './TagInput.svelte';
    import { onMount } from 'svelte';

    let documents = $state([]);
    let search = $state('');
    let filterType = $state('');
    let filterStatus = $state('');
    let filterTag = $state('');
    let filterAssignee = $state('');
    let filterTaskTypes = $state([]);
    let startDate = $state('');
    let endDate = $state('');
    let dateField = $state('registration_date');
    let presets = $state([]);

    let viewingDoc = $state(null);
    let journalDoc = $state(null);
    let editingEntry = $state(null);
    let previewAttachments = $state(null);
    let isFilterModalOpen = $state(false);
    let sortBy = $state('registration_date');
    let sortOrder = $state('desc');
    let { onEdit } = $props();

    export async function refresh() {
        let docs = await fetchDocuments(search, filterType, filterStatus, sortBy, sortOrder, filterTag, startDate, endDate, dateField, filterAssignee);
        
        // Client-side filtering by task types if specified
        if (filterTaskTypes && filterTaskTypes.length > 0) {
            docs = docs.filter(doc => {
                if (!doc.tasks || doc.tasks.length === 0) return false;
                // Check if document has any tasks with the selected types
                return doc.tasks.some(task => filterTaskTypes.includes(task.status));
            });
        }
        
        documents = docs;
    }

    async function loadPresets() {
        presets = await fetchFilterPresets();
    }

    onMount(() => {
        refresh();
        loadPresets();
    });

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

    function openJournalEntry(doc) {
        journalDoc = doc;
        editingEntry = null;
    }

    function openEditEntry(doc, entry) {
        journalDoc = doc;
        editingEntry = entry;
    }

    function closeJournalEntry() {
        journalDoc = null;
        editingEntry = null;
        refresh();
    }

    async function toggleNoteStatus(entryId, currentStatus) {
        const newStatus = currentStatus === 'pending' ? 'done' : 'pending';
        try {
            await updateJournalEntry(entryId, { status: newStatus });
            refresh();
            // Dispatch event to refresh journal view
            window.dispatchEvent(new CustomEvent('journal-entries-updated'));
        } catch (e) {
            console.error('Failed to update note status', e);
        }
    }

    function openImagePreview(attachments) {
        previewAttachments = attachments;
    }

    function closeImagePreview() {
        previewAttachments = null;
    }

    function getTaskCounts(tasks) {
        if (!tasks) return null;
        const counts = { planned: 0, pending: 0, done: 0 };
        tasks.forEach(t => {
            if (counts[t.status] !== undefined) counts[t.status]++;
        });
        return counts;
    }

    function getJournalCounts(entries) {
        if (!entries) return null;
        const counts = { info: 0, warning: 0, error: 0 };
        entries.forEach(e => {
            if (counts[e.type] !== undefined) counts[e.type]++;
        });
        return counts;
    }

    async function savePreset() {
        const name = prompt("Enter a name for this filter preset:");
        if (!name) return;

        const config = JSON.stringify({
            search, filterType, filterStatus, filterTag, filterAssignee, filterTaskTypes, startDate, endDate, dateField, sortBy, sortOrder
        });

        try {
            await createFilterPreset({ name, config });
            await loadPresets();
            alert("Preset saved!");
        } catch (e) {
            console.error(e);
            alert("Failed to save preset");
        }
    }

    async function loadPreset(configStr) {
        if (!configStr) return;
        try {
            const config = JSON.parse(configStr);
            search = config.search || '';
            filterType = config.filterType || '';
            filterStatus = config.filterStatus || '';
            filterTag = config.filterTag || '';
            filterAssignee = config.filterAssignee || '';
            filterTaskTypes = config.filterTaskTypes || [];
            startDate = config.startDate || '';
            endDate = config.endDate || '';
            dateField = config.dateField || 'registration_date';
            sortBy = config.sortBy || 'registration_date';
            sortOrder = config.sortOrder || 'desc';
            refresh();
        } catch (e) {
            console.error("Failed to parse preset", e);
        }
    }

    async function removePreset(id, e) {
        e.stopPropagation(); // prevent selection change
        if(!confirm("Delete this preset?")) return;
        try {
            await deleteFilterPreset(id);
            await loadPresets();
        } catch(e) {
            console.error(e);
        }
    }

    function openFilterModal() {
        isFilterModalOpen = true;
    }

    function closeFilterModal() {
        isFilterModalOpen = false;
    }

    function applyFilters(newFilters) {
        filterType = newFilters.filterType;
        filterStatus = newFilters.filterStatus;
        filterTag = newFilters.filterTag;
        filterAssignee = newFilters.filterAssignee;
        filterTaskTypes = newFilters.filterTaskTypes || [];
        startDate = newFilters.startDate;
        endDate = newFilters.endDate;
        dateField = newFilters.dateField;
        sortBy = newFilters.sortBy;
        sortOrder = newFilters.sortOrder;
        refresh();
    }
</script>

<div class="list-container">
    <div class="filters-bar">
        <div class="main-filters">
            <div class="search-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <input
                    type="text"
                    placeholder="Search documents..."
                    bind:value={search}
                    oninput={handleSearch}
                />
            </div>

            <button class="filter-btn" onclick={openFilterModal} title="Filter & Sort">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                </svg>
                Filters
                {#if filterType || filterStatus || filterTag || filterAssignee || startDate || endDate || (filterTaskTypes && filterTaskTypes.length > 0)}
                    <span class="filter-badge">●</span>
                {/if}
            </button>
        </div>
    </div>

    <div class="cards-wrapper">
        {#each documents as doc (doc.id)}
            {@const taskCounts = getTaskCounts(doc.tasks)}
            {@const journalCounts = getJournalCounts(doc.journal_entries)}

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

                {#if doc.tags && doc.tags.length > 0}
                    <div class="tags-row">
                        {#each doc.tags as tag}
                            <span class="tag-badge">#{tag.name}</span>
                        {/each}
                    </div>
                {/if}

                <div class="badges-row">
                    {#if doc.attachments && doc.attachments.length > 0}
                        <button class="icon-badge attachment-badge" onclick={() => openImagePreview(doc.attachments)} title="View Attachments">
                            📷 {doc.attachments.length}
                        </button>
                    {/if}

                    {#if taskCounts}
                        {#if taskCounts.planned > 0}<span class="icon-badge task-planned" title="Planned Tasks">📅 {taskCounts.planned}</span>{/if}
                        {#if taskCounts.pending > 0}<span class="icon-badge task-pending" title="Pending Tasks">⏳ {taskCounts.pending}</span>{/if}
                        {#if taskCounts.done > 0}<span class="icon-badge task-done" title="Completed Tasks">✅ {taskCounts.done}</span>{/if}
                    {/if}

                    {#if journalCounts}
                        {#if journalCounts.info > 0}<span class="icon-badge journal-info" title="Info Notes">ℹ️ {journalCounts.info}</span>{/if}
                        {#if journalCounts.warning > 0}<span class="icon-badge journal-warning" title="Warnings">⚠️ {journalCounts.warning}</span>{/if}
                        {#if journalCounts.error > 0}<span class="icon-badge journal-error" title="Errors">❌ {journalCounts.error}</span>{/if}
                    {/if}
                </div>

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

                <DocumentTasks document={doc} refresh={refresh} filterAssignee={filterAssignee} />

                {#if doc.journal_entries && doc.journal_entries.length > 0}
                    <div class="embedded-notes">
                        <h4>Notes</h4>
                        <div class="notes-list">
                            {#each doc.journal_entries as entry}
                                <div class="note-item {entry.type}">
                                    <div class="note-header">
                                        <span class="note-badge {entry.type}">{entry.type}</span>
                                        <span class="note-author">{entry.author || 'Unknown'}</span>
                                        <span class="note-date">{entry.created_at}</span>
                                        <button 
                                            class="note-edit-btn"
                                            onclick={() => openEditEntry(doc, entry)}
                                            title="Edit note"
                                        >
                                            ✏️
                                        </button>
                                        <button 
                                            class="note-status-btn {entry.status}"
                                            onclick={() => toggleNoteStatus(entry.id, entry.status)}
                                            title={entry.status === 'pending' ? 'Click to mark as done' : 'Click to mark as pending'}
                                        >
                                            {entry.status}
                                        </button>
                                    </div>
                                    <p class="note-text">{entry.text}</p>
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}

                <div class="card-actions">
                     <button class="action-btn" onclick={() => openJournalEntry(doc)} title="Add Note">
                        📝 Add Note
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

    <JournalEntryModal
        isOpen={!!journalDoc}
        close={closeJournalEntry}
        documentId={journalDoc?.id}
        documentName={journalDoc?.name}
        entry={editingEntry}
    />

    <ImagePreviewModal
        isOpen={!!previewAttachments}
        close={closeImagePreview}
        attachments={previewAttachments || []}
    />

    <FilterModal
        isOpen={isFilterModalOpen}
        close={closeFilterModal}
        filters={{
            filterType,
            filterStatus,
            filterTag,
            filterAssignee,
            filterTaskTypes,
            startDate,
            endDate,
            dateField,
            sortBy,
            sortOrder
        }}
        onApply={applyFilters}
    />
</div>

<style>
    .list-container {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }
    .filters-bar {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .main-filters, .advanced-filters {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        align-items: center;
    }
    .main-filters {
        justify-content: space-between;
    }

    @media (max-width: 768px) {
        .main-filters, .advanced-filters {
            flex-direction: column;
            align-items: stretch;
        }
        .search-box, .filter-btn {
            width: 100%;
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
        padding: 0.6rem 0.6rem 0.6rem 2.2rem;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        font-size: 0.95rem;
    }

    .filter-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.6rem 1rem;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        font-size: 0.95rem;
        font-weight: 500;
        color: #475569;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
    }
    .filter-btn:hover {
        background: #f8fafc;
        border-color: #cbd5e1;
    }
    .filter-badge {
        color: #3b82f6;
        font-size: 1.2rem;
        line-height: 1;
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

    .tags-row {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .tag-badge {
        background: #e0e7ff;
        color: #3730a3;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .badges-row {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .icon-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
        cursor: default;
    }
    button.icon-badge {
        cursor: pointer;
    }
    button.icon-badge:hover {
        background: #e2e8f0;
        transform: scale(1.05);
    }
    .attachment-badge { background: #f0f9ff; color: #0284c7; border-color: #bae6fd; font-weight: 600; }
    .task-planned { background: #e0e7ff; color: #3730a3; border-color: #c7d2fe; }
    .task-pending { background: #ffedd5; color: #9a3412; border-color: #fed7aa; }
    .task-done { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
    .journal-info { background: #dbeafe; color: #1e40af; border-color: #bfdbfe; }
    .journal-warning { background: #fef3c7; color: #92400e; border-color: #fde68a; }
    .journal-error { background: #fee2e2; color: #991b1b; border-color: #fecaca; }

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

    .embedded-notes {
        border-top: 1px solid #f1f5f9;
        margin-top: 1rem;
        padding-top: 1rem;
    }
    .embedded-notes h4 {
        margin: 0 0 0.75rem 0;
        font-size: 0.95rem;
        color: #475569;
        font-weight: 600;
    }
    .notes-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    .note-item {
        background: #f8fafc;
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 3px solid #ccc;
        font-size: 0.9rem;
    }
    .note-item.info { border-left-color: #3b82f6; }
    .note-item.warning { border-left-color: #f59e0b; }
    .note-item.error { border-left-color: #ef4444; }

    .note-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.4rem;
        flex-wrap: wrap;
    }
    .note-badge {
        font-size: 0.7rem;
        text-transform: uppercase;
        font-weight: bold;
        padding: 0.1rem 0.4rem;
        border-radius: 4px;
        color: white;
    }
    .note-badge.info { background: #3b82f6; }
    .note-badge.warning { background: #f59e0b; }
    .note-badge.error { background: #ef4444; }

    .note-author {
        font-weight: 600;
        color: #1e293b;
    }
    .note-date, .note-status {
        color: #64748b;
        font-size: 0.8rem;
    }
    .note-edit-btn {
        padding: 0.15rem 0.4rem;
        border: none;
        background: transparent;
        cursor: pointer;
        font-size: 0.9rem;
        border-radius: 4px;
        transition: background 0.2s;
    }
    .note-edit-btn:hover {
        background: #f1f5f9;
    }
    .note-edit-btn:focus-visible {
        outline: 2px solid #3b82f6;
        outline-offset: 2px;
    }
    .note-status-btn {
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: capitalize;
        cursor: pointer;
        border: 1px solid;
        margin-left: auto;
        transition: all 0.2s;
    }
    .note-status-btn:focus-visible {
        outline: 2px solid #3b82f6;
        outline-offset: 2px;
    }
    .note-status-btn.pending {
        background: #fff7ed;
        color: #c2410c;
        border-color: #fed7aa;
    }
    .note-status-btn.pending:hover {
        background: #ffedd5;
        transform: scale(1.05);
    }
    .note-status-btn.done {
        background: #f0fdf4;
        color: #15803d;
        border-color: #bbf7d0;
    }
    .note-status-btn.done:hover {
        background: #dcfce7;
        transform: scale(1.05);
    }
    .note-text {
        margin: 0;
        color: #334155;
        white-space: pre-wrap;
    }

    /* Mobile optimization - reduce spacing and font sizes */
    @media (max-width: 640px) {
        .card {
            border-radius: 8px;
            padding: 0.75rem;
            gap: 0.5rem;
        }
        .card-header {
            gap: 0.5rem;
        }
        .title-group h3 {
            font-size: 0.95rem;
        }
        .card-desc {
            font-size: 0.85rem;
        }
        .badge {
            font-size: 0.7rem;
            padding: 0.2rem 0.4rem;
        }
        .tags-row {
            gap: 0.25rem;
        }
        .tag-badge {
            font-size: 0.7rem;
            padding: 0.15rem 0.4rem;
        }
        .badges-row {
            gap: 0.25rem;
        }
        .icon-badge {
            font-size: 0.7rem;
            padding: 0.2rem 0.4rem;
        }
        .card-meta {
            gap: 0.75rem;
            font-size: 0.8rem;
        }
        .card-actions {
            gap: 0.25rem;
        }
        .action-btn {
            padding: 0.3rem 0.6rem;
            font-size: 0.8rem;
        }
        .embedded-notes {
            margin-top: 0.5rem;
            padding-top: 0.5rem;
        }
        .embedded-notes h4 {
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
        }
        .notes-list {
            gap: 0.5rem;
        }
        .note-item {
            padding: 0.5rem;
            border-radius: 6px;
            border-left-width: 2px;
            font-size: 0.8rem;
        }
        .note-header {
            gap: 0.25rem;
            margin-bottom: 0.25rem;
        }
        .note-badge {
            font-size: 0.65rem;
        }
        .note-author {
            font-size: 0.8rem;
        }
        .note-date {
            font-size: 0.75rem;
        }
        .note-status-btn {
            font-size: 0.7rem;
            padding: 0.125rem 0.4rem;
        }
    }
</style>
