<%inherit file="base.mako"/>
    <section id="hero">
        <video id="hero-video" muted loop playsinline preload="auto">
            <source src="${base_path}/static/video/background.mp4" type="video/mp4">
        </video>
        <div id="hero-video-tint" aria-hidden="true"></div>
        <div id="hero-content">
            <div class="hero-mark-block">
                <h1 class="hero-wordmark">iBlandbandet</h1>
                <p class="hero-citymark">Umeå</p>
            </div>
            <p class="subtitle">${subtitle}</p>
        </div>
        <div id="scroll-hint" aria-hidden="true"><i class="bi bi-chevron-down"></i></div>
    </section>
    <div id="hero-spacer" aria-hidden="true"></div>

    <section id="om-bandet" class="content-section">
        <div class="container">
            <h2>Om bandet</h2>
            <img src="${base_path}/static/img/saxes.webp" alt="Två saxofonister" class="section-photo section-photo--right">
            <p>
              <span class="lede">Sommaren 2023</span> bestämde sig två
              veteraner från <a href="https://snosvanget.se/">Umeås
              studentorkester Snösvänget</a> att de fortfarande
              saknade studentikosa upptåg (såsom att dricka öl och
              bröla brass) i sina liv, och bestämde sig helt sonika
              för att starta en ny orkester i storbandstappning med
              fokus på roliga upptåg och socialt umgänge — men denna
              gång anpassad för livet som trettioplussare, dvs
              jonglerandes det delikata livspusslet med heltidsarbete,
              småbarn, och allt annat som sorglösa studenter slipper
              bekymra sig om.
            </p>
            <p>
              Resultatet blev <b>iBlandbandet</b>, ett slags korplag
              för medelålderströtta musiker — de av oss som är för
              gamla för Snösvänget, för dåliga för Renhornen, men som
              fortfarande söker ett roligt musikaliskt sammanhang. Vi
              repar när andan faller på (i regel varje måndag), och
              spelar blandad musik av blandad kvalité. Ibland låter
              det rentav bra, och vi har nästan alltid roligt!
            </p>
        </div>
    </section>

    <section id="kalender" class="content-section alt">
        <div class="container">
            <h2>Kalender</h2>

            <div class="calendar-subscribe">
                <p class="mb-2">Prenumerera i din kalenderapp, så syns händelser automatiskt i din telefon:</p>
                <a href="${webcal_url}" class="btn btn-outline-primary btn-sm">Prenumerera</a>
                <div class="calendar-subscribe-url"><code>${feed_url}</code></div>
            </div>

            <div class="calendar-card">
                <div id="calendar" data-csrf-token="${csrf_token}"></div>
            </div>

% if member is None:
            <div id="calendar-event-details" class="calendar-event-details" hidden>
                <button type="button" class="btn-close float-end" id="calendarEventDetailsClose" aria-label="Stäng"></button>
                <h3 id="calendarEventDetailsTitle"></h3>
                <p id="calendarEventDetailsWhen" class="event-when"></p>
                <p id="calendarEventDetailsLocation" class="event-location" hidden></p>
                <p id="calendarEventDetailsDescription" hidden></p>
            </div>
% endif
        </div>
    </section>

    <section id="spela-med-oss" class="content-section">
      <div class="container">
        <h2>Spela med oss!</h2>

        <img src="${base_path}/static/img/guitar.webp" alt="Elgitarrist" class="section-photo section-photo--left">
        <p>
          <span class="lede">iBlandbandets ambition</span> är att vara
          en trygg, inkluderande plats där vi ger varandra tillfälle
          att utöva musik i grupp, utan krav på prestation eller
          regelbundet deltagande.
        </p>
        <p>
          Så spelar du brass, träblås, näsflöjt (eller t.o.m. något så
          exotiskt som trummor, piano eller gitarr), kan (eller vill
          lära dig) grunderna i notläsning, och känner att det skulle
          vara trevligt att putsa upp färdigheterna en gång i veckan?
          Hör av dig, vetja! Vi hittar en plats för de flesta
          instrument, och vi köper helhjärtat principerna att ju fler
          vi blir, desto roligare har vi och desto billigare blir
          fikat.
        </p>

      </div>
    </section>

    <section id="kontakt" class="content-section alt">
        <div class="container">
            <h2>Kontakt</h2>
            <p>
              Vill du berätta hur duktiga vi är, komma och spela med
              oss, eller bara svänga förbi för lite kaffe? Skriv till
              oss!
            </p>
            <p><i class="bi bi-envelope"></i> <a href="mailto:info@iblandbandet.se">info@iblandbandet.se</a></p>
        </div>
    </section>

    <footer>
        <p>&copy; 2026 iBlandbandet</p>
    </footer>

% if member is not None:
    <div class="modal fade" id="eventModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="eventModalTitle">Lägg till händelse</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Stäng"></button>
                </div>
                <div class="modal-body">
                    <div id="eventModalError" class="alert alert-danger" hidden></div>
                    <input type="hidden" id="eventId">
                    <div class="mb-3">
                        <label class="form-label" for="eventTitle">Titel</label>
                        <input class="form-control" id="eventTitle" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label" for="eventStart">Starttid</label>
                        <input class="form-control" type="datetime-local" id="eventStart" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label" for="eventEnd">Sluttid</label>
                        <input class="form-control" type="datetime-local" id="eventEnd">
                    </div>
                    <div class="mb-3 location-search">
                        <label class="form-label" for="eventLocation">Plats</label>
                        <input class="form-control" id="eventLocation" autocomplete="off" placeholder="Sök en plats...">
                        <ul id="eventLocationResults" class="location-search-results" hidden></ul>
                        <input type="hidden" id="eventLatitude">
                        <input type="hidden" id="eventLongitude">
                        <p class="location-attribution">
                            Platssökning: <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap-bidragsgivare</a>
                        </p>
                    </div>
                    <div class="mb-3">
                        <label class="form-label" for="eventDescription">Beskrivning</label>
                        <textarea class="form-control" id="eventDescription" rows="3"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-danger me-auto" id="eventDeleteBtn" hidden>Ta bort</button>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Avbryt</button>
                    <button type="button" class="btn btn-primary" id="eventSaveBtn">Spara</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
% endif
    <script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.15/index.global.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/core@6.1.15/locales/sv.global.min.js"></script>
    <script src="${base_path}/static/js/calendar.js"></script>
