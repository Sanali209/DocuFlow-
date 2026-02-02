<script>
    import { parseGnc, saveGnc } from "./api";
    import GncCanvas from "./components/GncCanvas.svelte";

    let sheet = $state(null);
    let selectedContour = $state(null);
    let filename = $state("");
    let loading = $state(false);

    // Property panel modes
    let propertyMode = $state("sheet"); // 'sheet' | 'part' | 'contour'
    let selectedPartId = $state(null);

    async function handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        filename = file.name;
        loading = true;
        sheet = null;
        selectedContour = null;

        try {
            sheet = await parseGnc(file);
            console.log("Parsed GNC sheet:", sheet);
            console.log("Parts:", sheet?.parts);
            console.log("Total parts:", sheet?.total_parts);

            // Default to first part if available
            if (sheet?.parts?.length > 0) {
                selectedPartId = sheet.parts[0].id;
            }
        } catch (err) {
            alert("Error parsing GNC file");
            console.error(err);
        } finally {
            loading = false;
        }
    }

    function handleContourSelect(e) {
        const eventData = e.detail;

        if (!eventData) {
            selectedContour = null;
            return;
        }

        // Handle new event structure: { contour, part }
        if (eventData.contour) {
            selectedContour = eventData.contour;

            // If in part mode or switching to it, select the parent part
            if (eventData.part) {
                selectedPartId = eventData.part.id;

                // If not already in part or contour mode, switch to contour mode
                if (propertyMode === "sheet") {
                    propertyMode = "contour";
                }
            } else {
                // Fallback: auto-switch to contour mode
                propertyMode = "contour";
            }
        } else {
            // Legacy: direct contour object
            selectedContour = eventData;
            propertyMode = "contour";
        }
    }

    async function handleSave() {
        if (!sheet || !filename) return;
        try {
            const res = await saveGnc(sheet, filename, true);
            alert(`Saved successfully to ${res.path}`);
        } catch (err) {
            alert("Failed to save file");
        }
    }

    function updatePCode(key, value) {
        if (selectedContour && selectedContour.metadata) {
            selectedContour.metadata[key] = value;
        }
    }

    function updateSheetField(field, value) {
        if (sheet) {
            sheet[field] = value;
        }
    }

    let selectedPart = $derived(
        sheet?.parts?.find((p) => p.id === selectedPartId),
    );
</script>

<div class="view-container">
    <div class="header">
        <h2>GNC Editor</h2>
        <div class="actions">
            <input
                type="file"
                id="gnc-upload"
                accept=".gnc,.nc"
                onchange={handleFileSelect}
                class="file-input"
            />
            <label for="gnc-upload" class="upload-btn">Open File</label>
            {#if filename}
                <span class="filename">{filename}</span>
            {/if}
            <button class="save-btn" onclick={handleSave} disabled={!sheet}
                >Save Changes</button
            >
        </div>
    </div>

    <div class="workspace">
        <div class="canvas-area">
            {#if loading}
                <div class="loading">Parsing GNC file...</div>
            {:else if sheet}
                <GncCanvas
                    {sheet}
                    width={800}
                    height={600}
                    on:select={handleContourSelect}
                />
            {:else}
                <div class="placeholder">
                    <p>No file loaded.</p>
                    <p class="hint">
                        Upload a .GNC file to visualize and edit.
                    </p>
                </div>
            {/if}
        </div>

        <div class="properties-panel">
            <div class="mode-selector">
                <button
                    class:active={propertyMode === "sheet"}
                    onclick={() => (propertyMode = "sheet")}>Sheet</button
                >
                <button
                    class:active={propertyMode === "part"}
                    onclick={() => (propertyMode = "part")}>Part</button
                >
                <button
                    class:active={propertyMode === "contour"}
                    onclick={() => (propertyMode = "contour")}>Contour</button
                >
            </div>

            {#if !sheet}
                <p class="hint-text">Load a GNC file to view properties.</p>
            {:else if propertyMode === "sheet"}
                <!-- Sheet Mode -->
                <h3>Sheet Properties</h3>
                <div class="prop-group">
                    <span class="label">Program Size (mm):</span>
                    <div class="inline-inputs">
                        <input
                            type="number"
                            value={sheet.program_width || 0}
                            oninput={(e) =>
                                updateSheetField(
                                    "program_width",
                                    parseFloat(e.target.value),
                                )}
                            step="0.1"
                        />
                        <span>×</span>
                        <input
                            type="number"
                            value={sheet.program_height || 0}
                            oninput={(e) =>
                                updateSheetField(
                                    "program_height",
                                    parseFloat(e.target.value),
                                )}
                            step="0.1"
                        />
                    </div>
                </div>
                <div class="prop-group">
                    <span class="label">Thickness (mm):</span>
                    <input
                        type="number"
                        value={sheet.thickness || 0}
                        oninput={(e) =>
                            updateSheetField(
                                "thickness",
                                parseFloat(e.target.value),
                            )}
                        step="0.1"
                    />
                </div>
                <div class="prop-group">
                    <span class="label">Cut Count:</span>
                    <input
                        type="number"
                        value={sheet.cut_count || 1}
                        oninput={(e) =>
                            updateSheetField(
                                "cut_count",
                                parseInt(e.target.value),
                            )}
                        min="1"
                    />
                </div>
                <div class="prop-group">
                    <span class="label">Material:</span>
                    <span class="value">{sheet.material || "N/A"}</span>
                </div>
                <div class="prop-group">
                    <span class="label">Total Parts:</span>
                    <span class="value">{sheet.total_parts}</span>
                </div>
                <div class="prop-group">
                    <span class="label">Total Contours:</span>
                    <span class="value">{sheet.total_contours}</span>
                </div>
            {:else if propertyMode === "part"}
                <!-- Part Mode -->
                <h3>Part Properties</h3>
                <div class="prop-group">
                    <span class="label">Select Part:</span>
                    <select bind:value={selectedPartId}>
                        {#each sheet.parts as part}
                            <option value={part.id}
                                >{part.name || `Part ${part.id}`}</option
                            >
                        {/each}
                    </select>
                </div>
                {#if selectedPart}
                    <div class="prop-group">
                        <span class="label">Part Name:</span>
                        <span class="value">{selectedPart.name || "N/A"}</span>
                    </div>
                    <div class="prop-group">
                        <span class="label">Contours:</span>
                        <span class="value">{selectedPart.contours.length}</span
                        >
                    </div>
                    <div class="prop-group">
                        <span class="label">Corner Count:</span>
                        <span class="value">{selectedPart.corner_count}</span>
                    </div>
                {/if}
            {:else if propertyMode === "contour"}
                <!-- Contour Mode -->
                <h3>Contour Properties</h3>
                {#if selectedContour}
                    <div class="prop-group">
                        <span class="label">Contour ID:</span>
                        <span class="value">#{selectedContour.id}</span>
                    </div>
                    <div class="prop-group">
                        <span class="label">Corners:</span>
                        <span class="value">{selectedContour.corner_count}</span
                        >
                    </div>

                    <h4 class="section-title">Technology Parameters</h4>
                    <div class="p-codes-list">
                        {#if selectedContour.metadata}
                            {#each Object.entries(selectedContour.metadata) as [key, value]}
                                {#if key.startsWith("P")}
                                    <div class="prop-field">
                                        <label for={key}>{key}</label>
                                        <input
                                            id={key}
                                            type="text"
                                            {value}
                                            oninput={(e) =>
                                                updatePCode(
                                                    key,
                                                    e.target.value,
                                                )}
                                        />
                                    </div>
                                {/if}
                            {/each}
                        {:else}
                            <p class="empty-props">
                                No technological parameters found.
                            </p>
                        {/if}
                    </div>
                {:else}
                    <p class="hint-text">
                        Select a contour on the canvas to view and edit its
                        properties.
                    </p>
                {/if}
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
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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
    h2 {
        margin: 0;
        font-size: 1.25rem;
        color: #1e293b;
    }

    .actions {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .file-input {
        display: none;
    }
    .upload-btn {
        background: white;
        border: 1px solid #cbd5e1;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .upload-btn:hover {
        background: #f1f5f9;
    }

    .save-btn {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
    }
    .save-btn:disabled {
        background-color: #94a3b8;
        cursor: not-allowed;
    }
    .filename {
        font-family: monospace;
        color: #64748b;
        font-size: 0.9rem;
    }

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
    .placeholder,
    .loading {
        color: #64748b;
        text-align: center;
    }
    .hint {
        font-size: 0.875rem;
        margin-top: 0.5rem;
    }

    .properties-panel {
        width: 300px;
        border-left: 1px solid #e2e8f0;
        background: white;
        padding: 1.5rem;
        overflow-y: auto;
    }
    .properties-panel h3 {
        margin-top: 0;
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }

    .prop-group {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    .label {
        color: #64748b;
    }
    .value {
        font-weight: 600;
    }

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
    .hint-text {
        color: #94a3b8;
        font-size: 0.875rem;
        text-align: center;
        margin-top: 2rem;
    }

    /* Mode Selector */
    .mode-selector {
        display: flex;
        gap: 4px;
        margin-bottom: 1rem;
        background: #f1f5f9;
        padding: 4px;
        border-radius: 6px;
    }
    .mode-selector button {
        flex: 1;
        padding: 0.5rem;
        border: none;
        background: transparent;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 500;
        font-size: 0.875rem;
        color: #64748b;
        transition: all 0.2s;
    }
    .mode-selector button.active {
        background: white;
        color: #3b82f6;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    .mode-selector button:hover:not(.active) {
        color: #1e293b;
    }

    /* Inline Inputs */
    .inline-inputs {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .inline-inputs input {
        flex: 1;
        max-width: 100px;
    }
    .inline-inputs span {
        color: #64748b;
        font-weight: 500;
    }
</style>
