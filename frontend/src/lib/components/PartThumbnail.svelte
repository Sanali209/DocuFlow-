<script>
    import { onMount } from "svelte";

    // Props: part
    let { part, onclick, onedit, onpreview } = $props();

    let materialName = $derived(
        part.material ? part.material.name : "Unknown Material",
    );
    let dims = $derived(`${part.width || "?"} x ${part.height || "?"}`);

    function handleEdit(e) {
        e.stopPropagation();
        if (onedit) {
            onedit(part);
        }
    }

    function handlePreview(e) {
        e.stopPropagation();
        if (onpreview) {
            onpreview(part);
        }
    }
</script>

<div
    class="thumbnail card"
    role="button"
    tabindex="0"
    {onclick}
    onkeydown={(e) => e.key === "Enter" && onclick && onclick()}
>
    <div class="preview">
        {#if part.gnc_file_path}
            <img
                src="/uploads/thumbnails/{part.registration_number ||
                    part.id}.svg"
                alt={part.name}
                class="thumbnail-img"
                onerror={(e) => {
                    // @ts-ignore
                    e.currentTarget.style.display = "none";
                }}
            />
        {/if}
        <div
            class="placeholder-geo"
            style={part.gnc_file_path ? "display: none;" : ""}
        >
            <span>⚙️</span>
        </div>

        <div class="overlay-actions">
            <button class="action-btn" onclick={handleEdit} title="Edit Part"
                >✏️</button
            >
            <button class="action-btn" onclick={handlePreview} title="Preview"
                >👁️</button
            >
        </div>
    </div>
    <div class="info">
        <h4 class="name" title={part.name}>{part.name}</h4>

        <div class="card-meta">
            <div class="meta-item">
                <span class="label">Registration:</span>
                <span class="value">{part.registration_number || "-"}</span>
            </div>
            <div class="meta-item">
                <span class="label">Dimensions:</span>
                <span class="value">{dims} mm</span>
            </div>
            <div class="meta-item">
                <span class="label">Material:</span>
                <span class="value">{materialName}</span>
            </div>
        </div>
    </div>
</div>

<style>
    .thumbnail {
        background: white;
        border: 1px solid #eee;
        border-radius: 8px;
        overflow: hidden;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        position: relative; /* Ensure absolute children are contained */
        height: auto; /* Let content dictate height */
        min-height: 140px;
        flex-direction: row;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        gap: 1.5rem;
        align-items: flex-start;
        border: 1px solid #e2e8f0;
    }

    .thumbnail:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-color: #cbd5e1;
    }

    .preview {
        height: 120px;
        width: 150px;
        background: #1e1e1e;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        border-radius: 8px;
    }

    .placeholder-geo {
        font-size: 3rem;
        opacity: 0.3;
        filter: grayscale(1);
    }

    .thumbnail-img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }

    /* Info Section */
    .info {
        padding: 0;
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    /* Name Styles */
    .name {
        margin: 0 0 5px 0;
        font-size: 1.1rem;
        font-weight: 600;
        white-space: normal;
        overflow: hidden;
        text-overflow: ellipsis;
        color: #0f172a;
        width: auto;
    }

    /* Card Meta */
    .card-meta {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
        background: #f8fafc;
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid #f1f5f9;
        width: 100%; /* Ensure it fills container */
    }

    .meta-item {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .meta-item .label {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
    }

    .meta-item .value {
        font-size: 0.9rem;
        color: #1e293b;
        font-weight: 600;
    }

    /* Overlay Actions */
    .overlay-actions {
        position: absolute;
        bottom: 8px;
        left: 8px;
        display: flex;
        gap: 6px;
        opacity: 0; /* Hidden by default */
        transition: opacity 0.2s;
    }

    .thumbnail:hover .overlay-actions {
        opacity: 1;
    }

    .action-btn {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 14px;
        padding: 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.2s;
    }

    .action-btn:hover {
        background: #f1f5f9;
        border-color: #cbd5e1;
        transform: translateY(-1px);
    }

    .reg {
        font-family: monospace;
    }
</style>
