<script lang="ts">
    import GncCanvas from '$lib/components/GncCanvas.svelte';
    import type { GNCSheet } from '$lib/types/gnc';

    let fileInput: HTMLInputElement;
    let sheet: GNCSheet | null = null;
    let isLoading = false;
    let error: string | null = null;

    async function handleFileUpload() {
        if (!fileInput.files || fileInput.files.length === 0) return;

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        isLoading = true;
        error = null;
        sheet = null;

        try {
            // Determine API URL (assuming relative path for same-origin or configured proxy)
            const response = await fetch('http://localhost:8000/api/parse-gnc', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Failed to parse file: ${response.statusText}`);
            }

            sheet = await response.json();
        } catch (e: any) {
            error = e.message;
            console.error(e);
        } finally {
            isLoading = false;
        }
    }
</script>

<div class="gnc-editor-container">
    <header>
        <h1>GNC Editor & Visualizer</h1>
        <div class="controls">
            <input
                type="file"
                accept=".gnc,.txt,.cnc"
                bind:this={fileInput}
                on:change={handleFileUpload}
                class="file-input"
            />
            {#if isLoading}
                <span class="loading">Processing...</span>
            {/if}
        </div>
        {#if error}
            <div class="error">{error}</div>
        {/if}
    </header>

    <div class="workspace">
        <div class="canvas-area">
            {#if sheet}
                <GncCanvas {sheet} width={1000} height={700} />
            {:else}
                <div class="placeholder">
                    <p>Upload a GNC file to visualize</p>
                </div>
            {/if}
        </div>

        <div class="info-panel">
            {#if sheet}
                <h2>File Stats</h2>
                <div class="stat-group">
                    <div class="stat">
                        <label>Parts</label>
                        <span>{sheet.total_parts}</span>
                    </div>
                    <div class="stat">
                        <label>Contours</label>
                        <span>{sheet.total_contours}</span>
                    </div>
                </div>

                <h3>Parts List</h3>
                <ul class="part-list">
                    {#each sheet.parts as part}
                        <li>
                            <strong>{part.name || `Part ${part.id}`}</strong>
                            <small>({part.contours.length} contours)</small>
                        </li>
                    {/each}
                </ul>
            {/if}
        </div>
    </div>
</div>

<style>
    .gnc-editor-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        background-color: #121212;
        color: #e0e0e0;
        padding: 1rem;
        box-sizing: border-box;
    }

    header {
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    h1 {
        font-size: 1.5rem;
        margin: 0;
        color: #64ffda;
    }

    .controls {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .file-input {
        background: #333;
        padding: 0.5rem;
        border-radius: 4px;
        color: white;
    }

    .loading {
        color: #ff9800;
    }

    .error {
        color: #ff5252;
        background: rgba(255, 82, 82, 0.1);
        padding: 0.5rem;
        border-radius: 4px;
    }

    .workspace {
        display: flex;
        flex: 1;
        gap: 1rem;
        overflow: hidden;
    }

    .canvas-area {
        flex: 3;
        background: #000;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        border: 1px solid #333;
    }

    .placeholder {
        color: #666;
        font-style: italic;
    }

    .info-panel {
        flex: 1;
        background: #1e1e1e;
        padding: 1rem;
        border-radius: 8px;
        overflow-y: auto;
        min-width: 250px;
    }

    h2, h3 {
        margin-top: 0;
        border-bottom: 1px solid #333;
        padding-bottom: 0.5rem;
    }

    .stat-group {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .stat {
        display: flex;
        flex-direction: column;
    }

    .stat label {
        font-size: 0.8rem;
        color: #888;
    }

    .stat span {
        font-size: 1.2rem;
        font-weight: bold;
    }

    .part-list {
        list-style: none;
        padding: 0;
    }

    .part-list li {
        padding: 0.5rem;
        border-bottom: 1px solid #333;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .part-list li small {
        color: #888;
    }
</style>
