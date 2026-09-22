-- Représentations visuelles de Git : graphe vivant, atlas des workflows,
-- pipeline CI, review guidée, commandes et niveau de risque, termes du
-- lexique, phrase-boussole, carte du parcours, équipe.
local O = dofile(quarto.utils.resolve_path('lib/outils.lua'))
local D = dofile(quarto.utils.resolve_path('lib/donnees.lua'))
local I = dofile(quarto.utils.resolve_path('lib/icones.lua'))
local N = dofile(quarto.utils.resolve_path('lib/navigation.lua'))

local M = {}

local function attr(el, nom, defaut)
  local v = el.attributes and el.attributes[nom]
  if v == nil or v == '' then return defaut end
  return v
end

-- ---------------------------------------------------------------------------
-- Graphe vivant
-- ---------------------------------------------------------------------------

-- Ordonne les références : branches locales, branches distantes, tags.
local function refs_triees(refs)
  local r = {}
  for nom, cible in pairs(refs or {}) do r[#r + 1] = { nom = O.texte(nom), cible = O.texte(cible) } end
  table.sort(r, function(a, b)
    local function rang(n)
      if n:match('^origin/') or n:match('^upstream/') then return 2 end
      return 1
    end
    if rang(a.nom) ~= rang(b.nom) then return rang(a.nom) < rang(b.nom) end
    return a.nom < b.nom
  end)
  return r
end

local function decrire_monde(nom, monde, commits)
  if not monde then return nil end
  local morceaux = {}
  for _, ref in ipairs(refs_triees(monde.refs)) do
    morceaux[#morceaux + 1] = ref.nom .. ' → ' .. ref.cible
  end
  for tag, cible in pairs(monde.tags or {}) do
    morceaux[#morceaux + 1] = 'tag ' .. O.texte(tag) .. ' → ' .. O.texte(cible)
  end
  local head = monde.head and O.texte(monde.head)
  if head then
    if (monde.refs or {})[head] or (monde.refs or {})[monde.head] then
      morceaux[#morceaux + 1] = 'HEAD → ' .. head
    else
      morceaux[#morceaux + 1] = 'HEAD détachée sur ' .. head
    end
  end
  local liste = {}
  for _, c in ipairs(monde.commits or {}) do liste[#liste + 1] = O.texte(c) end
  local txt = nom .. ' : commits ' .. table.concat(liste, ', ')
  if #morceaux > 0 then txt = txt .. ' ; ' .. table.concat(morceaux, ', ') end
  return txt .. '.'
end

local function alt_texte(sc)
  local h = { '<ol class="gf-graphe__alt-liste">' }
  for i, e in ipairs(sc.etapes or {}) do
    local mondes = {}
    if e['local'] or e.distant then
      mondes[#mondes + 1] = decrire_monde('Votre dépôt', e['local'], sc.commits)
      mondes[#mondes + 1] = decrire_monde(O.texte(sc.nom_distant or 'GitLab (origin)'), e.distant, sc.commits)
    else
      mondes[#mondes + 1] = decrire_monde('Dépôt', e, sc.commits)
    end
    h[#h + 1] = '<li><p class="gf-graphe__alt-texte">' .. (e.texte or '') .. '</p>'
    if e.commande then
      h[#h + 1] = '<pre class="gf-graphe__alt-commande"><code>' .. O.esc(O.texte(e.commande)) .. '</code></pre>'
    end
    local etats = {}
    for _, m in ipairs(mondes) do if m then etats[#etats + 1] = O.esc(m) end end
    if #etats > 0 then
      h[#h + 1] = '<p class="gf-graphe__alt-etat">' .. table.concat(etats, '<br>') .. '</p>'
    end
    h[#h + 1] = '</li>'
  end
  h[#h + 1] = '</ol>'
  return table.concat(h, '\n')
end

-- Rend un scénario YAML (assets/data/scenarios/<id>.yml) en figure interactive.
function M.graphe(div)
  local id = attr(div, 'scenario')
  if not id then
    O.avertir('graphe sans attribut scenario dans ' .. O.fichier_courant())
    return {}
  end
  local sc = D.lire('scenarios/' .. id .. '.yml')
  if not sc.etapes then return {} end
  -- Validation : toute référence doit désigner un commit déclaré et visible.
  -- (Piège YAML : un identifiant N, Y, on, off… est lu comme un booléen.)
  local connus = {}
  for cid, c in pairs(sc.commits or {}) do
    connus[O.texte(cid)] = true
    for _, par in ipairs(c.parents or {}) do
      if type(par) ~= 'string' or not (sc.commits or {})[par] then
        O.avertir('scénario ' .. id .. ' : parent inconnu « ' .. tostring(par) .. ' » pour le commit ' .. O.texte(cid))
      end
    end
  end
  local function verifier(n, m, nom)
    if not m then return end
    local vis = {}
    for _, c in ipairs(m.commits or {}) do
      if type(c) ~= 'string' or not connus[c] then
        O.avertir('scénario ' .. id .. ', étape ' .. n .. ' (' .. nom .. ') : commit inconnu « ' .. tostring(c) .. ' »')
      else vis[c] = true end
    end
    for _, champ in ipairs({ 'refs', 'tags' }) do
      for k, v in pairs(m[champ] or {}) do
        if type(v) ~= 'string' or not vis[v] then
          O.avertir('scénario ' .. id .. ', étape ' .. n .. ' (' .. nom .. ') : ' .. O.texte(k) .. ' pointe vers « ' .. tostring(v) .. ' », commit absent ou invisible')
        end
      end
    end
    if m.head and type(m.head) ~= 'string' then
      O.avertir('scénario ' .. id .. ', étape ' .. n .. ' : head invalide')
    elseif m.head and not (m.refs or {})[m.head] and not vis[m.head] then
      O.avertir('scénario ' .. id .. ', étape ' .. n .. ' (' .. nom .. ') : HEAD pointe vers « ' .. m.head .. ' », ni branche ni commit visible')
    end
  end
  for n, e in ipairs(sc.etapes) do
    if e['local'] or e.distant then
      verifier(n, e['local'], 'local'); verifier(n, e.distant, 'distant')
    else
      verifier(n, e, 'local')
    end
  end
  local titre = attr(div, 'titre') or (sc.titre and O.texte(sc.titre)) or 'Graphe de commits'
  local classes = 'gf-graphe gf-large'
  for _, c in ipairs(div.classes) do
    if c ~= 'git-graph' then classes = classes .. ' ' .. c end
  end
  local n = #sc.etapes
  -- Données transmises au composant JS (chaînes brutes, sans HTML).
  local donnees = { titre = titre, commits = {}, etapes = {}, couleurs = {}, nom_distant = sc.nom_distant and O.texte(sc.nom_distant) or 'GitLab (origin)' }
  for k, v in pairs(sc.couleurs or {}) do donnees.couleurs[O.texte(k)] = O.texte(v) end
  if sc.ids == false then donnees.ids = false end
  for cid, c in pairs(sc.commits or {}) do
    donnees.commits[O.texte(cid)] = {
      x = tonumber(O.texte(c.x)) or 0,
      y = tonumber(O.texte(c.y)) or 0,
      parents = (function() local p = {} for _, x in ipairs(c.parents or {}) do p[#p + 1] = O.texte(x) end return p end)(),
      msg = c.msg and O.texte(c.msg) or nil,
      label = c.label and O.texte(c.label) or nil,
      couleur = c.couleur and O.texte(c.couleur) or nil,
      auteur = c.auteur and O.texte(c.auteur) or nil,
    }
  end
  local function monde(m)
    if not m then return nil end
    local refs, tags = {}, {}
    for k, v in pairs(m.refs or {}) do refs[O.texte(k)] = O.texte(v) end
    for k, v in pairs(m.tags or {}) do tags[O.texte(k)] = O.texte(v) end
    local commits = {}
    for _, c in ipairs(m.commits or {}) do commits[#commits + 1] = O.texte(c) end
    return { commits = commits, refs = refs, tags = tags, head = m.head and O.texte(m.head) or nil }
  end
  for _, e in ipairs(sc.etapes) do
    local x = {
      texte = e.texte or '',
      commande = e.commande and O.texte(e.commande) or nil,
      estompes = {}, surligne = {},
    }
    for _, c in ipairs(e.estompes or {}) do x.estompes[#x.estompes + 1] = O.texte(c) end
    for _, c in ipairs(e.surligne or {}) do x.surligne[#x.surligne + 1] = O.texte(c) end
    if e['local'] or e.distant then
      x['local'] = monde(e['local'])
      x.distant = monde(e.distant)
    else
      x['local'] = monde(e)
    end
    donnees.etapes[#donnees.etapes + 1] = x
  end

  local h = {}
  h[#h + 1] = '<figure class="' .. classes .. '" data-gf-graphe data-etapes="' .. n .. '">'
  h[#h + 1] = '<figcaption class="gf-graphe__titre">' .. I.svg('branche') .. '<span>' .. O.esc(titre) .. '</span></figcaption>'
  h[#h + 1] = '<div class="gf-graphe__scene" data-gf-scene></div>'
  h[#h + 1] = '<div class="gf-graphe__legende" data-gf-legende aria-live="polite"></div>'
  h[#h + 1] = '<div class="gf-graphe__controles" data-gf-controles hidden></div>'
  h[#h + 1] = '<details class="gf-graphe__alt" open data-gf-alt><summary>Description textuelle du schéma'
    .. (n > 1 and (' (' .. n .. ' étapes)') or '') .. '</summary>' .. alt_texte(sc) .. '</details>'
  h[#h + 1] = '<script type="application/json" data-gf-donnees>' .. pandoc.json.encode(donnees):gsub('</', '<\\/') .. '</script>'
  h[#h + 1] = '</figure>'
  local r = { O.raw(table.concat(h, '\n')) }
  for _, b in ipairs(div.content) do r[#r + 1] = b end
  return r
end

-- Atlas des workflows : plusieurs graphes présentés en onglets (JS).
function M.atlas(div)
  local r = { O.raw('<div class="gf-atlas gf-large" data-gf-atlas>' .. (attr(div, 'titre') and ('<p class="gf-label gf-atlas__titre">' .. I.svg('boussole') .. O.esc(attr(div, 'titre')) .. '</p>') or '')) }
  for _, b in ipairs(div.content) do r[#r + 1] = b end
  r[#r + 1] = O.raw('</div>')
  return r
end

-- ---------------------------------------------------------------------------
-- Pipeline CI
-- ---------------------------------------------------------------------------
local statuts = {
  succes = { 'réussi', 'coche' },
  echec = { 'échoué', 'croix' },
  ignore = { 'ignoré', 'fleche' },
  attente = { 'en attente', 'horloge' },
  manuel = { 'manuel', 'personne' },
  encours = { 'en cours', 'engrenage' },
}

function M.pipeline(div)
  local id = attr(div, 'scenario')
  local p = D.lire('pipelines/' .. (id or '') .. '.yml')
  if not p.stages then return {} end
  local st = statuts[p.statut or 'attente'] or statuts.attente
  local h = {}
  h[#h + 1] = '<figure class="gf-pipeline gf-large gf-pipeline--' .. O.esc(p.statut or 'attente') .. '">'
  h[#h + 1] = '<figcaption class="gf-pipeline__tete"><span class="gf-statut gf-statut--' .. O.esc(p.statut or 'attente') .. '">'
    .. I.svg(st[2]) .. st[1] .. '</span><span class="gf-pipeline__titre">' .. O.texte(p.titre or 'Pipeline') .. '</span>'
    .. (p.declencheur and ('<span class="gf-pipeline__declencheur">' .. p.declencheur .. '</span>') or '')
    .. N.badges({ 'gitlab' }) .. '</figcaption>'
  h[#h + 1] = '<ol class="gf-pipeline__stages">'
  for _, s in ipairs(p.stages) do
    h[#h + 1] = '<li class="gf-stage"><p class="gf-stage__nom"><span class="gf-label">stage</span> ' .. O.texte(s.nom) .. '</p><ul class="gf-stage__jobs">'
    for _, j in ipairs(s.jobs or {}) do
      local js = statuts[j.statut or 'attente'] or statuts.attente
      h[#h + 1] = '<li class="gf-job gf-job--' .. O.esc(j.statut or 'attente') .. '">'
        .. '<span class="gf-job__statut">' .. I.svg(js[2]) .. '<span class="visually-hidden">' .. js[1] .. ' : </span></span>'
        .. '<span class="gf-job__nom">' .. O.texte(j.nom) .. '</span>'
        .. (j.question and ('<span class="gf-job__question">' .. j.question .. '</span>') or '')
        .. (j.image and ('<span class="gf-job__image"><span class="gf-label">image</span> <code>' .. O.esc(O.texte(j.image)) .. '</code></span>') or '')
        .. '</li>'
    end
    h[#h + 1] = '</ul></li>'
  end
  h[#h + 1] = '</ol></figure>'
  local r = { O.raw(table.concat(h, '\n')) }
  for _, b in ipairs(div.content) do r[#r + 1] = b end
  return r
end

-- ---------------------------------------------------------------------------
-- Review guidée : diff (bloc de code .diff dans la page) + problèmes (YAML)
-- ---------------------------------------------------------------------------
local categories = {
  code = 'Code', methode = 'Méthode', reproductibilite = 'Reproductibilité', donnees = 'Données',
  secrets = 'Secrets', chemins = 'Chemins', assertions = 'Assertions', clarte = 'Clarté', historique = 'Historique',
}

function M.review(div)
  local id = attr(div, 'scenario')
  local rv = D.lire('reviews/' .. (id or '') .. '.yml')
  local problemes = rv.problemes or {}
  -- Problèmes indexés par fichier et ligne
  local marques = {}
  for i, pb in ipairs(problemes) do
    local cle = O.texte(pb.fichier or '') .. ':' .. O.texte(pb.ligne or '')
    marques[cle] = marques[cle] or {}
    table.insert(marques[cle], i)
  end
  local h = {}
  h[#h + 1] = '<figure class="gf-review gf-large" data-gf-review>'
  h[#h + 1] = '<figcaption class="gf-review__tete">'
    .. '<span class="gf-review__mr">' .. I.svg('fusion') .. O.texte(rv.titre or 'Merge Request') .. '</span>'
    .. '<span class="gf-review__branches"><code>' .. O.esc(O.texte(rv.branche or '')) .. '</code> ' .. I.svg('fleche') .. ' <code>' .. O.esc(O.texte(rv.cible or 'main')) .. '</code></span>'
    .. (rv.auteur and ('<span class="gf-review__auteur">' .. N.avatar(O.texte(rv.auteur)) .. O.esc(O.texte((D.persona(O.texte(rv.auteur)) or {}).nom or rv.auteur)) .. '</span>') or '')
    .. (rv.commit and ('<span class="gf-review__commit">commit « ' .. O.esc(O.texte(rv.commit)) .. ' »</span>') or '')
    .. N.badges({ 'gitlab' }) .. '</figcaption>'
  h[#h + 1] = '<button type="button" class="gf-bouton gf-review__bascule" data-gf-bascule aria-pressed="false" hidden>'
    .. I.svg('loupe') .. '<span>Afficher les annotations</span></button>'
  -- Les blocs de code .diff de la div
  local autres = {}
  for _, b in ipairs(div.content) do
    if b.t == 'CodeBlock' and b.classes:includes('diff') then
      local fichier = b.attributes['fichier'] or ''
      h[#h + 1] = '<div class="gf-diff"><p class="gf-diff__fichier">' .. I.svg('crayon') .. '<code>' .. O.esc(fichier) .. '</code></p>'
        .. '<table class="gf-diff__table"><caption class="visually-hidden">Modifications du fichier ' .. O.esc(fichier) .. '</caption><tbody>'
      local n = 0
      for ligne in (b.text .. '\n'):gmatch('(.-)\n') do
        local signe = ligne:sub(1, 1)
        local code = ligne:sub(2)
        local classe = 'gf-diff__ligne'
        if signe == '+' then classe = classe .. ' gf-diff__ligne--ajout'
        elseif signe == '-' then classe = classe .. ' gf-diff__ligne--retrait'
        else signe = ' ' end
        if signe ~= '-' then n = n + 1 end
        local num = (signe ~= '-') and tostring(n) or ''
        local m = marques[fichier .. ':' .. num]
        local marque = ''
        if m then
          local refs = {}
          for _, k in ipairs(m) do
            refs[#refs + 1] = '<a class="gf-diff__marque" href="#' .. O.esc(id) .. '-pb-' .. k .. '" aria-label="Problème ' .. k .. '">' .. k .. '</a>'
          end
          marque = table.concat(refs)
          classe = classe .. ' gf-diff__ligne--annotee'
        end
        h[#h + 1] = '<tr class="' .. classe .. '"><td class="gf-diff__num">' .. num .. '</td><td class="gf-diff__signe">'
          .. (signe == ' ' and '' or O.esc(signe)) .. '</td><td class="gf-diff__code"><code>' .. O.esc(code) .. '</code></td><td class="gf-diff__marques">' .. marque .. '</td></tr>'
      end
      h[#h + 1] = '</tbody></table></div>'
    else
      autres[#autres + 1] = b
    end
  end
  -- Liste des problèmes (repliée : on cherche d'abord)
  h[#h + 1] = '<details class="gf-review__problemes"><summary>' .. I.svg('loupe') .. '<span>Les ' .. #problemes .. ' points à relever (après avoir cherché)</span></summary><ol>'
  for i, pb in ipairs(problemes) do
    h[#h + 1] = '<li id="' .. O.esc(id) .. '-pb-' .. i .. '"><p class="gf-review__pb-tete"><span class="gf-categorie gf-categorie--' .. O.esc(O.texte(pb.categorie or 'code')) .. '">'
      .. (categories[O.texte(pb.categorie or 'code')] or O.texte(pb.categorie or '')) .. '</span><strong>' .. (pb.titre or '') .. '</strong>'
      .. (pb.ligne and ('<span class="gf-review__pb-ligne">' .. O.esc(O.texte(pb.fichier or '')) .. ', ligne ' .. O.esc(O.texte(pb.ligne)) .. '</span>') or '')
      .. '</p><p>' .. (pb.explication or '') .. '</p>'
      .. (pb.correction and ('<p class="gf-review__pb-correction"><span class="gf-label">Commentaire de review</span> ' .. pb.correction .. '</p>') or '')
      .. '</li>'
  end
  h[#h + 1] = '</ol></details></figure>'
  local r = { O.raw(table.concat(h, '\n')) }
  for _, b in ipairs(autres) do r[#r + 1] = b end
  return r
end

-- ---------------------------------------------------------------------------
-- Commandes : niveau de risque
-- ---------------------------------------------------------------------------
local icones_risque = { sur = 'coche', reversible = 'retour', reecrit = 'eclair', dangereux = 'alerte' }

function M.commande(cb)
  local risque = cb.attributes['risque']
  if not risque then return nil end
  local info
  for _, x in ipairs(D.composants().risques or {}) do
    if x.id == risque then info = x end
  end
  if not info then
    O.avertir('niveau de risque inconnu : ' .. risque)
    return nil
  end
  cb.attributes['risque'] = nil
  return {
    O.raw('<div class="gf-commande gf-commande--' .. O.esc(risque) .. '"><p class="gf-risque gf-risque--' .. O.esc(risque) .. '" title="' .. O.attr(info.aide) .. '">'
      .. I.svg(icones_risque[risque]) .. '<span>' .. O.texte(info.libelle) .. '</span></p>'),
    cb,
    O.raw('</div>'),
  }
end

-- ---------------------------------------------------------------------------
-- Termes du lexique et badges
-- ---------------------------------------------------------------------------
function M.terme(span)
  local cle = span.attributes['ref'] or pandoc.utils.stringify(span.content)
  local t = D.terme(cle)
  if not t then
    O.avertir('terme inconnu du lexique : « ' .. cle .. ' » dans ' .. O.fichier_courant())
    return span.content
  end
  local proprios = D.proprios(t)
  local libelles = {}
  for _, p in ipairs(proprios) do libelles[#libelles + 1] = O.texte(N.libelle_proprio(p).libelle) end
  local lien = pandoc.Link(span.content, O.url('memos/lexique.qmd', 't-' .. t.id))
  lien.classes = { 'gf-t', 'gf-t--' .. (proprios[1] or 'git') }
  lien.attributes['data-ref'] = t.id
  lien.attributes['data-def'] = O.texte(t.def)
  lien.attributes['data-terme'] = O.texte(t.terme)
  lien.attributes['data-proprio'] = table.concat(libelles, ' · ')
  return lien
end

function M.badge(span, id)
  return pandoc.RawInline('html', N.badges({ id }))
end

-- ---------------------------------------------------------------------------
-- Phrase-boussole
-- ---------------------------------------------------------------------------
function M.boussole(div)
  local phrase = O.texte(D.composants().boussole or '')
  local morceaux = {}
  local total = 0
  local pos = 1
  while true do
    local debut, fin, ref, affiche = phrase:find('%[%[([^|%]]+)|([^%]]+)%]%]', pos)
    if not debut then
      morceaux[#morceaux + 1] = O.esc(phrase:sub(pos))
      break
    end
    morceaux[#morceaux + 1] = O.esc(phrase:sub(pos, debut - 1))
    local t = D.terme(ref)
    if t then
      total = total + 1
      local e = D.etape(t.etape)
      morceaux[#morceaux + 1] = '<a class="gf-boussole__terme" href="' .. O.url('memos/lexique.qmd', 't-' .. t.id) .. '" data-etape="'
        .. O.esc(t.etape) .. '" data-def="' .. O.attr(t.def) .. '" data-terme="' .. O.attr(t.terme) .. '">'
        .. O.esc(affiche) .. '<span class="gf-boussole__quand">' .. (e and ('E' .. O.texte(e.numero)) or '') .. '</span></a>'
    else
      O.avertir('terme de la boussole inconnu : ' .. ref)
      morceaux[#morceaux + 1] = O.esc(affiche)
    end
    pos = fin + 1
  end
  local h = '<figure class="gf-boussole" data-gf-boussole data-total="' .. total .. '">'
    .. '<blockquote class="gf-boussole__phrase"><p>« ' .. table.concat(morceaux) .. ' »</p></blockquote>'
    .. '<figcaption class="gf-boussole__legende"><span class="gf-boussole__compteur" data-gf-boussole-compteur hidden></span>'
  local r = { O.raw(h) }
  for _, b in ipairs(div.content) do r[#r + 1] = b end
  r[#r + 1] = O.raw('</figcaption></figure>')
  return r
end

-- ---------------------------------------------------------------------------
-- Carte du parcours (accueil, page parcours)
-- ---------------------------------------------------------------------------
function M.carte_parcours(div)
  local p = D.parcours()
  local detail = attr(div, 'detail', 'resume')
  local h = { '<div class="gf-carte gf-large gf-carte--' .. O.esc(detail) .. '" data-gf-carte>' }
  for _, jour in ipairs(p.jours or {}) do
    local duree = 0
    for _, e in ipairs(D.etapes()) do if e.jour == jour.id then duree = duree + (tonumber(e.duree) or 0) end end
    h[#h + 1] = '<section class="gf-carte__jour"><h3 class="gf-carte__jour-titre" id="carte-jour-' .. O.texte(jour.numero) .. '"><span class="gf-carte__jour-num">Jour ' .. O.texte(jour.numero)
      .. '</span><span class="gf-carte__jour-nom">' .. O.texte(jour.titre) .. '</span><span class="gf-carte__jour-duree">' .. O.minutes(duree) .. ' de parcours</span></h3><ol class="gf-carte__etapes">'
    local mv_prec = nil
    for _, e in ipairs(D.etapes()) do
      if e.jour == jour.id then
        if e.mouvement ~= mv_prec then
          local mv = D.mouvement(e.mouvement) or {}
          h[#h + 1] = '<li class="gf-carte__mouvement" aria-hidden="true"><span>' .. O.texte(mv.titre or '') .. '</span><span class="gf-carte__verbes">' .. O.texte(mv.verbes or '') .. '</span></li>'
          mv_prec = e.mouvement
        end
        h[#h + 1] = '<li class="gf-carte__etape" data-etape="' .. O.esc(e.id) .. '"><a href="' .. O.url(O.texte(e.fichier)) .. '">'
          .. '<span class="gf-carte__point" aria-hidden="true"></span>'
          .. '<span class="gf-carte__num">E' .. O.texte(e.numero) .. '</span>'
          .. '<span class="gf-carte__titre">' .. O.texte(e.titre) .. '</span>'
          .. '<span class="gf-carte__probleme">' .. e.probleme .. '</span>'
          .. (detail == 'complet' and ('<span class="gf-carte__outil"><span class="gf-label">Outils</span> ' .. e.outil .. '</span>') or '')
          .. '<span class="gf-carte__duree">' .. O.minutes(e.duree) .. '</span>'
          .. '<span class="gf-carte__etat visually-hidden" data-gf-etat></span>'
          .. '</a>'
        local br = {}
        for _, a in ipairs(p.approfondissements or {}) do
          if a.depuis == e.id then
            br[#br + 1] = '<li><a href="' .. O.url(O.texte(a.fichier)) .. '"><span class="gf-carte__branche-point" aria-hidden="true"></span>' .. O.texte(a.titre) .. '</a></li>'
          end
        end
        if #br > 0 then
          h[#h + 1] = '<ul class="gf-carte__branches" aria-label="Approfondissements">' .. table.concat(br) .. '</ul>'
        end
        h[#h + 1] = '</li>'
      end
    end
    h[#h + 1] = '</ol></section>'
  end
  h[#h + 1] = '</div>'
  local r = { O.raw(table.concat(h, '\n')) }
  for _, b in ipairs(div.content) do r[#r + 1] = b end
  return r
end

-- L'équipe du fil rouge
function M.equipe(div)
  local h = { '<ul class="gf-equipe">' }
  for _, p in ipairs(D.lire('personas.yml').personas or {}) do
    h[#h + 1] = '<li class="gf-equipe__membre">' .. N.avatar(p.id, 'grand')
      .. '<p class="gf-equipe__nom">' .. O.texte(p.nom) .. '</p><p class="gf-equipe__role">' .. O.texte(p.role) .. '</p>'
      .. (attr(div, 'detail') and ('<p class="gf-equipe__detail">' .. p.detail .. '</p><p class="gf-equipe__voix">' .. p.voix .. '</p>') or '')
      .. '</li>'
  end
  h[#h + 1] = '</ul>'
  local r = { O.raw(table.concat(h)) }
  for _, b in ipairs(div.content) do r[#r + 1] = b end
  return r
end

return M
