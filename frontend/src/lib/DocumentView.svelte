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
</div>

<style>
    h2 {
        margin-top: 0;
        color: #1e293b;
    }
    .meta {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
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
</style>
