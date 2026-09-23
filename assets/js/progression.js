// ---------------------------------------------------------------------------
// Progression personnelle (navigateur uniquement).
//
// Missions et étapes terminées sont mémorisées dans le localStorage de CE
// navigateur : c'est un confort, jamais une dépendance. Si le stockage est
// indisponible (navigation privée, politique d'entreprise), le site
// fonctionne à l'identique, simplement sans mémoire.
// ---------------------------------------------------------------------------

const CLE = 'git-a-plusieurs:progression:v1';

function lire() {
  try {
    const brut = window.localStorage.getItem(CLE);
    const d = brut ? JSON.parse(brut) : {};
    return { etapes: d.etapes || {}, missions: d.missions || {} };
  } catch {
    return { etapes: {}, missions: {} };
  }
}

function ecrire(etat) {
  try {
    window.localStorage.setItem(CLE, JSON.stringify(etat));
    return true;
  } catch {
    return false;
  }
}

function stockageDisponible() {
  try {
    const t = '__gf_test__';
    window.localStorage.setItem(t, t);
    window.localStorage.removeItem(t);
    return true;
  } catch {
    return false;
  }
}

let etat = lire();

function basculer(bouton, fait, libelleFait, libelleAFaire) {
  bouton.setAttribute('aria-pressed', fait ? 'true' : 'false');
  const span = bouton.querySelector('span');
  if (span) span.textContent = fait ? libelleFait : libelleAFaire;
}

function majRail() {
  const noeuds = document.querySelectorAll('.gf-rail .gf-noeud[data-etape], .gf-carte__etape[data-etape]');
  let faites = 0;
  const ids = new Set();
  for (const n of noeuds) {
    const id = n.dataset.etape;
    const fait = Boolean(etat.etapes[id]);
    n.classList.toggle('gf-noeud--fait', fait && n.classList.contains('gf-noeud'));
    n.classList.toggle('gf-carte__etape--faite', fait && n.classList.contains('gf-carte__etape'));
    const lib = n.querySelector('[data-gf-etat]');
    if (lib) lib.textContent = fait ? ' (terminée)' : '';
    if (n.classList.contains('gf-noeud')) {
      ids.add(id);
      if (fait) faites += 1;
    }
  }
  const av = document.querySelector('[data-gf-avancement]');
  if (av && ids.size) {
    av.textContent = `${faites} / ${ids.size}`;
    av.hidden = false;
    av.setAttribute('aria-label', `${faites} étapes terminées sur ${ids.size}`);
  }
}

function majBoussole() {
  const b = document.querySelector('[data-gf-boussole]');
  if (!b) return;
  const termes = b.querySelectorAll('.gf-boussole__terme');
  let compris = 0;
  for (const t of termes) {
    const ok = Boolean(etat.etapes[t.dataset.etape]);
    t.classList.toggle('gf-boussole__terme--compris', ok);
    if (ok) compris += 1;
  }
  const compteur = b.querySelector('[data-gf-boussole-compteur]');
  if (compteur) {
    compteur.hidden = false;
    compteur.textContent = compris === 0
      ? `Aucun des ${termes.length} termes n'est encore travaillé dans votre parcours.`
      : `${compris} terme${compris > 1 ? 's' : ''} sur ${termes.length} travaillé${compris > 1 ? 's' : ''} dans votre parcours.`;
  }
}

function majReprendre() {
  const lien = document.querySelector('[data-gf-reprendre]');
  if (!lien) return;
  const noeuds = [...document.querySelectorAll('.gf-carte__etape[data-etape]')];
  const prochaine = noeuds.find((n) => !etat.etapes[n.dataset.etape]);
  const dejaCommence = noeuds.some((n) => etat.etapes[n.dataset.etape]);
  if (!dejaCommence || !prochaine) return;
  const a = prochaine.querySelector('a');
  const num = prochaine.querySelector('.gf-carte__num');
  lien.href = a.getAttribute('href');
  lien.querySelector('span').textContent = `Reprendre à ${num ? num.textContent : 'la suite'}`;
  lien.hidden = false;
}

export function initProgression() {
  const dispo = stockageDisponible();

  for (const b of document.querySelectorAll('[data-gf-fait]')) {
    if (!dispo) continue;
    const id = b.dataset.gfFait;
    const section = b.closest('.gf-mission');
    const maj = () => {
      const fait = Boolean(etat.missions[id]);
      basculer(b, fait, 'Mission terminée ✓', 'Mission terminée');
      if (section) section.classList.toggle('gf-mission--faite', fait);
    };
    b.hidden = false;
    maj();
    b.addEventListener('click', () => {
      etat = lire();
      if (etat.missions[id]) delete etat.missions[id];
      else etat.missions[id] = Date.now();
      ecrire(etat);
      maj();
    });
  }

  for (const b of document.querySelectorAll('[data-gf-etape-faite]')) {
    if (!dispo) continue;
    const id = b.dataset.gfEtapeFaite;
    const maj = () => basculer(b, Boolean(etat.etapes[id]), 'Étape terminée ✓', 'Marquer l\'étape comme terminée');
    b.hidden = false;
    maj();
    b.addEventListener('click', () => {
      etat = lire();
      if (etat.etapes[id]) delete etat.etapes[id];
      else etat.etapes[id] = Date.now();
      ecrire(etat);
      maj();
      majRail();
    });
  }

  const reset = document.querySelector('[data-gf-reinitialiser]');
  if (reset && dispo) {
    reset.hidden = false;
    reset.addEventListener('click', () => {
      etat = { etapes: {}, missions: {} };
      ecrire(etat);
      majRail();
      majBoussole();
    });
  }

  majRail();
  majBoussole();
  majReprendre();
}
