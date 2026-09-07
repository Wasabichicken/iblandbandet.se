const header   = document.getElementById('header');
const sidebar  = document.getElementById('sidebar');
const overlay  = document.getElementById('overlay');
const hamburger    = document.getElementById('hamburger');
const sidebarClose = document.getElementById('sidebar-close');
const hero = document.getElementById('hero');

if (hero) {
    const heroVideo = document.getElementById('hero-video');
    const allowMotion = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    window.addEventListener('scroll', () => {
        if (window.scrollY > hero.offsetHeight * 0.6) {
            header.classList.add('visible');
        } else {
            header.classList.remove('visible');
        }

        if (heroVideo && allowMotion) {
            if (window.scrollY > window.innerHeight) {
                heroVideo.pause();
            } else if (heroVideo.paused) {
                heroVideo.play().catch(() => {});
            }
        }
    });

    if (heroVideo && allowMotion) {
        heroVideo.play().catch(() => {});
    }
} else {
    // No hero to scroll past on this page (e.g. register/profile) - show the header title right away.
    header.classList.add('visible');
}

function openSidebar() {
    sidebar.classList.add('open');
    sidebar.setAttribute('aria-hidden', 'false');
    overlay.classList.add('active');
    sidebarClose.focus();
}

function closeSidebar() {
    sidebar.classList.remove('open');
    sidebar.setAttribute('aria-hidden', 'true');
    overlay.classList.remove('active');
    hamburger.focus();
}

hamburger.addEventListener('click', openSidebar);
sidebarClose.addEventListener('click', closeSidebar);
overlay.addEventListener('click', closeSidebar);

document.querySelectorAll('.sidebar-link').forEach(link => {
    link.addEventListener('click', closeSidebar);
});

document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && sidebar.classList.contains('open')) closeSidebar();
});

if (sidebar.dataset.openOnLoad) openSidebar();
