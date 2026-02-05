<script>
    import { onMount } from "svelte";
    import {
        parseGnc,
        saveGnc,
        fetchTasks,
        fetchPartGnc,
        fetchStock,
        fetchMaterials,
        fetchSetting,
    } from "./api"; // Ensure fetchDocumentTasks is available or use fetchTasks
    import GncCanvas from "./components/GncCanvas.svelte";

    // Props
    let { documentId = null } = $props();

    let sheet = $state(null);
    let selectedContour = $state(null);
    let filename = $state("");
    let loading = $state(false);
    let documentTasks = $state([]); // Tasks from the DB
    let unplacedParts = $state([]); // Tasks not in sheet
    let stockItems = $state([]);
    let availableMaterials = $state([]);

    // Property panel modes
    let propertyMode = $state("sheet"); // 'sheet' | 'part' | 'contour' | 'unplaced'
    let selectedPartId = $state(null);

    // Derived: Tasks that have not been placed
    // We match by... name? Or if we have metadata.
    // For now, let's assume we list all tasks and user drags them in.
    // If a GNC file is loaded, we try to match existing parts.

    async function loadDocumentData() {
        if (!documentId) return;
        try {
            documentTasks = await fetchTasks(documentId);
            // Initial unplaced calculation: filtered by "placed" status if we track it
            // Or just list them all for now
            updateUnplacedParts();
        } catch (e) {
            console.error("Failed to load tasks", e);
        }
    }

    async function loadStockData() {
        try {
            const [stocks, mats] = await Promise.all([
                fetchStock(),
                fetchMaterials(),
            ]);
            stockItems = stocks;
            availableMaterials = mats;
        } catch (e) {
            console.error("Failed to load stock data", e);
        }
    }

    function handleStockSelect(e) {
        if (!sheet) {
            alert("No active sheet to update.");
            e.target.value = "";
            return;
        }

        const itemId = parseInt(e.target.value);
        if (!itemId) return; // "Select Stock" option

        const item = stockItems.find((i) => i.id === itemId);
        if (!item) return;

        const confirmMsg = `Update sheet dimensions to ${item.width}x${item.height} (${item.material?.name})?`;
        if (confirm(confirmMsg)) {
            pushState(); // Save state before resize
            sheet.program_width = item.width;
            sheet.program_height = item.height;
            sheet.thickness = 0; // Stock doesn't strictly have thickness in GNC usually, but we can set it if available
            // Material name
            if (item.material) {
                sheet.material = item.material.name;
            }
        } else {
            e.target.value = ""; // Revert selection
        }
    }

    function updateUnplacedParts() {
        if (!documentTasks || documentTasks.length === 0) return;

        if (!sheet) {
            unplacedParts = [...documentTasks];
            return;
        }

        // Get list of task IDs currently on the sheet
        const placedTaskIds = new Set(
            sheet.parts.filter((p) => p.taskId).map((p) => p.taskId),
        );

        // Filter out placed tasks
        unplacedParts = documentTasks.filter((t) => !placedTaskIds.has(t.id));
    }

    function handleDragStart(e, task) {
        e.dataTransfer.setData("text/plain", JSON.stringify(task));
        e.dataTransfer.effectAllowed = "copy";
    }

    // Undo/Redo History
    let history = $state([]);
    let historyIndex = $state(-1);

    function pushState() {
        if (!sheet) return;
        // Deep clone sheet to store in history
        const state = JSON.parse(JSON.stringify(sheet));

        // If we are in the middle of history, truncate future
        if (historyIndex < history.length - 1) {
            history = history.slice(0, historyIndex + 1);
        }

        history.push(state);
        historyIndex++;

        // Limit history size?
        if (history.length > 50) {
            history.shift();
            historyIndex--;
        }
    }

    function undo() {
        if (historyIndex > 0) {
            historyIndex--;
            sheet = JSON.parse(JSON.stringify(history[historyIndex]));
            updateUnplacedParts(); // Re-calc unplaced based on restored sheet
        }
    }

    function redo() {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            sheet = JSON.parse(JSON.stringify(history[historyIndex]));
            updateUnplacedParts();
        }
    }

    async function handlePlacePart(task) {
        if (!sheet) {
            alert("Please create or load a sheet first.");
            return;
        }

        try {
            pushState(); // Save state before placing

            // 1. Get Part ID.
            let partId = null;
            if (task.part_associations && task.part_associations.length > 0) {
                partId = task.part_associations[0].part_id;
            } else {
                console.warn("No part association found for task", task);
                alert("This task is not linked to a part geometry.");
                return;
            }

            // 2. Fetch GNC
            const partSheet = await fetchPartGnc(partId);
            if (
                !partSheet ||
                !partSheet.parts ||
                partSheet.parts.length === 0
            ) {
                alert("No geometry found for this part.");
                return;
            }

            // 3. Add to Sheet
            const partDef = partSheet.parts[0]; // The part definition

            const newPartId = Math.max(...sheet.parts.map((p) => p.id), 0) + 1;
            const newPart = {
                ...partDef,
                id: newPartId,
                name: task.name,
                taskId: task.id, // Link back to task for "Unplace" logic
                metadata: {
                    ...(partDef.metadata || {}),
                    source_part_id: partId,
                },
                x: 10,
                y: 10,
            };

            sheet.parts = [...sheet.parts, newPart];
            sheet.total_parts = sheet.parts.length;

            // 4. Update Unplaced
            updateUnplacedParts();
        } catch (e) {
            console.error(e);
            alert("Failed to place part.");
        }
    }

    function handleRemovePart(partId) {
        if (!sheet) return;
        const part = sheet.parts.find((p) => p.id === partId);
        if (!part) return;

        pushState(); // Save state before removing

        // Remove from sheet
        sheet.parts = sheet.parts.filter((p) => p.id !== partId);
        sheet.total_parts = sheet.parts.length;

        // Deselect if removed
        if (selectedPartId === partId) {
            selectedPartId = null;
            propertyMode = "sheet";
        }

        // Update unplaced list
        updateUnplacedParts();
    }

    let nestingWorker = null;
    let isNesting = $state(false);
    let nestingProgress = $state(0);

    onMount(() => {
        loadStockData();
        if (documentId) loadDocumentData();

        // Initialize Worker
        if (window.Worker) {
            nestingWorker = new Worker(
                new URL("./workers/NestingWorker.js", import.meta.url),
                { type: "module" },
            );
            nestingWorker.onmessage = (e) => {
                const { type, payload } = e.data;
                if (type === "PROGRESS") {
                    nestingProgress = payload;
                } else if (type === "COMPLETE") {
                    isNesting = false;
                    const { parts } = payload;
                    // Update sheet parts with new positions
                    // We need to match by ID or index. Worker returns full parts list with X/Y updated.
                    updateSheetPartsFromNest(parts);
                    alert("Nesting complete!");
                } else if (type === "STOPPED") {
                    isNesting = false;
                }
            };
        }
    });

    function updateSheetPartsFromNest(nestedParts) {
        if (!sheet) return;

        // Map nested parts back to sheet parts
        // Ensure we preserve other metadata
        sheet.parts = sheet.parts.map((p) => {
            const nested = nestedParts.find((np) => np.id === p.id);
            if (nested) {
                return {
                    ...p,
                    x: nested.x,
                    y: nested.y,
                    rotation: nested.rotation || 0,
                };
            }
            return p;
        });
        pushState(); // Save state
    }

    async function startAutoNest() {
        if (!nestingWorker || !sheet) return;
        if (isNesting) {
            nestingWorker.postMessage({ type: "STOP_NESTING" });
            return;
        }

        let rotations = 4;
        let population = 10;

        try {
            const [rotRes, popRes] = await Promise.all([
                fetchSetting("nesting_rotations").catch(() => ({ value: "4" })),
                fetchSetting("nesting_population").catch(() => ({
                    value: "10",
                })),
            ]);
            rotations = parseInt(rotRes.value) || 4;
            population = parseInt(popRes.value) || 10;
        } catch (e) {
            console.warn("Using default nesting settings", e);
        }

        const config = {
            rotations,
            population,
        };

        // Prepare data for worker
        nestingWorker.postMessage({
            type: "START_NESTING",
            payload: {
                sheet: {
                    width: sheet.program_width,
                    height: sheet.program_height,
                },
                parts: JSON.parse(JSON.stringify(sheet.parts)),
                config,
            },
        });
        isNesting = true;
        nestingProgress = 0;
    }

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

    async function handleSaveAsNewOrder() {
        if (!sheet) return;
        const name = prompt("Enter name for the new Order:");
        if (!name) return;

        try {
            // Need to import saveAsNewOrder
            const { saveAsNewOrder } = await import("./api");
            const res = await saveAsNewOrder(name, sheet, documentId);
            alert(`New Order "${res.name}" created successfully!`);
            // Redirect?
            // push(`/documents/${res.id}/gnc`); // Need navigate
        } catch (e) {
            console.error(e);
            alert("Failed to save as new order: " + e.message);
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
            <button
                class="icon-btn"
                onclick={undo}
                disabled={historyIndex <= 0}
                title="Undo">↩</button
            >
            <button
                class="icon-btn"
                onclick={redo}
                disabled={historyIndex >= history.length - 1}
                title="Redo">↪</button
            >
            <button class="save-btn" onclick={handleSave} disabled={!sheet}
                >Save Changes</button
            >
            <button
                class="save-btn"
                onclick={startAutoNest}
                disabled={!sheet}
                style="background-color: {isNesting ? '#ef4444' : '#8b5cf6'};"
            >
                {isNesting ? `Stop Nesting (${nestingProgress}%)` : "Auto Nest"}
            </button>
            <button
                class="save-btn"
                onclick={handleSaveAsNewOrder}
                disabled={!sheet}
                style="background-color: #10b981;">Save as New Order</button
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
                    <span class="label">Stock Size:</span>
                    <select onchange={handleStockSelect}>
                        <option value="">-- Select Stock --</option>
                        {#each stockItems as item}
                            <option value={item.id}>
                                {item.material?.name || "Unknown"} - {item.width}x{item.height}
                            </option>
                        {/each}
                    </select>
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
                <button
                    class:active={propertyMode === "unplaced"}
                    onclick={() => (propertyMode = "unplaced")}>Unplaced</button
                >
                <button
                    class="delete-btn"
                    onclick={() => handleRemovePart(selectedPartId)}
                    >Remove Part</button
                >
            {:else if propertyMode === "unplaced"}
                <h3>Unplaced Parts</h3>
                {#if unplacedParts.length === 0}
                    <p class="hint">No unplaced parts.</p>
                {:else}
                    <div class="part-list">
                        {#each unplacedParts as task}
                            <div
                                class="part-item"
                                draggable="true"
                                ondragstart={(e) => handleDragStart(e, task)}
                                onclick={() => handlePlacePart(task)}
                            >
                                <span class="name">{task.name}</span>
                                <button class="add-btn">+</button>
                            </div>
                        {/each}
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
