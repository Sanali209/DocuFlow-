const API_URL = import.meta.env.VITE_API_URL || '';

function getHeaders(extraHeaders = {}) {
    const role = localStorage.getItem('user_role') || 'admin';
    return {
        'X-User-Role': role,
        ...extraHeaders
    };
}

export class InventoryService {
    constructor(api_url) {
        this.baseUrl = api_url;
    }

    // Materials
    async fetchMaterials() {
        const response = await fetch(`${this.baseUrl}/materials/`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch materials');
        return await response.json();
    }

    async createMaterial(material) {
        const response = await fetch(`${this.baseUrl}/materials/`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(material),
        });
        if (!response.ok) throw new Error('Failed to create material');
        return await response.json();
    }

    async updateMaterial(id, name) {
        const response = await fetch(`${this.baseUrl}/materials/${id}?name=${encodeURIComponent(name)}`, {
            method: 'PUT',
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error('Failed to update material');
        return await response.json();
    }

    async deleteMaterial(id) {
        const response = await fetch(`${this.baseUrl}/materials/${id}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to delete material');
        return await response.json();
    }

    // Parts
    async fetchParts(skip = 0, limit = 100, filters = {}) {
        const params = new URLSearchParams({
            skip: String(skip),
            limit: String(limit)
        });

        if (filters.search) params.append('search', filters.search);
        if (filters.material_id) params.append('material_id', filters.material_id);
        if (filters.min_width) params.append('min_width', filters.min_width);
        if (filters.max_width) params.append('max_width', filters.max_width);
        if (filters.min_height) params.append('min_height', filters.min_height);
        if (filters.max_height) params.append('max_height', filters.max_height);

        const response = await fetch(`${this.baseUrl}/parts/?${params.toString()}`, {
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error('Failed to fetch parts');
        return await response.json();
    }

    async createPart(part) {
        const response = await fetch(`${this.baseUrl}/parts/`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(part),
        });
        if (!response.ok) throw new Error('Failed to create part');
        return await response.json();
    }

    async updatePart(id, data) {
        const response = await fetch(`${this.baseUrl}/parts/${id}`, {
            method: 'PUT',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error('Failed to update part');
        return await response.json();
    }

    async deletePart(id) {
        const response = await fetch(`${this.baseUrl}/parts/${id}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to delete part');
        return await response.json();
    }

    // Stock
    async fetchStock() {
        const response = await fetch(`${this.baseUrl}/stock/`, {
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error('Failed to fetch stock');
        return await response.json();
    }

    async createStockItem(item) {
        const response = await fetch(`${this.baseUrl}/stock/`, {
            method: 'POST',
            headers: getHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(item),
        });
        if (!response.ok) throw new Error('Failed to create stock item');
        return await response.json();
    }

    async deleteStockItem(id) {
        const response = await fetch(`${this.baseUrl}/stock/${id}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error('Failed to delete stock item');
        return await response.json();
    }

    async fetchPartGnc(id) {
        const response = await fetch(`${this.baseUrl}/parts/${id}/gnc`, {
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error("Failed to fetch part GNC");
        return await response.json();
    }

    async fetchLibraryParts() {
        const response = await fetch(`${this.baseUrl}/gnc/library-parts`, {
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error("Failed to fetch library parts");
        return await response.json();
    }

    async rescanParts() {
        const response = await fetch(`${this.baseUrl}/inventory/rescan`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error("Failed to trigger rescan");
        return await response.json();
    }
}
