<script>
    import { onMount } from "svelte";

    let {
        sheet = null,
        width = 800,
        height = 600,
        onselect = null,
        onAreaChange = null,
        showDebug = false,
        nestingMode = "hull",
    } = $props();

    let canvas = $state();
    let ctx = $state(null);

    // Pan/Zoom controls
    let userZoom = $state(1.0);
    let panX = $state(0);
    let panY = $state(0);
    let isDragging = $state(false);
    let dragStartX = $state(0);
    let dragStartY = $state(0);

    // Tool Modes: 'navigate' | 'select' | 'nestArea'
    let toolMode = $state("navigate");

    // Nesting Area Dragging
    let isDrawingArea = $state(false);
    let areaStartWorld = $state(null);
    let currentAreaWorld = $state(null);

    let selectedContourId = $state(null);
    let hoverContourId = $state(null);

    // Reactive Layout Calculations using $derived
    const bounds = $derived(
        sheet
            ? calculateBounds(sheet)
            : { minX: 0, minY: 0, maxX: 100, maxY: 100 },
    );

    const layout = $derived.by(() => {
        const dataW = bounds.maxX - bounds.minX;
        const dataH = bounds.maxY - bounds.minY;

        if (dataW === 0 && dataH === 0) {
            return { scale: 1, startX: 0, startY: 0, bounds };
        }

        const padding = 20;
        const availW = width - padding * 2;
        const availH = height - padding * 2;

        const scaleX = availW / dataW;
        const scaleY = availH / dataH;
        const baseScale = Math.min(scaleX, scaleY) * 0.95;
        const s = baseScale * userZoom;

        const contentW = dataW * s;
        const contentH = dataH * s;

        return {
            scale: s,
            startX: (width - contentW) / 2 + panX,
            startY: (height - contentH) / 2 + panY,
            bounds,
        };
    });

    $effect(() => {
        if (canvas && layout) {
            draw();
        }
    });

    onMount(() => {
        if (canvas) {
            ctx = canvas.getContext("2d");
            draw();
        }
    });

    function calculateBounds(sheet) {
        let minX = Infinity,
            minY = Infinity,
            maxX = -Infinity,
            maxY = -Infinity;
        let hasPoints = false;

        // Include Sheet Dimensions in bounds if available
        if (sheet.program_width && sheet.program_height) {
            minX = 0;
            minY = 0;
            maxX = sheet.program_width;
            maxY = sheet.program_height;
            hasPoints = true;
        }

        let currentX = 0;
        let currentY = 0;

        for (const part of sheet.parts) {
            const ox = part.x || 0;
            const oy = part.y || 0;
            let pCurrentX = 0;
            let pCurrentY = 0;

            for (const contour of part.contours) {
                for (const cmd of contour.commands) {
                    if (cmd.x !== undefined) pCurrentX = cmd.x;
                    if (cmd.y !== undefined) pCurrentY = cmd.y;

                    if (cmd.x !== undefined || cmd.y !== undefined) {
                        hasPoints = true;
                        const absX = part.x - (part.minX || 0) + pCurrentX;
                        const absY = part.y - (part.minY || 0) + pCurrentY;
                        if (absX < minX) minX = absX;
                        if (absX > maxX) maxX = absX;
                        if (absY < minY) minY = absY;
                        if (absY > maxY) maxY = absY;
                    }
                }
            }
        }

        if (!hasPoints) return { minX: 0, minY: 0, maxX: 100, maxY: 100 };
        return { minX, minY, maxX, maxY };
    }

    // Transform function: World -> Screen
    function toScreen(x, y) {
        return {
            x: layout.startX + (x - layout.bounds.minX) * layout.scale,
            y:
                height -
                (layout.startY + (y - layout.bounds.minY) * layout.scale),
        };
    }

    // Inverse Transform: Screen -> World
    function toWorld(screenX, screenY) {
        return {
            x: (screenX - layout.startX) / layout.scale + layout.bounds.minX,
            y:
                (height - screenY - layout.startY) / layout.scale +
                layout.bounds.minY,
        };
    }

    function draw() {
        if (!ctx || !sheet || !layout) return;

        // Clear
        ctx.fillStyle = "#1e1e1e";
        ctx.fillRect(0, 0, width, height);

        const { scale, startX, startY, bounds } = layout;

        const tx = (x, ox = 0) => startX + (x + ox - bounds.minX) * scale;
        const ty = (y, oy = 0) =>
            height - (startY + (y + oy - bounds.minY) * scale); // Flip Y

        // Draw Sheet Border
        if (sheet.program_width && sheet.program_height) {
            ctx.strokeStyle = "#444";
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.strokeRect(
                tx(0),
                ty(sheet.program_height),
                sheet.program_width * scale,
                sheet.program_height * scale,
            );
            ctx.setLineDash([]);
        }

        // Draw nesting area if it exists on sheet
        if (sheet.nestingArea) {
            ctx.strokeStyle = "rgba(0, 255, 0, 0.5)";
            ctx.lineWidth = 2;
            ctx.setLineDash([10, 5]);
            ctx.strokeRect(
                tx(sheet.nestingArea.x),
                ty(sheet.nestingArea.y + sheet.nestingArea.height),
                sheet.nestingArea.width * scale,
                sheet.nestingArea.height * scale,
            );
            ctx.fillStyle = "rgba(0, 255, 0, 0.05)";
            ctx.fillRect(
                tx(sheet.nestingArea.x),
                ty(sheet.nestingArea.y + sheet.nestingArea.height),
                sheet.nestingArea.width * scale,
                sheet.nestingArea.height * scale,
            );
            ctx.setLineDash([]);
        }

        // Draw current dragging area
        if (isDrawingArea && areaStartWorld && currentAreaWorld) {
            const minX = Math.min(areaStartWorld.x, currentAreaWorld.x);
            const minY = Math.min(areaStartWorld.y, currentAreaWorld.y);
            const maxX = Math.max(areaStartWorld.x, currentAreaWorld.x);
            const maxY = Math.max(areaStartWorld.y, currentAreaWorld.y);

            ctx.strokeStyle = "rgba(0, 255, 0, 0.8)";
            ctx.lineWidth = 2;
            ctx.strokeRect(
                tx(minX),
                ty(maxY),
                (maxX - minX) * scale,
                (maxY - minY) * scale,
            );
        }

        // Draw Parts (Main Layer)
        sheet.parts.forEach((part, pIndex) => {
            const hue = (pIndex * 137) % 360;
            const ox = (part.x || 0) - (part.minX || 0);
            const oy = (part.y || 0) - (part.minY || 0);

            part.contours.forEach((contour) => {
                const combinedId = `${part.id}-${contour.id}`;
                const isSelected = selectedContourId === combinedId;
                const isHovered = hoverContourId === combinedId;

                ctx.beginPath();
                ctx.strokeStyle = isSelected
                    ? "#ffffff"
                    : isHovered
                      ? "#fbbf24"
                      : `hsl(${hue}, 70%, 60%)`;
                ctx.lineWidth = isSelected ? 3 : isHovered ? 3 : 1.5;
                ctx.shadowBlur = isSelected ? 10 : isHovered ? 5 : 0;
                ctx.shadowColor = isSelected
                    ? "#ffffff"
                    : isHovered
                      ? "#fbbf24"
                      : "transparent";

                // Local position tracking for this contour only
                let currentX = null;
                let currentY = null;
                let hasMoved = false;

                contour.commands.forEach((cmd) => {
                    // Store previous position before updating for arc calculations
                    const prevX = currentX;
                    const prevY = currentY;

                    // Update current position from command
                    if (cmd.x !== undefined) currentX = cmd.x;
                    if (cmd.y !== undefined) currentY = cmd.y;

                    // Skip if we don't have valid coordinates yet
                    if (currentX === null || currentY === null) return;

                    // Handle different command types
                    if (
                        cmd.type === "G00" ||
                        (cmd.command === "G" && cmd.value === 0)
                    ) {
                        ctx.moveTo(tx(currentX, ox), ty(currentY, oy));
                        hasMoved = true;
                    } else if (
                        cmd.type === "G01" ||
                        (cmd.command === "G" && cmd.value === 1) ||
                        cmd.type === "MODAL" ||
                        cmd.type === "G41" ||
                        cmd.type === "G40"
                    ) {
                        if (!hasMoved) {
                            ctx.moveTo(tx(currentX, ox), ty(currentY, oy));
                            hasMoved = true;
                        } else {
                            ctx.lineTo(tx(currentX, ox), ty(currentY, oy));
                        }
                    } else if (
                        cmd.type === "G02" ||
                        cmd.type === "G03" ||
                        (cmd.command === "G" &&
                            (cmd.value === 2 || cmd.value === 3))
                    ) {
                        if (
                            cmd.i !== undefined &&
                            cmd.j !== undefined &&
                            prevX !== null &&
                            prevY !== null
                        ) {
                            const i = cmd.i;
                            const j = cmd.j;
                            const centerX = prevX + i;
                            const centerY = prevY + j;
                            const radius = Math.sqrt(i * i + j * j);

                            const cX = tx(centerX, ox);
                            const cY = ty(centerY, oy);
                            const scaledRadius = radius * scale;

                            const angStart = Math.atan2(
                                ty(prevY, oy) - cY,
                                tx(prevX, ox) - cX,
                            );
                            const angEnd = Math.atan2(
                                ty(currentY, oy) - cY,
                                tx(currentX, ox) - cX,
                            );

                            const counterClockwise =
                                cmd.type === "G02" ||
                                (cmd.command === "G" && cmd.value === 2);

                            ctx.arc(
                                cX,
                                cY,
                                scaledRadius,
                                angStart,
                                angEnd,
                                counterClockwise,
                            );
                        }
                    }
                });

                ctx.stroke();
                ctx.shadowBlur = 0; // Reset
            });
        });

        // Debug visualization (Overlay)
        if (showDebug) {
            sheet.parts.forEach((part) => {
                // For main contours (original coordinates), we need to shift by minX
                // But for normalized Debug data (BBox/Hull being 0-based), we ONLY need the placement position (part.x, part.y)
                // However, our `tx` function assumes it's handling world coords and subtracts bounds.

                // Let's define specific offsets for Debug elements
                // Hull/BBox are already normalized (0,0 is top-left of part), so we just place them at part.x, part.y
                const oxDebug = part.x || 0;
                const oyDebug = part.y || 0;

                // Draw Bounding Box if mode is 'bbox' or fallback
                if (nestingMode === "bbox" || !part.polygon) {
                    ctx.strokeStyle = "rgba(255, 0, 0, 0.8)"; // Red for BBox
                    ctx.lineWidth = 1;
                    ctx.setLineDash([2, 2]);
                    ctx.strokeRect(
                        tx(0, oxDebug),
                        ty(part.height || 0, oyDebug),
                        (part.width || 0) * scale,
                        (part.height || 0) * scale,
                    );
                }

                // Draw Hull Polygon if mode is 'hull' and available
                if (nestingMode === "hull" && part.polygon) {
                    ctx.beginPath();
                    ctx.strokeStyle = "rgba(0, 255, 255, 0.8)"; // Cyan for Hull
                    ctx.lineWidth = 1;
                    ctx.setLineDash([]);

                    // Polygon points are relative to (0,0)
                    part.polygon.forEach((p, i) => {
                        const sx = tx(p.x, oxDebug);
                        const sy = ty(p.y, oyDebug);
                        if (i === 0) ctx.moveTo(sx, sy);
                        else ctx.lineTo(sx, sy);
                    });
                    ctx.closePath();
                    ctx.stroke();

                    // Fill semi-transparent
                    ctx.fillStyle = "rgba(0, 255, 255, 0.2)";
                    ctx.fill();
                }

                ctx.setLineDash([]);
            });
        }
    }

    function getContourAt(clientX, clientY) {
        if (!sheet) return null;

        const rect = canvas.getBoundingClientRect();
        const mouseX = clientX - rect.left;
        const mouseY = clientY - rect.top;

        const worldPos = toWorld(mouseX, mouseY);
        const wX = worldPos.x;
        const wY = worldPos.y;

        const threshold = 5 / layout.scale;

        let closestContour = null;
        let closestPart = null;
        let minDistance = Infinity;

        for (const part of sheet.parts) {
            const pX = (part.x || 0) - (part.minX || 0);
            const pY = (part.y || 0) - (part.minY || 0);

            for (const contour of part.contours) {
                let currentX = null;
                let currentY = null;

                let contourDistance = Infinity;

                for (const cmd of contour.commands) {
                    const nextX = cmd.x !== undefined ? cmd.x : currentX;
                    const nextY = cmd.y !== undefined ? cmd.y : currentY;

                    let dist = Infinity;

                    if (
                        currentX !== null &&
                        currentY !== null &&
                        nextX !== null &&
                        nextY !== null
                    ) {
                        if (
                            cmd.type === "G01" ||
                            (cmd.command === "G" && cmd.value === 1) ||
                            cmd.type === "MODAL" ||
                            cmd.type === "G41" ||
                            cmd.type === "G40"
                        ) {
                            dist = distancePointToSegment(
                                wX,
                                wY,
                                currentX + pX,
                                currentY + pY,
                                nextX + pX,
                                nextY + pY,
                            );
                        } else if (
                            cmd.type === "G02" ||
                            cmd.type === "G03" ||
                            (cmd.command === "G" &&
                                (cmd.value === 2 || cmd.value === 3))
                        ) {
                            const i = cmd.i || 0;
                            const j = cmd.j || 0;
                            const centerX = currentX + i + pX;
                            const centerY = currentY + j + pY;
                            const radius = Math.sqrt(i * i + j * j);

                            const distToCenter = Math.sqrt(
                                (wX - centerX) ** 2 + (wY - centerY) ** 2,
                            );
                            dist = Math.abs(distToCenter - radius);

                            const startAngle = Math.atan2(
                                currentY + pY - centerY,
                                currentX + pX - centerX,
                            );
                            const endAngle = Math.atan2(
                                nextY + pY - centerY,
                                nextX + pX - centerX,
                            );
                            const pointAngle = Math.atan2(
                                wY - centerY,
                                wX - centerX,
                            );

                            const isClockwise =
                                cmd.type === "G02" ||
                                (cmd.command === "G" && cmd.value === 2);

                            if (
                                !isAngleBetween(
                                    pointAngle,
                                    startAngle,
                                    endAngle,
                                    isClockwise,
                                )
                            ) {
                                dist = Infinity;
                            }
                        }
                    } // End of null check

                    if (dist < contourDistance) contourDistance = dist;
                    currentX = nextX;
                    currentY = nextY;
                }

                if (
                    contourDistance < threshold &&
                    contourDistance < minDistance
                ) {
                    minDistance = contourDistance;
                    closestContour = contour;
                    closestPart = part;
                }
            }
        }

        if (closestContour)
            return { contour: closestContour, part: closestPart };
        return null;
    }

    function handleCanvasClick(event) {
        const hit = getContourAt(event.clientX, event.clientY);
        if (hit) {
            selectedContourId = `${hit.part.id}-${hit.contour.id}`;
            if (onselect) onselect(hit);
        } else {
            selectedContourId = null;
            if (onselect) onselect(null);
        }
        draw();
    }

    function distancePointToSegment(px, py, x1, y1, x2, y2) {
        const A = px - x1;
        const B = py - y1;
        const C = x2 - x1;
        const D = y2 - y1;

        const dot = A * C + B * D;
        const len_sq = C * C + D * D;
        let param = -1;
        if (len_sq != 0)
            //in case of 0 length line
            param = dot / len_sq;

        let xx, yy;

        if (param < 0) {
            xx = x1;
            yy = y1;
        } else if (param > 1) {
            xx = x2;
            yy = y2;
        } else {
            xx = x1 + param * C;
            yy = y1 + param * D;
        }

        const dx = px - xx;
        const dy = py - yy;
        return Math.sqrt(dx * dx + dy * dy);
    }

    // Pan/Zoom event handlers
    function handleWheel(e) {
        e.preventDefault();

        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        // Get world pos before zoom
        const worldPos = toWorld(mouseX, mouseY);

        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        const newZoom = Math.max(0.1, Math.min(10, userZoom * delta));

        if (layout.scale === 0 || userZoom === 0) return;

        // Calculate new pan to keep worldPos at mouseX/Y
        const baseScale = layout.scale / userZoom;
        const newScale = baseScale * newZoom;

        const dataW = layout.bounds.maxX - layout.bounds.minX;
        const dataH = layout.bounds.maxY - layout.bounds.minY;
        const newContentW = dataW * newScale;
        const newContentH = dataH * newScale;

        // Solve for newPanX/Y
        const newStartX = mouseX - (worldPos.x - layout.bounds.minX) * newScale;
        const newStartY =
            height - mouseY - (worldPos.y - layout.bounds.minY) * newScale;

        panX = newStartX - (width - newContentW) / 2;
        panY = newStartY - (height - newContentH) / 2;

        userZoom = newZoom;
        draw();
    }

    function handleMouseDown(e) {
        // Track start pos for click detection in all modes
        dragStartX = e.clientX;
        dragStartY = e.clientY;

        const rect = canvas.getBoundingClientRect();

        if (toolMode === "navigate") {
            isDragging = true;
        } else if (toolMode === "nestArea") {
            isDrawingArea = true;
            areaStartWorld = toWorld(
                e.clientX - rect.left,
                e.clientY - rect.top,
            );
            currentAreaWorld = areaStartWorld;
        }
    }

    function handleMouseMove(e) {
        if (toolMode === "navigate" && isDragging) {
            const dx = e.clientX - dragStartX;
            const dy = e.clientY - dragStartY;

            panX += dx;
            panY -= dy; // Subtract to fix inverted Y

            dragStartX = e.clientX;
            dragStartY = e.clientY;

            draw();
        } else if (toolMode === "select") {
            const hit = getContourAt(e.clientX, e.clientY);
            const newHoverId = hit ? `${hit.part.id}-${hit.contour.id}` : null;

            if (newHoverId !== hoverContourId) {
                hoverContourId = newHoverId;
                draw();
            }
        } else if (toolMode === "nestArea" && isDrawingArea) {
            const rect = canvas.getBoundingClientRect();
            currentAreaWorld = toWorld(
                e.clientX - rect.left,
                e.clientY - rect.top,
            );
            draw();
        }
    }

    function handleMouseLeave() {
        if (hoverContourId !== null) {
            hoverContourId = null;
            draw();
        }
        if (isDragging) isDragging = false;
    }

    function handleMouseUp(e) {
        const dx = Math.abs(e.clientX - dragStartX);
        const dy = Math.abs(e.clientY - dragStartY);
        const isClick = dx < 5 && dy < 5;

        if (toolMode === "navigate") {
            isDragging = false;
        } else if (toolMode === "select") {
            // Only trigger click handler if it was actually a click
            if (isClick) {
                handleCanvasClick(e);
            }
        } else if (toolMode === "nestArea" && isDrawingArea) {
            isDrawingArea = false;
            // Calculate final area rect
            const minX = Math.min(areaStartWorld.x, currentAreaWorld.x);
            const minY = Math.min(areaStartWorld.y, currentAreaWorld.y);
            const maxX = Math.max(areaStartWorld.x, currentAreaWorld.x);
            const maxY = Math.max(areaStartWorld.y, currentAreaWorld.y);

            const newArea = {
                x: minX,
                y: minY,
                width: maxX - minX,
                height: maxY - minY,
            };

            if (newArea.width > 5 && newArea.height > 5) {
                if (onAreaChange) onAreaChange(newArea);
            }
            draw();
        }
    }

    function isAngleBetween(target, start, end, clockwise) {
        const PI2 = Math.PI * 2;
        // Normalize
        const t = ((target % PI2) + PI2) % PI2;
        const s = ((start % PI2) + PI2) % PI2;
        const e = ((end % PI2) + PI2) % PI2;

        if (clockwise) {
            // Clockwise sweep from Start to End.
            const total = (s - e + PI2) % PI2;
            const point = (s - t + PI2) % PI2;
            return point <= total;
        } else {
            // CCW sweep from Start to End.
            const total = (e - s + PI2) % PI2;
            const point = (t - s + PI2) % PI2;
            return point <= total;
        }
    }

    function resetZoom() {
        userZoom = 1.0;
        panX = 0;
        panY = 0;
        draw();
    }
</script>

<div class="canvas-container" style="width: {width}px; height: {height}px;">
    <div class="toolbar">
        <button
            class:active={toolMode === "navigate"}
            onclick={() => (toolMode = "navigate")}
            title="Navigate (Pan)">✋</button
        >
        <button
            class:active={toolMode === "select"}
            onclick={() => (toolMode = "select")}
            title="Select">↖</button
        >
        <button
            class:active={toolMode === "nestArea"}
            onclick={() => (toolMode = "nestArea")}
            title="Define Nesting Area">🎯</button
        >
    </div>

    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <canvas
        bind:this={canvas}
        {width}
        {height}
        style="cursor: {toolMode === 'navigate'
            ? isDragging
                ? 'grabbing'
                : 'grab'
            : 'default'}"
        onwheel={handleWheel}
        onmousedown={handleMouseDown}
        onmousemove={handleMouseMove}
        onmouseup={handleMouseUp}
        onmouseleave={handleMouseLeave}
    ></canvas>
    <div class="zoom-controls">
        <button onclick={resetZoom} title="Reset Zoom">⟲</button>
        <span class="zoom-level">{Math.round(userZoom * 100)}%</span>
    </div>
</div>

<style>
    .canvas-container {
        background-color: #1e1e1e;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        position: relative;
    }
    canvas {
        display: block;
        /* cursor handled inline */
    }

    .toolbar {
        position: absolute;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 8px;
        background: rgba(0, 0, 0, 0.7);
        padding: 6px 10px;
        border-radius: 6px;
        z-index: 10;
    }
    .toolbar button {
        background: #333;
        border: 1px solid #555;
        color: #fff;
        width: 36px;
        height: 36px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
    }
    .toolbar button.active {
        background: #3b82f6;
        border-color: #2563eb;
    }
    .toolbar button:hover:not(.active) {
        background: #444;
    }
    .zoom-controls {
        position: absolute;
        bottom: 10px;
        right: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(0, 0, 0, 0.7);
        padding: 6px 10px;
        border-radius: 6px;
    }
    .zoom-controls button {
        background: #333;
        border: 1px solid #555;
        color: #fff;
        padding: 4px 8px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
    }
    .zoom-controls button:hover {
        background: #444;
    }
    .zoom-level {
        color: #fff;
        font-size: 12px;
        min-width: 40px;
        text-align: center;
    }
</style>
