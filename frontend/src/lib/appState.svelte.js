export const appState = $state({
    userRole: (typeof window !== "undefined" ? localStorage.getItem("user_role") : "admin") || "admin",
    configStatus: "unknown", // configured, needs_setup, db_error
    currentDocument: null,
    settings: {
        ocrUrl: "",
        docNameRegex: "",
        syncMihtavPath: "",
        syncSidraPath: ""
    }
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
