<script>
    import DocumentForm from './lib/DocumentForm.svelte';
    import DocumentList from './lib/DocumentList.svelte';

    let listComponent;

    function refreshList() {
        if (listComponent) {
            listComponent.refresh();
        }
    }
</script>

<main>
    <h1>Document Tracker</h1>
    <DocumentForm onDocumentCreated={refreshList} />
    <DocumentList bind:this={listComponent} />
</main>

<style>
    main {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
        font-family: Arial, sans-serif;
    }
    h1 {
        text-align: center;
        color: #333;
    }
</style>
