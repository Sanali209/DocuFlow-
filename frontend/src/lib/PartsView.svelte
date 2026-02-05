<script>
    import { onMount } from "svelte";
    import {
        fetchParts,
        fetchMaterials,
        scanParts,
        updatePart,
        getParts,
    } from "./api";
    import { appState, addToTray } from "./appState.svelte.js";
    import PartThumbnail from "./components/PartThumbnail.svelte";
    import Tray from "./components/Tray.svelte";
    import ScanProgressModal from "./ScanProgressModal.svelte";
    import PartEditModal from "./PartEditModal.svelte";
    import PartPreviewModal from "./PartPreviewModal.svelte";
    import { push } from "./Router.svelte"; // Import router push

    // State
    let parts = $state([]);
    let materials = $state([]);
    let error = $state(null);

    // Filter State
    let search = $state("");
    let selectedMaterial = $state("");
    let minWidth = $state("");
    let maxWidth = $state("");
    let minHeight = $state("");
    let maxHeight = $state("");

    let loading = $state(false);
    let viewMode = $state("grid"); // "grid" or "list"
    let currentPage = $state(0);
    const limit = 50;

    // Modal states
    let showScanModal = $state(false);
    let scanProgress = $state(0);
    let scanStatus = $state("");
    let scanMessage = $state("");

    let showEditModal = $state(false);
    let editingPart = $state(null);

    // Preview state
    let showPreviewModal = $state(false);
    let previewPart = $state(null);

    async function loadData() {
        loading = true;
        try {
            // Build filter object
            const filters = {};
            if (search) filters.search = search;
            if (selectedMaterial) filters.material_id = selectedMaterial;
            if (minWidth) filters.min_width = minWidth;
            if (maxWidth) filters.max_width = maxWidth;
            if (minHeight) filters.min_height = minHeight;
            if (maxHeight) filters.max_height = maxHeight;

            const [partsData, matData] = await Promise.all([
                fetchParts(currentPage * limit, limit, filters),
                // Only load materials once if empty
                materials.length === 0
                    ? fetchMaterials()
                    : Promise.resolve(materials),
            ]);

            parts = partsData;
            if (materials.length === 0) materials = matData;
        } catch (e) {
            console.error(e);
            alert("Failed to load parts");
        } finally {
            loading = false;
        }
    }

    function handleFilterChange() {
        currentPage = 0;
        loadData();
    }

    // Debounce search
    let timeout;
    function handleSearchInput() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            handleFilterChange();
        }, 500);
    }

    async function startScan() {
        showScanModal = true;
        scanProgress = 0;
        scanStatus = "starting";
        scanMessage = "Initializing scan...";

        try {
            await scanParts((update) => {
                scanProgress = update.percent || 0;
                scanStatus = update.status || "";
                scanMessage = update.message || "";
            });

            // Reload parts after scan completes
            if (scanStatus === "complete") {
                await loadData();
            }
        } catch (e) {
            console.error("Scan error:", e);
            scanStatus = "error";
            scanMessage = `Scan failed: ${e.message}`;
        }
    }

    function handleEdit(event) {
        editingPart = event.detail; // Changed to match event detail for custom event or direct arg
        // PartThumbnail dispatches standard 'onedit' with part as argument in custom logic or event detail?
        // Let's check PartThumbnail dispatch.
        // It calls onedit(part). In Svelte 5 props, this is a function call.
        // So handleEdit(part).
        // Wait, if it's passed as prop onedit={handleEdit}, it receives 'part'.
        // Previous code treated it as event? No, updatePart logic suggests editingPart is the object.
        // Let's standardise: onedit={(p) => handleEdit(p)} in template or matching sig.
        // In template: `onedit={handleEdit}` implies handleEdit(part).
    }

    // Correcting handleEdit for prop usage
    function onEditPart(part) {
        editingPart = part;
        showEditModal = true;
    }

    function handlePreview(part) {
        previewPart = part;
        showPreviewModal = true;
    }

    function handleFilterInDocs(part) {
        // Navigate to documents with part search
        push(`/documents?part_search=${encodeURIComponent(part.name)}`);
        // Note: Router.push might not trigger full reload if it just changes state,
        // but DocumentList needs to react to it.
        // If DocumentList is already mounted, it might need to watch for route changes or query params.
        // But commonly in SPA, this unmounts PartsView and mounts DocumentList.
    }

    async function handleSavePart(updatedPart) {
        try {
            await updatePart(editingPart.id, updatedPart);
            await loadData();
            alert("Part updated successfully");
            showEditModal = false;
        } catch (e) {
            console.error("Update error:", e);
            alert("Failed to update part");
        }
    }

    onMount(() => {
        loadData();
    });
</script>

<div class="parts-layout">
    <aside class="sidebar">
        <h3>Filters</h3>

        <div class="filter-group">
            <label for="search">Search</label>
            <input
                id="search"
                type="text"
                placeholder="Name or Reg #"
                bind:value={search}
                oninput={handleSearchInput}
            />
        </div>

        <div class="filter-group">
            <label for="material">Material</label>
            <select
                id="material"
                bind:value={selectedMaterial}
                onchange={handleFilterChange}
            >
                <option value="">All Materials</option>
                {#each materials as mat}
                    <option value={mat.id}>{mat.name}</option>
                {/each}
            </select>
        </div>

        <div class="filter-group">
            <span class="filter-label">Width (mm)</span>
            <div class="range">
                <input
                    type="number"
                    placeholder="Min"
                    bind:value={minWidth}
                    onchange={handleFilterChange}
                />
                <span>-</span>
                <input
                    type="number"
                    placeholder="Max"
                    bind:value={maxWidth}
                    onchange={handleFilterChange}
                />
            </div>
        </div>

        <div class="filter-group">
            <span class="filter-label">Height (mm)</span>
            <div class="range">
                <input
                    type="number"
                    placeholder="Min"
                    bind:value={minHeight}
                    onchange={handleFilterChange}
                />
                <span>-</span>
                <input
                    type="number"
                    placeholder="Max"
                    bind:value={maxHeight}
                    onchange={handleFilterChange}
                />
            </div>
        </div>

        <button
            class="reset-btn"
            onclick={() => {
                search = "";
                selectedMaterial = "";
                minWidth = "";
                maxWidth = "";
                minHeight = "";
                maxHeight = "";
                handleFilterChange();
            }}>Reset Filters</button
        >
    </aside>

    <main class="content">
        <header>
            <div class="title-row">
                <h2>Parts Library</h2>
            </div>
            <div class="actions">
                <button onclick={startScan}>🔄 Rescan Library</button>
                <button onclick={() => loadData()}>↻ Refresh</button>
            </div>
        </header>

        {#if loading}
            <div class="loading">Loading parts...</div>
        {:else if parts.length === 0}
            <div class="empty">No parts found matching filters.</div>
        {:else}
            <div class="grid {viewMode}">
                {#each parts as part (part.id)}
                    <PartThumbnail
                        {part}
                        onclick={() => addToTray(part)}
                        onedit={onEditPart}
                        onpreview={handlePreview}
                        onfilter={handleFilterInDocs}
                    />
                {/each}
            </div>
        {/if}
    </main>

    <ScanProgressModal
        bind:show={showScanModal}
        status={scanStatus}
        message={scanMessage}
        progress={scanProgress}
    />

    <PartEditModal
        bind:show={showEditModal}
        part={editingPart}
        onsave={handleSavePart}
    />

    <PartPreviewModal bind:show={showPreviewModal} part={previewPart} />

    <Tray />
</div>

<style>
    .parts-layout {
        display: flex;
        height: calc(
            100vh - 40px
        ); /* Fill screen height minus some space if needed */
        gap: 20px;
        padding: 20px;
        box-sizing: border-box;
        overflow: hidden; /* Prevent parent scrolling */
    }

    .sidebar {
        width: 250px;
        flex-shrink: 0;
        background: var(--bg-surface, #fff);
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        height: 100%; /* Sidebar takes full height */
        overflow-y: auto; /* Sidebar has its own scroll if needed */
    }

    .sidebar h3 {
        margin-top: 0;
        margin-bottom: 20px;
    }

    .filter-group {
        margin-bottom: 15px;
    }

    .filter-group label {
        display: block;
        margin-bottom: 5px;
        font-weight: 500;
        font-size: 0.9rem;
    }

    .filter-group input,
    .filter-group select {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-sizing: border-box;
    }

    .range {
        display: flex;
        gap: 5px;
        align-items: center;
    }

    .range input {
        width: calc(50% - 10px);
    }

    label,
    .filter-label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #475569;
        font-size: 0.9rem;
    }

    .reset-btn {
        width: 100%;
        padding: 8px;
        background: #f0f0f0;
        border: 1px solid #ddd;
        border-radius: 4px;
        cursor: pointer;
    }

    .reset-btn:hover {
        background: #ddd;
    }

    .content {
        flex: 1;
        display: flex;
        flex-direction: column;
        max-height: 100%;
        min-height: 0;
    }

    header {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-bottom: 20px;
    }

    .title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .actions {
        display: flex;
        gap: 10px;
    }

    h2 {
        margin: 0;
    }

    .grid {
        display: grid;
        gap: 15px;
        overflow-y: auto;
        padding-bottom: 20px;
        flex: 1;
        min-height: 0;
        grid-template-columns: 1fr;
    }

    .loading,
    .empty {
        text-align: center;
        padding: 40px;
        color: #666;
    }
</style>
