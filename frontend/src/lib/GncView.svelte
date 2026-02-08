<script>
    import { onMount } from "svelte";
    import { push } from "./Router.svelte";
    import {
        gncService,
        productionService,
        inventoryService,
        settingService,
        docService,
    } from "./stores/services.js";
    import { uiState } from "./stores/appState.svelte.js";
    import { setMenuActions, clearMenuActions } from "./appState.svelte.js";
    import GncCanvas from "./components/GncCanvas.svelte";

    // Props
    let { documentId = null, orderId = null } = $props();

    let sheets = $state([]); // Supports multiple sheets
    let activeSheetIndex = $state(0);
    let sheet = $derived(sheets[activeSheetIndex] || null);

    let selectedContour = $state(null);
    let filename = $state("");
    let loading = $state(false);
    let showDebug = $state(false);
    let documentTasks = $state([]); // Tasks from the DB/Order
    let inventory = $state([]); // Refined inventory: includes placed/total counts
    let libraryParts = $state([]); // Parts from library
    let materials = $state([]); // Available materials

    // Property panel modes
    let propertyMode = $state("sheet"); // 'sheet' | 'part' | 'contour' | 'inventory' | 'stock'
    let selectedPartId = $state(null);
    let libraryPageSize = $state(24);

    let inventorySearch = $state("");
    let libraryPage = $state(1);

    let nestingMode = $state("hull"); // 'bbox' | 'hull'

    const filteredInventory = $derived(
        inventory.filter((item) =>
            item.name.toLowerCase().includes(inventorySearch.toLowerCase()),
        ),
    );

    const filteredLibrary = $derived(
        libraryParts.filter((part) =>
            part.name.toLowerCase().includes(inventorySearch.toLowerCase()),
        ),
    );

    const totalLibraryPages = $derived(
        Math.ceil(filteredLibrary.length / libraryPageSize),
    );

    const paginatedLibrary = $derived(
        filteredLibrary.slice(
            (libraryPage - 1) * libraryPageSize,
            libraryPage * libraryPageSize,
        ),
    );

    $effect(() => {
        // Reset page if search changes
        inventorySearch;
        libraryPage = 1;
    });

    // Derived: Tasks that have not been placed
    // We match by... name? Or if we have metadata.
    // For now, let's assume we list all tasks and user drags them in.
    // If a GNC file is loaded, we try to match existing parts.

    async function loadDocumentData() {
        const id = orderId || documentId;
        if (!id) return;
        try {
            if (orderId) {
                documentTasks =
                    await productionService.fetchOrderTasks(orderId);
                // Attempt to load full nesting project if editing an order
                await loadProjectState();
            } else {
                // In the new system, jobs are fetched via productionService
                // Fetching all tasks for a document
                documentTasks = await productionService.fetchJobs(0, 1000, {
                    document_id: documentId,
                });
            }
            updateInventory();
        } catch (e) {
            console.error("Failed to load tasks", e);
            uiState.addNotification("Failed to load document tasks", "error");
        }
    }

    async function loadProjectState() {
        if (!orderId) return;
        try {
            loading = true;
            const project =
                await productionService.fetchOrderNestingProject(orderId);
            if (project && project.sheets) {
                sheets = project.sheets.map((s) => ({
                    ...s.data,
                    name: s.name,
                    task_id: s.data.task_id || null,
                }));
                if (sheets.length > 0) {
                    activeSheetIndex = 0;
                }
            }
        } catch (e) {
            console.warn(
                "No existing nesting project found for this order, starting fresh.",
                e,
            );
        } finally {
            loading = false;
        }
    }

    async function handleFileSelect(e) {
        // Handle file selection from input element or other source
        const file = e.target ? e.target.files[0] : e;
        if (!file) return;

        filename = file.name;
        loading = true;
        sheets = [];
        activeSheetIndex = 0;
        selectedContour = null;

        try {
            const parsedSheet = await gncService.parseGnc(file);
            sheets = [parsedSheet];
            updateInventory();

            if (parsedSheet?.parts?.length > 0) {
                selectedPartId = parsedSheet.parts[0].id;
            }
            // Trigger analysis immediately to get debug data
            if (nestingWorker) {
                // CLONE to avoid Proxy issues
                const sheetData = JSON.parse(JSON.stringify(parsedSheet));
                nestingWorker.postMessage({
                    type: "ANALYZE_SHEET",
                    payload: { sheet: sheetData },
                });
            }
            uiState.addNotification("GNC file parsed successfully", "info");
        } catch (err) {
            console.error(err);
            uiState.addNotification("Error parsing GNC file", "error");
        } finally {
            loading = false;
        }
    }

    function triggerFileUpload() {
        document.getElementById("gnc-upload-input").click();
    }

    function updateInventory() {
        if (!documentTasks || documentTasks.length === 0) {
            inventory = [];
            return;
        }

        // Calculate placed counts across ALL sheets
        const placedCounts = {};
        sheets.forEach((sh) => {
            sh.parts.forEach((p) => {
                const taskId = p.taskId;
                if (taskId) {
                    placedCounts[taskId] = (placedCounts[taskId] || 0) + 1;
                }
            });
        });

        inventory = documentTasks.map((t) => {
            // Determine total needed from task name/content or metadata if available
            // For now, assume 1 per task or check if task has quantity
            const total = t.quantity || 1;
            const placed = placedCounts[t.id] || 0;
            return {
                ...t,
                placed,
                total,
                remaining: Math.max(0, total - placed),
            };
        });
    }

    // Sheet Management
    function addSheet(template = null) {
        const newSheet = {
            parts: [],
            metadata: {},
            total_parts: 0,
            total_contours: 0,
            program_width: template?.width || 3000,
            program_height: template?.height || 1500,
            thickness: 0,
            cut_count: 1,
            material: template?.material || "Steel",
            name: template?.name || `Sheet ${sheets.length + 1}`,
            task_id: template?.task_id || null,
        };
        sheets = [...sheets, newSheet];
        activeSheetIndex = sheets.length - 1;
        pushState();
    }

    function removeSheet(index) {
        if (sheets.length <= 1) return;
        sheets = sheets.filter((_, i) => i !== index);
        if (activeSheetIndex >= sheets.length) {
            activeSheetIndex = sheets.length - 1;
        }
        pushState();
        updateInventory();
    }

    function handleDragStart(e, task) {
        e.dataTransfer.setData("text/plain", JSON.stringify(task));
        e.dataTransfer.effectAllowed = "copy";
    }

    // Undo/Redo History
    let history = $state([]);
    let historyIndex = $state(-1);

    function pushState() {
        if (sheets.length === 0) return;
        const state = JSON.parse(JSON.stringify(sheets));

        if (historyIndex < history.length - 1) {
            history = history.slice(0, historyIndex + 1);
        }

        history.push(state);
        historyIndex++;

        if (history.length > 50) {
            history.shift();
            historyIndex--;
        }
    }

    function undo() {
        if (historyIndex > 0) {
            historyIndex--;
            sheets = JSON.parse(JSON.stringify(history[historyIndex]));
            updateInventory();
        }
    }

    function redo() {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            sheets = JSON.parse(JSON.stringify(history[historyIndex]));
            updateInventory();
        }
    }

    async function handlePlacePart(item) {
        if (!sheet) {
            alert("Please create or load a sheet first.");
            return;
        }

        if (item.remaining <= 0 && !inventory.find((i) => i.id === item.id)) {
            // If it's a library part not in inventory, we can still place it
        } else if (item.remaining <= 0) {
            alert("All instances of this task are already placed.");
            return;
        }

        try {
            pushState();

            let partId = null;
            if (item.part_associations && item.part_associations.length > 0) {
                partId = item.part_associations[0].part_id;
            } else if (item.id && !item.document_id) {
                // Library part
                partId = item.id;
            } else {
                alert("This task is not linked to a part geometry.");
                return;
            }

            const partSheet = await inventoryService.fetchPartGnc(partId);
            if (
                !partSheet ||
                !partSheet.parts ||
                partSheet.parts.length === 0
            ) {
                uiState.addNotification(
                    "No geometry found for this part",
                    "warning",
                );
                return;
            }

            console.log("Placed Part GNC Data:", {
                partId,
                totalPartsInGnc: partSheet.parts.length,
                firstPartContours: partSheet.parts[0].contours.length,
                allParts: partSheet.parts.map((p) => ({
                    name: p.name,
                    contours: p.contours.length,
                })),
            });

            // Find the correct part by name or registration number within the GNC file
            let partDef = partSheet.parts.find(
                (p) =>
                    p.name &&
                    (p.name.includes(item.name) || item.name.includes(p.name)),
            );

            if (!partDef) {
                console.warn(
                    `Could not find geometry matching name "${item.name}", defaulting to first part.`,
                );
                partDef = partSheet.parts[0];
            }
            const newPartId =
                Math.max(
                    ...sheets.flatMap((s) => s.parts).map((p) => p.id),
                    0,
                ) + 1;

            const margin = 50;
            const sheetW = sheet.program_width || 2000;
            const sheetH = sheet.program_height || 1000;

            const randX =
                margin + Math.random() * Math.max(0, sheetW - margin * 2 - 200);
            const randY =
                margin + Math.random() * Math.max(0, sheetH - margin * 2 - 200);

            const newPart = {
                ...partDef,
                id: newPartId,
                name: item.name,
                taskId: item.id,
                metadata: {
                    ...(partDef.metadata || {}),
                    source_part_id: partId,
                },
                x: randX,
                y: randY,
            };

            sheet.parts = [...sheet.parts, newPart];
            sheet.total_parts = sheet.parts.length;
            sheet.total_parts = sheet.parts.length;
            updateInventory();
            if (nestingWorker) {
                // CLONE the sheet to avoid sending Proxies (Svelte 5 $state) to worker
                const sheetData = JSON.parse(JSON.stringify(sheet));
                nestingWorker.postMessage({
                    type: "ANALYZE_SHEET",
                    payload: { sheet: sheetData },
                });
            }
        } catch (e) {
            console.error(e);
            alert("Failed to place part.");
        }
    }

    function handleRemovePart(partId) {
        if (!sheet) return;

        pushState();
        sheet.parts = sheet.parts.filter((p) => p.id !== partId);
        sheet.total_parts = sheet.parts.length;

        if (selectedPartId === partId) {
            selectedPartId = null;
            propertyMode = "sheet";
        }

        updateInventory();
    }

    let nestingWorker = null;
    let isNesting = $state(false);
    let nestingProgress = $state(0);

    $effect(() => {
        if (orderId || documentId) {
            loadDocumentData();
        }
    });

    onMount(() => {
        inventoryService
            .fetchLibraryParts()
            .then((lib) => (libraryParts = lib))
            .catch(console.error);

        inventoryService
            .fetchMaterials()
            .then((m) => (materials = m))
            .catch(console.error);
        settingService
            .fetchSetting("gnc_library_page_size")
            .then((res) => {
                if (res.value) libraryPageSize = parseInt(res.value);
            })
            .catch(() => {});

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
                    console.log("COMPLETE payload", payload);
                    const { sheets: newSheets } = payload;
                    sheets = newSheets;
                    updateInventory();
                    pushState();
                    alert("Nesting complete!");
                } else if (type === "STOPPED") {
                    isNesting = false;
                } else if (type === "ANALYSIS_COMPLETE") {
                    // Update sheet parts with analyzed data (polygon, minX, minY)
                    const { sheetId, parts } = payload;
                    const sheetIdx = sheets.findIndex(
                        (s) =>
                            s.id === sheetId ||
                            (s.id === undefined && sheetId === undefined),
                    ); // Check handling of IDs
                    if (sheetIdx !== -1) {
                        sheets[sheetIdx].parts = parts;
                        // Force update of derived sheet if active
                        if (activeSheetIndex === sheetIdx) {
                            sheets = [...sheets];
                        }
                        console.log("Analysis complete for sheet", sheetId);
                    }
                }
            };
        }

        setMenuActions([
            {
                label: "File",
                items: [
                    { label: "Open File", action: triggerFileUpload },
                    { label: "Save Changes", action: handleSave },
                    {
                        label: "Save as New Order",
                        action: handleSaveAsNewOrder,
                    },
                ],
            },
            {
                label: "Edit",
                items: [
                    { label: "Undo", action: undo },
                    { label: "Redo", action: redo },
                ],
            },
            {
                label: "Nesting",
                items: [
                    { label: "Auto Nest", action: () => startAutoNest(false) },
                    { label: "Re-nest All", action: () => startAutoNest(true) },
                    { label: "Unplace All", action: unplaceAll },
                ],
            },
        ]);

        return () => {
            clearMenuActions();
            if (nestingWorker) nestingWorker.terminate();
        };
    });

    function unplaceAll() {
        if (!sheet) return;
        pushState();
        sheet.parts = [];
        updateInventory();
    }

    async function startAutoNest(isReNest = false) {
        if (!nestingWorker || sheets.length === 0) return;
        if (isNesting) {
            nestingWorker.postMessage({ type: "STOP_NESTING" });
            return;
        }

        let tasksToNest = [];
        if (isReNest) {
            // 1. Start with full quantities of all document tasks
            tasksToNest = JSON.parse(JSON.stringify(inventory)).map((item) => {
                item.remaining = item.total;
                return item;
            });

            // 2. Add library parts that are currently placed on sheets
            sheets.forEach((sh) => {
                sh.parts.forEach((p) => {
                    const isInInventory = inventory.some(
                        (inv) => inv.id === p.taskId,
                    );
                    if (!isInInventory) {
                        // Check if we already added this library part to the pool
                        let existing = tasksToNest.find(
                            (t) => t.id === (p.taskId || p.id),
                        );
                        if (existing) {
                            existing.remaining++;
                            existing.total++;
                        } else {
                            tasksToNest.push({
                                ...p,
                                id: p.taskId || p.id,
                                total: 1,
                                remaining: 1,
                                isLibraryPart: true,
                            });
                        }
                    }
                });
            });

            // 3. Clear all sheets for a fresh start
            pushState();
            sheets.forEach((sh) => {
                sh.parts = [];
            });
            updateInventory();
        } else {
            tasksToNest = JSON.parse(
                JSON.stringify(inventory.filter((i) => i.remaining > 0)),
            );
        }

        isNesting = true;
        nestingProgress = 0;

        console.log(
            `GncView: Preparing geometries for ${tasksToNest.length} items (isReNest: ${isReNest})`,
        );

        for (let item of tasksToNest) {
            if (item.contours && item.contours.length > 0) continue;

            let partId = null;
            if (item.part_associations && item.part_associations.length > 0) {
                partId = item.part_associations[0].part_id;
            } else if (item.id && !item.document_id) {
                partId = item.id;
            }

            if (partId) {
                try {
                    const partSheet =
                        await inventoryService.fetchPartGnc(partId);
                    if (partSheet?.parts?.length > 0) {
                        let partDef =
                            partSheet.parts.find(
                                (p) =>
                                    p.name &&
                                    (p.name.includes(item.name) ||
                                        item.name.includes(p.name)),
                            ) || partSheet.parts[0];

                        item.contours = partDef.contours;
                        // Map taskId for identification
                        item.taskId = item.id;
                    }
                } catch (e) {
                    console.error(
                        `GncView: Failed to fetch geometry for ${item.name}`,
                        e,
                    );
                }
            }
        }

        let rotations = 4;
        let population = 10;
        let spacing = 5;

        try {
            const [rotRes, popRes, spacRes] = await Promise.all([
                settingService
                    .fetchSetting("nesting_rotations")
                    .catch(() => ({ value: "4" })),
                settingService.fetchSetting("nesting_population").catch(() => ({
                    value: "10",
                })),
                settingService.fetchSetting("nesting_spacing").catch(() => ({
                    value: "5",
                })),
            ]);
            rotations = parseInt(rotRes.value) || 4;
            population = parseInt(popRes.value) || 10;
            spacing = parseFloat(spacRes.value) || 5;
        } catch (e) {
            console.warn("Using default nesting settings", e);
        }

        const config = {
            rotations,
            population,
            spacing,
            multiSheet: true,
            nestingMode,
        };

        nestingWorker.postMessage({
            type: "START_NESTING",
            payload: {
                sheets: JSON.parse(JSON.stringify(sheets)),
                inventory: JSON.parse(JSON.stringify(tasksToNest)),
                stock: [],
                config,
            },
        });
    }

    function handleContourSelect(hit) {
        if (!hit) {
            selectedContour = null;
            return;
        }

        if (hit.contour) {
            selectedContour = hit.contour;

            if (hit.part) {
                selectedPartId = hit.part.id;

                if (propertyMode === "sheet") {
                    propertyMode = "contour";
                }
            } else {
                propertyMode = "contour";
            }
        }
    }

    async function handleSave() {
        if (sheets.length === 0) return;
        try {
            loading = true;
            const project = {
                order_id: orderId,
                name: filename || "Nesting Project",
                sheets: sheets.map((s, i) => ({
                    id: i,
                    name: s.name || `Sheet ${i + 1}`,
                    data: s,
                })),
                inventory: documentTasks,
                stock: [],
            };

            if (orderId) {
                await productionService.saveOrderNesting(project);
            } else {
                // Legacy single save
                await gncService.saveGnc(sheet, filename, true);
            }
            uiState.addNotification("Project saved successfully", "info");
        } catch (err) {
            console.error(err);
            uiState.addNotification("Failed to save project", "error");
        } finally {
            loading = false;
        }
    }

    async function handleSaveAsNewOrder() {
        if (sheets.length === 0) return;
        const name = prompt("Enter name for the new Order:");
        if (!name) return;

        try {
            const allSheets = sheets.map((s, i) => ({
                name: s.metadata?.program_name || `Sheet ${i + 1}`,
                data: s,
            }));

            const res = await productionService.saveAsNewOrder(
                name,
                allSheets,
                documentId,
            );
            uiState.addNotification(`New Order "${res.name}" created`, "info");
            // Redirect to the new order
            push(`/gnc?orderId=${res.id}`);
            // Force reload data
            orderId = res.id;
            loadDocumentData();
        } catch (e) {
            console.error(e);
            uiState.addNotification("Failed to save as new order", "error");
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
        <!-- Actions are now in the global menu -->
        <input
            type="file"
            id="gnc-upload-input"
            accept=".gnc,.nc"
            onchange={handleFileSelect}
            class="hidden-input"
        />
        {#if filename}
            <span class="filename">{filename}</span>
        {/if}
        <div class="nest-controls">
            <select bind:value={nestingMode} class="nest-mode-select">
                <option value="hull">Precise Hull</option>
                <option value="bbox">Bounding Box</option>
            </select>
            <label class="debug-toggle">
                <input type="checkbox" bind:checked={showDebug} />
                Debug
            </label>
        </div>
    </div>

    <div class="sheet-tabs">
        {#each sheets as s, i}
            <div class="tab-wrapper" class:active={activeSheetIndex === i}>
                <button
                    class="sheet-tab"
                    onclick={() => (activeSheetIndex = i)}
                >
                    {s.name || `Sheet ${i + 1}`}
                </button>
                <button class="close-tab" onclick={() => removeSheet(i)}
                    >×</button
                >
            </div>
        {/each}
        <button class="add-sheet-btn" onclick={() => addSheet()}
            >+ Add Sheet</button
        >
    </div>

    <div class="workspace">
        <div class="canvas-area">
            {#if loading}
                <div class="loading">Processing...</div>
            {:else if sheet}
                <GncCanvas
                    {sheet}
                    {showDebug}
                    {nestingMode}
                    onselect={handleContourSelect}
                    onAreaChange={(area) => {
                        sheet.nestingArea = area;
                        pushState();
                    }}
                />
            {:else}
                <div class="placeholder">
                    <p>No sheet active.</p>
                    <button class="btn-primary" onclick={() => addSheet()}
                        >Create Blank Sheet</button
                    >
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
                <button
                    class:active={propertyMode === "inventory"}
                    onclick={() => (propertyMode = "inventory")}
                    >Inventory</button
                >
            </div>

            {#if !sheet}
                <p class="hint-text">Select or create a sheet.</p>
            {:else if propertyMode === "sheet"}
                <!-- Sheet Mode -->
                <h3>Sheet Properties</h3>
                <div class="prop-group">
                    <span class="label">Sheet Name:</span>
                    <input
                        type="text"
                        value={sheet.name || ""}
                        oninput={(e) =>
                            updateSheetField("name", e.currentTarget.value)}
                        placeholder="Sheet Name"
                    />
                </div>
                <div class="prop-group">
                    <span class="label">Program Size (mm):</span>
                    <div class="inline-inputs">
                        <input
                            type="number"
                            value={sheet.program_width || 0}
                            oninput={(e) =>
                                updateSheetField(
                                    "program_width",
                                    parseFloat(e.currentTarget.value),
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
                                    parseFloat(e.currentTarget.value),
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
                                parseFloat(e.currentTarget.value),
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
                                parseInt(e.currentTarget.value),
                            )}
                        min="1"
                    />
                </div>
                <div class="prop-group">
                    <span class="label">Material:</span>
                    <select
                        value={sheet.material || ""}
                        onchange={(e) =>
                            updateSheetField("material", e.currentTarget.value)}
                    >
                        <option value="">Select Material</option>
                        {#each materials as material}
                            <option value={material.name}
                                >{material.name}</option
                            >
                        {/each}
                    </select>
                </div>
                <div class="prop-group">
                    <span class="label">Total Parts:</span>
                    <span class="value">{sheet.total_parts}</span>
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
                {/if}
                <button
                    class="delete-btn"
                    onclick={() => handleRemovePart(selectedPartId)}
                    >Remove Part</button
                >
            {:else if propertyMode === "inventory"}
                <h3>Inventory</h3>

                <div class="search-bar">
                    <input
                        type="text"
                        placeholder="Search parts..."
                        bind:value={inventorySearch}
                    />
                </div>

                <div class="inventory-list">
                    {#each filteredInventory as item}
                        <div
                            class="inventory-item"
                            class:complete={item.remaining === 0}
                        >
                            <div class="info">
                                <span class="name">{item.name}</span>
                                <span class="stats"
                                    >{item.placed} / {item.total}</span
                                >
                            </div>
                            <button
                                class="add-btn"
                                onclick={() => handlePlacePart(item)}
                                disabled={item.remaining <= 0}>+</button
                            >
                        </div>
                    {/each}
                    {#if filteredInventory.length === 0}
                        <p class="empty-text">No matching tasks.</p>
                    {/if}
                </div>

                <h4 class="section-title">Library Parts</h4>
                <div class="library-grid">
                    {#each paginatedLibrary as part}
                        <button
                            class="lib-item"
                            onclick={() => handlePlacePart(part)}
                        >
                            {part.name}
                        </button>
                    {/each}
                    {#if filteredLibrary.length === 0}
                        <p class="empty-text">No matching library parts.</p>
                    {/if}
                </div>

                {#if totalLibraryPages > 1}
                    <div class="pagination-controls">
                        <button
                            class="page-btn"
                            disabled={libraryPage === 1}
                            onclick={() => libraryPage--}
                        >
                            ←
                        </button>
                        <span class="page-info"
                            >Page {libraryPage} of {totalLibraryPages}</span
                        >
                        <button
                            class="page-btn"
                            disabled={libraryPage === totalLibraryPages}
                            onclick={() => libraryPage++}
                        >
                            →
                        </button>
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

                    <h4 class="section-title">P-Codes</h4>
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
                                                    e.currentTarget.value,
                                                )}
                                        />
                                    </div>
                                {/if}
                            {/each}
                        {:else}
                            <p class="empty-props">No parameters found.</p>
                        {/if}
                    </div>
                {/if}
            {/if}
        </div>
    </div>
</div>

<style>
    .view-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        max-height: calc(100vh - 64px); /* Account for header if any */
        overflow: hidden;
    }

    .hidden-input {
        display: none;
    }

    .sheet-tabs {
        display: flex;
        background: #f1f5f9;
        padding: 0.5rem 1rem 0 1rem;
        gap: 0.25rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .tab-wrapper {
        display: flex;
        align-items: center;
        background: #e2e8f0;
        border-radius: 6px 6px 0 0;
        overflow: hidden;
    }
    .tab-wrapper.active {
        background: #3b82f6;
    }
    .sheet-tab {
        border: none;
        background: none;
        padding: 0.5rem 1rem;
        cursor: pointer;
        font-size: 0.875rem;
        color: #475569;
    }
    .tab-wrapper.active .sheet-tab {
        color: white;
    }
    .close-tab {
        border: none;
        background: none;
        padding: 0 0.5rem;
        cursor: pointer;
        color: #94a3b8;
    }

    .search-bar {
        margin-bottom: 1rem;
    }
    .search-bar input {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        font-size: 0.875rem;
    }
    .add-sheet-btn {
        border: 1px dashed #cbd5e1;
        background: none;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        margin-bottom: 4px;
        cursor: pointer;
        font-size: 0.8rem;
    }

    .workspace {
        display: flex;
        flex: 1;
        overflow: hidden;
    }

    .nest-controls {
        display: flex;
        gap: 0;
        align-items: center;
        border-radius: 6px;
        overflow: hidden;
    }
    .debug-toggle {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
        color: #64748b;
        cursor: pointer;
    }

    .nest-mode-select {
        background: #444;
        color: white;
        border: none;
        padding: 0.5rem;
        font-size: 0.8rem;
        border-right: 1px solid #555;
        outline: none;
    }

    .canvas-area {
        flex: 1;
        background: #1e1e1e;
        display: flex;
        justify-content: center;
        align-items: center;
        overflow: auto;
        position: relative;
    }
    .placeholder,
    .loading {
        color: #64748b;
        text-align: center;
    }
    .btn-primary {
        background: #3b82f6;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        margin-top: 1rem;
    }

    .properties-panel {
        width: 300px;
        border-left: 1px solid #e2e8f0;
        background: white;
        padding: 1rem;
        overflow-y: auto;
    }
    .mode-selector {
        display: flex;
        gap: 0.25rem;
        margin-bottom: 1rem;
        background: #f1f5f9;
        padding: 0.25rem;
        border-radius: 6px;
    }
    .mode-selector button {
        flex: 1;
        border: none;
        background: none;
        padding: 0.4rem;
        border-radius: 4px;
        font-size: 0.75rem;
        cursor: pointer;
    }
    .mode-selector button.active {
        background: white;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        font-weight: 500;
    }

    .inventory-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem;
        background: #f8fafc;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #3b82f6;
    }
    .inventory-item.complete {
        border-left-color: #10b981;
        opacity: 0.6;
    }
    .inventory-item .info {
        display: flex;
        flex-direction: column;
    }
    .inventory-item .name {
        font-size: 0.875rem;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 150px;
    }
    .inventory-item .stats {
        font-size: 0.75rem;
        color: #64748b;
    }
    .add-btn {
        background: #3b82f6;
        color: white;
        border: none;
        width: 24px;
        height: 24px;
        border-radius: 4px;
        cursor: pointer;
    }
    .add-btn:disabled {
        background: #cbd5e1;
        cursor: not-allowed;
    }

    .library-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
    }
    .lib-item {
        background: white;
        border: 1px solid #e2e8f0;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        cursor: pointer;
        text-align: center;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .lib-item:hover {
        border-color: #3b82f6;
        background: #eff6ff;
    }

    .prop-group {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        margin-bottom: 1rem;
    }
    .inline-inputs {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .inline-inputs input {
        width: 80px;
    }
    input,
    select {
        padding: 0.4rem;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        font-size: 0.875rem;
    }
    .section-title {
        margin: 1.5rem 0 0.5rem 0;
        font-size: 0.8rem;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.05em;
    }
    .delete-btn {
        width: 100%;
        background: #fee2e2;
        color: #dc2626;
        border: 1px solid #fecaca;
        padding: 0.5rem;
        border-radius: 6px;
        cursor: pointer;
    }

    /* Pagination CSS */
    .pagination-controls {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        margin-top: 1rem;
        padding: 0.5rem;
        border-top: 1px solid #e2e8f0;
    }
    .page-btn {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        color: #475569;
        width: 32px;
        height: 32px;
        border-radius: 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }
    .page-btn:hover:not(:disabled) {
        background: #e2e8f0;
        border-color: #94a3b8;
    }
    .page-btn:disabled {
        opacity: 0.3;
        cursor: not-allowed;
    }
    .page-info {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 500;
        min-width: 80px;
        text-align: center;
    }
</style>
