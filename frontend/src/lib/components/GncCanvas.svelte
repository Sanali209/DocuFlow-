<script>
    import { onMount, createEventDispatcher } from "svelte";

    export let sheet = null;
    export let width = 800;
    export let height = 600;

    const dispatch = createEventDispatcher();

    let canvas;
    let ctx = null;

    // Scaling variables
    let scale = 1;
    let offsetX = 0;
    let offsetY = 0;

    // Pan/Zoom controls
    let userZoom = 1.0;
    let panX = 0;
    let panY = 0;
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;

    // Tool Modes: 'navigate' | 'select'
    let toolMode = "navigate";

    // Bounds for hit testing
    let bounds = { minX: 0, minY: 0, maxX: 100, maxY: 100 };
    let startX = 0;
    let startY = 0;

    let selectedContourId = null;
    let hoverContourId = null;

    $: if (sheet && canvas) {
        console.log("GncCanvas: sheet changed, redrawing...", sheet);
        draw();
    }

    onMount(() => {
        if (canvas) {
            ctx = canvas.getContext("2d");
            console.log("GncCanvas: mounted, ctx:", ctx);
            draw();
        }
    });

    function calculateBounds(sheet) {
        let minX = Infinity,
            minY = Infinity,
            maxX = -Infinity,
            maxY = -Infinity;
        let hasPoints = false;

        let currentX = 0;
        let currentY = 0;

        console.log(
            "calculateBounds: sheet.parts.length =",
            sheet.parts.length,
        );

        for (const part of sheet.parts) {
            console.log(
                "calculateBounds: part.contours.length =",
                part.contours.length,
            );
            for (const contour of part.contours) {
                console.log(
                    "calculateBounds: contour.id =",
                    contour.id,
                    "commands.length =",
                    contour.commands.length,
                );
                for (const cmd of contour.commands) {
                    if (cmd.x !== undefined) currentX = cmd.x;
                    if (cmd.y !== undefined) currentY = cmd.y;

                    if (cmd.x !== undefined || cmd.y !== undefined) {
                        hasPoints = true;
                        if (currentX < minX) minX = currentX;
                        if (currentX > maxX) maxX = currentX;
                        if (currentY < minY) minY = currentY;
                        if (currentY > maxY) maxY = currentY;
                        console.log(
                            "calculateBounds: found point",
                            currentX,
                            currentY,
                            "from cmd.type =",
                            cmd.type,
                        );
                    }
                }
            }
        }

        console.log("calculateBounds: hasPoints =", hasPoints, "bounds =", {
            minX,
            minY,
            maxX,
            maxY,
        });

        if (!hasPoints) return { minX: 0, minY: 0, maxX: 100, maxY: 100 };
        return { minX, minY, maxX, maxY };
    }

    // Transform function: World -> Screen
    function toScreen(x, y) {
        return {
            x: startX + (x - bounds.minX) * scale,
            y: height - (startY + (y - bounds.minY) * scale),
        };
    }

    // Inverse Transform: Screen -> World
    function toWorld(screenX, screenY) {
        // x = (screenX - startX) / scale + minX
        // screenY = H - (startY + (y - minY)*scale)
        // startY + (y - minY)*scale = H - screenY
        // (y - minY)*scale = H - screenY - startY
        // y - minY = (H - screenY - startY) / scale
        // y = (H - screenY - startY) / scale + minY

        return {
            x: (screenX - startX) / scale + bounds.minX,
            y: (height - screenY - startY) / scale + bounds.minY,
        };
    }

    function draw() {
        if (!ctx || !sheet) {
            console.log(
                "GncCanvas draw: skipping - ctx:",
                !!ctx,
                "sheet:",
                !!sheet,
            );
            return;
        }

        console.log("GncCanvas draw: starting draw with sheet:", sheet);

        // Clear
        ctx.fillStyle = "#1e1e1e";
        ctx.fillRect(0, 0, width, height);

        bounds = calculateBounds(sheet);
        console.log("GncCanvas draw: bounds:", bounds);

        const dataW = bounds.maxX - bounds.minX;
        const dataH = bounds.maxY - bounds.minY;

        if (dataW === 0 && dataH === 0) {
            console.log("GncCanvas draw: no data (dataW and dataH are 0)");
            return;
        }

        const padding = 20;
        const availW = width - padding * 2;
        const availH = height - padding * 2;

        const scaleX = availW / dataW;
        const scaleY = availH / dataH;
        const baseScale = Math.min(scaleX, scaleY) * 0.95; // 0.95 safety factor
        scale = baseScale * userZoom; // Apply user zoom

        const contentW = dataW * scale;
        const contentH = dataH * scale;

        startX = (width - contentW) / 2 + panX;
        startY = (height - contentH) / 2 + panY;

        const tx = (x) => startX + (x - bounds.minX) * scale;
        const ty = (y) => height - (startY + (y - bounds.minY) * scale); // Flip Y

        sheet.parts.forEach((part, pIndex) => {
            const hue = (pIndex * 137) % 360;

            part.contours.forEach((contour) => {
                const isSelected = selectedContourId === contour.id;
                const isHovered = hoverContourId === contour.id;

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
                        ctx.moveTo(tx(currentX), ty(currentY));
                        hasMoved = true;
                    } else if (
                        cmd.type === "G01" ||
                        (cmd.command === "G" && cmd.value === 1) ||
                        cmd.type === "MODAL" ||
                        cmd.type === "G41" ||
                        cmd.type === "G40"
                    ) {
                        if (!hasMoved) {
                            ctx.moveTo(tx(currentX), ty(currentY));
                            hasMoved = true;
                        } else {
                            ctx.lineTo(tx(currentX), ty(currentY));
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

                            const cX = tx(centerX);
                            const cY = ty(centerY);
                            const scaledRadius = radius * scale;

                            const angStart = Math.atan2(
                                ty(prevY) - cY,
                                tx(prevX) - cX,
                            );
                            const angEnd = Math.atan2(
                                ty(currentY) - cY,
                                tx(currentX) - cX,
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
    }

    function getContourAt(clientX, clientY) {
        if (!sheet) return null;

        const rect = canvas.getBoundingClientRect();
        const mouseX = clientX - rect.left;
        const mouseY = clientY - rect.top;

        const worldPos = toWorld(mouseX, mouseY);
        const wX = worldPos.x;
        const wY = worldPos.y;

        const threshold = 5 / scale;

        let closestContour = null;
        let closestPart = null;
        let minDistance = Infinity;

        for (const part of sheet.parts) {
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
                                currentX,
                                currentY,
                                nextX,
                                nextY,
                            );
                        } else if (
                            cmd.type === "G02" ||
                            cmd.type === "G03" ||
                            (cmd.command === "G" &&
                                (cmd.value === 2 || cmd.value === 3))
                        ) {
                            const i = cmd.i || 0;
                            const j = cmd.j || 0;
                            const centerX = currentX + i;
                            const centerY = currentY + j;
                            const radius = Math.sqrt(i * i + j * j);

                            const distToCenter = Math.sqrt(
                                (wX - centerX) ** 2 + (wY - centerY) ** 2,
                            );
                            dist = Math.abs(distToCenter - radius);

                            const startAngle = Math.atan2(
                                currentY - centerY,
                                currentX - centerX,
                            );
                            const endAngle = Math.atan2(
                                nextY - centerY,
                                nextX - centerX,
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
            selectedContourId = hit.contour.id;
            dispatch("select", hit);
        } else {
            selectedContourId = null;
            dispatch("select", null);
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

        if (scale === 0 || userZoom === 0) return;

        // Calculate new pan to keep worldPos at mouseX/Y
        const baseScale = scale / userZoom;
        const newScale = baseScale * newZoom;

        const dataW = bounds.maxX - bounds.minX;
        const dataH = bounds.maxY - bounds.minY;
        const newContentW = dataW * newScale;
        const newContentH = dataH * newScale;

        // Solve for newPanX/Y
        const newStartX = mouseX - (worldPos.x - bounds.minX) * newScale;
        const newStartY =
            height - mouseY - (worldPos.y - bounds.minY) * newScale;

        panX = newStartX - (width - newContentW) / 2;
        panY = newStartY - (height - newContentH) / 2;

        userZoom = newZoom;
        draw();
    }

    function handleMouseDown(e) {
        // Track start pos for click detection in all modes
        dragStartX = e.clientX;
        dragStartY = e.clientY;

        if (toolMode === "navigate") {
            isDragging = true;
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
            const newHoverId = hit ? hit.contour.id : null;

            if (newHoverId !== hoverContourId) {
                hoverContourId = newHoverId;
                draw();
            }
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
