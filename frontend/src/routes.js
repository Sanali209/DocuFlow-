import DashboardView from "./lib/DashboardView.svelte";
import DocumentsPage from "./lib/DocumentsPage.svelte";
import JournalView from "./lib/JournalView.svelte";
import JobView from "./lib/JobView.svelte";
import PartsView from "./lib/PartsView.svelte";
import GncView from "./lib/GncView.svelte";
import StockView from "./lib/StockView.svelte";
import SetupView from "./lib/SetupView.svelte";

// Define the routes
export default {
    "/": DashboardView,
    "/documents": DocumentsPage,
    "/journal": JournalView,
    "/job": JobView,
    "/parts": PartsView,
    "/gnc": GncView,
    "/stock": StockView,
    "/setup": SetupView
};
