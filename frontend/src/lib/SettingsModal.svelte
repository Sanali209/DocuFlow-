<script>
    import { fetchSetting, updateSetting, downloadBackup, uploadRestore } from './api.js';

    let { isOpen, close } = $props();
    let ocrUrl = $state('');
    let docNameRegex = $state('');
    let loading = $state(false);
    let message = $state('');
    let isError = $state(false);
    let restoreFile = $state(null);
    let showRestoreConfirm = $state(false);

    $effect(() => {
        if (isOpen) {
            loadSettings();
        }
    });

    async function loadSettings() {
        loading = true;
        message = '';
        try {
            const resultUrl = await fetchSetting('ocr_url');
            ocrUrl = resultUrl.value;
            try {
                const resultRegex = await fetchSetting('doc_name_regex');
                docNameRegex = resultRegex.value;
            } catch (e) {
                // Ignore if not set (backend defaults will be used, but we might want to show them?
                // Currently backend returns default if missing, so this should work unless 404 behavior changed)
                console.warn("Regex setting might be missing", e);
            }
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
            await updateSetting('doc_name_regex', docNameRegex);
            message = 'Settings saved successfully';
        } catch (e) {
            console.error(e);
            message = 'Failed to save settings';
            isError = true;
        } finally {
            loading = false;
        }
    }

    async function handleBackup() {
        loading = true;
        message = '';
        isError = false;

        try {
            await downloadBackup();
            message = 'Backup downloaded successfully';
        } catch (e) {
            console.error(e);
            message = 'Failed to download backup: ' + e.message;
            isError = true;
        } finally {
            loading = false;
        }
    }

    function handleRestoreFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            restoreFile = file;
            showRestoreConfirm = true;
        }
    }

    async function handleRestoreConfirm() {
        if (!restoreFile) return;

        loading = true;
        message = '';
        isError = false;
        showRestoreConfirm = false;

        try {
            const result = await uploadRestore(restoreFile);
            message = `Restore successful! Restored: ${result.restored.documents} documents, ${result.restored.tasks} tasks, ${result.restored.materials} materials`;
            restoreFile = null;
            
            // Reload page after successful restore
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } catch (e) {
            console.error(e);
            message = 'Failed to restore backup: ' + e.message;
            isError = true;
            restoreFile = null;
        } finally {
            loading = false;
        }
    }

    function handleRestoreCancel() {
        showRestoreConfirm = false;
        restoreFile = null;
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

        <div class="form-group">
            <label for="doc_name_regex">Document Name Regex</label>
            <input
                id="doc_name_regex"
                type="text"
                bind:value={docNameRegex}
                placeholder="(?si)Order:\s*(.*?)\s*Date:"
            />
            <p class="help-text">Regex to extract document name from OCR content.</p>
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

    <hr class="divider" />

    <div class="backup-section">
        <h3>Backup & Restore</h3>
        <p class="help-text">Download or restore all your data as a ZIP file containing JSON backup.</p>
        
        <div class="backup-actions">
            <button 
                type="button" 
                class="btn-backup" 
                onclick={handleBackup}
                disabled={loading}
            >
                💾 Download Backup
            </button>
            
            <label class="btn-restore" class:disabled={loading}>
                📁 Restore from Backup
                <input 
                    type="file" 
                    accept=".zip"
                    onchange={handleRestoreFileSelect}
                    disabled={loading}
                    style="display: none;"
                />
            </label>
        </div>
    </div>

    {#if showRestoreConfirm}
        <div class="confirm-overlay">
            <div class="confirm-dialog">
                <h3>⚠️ Confirm Restore</h3>
                <p>This will replace ALL current data with the backup data.</p>
                <p><strong>This action cannot be undone!</strong></p>
                <p>Selected file: <code>{restoreFile?.name}</code></p>
                <div class="confirm-actions">
                    <button 
                        type="button" 
                        class="btn-secondary" 
                        onclick={handleRestoreCancel}
                    >
                        Cancel
                    </button>
                    <button 
                        type="button" 
                        class="btn-danger" 
                        onclick={handleRestoreConfirm}
                    >
                        Yes, Restore Data
                    </button>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    h2 {
        margin-top: 0;
        margin-bottom: 1.5rem;
        color: #2c3e50;
    }
    h3 {
        margin-top: 0;
        margin-bottom: 1rem;
        color: #2c3e50;
        font-size: 1.1rem;
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

    /* Backup section styles */
    .divider {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 2rem 0;
    }
    
    .backup-section {
        margin-top: 1.5rem;
    }
    
    .backup-actions {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
        flex-wrap: wrap;
    }
    
    .btn-backup,
    .btn-restore {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.95rem;
        border: 1px solid #e2e8f0;
        background-color: white;
        color: #2c3e50;
        transition: all 0.2s;
    }
    
    .btn-backup:hover,
    .btn-restore:hover {
        background-color: #f8fafc;
        border-color: #cbd5e1;
        transform: translateY(-1px);
    }
    
    .btn-backup:disabled,
    .btn-restore.disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
    }
    
    .btn-restore {
        display: inline-block;
    }

    /* Confirmation dialog styles */
    .confirm-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    }
    
    .confirm-dialog {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        max-width: 500px;
        width: 90%;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    .confirm-dialog h3 {
        margin-top: 0;
        color: #dc2626;
    }
    
    .confirm-dialog p {
        margin: 0.75rem 0;
        color: #475569;
        line-height: 1.6;
    }
    
    .confirm-dialog code {
        background: #f1f5f9;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    
    .confirm-actions {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        margin-top: 1.5rem;
    }
    
    .btn-danger {
        background-color: #dc2626;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
    }
    
    .btn-danger:hover {
        background-color: #b91c1c;
    }
</style>
