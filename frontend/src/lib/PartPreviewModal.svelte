<script>
    let { show = $bindable(false), part } = $props();

    function close() {
        show = false;
    }

    function handleKeydown(e) {
        if (e.key === "Escape") {
            close();
        }
    }
</script>

{#if show && part}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="modal-backdrop" onclick={close}>
        <div class="modal" onclick={(e) => e.stopPropagation()}>
            <header>
                <h3>{part.name}</h3>
                <button class="close-btn" onclick={close}>&times;</button>
            </header>
            <div class="content">
                {#if part.gnc_file_path}
                    <img
                        src="/uploads/thumbnails/{part.registration_number ||
                            part.id}.svg"
                        alt={part.name}
                        class="preview-img"
                    />
                {:else}
                    <div class="no-preview">No preview available</div>
                {/if}
                <div class="details">
                    <p>
                        <strong>Registration:</strong>
                        {part.registration_number || "-"}
                    </p>
                    <p>
                        <strong>Dimensions:</strong>
                        {part.width || "?"} x {part.height || "?"} mm
                    </p>
                </div>
            </div>
        </div>
    </div>
{/if}

<svelte:window onkeydown={handleKeydown} />

<style>
    .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }

    .modal {
        background: white;
        border-radius: 8px;
        width: 90%;
        max-width: 800px;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    header {
        padding: 15px 20px;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    h3 {
        margin: 0;
        font-size: 1.25rem;
    }

    .close-btn {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0;
        color: #666;
    }

    .close-btn:hover {
        color: #333;
    }

    .content {
        padding: 20px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 20px;
    }

    .preview-img {
        max-width: 100%;
        max-height: 60vh;
        object-fit: contain;
        background: #f8fafc;
        border-radius: 4px;
        padding: 20px;
    }

    .details {
        display: flex;
        gap: 20px;
        color: #666;
    }

    .no-preview {
        padding: 40px;
        background: #f8fafc;
        border-radius: 4px;
        color: #94a3b8;
    }
</style>
