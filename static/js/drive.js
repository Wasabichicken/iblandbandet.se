const typeFilter = document.getElementById('drive-type-filter');
const dateFilter = document.getElementById('drive-date-filter');
const table = document.getElementById('drive-table');

if (table && typeFilter && dateFilter) {
    // The ".." row is a navigation aid, not content - it stays visible
    // regardless of the type/date filters, so it's excluded from this set.
    const filterableRows = table.querySelectorAll('tbody tr:not(.drive-parent-row)');

    function withinDateRange(row, range) {
        if (range === 'all') return true;
        const days = { week: 7, month: 30, year: 365 }[range];
        const created = new Date(row.dataset.created);
        const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
        return created >= cutoff;
    }

    function applyFilters() {
        const type = typeFilter.value;
        const dateRange = dateFilter.value;
        filterableRows.forEach(row => {
            const matchesType = type === 'all' || row.dataset.type === type;
            const matchesDate = withinDateRange(row, dateRange);
            row.hidden = !(matchesType && matchesDate);
        });
    }

    typeFilter.addEventListener('change', applyFilters);
    dateFilter.addEventListener('change', applyFilters);

    // Drag-and-drop move: any owned row can be dragged, any folder row
    // (including the ".." row, to move something up to the parent) is a
    // valid drop target. The actual move is decided server-side regardless
    // (ownership, cycle prevention) - this just submits the same hidden form
    // the "Flytta till..." picker uses, as a real page reload.
    let draggedItemId = null;
    const dragDropForm = document.getElementById('drive-dragdrop-move-form');
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach(row => {
        row.addEventListener('dragstart', e => {
            if (row.dataset.owned !== 'true') {
                e.preventDefault();
                return;
            }
            draggedItemId = row.dataset.itemId;
        });

        if (row.dataset.isDirectory === 'true') {
            row.addEventListener('dragover', e => {
                if (draggedItemId === null || draggedItemId === row.dataset.itemId) return;
                e.preventDefault();
                row.classList.add('drive-drop-target-active');
            });

            row.addEventListener('dragleave', () => {
                row.classList.remove('drive-drop-target-active');
            });

            row.addEventListener('drop', e => {
                e.preventDefault();
                row.classList.remove('drive-drop-target-active');
                if (draggedItemId === null || draggedItemId === row.dataset.itemId || !dragDropForm) return;
                document.getElementById('drive-dragdrop-item-id').value = draggedItemId;
                document.getElementById('drive-dragdrop-new-parent-id').value = row.dataset.itemId;
                dragDropForm.submit();
            });
        }
    });
}

// "..." action menu: a plain hand-rolled toggle using Bootstrap's own
// .dropdown-menu/.show CSS classes (already loaded sitewide) rather than
// pulling in bootstrap.bundle.min.js just for this.
document.querySelectorAll('.drive-actions-toggle').forEach(toggle => {
    toggle.addEventListener('click', e => {
        e.stopPropagation();
        const menu = toggle.nextElementSibling;
        const wasOpen = menu.classList.contains('show');
        document.querySelectorAll('.drive-actions-dropdown .dropdown-menu.show').forEach(m => m.classList.remove('show'));
        if (!wasOpen) menu.classList.add('show');
    });
});

document.addEventListener('click', () => {
    document.querySelectorAll('.drive-actions-dropdown .dropdown-menu.show').forEach(m => m.classList.remove('show'));
});
