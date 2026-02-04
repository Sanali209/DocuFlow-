<script>
    import { onMount } from "svelte";
    import Router, { push, location } from "./lib/Router.svelte";
    import routes from "./routes";
    import Sidebar from "./lib/Sidebar.svelte";
    import SettingsModal from "./lib/SettingsModal.svelte";
    import Modal from "./lib/Modal.svelte";
    import { appState, setConfigStatus } from "./lib/appState.svelte.js";

    import "./lib/design_system.css";

    let isSettingsOpen = $state(false);

    onMount(async () => {
        try {
            // Check config
            const res = await fetch("/api/config-check");
            const data = await res.json();

            setConfigStatus(data.status);

            if (data.needs_setup) {
                // If DB is broken or missing path, go to setup
                push("/setup");
            }
        } catch (e) {
            console.error("Config check failed", e);
            // Assume setup needed if API fails
            push("/setup");
        }
    });

    function openSettings() {
        isSettingsOpen = true;
    }
</script>

<div class="app-container">
    {#if location.path !== "/setup"}
        <Sidebar />
    {/if}

    <main class="main-content">
        <div class="top-bar">
            <div class="spacer"></div>
            <button
                class="settings-btn"
                onclick={openSettings}
                title="Settings"
            >
                ⚙️
            </button>
        </div>

        <div class="route-content">
            <Router {routes} />
        </div>
    </main>

    <Modal isOpen={isSettingsOpen} close={() => (isSettingsOpen = false)}>
        <SettingsModal
            isOpen={isSettingsOpen}
            close={() => (isSettingsOpen = false)}
        />
    </Modal>
</div>

<style>
    :global(body) {
        /* Styles are now in design_system.css */
        margin: 0;
    }

    .app-container {
        display: flex;
        min-height: 100vh;
    }

    .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow-x: hidden;
    }

    .top-bar {
        height: 48px;
        display: flex;
        align-items: center;
        padding: 0 1rem;
        background: white;
        border-bottom: 1px solid #e2e8f0;
    }

    .spacer {
        flex: 1;
    }

    .settings-btn {
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        padding: 0.5rem;
        border-radius: 50%;
        transition: background 0.2s;
    }
    .settings-btn:hover {
        background: #e2e8f0;
    }

    .route-content {
        flex: 1;
        padding: 1.5rem;
        overflow-y: auto;
    }
</style>
