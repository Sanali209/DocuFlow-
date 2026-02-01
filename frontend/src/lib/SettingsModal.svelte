<script>
    import { onMount } from 'svelte';
    import { fetchSetting, updateSetting } from './api';

    export let isOpen = false;
    export let close;

    let ocrUrl = '';
    let docNameRegex = '';
    let userRole = 'operator';
    let loading = true;

    async function loadSettings() {
        loading = true;
        try {
            const [urlSetting, regexSetting] = await Promise.all([
                fetchSetting('ocr_url').catch(() => ({ value: '' })),
                fetchSetting('doc_name_regex').catch(() => ({ value: '' }))
            ]);
            ocrUrl = urlSetting.value;
            docNameRegex = regexSetting.value;

            // Load role
            const storedRole = localStorage.getItem('user_role');
            if (storedRole) userRole = storedRole;

        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    }

    async function saveSettings() {
        try {
            await Promise.all([
                updateSetting('ocr_url', ocrUrl),
                updateSetting('doc_name_regex', docNameRegex)
            ]);

            // Save role locally
            localStorage.setItem('user_role', userRole);

            // Reload page to apply role changes globally (simplest way for MVP)
            window.location.reload();
            
            close();
        } catch (e) {
            alert('Failed to save settings. Ensure you have Admin privileges.');
            console.error(e);
        }
    }

    // Inject role into headers
    // Note: This logic should ideally be in a central API wrapper,
    // but for this MVP phase, we rely on api.js.
    // We need to modify api.js to read from localStorage.

    $effect(() => {
        if (isOpen) {
            loadSettings();
        }
    });
</script>

{#if isOpen}
    <div class="modal-content">
        <h2>Settings</h2>

        {#if loading}
            <p>Loading...</p>
        {:else}
            <div class="field">
                <label for="ocr-url">OCR Service URL</label>
                <input id="ocr-url" type="text" bind:value={ocrUrl} placeholder="http://localhost:7860" />
            </div>
            <div class="field">
                <label for="regex">Document Name Regex</label>
                <input id="regex" type="text" bind:value={docNameRegex} placeholder="Regex Pattern" />
            </div>

            <hr class="divider"/>

            <div class="field">
                <label for="role">User Mode (Simulated)</label>
                <select id="role" bind:value={userRole}>
                    <option value="operator">Operator (Read-Only)</option>
                    <option value="admin">Admin (Full Access)</option>
                </select>
                <p class="hint">Switching mode will reload the application.</p>
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
    input, select {
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
</style>
