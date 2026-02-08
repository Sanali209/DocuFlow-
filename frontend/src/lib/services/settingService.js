const API_URL = import.meta.env.VITE_API_URL || '';

function getHeaders(extraHeaders = {}) {
    const role = localStorage.getItem('user_role') || 'admin';
    return {
        'X-User-Role': role,
        ...extraHeaders
    };
}

export class SettingService {
    constructor(api_url) {
        this.baseUrl = `${api_url}/settings`;
    }

    async fetchSetting(key) {
        const response = await fetch(`${this.baseUrl}/${key}`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch setting');
        return await response.json();
    }

    async updateSetting(key, value) {
        const response = await fetch(`${this.baseUrl}/`, {
            method: 'PUT',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ key, value }),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Failed to update setting');
        }
        return await response.json();
    }

    async testPath(path) {
        const response = await fetch(`${this.baseUrl}/test-path`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ path }),
        });
        if (!response.ok) throw new Error('Failed to test path');
        return await response.json();
    }

    async fetchAssignees() {
        const response = await fetch(`${this.baseUrl}/assignees/list`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch assignees');
        return await response.json();
    }

    async createAssignee(data) {
        const response = await fetch(`${this.baseUrl}/assignees`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error('Failed to create assignee');
        return await response.json();
    }

    async updateAssignee(id, name) {
        const response = await fetch(`${this.baseUrl}/assignees/${id}`, {
            method: 'PUT',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ name }),
        });
        if (!response.ok) throw new Error('Failed to update assignee');
        return await response.json();
    }

    async deleteAssignee(id) {
        const response = await fetch(`${this.baseUrl}/assignees/${id}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to delete assignee');
        return await response.json();
    }

    async fetchDatabaseConfig() {
        const response = await fetch(`${API_URL}/settings/database/config`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch database config');
        return await response.json();
    }

    async updateDatabaseConfig(config) {
        const response = await fetch(`${API_URL}/settings/database/config`, {
            method: 'PUT',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(config)
        });
        if (!response.ok) throw new Error('Failed to update database config');
        return await response.json();
    }

    async triggerRescan() {
        const response = await fetch(`${API_URL}/inventory/rescan`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to trigger rescan');
        return await response.json();
    }
}
