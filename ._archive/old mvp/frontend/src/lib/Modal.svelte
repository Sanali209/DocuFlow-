<script>
    let { isOpen, close, children, maxWidth = '500px' } = $props();

    function handleKeydown(e) {
        if (e.key === 'Escape') {
            close();
        }
    }
</script>

{#if isOpen}
    <div class="modal-backdrop" onclick={close} onkeydown={handleKeydown} role="button" tabindex="0">
        <div class="modal-content" style="max-width: {maxWidth}" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()} role="document" tabindex="0">
            <button class="close-btn" onclick={close}>&times;</button>
            {@render children()}
        </div>
    </div>
{/if}

<style>
    .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        backdrop-filter: blur(2px);
    }
    .modal-content {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        position: relative;
        width: 90%;
        animation: slideIn 0.3s ease-out;
        max-height: 90vh;
        overflow-y: auto;
    }
    .close-btn {
        position: absolute;
        top: 10px;
        right: 15px;
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: #666;
    }
    .close-btn:hover {
        color: #000;
    }
    @keyframes slideIn {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
</style>
