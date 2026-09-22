// ---------------------------------------------------------------------------
// Graphe Git vivant
//
// Amélioration progressive d'une <figure data-gf-graphe> produite par
// l'extension Quarto. Sans JavaScript, la description textuelle reste lisible.
//
// Ce n'est PAS un simulateur Git : chaque étape déclare un état (commits
// visibles, références, HEAD) et le composant anime la transition entre deux
// états. Les animations portent du sens : une étiquette de branche qui glisse
// vers un nouveau commit, des commits recréés par un rebase, un remote qui
// apparaît.
//
// Grammaire : temps de gauche à droite ; en mode étroit, de bas en haut comme
// `git log --graph --oneline --decorate` (le plus récent en haut, étiquettes
// et messages à droite).
// ---------------------------------------------------------------------------

const NS = 'http://www.w3.org/2000/svg';
const LARGEUR_VERTICALE = 560; // en dessous : mode vertical « git log »

const G = {
  h: { dx: 76, r: 13, pas: 66, rang: 23, marge: 26, ecart: 8 },
  v: { dy: 44, r: 11, pas: 36, marge: 18 },
};
const HAUTEUR_ETIQUETTE = 18;

// Lua encode une table vide en {} : on normalise listes et dictionnaires.
const liste = (v) => (Array.isArray(v) ? v : []);
const dico = (v) => (v && typeof v === 'object' && !Array.isArray(v) ? v : {});

function normaliserMonde(m) {
  if (!m) return null;
  return { commits: liste(m.commits), refs: dico(m.refs), tags: dico(m.tags), head: m.head || null };
}

function el(nom, attrs = {}, parent) {
  const n = document.createElementNS(NS, nom);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (parent) parent.appendChild(n);
  return n;
}

const estDistante = (nom) => /^(origin|upstream)\//.test(nom);

function couleurRef(nom, donnees, commit) {
  const court = nom.replace(/^(origin|upstream)\//, '');
  const perso = donnees.couleurs[nom] || donnees.couleurs[court];
  if (perso) return perso;
  if (court === 'main' || court === 'master') return 'main';
  if (court === 'develop') return 'develop';
  if (/^release\//.test(court) || /^maintenance\//.test(court)) return 'release';
  if (/^hotfix\//.test(court)) return 'hotfix';
  return (commit && commit.couleur) || 'travail';
}

function couleurCommit(c) {
  if (c.couleur) return c.couleur;
  return c.y === 0 ? 'main' : 'travail';
}

const largeurTexte = (t) => Math.round(t.length * 6.9 + 14);

// Groupes d'étiquettes par commit. Un groupe = une référence, précédée de
// HEAD si HEAD pointe sur cette branche. HEAD détachée forme son propre groupe.
function groupes(monde, donnees) {
  const parCommit = new Map();
  const ajouter = (cible, g) => {
    if (!parCommit.has(cible)) parCommit.set(cible, []);
    parCommit.get(cible).push(g);
  };
  const refs = monde.refs;
  const head = monde.head;
  const headSurBranche = Boolean(head) && Object.prototype.hasOwnProperty.call(refs, head);
  if (head && !headSurBranche) {
    ajouter(head, [{ cle: 'r:HEAD', nom: 'HEAD', type: 'head' }]);
  }
  const noms = Object.keys(refs).sort((a, b) => {
    const rang = (n) => (n === head ? 0 : estDistante(n) ? 2 : 1);
    return rang(a) - rang(b) || a.localeCompare(b);
  });
  for (const nom of noms) {
    const item = {
      cle: 'r:' + nom,
      nom,
      type: estDistante(nom) ? 'distante' : 'branche',
      couleur: couleurRef(nom, donnees, donnees.commits[refs[nom]]),
    };
    ajouter(refs[nom], headSurBranche && nom === head
      ? [{ cle: 'r:HEAD', nom: 'HEAD', type: 'head', attache: true }, item]
      : [item]);
  }
  for (const [nom, cible] of Object.entries(monde.tags)) {
    ajouter(cible, [{ cle: 't:' + nom, nom, type: 'tag' }]);
  }
  for (const liste2 of parCommit.values()) {
    for (const g of liste2) g.largeur = g.reduce((s, it) => s + largeurTexte(it.nom), 0) + (g.length - 1) * 3;
  }
  return parCommit;
}

class Graphe {
  constructor(figure) {
    this.figure = figure;
    const script = figure.querySelector('script[data-gf-donnees]');
    this.donnees = JSON.parse(script.textContent);
    this.donnees.couleurs = dico(this.donnees.couleurs);
    this.commits = dico(this.donnees.commits);
    for (const c of Object.values(this.commits)) c.parents = liste(c.parents);
    this.etapes = liste(this.donnees.etapes).map((e) => ({
      ...e,
      estompes: liste(e.estompes),
      surligne: liste(e.surligne),
      local: normaliserMonde(e.local),
      distant: normaliserMonde(e.distant),
    }));
    this.index = 0;
    this.scene = figure.querySelector('[data-gf-scene]');
    this.legende = figure.querySelector('[data-gf-legende]');
    this.controles = figure.querySelector('[data-gf-controles]');
    this.aDistant = this.etapes.some((e) => e.distant);
    this.orientation = null;
    const xs = Object.values(this.commits).map((c) => c.x);
    this.xMin = Math.min(...xs, 0);
    this.xMax = Math.max(...xs, 0);
    this.lignes = [...new Set(Object.values(this.commits).map((c) => c.y))].sort((a, b) => a - b);
    this.construireControles();
    const alt = figure.querySelector('[data-gf-alt]');
    if (alt) alt.removeAttribute('open');
    this.observer = new ResizeObserver(() => this.adapter());
    this.observer.observe(figure);
    this.adapter();
  }

  // --- Contrôles ------------------------------------------------------------
  construireControles() {
    if (this.etapes.length < 2) return;
    const c = this.controles;
    c.innerHTML = '';
    const points = document.createElement('ol');
    points.className = 'gf-graphe__points';
    points.setAttribute('aria-label', 'Étapes du schéma');
    this.boutonsPoints = this.etapes.map((_, i) => {
      const li = document.createElement('li');
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'gf-graphe__point';
      b.textContent = String(i + 1);
      b.setAttribute('aria-label', `Étape ${i + 1} sur ${this.etapes.length}`);
      b.addEventListener('click', () => this.aller(i));
      li.appendChild(b);
      points.appendChild(li);
      return b;
    });
    const boutons = document.createElement('div');
    boutons.className = 'gf-graphe__boutons';
    this.prec = this.bouton('← Précédent', () => this.aller(this.index - 1));
    this.suiv = this.bouton('Suivant →', () => this.aller(this.index + 1));
    boutons.append(this.prec, this.suiv);
    c.append(points, boutons);
    c.hidden = false;
    this.figure.addEventListener('keydown', (ev) => {
      if (ev.target.closest('details, a, input, textarea')) return;
      if (ev.key === 'ArrowRight') { this.aller(this.index + 1); ev.preventDefault(); }
      if (ev.key === 'ArrowLeft') { this.aller(this.index - 1); ev.preventDefault(); }
    });
  }

  bouton(texte, action) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'gf-bouton gf-bouton--discret';
    b.textContent = texte;
    b.addEventListener('click', action);
    return b;
  }

  aller(i) {
    if (i < 0 || i >= this.etapes.length || i === this.index) return;
    this.index = i;
    this.dessiner(true);
  }

  adapter() {
    const largeur = this.figure.clientWidth;
    if (largeur === 0) return;
    const o = largeur < LARGEUR_VERTICALE ? 'v' : 'h';
    if (o !== this.orientation) {
      this.orientation = o;
      this.construireScene();
      this.dessiner(false);
    }
  }

  // --- Scène ----------------------------------------------------------------
  construireScene() {
    this.scene.innerHTML = '';
    this.panneaux = [];
    const mondes = this.aDistant ? ['local', 'distant'] : ['local'];
    for (const m of mondes) {
      const p = document.createElement('div');
      p.className = `gf-graphe__panneau gf-graphe__panneau--${m}`;
      if (this.aDistant) {
        const t = document.createElement('p');
        t.className = 'gf-graphe__panneau-titre';
        const icone = m === 'local'
          ? '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 8.5h18M9 8.5V20"/>'
          : '<rect x="4" y="4" width="16" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="16" height="6.5" rx="1.5"/>';
        t.innerHTML = `<svg class="gf-icone" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true">${icone}</svg>`;
        t.append(m === 'local' ? 'Votre dépôt local' : (this.donnees.nom_distant || 'GitLab (origin)'));
        p.appendChild(t);
      }
      const toile = document.createElement('div');
      toile.className = 'gf-graphe__toile';
      p.appendChild(toile);
      this.scene.appendChild(p);
      const svg = el('svg', { 'aria-hidden': 'true', focusable: 'false' }, toile);
      const gLiens = el('g', { class: 'gf-g-liens' }, svg);
      const gCommits = el('g', { class: 'gf-g-commits' }, svg);
      const gRefs = el('g', { class: 'gf-g-refs' }, svg);
      this.panneaux.push({ monde: m, svg, gLiens, gCommits, gRefs, noeuds: new Map(), liens: new Map(), refs: new Map() });
    }
    this.calculerDimensions();
  }

  // Place les groupes d'étiquettes en rangées sans chevauchement (horizontal).
  allouer(monde, xDe) {
    const parGroupe = groupes(monde, this.donnees);
    const visibles = new Set(monde.commits);
    const rangees = new Map(); // ligne -> [[x0, x1], ...] par rang
    const places = [];
    const cibles = [...parGroupe.keys()]
      .filter((id) => visibles.has(id) && this.commits[id])
      .sort((a, b) => this.commits[a].x - this.commits[b].x);
    for (const cible of cibles) {
      const ligne = this.commits[cible].y;
      if (!rangees.has(ligne)) rangees.set(ligne, []);
      const rangs = rangees.get(ligne);
      for (const groupe of parGroupe.get(cible)) {
        const cx = xDe(cible);
        const x0 = cx - groupe.largeur / 2;
        const x1 = cx + groupe.largeur / 2;
        let r = 0;
        while (rangs[r] && rangs[r].some(([a, b]) => x0 < b + G.h.ecart && x1 > a - G.h.ecart)) r += 1;
        if (!rangs[r]) rangs[r] = [];
        rangs[r].push([x0, x1]);
        places.push({ cible, groupe, rang: r, x0 });
      }
    }
    const rangsParLigne = new Map([...rangees].map(([l, rs]) => [l, rs.length]));
    return { places, rangsParLigne };
  }

  // Géométrie propre à chaque panneau (local, distant) : les colonnes (x)
  // sont communes, la hauteur dépend des étiquettes présentes dans ce monde.
  calculerDimensions() {
    const o = this.orientation;
    for (const p of this.panneaux) {
      p.pos = {};
      if (o === 'h') {
        const g = G.h;
        const xDe = (id) => g.marge + 40 + (this.commits[id].x - this.xMin) * g.dx;
        const rangsMax = new Map();
        for (const e of this.etapes) {
          const monde = e[p.monde];
          if (!monde) continue;
          for (const [l, n] of this.allouer(monde, xDe).rangsParLigne) {
            rangsMax.set(l, Math.max(rangsMax.get(l) || 0, n));
          }
        }
        const yLigne = new Map();
        const premiere = this.lignes[0];
        let y = g.marge + (rangsMax.get(premiere) || 0) * g.rang + g.r + 4;
        this.lignes.forEach((l, i) => {
          if (i > 0) {
            const prec = this.lignes[i - 1];
            y += g.pas + (i - 1 === 0 ? 0 : (rangsMax.get(prec) || 0) * g.rang);
          }
          yLigne.set(l, y);
        });
        const derniere = this.lignes[this.lignes.length - 1];
        const bas = this.lignes.length > 1 ? (rangsMax.get(derniere) || 0) * g.rang : 0;
        p.hauteur = y + g.r + bas + g.marge;
        p.largeur = 2 * (g.marge + 40) + (this.xMax - this.xMin) * g.dx;
        for (const id of Object.keys(this.commits)) {
          p.pos[id] = { x: xDe(id), y: yLigne.get(this.commits[id].y) };
        }
        p.xDe = xDe;
      } else {
        const g = G.v;
        const xs = new Map();
        this.lignes.forEach((l, i) => xs.set(l, g.marge + g.r + i * g.pas));
        p.xEtiquettes = g.marge + g.r * 2 + (this.lignes.length - 1) * g.pas + 14;
        for (const [id, c] of Object.entries(this.commits)) {
          p.pos[id] = { x: xs.get(c.y), y: g.marge + g.r + (this.xMax - c.x) * g.dy };
        }
        p.hauteur = (this.xMax - this.xMin) * g.dy + 2 * (g.marge + g.r);
        p.largeur = p.xEtiquettes + 380;
      }
      p.svg.setAttribute('viewBox', `0 0 ${p.largeur} ${p.hauteur}`);
      p.svg.setAttribute('width', p.largeur);
      p.svg.setAttribute('height', p.hauteur);
      p.svg.style.maxWidth = o === 'h' ? `${p.largeur}px` : 'none';
    }
  }

  chemin(p, parent, enfant) {
    const a = p.pos[parent];
    const b = p.pos[enfant];
    if (!a || !b) return '';
    if (this.orientation === 'h') {
      if (a.y === b.y) return `M${a.x},${a.y} L${b.x},${b.y}`;
      const mx = (b.x - a.x) * 0.55;
      return `M${a.x},${a.y} C${a.x + mx},${a.y} ${b.x - mx},${b.y} ${b.x},${b.y}`;
    }
    if (a.x === b.x) return `M${a.x},${a.y} L${b.x},${b.y}`;
    const my = (a.y - b.y) * 0.55;
    return `M${a.x},${a.y} C${a.x},${a.y - my} ${b.x},${b.y + my} ${b.x},${b.y}`;
  }

  dessiner(anime) {
    const etape = this.etapes[this.index];
    for (const p of this.panneaux) {
      this.dessinerMonde(p, etape[p.monde] || normaliserMonde({}), etape, !anime);
    }
    this.majLegende(etape);
    this.majControles();
  }

  apparaitre(noeud, fin, debut) {
    noeud.style.opacity = '0';
    if (debut) noeud.style.transform = debut;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      noeud.style.opacity = '';
      if (fin) noeud.style.transform = fin;
    }));
  }

  dessinerMonde(p, monde, etape, figer) {
    const visibles = new Set(monde.commits);
    const estompes = new Set(etape.estompes);
    const surligne = new Set(etape.surligne);
    const o = this.orientation;
    const r = G[o].r;

    // Liens enfant → parent (sans flèche : un commit connaît ses parents)
    const liensVus = new Set();
    for (const id of visibles) {
      const c = this.commits[id];
      if (!c) continue;
      for (const par of c.parents) {
        if (!visibles.has(par)) continue;
        const cle = par + '>' + id;
        liensVus.add(cle);
        let path = p.liens.get(cle);
        if (!path) {
          path = el('path', {}, p.gLiens);
          p.liens.set(cle, path);
          if (!figer) this.apparaitre(path);
        }
        path.setAttribute('d', this.chemin(p, par, id));
        path.setAttribute('class', `gf-g-lien gf-c-${couleurCommit(c)}${estompes.has(id) ? ' gf-g-lien--estompe' : ''}`);
      }
    }
    for (const [cle, path] of p.liens) {
      if (!liensVus.has(cle)) { path.remove(); p.liens.delete(cle); }
    }

    // Commits
    for (const id of visibles) {
      const c = this.commits[id];
      if (!c) continue;
      const pos = p.pos[id];
      let g = p.noeuds.get(id);
      const nouveau = !g;
      if (!g) {
        g = el('g', {}, p.gCommits);
        el('circle', { class: 'gf-g-halo', r: r + 5 }, g);
        el('circle', { class: 'gf-g-disque', r }, g);
        const t = el('text', { class: 'gf-g-id', x: 0, y: 0 }, g);
        t.textContent = c.label || id;
        if (c.msg) el('title', {}, g).textContent = `${c.label || id} · ${c.msg}`;
        p.noeuds.set(id, g);
      }
      let cls = `gf-g-commit gf-c-${couleurCommit(c)}`;
      if (estompes.has(id)) cls += ' gf-g-commit--estompe';
      if (surligne.has(id)) cls += ' gf-g-commit--surligne';
      g.setAttribute('class', cls);
      const fin = `translate(${pos.x}px, ${pos.y}px)`;
      if (nouveau && !figer) this.apparaitre(g, fin, `${fin} scale(.5)`);
      else g.style.transform = fin;
      let msg = g.querySelector('.gf-g-msg');
      if (o === 'v' && c.msg) {
        if (!msg) msg = el('text', { class: 'gf-g-msg', y: 0 }, g);
        msg.textContent = c.msg;
      } else if (msg) {
        msg.remove();
      }
    }
    for (const [id, g] of p.noeuds) {
      if (!visibles.has(id)) { g.remove(); p.noeuds.delete(id); }
    }

    // Références
    const vues = new Set();
    if (o === 'h') {
      const { places } = this.allouer(monde, p.xDe);
      const premiere = this.lignes[0];
      for (const { cible, groupe, rang, x0 } of places) {
        const base = p.pos[cible];
        const enHaut = this.commits[cible].y === premiere;
        const y = enHaut
          ? base.y - r - 6 - (rang + 1) * G.h.rang + (G.h.rang - HAUTEUR_ETIQUETTE)
          : base.y + r + 6 + rang * G.h.rang;
        let x = x0;
        groupe.forEach((it, i) => {
          vues.add(it.cle);
          const w = largeurTexte(it.nom);
          // Trait de rappel quand l'étiquette est décalée vers le haut/bas
          const attache = i === groupe.length - 1 && rang > 0
            ? { x: base.x - x, y1: enHaut ? HAUTEUR_ETIQUETTE : 0, y2: enHaut ? base.y - r - y : base.y + r - y }
            : null;
          this.dessinerRef(p, it, x, y, w, figer, attache);
          x += w + 3;
        });
      }
    } else {
      const parGroupe = groupes(monde, this.donnees);
      for (const [cible, liste2] of parGroupe) {
        if (!visibles.has(cible) || !p.pos[cible]) continue;
        let x = p.xEtiquettes;
        const y = p.pos[cible].y - HAUTEUR_ETIQUETTE / 2;
        for (const groupe of liste2) {
          for (const it of groupe) {
            vues.add(it.cle);
            const w = largeurTexte(it.nom);
            this.dessinerRef(p, it, x, y, w, figer, null);
            x += w + 3;
          }
          x += 4;
        }
        const g = p.noeuds.get(cible);
        const msg = g && g.querySelector('.gf-g-msg');
        if (msg) msg.setAttribute('x', x + 4 - p.pos[cible].x);
      }
      for (const [id, g] of p.noeuds) {
        const msg = g.querySelector('.gf-g-msg');
        if (msg && !parGroupe.has(id)) msg.setAttribute('x', p.xEtiquettes - p.pos[id].x);
      }
    }
    for (const [cle, g] of p.refs) {
      if (!vues.has(cle)) { g.remove(); p.refs.delete(cle); }
    }
  }

  dessinerRef(p, it, x, y, w, figer, attache) {
    let g = p.refs.get(it.cle);
    const nouveau = !g;
    if (!g) {
      g = el('g', {}, p.gRefs);
      el('line', { class: 'gf-g-attache' }, g);
      if (it.type === 'tag') el('path', {}, g);
      else el('rect', { rx: 4, ry: 4, height: HAUTEUR_ETIQUETTE }, g);
      el('text', { x: 7, y: HAUTEUR_ETIQUETTE / 2 }, g).textContent = it.nom;
      p.refs.set(it.cle, g);
    }
    g.setAttribute('class', `gf-g-ref gf-g-ref--${it.type}${it.couleur ? ` gf-c-${it.couleur}` : ''}`);
    if (it.type === 'tag') {
      g.querySelector('path').setAttribute('d', `M0,0 H${w} V${HAUTEUR_ETIQUETTE} H0 L-6,${HAUTEUR_ETIQUETTE / 2} Z`);
    } else {
      g.querySelector('rect').setAttribute('width', w);
    }
    const ligne = g.querySelector('line');
    if (attache) {
      ligne.setAttribute('x1', attache.x);
      ligne.setAttribute('x2', attache.x);
      ligne.setAttribute('y1', attache.y1);
      ligne.setAttribute('y2', attache.y2);
      ligne.style.display = '';
    } else {
      ligne.style.display = 'none';
    }
    const fin = `translate(${x}px, ${y}px)`;
    if (nouveau && !figer) this.apparaitre(g, fin, `translate(${x}px, ${y - 8}px)`);
    else g.style.transform = fin;
  }

  majLegende(etape) {
    this.legende.innerHTML = '';
    if (etape.texte) {
      const d = document.createElement('div');
      d.className = 'gf-graphe__texte';
      d.innerHTML = etape.texte; // HTML produit au rendu à partir du YAML du site
      this.legende.appendChild(d);
    }
    if (etape.commande) {
      const pre = document.createElement('pre');
      pre.className = 'gf-graphe__cmd';
      const code = document.createElement('code');
      code.textContent = etape.commande;
      pre.appendChild(code);
      this.legende.appendChild(pre);
    }
  }

  majControles() {
    if (!this.prec) return;
    this.prec.disabled = this.index === 0;
    this.suiv.disabled = this.index === this.etapes.length - 1;
    this.boutonsPoints.forEach((b, i) => {
      if (i === this.index) b.setAttribute('aria-current', 'step');
      else b.removeAttribute('aria-current');
    });
  }
}

export function initGraphes(racine = document) {
  for (const fig of racine.querySelectorAll('figure[data-gf-graphe]')) {
    if (fig.dataset.gfPret) continue;
    try {
      fig._graphe = new Graphe(fig);
      fig.dataset.gfPret = '1';
    } catch (err) {
      // En cas d'erreur, la description textuelle reste affichée.
      console.error('[graphe]', err);
      const alt = fig.querySelector('[data-gf-alt]');
      if (alt) alt.setAttribute('open', '');
    }
  }
}
