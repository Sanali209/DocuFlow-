<script module>
    import { tick } from "svelte";

    // Simple push function
    export function push(path) {
        window.history.pushState({}, "", path);
        window.dispatchEvent(new Event("popstate"));
    }

    let _location = $state({ path: window.location.pathname });

    if (typeof window !== "undefined") {
        const originalPushState = history.pushState;
        history.pushState = function (...args) {
            originalPushState.apply(this, args);
            _location.path = window.location.pathname;
            window.dispatchEvent(new Event("popstate"));
        };

        window.addEventListener("popstate", () => {
            _location.path = window.location.pathname;
        });
    }

    export const location = {
        get path() {
            return _location.path;
        },
    };
</script>

<script>
    import { onMount } from "svelte";

    let { routes } = $props();

    let currentPath = $state(window.location.pathname);
    let ActiveComponent = $state(null);

    function handleNavigation() {
        currentPath = window.location.pathname;
    }

    $effect(() => {
        let path = currentPath;
        let matched = null;

        // Ensure routes are valid
        if (!routes) return;

        const sortedRoutes = Object.keys(routes).sort(
            (a, b) => b.length - a.length,
        );

        for (const route of sortedRoutes) {
            if (route === path) {
                matched = routes[route];
                break;
            }
            if (path.startsWith(route) && route !== "/") {
                matched = routes[route];
                break;
            }
        }

        if (!matched) matched = routes["/"] || null;

        ActiveComponent = matched;
    });

    onMount(() => {
        window.addEventListener("popstate", handleNavigation);
        return () => {
            window.removeEventListener("popstate", handleNavigation);
        };
    });
</script>

{#if ActiveComponent}
    <ActiveComponent />
{:else}
    <p>404 Not Found</p>
{/if}
