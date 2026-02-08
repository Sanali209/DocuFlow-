const API_URL = import.meta.env.VITE_API_URL || '';

function getHeaders(extraHeaders = {}) {
    const role = localStorage.getItem('user_role') || 'admin';
    return {
        'X-User-Role': role,
        ...extraHeaders
    };
}

export class JournalService {
    constructor(api_url) {
        this.baseUrl = `${api_url}/journal`;
    }

    async fetchJournal(skip = 0, limit = 100) {
        const response = await fetch(`${this.baseUrl}/?skip=${skip}&limit=${limit}`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch journal');
        return await response.json();
    }

    async createEntry(entry) {
        const response = await fetch(`${API_URL}/journal/`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(entry),
        });
        if (!response.ok) throw new Error('Failed to create journal entry');
        return await response.json();
    }

    async deleteEntry(id) {
        const response = await fetch(`${API_URL}/journal/${id}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to delete journal entry');
        return await response.json();
    }

    async updateEntry(id, entry) {
        const response = await fetch(`${API_URL}/journal/${id}`, {
            method: 'PUT',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(entry),
        });
        if (!response.ok) throw new Error('Failed to update journal entry');
        return await response.json();
    }
}
