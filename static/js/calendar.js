(function () {
    const basePath = window.APP_BASE_PATH || '';
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    const csrfToken = calendarEl.dataset.csrfToken;
    const isLoggedIn = !!csrfToken;

    const SWEDISH_MONTHS = ['jan', 'feb', 'mar', 'apr', 'maj', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];

    function pad(n) {
        return String(n).padStart(2, '0');
    }

    function toLocalInputValue(date) {
        return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) +
            'T' + pad(date.getHours()) + ':' + pad(date.getMinutes());
    }

    function formatEventWhen(start, end) {
        const datePart = start.getDate() + ' ' + SWEDISH_MONTHS[start.getMonth()] + ' ' + start.getFullYear();
        let timePart = pad(start.getHours()) + ':' + pad(start.getMinutes());
        if (end) timePart += '–' + pad(end.getHours()) + ':' + pad(end.getMinutes());
        return datePart + ', ' + timePart;
    }

    // --- Read-only event details (shown to visitors who aren't logged in) ---

    const detailsEl = document.getElementById('calendar-event-details');

    function showEventDetails(event) {
        if (!detailsEl) return;
        const detailsTitle = document.getElementById('calendarEventDetailsTitle');
        const detailsWhen = document.getElementById('calendarEventDetailsWhen');
        const detailsLocation = document.getElementById('calendarEventDetailsLocation');
        const detailsDescription = document.getElementById('calendarEventDetailsDescription');

        detailsTitle.textContent = event.title;
        detailsWhen.textContent = formatEventWhen(event.start, event.end);

        const location = event.extendedProps.location;
        const lat = event.extendedProps.latitude;
        const lon = event.extendedProps.longitude;
        detailsLocation.innerHTML = '';
        if (location) {
            if (lat != null && lon != null) {
                const link = document.createElement('a');
                link.href = 'https://www.openstreetmap.org/?mlat=' + lat + '&mlon=' + lon + '#map=17/' + lat + '/' + lon;
                link.target = '_blank';
                link.rel = 'noopener';
                link.textContent = location;
                detailsLocation.appendChild(link);
            } else {
                detailsLocation.textContent = location;
            }
        }
        detailsLocation.hidden = !location;

        detailsDescription.textContent = event.extendedProps.description || '';
        detailsDescription.hidden = !event.extendedProps.description;

        detailsEl.hidden = false;
    }

    const detailsCloseBtn = document.getElementById('calendarEventDetailsClose');
    if (detailsCloseBtn) {
        detailsCloseBtn.addEventListener('click', () => {
            detailsEl.hidden = true;
        });
    }

    // --- Editable event modal (members only) ---

    let modal, modalTitle, modalError, eventIdInput, titleInput, startInput, endInput,
        locationInput, locationResultsEl, latitudeInput, longitudeInput, descriptionInput,
        deleteBtn, saveBtn;

    if (isLoggedIn) {
        modal = new bootstrap.Modal(document.getElementById('eventModal'));
        modalTitle = document.getElementById('eventModalTitle');
        modalError = document.getElementById('eventModalError');
        eventIdInput = document.getElementById('eventId');
        titleInput = document.getElementById('eventTitle');
        startInput = document.getElementById('eventStart');
        endInput = document.getElementById('eventEnd');
        locationInput = document.getElementById('eventLocation');
        locationResultsEl = document.getElementById('eventLocationResults');
        latitudeInput = document.getElementById('eventLatitude');
        longitudeInput = document.getElementById('eventLongitude');
        descriptionInput = document.getElementById('eventDescription');
        deleteBtn = document.getElementById('eventDeleteBtn');
        saveBtn = document.getElementById('eventSaveBtn');
    }

    function showError(message) {
        modalError.textContent = message;
        modalError.hidden = false;
    }

    function hideLocationResults() {
        locationResultsEl.hidden = true;
        locationResultsEl.innerHTML = '';
    }

    function resetForm() {
        modalError.hidden = true;
        eventIdInput.value = '';
        titleInput.value = '';
        startInput.value = '';
        endInput.value = '';
        locationInput.value = '';
        latitudeInput.value = '';
        longitudeInput.value = '';
        hideLocationResults();
        descriptionInput.value = '';
        deleteBtn.hidden = true;
    }

    function openCreateModal(startDate) {
        resetForm();
        modalTitle.textContent = 'Lägg till händelse';
        if (startDate) startInput.value = toLocalInputValue(startDate);
        modal.show();
    }

    function openEditModal(event) {
        resetForm();
        modalTitle.textContent = 'Redigera händelse';
        eventIdInput.value = event.id;
        titleInput.value = event.title;
        startInput.value = toLocalInputValue(event.start);
        endInput.value = event.end ? toLocalInputValue(event.end) : '';
        locationInput.value = event.extendedProps.location || '';
        latitudeInput.value = event.extendedProps.latitude != null ? event.extendedProps.latitude : '';
        longitudeInput.value = event.extendedProps.longitude != null ? event.extendedProps.longitude : '';
        descriptionInput.value = event.extendedProps.description || '';
        deleteBtn.hidden = false;
        modal.show();
    }

    // Location search - OpenStreetMap's free Nominatim API, called directly
    // from the browser (no backend involved). Debounced well past their
    // 1 request/second usage policy, since a keystroke resets the timer.
    let searchTimeout = null;

    function searchLocation(query) {
        fetch('https://nominatim.openstreetmap.org/search?format=json&limit=5&q=' + encodeURIComponent(query))
            .then((response) => response.json())
            .then((results) => {
                locationResultsEl.innerHTML = '';
                if (!results.length) {
                    hideLocationResults();
                    return;
                }
                results.forEach((result) => {
                    const li = document.createElement('li');
                    li.textContent = result.display_name;
                    li.addEventListener('click', () => {
                        locationInput.value = result.display_name;
                        latitudeInput.value = result.lat;
                        longitudeInput.value = result.lon;
                        hideLocationResults();
                    });
                    locationResultsEl.appendChild(li);
                });
                locationResultsEl.hidden = false;
            })
            .catch(() => hideLocationResults());
    }

    function postToApi(fields) {
        const body = new URLSearchParams(Object.assign({ csrf_token: csrfToken }, fields));
        return fetch(basePath + '/members/calendar_api.cgi', { method: 'POST', body: body })
            .then((response) => response.json());
    }

    function persistEventChange(event) {
        return postToApi({
            action: 'update',
            event_id: event.id,
            title: event.title,
            starts_at: toLocalInputValue(event.start),
            ends_at: event.end ? toLocalInputValue(event.end) : '',
            location: event.extendedProps.location || '',
            latitude: event.extendedProps.latitude != null ? event.extendedProps.latitude : '',
            longitude: event.extendedProps.longitude != null ? event.extendedProps.longitude : '',
            description: event.extendedProps.description || '',
        }).then((data) => {
            if (data.error) throw new Error(data.error);
        });
    }

    if (isLoggedIn) {
        locationInput.addEventListener('input', () => {
            latitudeInput.value = '';
            longitudeInput.value = '';
            clearTimeout(searchTimeout);
            const query = locationInput.value.trim();
            if (query.length < 3) {
                hideLocationResults();
                return;
            }
            searchTimeout = setTimeout(() => searchLocation(query), 600);
        });

        document.addEventListener('click', (event) => {
            if (event.target !== locationInput && !locationResultsEl.contains(event.target)) {
                hideLocationResults();
            }
        });

        saveBtn.addEventListener('click', () => {
            if (!titleInput.value || !startInput.value) {
                showError('Titel och starttid måste fyllas i.');
                return;
            }

            const isEdit = !!eventIdInput.value;
            saveBtn.disabled = true;
            postToApi({
                action: isEdit ? 'update' : 'create',
                event_id: eventIdInput.value,
                title: titleInput.value,
                starts_at: startInput.value,
                ends_at: endInput.value,
                location: locationInput.value,
                latitude: latitudeInput.value,
                longitude: longitudeInput.value,
                description: descriptionInput.value,
            }).then((data) => {
                saveBtn.disabled = false;
                if (data.error) {
                    showError(data.error);
                    return;
                }
                modal.hide();
                calendar.refetchEvents();
            }).catch(() => {
                saveBtn.disabled = false;
                showError('Något gick fel. Försök igen.');
            });
        });

        deleteBtn.addEventListener('click', () => {
            if (!eventIdInput.value) return;
            deleteBtn.disabled = true;
            postToApi({ action: 'delete', event_id: eventIdInput.value }).then((data) => {
                deleteBtn.disabled = false;
                if (data.error) {
                    showError(data.error);
                    return;
                }
                modal.hide();
                calendar.refetchEvents();
            }).catch(() => {
                deleteBtn.disabled = false;
                showError('Något gick fel. Försök igen.');
            });
        });
    }

    // --- FullCalendar itself ---

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'sv',
        height: 'auto',
        editable: isLoggedIn,
        events: basePath + '/members/calendar_api.cgi',
        dateClick: isLoggedIn ? (info) => openCreateModal(info.date) : undefined,
        eventClick: isLoggedIn ? (info) => openEditModal(info.event) : (info) => showEventDetails(info.event),
        eventDrop: isLoggedIn ? (info) => {
            persistEventChange(info.event).catch(() => {
                info.revert();
                alert('Kunde inte flytta händelsen. Försök igen.');
            });
        } : undefined,
        eventResize: isLoggedIn ? (info) => {
            persistEventChange(info.event).catch(() => {
                info.revert();
                alert('Kunde inte ändra händelsen. Försök igen.');
            });
        } : undefined,
    });
    calendar.render();
})();
