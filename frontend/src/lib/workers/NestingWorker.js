/**
 * NestingWorker.js
 * Handles nesting logic with robust contour welding and spur removal.
 */

self.onmessage = function (e) {
    const { type, payload } = e.data;

    if (type === 'START_NESTING') {
        const { sheets, inventory, stock, config } = payload;
        const nestingMode = config.nestingMode || 'hull';

        console.log("Worker: START_NESTING received", {
            sheetsCount: sheets.length,
            inventorySize: inventory.length,
            multiSheet: config.multiSheet,
            mode: nestingMode
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
                    polygon: nestingMode === 'hull' ? processed.polygon : null,
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

            for (let sheet of resultSheets) {
                const area = sheet.nestingArea || {
                    x: 10, y: 10,
                    width: (sheet.width || 2000) - 20,
                    height: (sheet.height || 1000) - 20
                };

                const pos = findPlacement(part, sheet, area);
                if (pos) {
                    const newPartId = Math.max(0, ...resultSheets.flatMap(s => s.parts || []).map(p => p.id), ...placedParts.map(p => p.id)) + 1;
                    const newPart = {
                        ...part,
                        id: newPartId,
                        x: pos.x,
                        y: pos.y,
                        sheetIndex: resultSheets.indexOf(sheet)
                    };
                    sheet.parts = [...(sheet.parts || []), newPart];
                    placedParts.push(newPart);
                    placed = true;
                    console.log(`Worker: Placed ${part.name} at ${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}`);
                    break;
                }
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
                const pos = findPlacement(part, newSheet, area);
                if (pos) {
                    const newPartId = Math.max(0, ...resultSheets.flatMap(s => s.parts || []).map(p => p.id), ...placedParts.map(p => p.id)) + 1;
                    const newPart = {
                        ...part,
                        id: newPartId,
                        x: pos.x,
                        y: pos.y,
                        sheetIndex: resultSheets.length
                    };
                    newSheet.parts.push(newPart);
                    resultSheets.push(newSheet);
                    placedParts.push(newPart);
                    placed = true;
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

function dist(x1, y1, x2, y2) {
    return Math.sqrt(Math.pow(x1 - x2, 2) + Math.pow(y1 - y2, 2));
}

function findPlacement(part, sheet, area) {
    const pw = part.width;
    const ph = part.height;
    const padding = 5;

    for (let y = area.y; y <= area.y + area.height - ph; y += 5) {
        for (let x = area.x; x <= area.x + area.width - pw; x += 5) {
            let collision = false;
            for (let other of (sheet.parts || [])) {
                if (checkCollision(x, y, part, other, padding)) {
                    collision = true;
                    break;
                }
            }
            if (!collision) return { x, y };
        }
    }
    return null;
}

function checkCollision(x1, y1, part1, other, padding) {
    // 1. Fast bounding box check
    if (!(x1 + part1.width + padding < other.x || x1 > other.x + other.width + padding ||
        y1 + part1.height + padding < other.y || y1 > other.y + other.height + padding)) {

        // 2. Precise hull check if both have polygons
        if (part1.polygon && other.polygon) {
            return polygonsIntersect(
                part1.polygon.map(p => ({ x: p.x + x1, y: p.y + y1 })),
                other.polygon.map(p => ({ x: p.x + other.x, y: p.y + other.y })),
                padding
            );
        }
        return true; // Fallback to BBox if either lacks polygon
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
    return false;
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
