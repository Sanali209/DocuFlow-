<script>
    import { onMount } from "svelte";

    // Props: part
    let { part, onclick } = $props();

    // Logic to possibly render SVG from stats or use default
    // We can assume parts have 'gnc_file_path'.
    // Or we show dimensions.

    let materialName = $derived(
        part.material ? part.material.name : "Unknown Material",
    );
    let dims = $derived(`${part.width || "?"} x ${part.height || "?"}`);
</script>

<div
    class="thumbnail"
    role="button"
    tabindex="0"
    {onclick}
    onkeydown={(e) => e.key === "Enter" && onclick && onclick()}
>
    <div class="preview">
        <!-- Placeholder for actual Geometry Preview -->
        <div class="placeholder-geo">
            <span>⚙️</span>
        </div>
        <div class="stats-overlay">
            {dims}
        </div>
    </div>
    <div class="info">
        <h4 class="name" title={part.name}>{part.name}</h4>
        <div class="details">
            <span class="reg">{part.registration_number || "No Reg"}</span>
            <span class="material">{materialName}</span>
        </div>
    </div>
</div>

<style>
    .thumbnail {
        border: 1px solid var(--border-color, #ccc);
        border-radius: 8px;
        background: var(--bg-surface, #fff);
        width: 100%;
        max-width: 250px;
        cursor: pointer;
        transition:
            transform 0.2s,
            box-shadow 0.2s;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .thumbnail:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: var(--primary-color, #007bff);
    }

    .preview {
        height: 150px;
        background: #f5f5f5;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .placeholder-geo {
        font-size: 3rem;
        opacity: 0.3;
        filter: grayscale(1);
    }

    .stats-overlay {
        position: absolute;
        bottom: 5px;
        right: 5px;
        background: rgba(0, 0, 0, 0.6);
        color: white;
        font-size: 0.75rem;
        padding: 2px 6px;
        border-radius: 4px;
    }

    .info {
        padding: 10px;
    }

    .name {
        margin: 0 0 5px 0;
        font-size: 1rem;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: var(--text-primary, #333);
    }

    .details {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        color: var(--text-secondary, #666);
    }

    .reg {
        font-family: monospace;
    }
</style>
