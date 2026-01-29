<script>
    import { marked } from 'marked';

    let { document } = $props();
    let htmlContent = $derived(document && document.content ? marked.parse(document.content) : '<p>No content available.</p>');
</script>

<div class="document-view">
    <h2>{document?.name}</h2>
    <div class="meta">
        <span class="badge {document?.type}">{document?.type}</span>
        <span class="badge status-{document?.status}">{document?.status.replace('_', ' ')}</span>
        <span class="date">{document?.registration_date}</span>
        {#if document?.author}
            <span class="author">By {document.author}</span>
        {/if}
         {#if document?.done_date}
            <span class="date">Done: {document.done_date}</span>
        {/if}
    </div>

    {#if document?.tags?.length > 0}
        <div class="tags-row">
            {#each document.tags as tag}
                <span class="tag-badge">#{tag.name}</span>
            {/each}
        </div>
    {/if}

    <div class="content markdown-body">
        {@html htmlContent}
    </div>

    {#if document?.attachments?.length > 0}
        <div class="attachments">
            <h3>Attachments</h3>
            <div class="grid">
                {#each document.attachments as att}
                    <div class="attachment-card">
                         {#if att.media_type && att.media_type.startsWith('image/')}
                            <img src={att.file_path} alt={att.filename} />
                         {/if}
                         <a href={att.file_path} target="_blank" rel="noreferrer">{att.filename}</a>
                    </div>
                {/each}
            </div>
        </div>
    {/if}

    {#if document?.journal_entries?.length > 0}
        <div class="notes-section">
            <h3>Notes</h3>
            <div class="notes-list">
                {#each document.journal_entries as entry}
                    <div class="note-card">
                        <div class="note-header">
                            <span class="note-badge {entry.type}">{entry.type}</span>
                            <span class="note-author">{entry.author || 'Unknown'}</span>
                            <span class="note-date">{entry.created_at}</span>
                            <span class="note-status {entry.status}">{entry.status}</span>
                        </div>
                        <p class="note-text">{entry.text}</p>
                        {#if entry.attachments?.length > 0}
                            <div class="note-attachments">
                                <strong>Attachments:</strong>
                                {#each entry.attachments as att}
                                    <a href={att.file_path} target="_blank" rel="noreferrer" class="note-attachment-link">
                                        📎 {att.filename}
                                    </a>
                                {/each}
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
        </div>
    {/if}
</div>

<style>
    h2 {
        margin-top: 0;
        color: #1e293b;
    }
    .meta {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
        align-items: center;
        font-size: 0.9rem;
        color: #64748b;
        flex-wrap: wrap;
    }
    .badge {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .plan { background-color: #dbeafe; color: #1e40af; }
    .mail { background-color: #fce7f3; color: #9d174d; }
    .other { background-color: #f3f4f6; color: #374151; }
    .status-in_progress { background-color: #fef3c7; color: #92400e; }
    .status-done { background-color: #dcfce7; color: #166534; }

    .tags-row {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-bottom: 1.5rem;
    }
    .tag-badge {
        background: #e0e7ff;
        color: #3730a3;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .content {
        border-top: 1px solid #e2e8f0;
        padding-top: 1rem;
        line-height: 1.6;
        color: #334155;
    }

    /* Markdown Styles */
    :global(.markdown-body table) {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
    }
    :global(.markdown-body th), :global(.markdown-body td) {
        border: 1px solid #cbd5e1;
        padding: 0.5rem;
    }
    :global(.markdown-body th) {
        background-color: #f1f5f9;
        font-weight: 600;
    }
    :global(.markdown-body h1), :global(.markdown-body h2) {
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 0.3rem;
    }
    :global(.markdown-body p) {
        margin-bottom: 1rem;
    }

    .attachments {
        margin-top: 2rem;
        border-top: 1px solid #e2e8f0;
        padding-top: 1rem;
    }
    .attachments h3 {
        font-size: 1.1rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    .attachment-card {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.5rem;
        text-align: center;
        background: #f8fafc;
    }
    .attachment-card img {
        max-width: 100%;
        height: auto;
        display: block;
        margin-bottom: 0.5rem;
        border-radius: 4px;
    }
    .attachment-card a {
        font-size: 0.85rem;
        color: #3b82f6;
        text-decoration: none;
        word-break: break-all;
    }

    .notes-section {
        margin-top: 2rem;
        border-top: 1px solid #e2e8f0;
        padding-top: 1rem;
    }
    .notes-section h3 {
        font-size: 1.1rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .notes-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .note-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid #cbd5e1;
    }
    .note-card.info { border-left-color: #3b82f6; }
    .note-card.warning { border-left-color: #f59e0b; }
    .note-card.error { border-left-color: #ef4444; }
    .note-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
        flex-wrap: wrap;
        font-size: 0.85rem;
    }
    .note-badge {
        font-size: 0.7rem;
        text-transform: uppercase;
        font-weight: bold;
        padding: 0.1rem 0.4rem;
        border-radius: 4px;
        color: white;
    }
    .note-badge.info { background: #3b82f6; }
    .note-badge.warning { background: #f59e0b; }
    .note-badge.error { background: #ef4444; }
    .note-author {
        font-weight: 600;
        color: #1e293b;
    }
    .note-date {
        color: #64748b;
        font-size: 0.8rem;
    }
    .note-status {
        padding: 0.1rem 0.4rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .note-status.pending {
        background: #fff7ed;
        color: #c2410c;
    }
    .note-status.done {
        background: #f0fdf4;
        color: #15803d;
    }
    .note-text {
        color: #334155;
        margin: 0;
        line-height: 1.5;
        white-space: pre-wrap;
    }
    .note-attachments {
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid #e2e8f0;
        font-size: 0.85rem;
    }
    .note-attachments strong {
        color: #475569;
        display: block;
        margin-bottom: 0.5rem;
    }
    .note-attachment-link {
        display: block;
        color: #3b82f6;
        text-decoration: none;
        margin-bottom: 0.25rem;
    }
    .note-attachment-link:hover {
        text-decoration: underline;
    }

    /* Mobile optimization */
    @media (max-width: 640px) {
        h2 {
            font-size: 1.1rem;
        }
        .meta {
            gap: 0.25rem;
            font-size: 0.8rem;
        }
        .badge {
            font-size: 0.7rem;
            padding: 0.2rem 0.4rem;
        }
        .tags-row {
            gap: 0.25rem;
            margin-bottom: 1rem;
        }
        .tag-badge {
            font-size: 0.7rem;
            padding: 0.15rem 0.4rem;
        }
        .content {
            padding-top: 0.75rem;
            font-size: 0.9rem;
        }
        .attachments, .notes-section {
            margin-top: 1rem;
            padding-top: 0.75rem;
        }
        .attachments h3, .notes-section h3 {
            font-size: 0.95rem;
            margin-bottom: 0.75rem;
        }
        .grid {
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 0.5rem;
        }
        .attachment-card {
            padding: 0.4rem;
        }
        .attachment-card a {
            font-size: 0.75rem;
        }
        .notes-list {
            gap: 0.75rem;
        }
        .note-card {
            padding: 0.75rem;
            border-radius: 6px;
            border-left-width: 2px;
        }
        .note-header {
            gap: 0.25rem;
            margin-bottom: 0.4rem;
            font-size: 0.8rem;
        }
        .note-badge {
            font-size: 0.65rem;
        }
        .note-author {
            font-size: 0.8rem;
        }
        .note-date {
            font-size: 0.75rem;
        }
        .note-status {
            font-size: 0.7rem;
        }
        .note-text {
            font-size: 0.85rem;
        }
        .note-attachments {
            font-size: 0.8rem;
            margin-top: 0.5rem;
            padding-top: 0.5rem;
        }
        .note-attachment-link {
            font-size: 0.8rem;
        }
    }
</style>
