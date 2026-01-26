<script>
    import DocumentForm from './lib/DocumentForm.svelte';
    import DocumentList from './lib/DocumentList.svelte';
    import Modal from './lib/Modal.svelte';

    let listComponent;
    let isModalOpen = $state(false);

    function refreshList() {
        if (listComponent) {
            listComponent.refresh();
        }
        isModalOpen = false;
    }

    function openModal() {
        isModalOpen = true;
    }

    function closeModal() {
        isModalOpen = false;
    }
</script>

<div class="app-container">
    <header>
        <div class="header-content">
            <h1>DocuFlow</h1>
            <button class="add-btn" onclick={openModal}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                New Document
            </button>
        </div>
    </header>

    <main>
        <DocumentList bind:this={listComponent} />
    </main>

    <Modal isOpen={isModalOpen} close={closeModal}>
        <DocumentForm onDocumentCreated={refreshList} onCancel={closeModal} />
    </Modal>
</div>

<style>
    :global(body) {
        margin: 0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #f1f5f9;
        color: #1e293b;
    }
    .app-container {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
    }
    header {
        background-color: white;
        border-bottom: 1px solid #e2e8f0;
        padding: 1rem 0;
        position: sticky;
        top: 0;
        z-index: 100;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .header-content {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    @media (max-width: 640px) {
        .header-content {
            padding: 0 1rem;
        }
        h1 {
            font-size: 1.25rem;
        }
        .add-btn {
            padding: 0.5rem 0.75rem;
            font-size: 0.875rem;
        }
        main {
            padding: 1.5rem 1rem;
        }
    }
    h1 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.025em;
    }
    main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1.5rem;
        width: 100%;
        box-sizing: border-box;
        flex: 1;
    }
    .add-btn {
        background-color: #0f172a;
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        transition: background-color 0.2s;
        font-size: 0.95rem;
    }
    .add-btn:hover {
        background-color: #334155;
    }
</style>
