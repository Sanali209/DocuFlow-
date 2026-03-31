<script>
    import { onMount } from "svelte";
    import { settingService } from "./stores/services.js";
    import { uiState } from "./stores/appState.svelte.js";

    let activeTab = $state("general"); // 'general' | 'nesting' | 'database'
    let docNameRegex = $state("");
    let userRole = $state("admin");
    let syncMihtavPath = $state("");
    let syncSidraPath = $state("");
    let syncRescanInterval = $state(60);
    let rescanning = $state(false);

    // Database Settings
    let databasePath = $state("");
    let refreshing = $state(false);

    // Nesting Settings
    let nestingRotations = $state(4);
    let nestingPopulation = $state(10);
    let nestingSpacing = $state(5);
    let gncLibraryPageSize = $state(24);

    let loading = $state(true);
    let testing = $state({ mihtav: false, sidra: false });
    let testResults = $state({ mihtav: null, sidra: null });

    async function loadSettings() {
        loading = true;
        try {
            const [
                regexSetting,
                mihtavSetting,
                sidraSetting,
                rotSetting,
                popSetting,
                spacSetting,
                pageSizeSetting,
                dbConfig,
                rescanSetting,
            ] = await Promise.all([
                settingService
                    .fetchSetting("doc_name_regex")
                    .catch(() => ({ value: "" })),
                settingService
                    .fetchSetting("sync_mihtav_path")
                    .catch(() => ({ value: "" })),
                settingService
                    .fetchSetting("sync_sidra_path")
                    .catch(() => ({ value: "" })),
                settingService
                    .fetchSetting("nesting_rotations")
                    .catch(() => ({ value: "4" })),
                settingService.fetchSetting("nesting_population").catch(() => ({
                    value: "10",
                })),
                settingService.fetchSetting("nesting_spacing").catch(() => ({
                    value: "5",
                })),
                settingService
                    .fetchSetting("gnc_library_page_size")
                    .catch(() => ({
                        value: "24",
                    })),
                settingService.fetchDatabaseConfig().catch(() => ({
                    database_path: "sql_app.db",
                })),
                settingService
                    .fetchSetting("sync_rescan_interval")
                    .catch(() => ({ value: "60" })),
            ]);
            docNameRegex = regexSetting.value || "";
            syncMihtavPath = mihtavSetting.value || "";
            syncSidraPath = sidraSetting.value || "";
            nestingRotations = parseInt(rotSetting.value) || 4;
            nestingPopulation = parseInt(popSetting.value) || 10;
            nestingSpacing = parseFloat(spacSetting?.value) || 5;
            gncLibraryPageSize = parseInt(pageSizeSetting?.value) || 24;
            databasePath = dbConfig.database_path;
            syncRescanInterval = parseInt(rescanSetting?.value) || 60;

            // Load role
            const storedRole = localStorage.getItem("user_role");
            if (storedRole) userRole = storedRole;
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    }

    async function handleTestPath(type) {
        const path = type === "mihtav" ? syncMihtavPath : syncSidraPath;
        if (!path) {
            testResults[type] = { accessible: false, error: "Path is empty" };
            return;
        }
        testing[type] = true;
        try {
            const result = await settingService.testPath(path);
            testResults[type] = {
                accessible: result.ok,
                error: result.error,
            };
        } catch (e) {
            testResults[type] = { accessible: false, error: e.message };
        } finally {
            testing[type] = false;
        }
    }

    async function saveSettings() {
        try {
            await Promise.all([
                settingService.updateSetting("doc_name_regex", docNameRegex),
                settingService.updateSetting(
                    "sync_mihtav_path",
                    syncMihtavPath,
                ),
                settingService.updateSetting("sync_sidra_path", syncSidraPath),
                settingService.updateSetting(
                    "nesting_population",
                    nestingPopulation.toString(),
                ),
                settingService.updateSetting(
                    "nesting_rotations",
                    nestingRotations.toString(),
                ),
                settingService.updateSetting(
                    "nesting_spacing",
                    nestingSpacing.toString(),
                ),
                settingService.updateSetting(
                    "gnc_library_page_size",
                    gncLibraryPageSize.toString(),
                ),
                settingService.updateSetting(
                    "sync_rescan_interval",
                    syncRescanInterval.toString(),
                ),
                settingService
                    .updateDatabaseConfig({ database_path: databasePath })
                    .then((res) => {
                        if (res.ok) {
                            refreshing = true;
                            // Wait for backend to reload (usually ~1-2s)
                            setTimeout(() => {
                                window.location.reload();
                            }, 3000);
                        }
                    }),
            ]);

            // Save role locally
            localStorage.setItem("user_role", userRole);
            uiState.addNotification("Settings saved successfully", "info");

            // Reload page to apply role changes globally
            if (!refreshing) {
                window.location.reload();
            }
        } catch (e) {
            uiState.addNotification(
                "Failed to save settings. Admin access required.",
                "error",
            );
            console.error(e);
        }
    }

    async function handleManualRescan() {
        rescanning = true;
        try {
            await settingService.triggerRescan();
            uiState.addNotification("Rescan triggered successfully", "info");
        } catch (e) {
            uiState.addNotification("Failed to trigger rescan", "error");
            console.error(e);
        } finally {
            rescanning = false;
        }
    }

    onMount(() => {
        loadSettings();
    });
</script>

<div class="settings-view">
    <div class="page-header">
        <h2>Settings</h2>
        <button class="save-btn" onclick={saveSettings}>Save Changes</button>
    </div>

    {#if loading}
        <p class="loading">Loading settings...</p>
    {:else}
        <div class="content-wrapper">
            <div class="tabs">
                <button
                    class:active={activeTab === "general"}
                    onclick={() => (activeTab = "general")}
                >
                    General
                </button>
                <button
                    class:active={activeTab === "nesting"}
                    onclick={() => (activeTab = "nesting")}
                >
                    Nesting
                </button>
                <button
                    class:active={activeTab === "database"}
                    onclick={() => (activeTab = "database")}
                >
                    Database
                </button>
            </div>

            <div class="tab-content">
                {#if activeTab === "general"}
                    <div class="card">
                        <div class="field">
                            <label for="regex">Document Name Regex</label>
                            <input
                                id="regex"
                                type="text"
                                bind:value={docNameRegex}
                                placeholder="Regex Pattern"
                            />
                        </div>

                        <hr class="divider" />

                        <h3 class="section-title">Sync Folder Paths</h3>
                        <p class="section-hint">
                            Configure paths to network folders for automatic
                            file import.
                        </p>

                        <div class="field path-field">
                            <label for="mihtav-path">Mihtav (Orders) Path</label
                            >
                            <div class="path-input-group">
                                <input
                                    id="mihtav-path"
                                    type="text"
                                    bind:value={syncMihtavPath}
                                    placeholder="Z:\Mihtavim or \\server\share\orders"
                                />
                                <button
                                    class="test-btn"
                                    onclick={() => handleTestPath("mihtav")}
                                    disabled={testing.mihtav}
                                >
                                    {testing.mihtav ? "Testing..." : "Test"}
                                </button>
                            </div>
                            {#if testResults.mihtav}
                                <span
                                    class="test-result"
                                    class:success={testResults.mihtav
                                        .accessible}
                                    class:error={!testResults.mihtav.accessible}
                                >
                                    {testResults.mihtav.accessible
                                        ? "✓ Path accessible"
                                        : `✗ ${testResults.mihtav.error || "Path not accessible"}`}
                                </span>
                            {/if}
                        </div>

                        <div class="field path-field">
                            <label for="sidra-path"
                                >Sidra (Parts Library) Path</label
                            >
                            <div class="path-input-group">
                                <input
                                    id="sidra-path"
                                    type="text"
                                    bind:value={syncSidraPath}
                                    placeholder="Z:\Sidra or \\server\share\parts"
                                />
                                <button
                                    class="test-btn"
                                    onclick={() => handleTestPath("sidra")}
                                    disabled={testing.sidra}
                                >
                                    {testing.sidra ? "Testing..." : "Test"}
                                </button>
                            </div>
                            {#if testResults.sidra}
                                <span
                                    class="test-result"
                                    class:success={testResults.sidra.accessible}
                                    class:error={!testResults.sidra.accessible}
                                >
                                    {testResults.sidra.accessible
                                        ? "✓ Path accessible"
                                        : `✗ ${testResults.sidra.error || "Path not accessible"}`}
                                </span>
                            {/if}
                        </div>

                        <div class="field">
                            <label for="rescan-interval"
                                >Auto-Rescan Interval (minutes)</label
                            >
                            <div class="path-input-group">
                                <input
                                    id="rescan-interval"
                                    type="number"
                                    bind:value={syncRescanInterval}
                                    min="1"
                                    placeholder="60"
                                />
                                <button
                                    class="test-btn"
                                    onclick={handleManualRescan}
                                    disabled={rescanning}
                                >
                                    {rescanning ? "Scanning..." : "Rescan Now"}
                                </button>
                            </div>
                            <p class="hint">
                                How often to scan folders for new files. Set to
                                0 to disable auto-scan.
                            </p>
                        </div>

                        <div class="field">
                            <label for="role">User Mode (Simulated)</label>
                            <select id="role" bind:value={userRole}>
                                <option value="operator"
                                    >Operator (Read-Only)</option
                                >
                                <option value="admin"
                                    >Admin (Full Access)</option
                                >
                            </select>
                            <p class="hint">
                                Switching mode will reload the application.
                            </p>
                        </div>
                        <hr class="divider" />
                        <h3 class="section-title">Editor Settings</h3>
                        <div class="field">
                            <label for="gnc-page-size"
                                >GNC Library Page Size</label
                            >
                            <input
                                id="gnc-page-size"
                                type="number"
                                bind:value={gncLibraryPageSize}
                                min="1"
                                max="100"
                            />
                            <p class="hint">
                                Number of parts to show per page in the GNC
                                Editor's library.
                            </p>
                        </div>
                    </div>
                {:else if activeTab === "nesting"}
                    <div class="card">
                        <h3 class="section-title">
                            Auto-Nesting Configuration
                        </h3>
                        <p class="section-hint">
                            Adjust parameters for the nesting algorithm
                            (SVGnest).
                        </p>

                        <div class="field">
                            <label for="rotations">Rotations</label>
                            <input
                                id="rotations"
                                type="number"
                                bind:value={nestingRotations}
                                min="1"
                                max="360"
                            />
                            <p class="hint">
                                Number of rotation steps (e.g., 4 = 0, 90, 180,
                                270).
                            </p>
                        </div>

                        <div class="field">
                            <label for="population">Population Size</label>
                            <input
                                id="population"
                                type="number"
                                bind:value={nestingPopulation}
                                min="5"
                                max="100"
                            />
                            <p class="hint">
                                Higher values check more combinations but run
                                slower.
                            </p>
                        </div>

                        <div class="field">
                            <label for="spacing">Part Spacing (mm)</label>
                            <input
                                id="spacing"
                                type="number"
                                bind:value={nestingSpacing}
                                min="0"
                                step="0.5"
                            />
                            <p class="hint">Minimum distance between parts.</p>
                        </div>
                    </div>
                {:else if activeTab === "database"}
                    <div class="card">
                        <h3 class="section-title">Database Storage</h3>
                        <p class="section-hint">
                            Configure the location of the SQLite database file.
                        </p>

                        <div class="field">
                            <label for="db-path">Database Path</label>
                            <input
                                id="db-path"
                                type="text"
                                bind:value={databasePath}
                                placeholder="e.g., sql_app.db or data/production.db"
                            />
                            <p class="hint">
                                Provide a relative or absolute path. If the
                                directory doesn't exist, it will be created.
                            </p>
                        </div>

                        {#if refreshing}
                            <div class="refresh-overlay">
                                <div class="spinner"></div>
                                <p>Applying changes and refreshing system...</p>
                            </div>
                        {/if}
                    </div>
                {/if}
            </div>
        </div>
    {/if}
</div>

<style>
    .settings-view {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        padding-bottom: 2rem;
    }
    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    h2 {
        margin: 0;
        font-size: 1.5rem;
        color: #1e293b;
    }
    .loading {
        text-align: center;
        padding: 3rem;
        color: #64748b;
    }
    .content-wrapper {
        max-width: 800px;
    }
    .card {
        background: white;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    .field {
        margin-bottom: 1.5rem;
    }
    label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #475569;
    }
    input,
    select {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        font-size: 1rem;
        box-sizing: border-box;
    }
    .divider {
        border: 0;
        border-top: 1px solid #e2e8f0;
        margin: 2rem 0;
    }
    .hint {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.5rem;
    }
    .save-btn {
        background: #0f172a;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
        font-size: 1rem;
    }
    .save-btn:hover {
        background: #334155;
    }
    .section-title {
        font-size: 1.1rem;
        color: #1e293b;
        margin: 0 0 0.5rem 0;
    }
    .section-hint {
        font-size: 0.85rem;
        color: #64748b;
        margin: 0 0 1rem 0;
    }
    .path-input-group {
        display: flex;
        gap: 0.5rem;
    }
    .path-input-group input {
        flex: 1;
    }
    .test-btn {
        padding: 0.5rem 1rem;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.875rem;
        white-space: nowrap;
    }
    .test-btn:hover:not(:disabled) {
        background: #e2e8f0;
    }
    .test-btn:disabled {
        cursor: wait;
        opacity: 0.7;
    }
    .test-result {
        display: block;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .test-result.success {
        color: #16a34a;
    }
    .test-result.error {
        color: #dc2626;
    }

    .tabs {
        display: flex;
        gap: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    .tabs button {
        background: transparent;
        color: #64748b;
        border: none;
        padding: 0.75rem 1.25rem;
        cursor: pointer;
        border-radius: 6px 6px 0 0;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        font-weight: 600;
        font-size: 1rem;
    }
    .tabs button.active {
        color: #0f172a;
        border-bottom-color: #0f172a;
        background: white;
    }
    .tabs button:hover:not(.active) {
        color: #334155;
        background: #f1f5f9;
    }

    .refresh-overlay {
        position: absolute;
        inset: 0;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        z-index: 10;
        border-radius: 8px;
    }

    .spinner {
        width: 32px;
        height: 32px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #0f172a;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }

    .card {
        position: relative;
    }
</style>
