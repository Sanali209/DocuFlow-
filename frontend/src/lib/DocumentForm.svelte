<script>
    import { createDocument } from './api.js';

    let { onDocumentCreated, onCancel } = $props();

    let name = $state('');
    let type = $state('plan');
    let status = $state('in_progress');
    let registration_date = $state('');

    async function handleSubmit(e) {
        e.preventDefault();
        const newDoc = {
            name,
            type,
            status,
            registration_date: registration_date || undefined
        };

        await createDocument(newDoc);

        // Reset form
        name = '';
        type = 'plan';
        status = 'in_progress';
        registration_date = '';

        onDocumentCreated();
    }
</script>

<div class="form-container">
    <h3>New Document</h3>
    <form onsubmit={handleSubmit}>
        <div class="form-group">
            <label for="name">Name</label>
            <input id="name" type="text" bind:value={name} required placeholder="e.g. Project Alpha Specs" />
        </div>

        <div class="row">
            <div class="form-group half">
                <label for="type">Type</label>
                <select id="type" bind:value={type}>
                    <option value="plan">Plan</option>
                    <option value="mail">Mail</option>
                    <option value="other">Other</option>
                </select>
            </div>

            <div class="form-group half">
                <label for="status">Status</label>
                <select id="status" bind:value={status}>
                    <option value="in_progress">In Progress</option>
                    <option value="done">Done</option>
                </select>
            </div>
        </div>

         <div class="form-group">
            <label for="date">Registration Date</label>
            <input id="date" type="date" bind:value={registration_date} />
        </div>

        <div class="actions">
            <button type="button" class="btn-secondary" onclick={onCancel}>Cancel</button>
            <button type="submit" class="btn-primary">Register Document</button>
        </div>
    </form>
</div>

<style>
    .form-container h3 {
        margin-top: 0;
        margin-bottom: 1.5rem;
        color: #2c3e50;
    }
    .form-group {
        margin-bottom: 1.25rem;
    }
    .row {
        display: flex;
        gap: 1rem;
    }
    .half {
        flex: 1;
    }
    label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #555;
        font-size: 0.9rem;
    }
    input, select {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        box-sizing: border-box;
        font-size: 1rem;
        transition: border-color 0.2s;
    }
    input:focus, select:focus {
        border-color: #3b82f6;
        outline: none;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    .actions {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        margin-top: 2rem;
    }
    button {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
        transition: background-color 0.2s;
    }
    .btn-primary {
        background-color: #3b82f6;
        color: white;
    }
    .btn-primary:hover {
        background-color: #2563eb;
    }
    .btn-secondary {
        background-color: #f1f5f9;
        color: #64748b;
    }
    .btn-secondary:hover {
        background-color: #e2e8f0;
    }
</style>
