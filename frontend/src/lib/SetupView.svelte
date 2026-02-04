<script>
    import { onMount } from "svelte";
    import { checkConfig, testPath, updateSetting } from "./api"; // Ensure updateSetting is exported or similar
    import { push } from "./Router.svelte";
    import { appState } from "./appState.svelte.js";

    let dbPath = $state("");
    let testing = $state(false);
    let testResult = $state(null);
    let saving = $state(false);

    onMount(async () => {
        // Fetch current config if available
        try {
            const res = await fetch("/api/config");
            const data = await res.json();
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
            // Test if the DIRECTORY of the DB exists (we can't test file if it doesn't exist yet, but maybe dir)
            // Or just check if path is accessible.
            // The API test-path checks existence.
            // For a new DB, we might want to check the folder.
            // Let's just send the path.
            const res = await fetch("/api/test-path", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ path: dbPath }),
            });
            const data = await res.json();

            // Logic: If it's a file path, check if parent dir exists
            // Since backend test_path covers basic existence.

            testResult = {
                ok: data.accessible || !data.exists, // If it doesn't exist, we might be able to create it (sqlite)
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
            const res = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ database_path: dbPath }),
            });
            const data = await res.json();
            if (data.ok) {
                // Config saved.
                // We typically need to restart the backend to pick up the NEW database string in database.py?
                // Or does separate process reload?
                // For this architecture, a restart is safest.
                alert(
                    "Configuration saved. Please restart the application (Server) to apply changes.",
                );
                appState.configStatus = "configured"; // Optimistic
                push("/");
            } else {
                alert("Failed to save config.");
            }
        } catch (e) {
            alert("Error saving config: " + e.message);
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
