// ---------------------------------------------------------------------------
// Atlas des workflows : les graphes d'un même scénario deviennent des onglets.
// Sans JS, ils restent empilés et tous lisibles.
// ---------------------------------------------------------------------------

let n = 0;

export function initOnglets() {
  for (const atlas of document.querySelectorAll('[data-gf-atlas]')) {
    const figures = [...atlas.querySelectorAll(':scope > figure.gf-graphe')];
    if (figures.length < 2) continue;
    n += 1;
    const liste = document.createElement('div');
    liste.className = 'gf-atlas__onglets';
    liste.setAttribute('role', 'tablist');
    liste.setAttribute('aria-label', 'Choisir un workflow');
    const onglets = figures.map((fig, i) => {
      const titre = fig.querySelector('.gf-graphe__titre span');
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'gf-atlas__onglet';
      b.id = `gf-onglet-${n}-${i}`;
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-controls', fig.id || (fig.id = `gf-panneau-${n}-${i}`));
      b.textContent = titre ? titre.textContent : `Workflow ${i + 1}`;
      fig.setAttribute('role', 'tabpanel');
      fig.setAttribute('aria-labelledby', b.id);
      liste.appendChild(b);
      return b;
    });
    const choisir = (i, focus = false) => {
      onglets.forEach((b, j) => {
        const actif = i === j;
        b.setAttribute('aria-selected', actif ? 'true' : 'false');
        b.tabIndex = actif ? 0 : -1;
        figures[j].hidden = !actif;
      });
      if (focus) onglets[i].focus();
    };
    onglets.forEach((b, i) => {
      b.addEventListener('click', () => choisir(i));
      b.addEventListener('keydown', (ev) => {
        if (ev.key === 'ArrowRight') { choisir((i + 1) % onglets.length, true); ev.preventDefault(); }
        if (ev.key === 'ArrowLeft') { choisir((i - 1 + onglets.length) % onglets.length, true); ev.preventDefault(); }
        if (ev.key === 'Home') { choisir(0, true); ev.preventDefault(); }
        if (ev.key === 'End') { choisir(onglets.length - 1, true); ev.preventDefault(); }
      });
    });
    figures[0].before(liste);
    atlas.classList.add('gf-atlas--actif');
    choisir(0);
  }
}
