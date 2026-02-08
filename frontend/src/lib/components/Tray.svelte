<script>
    import {
        appState,
        removeFromTray,
        updateTrayQuantity,
        clearTray,
        toggleTray,
    } from "../appState.svelte.js";
    import { docService } from "../stores/services.js";

    let creating = $state(false);
    let orderName = $state("");

    async function handleCreateOrder() {
        if (appState.partTray.length === 0) return;
        if (!orderName) return alert("Please enter an Order Name");

        creating = true;
        try {
            // Map items to simple format for API
            const items = appState.partTray.map((i) => ({
                id: i.part.id,
                qty: i.quantity,
            }));
            await docService.createOrder(orderName, items);

            clearTray();
            toggleTray();
            alert("Order created successfully!");
        } catch (e) {
            console.error(e);
            alert("Failed to create order: " + e.message);
        } finally {
            creating = false;
        }
    }
</script>

{#if appState.trayVisible}
    <!-- Backdrop -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="tray-backdrop" onclick={toggleTray}></div>

    <aside class="tray-panel">
        <header>
            <h3>Order Tray</h3>
            <button class="close-btn" onclick={toggleTray}>&times;</button>
        </header>

        <div class="items">
            {#each appState.partTray as item (item.part.id)}
                <div class="tray-item">
                    <img
                        src={item.part.thumbnail_url || "/placeholder.png"}
                        alt={item.part.name}
                        class="thumb"
                    />
                    <div class="details">
                        <span class="name">{item.part.name}</span>
                        <div class="qty-controls">
                            <button
                                onclick={() =>
                                    updateTrayQuantity(item.part.id, -1)}
                                disabled={item.quantity <= 1}>-</button
                            >
                            <span class="qty">{item.quantity}</span>
                            <button
                                onclick={() =>
                                    updateTrayQuantity(item.part.id, 1)}
                                >+</button
                            >
                        </div>
                    </div>
                    <button
                        class="remove-btn"
                        onclick={() => removeFromTray(item.part.id)}
                        title="Remove">🗑️</button
                    >
                </div>
            {/each}
            {#if appState.partTray.length === 0}
                <div class="empty">
                    Tray is empty. Add parts from the library.
                </div>
            {/if}
        </div>

        <footer>
            <div class="input-group">
                <label for="order-name">Order Name</label>
                <input
                    id="order-name"
                    type="text"
                    placeholder="e.g. ORDER-2024-001"
                    bind:value={orderName}
                />
            </div>
            <div class="actions">
                <button
                    class="clear-btn"
                    onclick={clearTray}
                    disabled={appState.partTray.length === 0}>Clear</button
                >
                <button
                    class="create-btn"
                    onclick={handleCreateOrder}
                    disabled={appState.partTray.length === 0 ||
                        creating ||
                        !orderName}
                >
                    {creating ? "Creating..." : "Create Order"}
                </button>
            </div>
        </footer>
    </aside>
{/if}

<style>
    .tray-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.3);
        z-index: 998;
    }

    .tray-panel {
        position: fixed;
        top: 0;
        right: 0;
        width: 350px;
        height: 100vh;
        background: white;
        box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
        z-index: 999;
        display: flex;
        flex-direction: column;
        animation: slideIn 0.3s ease-out;
    }

    @keyframes slideIn {
        from {
            transform: translateX(100%);
        }
        to {
            transform: translateX(0);
        }
    }

    header {
        padding: 15px 20px;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    header h3 {
        margin: 0;
        font-size: 1.2rem;
        color: #333;
    }

    .close-btn {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0 5px;
        color: #666;
    }

    .close-btn:hover {
        color: #000;
    }

    .items {
        flex: 1;
        overflow-y: auto;
        padding: 15px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .tray-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background: #f9f9f9;
        border-radius: 6px;
        border: 1px solid #eee;
    }

    .thumb {
        width: 50px;
        height: 50px;
        object-fit: cover;
        border-radius: 4px;
        background: #ddd;
    }

    .details {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 5px;
        min-width: 0; /* Text truncation */
    }

    .name {
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .qty-controls {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .qty-controls button {
        width: 24px;
        height: 24px;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #ccc;
        background: white;
        border-radius: 4px;
        cursor: pointer;
    }

    .qty-controls button:hover:not(:disabled) {
        background: #f0f0f0;
    }

    .qty-controls button:disabled {
        opacity: 0.5;
        cursor: default;
    }

    .qty {
        font-weight: 600;
        min-width: 20px;
        text-align: center;
    }

    .remove-btn {
        background: none;
        border: none;
        cursor: pointer;
        padding: 5px;
        opacity: 0.5;
        transition: opacity 0.2s;
    }

    .remove-btn:hover {
        opacity: 1;
    }

    .empty {
        text-align: center;
        color: #999;
        margin-top: 40px;
        font-style: italic;
    }

    footer {
        padding: 20px;
        border-top: 1px solid #eee;
        background: #fcfcfc;
    }

    .input-group {
        display: flex;
        flex-direction: column;
        gap: 5px;
        margin-bottom: 15px;
    }

    .input-group label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #555;
    }

    .input-group input {
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    .actions {
        display: flex;
        gap: 10px;
    }

    .clear-btn,
    .create-btn {
        padding: 10px;
        border-radius: 6px;
        cursor: pointer;
        border: none;
        font-weight: 500;
        transition: opacity 0.2s;
    }

    .clear-btn {
        background: #f0f0f0;
        color: #555;
        flex: 1;
    }

    .create-btn {
        background: #007bff;
        color: white;
        flex: 2;
    }

    .create-btn:disabled,
    .clear-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .create-btn:hover:not(:disabled) {
        background: #0056b3;
    }

    .clear-btn:hover:not(:disabled) {
        background: #e0e0e0;
    }
</style>
