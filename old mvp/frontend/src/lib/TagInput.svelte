<script>
    import { onMount } from "svelte";
    import { docService } from "./stores/services.js";

    let { selectedTags = $bindable([]), placeholder = "Add tag..." } = $props();

    let inputValue = $state("");
    let allTags = $state([]);
    let suggestions = $state([]);
    let showSuggestions = $state(false);
    let inputEl;

    onMount(async () => {
        try {
            allTags = await docService.fetchTags();
        } catch (e) {
            console.error("Failed to fetch tags", e);
        }
    });

    function handleInput(e) {
        inputValue = e.target.value;

        // Check for comma
        if (inputValue.includes(",")) {
            const parts = inputValue.split(",");
            // If comma is not at start, process preceding part
            for (let part of parts) {
                part = part.trim();
                if (part) {
                    if (!selectedTags.includes(part)) {
                        selectedTags = [...selectedTags, part];
                    }
                }
            }
            inputValue = ""; // Clear input after comma
            showSuggestions = false;
            return;
        }

        if (inputValue) {
            suggestions = allTags.filter(
                (t) =>
                    t.name.toLowerCase().includes(inputValue.toLowerCase()) &&
                    !selectedTags.includes(t.name),
            );
            showSuggestions = true;
        } else {
            showSuggestions = false;
        }
    }

    function addTag(name) {
        if (name && !selectedTags.includes(name)) {
            selectedTags = [...selectedTags, name];
        }
        inputValue = "";
        showSuggestions = false;
        inputEl.focus();
    }

    function removeTag(name) {
        selectedTags = selectedTags.filter((t) => t !== name);
    }

    function handleKeydown(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            if (inputValue.trim()) {
                addTag(inputValue.trim());
            }
        } else if (
            e.key === "Backspace" &&
            !inputValue &&
            selectedTags.length > 0
        ) {
            removeTag(selectedTags[selectedTags.length - 1]);
        }
    }
</script>

<div class="tag-input-container">
    {#each selectedTags as tag}
        <span class="tag-chip">
            {tag}
            <button type="button" onclick={() => removeTag(tag)}>&times;</button
            >
        </span>
    {/each}

    <div class="input-wrapper">
        <input
            bind:this={inputEl}
            type="text"
            bind:value={inputValue}
            oninput={handleInput}
            onkeydown={handleKeydown}
            {placeholder}
            onblur={() => setTimeout(() => (showSuggestions = false), 200)}
            onfocus={() => inputValue && (showSuggestions = true)}
        />

        {#if showSuggestions && suggestions.length > 0}
            <ul class="suggestions">
                {#each suggestions as tag}
                    <!-- svelte-ignore a11y_click_events_have_key_events -->
                    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
                    <li onclick={() => addTag(tag.name)}>
                        {tag.name}
                    </li>
                {/each}
            </ul>
        {/if}
    </div>
</div>

<style>
    .tag-input-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        padding: 0.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        background: white;
        align-items: center;
    }
    .tag-chip {
        background: #e0e7ff;
        color: #3730a3;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }
    .tag-chip button {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 1rem;
        line-height: 1;
        padding: 0;
        color: #3730a3;
        opacity: 0.6;
    }
    .tag-chip button:hover {
        opacity: 1;
    }

    .input-wrapper {
        position: relative;
        flex-grow: 1;
        min-width: 100px;
    }
    input {
        border: none;
        outline: none;
        width: 100%;
        padding: 0.2rem;
        font-size: 0.95rem;
    }

    .suggestions {
        position: absolute;
        top: 100%;
        left: 0;
        width: 100%;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        list-style: none;
        padding: 0;
        margin: 0;
        max-height: 150px;
        overflow-y: auto;
        z-index: 10;
    }
    .suggestions li {
        padding: 0.5rem;
        cursor: pointer;
        font-size: 0.9rem;
    }
    .suggestions li:hover {
        background: #f1f5f9;
    }
</style>
