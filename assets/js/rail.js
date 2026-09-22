// ---------------------------------------------------------------------------
// Rail du parcours et « Sur cette page ».
// - Écran large : le rail est toujours déplié.
// - Écran étroit : il se replie en une barre « E3 / 11 · … » que l'on ouvre.
// - « Sur cette page » suit la lecture (IntersectionObserver).
// ---------------------------------------------------------------------------

const LARGE = window.matchMedia('(min-width: 64rem)');

function adapterRail() {
  const d = document.querySelector('[data-gf-rail]');
  if (!d) return;
  if (LARGE.matches) d.setAttribute('open', '');
  else d.removeAttribute('open');
}

function suivreLecture() {
  const liens = [...document.querySelectorAll('.gf-anatomie a[href^="#"]')];
  if (!liens.length || !('IntersectionObserver' in window)) return;
  const cibles = liens
    .map((a) => document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1))))
    .filter(Boolean);
  const visibles = new Set();
  const maj = () => {
    let actif = null;
    for (const c of cibles) {
      if (visibles.has(c)) { actif = c; break; }
    }
    if (!actif) return;
    for (const a of liens) {
      const courant = a.getAttribute('href').slice(1) === actif.id;
      if (courant) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    }
  };
  const obs = new IntersectionObserver((entrees) => {
    for (const e of entrees) {
      if (e.isIntersecting) visibles.add(e.target);
      else visibles.delete(e.target);
    }
    maj();
  }, { rootMargin: '-15% 0px -70% 0px' });
  cibles.forEach((c) => obs.observe(c));
}

export function initRail() {
  adapterRail();
  LARGE.addEventListener('change', adapterRail);
  // Un lien du rail choisi sur mobile referme le panneau.
  const d = document.querySelector('[data-gf-rail]');
  if (d) {
    d.addEventListener('click', (ev) => {
      if (!LARGE.matches && ev.target.closest('a')) d.removeAttribute('open');
    });
  }
  suivreLecture();
}
