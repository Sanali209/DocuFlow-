<script>
    import { onMount } from 'svelte';
    import { fetchDocuments, fetchMaterials } from './api.js';
    import { setMenuActions, clearMenuActions } from "./appState.svelte.js";

    let stats = $state({
        totalDocuments: 0,
        totalTasks: 0,
        totalMaterials: 0,
        documentsInProgress: 0,
        documentsDone: 0,
        tasksPlanned: 0,
        tasksPending: 0,
        tasksDone: 0
    });

    let dailyReport = $state({
        tasksCompleted: 0,
        documentsCreated: 0,
        documentsCompleted: 0
    });

    let weeklyReport = $state({
        tasksCompleted: 0,
        documentsCreated: 0,
        documentsCompleted: 0
    });

    let monthlyReport = $state({
        tasksCompleted: 0,
        documentsCreated: 0,
        documentsCompleted: 0
    });

    let recentDocuments = $state([]);
    let loading = $state(true);

    onMount(() => {
        loadDashboardData();
        setMenuActions([
            {
                label: "Dashboard",
                items: [
                    { label: "Refresh", action: loadDashboardData }
                ]
            }
        ]);

        return () => {
            clearMenuActions();
        };
    });

    async function loadDashboardData() {
        loading = true;
        try {
            // Fetch all documents with their tasks
            const documents = await fetchDocuments('', '', '', 'registration_date', 'desc');
            const materials = await fetchMaterials();

            // Calculate general stats
            stats.totalDocuments = documents.length;
            stats.totalMaterials = materials.length;
            stats.documentsInProgress = documents.filter(d => d.status === 'in_progress').length;
            stats.documentsDone = documents.filter(d => d.status === 'done').length;

            // Calculate task stats
            let allTasks = [];
            documents.forEach(doc => {
                if (doc.tasks) {
                    allTasks = allTasks.concat(doc.tasks);
                }
            });

            stats.totalTasks = allTasks.length;
            stats.tasksPlanned = allTasks.filter(t => t.status === 'planned').length;
            stats.tasksPending = allTasks.filter(t => t.status === 'pending').length;
            stats.tasksDone = allTasks.filter(t => t.status === 'done').length;

            // Calculate daily report (today)
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            dailyReport.documentsCreated = documents.filter(d => {
                const regDate = new Date(d.registration_date);
                regDate.setHours(0, 0, 0, 0);
                return regDate.getTime() === today.getTime();
            }).length;

            dailyReport.documentsCompleted = documents.filter(d => {
                if (!d.done_date) return false;
                const doneDate = new Date(d.done_date);
                doneDate.setHours(0, 0, 0, 0);
                return doneDate.getTime() === today.getTime();
            }).length;

            // Calculate weekly report (last 7 days)
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            weekAgo.setHours(0, 0, 0, 0);

            weeklyReport.documentsCreated = documents.filter(d => {
                const regDate = new Date(d.registration_date);
                return regDate >= weekAgo;
            }).length;

            weeklyReport.documentsCompleted = documents.filter(d => {
                if (!d.done_date) return false;
                const doneDate = new Date(d.done_date);
                return doneDate >= weekAgo;
            }).length;

            // Calculate monthly report (last 30 days)
            const monthAgo = new Date();
            monthAgo.setDate(monthAgo.getDate() - 30);
            monthAgo.setHours(0, 0, 0, 0);

            monthlyReport.documentsCreated = documents.filter(d => {
                const regDate = new Date(d.registration_date);
                return regDate >= monthAgo;
            }).length;

            monthlyReport.documentsCompleted = documents.filter(d => {
                if (!d.done_date) return false;
                const doneDate = new Date(d.done_date);
                return doneDate >= monthAgo;
            }).length;

            // Get recent documents (last 5)
            recentDocuments = documents.slice(0, 5);

        } catch (e) {
            console.error('Failed to load dashboard data', e);
        } finally {
            loading = false;
        }
    }
</script>

<div class="dashboard-container">
    {#if loading}
        <div class="loading">Loading dashboard...</div>
    {:else}
        <!-- Overview Statistics -->
        <div class="dashboard-section">
            <h2>📊 Overview</h2>
            <div class="stats-grid">
                <div class="stat-card documents">
                    <div class="stat-icon">📄</div>
                    <div class="stat-content">
                        <div class="stat-value">{stats.totalDocuments}</div>
                        <div class="stat-label">Total Documents</div>
                        <div class="stat-breakdown">
                            <span class="in-progress">{stats.documentsInProgress} in progress</span>
                            <span class="done">{stats.documentsDone} done</span>
                        </div>
                    </div>
                </div>

                <div class="stat-card tasks">
                    <div class="stat-icon">✓</div>
                    <div class="stat-content">
                        <div class="stat-value">{stats.totalTasks}</div>
                        <div class="stat-label">Total Tasks</div>
                        <div class="stat-breakdown">
                            <span class="planned">{stats.tasksPlanned} planned</span>
                            <span class="pending">{stats.tasksPending} pending</span>
                            <span class="done">{stats.tasksDone} done</span>
                        </div>
                    </div>
                </div>

                <div class="stat-card materials">
                    <div class="stat-icon">📦</div>
                    <div class="stat-content">
                        <div class="stat-value">{stats.totalMaterials}</div>
                        <div class="stat-label">Materials</div>
                    </div>
                </div>

                <div class="stat-card completion">
                    <div class="stat-icon">📈</div>
                    <div class="stat-content">
                        <div class="stat-value">
                            {stats.totalDocuments > 0 ? Math.round((stats.documentsDone / stats.totalDocuments) * 100) : 0}%
                        </div>
                        <div class="stat-label">Completion Rate</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Reports -->
        <div class="dashboard-section">
            <h2>📅 Reports</h2>
            <div class="reports-grid">
                <!-- Daily Report -->
                <div class="report-card">
                    <h3>Today</h3>
                    <div class="report-item">
                        <span class="report-label">Documents Created:</span>
                        <span class="report-value">{dailyReport.documentsCreated}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Documents Completed:</span>
                        <span class="report-value">{dailyReport.documentsCompleted}</span>
                    </div>
                </div>

                <!-- Weekly Report -->
                <div class="report-card">
                    <h3>Last 7 Days</h3>
                    <div class="report-item">
                        <span class="report-label">Documents Created:</span>
                        <span class="report-value">{weeklyReport.documentsCreated}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Documents Completed:</span>
                        <span class="report-value">{weeklyReport.documentsCompleted}</span>
                    </div>
                </div>

                <!-- Monthly Report -->
                <div class="report-card">
                    <h3>Last 30 Days</h3>
                    <div class="report-item">
                        <span class="report-label">Documents Created:</span>
                        <span class="report-value">{monthlyReport.documentsCreated}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Documents Completed:</span>
                        <span class="report-value">{monthlyReport.documentsCompleted}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Documents -->
        <div class="dashboard-section">
            <h2>📝 Recent Documents</h2>
            <div class="recent-documents">
                {#each recentDocuments as doc}
                    <div class="recent-doc-item">
                        <div class="doc-info">
                            <span class="doc-name">{doc.name}</span>
                            <span class="doc-date">{doc.registration_date}</span>
                        </div>
                        <span class="doc-status {doc.status}">{doc.status}</span>
                    </div>
                {/each}
                {#if recentDocuments.length === 0}
                    <div class="empty-state">No documents yet</div>
                {/if}
            </div>
        </div>
    {/if}
</div>

<style>
    .dashboard-container {
        padding: 0;
    }

    .loading {
        text-align: center;
        padding: 3rem;
        color: #64748b;
        font-size: 1.1rem;
    }

    .dashboard-section {
        margin-bottom: 2rem;
    }

    .dashboard-section h2 {
        margin: 0 0 1.5rem 0;
        font-size: 1.5rem;
        color: #1e293b;
        font-weight: 600;
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
    }

    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        display: flex;
        gap: 1rem;
        align-items: flex-start;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .stat-icon {
        font-size: 2.5rem;
        flex-shrink: 0;
    }

    .stat-content {
        flex: 1;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.25rem;
    }

    .stat-label {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }

    .stat-breakdown {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        font-size: 0.85rem;
    }

    .stat-breakdown span {
        color: #64748b;
    }

    .stat-breakdown .in-progress {
        color: #3b82f6;
    }

    .stat-breakdown .done {
        color: #10b981;
    }

    .stat-breakdown .planned {
        color: #6366f1;
    }

    .stat-breakdown .pending {
        color: #f59e0b;
    }

    .reports-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
    }

    .report-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }

    .report-card h3 {
        margin: 0 0 1rem 0;
        font-size: 1.1rem;
        color: #1e293b;
        font-weight: 600;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #f1f5f9;
    }

    .report-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid #f1f5f9;
    }

    .report-item:last-child {
        border-bottom: none;
    }

    .report-label {
        color: #64748b;
        font-size: 0.9rem;
    }

    .report-value {
        font-weight: 600;
        color: #1e293b;
        font-size: 1.1rem;
    }

    .recent-documents {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }

    .recent-doc-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        border-bottom: 1px solid #f1f5f9;
        transition: background-color 0.2s;
    }

    .recent-doc-item:hover {
        background-color: #f8fafc;
    }

    .recent-doc-item:last-child {
        border-bottom: none;
    }

    .doc-info {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .doc-name {
        font-weight: 500;
        color: #1e293b;
    }

    .doc-date {
        font-size: 0.85rem;
        color: #94a3b8;
    }

    .doc-status {
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: capitalize;
    }

    .doc-status.in_progress {
        background: #dbeafe;
        color: #1e40af;
    }

    .doc-status.done {
        background: #dcfce7;
        color: #166534;
    }

    .empty-state {
        text-align: center;
        padding: 2rem;
        color: #94a3b8;
        font-style: italic;
    }

    @media (max-width: 640px) {
        .stats-grid, .reports-grid {
            grid-template-columns: 1fr;
        }

        .stat-card {
            padding: 1rem;
        }

        .stat-icon {
            font-size: 2rem;
        }

        .stat-value {
            font-size: 1.5rem;
        }
    }
</style>
