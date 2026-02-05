<script>
    import { onMount } from "svelte";
    import DocumentList from "./DocumentList.svelte";
    import DocumentForm from "./DocumentForm.svelte";
    import Modal from "./Modal.svelte";
    import { setMenuActions, clearMenuActions } from "./appState.svelte.js";

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
        if (listComponent && listComponent.refresh) {
            listComponent.refresh();
        }
    }

    function handleCreated() {
        closeModal();
        refreshList();
    }

    onMount(() => {
        setMenuActions([
            {
                label: "Documents",
                items: [
                    { label: "New Document", action: openCreateModal },
                    { label: "Refresh", action: refreshList }
                ]
            }
        ]);

        return () => {
            clearMenuActions();
        };
    });
</script>

<div class="page-container">
    <DocumentList bind:this={listComponent} onEdit={openEditModal} />

    <Modal isOpen={isModalOpen} close={closeModal}>
        <DocumentForm
            onDocumentCreated={handleCreated}
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
</style>
