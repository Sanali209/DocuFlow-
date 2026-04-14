export const appState = $state({
    userRole: (typeof window !== "undefined" ? localStorage.getItem("user_role") : "admin") || "admin",
    configStatus: "unknown", // configured, needs_setup, db_error
    currentDocument: null,
    settings: {
        ocrUrl: "",
        docNameRegex: "",
        syncMihtavPath: "",
        syncSidraPath: ""
    },
    // Tray Management
    partTray: [], // { part, quantity }
    trayVisible: false,

    // Global Menu Actions
    menuActions: [] // Array of { label: string, items: Array<{ label: string, action: () => void }> }
});

export function setUserRole(role) {
    appState.userRole = role;
    if (typeof window !== "undefined") {
        localStorage.setItem("user_role", role);
    }
}

export function setConfigStatus(status) {
    appState.configStatus = status;
}

// Menu Management
export function setMenuActions(actions) {
    appState.menuActions = actions;
}

export function clearMenuActions() {
    appState.menuActions = [];
}

// Tray helper functions exported below

export function addToTray(part) {
    const existing = appState.partTray.find(p => p.part.id === part.id);
    if (existing) {
        existing.quantity += 1;
    } else {
        appState.partTray.push({ part, quantity: 1 });
    }
    appState.trayVisible = true;
}

export function removeFromTray(partId) {
    appState.partTray = appState.partTray.filter(p => p.part.id !== partId);
}

export function updateTrayQuantity(partId, delta) {
    const item = appState.partTray.find(p => p.part.id === partId);
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            removeFromTray(partId);
        }
    }
}

export function clearTray() {
    appState.partTray = [];
}

export function toggleTray() {
    appState.trayVisible = !appState.trayVisible;
}
