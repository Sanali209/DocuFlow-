<script>
    import { onMount } from "svelte";
    import { fetchDashboardStats } from "./api.js";
    import { setMenuActions, clearMenuActions } from "./appState.svelte.js";

    let stats = $state(null);
    let loading = $state(true);
    let error = $state(null);

    onMount(() => {
        loadDashboardData();
        setMenuActions([
            {
                label: "Dashboard",
                items: [{ label: "Refresh", action: loadDashboardData }],
            },
        ]);

        return () => {
            clearMenuActions();
        };
    });

    async function loadDashboardData() {
        loading = true;
        error = null;
        try {
            stats = await fetchDashboardStats();
        } catch (e) {
            console.error("Failed to load dashboard data", e);
            error =
                "Failed to load dashboard statistics. Please try again later.";
        } finally {
            loading = false;
        }
    }

    function formatDate(dateStr) {
        if (!dateStr) return "";
        const date = new Date(dateStr);
        return date.toLocaleString();
    }

    function getActionIcon(action) {
        switch (action) {
            case "POST":
                return "➕";
            case "PUT":
                return "📝";
            case "DELETE":
                return "🗑️";
            default:
                return "⚡";
        }
    }

    function getEntityLabel(entity) {
        return entity
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
    }
</script>

<div class="dashboard-wrapper">
    {#if loading}
        <div class="loading-container">
            <div class="spinner"></div>
            <p>Gathering insights...</p>
        </div>
    {:else if error}
        <div class="error-container">
            <span class="error-icon">⚠️</span>
            <p>{error}</p>
            <button onclick={loadDashboardData}>Retry</button>
        </div>
    {:else if stats}
        <header class="dashboard-header">
            <h1>Workspace Overview</h1>
            <p class="subtitle">Operational metrics and recent activity</p>
        </header>

        <div class="bento-grid">
            <!-- Major Stats -->
            <div class="bento-item stats-overview">
                <div class="stat-main">
                    <span class="stat-value">{stats.document_stats.total}</span>
                    <span class="stat-label">Total Documents</span>
                </div>
                <div class="stat-sub-grid">
                    <div class="stat-sub">
                        <span class="sub-label">In Progress</span>
                        <span class="sub-value progress"
                            >{stats.document_stats.by_status.in_progress ||
                                0}</span
                        >
                    </div>
                    <div class="stat-sub">
                        <span class="sub-label">Completed</span>
                        <span class="sub-value done"
                            >{stats.document_stats.by_status.done || 0}</span
                        >
                    </div>
                </div>
            </div>

            <div class="bento-item task-distribution">
                <h3>Task Allocation</h3>
                <div class="task-bars">
                    {#each Object.entries(stats.task_stats.by_status) as [status, count]}
                        <div class="task-bar-item">
                            <div class="bar-header">
                                <span class="status-name">{status}</span>
                                <span class="status-count">{count}</span>
                            </div>
                            <div class="bar-track">
                                <div
                                    class="bar-fill {status}"
                                    style="width: {(count /
                                        stats.task_stats.total) *
                                        100 || 0}%"
                                ></div>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Inventory Highlights -->
            <div class="bento-item inventory-card">
                <h3>📦 Inventory</h3>
                <div class="inv-metrics">
                    <div class="inv-item">
                        <span class="inv-label">Materials</span>
                        <span class="inv-value"
                            >{stats.inventory.total_materials}</span
                        >
                    </div>
                    <div class="inv-item">
                        <span class="inv-label">Total Stock</span>
                        <span class="inv-value"
                            >{stats.inventory.total_quantity}</span
                        >
                    </div>
                    <div class="inv-item">
                        <span class="inv-label">Reserved</span>
                        <span class="inv-value highlight"
                            >{stats.inventory.total_reserved}</span
                        >
                    </div>
                </div>
            </div>

            <!-- Recent Activity Feed -->
            <div class="bento-item activity-feed">
                <h3>Activity Stream</h3>
                <div class="feed-list">
                    {#each stats.recent_activity as log}
                        <div class="feed-item">
                            <span class="action-icon"
                                >{getActionIcon(log.action)}</span
                            >
                            <div class="feed-content">
                                <p>
                                    <strong>{log.actor}</strong>
                                    {log.action.toLowerCase() === "post"
                                        ? "created"
                                        : log.action.toLowerCase() === "put"
                                          ? "updated"
                                          : "removed"}
                                    {getEntityLabel(log.entity)} #{log.entity_id}
                                </p>
                                <span class="feed-time"
                                    >{formatDate(log.timestamp)}</span
                                >
                            </div>
                        </div>
                    {:else}
                        <p class="empty-feed">No recent activity detected.</p>
                    {/each}
                </div>
            </div>

            <!-- Assignee Workload -->
            <div class="bento-item workload-grid">
                <h3>Assignee Distribution</h3>
                <div class="assignee-list">
                    {#each Object.entries(stats.task_stats.by_assignee) as [name, count]}
                        <div class="assignee-item">
                            <span class="assignee-name">{name}</span>
                            <span class="assignee-count">{count} tasks</span>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Journal Summary -->
            {#if stats.journal_summary.warning || stats.journal_summary.error}
                <div class="bento-item journal-alerts">
                    <h3>⚠️ System Alerts</h3>
                    <div class="alerts-list">
                        {#if stats.journal_summary.error}
                            <div class="alert-box error">
                                <span class="alert-count"
                                    >{stats.journal_summary.error}</span
                                >
                                <span class="alert-text">Critical Errors</span>
                            </div>
                        {/if}
                        {#if stats.journal_summary.warning}
                            <div class="alert-box warning">
                                <span class="alert-count"
                                    >{stats.journal_summary.warning}</span
                                >
                                <span class="alert-text">System Warnings</span>
                            </div>
                        {/if}
                    </div>
                </div>
            {/if}
        </div>
    {/if}
</div>

<style>
    :root {
        --bg-color: #f8fafc;
        --card-bg: #ffffff;
        --text-primary: #0f172a;
        --text-secondary: #64748b;
        --border-color: #e2e8f0;
        --accent-blue: #3b82f6;
        --accent-green: #10b981;
        --accent-orange: #f59e0b;
        --accent-red: #ef4444;
        --bento-gap: 1.25rem;
    }

    .dashboard-wrapper {
        padding: 1.5rem;
        background-color: var(--bg-color);
        min-height: 100%;
        font-family:
            "Inter",
            system-ui,
            -apple-system,
            sans-serif;
    }

    .dashboard-header {
        margin-bottom: 2rem;
    }

    .dashboard-header h1 {
        font-size: 1.875rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }

    .subtitle {
        color: var(--text-secondary);
        margin: 0.25rem 0 0 0;
    }

    /* Bento Grid Layout */
    .bento-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        grid-auto-rows: minmax(160px, auto);
        gap: var(--bento-gap);
    }

    .bento-item {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 1.25rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        transition: all 0.2s ease;
    }

    .bento-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #cbd5e1;
    }

    /* Column/Row Spanning */
    .stats-overview {
        grid-column: span 2;
        grid-row: span 1;
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    .task-distribution {
        grid-column: span 2;
        grid-row: span 1;
    }
    .inventory-card {
        grid-column: span 1;
        grid-row: span 2;
    }
    .activity-feed {
        grid-column: span 2;
        grid-row: span 2;
    }
    .workload-grid {
        grid-column: span 1;
        grid-row: span 2;
    }
    .journal-alerts {
        grid-column: span 1;
        grid-row: span 1;
        border-color: #fecaca;
        background: #fffafb;
    }

    /* Widgets Styling */
    h3 {
        font-size: 1rem;
        font-weight: 600;
        margin: 0 0 1rem 0;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Stats Overview */
    .stat-main {
        display: flex;
        flex-direction: column;
    }
    .stat-main .stat-value {
        font-size: 3rem;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1;
    }
    .stat-main .stat-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-top: 0.5rem;
    }

    .stat-sub-grid {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        border-left: 1px solid var(--border-color);
        padding-left: 2rem;
    }
    .stat-sub {
        display: flex;
        flex-direction: column;
    }
    .sub-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    .sub-value {
        font-size: 1.25rem;
        font-weight: 700;
    }
    .sub-value.progress {
        color: var(--accent-blue);
    }
    .sub-value.done {
        color: var(--accent-green);
    }

    /* Task Bars */
    .task-bars {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .task-bar-item {
        width: 100%;
    }
    .bar-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.4rem;
        font-size: 0.8rem;
    }
    .status-name {
        color: var(--text-secondary);
        text-transform: capitalize;
    }
    .status-count {
        font-weight: 600;
        color: var(--text-primary);
    }
    .bar-track {
        height: 6px;
        background: #f1f5f9;
        border-radius: 3px;
        overflow: hidden;
    }
    .bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .bar-fill.planned {
        background: #818cf8;
    }
    .bar-fill.pending {
        background: #fbbf24;
    }
    .bar-fill.done {
        background: var(--accent-green);
    }

    /* Inventory */
    .inv-metrics {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
        margin-top: 1rem;
    }
    .inv-item {
        display: flex;
        flex-direction: column;
    }
    .inv-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
    }
    .inv-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .inv-value.highlight {
        color: var(--accent-orange);
    }

    /* Feed */
    .feed-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        max-height: 350px;
        overflow-y: auto;
        padding-right: 0.5rem;
    }
    .feed-item {
        display: flex;
        gap: 0.75rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #f1f5f9;
    }
    .feed-item:last-child {
        border-bottom: none;
    }
    .action-icon {
        font-size: 1.25rem;
        background: #f8fafc;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 0.75rem;
        flex-shrink: 0;
    }
    .feed-content p {
        margin: 0;
        font-size: 0.9rem;
        color: var(--text-primary);
    }
    .feed-time {
        font-size: 0.75rem;
        color: var(--text-secondary);
    }

    /* Workload */
    .assignee-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    .assignee-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.6rem 0.8rem;
        background: #f8fafc;
        border-radius: 0.75rem;
        font-size: 0.85rem;
    }
    .assignee-name {
        font-weight: 500;
    }
    .assignee-count {
        background: #fff;
        padding: 0.2rem 0.5rem;
        border-radius: 0.4rem;
        border: 1px solid var(--border-color);
        font-weight: 600;
        color: var(--accent-blue);
    }

    /* Alerts */
    .alerts-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    .alert-box {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem;
        border-radius: 0.75rem;
    }
    .alert-box.error {
        background: #fee2e2;
        color: #b91c1c;
    }
    .alert-box.warning {
        background: #fef3c7;
        color: #92400e;
    }
    .alert-count {
        font-size: 1.25rem;
        font-weight: 800;
    }
    .alert-text {
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* State Mixins */
    .loading-container {
        height: 400px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: var(--text-secondary);
    }
    .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid #e2e8f0;
        border-top-color: var(--accent-blue);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }
    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    .error-container {
        height: 300px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .error-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .error-container button {
        margin-top: 1rem;
        padding: 0.5rem 1.5rem;
        background: var(--accent-blue);
        color: white;
        border: none;
        border-radius: 0.5rem;
        cursor: pointer;
    }

    /* Responsive */
    @media (max-width: 1200px) {
        .bento-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    @media (max-width: 768px) {
        .bento-grid {
            grid-template-columns: 1fr;
        }
        .stats-overview,
        .task-distribution,
        .activity-feed,
        .inventory-card,
        .workload-grid {
            grid-column: span 1;
        }
        .stats-overview {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }
        .stat-sub-grid {
            border-left: none;
            padding-left: 0;
            border-top: 1px solid var(--border-color);
            padding-top: 1rem;
            width: 100%;
        }
    }
</style>
