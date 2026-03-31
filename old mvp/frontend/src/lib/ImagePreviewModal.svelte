<script>
    let { isOpen, close, attachments } = $props();
</script>

{#if isOpen}
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="modal-overlay" onclick={close}>
    <div class="modal-content" onclick={(e) => e.stopPropagation()}>
        <button class="close-btn" onclick={close}>&times;</button>
        <div class="gallery">
            {#each attachments as att}
                <div class="image-wrapper">
                    {#if att.media_type && att.media_type.startsWith('image/')}
                        <img src={att.file_path} alt={att.filename} />
                    {:else}
                        <div class="file-placeholder">
                            <span>📄 {att.filename}</span>
                            <a href={att.file_path} target="_blank" rel="noreferrer">Download</a>
                        </div>
                    {/if}
                </div>
            {/each}
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
        background: rgba(0, 0, 0, 0.85);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
    }
    .modal-content {
        position: relative;
        max-width: 90%;
        max-height: 90%;
        overflow: auto;
    }
    .close-btn {
        position: absolute;
        top: -40px;
        right: 0;
        background: none;
        border: none;
        color: white;
        font-size: 2rem;
        cursor: pointer;
    }
    .gallery {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        justify-content: center;
    }
    .image-wrapper img {
        max-width: 100%;
        max-height: 80vh;
        border-radius: 4px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .file-placeholder {
        background: white;
        padding: 2rem;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }
</style>
