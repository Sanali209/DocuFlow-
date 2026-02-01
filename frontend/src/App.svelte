<script>
    import { onMount } from 'svelte';
    import { checkConfig } from './api';
    import Modal from './lib/Modal.svelte';
    import SettingsModal from './lib/SettingsModal.svelte';

    // ... existing props ...

    // ... existing logic ...

    let isConfigOpen = $state(false);

    onMount(async () => {
        try {
            const config = await checkConfig();
            if (config.status !== 'configured') {
                isConfigOpen = true;
            }
        } catch (e) {
            console.error('Config check failed', e);
            // Don't block app on network error, but maybe show toast
        }
    });

    function closeConfig() {
        isConfigOpen = false;
    }
</script>

<div class="app-container">
    <!-- ... existing markup ... -->
    <Sidebar activeView={currentView} onSelect={handleViewChange} />

    <div class="main-content-wrapper">
        <header>
            <div class="header-content">
                <h1>{getViewTitle(currentView)}</h1>
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
            {#if currentView === "dashboard"}
                <DashboardView />
            {:else if currentView === "documents"}
                <DocumentList
                    bind:this={listComponent}
                    onEdit={openEditModal}
                />
            {:else if currentView === "journal"}
                <JournalView />
            {:else if currentView === "job"}
                <JobView />
            {:else if currentView === "parts"}
                <PartsView />
            {:else if currentView === "gnc"}
                <GncView />
            {:else if currentView === "stock"}
                <StockView />
            {:else if currentView === "logs"}
                <ShiftLogView />
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

    <!-- Startup Configuration Modal (reuses SettingsModal logic but forces open) -->
    {#if isConfigOpen}
        <div class="startup-overlay">
            <div class="startup-modal">
                <div class="startup-header">
                    <h2>Welcome to DocuFlow</h2>
                    <p>Please configure the database connection to continue.</p>
                </div>
                <SettingsModal isOpen={true} close={closeConfig} />
            </div>
        </div>
    {/if}
</div>

<style>
    /* ... existing styles ... */
    :global(*), :global(*::before), :global(*::after) {
        box-sizing: border-box;
    }
    :global(html) {
        background-color: #f1f5f9;
    }
    :global(body) {
        margin: 0;
        padding: 0;
        min-height: 100dvh;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1e293b;
        background-color: #f1f5f9;
        width: 100%;
    }
    .app-container {
        min-height: 100dvh;
        display: flex;
        flex-direction: row;
        width: 100%;
    }
    .main-content-wrapper {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
        max-height: 100vh; /* Contain within viewport for scrollable areas */
        overflow: hidden; /* Main scroll is handled by inner containers */
    }
    header {
        background-color: white;
        border-bottom: 1px solid #e2e8f0;
        padding: 1rem 0;
        z-index: 100;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        flex-shrink: 0; /* Don't shrink header */
    }
    .header-content {
        max-width: 1400px;
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
            padding: 1rem;
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
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem 1.5rem;
        width: 100%;
        flex: 1;
        overflow-y: auto; /* Enable scrolling for content */
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

    /* Startup Modal Styles */
    .startup-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7); /* Darker background */
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }
    .startup-modal {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        width: 90%;
        max-width: 500px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    .startup-header {
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .startup-header h2 {
        margin: 0 0 0.5rem 0;
        color: #0f172a;
    }
    .startup-header p {
        margin: 0;
        color: #64748b;
    }
</style>
