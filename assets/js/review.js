// ---------------------------------------------------------------------------
// Review guidée : on cherche d'abord, puis on affiche les annotations.
// Sans JS, les marqueurs sont visibles et la liste des points reste repliée.
// ---------------------------------------------------------------------------

export function initReview() {
  for (const fig of document.querySelectorAll('[data-gf-review]')) {
    const bouton = fig.querySelector('[data-gf-bascule]');
    if (!bouton) continue;
    bouton.hidden = false;
    const libelle = bouton.querySelector('span');
    bouton.addEventListener('click', () => {
      const actif = fig.classList.toggle('gf-review--annotee');
      bouton.setAttribute('aria-pressed', actif ? 'true' : 'false');
      libelle.textContent = actif ? 'Masquer les annotations' : 'Afficher les annotations';
    });
    // Un clic sur un marqueur ouvre la liste des points.
    fig.addEventListener('click', (ev) => {
      if (ev.target.closest('.gf-diff__marque')) {
        const d = fig.querySelector('.gf-review__problemes');
        if (d) d.setAttribute('open', '');
      }
    });
  }
}
