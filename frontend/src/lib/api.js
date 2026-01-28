const API_URL = import.meta.env.VITE_API_URL || '';

export async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
    });
    if (!response.ok) throw new Error('Upload failed');
    return await response.json();
}

export async function fetchDocuments(search = '', type = '', status = '', sortBy = 'registration_date', sortOrder = 'desc') {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (type) params.append('type', type);
    if (status) params.append('status', status);
    if (sortBy) params.append('sort_by', sortBy);
    if (sortOrder) params.append('sort_order', sortOrder);

    const response = await fetch(`${API_URL}/documents/?${params.toString()}`);
    return await response.json();
}

export async function fetchSetting(key) {
    const response = await fetch(`${API_URL}/settings/${key}`);
    if (!response.ok) {
        throw new Error('Failed to fetch setting');
    }
    return await response.json();
}

export async function updateSetting(key, value) {
    const response = await fetch(`${API_URL}/settings/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ key, value }),
    });
    return await response.json();
}

export async function createDocument(doc) {
    const response = await fetch(`${API_URL}/documents/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(doc),
    });
    return await response.json();
}

export async function updateDocumentStatus(id, status) {
    const response = await fetch(`${API_URL}/documents/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
    });
    return await response.json();
}

export async function updateDocument(id, data) {
    const response = await fetch(`${API_URL}/documents/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });
    return await response.json();
}

export async function scanDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/documents/scan`, {
        method: 'POST',
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
    });
    return await response.json();
}

export async function fetchJournalEntries(type = '', status = '', document_id = '') {
    const params = new URLSearchParams();
    if (type) params.append('type', type);
    if (status) params.append('status', status);
    if (document_id) params.append('document_id', document_id);

    const response = await fetch(`${API_URL}/journal/?${params.toString()}`);
    return await response.json();
}

export async function createJournalEntry(entry) {
    const response = await fetch(`${API_URL}/journal/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(entry),
    });
    return await response.json();
}

export async function updateJournalEntry(id, entry) {
    const response = await fetch(`${API_URL}/journal/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(entry),
    });
    return await response.json();
}

export async function deleteJournalEntry(id) {
    const response = await fetch(`${API_URL}/journal/${id}`, {
        method: 'DELETE',
    });
    return await response.json();
}

// Tasks
export async function fetchTasks(documentId) {
    const response = await fetch(`${API_URL}/documents/${documentId}/tasks`);
    return await response.json();
}

export async function createTask(documentId, task) {
    const response = await fetch(`${API_URL}/documents/${documentId}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(task),
    });
    return await response.json();
}

export async function updateTask(taskId, task) {
    const response = await fetch(`${API_URL}/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(task),
    });
    return await response.json();
}

export async function deleteTask(taskId) {
    const response = await fetch(`${API_URL}/tasks/${taskId}`, {
        method: 'DELETE',
    });
    return await response.json();
}

export async function deleteAttachment(attachmentId) {
    const response = await fetch(`${API_URL}/attachments/${attachmentId}`, {
        method: 'DELETE',
    });
    return await response.json();
}
