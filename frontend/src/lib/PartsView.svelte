<script>
    import { onMount } from "svelte";
    import { fetchParts, fetchMaterials } from "./api";
    import PartThumbnail from "./components/PartThumbnail.svelte";

    // State
    let parts = $state([]);
    let materials = $state([]);

    // Filter State
    let search = $state("");
    let selectedMaterial = $state("");
    let minWidth = $state("");
    let maxWidth = $state("");
    let minHeight = $state("");
    let maxHeight = $state("");

    let loading = $state(false);
    let currentPage = $state(0);
    const limit = 50;

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
            <label>Width (mm)</label>
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
            <label>Height (mm)</label>
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
            <h2>Parts Library</h2>
            <div class="actions">
                <button onclick={() => loadData()}>↻ Refresh</button>
            </div>
        </header>

        {#if loading}
            <div class="loading">Loading parts...</div>
        {:else if parts.length === 0}
            <div class="empty">No parts found matching filters.</div>
        {:else}
            <div class="grid">
                {#each parts as part (part.id)}
                    <PartThumbnail
                        {part}
                        onclick={() => console.log("Part clicked", part.id)}
                    />
                {/each}
            </div>
        {/if}
    </main>
</div>

<style>
    .parts-layout {
        display: flex;
        height: 100%;
        gap: 20px;
        padding: 20px;
        box-sizing: border-box;
    }

    .sidebar {
        width: 250px;
        flex-shrink: 0;
        background: var(--bg-surface, #fff);
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        height: fit-content;
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
        overflow: hidden;
    }

    header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }

    h2 {
        margin: 0;
    }

    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 20px;
        overflow-y: auto;
        padding-bottom: 20px;
    }

    .loading,
    .empty {
        text-align: center;
        padding: 40px;
        color: #666;
    }
</style>
