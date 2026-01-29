<script>
    import { onMount } from 'svelte';
    import { fetchMaterials } from './api.js';

    let { 
        isOpen, 
        close, 
        filters,
        onApply 
    } = $props();
    
    let localFilters = $state({
        filterType: '',
        filterStatus: '',
        filterTag: '',
        filterAssignee: '',
        filterMaterial: '', // New: filter by material
        filterTaskTypes: [], // Array of task types: planned, pending, done
        startDate: '',
        endDate: '',
        dateField: 'registration_date',
        sortBy: 'registration_date',
        sortOrder: 'desc'
    });
    
    let materials = $state([]);
    
    // Track previous isOpen state to detect when modal opens
    let wasOpen = false;

    $effect(() => {
        // Only update when modal transitions from closed to open
        if (isOpen && !wasOpen) {
            if (filters) {
                localFilters = { ...filters };
                // Ensure filterTaskTypes is always an array
                if (!Array.isArray(localFilters.filterTaskTypes)) {
                    localFilters.filterTaskTypes = [];
                }
            }
            // Load materials when modal opens
            loadMaterials();
        }
        wasOpen = isOpen;
    });

    async function loadMaterials() {
        try {
            materials = await fetchMaterials();
        } catch (e) {
            console.error('Failed to load materials', e);
        }
    }

    function handleApply() {
        onApply(localFilters);
        close();
    }

    function handleReset() {
        localFilters = {
            filterType: '',
            filterStatus: '',
            filterTag: '',
            filterAssignee: '',
            filterMaterial: '',
            filterTaskTypes: [],
            startDate: '',
            endDate: '',
            dateField: 'registration_date',
            sortBy: 'registration_date',
            sortOrder: 'desc'
        };
    }
    
    function toggleTaskType(type) {
        if (localFilters.filterTaskTypes.includes(type)) {
            localFilters.filterTaskTypes = localFilters.filterTaskTypes.filter(t => t !== type);
        } else {
            localFilters.filterTaskTypes = [...localFilters.filterTaskTypes, type];
        }
    }
</script>

{#if isOpen}
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="modal-overlay" onclick={close}>
    <div class="modal-content" onclick={(e) => e.stopPropagation()}>
        <div class="modal-header">
            <h3>🔍 Filter Documents</h3>
            <button class="close-btn" onclick={close}>&times;</button>
        </div>

        <div class="modal-body">
            <div class="filter-section">
                <h4>Document Type</h4>
                <select bind:value={localFilters.filterType} class="filter-input">
                    <option value="">All Types</option>
                    <option value="plan">Plan</option>
                    <option value="mail">Mail</option>
                    <option value="other">Other</option>
                </select>
            </div>

            <div class="filter-section">
                <h4>Status</h4>
                <select bind:value={localFilters.filterStatus} class="filter-input">
                    <option value="">All Statuses</option>
                    <option value="in_progress">In Progress</option>
                    <option value="done">Done</option>
                </select>
            </div>

            <div class="filter-section">
                <h4>Tag</h4>
                <input
                    type="text"
                    placeholder="Filter by tag..."
                    bind:value={localFilters.filterTag}
                    class="filter-input"
                />
            </div>

            <div class="filter-section">
                <h4>Assignee</h4>
                <input
                    type="text"
                    placeholder="Filter by assignee..."
                    bind:value={localFilters.filterAssignee}
                    class="filter-input"
                />
            </div>

            <div class="filter-section">
                <h4>Material</h4>
                <select bind:value={localFilters.filterMaterial} class="filter-input">
                    <option value="">All Materials</option>
                    {#each materials as material}
                        <option value={material.id}>{material.name}</option>
                    {/each}
                </select>
            </div>

            <div class="filter-section">
                <h4>Task Types (Show documents with these task types)</h4>
                <div class="checkbox-group">
                    <label class="checkbox-label">
                        <input
                            type="checkbox"
                            checked={localFilters.filterTaskTypes.includes('planned')}
                            onchange={() => toggleTaskType('planned')}
                        />
                        <span class="checkbox-text">Planned</span>
                    </label>
                    <label class="checkbox-label">
                        <input
                            type="checkbox"
                            checked={localFilters.filterTaskTypes.includes('pending')}
                            onchange={() => toggleTaskType('pending')}
                        />
                        <span class="checkbox-text">Pending</span>
                    </label>
                    <label class="checkbox-label">
                        <input
                            type="checkbox"
                            checked={localFilters.filterTaskTypes.includes('done')}
                            onchange={() => toggleTaskType('done')}
                        />
                        <span class="checkbox-text">Done</span>
                    </label>
                </div>
            </div>

            <div class="filter-section">
                <h4>Date Range</h4>
                <select bind:value={localFilters.dateField} class="filter-input">
                    <option value="registration_date">Registration Date</option>
                    <option value="done_date">Done Date</option>
                </select>
                <div class="date-range">
                    <input 
                        type="date" 
                        bind:value={localFilters.startDate} 
                        class="filter-input"
                        placeholder="Start Date"
                    />
                    <span class="date-separator">to</span>
                    <input 
                        type="date" 
                        bind:value={localFilters.endDate} 
                        class="filter-input"
                        placeholder="End Date"
                    />
                </div>
            </div>

            <div class="filter-section">
                <h4>Sort By</h4>
                <div class="sort-controls">
                    <select bind:value={localFilters.sortBy} class="filter-input">
                        <option value="registration_date">Date</option>
                        <option value="name">Name</option>
                        <option value="author">Author</option>
                        <option value="status">Status</option>
                        <option value="done_date">Done Date</option>
                    </select>
                    <button 
                        class="sort-order-btn" 
                        onclick={() => localFilters.sortOrder = localFilters.sortOrder === 'desc' ? 'asc' : 'desc'}
                        title="Toggle sort order"
                    >
                        {localFilters.sortOrder === 'desc' ? '↓ Desc' : '↑ Asc'}
                    </button>
                </div>
            </div>
        </div>

        <div class="modal-footer">
            <button class="btn-secondary" onclick={handleReset}>Reset All</button>
            <button class="btn-primary" onclick={handleApply}>Apply Filters</button>
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
        border-radius: 12px;
        width: 100%;
        max-width: 600px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
    }
    
    .modal-header {
        padding: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        background: white;
        z-index: 1;
    }
    
    .modal-header h3 {
        margin: 0;
        font-size: 1.25rem;
        color: #1e293b;
        font-weight: 600;
    }
    
    .close-btn {
        background: none;
        border: none;
        font-size: 1.5rem;
        color: #64748b;
        cursor: pointer;
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
    }
    
    .close-btn:hover {
        background: #f1f5f9;
    }
    
    .modal-body {
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }
    
    .filter-section {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .filter-section h4 {
        margin: 0;
        font-size: 0.95rem;
        font-weight: 600;
        color: #475569;
    }
    
    .filter-input {
        padding: 0.75rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        font-size: 0.95rem;
        font-family: inherit;
        transition: border-color 0.2s;
    }
    
    .filter-input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    .checkbox-group {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .checkbox-label {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        cursor: pointer;
        padding: 0.5rem;
        border-radius: 6px;
        transition: background-color 0.2s;
    }
    
    .checkbox-label:hover {
        background-color: #f8fafc;
    }
    
    .checkbox-label input[type="checkbox"] {
        width: 18px;
        height: 18px;
        cursor: pointer;
    }
    
    .checkbox-text {
        font-size: 0.95rem;
        color: #475569;
        font-weight: 500;
    }
    
    .date-range {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .date-separator {
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .sort-controls {
        display: flex;
        gap: 0.75rem;
    }
    
    .sort-controls .filter-input {
        flex: 1;
    }
    
    .sort-order-btn {
        padding: 0.75rem 1rem;
        border: 1px solid #e2e8f0;
        background: white;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
    }
    
    .sort-order-btn:hover {
        background: #f8fafc;
        border-color: #cbd5e1;
    }
    
    .modal-footer {
        padding: 1.5rem;
        border-top: 1px solid #e2e8f0;
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        position: sticky;
        bottom: 0;
        background: white;
    }
    
    button {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        border: none;
        font-size: 0.95rem;
        transition: all 0.2s;
    }
    
    .btn-primary {
        background: #3b82f6;
        color: white;
    }
    
    .btn-primary:hover {
        background: #2563eb;
    }
    
    .btn-secondary {
        background: #f1f5f9;
        color: #475569;
    }
    
    .btn-secondary:hover {
        background: #e2e8f0;
    }
</style>
