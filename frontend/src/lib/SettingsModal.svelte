<script>
    import { fetchSetting, updateSetting } from './api.js';

    let { isOpen, close } = $props();
    let ocrUrl = $state('');
    let loading = $state(false);
    let message = $state('');
    let isError = $state(false);

    $effect(() => {
        if (isOpen) {
            loadSettings();
        }
    });

    async function loadSettings() {
        loading = true;
        message = '';
        try {
            const result = await fetchSetting('ocr_url');
            ocrUrl = result.value;
        } catch (e) {
            console.error(e);
            message = 'Failed to load settings';
            isError = true;
        } finally {
            loading = false;
        }
    }

    async function handleSave(e) {
        e.preventDefault();
        loading = true;
        message = '';
        isError = false;

        try {
            await updateSetting('ocr_url', ocrUrl);
            message = 'Settings saved successfully';
        } catch (e) {
            console.error(e);
            message = 'Failed to save settings';
            isError = true;
        } finally {
            loading = false;
        }
    }
</script>

<div class="settings-container">
    <h2>Settings</h2>

    <form onsubmit={handleSave}>
        <div class="form-group">
            <label for="ocr_url">OCR Service URL</label>
            <input
                id="ocr_url"
                type="url"
                bind:value={ocrUrl}
                placeholder="http://localhost:7860"
                required
            />
            <p class="help-text">URL of the Docling OCR service.</p>
        </div>

        {#if message}
            <div class="message {isError ? 'error' : 'success'}">
                {message}
            </div>
        {/if}

        <div class="actions">
            <button type="button" class="btn-secondary" onclick={close} disabled={loading}>Close</button>
            <button type="submit" class="btn-primary" disabled={loading}>
                {loading ? 'Saving...' : 'Save Settings'}
            </button>
        </div>
    </form>
</div>

<style>
    h2 {
        margin-top: 0;
        margin-bottom: 1.5rem;
        color: #2c3e50;
    }
    .form-group {
        margin-bottom: 1.25rem;
    }
    label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #555;
        font-size: 0.9rem;
    }
    input {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        box-sizing: border-box;
        font-size: 1rem;
    }
    input:focus {
        border-color: #3b82f6;
        outline: none;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    .help-text {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 0.25rem;
    }
    .actions {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        margin-top: 2rem;
    }
    button {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
    }
    .btn-primary {
        background-color: #3b82f6;
        color: white;
    }
    .btn-primary:disabled {
        background-color: #93c5fd;
        cursor: not-allowed;
    }
    .btn-secondary {
        background-color: #f1f5f9;
        color: #64748b;
    }
    .message {
        padding: 0.75rem;
        border-radius: 6px;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .message.success {
        background-color: #dcfce7;
        color: #166534;
    }
    .message.error {
        background-color: #fee2e2;
        color: #991b1b;
    }
</style>
