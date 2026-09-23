// ---------------------------------------------------------------------------
// Infobulles du lexique.
//
// Chaque terme est d'abord un lien vers le lexique (fonctionne sans JS).
// Avec JS : survol ou focus → définition ; sur écran tactile, un premier
// appui ouvre la définition, un second suit le lien.
// ---------------------------------------------------------------------------

let bulle;
let ancre = null;
let minuterie;

function creerBulle() {
  bulle = document.createElement('div');
  bulle.className = 'gf-bulle';
  bulle.id = 'gf-bulle';
  bulle.setAttribute('role', 'tooltip');
  bulle.hidden = true;
  document.body.appendChild(bulle);
  bulle.addEventListener('mouseenter', () => clearTimeout(minuterie));
  bulle.addEventListener('mouseleave', () => cacher());
}

function placer(lien) {
  const r = lien.getBoundingClientRect();
  const marge = 12;
  bulle.style.left = '0px';
  bulle.style.top = '0px';
  const b = bulle.getBoundingClientRect();
  let x = window.scrollX + r.left + r.width / 2 - b.width / 2;
  x = Math.max(window.scrollX + marge, Math.min(x, window.scrollX + document.documentElement.clientWidth - b.width - marge));
  let y = window.scrollY + r.bottom + 8;
  if (r.bottom + b.height + 16 > window.innerHeight && r.top > b.height + 16) {
    y = window.scrollY + r.top - b.height - 8;
  }
  bulle.style.left = `${x}px`;
  bulle.style.top = `${y}px`;
}

function montrer(lien) {
  clearTimeout(minuterie);
  if (!bulle) creerBulle();
  ancre = lien;
  const terme = lien.dataset.terme || lien.textContent;
  const proprio = lien.dataset.proprio || '';
  bulle.innerHTML = '';
  const tete = document.createElement('p');
  tete.className = 'gf-bulle__tete';
  const t = document.createElement('span');
  t.className = 'gf-bulle__terme';
  t.textContent = terme;
  tete.appendChild(t);
  if (proprio) {
    const p = document.createElement('span');
    p.className = 'gf-bulle__proprio';
    p.textContent = proprio;
    tete.appendChild(p);
  }
  const def = document.createElement('p');
  def.textContent = lien.dataset.def || '';
  const plus = document.createElement('p');
  const a = document.createElement('a');
  a.href = lien.getAttribute('href');
  a.textContent = 'Voir dans le lexique →';
  plus.appendChild(a);
  bulle.append(tete, def, plus);
  bulle.hidden = false;
  lien.setAttribute('aria-describedby', 'gf-bulle');
  placer(lien);
}

function cacher(immediat = false) {
  clearTimeout(minuterie);
  const faire = () => {
    if (bulle) bulle.hidden = true;
    if (ancre) ancre.removeAttribute('aria-describedby');
    ancre = null;
  };
  if (immediat) faire();
  else minuterie = setTimeout(faire, 180);
}

export function initTermes() {
  const liens = document.querySelectorAll('a.gf-t[data-def], a.gf-boussole__terme[data-def]');
  if (!liens.length) return;
  const tactile = window.matchMedia('(hover: none)').matches;
  for (const lien of liens) {
    lien.addEventListener('mouseenter', () => montrer(lien));
    lien.addEventListener('mouseleave', () => cacher());
    lien.addEventListener('focus', () => montrer(lien));
    lien.addEventListener('blur', () => cacher());
    if (tactile) {
      lien.addEventListener('click', (ev) => {
        if (ancre !== lien || bulle.hidden) {
          ev.preventDefault();
          montrer(lien);
        }
      });
    }
  }
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') cacher(true);
  });
  document.addEventListener('click', (ev) => {
    if (bulle && !bulle.hidden && !ev.target.closest('.gf-bulle, a.gf-t, a.gf-boussole__terme')) cacher(true);
  });
  window.addEventListener('scroll', () => { if (ancre) placer(ancre); }, { passive: true });
}
