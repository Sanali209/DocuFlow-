<script>
    import { onMount } from "svelte";
    import { fetchSetting, updateSetting, checkConfig, testPath } from "./api";

    let { isOpen = false, close } = $props();

    let activeTab = $state("general"); // 'general' | 'nesting'
    let docNameRegex = $state("");
    let userRole = $state("admin");
    let syncMihtavPath = $state("");
    let syncSidraPath = $state("");

    // Nesting Settings
    let nestingRotations = $state(4);
    let nestingPopulation = $state(10);

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
            ] = await Promise.all([
                fetchSetting("doc_name_regex").catch(() => ({ value: "" })),
                fetchSetting("sync_mihtav_path").catch(() => ({ value: "" })),
                fetchSetting("sync_sidra_path").catch(() => ({ value: "" })),
                fetchSetting("nesting_rotations").catch(() => ({ value: "4" })),
                fetchSetting("nesting_population").catch(() => ({
                    value: "10",
                })),
            ]);
            docNameRegex = regexSetting.value || "";
            syncMihtavPath = mihtavSetting.value || "";
            syncSidraPath = sidraSetting.value || "";
            nestingRotations = parseInt(rotSetting.value) || 4;
            nestingPopulation = parseInt(popSetting.value) || 10;

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
            const result = await testPath(path);
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
                updateSetting("doc_name_regex", docNameRegex),
                updateSetting("sync_mihtav_path", syncMihtavPath),
                updateSetting("sync_sidra_path", syncSidraPath),
                updateSetting("nesting_rotations", nestingRotations.toString()),
                updateSetting(
                    "nesting_population",
                    nestingPopulation.toString(),
                ),
            ]);

            // Save role locally
            localStorage.setItem("user_role", userRole);

            // Reload page to apply role changes globally (simplest way for MVP)
            window.location.reload();

            close();
        } catch (e) {
            alert("Failed to save settings. Ensure you have Admin privileges.");
            console.error(e);
        }
    }

    $effect(() => {
        if (isOpen) {
            loadSettings();
            testResults = { mihtav: null, sidra: null };
        }
    });
</script>

{#if isOpen}
    <div class="modal-content">
        <h2>Settings</h2>

        {#if loading}
            <p>Loading...</p>
        {:else}
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
            </div>

            <div class="tab-content">
                {#if activeTab === "general"}
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
                        Configure paths to network folders for automatic file
                        import.
                    </p>

                    <div class="field path-field">
                        <label for="mihtav-path">Mihtav (Orders) Path</label>
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
                                class:success={testResults.mihtav.accessible}
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
                        <label for="role">User Mode (Simulated)</label>
                        <select id="role" bind:value={userRole}>
                            <option value="operator"
                                >Operator (Read-Only)</option
                            >
                            <option value="admin">Admin (Full Access)</option>
                        </select>
                        <p class="hint">
                            Switching mode will reload the application.
                        </p>
                    </div>
                {:else if activeTab === "nesting"}
                    <h3 class="section-title">Auto-Nesting Configuration</h3>
                    <p class="section-hint">
                        Adjust parameters for the nesting algorithm (SVGnest).
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
                {/if}
            </div>
        {/if}

        <div class="actions">
            <button class="cancel-btn" onclick={close}>Cancel</button>
            <button class="save-btn" onclick={saveSettings}>Save</button>
        </div>
    </div>
{/if}

<style>
    .modal-content {
        padding: 0.5rem;
    }
    h2 {
        margin-top: 0;
        margin-bottom: 1.5rem;
        font-size: 1.5rem;
        color: #1e293b;
    }
    .field {
        margin-bottom: 1.25rem;
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
    }
    .divider {
        border: 0;
        border-top: 1px solid #e2e8f0;
        margin: 1.5rem 0;
    }
    .hint {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.5rem;
    }
    .actions {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        margin-top: 2rem;
    }
    button {
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
        font-size: 1rem;
    }
    .cancel-btn {
        background: white;
        border: 1px solid #cbd5e1;
        color: #475569;
    }
    .save-btn {
        background: #0f172a;
        color: white;
        border: none;
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
        padding: 0.5rem 1rem;
        cursor: pointer;
        border-radius: 6px 6px 0 0;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        font-weight: 600;
    }
    .tabs button.active {
        color: #0f172a;
        border-bottom-color: #0f172a;
        background: #f8fafc;
    }
    .tabs button:hover:not(.active) {
        color: #334155;
        background: #f1f5f9;
    }
</style>
