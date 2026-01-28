<script>
    let { activeView = 'documents', onSelect } = $props();

    let isExpanded = $state(false);

    function select(view) {
        onSelect(view);
    }

    function toggle() {
        isExpanded = !isExpanded;
    }

    function handleKeydown(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            toggle();
            e.preventDefault();
        }
    }
</script>

<aside class="sidebar" class:expanded={isExpanded}>
    <div class="sidebar-header"
         onclick={toggle}
         onkeydown={handleKeydown}
         role="button"
         tabindex="0"
         title="Toggle Sidebar">
        <span class="logo-icon">DF</span>
    </div>
    <nav>
        <button 
            class:active={activeView === 'documents'} 
            onclick={() => select('documents')}>
            <span class="icon">📄</span>
            <span class="label">Documents</span>
        </button>
        <button 
            class:active={activeView === 'journal'} 
            onclick={() => select('journal')}>
            <span class="icon">📓</span>
            <span class="label">Journal</span>
        </button>
    </nav>
</aside>

<style>
    .sidebar {
        width: 64px;
        background-color: #0f172a;
        color: white;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 1rem;
        transition: width 0.2s;
        z-index: 200;
    }
    
    .sidebar.expanded {
        width: 200px;
    }

    .sidebar-header {
        margin-bottom: 2rem;
        font-weight: bold;
        display: flex;
        justify-content: center;
        width: 100%;
        cursor: pointer;
    }

    .logo-icon {
        background: #3b82f6;
        padding: 0.5rem;
        border-radius: 8px;
        font-size: 1.2rem;
    }

    nav {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        width: 100%;
        padding: 0 0.5rem;
    }

    button {
        background: none;
        border: none;
        color: #94a3b8;
        padding: 0.75rem;
        border-radius: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 1rem;
        width: 100%;
        transition: all 0.2s;
        font-size: 1rem;
        overflow: hidden;
        white-space: nowrap;
    }

    button:hover {
        background-color: #1e293b;
        color: white;
    }

    button.active {
        background-color: #3b82f6;
        color: white;
    }

    .icon {
        font-size: 1.2rem;
        min-width: 24px;
        display: flex;
        justify-content: center;
    }

    .label {
        opacity: 0;
        transition: opacity 0.2s;
    }

    .sidebar.expanded .label {
        opacity: 1;
    }
</style>
