<script>
    import { push, location } from "./Router.svelte";
    import { appState } from "./appState.svelte.js";

    let isMenuOpen = $state(false);

    function toggleMenu() {
        isMenuOpen = !isMenuOpen;
    }

    function closeMenu() {
        isMenuOpen = false;
    }

    // Handle mouse enter for the menu container
    function handleMouseEnter() {
        isMenuOpen = true;
    }

    // Handle mouse leave for the menu container
    function handleMouseLeave() {
        isMenuOpen = false;
    }

    function handleNavigate(path) {
        push(path);
        closeMenu();
    }

    function handleAction(action) {
        if (action) action();
        closeMenu();
    }
</script>

<header class="app-header">
    <div
        class="menu-container"
        onmouseenter={handleMouseEnter}
        onmouseleave={handleMouseLeave}
    >
        <button class="menu-btn" aria-label="Menu" onclick={toggleMenu}>
            <span class="icon">☰</span>
        </button>

        {#if isMenuOpen}
            <div class="dropdown-menu">
                <!-- Navigation Submenu -->
                <div class="submenu-group">
                    <div class="submenu-title">Views</div>
                    <button class:active={location.path === "/"} onclick={() => handleNavigate("/")}>
                        Dashboard
                    </button>
                    <button class:active={location.path.includes("/documents")} onclick={() => handleNavigate("/documents")}>
                        Documents
                    </button>
                    <button class:active={location.path.includes("/parts")} onclick={() => handleNavigate("/parts")}>
                        Parts Library
                    </button>
                    <button class:active={location.path.includes("/gnc")} onclick={() => handleNavigate("/gnc")}>
                        GNC Editor
                    </button>
                    <button class:active={location.path.includes("/job")} onclick={() => handleNavigate("/job")}>
                        Job Processing
                    </button>
                    <button class:active={location.path.includes("/stock")} onclick={() => handleNavigate("/stock")}>
                        Stock
                    </button>
                    <button class:active={location.path.includes("/journal")} onclick={() => handleNavigate("/journal")}>
                        Journal
                    </button>
                    <div class="divider"></div>
                    <button class:active={location.path.includes("/settings")} onclick={() => handleNavigate("/settings")}>
                        Settings
                    </button>
                </div>

                <!-- Dynamic Action Submenus -->
                {#if appState.menuActions && appState.menuActions.length > 0}
                    <div class="divider-vertical"></div>
                    <div class="dynamic-actions">
                        {#each appState.menuActions as group}
                            <div class="submenu-group">
                                <div class="submenu-title">{group.label}</div>
                                {#each group.items as item}
                                    <button onclick={() => handleAction(item.action)}>
                                        {item.label}
                                    </button>
                                {/each}
                            </div>
                        {/each}
                    </div>
                {/if}
            </div>
        {/if}
    </div>

    <div class="logo">
        <span class="logo-text">DocuFlow</span>
    </div>
</header>

<style>
    .app-header {
        height: 50px;
        background-color: #0f172a;
        display: flex;
        align-items: center;
        padding: 0 1rem;
        color: white;
        position: relative;
        z-index: 1000;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .menu-container {
        position: relative;
        height: 100%;
        display: flex;
        align-items: center;
    }

    .menu-btn {
        background: none;
        border: none;
        color: white;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0.5rem;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .menu-btn:hover {
        background-color: #334155;
    }

    .dropdown-menu {
        position: absolute;
        top: 100%;
        left: 0;
        background-color: white;
        min-width: 200px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-radius: 0 0 8px 8px;
        display: flex;
        overflow: hidden;
        border: 1px solid #e2e8f0;
        border-top: none;
    }

    .submenu-group {
        display: flex;
        flex-direction: column;
        padding: 0.5rem 0;
        min-width: 180px;
    }

    .submenu-title {
        padding: 0.5rem 1rem;
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #64748b;
        font-weight: 700;
        letter-spacing: 0.05em;
    }

    .submenu-group button {
        background: none;
        border: none;
        text-align: left;
        padding: 0.5rem 1rem;
        cursor: pointer;
        font-size: 0.9rem;
        color: #334155;
        transition: background-color 0.1s;
    }

    .submenu-group button:hover {
        background-color: #f1f5f9;
        color: #0f172a;
    }

    .submenu-group button.active {
        background-color: #eff6ff;
        color: #2563eb;
        font-weight: 500;
    }

    .divider {
        height: 1px;
        background-color: #e2e8f0;
        margin: 0.5rem 0;
    }

    .divider-vertical {
        width: 1px;
        background-color: #e2e8f0;
    }

    .dynamic-actions {
        display: flex;
    }

    .logo {
        margin-left: 1rem;
        font-weight: 700;
        font-size: 1.1rem;
        letter-spacing: -0.025em;
    }
</style>
