<script lang="ts">
    import { onMount, createEventDispatcher } from 'svelte';
    import type { GNCSheet, GNCPart, GNCContour, GNCCommand } from '$lib/types/gnc';

    export let sheet: GNCSheet | null = null;
    export let width = 800;
    export let height = 600;

    const dispatch = createEventDispatcher();

    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D | null = null;

    // Scaling variables
    let scale = 1;
    let offsetX = 0;
    let offsetY = 0;

    // Bounds for hit testing
    let bounds = { minX: 0, minY: 0, maxX: 100, maxY: 100 };
    let startX = 0;
    let startY = 0;

    let selectedContourId: number | null = null;

    $: if (sheet && canvas) {
        draw();
    }

    onMount(() => {
        if (canvas) {
            ctx = canvas.getContext('2d');
            draw();
        }
    });

    function calculateBounds(sheet: GNCSheet) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        let hasPoints = false;

        let currentX = 0;
        let currentY = 0;

        for (const part of sheet.parts) {
            for (const contour of part.contours) {
                for (const cmd of contour.commands) {
                    if (cmd.x !== undefined) currentX = cmd.x;
                    if (cmd.y !== undefined) currentY = cmd.y;

                    if (cmd.x !== undefined || cmd.y !== undefined) {
                        hasPoints = true;
                        if (currentX < minX) minX = currentX;
                        if (currentX > maxX) maxX = currentX;
                        if (currentY < minY) minY = currentY;
                        if (currentY > maxY) maxY = currentY;
                    }
                }
            }
        }

        if (!hasPoints) return { minX: 0, minY: 0, maxX: 100, maxY: 100 };
        return { minX, minY, maxX, maxY };
    }

    // Transform function: World -> Screen
    function toScreen(x: number, y: number) {
        return {
            x: startX + (x - bounds.minX) * scale,
            y: height - (startY + (y - bounds.minY) * scale)
        };
    }

    // Inverse Transform: Screen -> World
    function toWorld(screenX: number, screenY: number) {
        // x = (screenX - startX) / scale + minX
        // screenY = H - (startY + (y - minY)*scale)
        // startY + (y - minY)*scale = H - screenY
        // (y - minY)*scale = H - screenY - startY
        // y - minY = (H - screenY - startY) / scale
        // y = (H - screenY - startY) / scale + minY

        return {
            x: (screenX - startX) / scale + bounds.minX,
            y: (height - screenY - startY) / scale + bounds.minY
        };
    }

    function draw() {
        if (!ctx || !sheet) return;

        // Clear
        ctx.fillStyle = '#1e1e1e';
        ctx.fillRect(0, 0, width, height);

        bounds = calculateBounds(sheet);
        const dataW = bounds.maxX - bounds.minX;
        const dataH = bounds.maxY - bounds.minY;

        if (dataW === 0 && dataH === 0) return;

        const padding = 20;
        const availW = width - padding * 2;
        const availH = height - padding * 2;

        const scaleX = availW / dataW;
        const scaleY = availH / dataH;
        scale = Math.min(scaleX, scaleY) * 0.95; // 0.95 safety factor

        const contentW = dataW * scale;
        const contentH = dataH * scale;

        startX = (width - contentW) / 2;
        startY = (height - contentH) / 2;

        const tx = (x: number) => startX + (x - bounds.minX) * scale;
        const ty = (y: number) => height - (startY + (y - bounds.minY) * scale); // Flip Y

        let currentX = 0;
        let currentY = 0;

        sheet.parts.forEach((part, pIndex) => {
            const hue = (pIndex * 137) % 360;

            part.contours.forEach(contour => {
                const isSelected = selectedContourId === contour.id;

                ctx.beginPath();
                ctx.strokeStyle = isSelected ? '#ffffff' : `hsl(${hue}, 70%, 60%)`;
                ctx.lineWidth = isSelected ? 3 : 1.5;
                ctx.shadowBlur = isSelected ? 10 : 0;
                ctx.shadowColor = isSelected ? '#ffffff' : 'transparent';

                // Reset start for each contour? Usually implicit.
                // But we need accurate start point.
                // Assuming continuity unless G00.

                contour.commands.forEach(cmd => {
                    const nextX = cmd.x !== undefined ? cmd.x : currentX;
                    const nextY = cmd.y !== undefined ? cmd.y : currentY;

                    if (cmd.type === 'G00') {
                        ctx.moveTo(tx(nextX), ty(nextY));
                    } else if (cmd.type === 'G01') {
                        ctx.lineTo(tx(nextX), ty(nextY));
                    } else if (cmd.type === 'G02' || cmd.type === 'G03') {
                        const i = cmd.i || 0;
                        const j = cmd.j || 0;
                        const centerX = currentX + i;
                        const centerY = currentY + j;
                        const radius = Math.sqrt(i*i + j*j);

                        const cX = tx(centerX);
                        const cY = ty(centerY);
                        const scaledRadius = radius * scale;

                        const angStart = Math.atan2(ty(currentY) - cY, tx(currentX) - cX);
                        const angEnd = Math.atan2(ty(nextY) - cY, tx(nextX) - cX);

                        const counterClockwise = cmd.type === 'G02';

                        ctx.arc(cX, cY, scaledRadius, angStart, angEnd, counterClockwise);
                    }

                    currentX = nextX;
                    currentY = nextY;
                });

                ctx.stroke();
                ctx.shadowBlur = 0; // Reset
            });
        });
    }

    function handleCanvasClick(event: MouseEvent) {
        if (!sheet) return;

        const rect = canvas.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const clickY = event.clientY - rect.top;

        // Convert click to World Coordinates
        const worldPos = toWorld(clickX, clickY);
        const wX = worldPos.x;
        const wY = worldPos.y;

        // Find closest contour
        // Threshold in world units (e.g., 5 pixels / scale)
        const threshold = 5 / scale;

        let closestContour: GNCContour | null = null;
        let minDistance = Infinity;

        // Reset state for calculation
        let currentX = 0;
        let currentY = 0;

        for (const part of sheet.parts) {
            for (const contour of part.contours) {
                let contourDistance = Infinity;

                for (const cmd of contour.commands) {
                    const nextX = cmd.x !== undefined ? cmd.x : currentX;
                    const nextY = cmd.y !== undefined ? cmd.y : currentY;

                    let dist = Infinity;

                    if (cmd.type === 'G00') {
                        // Just a move, check endpoint? or ignore?
                        // dist = distancePointToPoint(wX, wY, nextX, nextY);
                    } else if (cmd.type === 'G01') {
                        dist = distancePointToSegment(wX, wY, currentX, currentY, nextX, nextY);
                    } else if (cmd.type === 'G02' || cmd.type === 'G03') {
                        // Arc distance is distance to center minus radius (abs)
                        const i = cmd.i || 0;
                        const j = cmd.j || 0;
                        const centerX = currentX + i;
                        const centerY = currentY + j;
                        const radius = Math.sqrt(i*i + j*j);

                        const distToCenter = Math.sqrt((wX - centerX)**2 + (wY - centerY)**2);
                        dist = Math.abs(distToCenter - radius);

                        // Refinement: check if point is within arc angles?
                        // For MVP, distance to circle is often enough if contours aren't overlapping crazily
                    }

                    if (dist < contourDistance) contourDistance = dist;

                    currentX = nextX;
                    currentY = nextY;
                }

                if (contourDistance < threshold && contourDistance < minDistance) {
                    minDistance = contourDistance;
                    closestContour = contour;
                }
            }
        }

        if (closestContour) {
            selectedContourId = closestContour.id;
            draw(); // Redraw with highlight
            dispatch('select', closestContour);
        } else {
            selectedContourId = null;
            draw();
            dispatch('select', null);
        }
    }

    function distancePointToSegment(px: number, py: number, x1: number, y1: number, x2: number, y2: number) {
        const A = px - x1;
        const B = py - y1;
        const C = x2 - x1;
        const D = y2 - y1;

        const dot = A * C + B * D;
        const len_sq = C * C + D * D;
        let param = -1;
        if (len_sq != 0) //in case of 0 length line
            param = dot / len_sq;

        let xx, yy;

        if (param < 0) {
            xx = x1;
            yy = y1;
        }
        else if (param > 1) {
            xx = x2;
            yy = y2;
        }
        else {
            xx = x1 + param * C;
            yy = y1 + param * D;
        }

        const dx = px - xx;
        const dy = py - yy;
        return Math.sqrt(dx * dx + dy * dy);
    }
</script>

<div class="canvas-container" style="width: {width}px; height: {height}px;">
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <canvas
        bind:this={canvas}
        {width}
        {height}
        onclick={handleCanvasClick}
    ></canvas>
</div>

<style>
    .canvas-container {
        background-color: #1e1e1e;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    canvas {
        display: block;
        cursor: crosshair;
    }
</style>
