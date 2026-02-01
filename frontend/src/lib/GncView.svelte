<script>
    import { parseGnc, saveGnc } from './api';
    import GncCanvas from './components/GncCanvas.svelte';

    let sheet = $state(null);
    let selectedContour = $state(null);
    let filename = $state('');
    let loading = $state(false);

    async function handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        filename = file.name;
        loading = true;
        sheet = null;
        selectedContour = null;

        try {
            sheet = await parseGnc(file);
        } catch (err) {
            alert('Error parsing GNC file');
            console.error(err);
        } finally {
            loading = false;
        }
    }

    function handleContourSelect(e) {
        selectedContour = e.detail;
    }

    async function handleSave() {
        if (!sheet || !filename) return;
        try {
            const res = await saveGnc(sheet, filename, true);
            alert(`Saved successfully to ${res.path}`);
        } catch (err) {
            alert('Failed to save file');
        }
    }

    function updatePCode(key, value) {
        if (selectedContour && selectedContour.metadata) {
            selectedContour.metadata[key] = value;
        }
    }
</script>

<div class="view-container">
    <div class="header">
        <h2>GNC Editor</h2>
        <div class="actions">
            <input type="file" id="gnc-upload" accept=".gnc,.nc" onchange={handleFileSelect} class="file-input" />
            <label for="gnc-upload" class="upload-btn">Open File</label>
            {#if filename}
                <span class="filename">{filename}</span>
            {/if}
            <button class="save-btn" onclick={handleSave} disabled={!sheet}>Save Changes</button>
        </div>
    </div>

    <div class="workspace">
        <div class="canvas-area">
            {#if loading}
                <div class="loading">Parsing GNC file...</div>
            {:else if sheet}
                <GncCanvas {sheet} width={800} height={600} on:select={handleContourSelect} />
            {:else}
                <div class="placeholder">
                    <p>No file loaded.</p>
                    <p class="hint">Upload a .GNC file to visualize and edit.</p>
                </div>
            {/if}
        </div>

        <div class="properties-panel">
            <h3>Properties</h3>
            {#if selectedContour}
                <div class="prop-group">
                    <span class="label">Contour ID:</span>
                    <span class="value">#{selectedContour.id}</span>
                </div>
                 <div class="prop-group">
                    <span class="label">Corners:</span>
                    <span class="value">{selectedContour.corner_count}</span>
                </div>

                <h4 class="section-title">Technology Parameters</h4>
                <div class="p-codes-list">
                    {#if selectedContour.metadata}
                        {#each Object.entries(selectedContour.metadata) as [key, value]}
                            {#if key.startsWith('P')}
                                <div class="prop-field">
                                    <label for={key}>{key}</label>
                                    <input
                                        id={key}
                                        type="text"
                                        value={value}
                                        oninput={(e) => updatePCode(key, e.target.value)}
                                    />
                                </div>
                            {/if}
                        {/each}
                    {:else}
                        <p class="empty-props">No technological parameters found.</p>
                    {/if}
                </div>

            {:else}
                <p class="hint-text">Select a contour on the canvas to view and edit its properties.</p>
            {/if}
        </div>
    </div>
</div>

<style>
    .view-container {
        display: flex;
        flex-direction: column;
        height: calc(100vh - 80px); /* Fit within layout */
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    .header {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #f8fafc;
    }
    h2 { margin: 0; font-size: 1.25rem; color: #1e293b; }

    .actions { display: flex; align-items: center; gap: 1rem; }
    .file-input { display: none; }
    .upload-btn {
        background: white;
        border: 1px solid #cbd5e1;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .upload-btn:hover { background: #f1f5f9; }

    .save-btn {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
    }
    .save-btn:disabled { background-color: #94a3b8; cursor: not-allowed; }
    .filename { font-family: monospace; color: #64748b; font-size: 0.9rem; }

    .workspace {
        display: flex;
        flex: 1;
        overflow: hidden;
    }
    .canvas-area {
        flex: 1;
        background: #1e1e1e;
        display: flex;
        justify-content: center;
        align-items: center;
        overflow: auto;
    }
    .placeholder, .loading {
        color: #64748b;
        text-align: center;
    }
    .hint { font-size: 0.875rem; margin-top: 0.5rem; }

    .properties-panel {
        width: 300px;
        border-left: 1px solid #e2e8f0;
        background: white;
        padding: 1.5rem;
        overflow-y: auto;
    }
    .properties-panel h3 { margin-top: 0; margin-bottom: 1rem; font-size: 1.1rem; }

    .prop-group {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    .label { color: #64748b; }
    .value { font-weight: 600; }

    .section-title {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 0.5rem;
    }

    .prop-field {
        margin-bottom: 1rem;
    }
    .prop-field label {
        display: block;
        font-size: 0.875rem;
        color: #475569;
        margin-bottom: 0.25rem;
    }
    .prop-field input {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        font-family: monospace;
    }
    .hint-text { color: #94a3b8; font-size: 0.875rem; font-style: italic; }
</style>
