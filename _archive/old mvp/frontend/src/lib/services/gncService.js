const API_URL = import.meta.env.VITE_API_URL || '';

function getHeaders(extraHeaders = {}) {
    const role = localStorage.getItem('user_role') || 'admin';
    return {
        'X-User-Role': role,
        ...extraHeaders
    };
}

export class GncService {
    constructor(api_url) {
        this.baseUrl = `${api_url}/gnc`;
    }

    async parseGnc(file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${this.baseUrl}/parse`, {
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

    async saveGnc(sheet, filename, overwrite = true) {
        const response = await fetch(`${this.baseUrl}/save`, {
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

    async scanParts(onProgress) {
        const response = await fetch(`${this.baseUrl}/scan`, {
            method: "POST",
            headers: getHeaders()
        });

        if (!response.ok) throw new Error("Failed to start scan");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n').filter(line => line.trim());

            for (const line of lines) {
                try {
                    const update = JSON.parse(line);
                    onProgress(update);
                } catch (e) {
                    console.error("Failed to parse progress:", line);
                }
            }
        }
    }
}
