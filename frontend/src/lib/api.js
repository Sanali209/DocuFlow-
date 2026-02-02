const API_URL = import.meta.env.VITE_API_URL || '';

function getHeaders(extraHeaders = {}) {
    const role = localStorage.getItem('user_role') || 'admin';
    return {
        'X-User-Role': role,
        ...extraHeaders
    };
}

export async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        headers: getHeaders(),
        body: formData,
    });
    if (!response.ok) throw new Error('Upload failed');
    return await response.json();
}

export async function fetchDocuments(search = '', type = '', status = '', sortBy = 'registration_date', sortOrder = 'desc', tag = '', startDate = '', endDate = '', dateField = 'registration_date') {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (type) params.append('type', type);
    if (status) params.append('status', status);
    if (tag) params.append('tag', tag);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (dateField) params.append('date_field', dateField);
    if (sortBy) params.append('sort_by', sortBy);
    if (sortOrder) params.append('sort_order', sortOrder);

    const response = await fetch(`${API_URL}/documents/?${params.toString()}`, {
        headers: getHeaders()
    });
    return await response.json();
}

export async function fetchTags() {
    const response = await fetch(`${API_URL}/tags`, {
        headers: getHeaders()
    });
    return await response.json();
}

export async function fetchSetting(key) {
    const response = await fetch(`${API_URL}/settings/${key}`, {
        headers: getHeaders()
    });
    if (!response.ok) {
        throw new Error('Failed to fetch setting');
    }
    return await response.json();
}

export async function updateSetting(key, value) {
    const response = await fetch(`${API_URL}/settings/`, {
        method: 'PUT',
        headers: getHeaders({
            'Content-Type': 'application/json',
        }),
        body: JSON.stringify({ key, value }),
    });
    if (!response.ok) {
        // Pass through error
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Failed to update setting (${response.status})`);
    }
    return await response.json();
}

export async function checkConfig() {
    const response = await fetch(`${API_URL}/api/config-check`, {
        headers: getHeaders()
    });
    return await response.json();
}

export async function testPath(path) {
    const response = await fetch(`${API_URL}/settings/test-path`, {
        method: 'POST',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ path }),
    });
    return await response.json();
}

export async function createDocument(doc) {
    const response = await fetch(`${API_URL}/documents/`, {
        method: 'POST',
        headers: getHeaders({
            'Content-Type': 'application/json',
        }),
        body: JSON.stringify(doc),
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Failed to create document (${response.status})`);
    }
    return await response.json();
}

export async function updateDocumentStatus(id, status) {
    const response = await fetch(`${API_URL}/documents/${id}`, {
        method: 'PUT',
        headers: getHeaders({
            'Content-Type': 'application/json',
        }),
        body: JSON.stringify({ status }),
    });
    return await response.json();
}

export async function updateDocument(id, data) {
    const response = await fetch(`${API_URL}/documents/${id}`, {
        method: 'PUT',
        headers: getHeaders({
            'Content-Type': 'application/json',
        }),
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Failed to update document (${response.status})`);
    }
    return await response.json();
}

export async function scanDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/documents/scan`, {
        method: 'POST',
        headers: getHeaders(),
        body: formData,
    });

    if (!response.ok) {
        throw new Error('Scan failed');
    }
    return await response.json();
}

export async function deleteDocument(id) {
    const response = await fetch(`${API_URL}/documents/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
    });
    return await response.json();
}

export async function fetchJournalEntries(type = '', status = '', document_id = '') {
    const params = new URLSearchParams();
    if (type) params.append('type', type);
    if (status) params.append('status', status);
    if (document_id) params.append('document_id', document_id);

    const response = await fetch(`${API_URL}/journal/?${params.toString()}`, {
        headers: getHeaders(),
    });
    return await response.json();
}

export async function createJournalEntry(entry) {
    const response = await fetch(`${API_URL}/journal/`, {
        method: 'POST',
        headers: getHeaders({
            'Content-Type': 'application/json',
        }),
        body: JSON.stringify(entry),
    });
    return await response.json();
}

export async function updateJournalEntry(id, entry) {
    const response = await fetch(`${API_URL}/journal/${id}`, {
        method: 'PUT',
        headers: getHeaders({
            'Content-Type': 'application/json',
        }),
        body: JSON.stringify(entry),
    });
    return await response.json();
}

export async function deleteJournalEntry(id) {
    const response = await fetch(`${API_URL}/journal/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
    });
    return await response.json();
}

// Tasks
export async function fetchTasks(documentId) {
    const response = await fetch(`${API_URL}/documents/${documentId}/tasks`, {
        headers: getHeaders(),
    });
    return await response.json();
}

export async function createTask(documentId, task) {
    const response = await fetch(`${API_URL}/documents/${documentId}/tasks`, {
        method: 'POST',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(task),
    });
    return await response.json();
}

export async function updateTask(taskId, task) {
    const response = await fetch(`${API_URL}/tasks/${taskId}`, {
        method: 'PUT',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(task),
    });
    return await response.json();
}

export async function deleteTask(taskId) {
    const response = await fetch(`${API_URL}/tasks/${taskId}`, {
        method: 'DELETE',
        headers: getHeaders(),
    });
    return await response.json();
}

export async function deleteAttachment(attachmentId) {
    const response = await fetch(`${API_URL}/attachments/${attachmentId}`, {
        method: 'DELETE',
        headers: getHeaders(),
    });
    return await response.json();
}

// Filter Presets
export async function fetchFilterPresets() {
    const response = await fetch(`${API_URL}/filter-presets`, {
        headers: getHeaders(),
    });
    return await response.json();
}

export async function createFilterPreset(preset) {
    const response = await fetch(`${API_URL}/filter-presets`, {
        method: 'POST',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(preset),
    });
    return await response.json();
}

export async function deleteFilterPreset(id) {
    const response = await fetch(`${API_URL}/filter-presets/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
    });
    return await response.json();
}

// Materials
export async function fetchMaterials() {
    const response = await fetch(`${API_URL}/materials`, {
        headers: getHeaders(),
    });
    return await response.json();
}

export async function createMaterial(material) {
    const response = await fetch(`${API_URL}/materials`, {
        method: 'POST',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(material),
    });
    return await response.json();
}

export async function updateMaterial(materialId, name) {
    const response = await fetch(`${API_URL}/materials/${materialId}?name=${encodeURIComponent(name)}`, {
        method: 'PUT',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
    });
    return await response.json();
}

export async function deleteMaterial(materialId) {
    const response = await fetch(`${API_URL}/materials/${materialId}`, {
        method: 'DELETE',
        headers: getHeaders(),
    });
    return await response.json();
}

// Backup and Restore
export async function downloadBackup() {
    const response = await fetch(`${API_URL}/backup`, {
        headers: getHeaders(),
    });
    if (!response.ok) {
        throw new Error('Backup download failed');
    }

    // Get the blob
    const blob = await response.blob();

    // Create a download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    // Extract filename from Content-Disposition header if available
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'docuflow_backup.zip';
    if (contentDisposition) {
        const match = contentDisposition.match(/filename="?(.+)"?/);
        if (match) {
            filename = match[1];
        }
    }

    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

export async function uploadRestore(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/restore`, {
        method: 'POST',
        headers: getHeaders(),
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Restore failed');
    }

    return await response.json();
}

// Parts
export async function fetchParts(skip = 0, limit = 100, filters = {}) {
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

    const response = await fetch(`${API_URL}/parts?${params.toString()}`, {
        headers: getHeaders(),
    });
    return await response.json();
}

export async function createPart(part) {
    const response = await fetch(`${API_URL}/parts`, {
        method: 'POST',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(part),
    });
    return await response.json();
}

export async function deletePart(id) {
    const response = await fetch(`${API_URL}/parts/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
    });
    return await response.json();
}

// Stock
export async function fetchStock() {
    const response = await fetch(`${API_URL}/stock`, {
        headers: getHeaders(),
    });
    return await response.json();
}

export async function createStockItem(item) {
    const response = await fetch(`${API_URL}/stock`, {
        method: 'POST',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(item),
    });
    return await response.json();
}

export async function deleteStockItem(id) {
    const response = await fetch(`${API_URL}/stock/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
    });
    return await response.json();
}

// Shift Logs
export async function fetchShiftLogs(skip = 0, limit = 100) {
    const response = await fetch(`${API_URL}/shift-logs?skip=${skip}&limit=${limit}`, {
        headers: getHeaders(),
    });
    return await response.json();
}

export async function createShiftLog(log) {
    const response = await fetch(`${API_URL}/shift-logs`, {
        method: 'POST',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(log),
    });
    return await response.json();
}

// GNC
export async function parseGnc(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_URL}/gnc/parse`, {
        method: 'POST',
        headers: getHeaders(),
        body: formData,
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to parse GNC file');
    }
    return await response.json();
}

export async function saveGnc(sheet, filename, overwrite = true) {
    const response = await fetch(`${API_URL}/gnc/save`, {
        method: 'PUT',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
            sheet,
            filename,
            overwrite
        }),
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to save GNC file');
    }
    return await response.json();
}


