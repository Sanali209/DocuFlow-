// NestingWorker.js
// Handles CPU-intensive nesting operations using a genetic algorithm approach.

self.onmessage = function (e) {
    const { type, payload } = e.data;

    switch (type) {
        case 'START_NESTING':
            startNesting(payload);
            break;
        case 'STOP_NESTING':
            stopNesting();
            break;
        default:
            console.error('Unknown message type:', type);
    }
};

let isRunning = false;

function startNesting(data) {
    const { sheet, parts, config } = data;
    isRunning = true;

    // Simulate nesting process for now
    let progress = 0;

    console.log("Worker starting nesting...", data);

    const interval = setInterval(() => {
        if (!isRunning) {
            clearInterval(interval);
            return;
        }

        progress += 10;
        self.postMessage({ type: 'PROGRESS', payload: progress });

        if (progress >= 100) {
            clearInterval(interval);
            isRunning = false;

            // Mock result: simpler placement (grid)
            const nestedParts = parts.map((p, i) => ({
                ...p,
                x: (i % 5) * 100 + 10,
                y: Math.floor(i / 5) * 100 + 10,
                rotation: 0
            }));

            self.postMessage({ type: 'COMPLETE', payload: { parts: nestedParts } });
        }
    }, 500);
}

function stopNesting() {
    isRunning = false;
    self.postMessage({ type: 'STOPPED' });
}
