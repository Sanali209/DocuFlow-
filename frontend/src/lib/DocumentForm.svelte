<script>
    import { createDocument } from './api.js';

    let { onDocumentCreated } = $props();

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
    <h3>Register Document</h3>
    <form onsubmit={handleSubmit}>
        <div class="form-group">
            <label for="name">Name:</label>
            <input id="name" type="text" bind:value={name} required placeholder="Document Name" />
        </div>

        <div class="form-group">
            <label for="type">Type:</label>
            <select id="type" bind:value={type}>
                <option value="plan">Plan</option>
                <option value="mail">Mail</option>
                <option value="other">Other</option>
            </select>
        </div>

        <div class="form-group">
            <label for="status">Status:</label>
            <select id="status" bind:value={status}>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
            </select>
        </div>

         <div class="form-group">
            <label for="date">Date:</label>
            <input id="date" type="date" bind:value={registration_date} />
        </div>

        <button type="submit">Register</button>
    </form>
</div>

<style>
    .form-container {
        padding: 1rem;
        border: 1px solid #ccc;
        border-radius: 8px;
        margin-bottom: 2rem;
        background-color: #f9f9f9;
    }
    .form-group {
        margin-bottom: 1rem;
    }
    label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: bold;
    }
    input, select {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-sizing: border-box;
    }
    button {
        padding: 0.5rem 1rem;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    button:hover {
        background-color: #0056b3;
    }
</style>
