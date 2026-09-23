// ---------------------------------------------------------------------------
// Contrôles automatiques du site rendu.
//
//   node verifier-site.mjs ../_site
//
// Pour chaque page HTML du site :
//   1. aucune erreur JavaScript ni erreur de console ;
//   2. toutes les ressources chargées (CSS, JS, images) répondent 200 ;
//   3. tous les liens internes pointent vers une page existante, et toutes les
//      ancres (#id) existent dans la page cible ;
//   4. aucun débordement horizontal global à 390, 1280 et 1920 px ;
//   5. audit d'accessibilité axe-core (WCAG 2.1 A/AA) : aucune violation
//      « critical » ou « serious » ;
//   6. sans JavaScript : le contenu principal reste lisible (graphes décrits
//      textuellement, rail présent).
// Plus quelques contrôles ciblés : lien d'évitement, clavier sur le graphe,
// profil stagiaire sans contenu formateur.
//
// Code de sortie 1 si un contrôle échoue. Rapport : rapports/rapport.md
// ---------------------------------------------------------------------------
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const AXE = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const RACINE = path.resolve(process.argv[2] || '../_site');
const LARGEURS = [390, 1280, 1920];
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.woff2': 'font/woff2', '.txt': 'text/plain', '.xml': 'application/xml',
};

// Chemin de base du site publié (ex. /Workflow_collaboratif_git_gitlab/), lu dans
// site-url : la page 404 utilise des liens absolus qui en dépendent.
const config = fs.readFileSync(path.resolve(RACINE, '..', '_quarto.yml'), 'utf8');
const siteUrl = (config.match(/site-url:\s*"?([^"\n]+)"?/) || [])[1] || '';
const BASE_CHEMIN = siteUrl ? new URL(siteUrl).pathname : '/';
const sansBase = (u) => (BASE_CHEMIN !== '/' && u.startsWith(BASE_CHEMIN) ? '/' + u.slice(BASE_CHEMIN.length) : u);

if (!fs.existsSync(path.join(RACINE, 'index.html'))) {
  console.error(`Site introuvable : ${RACINE}/index.html (lancez d'abord quarto render)`);
  process.exit(2);
}

// Serveur statique minimal (aucune dépendance)
const serveur = http.createServer((req, res) => {
  const url = sansBase(decodeURIComponent(new URL(req.url, 'http://x').pathname));
  let fichier = path.join(RACINE, url);
  if (!fichier.startsWith(RACINE)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(fichier) && fs.statSync(fichier).isDirectory()) fichier = path.join(fichier, 'index.html');
  if (!fs.existsSync(fichier)) { res.writeHead(404); return res.end('404'); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(fichier)] || 'application/octet-stream' });
  fs.createReadStream(fichier).pipe(res);
});
await new Promise((ok) => serveur.listen(0, '127.0.0.1', ok));
const BASE = `http://127.0.0.1:${serveur.address().port}`;

function pagesHtml(dir, base = '') {
  const r = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === 'site_libs') continue;
    const rel = path.posix.join(base, e.name);
    if (e.isDirectory()) r.push(...pagesHtml(path.join(dir, e.name), rel));
    else if (e.name.endsWith('.html')) r.push(rel);
  }
  return r.sort();
}

const pages = pagesHtml(RACINE);
const echecs = [];
const avert = [];
const echouer = (page, msg) => echecs.push(`${page} : ${msg}`);

const navigateur = await chromium.launch();

// Index des identifiants par page (pour vérifier les ancres)
const ids = new Map();
for (const p of pages) {
  const html = fs.readFileSync(path.join(RACINE, p), 'utf8');
  ids.set(p, new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1])));
}

for (const p of pages) {
  const url = `${BASE}/${p}`;
  // ---- 1-5 : avec JavaScript, à plusieurs largeurs ----------------------------
  for (const largeur of LARGEURS) {
    const ctx = await navigateur.newContext({ viewport: { width: largeur, height: 900 } });
    const page = await ctx.newPage();
    const erreurs = [];
    page.on('pageerror', (e) => erreurs.push(`JS : ${e.message}`));
    page.on('console', (m) => { if (m.type() === 'error') erreurs.push(`console : ${m.text()}`); });
    page.on('response', (r) => {
      if (r.url().startsWith(BASE) && r.status() >= 400) erreurs.push(`ressource ${r.status()} : ${r.url().slice(BASE.length)}`);
    });
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(150);
    const debord = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    if (debord > 1) echouer(p, `débordement horizontal de ${debord}px à ${largeur}px`);
    for (const e of erreurs) echouer(p, `${e} (${largeur}px)`);

    if (largeur === 1280) {
      // Liens internes et ancres
      // Liens résolus par le navigateur (Quarto réécrit certains liens en absolu).
      const liens = await page.$$eval('a[href]', (as) => as.map((a) => ({ brut: a.getAttribute('href'), url: a.href })));
      // Identifiants présents dans le DOM vivant (certains sont créés par Quarto au chargement)
      const idsVivants = new Set(await page.$$eval('[id]', (els) => els.map((e) => e.id)));
      for (const { brut, url: absolu } of liens) {
        if (!absolu.startsWith(BASE + '/')) continue; // lien externe, mailto, javascript…
        const u = new URL(absolu);
        let cible = sansBase(decodeURIComponent(u.pathname)).slice(1);
        if (cible === '' || cible.endsWith('/')) cible += 'index.html';
        const ancre = u.hash ? decodeURIComponent(u.hash.slice(1)) : '';
        if (!ids.has(cible)) {
          if (!fs.existsSync(path.join(RACINE, cible))) echouer(p, `lien cassé → ${brut}`);
          continue;
        }
        const idsCible = cible === p ? new Set([...ids.get(cible), ...idsVivants]) : ids.get(cible);
        if (ancre && !idsCible.has(ancre)) echouer(p, `ancre absente → ${brut}`);
      }
      // Accessibilité (axe-core)
      await page.addScriptTag({ content: AXE });
      const res = await page.evaluate(async () => {
        // eslint-disable-next-line no-undef
        const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } });
        return r.violations.map((v) => ({ id: v.id, impact: v.impact, n: v.nodes.length, cible: v.nodes[0] && v.nodes[0].target.join(' ') }));
      });
      for (const v of res) {
        const msg = `axe ${v.impact} ${v.id} (${v.n} nœud(s), ex. ${v.cible})`;
        if (v.impact === 'critical' || v.impact === 'serious') echouer(p, msg);
        else avert.push(`${p} : ${msg}`);
      }
      // Lien d'évitement en premier focus
      await page.keyboard.press('Tab');
      const premier = await page.evaluate(() => document.activeElement && document.activeElement.className);
      if (!String(premier).includes('gf-evitement')) echouer(p, `le premier Tab ne cible pas le lien d'évitement (${premier})`);
    }
    await ctx.close();
  }

  // ---- 6 : sans JavaScript ------------------------------------------------------
  const ctx = await navigateur.newContext({ javaScriptEnabled: false, viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(url, { waitUntil: 'load' });
  const sansJs = await page.evaluate(() => ({
    main: Boolean(document.querySelector('main#contenu')),
    texte: (document.querySelector('main#contenu') || document.body).innerText.length,
    graphes: document.querySelectorAll('figure[data-gf-graphe]').length,
    altOuverts: document.querySelectorAll('figure[data-gf-graphe] details[open]').length,
  }));
  if (!sansJs.main) echouer(p, 'sans JS : <main id="contenu"> absent');
  if (sansJs.texte < 200) echouer(p, `sans JS : contenu principal quasi vide (${sansJs.texte} caractères)`);
  if (sansJs.graphes !== sansJs.altOuverts) echouer(p, `sans JS : ${sansJs.graphes - sansJs.altOuverts} graphe(s) sans description textuelle visible`);
  await ctx.close();
}

// ---- Contrôles ciblés -------------------------------------------------------------
{
  const ctx = await navigateur.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(`${BASE}/index.html`, { waitUntil: 'networkidle' });
  const graphe = page.locator('figure[data-gf-graphe]').first();
  if (await graphe.count()) {
    const suivant = graphe.getByRole('button', { name: /Suivant/ });
    await suivant.focus();
    await page.keyboard.press('Enter');
    const courant = await graphe.locator('[aria-current="step"]').textContent();
    if (courant.trim() !== '2') echouer('index.html', `le graphe ne répond pas au clavier (étape ${courant})`);
  }
  await ctx.close();
}
// Profil stagiaire : aucune trace des blocs réservés au formateur
for (const p of pages) {
  const html = fs.readFileSync(path.join(RACINE, p), 'utf8');
  if (html.includes('gf-formateur') && !RACINE.includes('formateur')) echouer(p, 'contenu formateur présent dans le site stagiaire');
}

await navigateur.close();
serveur.close();

// ---- Rapport ----------------------------------------------------------------------
fs.mkdirSync('rapports', { recursive: true });
const lignes = [
  `# Contrôles du site (${pages.length} pages, largeurs ${LARGEURS.join(', ')} px)`,
  '',
  `## Échecs (${echecs.length})`,
  ...echecs.map((e) => `- ${e}`),
  '',
  `## Avertissements (${avert.length})`,
  ...avert.map((e) => `- ${e}`),
];
fs.writeFileSync('rapports/rapport.md', lignes.join('\n') + '\n');
console.log(lignes.slice(0, 3 + echecs.length).join('\n'));
console.log(`\n${avert.length} avertissement(s) mineur(s) : voir tests/rapports/rapport.md`);
process.exit(echecs.length ? 1 : 0);
