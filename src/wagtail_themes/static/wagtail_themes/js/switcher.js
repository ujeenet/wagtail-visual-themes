(function () {
    "use strict";
    const KEY = "wagtail-themes:mode";
    const root = document.documentElement;

    function getMode() {
        try { return localStorage.getItem(KEY) || root.getAttribute("data-theme") || "system"; }
        catch (e) { return root.getAttribute("data-theme") || "system"; }
    }

    function setMode(mode) {
        root.setAttribute("data-theme", mode);
        try { localStorage.setItem(KEY, mode); } catch (e) { /* noop */ }
        document.querySelectorAll("[data-wt-switcher]").forEach(syncSwitcher);
    }

    function syncSwitcher(switcher) {
        const current = getMode();
        switcher.querySelectorAll("button[data-wt-mode]").forEach(function (btn) {
            const isActive = btn.dataset.wtMode === current;
            btn.setAttribute("aria-pressed", isActive ? "true" : "false");
        });
    }

    function init() {
        document.querySelectorAll("[data-wt-switcher]").forEach(function (switcher) {
            if (switcher.dataset.initialized) return;
            switcher.dataset.initialized = "true";
            syncSwitcher(switcher);
            switcher.addEventListener("click", function (e) {
                const btn = e.target.closest("button[data-wt-mode]");
                if (!btn) return;
                setMode(btn.dataset.wtMode);
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
