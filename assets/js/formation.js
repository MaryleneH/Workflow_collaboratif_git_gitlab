// ---------------------------------------------------------------------------
// Point d'entrée (module ES chargé par l'extension Quarto « formation »).
// Chaque module améliore un contenu déjà lisible sans JavaScript.
// ---------------------------------------------------------------------------
import { initGraphes } from './graphe.js';
import { initProgression } from './progression.js';
import { initTermes } from './termes.js';
import { initOnglets } from './onglets.js';
import { initRail } from './rail.js';
import { initReview } from './review.js';

document.documentElement.classList.add('gf-js');

// Le lien d'évitement doit être le premier élément focalisable de la page.
function placerEvitement() {
  const lien = document.querySelector('.gf-evitement');
  if (lien && document.body.firstElementChild !== lien) document.body.prepend(lien);
}

// Toute zone qui défile horizontalement doit être atteignable au clavier.
function zonesDefilantes() {
  for (const el of document.querySelectorAll('main pre, main .sourceCode')) {
    if (el.scrollWidth > el.clientWidth + 1 && !el.hasAttribute('tabindex')) el.tabIndex = 0;
  }
}

function demarrer() {
  const etapes = [
    ['évitement', placerEvitement],
    ['rail', initRail],
    ['onglets', initOnglets],
    ['graphes', initGraphes],
    ['termes', initTermes],
    ['review', initReview],
    ['progression', initProgression],
    ['zones défilantes', zonesDefilantes],
  ];
  for (const [nom, f] of etapes) {
    try {
      f();
    } catch (err) {
      console.error(`[formation] ${nom} :`, err);
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', demarrer);
} else {
  demarrer();
}
