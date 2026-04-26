(function () {
    "use strict";

    function init() {
        document.querySelectorAll('[data-brand-color-chooser]').forEach(function (wrapper) {
            if (wrapper.dataset.initialized) return;
            wrapper.dataset.initialized = 'true';

            const select = wrapper.querySelector('.brand-color-select-hidden');
            const customSelect = wrapper.querySelector('.brand-color-select-custom');
            const selected = wrapper.querySelector('.brand-color-select-selected');
            const options = wrapper.querySelectorAll('.brand-color-select-option');
            const mainSwatch = wrapper.querySelector('.brand-color-preview-swatch');
            const selectedSwatch = selected.querySelector('.brand-color-option-swatch');
            const selectedLabel = selected.querySelector('.brand-color-option-label');

            updateDisplay();

            selected.addEventListener('click', function (e) {
                e.stopPropagation();
                closeAll();
                customSelect.classList.toggle('open');
            });

            customSelect.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    customSelect.classList.toggle('open');
                } else if (e.key === 'Escape') {
                    customSelect.classList.remove('open');
                } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                    e.preventDefault();
                    if (!customSelect.classList.contains('open')) {
                        customSelect.classList.add('open');
                    } else {
                        navigate(e.key === 'ArrowDown' ? 1 : -1);
                    }
                }
            });

            options.forEach(function (option) {
                option.addEventListener('click', function (e) {
                    e.stopPropagation();
                    selectOption(this);
                });
            });

            function selectOption(option) {
                select.value = option.dataset.value;
                select.dispatchEvent(new Event('change', { bubbles: true }));
                options.forEach(function (o) { o.classList.remove('selected'); });
                option.classList.add('selected');
                updateDisplay();
                customSelect.classList.remove('open');
            }

            function updateDisplay() {
                const value = select.value;
                const opt = select.options[select.selectedIndex];
                if (value && opt) {
                    const colorValue = opt.dataset.colorValue || '';
                    if (colorValue) {
                        selectedSwatch.style.background = colorValue;
                        selectedSwatch.style.borderStyle = 'solid';
                        if (mainSwatch) mainSwatch.style.background = colorValue;
                    } else {
                        selectedSwatch.style.background = 'transparent';
                        selectedSwatch.style.borderStyle = 'dashed';
                        if (mainSwatch) mainSwatch.style.background = 'transparent';
                    }
                    selectedLabel.textContent = opt.textContent;
                } else {
                    selectedSwatch.style.background = 'transparent';
                    selectedSwatch.style.borderStyle = 'dashed';
                    if (mainSwatch) mainSwatch.style.background = 'transparent';
                    selectedLabel.textContent = opt ? opt.textContent : '—';
                }
            }

            function navigate(direction) {
                const arr = Array.from(options);
                const current = arr.findIndex(function (o) { return o.classList.contains('selected'); });
                let next = current + direction;
                if (next < 0) next = arr.length - 1;
                if (next >= arr.length) next = 0;
                arr[next].scrollIntoView({ block: 'nearest' });
                selectOption(arr[next]);
            }
        });
    }

    function closeAll() {
        document.querySelectorAll('.brand-color-select-custom.open').forEach(function (el) {
            el.classList.remove('open');
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        init();
        document.addEventListener('click', function (e) {
            if (!e.target.closest('[data-brand-color-chooser]')) closeAll();
        });
        const observer = new MutationObserver(init);
        observer.observe(document.body, { childList: true, subtree: true });
    });
})();
