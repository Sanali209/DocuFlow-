<script>
    import { onMount } from 'svelte';
    import { fetchShiftLogs, createShiftLog } from './api';

    let logs = $state([]);
    let loading = $state(true);
    let newLogContent = $state('');
    let author = $state(localStorage.getItem('shift_author') || '');

    async function loadLogs() {
        loading = true;
        try {
            logs = await fetchShiftLogs();
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    }

    async function handleSubmit() {
        if (!newLogContent.trim() || !author.trim()) return;

        // Persist author
        localStorage.setItem('shift_author', author);

        try {
            const newLog = await createShiftLog({
                author,
                content: newLogContent,
                type: 'info'
            });
            logs = [newLog, ...logs];
            newLogContent = '';
        } catch (e) {
            alert('Failed to add log');
        }
    }

    onMount(loadLogs);
</script>

<div class="view-container">
    <div class="header">
        <h2>Shift Logs</h2>
    </div>

    <div class="input-area">
        <div class="input-row">
            <input
                type="text"
                placeholder="Author Name"
                bind:value={author}
                class="author-input"
            />
            <button class="post-btn" onclick={handleSubmit} disabled={!newLogContent.trim() || !author.trim()}>
                Post Log
            </button>
        </div>
        <textarea
            placeholder="What happened during this shift?"
            bind:value={newLogContent}
            rows="3"
        ></textarea>
    </div>

    {#if loading}
        <p class="loading">Loading logs...</p>
    {:else if logs.length === 0}
        <div class="empty-state">No logs yet. Start the conversation!</div>
    {:else}
        <div class="logs-feed">
            {#each logs as log}
                <div class="log-card">
                    <div class="log-header">
                        <span class="author">{log.author}</span>
                        <span class="time">{new Date(log.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="log-content">
                        {log.content}
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .view-container {
        max-width: 800px;
        margin: 0 auto;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        height: 80vh; /* Fixed height for scrolling */
    }
    .header {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #e2e8f0;
    }
    h2 { margin: 0; font-size: 1.25rem; color: #1e293b; }

    .input-area {
        padding: 1.5rem;
        background: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    .input-row {
        display: flex;
        gap: 1rem;
    }
    .author-input {
        flex: 1;
        padding: 0.5rem;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        max-width: 200px;
    }
    textarea {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        resize: vertical;
        font-family: inherit;
    }
    .post-btn {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
    }
    .post-btn:disabled {
        background-color: #94a3b8;
        cursor: not-allowed;
    }

    .logs-feed {
        flex: 1;
        overflow-y: auto;
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .log-card {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        background: white;
    }
    .log-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-size: 0.875rem;
    }
    .author { font-weight: 600; color: #0f172a; }
    .time { color: #64748b; }
    .log-content { color: #334155; white-space: pre-wrap; line-height: 1.5; }

    .loading, .empty-state { text-align: center; color: #64748b; padding: 2rem; }
</style>
