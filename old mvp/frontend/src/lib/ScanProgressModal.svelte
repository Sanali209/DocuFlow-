<script>
    import { createEventDispatcher } from "svelte";

    const dispatch = createEventDispatcher();

    let {
        show = $bindable(false),
        progress = 0,
        status = "",
        message = "",
    } = $props();

    function close() {
        if (status !== "scanning") {
            show = false;
            dispatch("close");
        }
    }
</script>

{#if show}
    <div class="modal-overlay" onclick={close}>
        <div class="modal" onclick={(e) => e.stopPropagation()}>
            <h2>Scanning Library</h2>

            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress}%"></div>
                </div>
                <span class="progress-text">{progress}%</span>
            </div>

            <div class="status">
                <strong>Status:</strong>
                {status}
            </div>

            {#if message}
                <div class="message">{message}</div>
            {/if}

            <div class="actions">
                <button onclick={close} disabled={status === "scanning"}>
                    {status === "scanning" ? "Scanning..." : "Close"}
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .modal {
        background: white;
        padding: 24px;
        border-radius: 8px;
        width: 90%;
        max-width: 500px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    h2 {
        margin-top: 0;
        margin-bottom: 20px;
    }

    .progress-container {
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .progress-bar {
        flex: 1;
        height: 24px;
        background: #e0e0e0;
        border-radius: 12px;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        transition: width 0.3s ease;
    }

    .progress-text {
        font-weight: bold;
        min-width: 45px;
        text-align: right;
    }

    .status {
        margin-bottom: 12px;
        font-size: 14px;
    }

    .message {
        padding: 12px;
        background: #f5f5f5;
        border-radius: 4px;
        font-size: 13px;
        margin-bottom: 20px;
        min-height: 60px;
        max-height: 200px;
        overflow-y: auto;
    }

    .actions {
        display: flex;
        justify-content: flex-end;
    }

    button {
        padding: 8px 16px;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }

    button:hover:not(:disabled) {
        background: #2563eb;
    }

    button:disabled {
        background: #9ca3af;
        cursor: not-allowed;
    }
</style>
