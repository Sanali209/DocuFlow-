<script>
    import { onMount } from "svelte";
    import Router, { push, location } from "./lib/Router.svelte";
    import routes from "./routes";
    import Header from "./lib/Header.svelte";
    import Modal from "./lib/Modal.svelte";
    import { appState, setConfigStatus } from "./lib/appState.svelte.js";

    import "./lib/design_system.css";

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
</script>

<div class="app-container">
    {#if location.path !== "/setup"}
        <Header />
    {/if}

    <main class="main-content">
        <div class="route-content">
            <Router {routes} />
        </div>
    </main>
</div>

<style>
    :global(body) {
        /* Styles are now in design_system.css */
        margin: 0;
    }

    .app-container {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }

    .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow-x: hidden;
        background-color: #f8fafc;
    }

    .route-content {
        flex: 1;
        padding: 1.5rem;
        overflow-y: auto;
    }
</style>
