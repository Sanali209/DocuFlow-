// Svelte 5 Global UI State
export const uiState = $state({
    userRole: localStorage.getItem('user_role') || 'admin',
    isLoading: false,
    notifications: [],

    addNotification(message, type = 'info') {
        const id = Date.now();
        this.notifications.push({ id, message, type });
        setTimeout(() => {
            this.notifications = this.notifications.filter(n => n.id !== id);
        }, 5000);
    },

    setRole(role) {
        this.userRole = role;
        localStorage.setItem('user_role', role);
    }
});
