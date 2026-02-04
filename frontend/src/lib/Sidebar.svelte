<script>
    import { push, location } from "./Router.svelte";
</script>

<aside class="sidebar">
    <div class="sidebar-header">
        <span class="logo-icon">DF</span>
    </div>
    <nav>
        <button class:active={location.path === "/"} onclick={() => push("/")}>
            <span class="icon">📊</span>
            <span class="label">Dashboard</span>
        </button>
        <button
            class:active={location.path.includes("/documents")}
            onclick={() => push("/documents")}
        >
            <span class="icon">📄</span>
            <span class="label">Documents</span>
        </button>
        <button
            class:active={location.path.includes("/parts")}
            onclick={() => push("/parts")}
        >
            <span class="icon">⚙️</span>
            <span class="label">Parts Library</span>
        </button>
        <button
            class:active={location.path.includes("/gnc")}
            onclick={() => push("/gnc")}
        >
            <span class="icon">📐</span>
            <span class="label">GNC Editor</span>
        </button>
        <button
            class:active={location.path.includes("/job")}
            onclick={() => push("/job")}
        >
            <span class="icon">👷</span>
            <span class="label">Job Processing</span>
        </button>
        <button
            class:active={location.path.includes("/stock")}
            onclick={() => push("/stock")}
        >
            <span class="icon">📦</span>
            <span class="label">Stock</span>
        </button>
        <button
            class:active={location.path.includes("/journal")}
            onclick={() => push("/journal")}
        >
            <span class="icon">📓</span>
            <span class="label">Journal</span>
        </button>
    </nav>
</aside>

<style>
    .sidebar {
        width: 64px;
        background-color: #0f172a;
        color: white;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 1rem;
        transition: width 0.2s;
        z-index: 200;
        height: 100vh;
        position: sticky;
        top: 0;
    }

    /* Only enable hover expansion on desktop */
    @media (min-width: 768px) {
        .sidebar:hover {
            width: 220px;
        }

        .sidebar:hover .label {
            opacity: 1;
        }

        /* Align content left when expanded */
        .sidebar:hover button {
            justify-content: flex-start;
        }
    }

    .sidebar-header {
        margin-bottom: 2rem;
        font-weight: bold;
        display: flex;
        justify-content: center;
        width: 100%;
    }

    .logo-icon {
        background: #3b82f6;
        padding: 0.5rem;
        border-radius: 8px;
        font-size: 1.2rem;
    }

    nav {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        width: 100%;
        padding: 0 0.5rem;
        overflow-y: auto; /* Allow scrolling if too many items */
    }

    button {
        background: none;
        border: none;
        color: #94a3b8;
        padding: 0.75rem;
        border-radius: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center; /* Center icon on mobile */
        gap: 1rem;
        width: 100%;
        transition: all 0.2s;
        font-size: 0.95rem;
        overflow: hidden;
        white-space: nowrap;
    }

    button:hover {
        background-color: #1e293b;
        color: white;
        border: none;
    }

    button.active {
        background-color: #3b82f6;
        color: white;
    }

    .icon {
        font-size: 1.2rem;
        min-width: 24px;
        display: flex;
        justify-content: center;
    }

    .label {
        opacity: 0;
        transition: opacity 0.2s;
    }

    /* Mobile: keep sidebar compact, hide labels */
    @media (max-width: 768px) {
        .sidebar {
            width: 56px; /* Slightly narrower on mobile */
            padding-top: 0.75rem;
        }

        .sidebar-header {
            margin-bottom: 1.5rem;
        }

        .logo-icon {
            font-size: 1rem;
            padding: 0.4rem;
        }

        nav {
            padding: 0 0.25rem;
            gap: 0.25rem;
        }

        button {
            padding: 0.6rem;
        }

        .icon {
            font-size: 1.1rem;
        }

        .label {
            display: none; /* Completely hide labels on mobile */
        }
    }
</style>
