const API_URL = import.meta.env.VITE_API_URL || '';

function getHeaders(extraHeaders = {}) {
    const role = localStorage.getItem('user_role') || 'admin';
    return {
        'X-User-Role': role,
        ...extraHeaders
    };
}

export class ProductionService {
    constructor(api_url) {
        this.baseUrl = `${api_url}/jobs`;
    }

    async fetchJobs(skip = 0, limit = 100, filters = {}) {
        const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString(), ...filters });
        const response = await fetch(`${this.baseUrl}/?${params.toString()}`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch jobs');
        return await response.json();
    }

    async getJob(id) {
        const response = await fetch(`${this.baseUrl}/${id}`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch job');
        return await response.json();
    }

    async createJob(job) {
        const response = await fetch(`${this.baseUrl}/`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(job),
        });
        if (!response.ok) throw new Error('Failed to create job');
        return await response.json();
    }

    async updateJob(id, job) {
        const response = await fetch(`${this.baseUrl}/${id}`, {
            method: 'PUT',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(job),
        });
        if (!response.ok) throw new Error('Failed to update job');
        return await response.json();
    }

    async updateJobStatus(id, status) {
        const response = await fetch(`${this.baseUrl}/${id}/status?status=${encodeURIComponent(status)}`, {
            method: 'PATCH',
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error('Failed to update job status');
        return await response.json();
    }

    async deleteJob(id) {
        const response = await fetch(`${this.baseUrl}/${id}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to delete job');
        return await response.json();
    }

    async fetchOrderTasks(orderId) {
        const response = await fetch(`${API_URL}/gnc/orders/${orderId}/tasks`, {
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error('Failed to fetch order tasks');
        return await response.json();
    }

    async saveOrderNesting(project) {
        const response = await fetch(`${API_URL}/gnc/save-order-nesting`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(project),
        });
        if (!response.ok) throw new Error('Failed to save order nesting');
        return await response.json();
    }

    async fetchOrderNestingProject(orderId) {
        const response = await fetch(`${API_URL}/gnc/orders/${orderId}/project`, {
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error('Failed to fetch nesting project');
        return await response.json();
    }

    async saveAsNewOrder(name, sheets, originalDocumentId) {
        const response = await fetch(`${API_URL}/documents/save-as-new-order`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ name, sheets, original_document_id: originalDocumentId }),
        });
        if (!response.ok) throw new Error('Failed to save as new order');
        return await response.json();
    }
}
