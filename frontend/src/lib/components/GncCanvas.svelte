<script lang="ts">
    import { onMount } from 'svelte';
    import type { GNCSheet, GNCPart, GNCContour, GNCCommand } from '$lib/types/gnc';

    export let sheet: GNCSheet | null = null;
    export let width = 800;
    export let height = 600;

    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D | null = null;

    // Scaling variables
    let scale = 1;
    let offsetX = 0;
    let offsetY = 0;

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

        // Iterate through all parts/contours to find bounds based on Absolute Coordinates
        // This is tricky because G-code is stateful. We need to simulate the path to find absolute positions.
        // For simplicity in this MVP, we assume G90 (Absolute Programming) is predominant or coordinates are absolute.
        // If relative (G91) is used, we'd need a full simulator.

        // Simulating state
        let currentX = 0;
        let currentY = 0;

        for (const part of sheet.parts) {
            for (const contour of part.contours) {
                // Assumption: Contours might start with a G00 to position
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

                    // Note: Arcs (G02/G03) might extend beyond start/end points.
                    // Bounding box of arc segments is complex.
                    // For MVP, using endpoints is a reasonable approximation.
                }
            }
        }

        if (!hasPoints) return { minX: 0, minY: 0, maxX: 100, maxY: 100 };
        return { minX, minY, maxX, maxY };
    }

    function fitToCanvas(bounds: { minX: number, minY: number, maxX: number, maxY: number }) {
        const dataWidth = bounds.maxX - bounds.minX;
        const dataHeight = bounds.maxY - bounds.minY;

        // Add 10% padding
        const padding = Math.min(width, height) * 0.1;

        const scaleX = (width - padding * 2) / dataWidth;
        const scaleY = (height - padding * 2) / dataHeight;

        // Keep aspect ratio
        scale = Math.min(scaleX, scaleY);

        // Center content
        offsetX = padding + (width - padding * 2 - dataWidth * scale) / 2 - bounds.minX * scale;
        // Invert Y: Canvas Y increases downwards, G-code Y increases upwards.
        // We map bounds.minY to bottom, bounds.maxY to top.
        offsetY = height - (padding + (height - padding * 2 - dataHeight * scale) / 2 + bounds.minY * scale);

        return { scale, offsetX, offsetY };
    }

    function toCanvas(x: number, y: number) {
        return {
            x: x * scale + offsetX,
            y: height - (y * scale + (height - offsetY)) // Correct Y inversion logic?
            // Let's re-derive:
            // World Y=0 -> Canvas Y should be low (bottom).
            // World Y=Max -> Canvas Y should be high (top, usually 0).
            // CanvasY = Height - (WorldY * scale + ShiftY)
            // Where ShiftY centers it.
        };
    }

    function transformY(y: number): number {
        // Simple transform: Flip Y axis relative to canvas height
        // Origin is bottom-left in G-code, Top-Left in Canvas.
        // We want (x,y) -> (x*scale + dx, Height - (y*scale + dy))
        // But we calculated offsets to center it.
        // Let's use a simpler transform approach:
        // 1. Translate to origin (-minX, -minY)
        // 2. Scale
        // 3. Flip Y
        // 4. Translate to center of canvas
        return 0; // Placeholder, logic inside draw
    }

    function draw() {
        if (!ctx || !sheet) return;

        // Clear
        ctx.fillStyle = '#1e1e1e';
        ctx.fillRect(0, 0, width, height);

        const bounds = calculateBounds(sheet);
        const dataW = bounds.maxX - bounds.minX;
        const dataH = bounds.maxY - bounds.minY;

        if (dataW === 0 && dataH === 0) return;

        const padding = 20;
        const availW = width - padding * 2;
        const availH = height - padding * 2;

        const scaleX = availW / dataW;
        const scaleY = availH / dataH;
        scale = Math.min(scaleX, scaleY) * 0.95; // 0.95 safety factor

        // Centering offsets
        const contentW = dataW * scale;
        const contentH = dataH * scale;

        const startX = (width - contentW) / 2;
        const startY = (height - contentH) / 2;

        // Transform function
        const tx = (x: number) => startX + (x - bounds.minX) * scale;
        const ty = (y: number) => height - (startY + (y - bounds.minY) * scale); // Flip Y

        // Draw Contours
        ctx.lineWidth = 1.5;

        let currentX = 0;
        let currentY = 0;

        sheet.parts.forEach((part, pIndex) => {
            // Pick color based on part index
            const hue = (pIndex * 137) % 360;
            ctx.strokeStyle = `hsl(${hue}, 70%, 60%)`;

            part.contours.forEach(contour => {
                ctx.beginPath();

                // Track start of path for G00 logic
                let isPenDown = false;

                contour.commands.forEach(cmd => {
                    const nextX = cmd.x !== undefined ? cmd.x : currentX;
                    const nextY = cmd.y !== undefined ? cmd.y : currentY;

                    if (cmd.type === 'G00') {
                        // Rapid move - Move without drawing
                        ctx.moveTo(tx(nextX), ty(nextY));
                        // Close path if we were drawing?
                        // Usually G00 implies starting a new shape or jumping.
                        // Ideally we Stroke previous path if exists.
                        // For HTML5 Canvas, moveTo simply moves the sub-path cursor.
                    } else if (cmd.type === 'G01') {
                        // Line
                        ctx.lineTo(tx(nextX), ty(nextY));
                    } else if (cmd.type === 'G02' || cmd.type === 'G03') {
                        // Arc
                        // Canvas arc is defined by Center, Radius, StartAngle, EndAngle.
                        // G-code gives EndPoint (X,Y) and Offset to Center (I,J) from StartPoint.
                        // CenterX = StartX + I
                        // CenterY = StartY + J

                        const i = cmd.i || 0;
                        const j = cmd.j || 0;

                        const centerX = currentX + i;
                        const centerY = currentY + j;

                        const radius = Math.sqrt(i*i + j*j);

                        // Angles in Radians
                        // Math.atan2(y, x) returns angle from X axis
                        const startAngle = Math.atan2(currentY - centerY, currentX - centerX);
                        const endAngle = Math.atan2(nextY - centerY, nextX - centerX);

                        // G02 is CW (Clockwise), G03 is CCW (Counter-Clockwise)
                        // Canvas arc(x, y, radius, startAngle, endAngle, counterclockwise)
                        // Canvas Y is inverted relative to standard cartesian:
                        // Standard: G02 (CW) -> Angle decreases. G03 (CCW) -> Angle increases.
                        // Canvas (Y down): Top is -Y, Bottom is +Y.
                        // This flips the visual rotation.
                        // Wait, our ty() function flips Y visually.
                        // So a CW motion in World space should look CW on screen.
                        // However, ctx.arc works in screen coordinates.
                        // Screen Y points down.
                        // A world angle of 0 (Right) is Screen 0.
                        // A world angle of 90 (Up) is Screen -90 (or 270).
                        // Let's rely on standard math:
                        // If we map coordinates correctly with ty(), we are drawing in a flipped space?
                        // No, ctx.arc takes screen coordinates for center.
                        // But angles?
                        // Angle 0 is always East (Right).
                        // Positive angle is Clockwise in Screen Space? No, standard is CCW from X-axis.
                        // If Y is flipped, CCW becomes CW visually?

                        // Let's try standard mapping first.
                        // We need the visual center on screen.
                        const cX = tx(centerX);
                        const cY = ty(centerY);
                        const scaledRadius = radius * scale;

                        // We need angles in the Screen Coordinate system.
                        // StartPoint on screen: (tx(currentX), ty(currentY))
                        // Center on screen: (cX, cY)
                        // vector = (tx(x) - cX, ty(y) - cY)
                        // = ( scale*(x-cx), -scale*(y-cy) )  <-- Note the minus on Y because ty flips
                        // So angle = atan2( - (y - cy), x - cx ) = atan2( cy - y, x - cx )

                        const angStart = Math.atan2(ty(currentY) - cY, tx(currentX) - cX);
                        const angEnd = Math.atan2(ty(nextY) - cY, tx(nextX) - cX);

                        // G02 (CW in Cartesian) -> CCW in Screen (if Y flipped)?
                        // Cartesian: +Y Up. CW = Angle Decreasing.
                        // Screen: +Y Down.
                        // Visual check: Clock hands move Right-Down-Left-Up.
                        // If we draw CW on screen, `anticlockwise` arg should be false.
                        // Does G02 correspond to visual CW on screen? Yes.
                        // So G02 -> anticlockwise=false. G03 -> true.
                        // BUT: Our Y-axis flip might invert the angle direction logic.

                        // Let's visualize:
                        // Start (1,0), Center (0,0), End (0,1).
                        // G03 (CCW).
                        // Screen: Start (100, 500), Center (0, 500), End (0, 400) (Up is lower Y).
                        // Vector Start: (100,0). Angle 0.
                        // Vector End: (0,-100). Angle -90.
                        // Canvas defaults to CCW being Positive Angle. 0 -> -90 is CW motion.
                        // So G03 (CCW World) became CW Screen?
                        // Yes, flipping one axis reverses winding order.
                        // So: G02 (CW World) -> CCW Screen (true).
                        //     G03 (CCW World) -> CW Screen (false).

                        const counterClockwise = cmd.type === 'G02';

                        ctx.arc(cX, cY, scaledRadius, angStart, angEnd, counterClockwise);

                        // We must ensure we lineTo the actual end point to fix rounding errors in arc drawing
                        // actually arc() does a moveTo start and lineTo end implicitly or explicitly?
                        // arc() draws from current point to start of arc, then the arc.
                        // We are already at start point (currentX/Y).
                    }

                    currentX = nextX;
                    currentY = nextY;
                });

                ctx.stroke();
            });
        });
    }
</script>

<div class="canvas-container" style="width: {width}px; height: {height}px;">
    <canvas
        bind:this={canvas}
        {width}
        {height}
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
    }
</style>
