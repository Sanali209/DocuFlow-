<script>
    export let activeView = 'documents';
    export let onSelect; // Function to handle selection

    function select(view) {
        onSelect(view);
    }
</script>

<aside class="sidebar">
    <div class="sidebar-header">
        <span class="logo-icon">DF</span>
    </div>
    <nav>
        <button 
            class:active={activeView === 'dashboard'} 
            onclick={() => select('dashboard')}>
            <span class="icon">📊</span>
            <span class="label">Dashboard</span>
        </button>
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
        <button 
            class:active={activeView === 'job'} 
            onclick={() => select('job')}>
            <span class="icon">💼</span>
            <span class="label">Job Tracking</span>
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
    
    /* Only enable hover expansion on desktop */
    @media (min-width: 768px) {
        .sidebar:hover {
            width: 200px;
        }
        
        .sidebar:hover .label {
            opacity: 1;
        }
        
        /* Align content left when expanded */
        .sidebar:hover button {
            justify-content: flex-start;
        }
    }

    .sidebar-header {
        margin-bottom: 2rem;
        font-weight: bold;
        display: flex;
        justify-content: center;
        width: 100%;
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
        justify-content: center; /* Center icon on mobile */
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

    /* Mobile: keep sidebar compact, hide labels */
    @media (max-width: 768px) {
        .sidebar {
            width: 56px; /* Slightly narrower on mobile */
            padding-top: 0.75rem;
        }
        
        .sidebar-header {
            margin-bottom: 1.5rem;
        }
        
        .logo-icon {
            font-size: 1rem;
            padding: 0.4rem;
        }
        
        nav {
            padding: 0 0.25rem;
            gap: 0.25rem;
        }
        
        button {
            padding: 0.6rem;
        }
        
        .icon {
            font-size: 1.1rem;
        }
        
        .label {
            display: none; /* Completely hide labels on mobile */
        }
    }
</style>
