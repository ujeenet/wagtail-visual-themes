(function () {
    "use strict";

    const HEX_RE = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;

    function expandHex(value) {
        // #abc → #aabbcc, #aabbcc → #aabbcc
        const v = value.trim();
        if (!HEX_RE.test(v)) return null;
        let digits = v.slice(1);
        if (digits.length === 3) {
            digits = digits.split("").map(function (c) { return c + c; }).join("");
        }
        return "#" + digits.toLowerCase();
    }

    function init(root) {
        (root || document).querySelectorAll("[data-wt-color-picker]").forEach(function (wrap) {
            if (wrap.dataset.initialized) return;
            wrap.dataset.initialized = "true";

            const swatch = wrap.querySelector("[data-wt-color-swatch]");
            const text = wrap.querySelector("[data-wt-color-text]");
            if (!swatch || !text) return;

            // Picker → text
            swatch.addEventListener("input", function () {
                text.value = swatch.value;
                text.dispatchEvent(new Event("input", { bubbles: true }));
                text.dispatchEvent(new Event("change", { bubbles: true }));
            });

            // Text → picker (only when value is a parseable hex)
            text.addEventListener("input", function () {
                const expanded = expandHex(text.value);
                if (expanded) swatch.value = expanded;
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { init(); });
    } else {
        init();
    }

    // Re-init when Wagtail injects new form fields (panel expand, inline forms).
    new MutationObserver(function (mutations) {
        for (const m of mutations) {
            if (m.addedNodes && m.addedNodes.length) {
                init();
                return;
            }
        }
    }).observe(document.body, { childList: true, subtree: true });
})();
