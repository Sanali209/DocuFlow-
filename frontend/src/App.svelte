<script>
    import DocumentForm from "./lib/DocumentForm.svelte";
    import DocumentList from "./lib/DocumentList.svelte";
    import Modal from "./lib/Modal.svelte";
    import SettingsModal from "./lib/SettingsModal.svelte";
    import Sidebar from "./lib/Sidebar.svelte";
    import JournalView from "./lib/JournalView.svelte";
    import JobView from "./lib/JobView.svelte";

    let listComponent;
    let isModalOpen = $state(false);
    let isSettingsOpen = $state(false);
    let editingDoc = $state(null);
    let currentView = $state("documents"); // 'documents' | 'journal' | 'job'

    function refreshList() {
        if (listComponent) {
            listComponent.refresh();
        }
        isModalOpen = false;
        editingDoc = null;
    }

    function openCreateModal() {
        editingDoc = null;
        isModalOpen = true;
    }

    function openEditModal(doc) {
        editingDoc = doc;
        isModalOpen = true;
    }

    function closeModal() {
        isModalOpen = false;
        editingDoc = null;
    }

    function openSettings() {
        isSettingsOpen = true;
    }

    function closeSettings() {
        isSettingsOpen = false;
    }

    function handleViewChange(view) {
        currentView = view;
    }
</script>

<div class="app-container">
    <Sidebar activeView={currentView} onSelect={handleViewChange} />

    <div class="main-content-wrapper">
        <header>
            <div class="header-content">
                <h1>
                    {#if currentView === "documents"}
                        DocuFlow
                    {:else if currentView === "journal"}
                        Journal
                    {:else if currentView === "job"}
                        Job Tracking
                    {/if}
                </h1>
                <div class="header-actions">
                    <button
                        class="icon-btn"
                        onclick={openSettings}
                        title="Settings"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            ><circle cx="12" cy="12" r="3"></circle><path
                                d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
                            ></path></svg
                        >
                    </button>
                    {#if currentView === "documents"}
                        <button class="add-btn" onclick={openCreateModal}>
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="20"
                                height="20"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                stroke-width="2"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                ><line x1="12" y1="5" x2="12" y2="19"
                                ></line><line x1="5" y1="12" x2="19" y2="12"
                                ></line></svg
                            >
                            New Document
                        </button>
                    {/if}
                </div>
            </div>
        </header>

        <main>
            {#if currentView === "documents"}
                <DocumentList
                    bind:this={listComponent}
                    onEdit={openEditModal}
                />
            {:else if currentView === "journal"}
                <JournalView />
            {:else if currentView === "job"}
                <JobView />
            {/if}
        </main>
    </div>

    <Modal isOpen={isModalOpen} close={closeModal}>
        <DocumentForm
            onDocumentCreated={refreshList}
            onCancel={closeModal}
            document={editingDoc}
        />
    </Modal>

    <Modal isOpen={isSettingsOpen} close={closeSettings}>
        <SettingsModal isOpen={isSettingsOpen} close={closeSettings} />
    </Modal>
</div>

<style>
    :global(*), :global(*::before), :global(*::after) {
        box-sizing: border-box;
    }
    :global(html) {
        /* Ensure background covers the entire canvas, even on overscroll */
        background-color: #f1f5f9;
        /* Prevent horizontal scroll if possible, though overflow-x hidden on body is safer */
    }
    :global(body) {
        margin: 0;
        padding: 0;
        min-height: 100dvh; /* Dynamic viewport height to handle address bars */
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1e293b;
        background-color: #f1f5f9;
        /* Ensure body takes full width */
        width: 100%;
    }
    .app-container {
        min-height: 100dvh; /* Ensure container fills the dynamic viewport */
        display: flex;
        flex-direction: row; /* Changed to row for sidebar */
        width: 100%;
    }
    .main-content-wrapper {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0; /* Prevent flex child overflow */
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
        max-width: 1200px; /* Or unset to fill space */
        margin: 0 auto;
        padding: 0 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
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
        flex: 1; /* Pushes footer down if we had one */
    }
    .header-actions {
        display: flex;
        gap: 0.75rem;
        align-items: center;
    }
    .icon-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: #64748b;
        padding: 0.5rem;
        border-radius: 6px;
        display: flex;
        align-items: center;
        transition: background-color 0.2s, color 0.2s;
    }
    .icon-btn:hover {
        background-color: #f1f5f9;
        color: #0f172a;
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
