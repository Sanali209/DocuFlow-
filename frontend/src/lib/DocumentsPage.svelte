<script>
    import { onMount } from "svelte";
    import DocumentList from "./DocumentList.svelte";
    import DocumentForm from "./DocumentForm.svelte";
    import Modal from "./Modal.svelte";

    let isModalOpen = $state(false);
    let editingDoc = $state(null);
    let listComponent = $state(null);

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

    function refreshList() {
        closeModal();
        if (listComponent && listComponent.refresh) {
            listComponent.refresh();
        }
    }
</script>

<div class="page-container">
    <div class="actions-bar">
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
                ><line x1="12" y1="5" x2="12" y2="19"></line><line
                    x1="5"
                    y1="12"
                    x2="19"
                    y2="12"
                ></line></svg
            >
            New Document
        </button>
    </div>

    <DocumentList bind:this={listComponent} onEdit={openEditModal} />

    <Modal isOpen={isModalOpen} close={closeModal}>
        <DocumentForm
            onDocumentCreated={refreshList}
            onCancel={closeModal}
            document={editingDoc}
        />
    </Modal>
</div>

<style>
    .page-container {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .actions-bar {
        display: flex;
        justify-content: flex-end;
        padding-bottom: 1rem;
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
