<script>
    import { onMount } from "svelte";
    import { settingService } from "./stores/services.js";
    import { uiState } from "./stores/appState.svelte.js";
    import { push } from "./Router.svelte";
    import { appState } from "./appState.svelte.js";

    let dbPath = $state("");
    let testing = $state(false);
    let testResult = $state(null);
    let saving = $state(false);

    onMount(async () => {
        // Fetch current config if available
        try {
            const data = await settingService.fetchDatabaseConfig();
            if (data.database_path) dbPath = data.database_path;
        } catch (e) {
            console.error(e);
        }
    });

    async function handleTest() {
        if (!dbPath) return;
        testing = true;
        testResult = null;
        try {
            const data = await settingService.testPath(dbPath);
            testResult = {
                ok: data.accessible || !data.exists,
                message: data.accessible
                    ? "Path exists and is readable."
                    : data.exists
                      ? "Path exists but not readable."
                      : "File does not exist (will be created).",
            };
        } catch (e) {
            testResult = { ok: false, message: e.message };
        } finally {
            testing = false;
        }
    }

    async function handleSave() {
        saving = true;
        try {
            const res = await settingService.updateDatabaseConfig({
                database_path: dbPath,
            });
            if (res.ok) {
                uiState.addNotification(
                    "Configuration saved. Application will restart.",
                    "info",
                );
                appState.configStatus = "configured";
                // Wait for restart
                setTimeout(() => {
                    push("/");
                    window.location.reload();
                }, 3000);
            } else {
                uiState.addNotification(
                    "Failed to save configuration",
                    "error",
                );
            }
        } catch (e) {
            uiState.addNotification("Error saving configuration", "error");
            console.error(e);
        } finally {
            saving = false;
        }
    }
</script>

<div class="setup-container">
    <div class="card">
        <h1>Welcome to DocuFlow</h1>
        <p class="subtitle">Please configure the database connection.</p>

        <div class="field">
            <label for="db-path">Database File Path</label>
            <p class="help-text">
                Enter the full path to the SQLite database file. For network
                sharing, use a path on the shared drive (e.g., <code
                    >Z:\DocuFlow\data.db</code
                >).
            </p>
            <div class="input-group">
                <input
                    id="db-path"
                    type="text"
                    bind:value={dbPath}
                    placeholder="C:\DocuFlow\data.db"
                />
                <button onclick={handleTest} disabled={testing}>
                    {testing ? "Testing..." : "Test Path"}
                </button>
            </div>
            {#if testResult}
                <p class="result {testResult.ok ? 'success' : 'warn'}">
                    {testResult.message}
                </p>
            {/if}
        </div>

        <div class="actions">
            <button
                class="primary"
                onclick={handleSave}
                disabled={saving || !dbPath}
            >
                {saving ? "Saving..." : "Save Configuration"}
            </button>
        </div>
    </div>
</div>

<style>
    .setup-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background-color: #f1f5f9;
        padding: 1rem;
    }
    .card {
        background: white;
        padding: 2.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        width: 100%;
        max-width: 500px;
    }
    h1 {
        margin: 0 0 0.5rem 0;
        color: #0f172a;
        font-size: 1.75rem;
    }
    .subtitle {
        color: #64748b;
        margin-bottom: 2rem;
    }
    .field {
        margin-bottom: 2rem;
    }
    label {
        display: block;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #334155;
    }
    .help-text {
        font-size: 0.875rem;
        color: #64748b;
        margin-bottom: 0.75rem;
        line-height: 1.4;
    }
    .input-group {
        display: flex;
        gap: 0.5rem;
    }
    input {
        flex: 1;
        padding: 0.75rem;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        font-size: 1rem;
    }
    button {
        padding: 0.75rem 1.25rem;
        font-weight: 600;
        border-radius: 6px;
        cursor: pointer;
        border: 1px solid #cbd5e1;
        background: white;
        color: #334155;
    }
    button.primary {
        width: 100%;
        background: #0f172a;
        color: white;
        border: none;
        font-size: 1.1rem;
        padding: 1rem;
    }
    button.primary:hover:not(:disabled) {
        background: #1e293b;
    }
    .result {
        margin-top: 0.5rem;
        font-size: 0.875rem;
    }
    .result.success {
        color: #16a34a;
    }
    .result.warn {
        color: #d97706;
    }
</style>
