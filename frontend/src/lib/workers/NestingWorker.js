/**
 * NestingWorker.js
 * Handles nesting logic with robust contour welding and spur removal.
 */

self.onmessage = function (e) {
    const { type, payload } = e.data;

    if (type === 'START_NESTING') {
        const { sheets, inventory, stock, config } = payload;
        const nestingMode = config.nestingMode || 'hull';
        const spacing = config.spacing !== undefined ? config.spacing : 5;
        const rotations = config.rotations || 4;

        console.log("Worker: START_NESTING received", {
            sheetsCount: sheets.length,
            inventorySize: inventory.length,
            multiSheet: config.multiSheet,
            mode: nestingMode,
            rotations: rotations
        });

        // 1. Prepare Inventory with Welding and Polygon Extraction
        let partsToPlace = [];
        inventory.forEach(item => {
            const processed = weldAndCloseContours(item);

            if (nestingMode === 'hull' && !processed.isClosed) {
                console.warn(`Worker: Part ${item.name} could not be closed after welding. Skipping in 'hull' mode.`);
                return;
            }

            for (let i = 0; i < item.remaining; i++) {
                partsToPlace.push({
                    ...item,
                    width: processed.width || item.width || 100,
                    height: processed.height || item.height || 100,
                    polygon: processed.polygon || null,
                    minX: processed.minX || 0,
                    minY: processed.minY || 0,
                    originalRef: item,
                    instanceId: i
                });
            }
        });

        console.log(`Worker: Prepared ${partsToPlace.length} parts to place.`);

        // 2. Sort by Area (Decreasing) 
        partsToPlace.sort((a, b) => (b.width * b.height) - (a.width * a.height));

        let resultSheets = JSON.parse(JSON.stringify(sheets));
        let placedParts = [];
        let totalToPlace = partsToPlace.length;
        let processedCount = 0;

        if (totalToPlace === 0) {
            console.warn("Worker: No valid parts to place.");
            self.postMessage({ type: 'COMPLETE', payload: { sheets: resultSheets, parts: [] } });
            return;
        }

        // 3. Nesting Loop
        for (let part of partsToPlace) {
            let placed = false;

            // Try different rotations
            const angleStep = 360 / rotations;
            for (let r = 0; r < rotations; r++) {
                const angle = r * angleStep;
                let rotatedPart = part;

                if (angle !== 0) {
                    const rotated = rotatePolygon(part.polygon, angle);
                    if (rotated) {
                        const bounds = getPolygonBounds(rotated);
                        // Normalize
                        const normalizedPoly = rotated.map(p => ({
                            x: p.x - bounds.minX,
                            y: p.y - bounds.minY
                        }));
                        rotatedPart = {
                            ...part,
                            polygon: normalizedPoly,
                            width: bounds.width,
                            height: bounds.height,
                            rotation: angle
                        };
                    }
                } else {
                    rotatedPart.rotation = 0;
                }

                for (let sheet of resultSheets) {
                    const area = sheet.nestingArea || {
                        x: 10, y: 10,
                        width: (sheet.width || 2000) - 20,
                        height: (sheet.height || 1000) - 20
                    };

                    const pos = findPlacement(rotatedPart, sheet, area, spacing, config);
                    if (pos) {
                        const newPartId = Math.max(0, ...resultSheets.flatMap(s => s.parts || []).map(p => p.id), ...placedParts.map(p => p.id)) + 1;
                        const newPart = {
                            ...rotatedPart,
                            id: newPartId,
                            x: pos.x,
                            y: pos.y,
                            sheetIndex: resultSheets.indexOf(sheet)
                        };
                        sheet.parts = [...(sheet.parts || []), newPart];
                        placedParts.push(newPart);
                        placed = true;
                        console.log(`Worker: Placed ${part.name} at ${pos.x.toFixed(1)}, ${pos.y.toFixed(1)} with rotation ${angle}`);
                        break;
                    }
                }
                if (placed) break;
            }

            // New Sheet if needed
            if (!placed && config.multiSheet && stock && stock.length > 0) {
                const bestStock = stock[0];
                const newSheet = {
                    id: resultSheets.length,
                    name: `Sheet ${resultSheets.length + 1}`,
                    width: bestStock.width,
                    height: bestStock.height,
                    parts: []
                };

                const area = { x: 10, y: 10, width: newSheet.width - 20, height: newSheet.height - 20 };
                // Also try rotations for new sheet
                const angleStep = 360 / rotations;
                for (let r = 0; r < rotations; r++) {
                    const angle = r * angleStep;
                    let rotatedPart = part;
                    if (angle !== 0) {
                        const rotated = rotatePolygon(part.polygon, angle);
                        if (rotated) {
                            const bounds = getPolygonBounds(rotated);
                            const normalizedPoly = rotated.map(p => ({
                                x: p.x - bounds.minX,
                                y: p.y - bounds.minY
                            }));
                            rotatedPart = {
                                ...part,
                                polygon: normalizedPoly,
                                width: bounds.width,
                                height: bounds.height,
                                rotation: angle
                            };
                        }
                    } else {
                        rotatedPart.rotation = 0;
                    }

                    const pos = findPlacement(rotatedPart, newSheet, area, spacing, config);
                    if (pos) {
                        const newPartId = Math.max(0, ...resultSheets.flatMap(s => s.parts || []).map(p => p.id), ...placedParts.map(p => p.id)) + 1;
                        const newPart = {
                            ...rotatedPart,
                            id: newPartId,
                            x: pos.x,
                            y: pos.y,
                            sheetIndex: resultSheets.length
                        };
                        newSheet.parts.push(newPart);
                        resultSheets.push(newSheet);
                        placedParts.push(newPart);
                        placed = true;
                        break;
                    }
                    if (placed) break;
                }
            }

            if (!placed) {
                console.error(`Worker: FAILED to place part ${part.name}`);
            }

            processedCount++;
            self.postMessage({
                type: 'PROGRESS',
                payload: Math.floor((processedCount / totalToPlace) * 100)
            });
        }

        self.postMessage({ type: 'COMPLETE', payload: { sheets: resultSheets, parts: placedParts } });

    } else if (type === 'STOP_NESTING') {
        self.postMessage({ type: 'STOPPED' });
    } else if (type === 'ANALYZE_SHEET') {
        const { sheet } = payload;
        console.log("Worker: Analysis started for sheet", sheet.id);

        const analyzedParts = sheet.parts.map(part => {
            const processed = weldAndCloseContours(part);
            return {
                ...part,
                width: processed.width || part.width || 0,
                height: processed.height || part.height || 0,
                polygon: processed.polygon || null,
                minX: processed.minX || 0,
                minY: processed.minY || 0,
                analysisComplete: true
            };
        });

        self.postMessage({
            type: 'ANALYSIS_COMPLETE',
            payload: {
                sheetId: sheet.id,
                parts: analyzedParts
            }
        });
    }
};

/**
 * Welds segments and removes "spurs" (dangling lead-ins) to find the outer hull.
 */
function weldAndCloseContours(part) {
    if (!part.contours) return { isClosed: false };

    let segments = [];
    part.contours.forEach(c => {
        let curX = null, curY = null;
        c.commands.forEach(cmd => {
            const prevX = curX;
            const prevY = curY;
            if (cmd.x !== undefined) curX = cmd.x;
            if (cmd.y !== undefined) curY = cmd.y;
            if (prevX !== null && curX !== null && (prevX !== curX || prevY !== curY)) {
                segments.push({ x1: prevX, y1: prevY, x2: curX, y2: curY });
            }
        });
    });

    if (segments.length === 0) return { isClosed: false };

    // Weld segments based on proximity (2.0mm threshold for welding - higher for lead-ins as requested)
    const threshold = 2.0;
    let graphEdges = [];

    // Simplify segments by snapping endpoints to a grid or merged points
    let points = [];
    function getPid(x, y) {
        for (let i = 0; i < points.length; i++) {
            if (dist(x, y, points[i].x, points[i].y) < threshold) return i;
        }
        points.push({ x, y });
        return points.length - 1;
    }

    segments.forEach(s => {
        const p1 = getPid(s.x1, s.y1);
        const p2 = getPid(s.x2, s.y2);
        if (p1 !== p2) {
            graphEdges.push([p1, p2]);
        }
    });

    // 2. Recursive Spur Removal (remove vertices with valence 1)
    let degrees = new Array(points.length).fill(0);
    graphEdges.forEach(e => { degrees[e[0]]++; degrees[e[1]]++; });

    let changed = true;
    while (changed) {
        changed = false;
        for (let i = 0; i < points.length; i++) {
            if (degrees[i] === 1) {
                // Find and remove the edge
                for (let j = 0; j < graphEdges.length; j++) {
                    const e = graphEdges[j];
                    if (e[0] === i || e[1] === i) {
                        degrees[e[0]]--;
                        degrees[e[1]]--;
                        graphEdges.splice(j, 1);
                        changed = true;
                        break;
                    }
                }
            }
        }
    }

    // 3. Reconstruct paths from cleaned graph
    let adj = new Array(points.length).fill(0).map(() => []);
    graphEdges.forEach(e => { adj[e[0]].push(e[1]); adj[e[1]].push(e[0]); });

    let visited = new Set();
    let loops = [];
    for (let i = 0; i < points.length; i++) {
        if (!visited.has(i) && adj[i].length >= 2) {
            let path = [i];
            let curr = i;
            let next = adj[i][0];
            while (next !== undefined && !visited.has(next)) {
                visited.add(next);
                path.push(next);
                let neighbors = adj[next];
                let prev = path[path.length - 2];
                next = neighbors.find(n => n !== prev);
                if (next === i) break; // Closed loop
            }
            if (path.length > 2) loops.push(path);
        }
    }

    // 4. Find the largest loop (outer hull)
    if (loops.length === 0) {
        let minX = Math.min(...points.map(p => p.x)), maxX = Math.max(...points.map(p => p.x));
        let minY = Math.min(...points.map(p => p.y)), maxY = Math.max(...points.map(p => p.y));
        return { isClosed: false, width: maxX - minX, height: maxY - minY };
    }

    // Sort by perimeter as a proxy for size
    let bestLoop = loops.sort((a, b) => b.length - a.length)[0];
    let poly = bestLoop.map(id => points[id]);

    let minX = Math.min(...poly.map(p => p.x)), maxX = Math.max(...poly.map(p => p.x));
    let minY = Math.min(...poly.map(p => p.y)), maxY = Math.max(...poly.map(p => p.y));

    // Normalize polygon relative to minX, minY
    poly = poly.map(p => ({ x: p.x - minX, y: p.y - minY }));

    return {
        isClosed: true,
        width: maxX - minX,
        height: maxY - minY,
        polygon: poly,
        minX, minY
    };
}

function rotatePolygon(poly, angle) {
    if (!poly) return null;
    const rad = (angle * Math.PI) / 180;
    const cos = Math.cos(rad);
    const sin = Math.sin(rad);
    return poly.map(p => ({
        x: p.x * cos - p.y * sin,
        y: p.x * sin + p.y * cos
    }));
}

function getPolygonBounds(poly) {
    if (!poly || poly.length === 0) return { minX: 0, minY: 0, width: 0, height: 0 };
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    poly.forEach(p => {
        if (p.x < minX) minX = p.x;
        if (p.x > maxX) maxX = p.x;
        if (p.y < minY) minY = p.y;
        if (p.y > maxY) maxY = p.y;
    });
    return { minX, minY, width: maxX - minX, height: maxY - minY };
}

function dist(x1, y1, x2, y2) {
    return Math.sqrt(Math.pow(x1 - x2, 2) + Math.pow(y1 - y2, 2));
}

function findPlacement(part, sheet, area, padding, config) {
    const pw = part.width;
    const ph = part.height;

    // Step size can be smaller than padding for better fit, or equal. 5mm is a reasonable default.
    const step = 5;

    for (let y = area.y; y <= area.y + area.height - ph; y += step) {
        for (let x = area.x; x <= area.x + area.width - pw; x += step) {
            let collision = false;
            for (let other of (sheet.parts || [])) {
                if (checkCollision(x, y, part, other, padding, config)) {
                    collision = true;
                    break;
                }
            }
            if (!collision) return { x, y };
        }
    }
    return null;
}

function checkCollision(x1, y1, part1, other, padding, config) {
    // 1. Fast bounding box check
    if (!(x1 + part1.width + padding < other.x || x1 > other.x + other.width + padding ||
        y1 + part1.height + padding < other.y || y1 > other.y + other.height + padding)) {

        // 2. Precise hull check if both have polygons AND we are in 'hull' mode
        if (config.nestingMode === 'hull' && part1.polygon && other.polygon) {
            return polygonsIntersect(
                part1.polygon.map(p => ({ x: p.x + x1, y: p.y + y1 })),
                other.polygon.map(p => ({ x: p.x + other.x, y: p.y + other.y })),
                padding
            );
        }
        return true; // Fallback to BBox if either lacks polygon or we are in 'bbox' mode
    }
    return false;
}

function polygonsIntersect(a, b, padding) {
    // Check for segment intersections
    for (let i = 0; i < a.length; i++) {
        const a1 = a[i];
        const a2 = a[(i + 1) % a.length];
        for (let j = 0; j < b.length; j++) {
            const b1 = b[j];
            const b2 = b[(j + 1) % b.length];
            if (segmentsIntersect(a1, a2, b1, b2)) return true;
        }
    }
    // Check if any point is inside the other
    if (pointInPolygon(a[0], b) || pointInPolygon(b[0], a)) return true;

    // Check padding (minimum distance)
    if (padding > 0) {
        // Check if any point of A is close to B
        for (let i = 0; i < a.length; i++) {
            if (pointPolygonDist(a[i], b) < padding) return true;
        }
        // Check if any point of B is close to A
        for (let i = 0; i < b.length; i++) {
            if (pointPolygonDist(b[i], a) < padding) return true;
        }
    }

    return false;
}

function pointPolygonDist(p, poly) {
    let minD2 = Infinity;
    for (let i = 0; i < poly.length; i++) {
        const p1 = poly[i];
        const p2 = poly[(i + 1) % poly.length];
        const d2 = distToSegmentSquared(p, p1, p2);
        if (d2 < minD2) minD2 = d2;
    }
    return Math.sqrt(minD2);
}

function distToSegmentSquared(p, v, w) {
    const l2 = (v.x - w.x) ** 2 + (v.y - w.y) ** 2;
    if (l2 === 0) return (p.x - v.x) ** 2 + (p.y - v.y) ** 2;
    let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
    t = Math.max(0, Math.min(1, t));
    return (p.x - (v.x + t * (w.x - v.x))) ** 2 + (p.y - (v.y + t * (w.y - v.y))) ** 2;
}

function segmentsIntersect(p1, p2, p3, p4) {
    const det = (p2.x - p1.x) * (p4.y - p3.y) - (p2.y - p1.y) * (p4.x - p3.x);
    if (det === 0) return false;
    const lambda = ((p4.y - p3.y) * (p4.x - p1.x) + (p3.x - p4.x) * (p4.y - p1.y)) / det;
    const gamma = ((p1.y - p2.y) * (p4.x - p1.x) + (p2.x - p1.x) * (p4.y - p1.y)) / det;
    return (0 < lambda && lambda < 1) && (0 < gamma && gamma < 1);
}

function pointInPolygon(p, poly) {
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
        if (((poly[i].y > p.y) !== (poly[j].y > p.y)) &&
            (p.x < (poly[j].x - poly[i].x) * (p.y - poly[i].y) / (poly[j].y - poly[i].y) + poly[i].x)) {
            inside = !inside;
        }
    }
    return inside;
}
