const API_URL = import.meta.env.VITE_API_URL || '';
const DOC_BASE_URL = `${API_URL}/documents`;

function getHeaders(extraHeaders = {}) {
    const role = localStorage.getItem('user_role') || 'admin';
    return {
        'X-User-Role': role,
        ...extraHeaders
    };
}

export class DocumentService {
    constructor(api_url) {
        this.baseUrl = `${api_url}/documents`;
    }

    async fetchDocuments(params = {}) {
        const queryParams = new URLSearchParams(params);
        const response = await fetch(`${this.baseUrl}/?${queryParams.toString()}`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch documents');
        return await response.json();
    }

    async updateStatus(id, status) {
        const res = await fetch(`${this.baseUrl}/${id}/status`, {
            method: 'PUT',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ status })
        });
        if (!res.ok) throw new Error('Failed to update status');
        return await res.json();
    }

    async fetchDashboardStats() {
        const res = await fetch(`${this.baseUrl}/dashboard/stats`, {
            headers: getHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch dashboard stats');
        return await res.json();
    }

    async createDocument(doc) {
        const response = await fetch(`${this.baseUrl}/`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(doc),
        });
        if (!response.ok) throw new Error('Failed to create document');
        return await response.json();
    }

    async updateDocument(id, doc) {
        const response = await fetch(`${this.baseUrl}/${id}`, {
            method: 'PUT',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(doc),
        });
        if (!response.ok) throw new Error('Failed to update document');
        return await response.json();
    }

    async deleteDocument(id) {
        const response = await fetch(`${this.baseUrl}/${id}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to delete document');
        return await response.json();
    }

    async downloadDocumentZip(id) {
        window.location.href = `${this.baseUrl}/${id}/zip`;
    }

    async deleteAttachment(id) {
        const response = await fetch(`${API_URL}/attachments/${id}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to delete attachment');
        return await response.json();
    }

    async uploadFile(formData) {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            headers: getHeaders(),
            body: formData,
        });
        if (!response.ok) throw new Error('Failed to upload file');
        return await response.json();
    }

    async createOrder(name, items) {
        const response = await fetch(`${this.baseUrl}/create-order`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ name, items }),
        });
        if (!response.ok) throw new Error('Failed to create order');
        return await response.json();
    }

    async fetchTags() {
        const response = await fetch(`${this.baseUrl}/tags`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch tags');
        return await response.json();
    }
}
