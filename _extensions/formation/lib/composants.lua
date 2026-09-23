-- Composants pédagogiques écrits en Markdown (divs balisés) et rendus en HTML
-- sémantique. Le contenu intérieur reste un AST Pandoc : Quarto continue de
-- traiter liens, code, termes du lexique, etc.
local O = dofile(quarto.utils.resolve_path('lib/outils.lua'))
local D = dofile(quarto.utils.resolve_path('lib/donnees.lua'))
local I = dofile(quarto.utils.resolve_path('lib/icones.lua'))
local N = dofile(quarto.utils.resolve_path('lib/navigation.lua'))

local M = {}
local compteur = 0

local function nouvel_id(prefixe)
  compteur = compteur + 1
  return prefixe .. '-' .. compteur
end

local function attr(div, nom, defaut)
  local v = div.attributes[nom]
  if v == nil or v == '' then return defaut end
  return v
end

-- Sépare les sous-blocs balisés d'un div : { classe = {blocs...}, _reste = {...} }
local function decouper(div, classes)
  local parts = { _reste = {} }
  for _, c in ipairs(classes) do parts[c] = {} end
  for _, b in ipairs(div.content) do
    local range = false
    if b.t == 'Div' then
      for _, c in ipairs(classes) do
        if b.classes:includes(c) then
          table.insert(parts[c], b)
          range = true
          break
        end
      end
    end
    if not range then table.insert(parts._reste, b) end
  end
  return parts
end

local function envelopper(ouverture, blocs, fermeture)
  local r = { O.raw(ouverture) }
  for _, b in ipairs(blocs) do r[#r + 1] = b end
  r[#r + 1] = O.raw(fermeture)
  return r
end

local function contenu(divs)
  local r = {}
  for _, d in ipairs(divs) do
    for _, b in ipairs(d.content) do r[#r + 1] = b end
  end
  return r
end

local function titre_h(niveau, id, texte, classe)
  return '<h' .. niveau .. ' id="' .. O.esc(id) .. '" class="' .. (classe or '') .. '">' .. O.esc(texte) .. '</h' .. niveau .. '>'
end

local est_formateur = (O.profil() == 'formateur')

-- Bloc réservé au formateur ---------------------------------------------------
local function bloc_formateur(blocs, titre)
  if not est_formateur then return {} end
  return envelopper('<div class="gf-formateur" role="note"><p class="gf-formateur__tete">' .. I.svg('personne')
    .. '<span>' .. O.esc(titre or 'Note formateur') .. '</span></p>', blocs, '</div>')
end

function M.formateur(div)
  return bloc_formateur(div.content, attr(div, 'titre'))
end

-- Récit (fil rouge) -----------------------------------------------------------
function M.recit(div)
  local id = attr(div, 'persona')
  local p = id and D.persona(id)
  if p then
    return envelopper('<figure class="gf-recit gf-recit--persona">'
      .. N.avatar(id) .. '<figcaption class="gf-recit__qui"><strong>' .. O.esc(O.texte(p.nom)) .. '</strong>'
      .. '<span>' .. O.esc(O.texte(p.role)) .. '</span></figcaption><blockquote class="gf-recit__texte">',
      div.content, '</blockquote></figure>')
  end
  return envelopper('<div class="gf-recit gf-recit--narration">', div.content, '</div>')
end

function M.situation(div)
  local titre = attr(div, 'titre', 'La situation')
  return envelopper('<section class="gf-situation" aria-label="' .. O.esc(titre) .. '"><p class="gf-label gf-situation__label">'
    .. I.svg('equipe') .. O.esc(titre) .. '</p><div class="gf-situation__texte">', div.content, '</div></section>')
end

-- Mission ----------------------------------------------------------------------
function M.mission(div)
  local id = div.identifier ~= '' and div.identifier or nouvel_id('mission')
  local titre = attr(div, 'titre', 'Mission')
  local parts = decouper(div, { 'objectif', 'consignes', 'reussite', 'indice', 'corrige' })
  local meta = {}
  if attr(div, 'duree') then meta[#meta + 1] = '<li>' .. I.svg('horloge') .. O.esc(attr(div, 'duree')) .. '</li>' end
  if attr(div, 'mode') then meta[#meta + 1] = '<li>' .. I.svg('equipe') .. O.esc(attr(div, 'mode')) .. '</li>' end
  if attr(div, 'depart') then
    meta[#meta + 1] = '<li>' .. I.svg('etiquette') .. 'point de départ <code>' .. O.esc(attr(div, 'depart')) .. '</code></li>'
  end
  local r = {}
  r[#r + 1] = O.raw('<section class="gf-mission" id="' .. O.esc(id) .. '" aria-labelledby="' .. O.esc(id) .. '-titre" data-gf-mission="' .. O.esc(id) .. '">'
    .. '<header class="gf-mission__tete"><p class="gf-mission__type">' .. I.svg('mission') .. '<span>Mission</span></p>'
    .. titre_h(3, id .. '-titre', titre, 'gf-mission__titre')
    .. (#meta > 0 and ('<ul class="gf-mission__meta">' .. table.concat(meta) .. '</ul>') or '')
    .. '</header><div class="gf-mission__corps">')
  local function section(cle, label, classe)
    if #parts[cle] > 0 then
      for _, b in ipairs(envelopper('<div class="gf-mission__' .. classe .. '"><p class="gf-label">' .. label .. '</p>', contenu(parts[cle]), '</div>')) do
        r[#r + 1] = b
      end
    end
  end
  section('objectif', 'Objectif', 'objectif')
  for _, b in ipairs(parts._reste) do r[#r + 1] = b end
  section('consignes', 'Consignes', 'consignes')
  section('reussite', 'Vous avez réussi si…', 'reussite')
  for n, ind in ipairs(parts.indice) do
    local label = ind.attributes['titre'] or ('Indice ' .. n)
    for _, b in ipairs(envelopper('<details class="gf-indice"><summary>' .. I.svg('loupe') .. '<span>' .. O.esc(label) .. '</span></summary><div class="gf-indice__corps">', ind.content, '</div></details>')) do
      r[#r + 1] = b
    end
  end
  if #parts.corrige > 0 then
    for _, b in ipairs(bloc_formateur(contenu(parts.corrige), 'Corrigé (formateur)')) do r[#r + 1] = b end
  end
  r[#r + 1] = O.raw('</div><footer class="gf-mission__pied"><button type="button" class="gf-bouton gf-bouton--discret" data-gf-fait="'
    .. O.esc(id) .. '" aria-pressed="false" hidden>' .. I.svg('coche') .. '<span>Mission terminée</span></button></footer></section>')
  return r
end

-- Incident : message réel → hypothèses → diagnostic → correction → prévention
function M.incident(div)
  local id = div.identifier ~= '' and div.identifier or nouvel_id('incident')
  local titre = attr(div, 'titre', 'Incident')
  local parts = decouper(div, { 'symptome', 'hypotheses', 'diagnostic', 'correction', 'prevention' })
  local r = {}
  r[#r + 1] = O.raw('<section class="gf-incident" id="' .. O.esc(id) .. '" aria-labelledby="' .. O.esc(id) .. '-titre">'
    .. '<header class="gf-incident__tete"><p class="gf-incident__type">' .. I.svg('alerte') .. '<span>Incident</span></p>'
    .. titre_h(3, id .. '-titre', titre, 'gf-incident__titre')
    .. '<ol class="gf-incident__etapes" aria-label="Démarche"><li>Message</li><li>Hypothèses</li><li>Diagnostic</li><li>Correction</li><li>Prévention</li></ol>'
    .. '</header>')
  for _, b in ipairs(parts._reste) do r[#r + 1] = b end
  local function bloc(cle, label, classe)
    if #parts[cle] == 0 then return end
    for _, b in ipairs(envelopper('<div class="gf-incident__' .. classe .. '"><p class="gf-label">' .. label .. '</p>', contenu(parts[cle]), '</div>')) do
      r[#r + 1] = b
    end
  end
  bloc('symptome', 'Ce que vous voyez', 'symptome')
  bloc('hypotheses', 'Vos hypothèses, avant de lire la suite', 'hypotheses')
  if #parts.diagnostic + #parts.correction + #parts.prevention > 0 then
    r[#r + 1] = O.raw('<details class="gf-incident__revelation"><summary>' .. I.svg('loupe') .. '<span>Diagnostic et correction</span></summary><div class="gf-incident__suite">')
    bloc('diagnostic', 'Diagnostic', 'diagnostic')
    bloc('correction', 'Correction', 'correction')
    r[#r + 1] = O.raw('</div></details>')
    -- La prévention reste visible : c'est elle que l'on veut retenir.
    if #parts.prevention > 0 then
      bloc('prevention', 'Prévention', 'prevention')
    end
  end
  r[#r + 1] = O.raw('</section>')
  return r
end

-- À retenir (3 idées maximum) ----------------------------------------------------
function M.retenir(div)
  local n = 0
  for _, b in ipairs(div.content) do
    if b.t == 'OrderedList' or b.t == 'BulletList' then n = n + #b.content end
  end
  if n > 3 then
    O.avertir('bloc « retenir » de ' .. O.fichier_courant() .. ' : ' .. n .. ' idées (3 maximum recommandées)')
  end
  local blocs = {}
  for _, b in ipairs(div.content) do
    if b.t == 'BulletList' then
      blocs[#blocs + 1] = pandoc.OrderedList(b.content)
    else
      blocs[#blocs + 1] = b
    end
  end
  return envelopper('<section class="gf-retenir" aria-label="À retenir"><p class="gf-retenir__titre">À retenir</p>', blocs, '</section>')
end

-- Règle du carnet ----------------------------------------------------------------
function M.regle(div)
  local ref = attr(div, 'ref')
  local r, rang = D.regle(ref or '')
  if not r then
    O.avertir('règle inconnue : ' .. tostring(ref))
    return {}
  end
  local p = D.principe(r.principe) or {}
  local total = #D.regles()
  local html = '<div class="gf-regle" role="note" aria-label="Nouvelle règle au carnet : ' .. O.esc(r.id) .. '">'
    .. '<p class="gf-regle__tete">' .. I.svg('carnet') .. '<span class="gf-regle__num">' .. O.esc(r.id) .. '</span>'
    .. '<span class="gf-regle__label">Nouvelle règle au carnet</span>'
    .. '<span class="gf-principe gf-principe--' .. O.esc(r.principe) .. '">' .. O.texte(p.titre or '') .. '</span></p>'
    .. '<p class="gf-regle__texte">' .. r.texte .. '</p>'
    .. '<p class="gf-regle__origine"><span class="gf-label">Née de</span> ' .. r.origine .. '</p>'
    .. '<p class="gf-regle__lien"><a href="' .. O.url('memos/carnet-de-regles.qmd', r.id) .. '">Voir le carnet · règle ' .. rang .. ' sur ' .. total .. '</a></p>'
  local blocs = { O.raw(html) }
  for _, b in ipairs(div.content) do blocs[#blocs + 1] = b end
  blocs[#blocs + 1] = O.raw('</div>')
  return blocs
end

-- Décodeur : une phrase de jargon, traduite terme à terme -------------------------
function M.decodeur(div)
  local vus, ordre = {}, {}
  -- Les termes ont déjà été transformés en liens (.gf-t, data-ref).
  div:walk({
    Link = function(l)
      if l.classes:includes('gf-t') then
        local t = D.terme(l.attributes['data-ref'])
        if t and not vus[t.id] then
          vus[t.id] = true
          ordre[#ordre + 1] = t
        end
      end
    end,
  })
  local parts = decouper(div, { 'traduction' })
  local dl = {}
  for _, t in ipairs(ordre) do
    dl[#dl + 1] = '<div class="gf-decodeur__entree"><dt><span class="gf-decodeur__terme">' .. O.texte(t.terme) .. '</span>'
      .. N.badges(D.proprios(t)) .. '</dt><dd>' .. t.def .. '</dd></div>'
  end
  local r = envelopper('<section class="gf-decodeur" aria-label="Décodeur de jargon"><p class="gf-label gf-decodeur__label">'
    .. I.svg('bulle') .. 'Décodeur</p><div class="gf-decodeur__phrase">', parts._reste, '</div>')
  if #parts.traduction > 0 then
    for _, b in ipairs(envelopper('<div class="gf-decodeur__traduction"><p class="gf-label">En clair</p>', contenu(parts.traduction), '</div>')) do
      r[#r + 1] = b
    end
  end
  r[#r + 1] = O.raw('<dl class="gf-decodeur__termes">' .. table.concat(dl) .. '</dl></section>')
  return r
end

-- Rosette : un principe, deux pratiques ---------------------------------------------
function M.rosette(div)
  local parts = decouper(div, { 'principe', 'dev', 'stat' })
  local pid = attr(div, 'principe')
  local p = pid and D.principe(pid)
  local r = {}
  r[#r + 1] = O.raw('<section class="gf-rosette" aria-label="Un principe, deux pratiques">')
  for _, b in ipairs(envelopper('<div class="gf-rosette__principe"><p class="gf-label">Le principe'
    .. (p and (' · <span class="gf-principe gf-principe--' .. O.esc(pid) .. '">' .. O.texte(p.titre) .. '</span>') or '') .. '</p>',
    contenu(parts.principe), '</div>')) do r[#r + 1] = b end
  r[#r + 1] = O.raw('<div class="gf-rosette__deux">')
  for _, b in ipairs(envelopper('<div class="gf-rosette__dev"><p class="gf-label">' .. I.svg('terminal') .. 'Chez les développeurs</p>', contenu(parts.dev), '</div>')) do r[#r + 1] = b end
  for _, b in ipairs(envelopper('<div class="gf-rosette__stat"><p class="gf-label">' .. I.svg('cible') .. 'Dans notre projet statistique</p>', contenu(parts.stat), '</div>')) do r[#r + 1] = b end
  r[#r + 1] = O.raw('</div>')
  for _, b in ipairs(parts._reste) do r[#r + 1] = b end
  r[#r + 1] = O.raw('</section>')
  return r
end

-- VS Code : l'équivalent visuel ------------------------------------------------------
function M.vscode(div)
  local titre = attr(div, 'titre', 'L\'équivalent visuel')
  return envelopper('<div class="gf-vscode" role="note" aria-label="Dans VS Code"><p class="gf-vscode__tete">' .. I.svg('fenetre')
    .. '<span class="gf-vscode__nom">Dans VS Code</span><span class="gf-vscode__titre">' .. O.esc(titre) .. '</span></p><div class="gf-vscode__corps">',
    div.content, '</div></div>')
end

-- Idée reçue → réalité ------------------------------------------------------------------
function M.idee_fausse(div)
  local parts = decouper(div, { 'fausse', 'juste' })
  local r = { O.raw('<div class="gf-idee" role="group" aria-label="Idée reçue corrigée">') }
  for _, b in ipairs(envelopper('<div class="gf-idee__fausse"><p class="gf-label">' .. I.svg('croix') .. 'Idée reçue</p>', contenu(parts.fausse), '</div>')) do r[#r + 1] = b end
  for _, b in ipairs(envelopper('<div class="gf-idee__juste"><p class="gf-label">' .. I.svg('coche') .. 'Ce qui se passe réellement</p>', contenu(parts.juste), '</div>')) do r[#r + 1] = b end
  for _, b in ipairs(parts._reste) do r[#r + 1] = b end
  r[#r + 1] = O.raw('</div>')
  return r
end

-- Checkpoint (questions + réponses repliées) ----------------------------------------------
function M.checkpoint(div)
  local titre = attr(div, 'titre', 'Checkpoint')
  local r = { O.raw('<section class="gf-checkpoint" aria-label="' .. O.esc(titre) .. '"><header class="gf-checkpoint__tete"><p class="gf-label">'
    .. I.svg('drapeau') .. 'Checkpoint</p>' .. (attr(div, 'titre') and ('<h3 class="gf-checkpoint__titre">' .. O.esc(titre) .. '</h3>') or '') .. '</header><ol class="gf-checkpoint__questions">') }
  local autres = {}
  for _, b in ipairs(div.content) do
    if b.t == 'Div' and b.classes:includes('question') then
      local parts = decouper(b, { 'reponse' })
      local rappel = b.attributes['rappel']
      r[#r + 1] = O.raw('<li class="gf-question">' .. (rappel and ('<span class="gf-question__rappel">rappel ' .. O.esc(rappel:upper()) .. '</span>') or ''))
      for _, x in ipairs(parts._reste) do r[#r + 1] = x end
      if #parts.reponse > 0 then
        for _, x in ipairs(envelopper('<details class="gf-reponse"><summary>Voir la réponse</summary><div class="gf-reponse__corps">', contenu(parts.reponse), '</div></details>')) do
          r[#r + 1] = x
        end
      end
      r[#r + 1] = O.raw('</li>')
    else
      autres[#autres + 1] = b
    end
  end
  r[#r + 1] = O.raw('</ol>')
  for _, b in ipairs(autres) do r[#r + 1] = b end
  r[#r + 1] = O.raw('</section>')
  return r
end

-- Parcours d'une Merge Request -----------------------------------------------------------------
function M.parcours_mr(div)
  local actif = attr(div, 'etape')
  local actifs = {}
  if actif then for x in actif:gmatch('[^,%s]+') do actifs[x] = true end end
  local h = { '<figure class="gf-mr-parcours gf-large"><figcaption class="gf-label">' .. I.svg('fusion') .. 'Le parcours d\'une Merge Request</figcaption><ol class="gf-mr-parcours__liste">' }
  for i, s in ipairs(D.composants().parcours_mr or {}) do
    local cls = 'gf-station' .. (actifs[s.id] and ' gf-station--active' or '')
    h[#h + 1] = '<li class="' .. cls .. '"' .. (actifs[s.id] and ' aria-current="step"' or '') .. '>'
      .. '<span class="gf-station__num" aria-hidden="true">' .. i .. '</span>'
      .. '<span class="gf-station__titre">' .. O.texte(s.titre) .. '</span>'
      .. N.badges({ s.proprio })
      .. '<span class="gf-station__texte">' .. s.texte .. '</span></li>'
  end
  h[#h + 1] = '</ol></figure>'
  local r = { O.raw(table.concat(h)) }
  for _, b in ipairs(div.content) do r[#r + 1] = b end
  return r
end

-- Chaîne de confiance ---------------------------------------------------------------------------
function M.chaine_confiance(div)
  local jusqua = attr(div, 'jusqua')
  local atteint = (jusqua == nil)
  local h = { '<figure class="gf-chaine gf-large"><figcaption class="gf-label">' .. I.svg('cadenas') .. 'La chaîne de confiance d\'un chiffre publié</figcaption><ol class="gf-chaine__liste">' }
  local encore = true
  for _, m in ipairs(D.composants().chaine_confiance or {}) do
    local e = D.etape(m.etape)
    local etat = (atteint or encore) and 'acquis' or 'a-venir'
    h[#h + 1] = '<li class="gf-maillon gf-maillon--' .. etat .. '">'
      .. '<span class="gf-maillon__titre">' .. O.texte(m.titre) .. '</span>'
      .. '<span class="gf-maillon__texte">' .. m.texte .. '</span>'
      .. (e and ('<span class="gf-maillon__etape">' .. 'E' .. O.texte(e.numero) .. '</span>') or '')
      .. '<span class="visually-hidden">' .. (etat == 'acquis' and ' (acquis)' or ' (à venir)') .. '</span>'
      .. '</li>'
    if jusqua and m.id == jusqua then encore = false end
  end
  h[#h + 1] = '</ol></figure>'
  local r = { O.raw(table.concat(h)) }
  for _, b in ipairs(div.content) do r[#r + 1] = b end
  return r
end

-- Carnet de règles complet (page mémo) -------------------------------------------------------------
function M.carnet(div)
  local h = {}
  local par_principe = attr(div, 'groupe') == 'principe'
  local function carte(r)
    local p = D.principe(r.principe) or {}
    local e = D.etape(r.etape)
    return '<li class="gf-carnet__regle" id="' .. O.esc(r.id) .. '"><p class="gf-regle__tete"><span class="gf-regle__num">' .. O.esc(r.id) .. '</span>'
      .. '<span class="gf-principe gf-principe--' .. O.esc(r.principe) .. '">' .. O.texte(p.titre or '') .. '</span>'
      .. (e and ('<a class="gf-carnet__etape" href="' .. O.url(O.texte(e.fichier)) .. '">née en E' .. O.texte(e.numero) .. '</a>') or '')
      .. '</p><p class="gf-regle__texte">' .. r.texte .. '</p><p class="gf-regle__origine"><span class="gf-label">Née de</span> ' .. r.origine .. '</p></li>'
  end
  if par_principe then
    for _, p in ipairs(D.lire('regles.yml').principes or {}) do
      h[#h + 1] = '<section class="gf-carnet__groupe"><h3 id="principe-' .. O.esc(p.id) .. '"><span class="gf-principe gf-principe--' .. O.esc(p.id) .. '">'
        .. O.texte(p.titre) .. '</span></h3><p class="gf-carnet__def">' .. p.def .. '</p><ol class="gf-carnet">'
      for _, r in ipairs(D.regles()) do
        if r.principe == p.id then h[#h + 1] = carte(r) end
      end
      h[#h + 1] = '</ol></section>'
    end
  else
    h[#h + 1] = '<ol class="gf-carnet">'
    for _, r in ipairs(D.regles()) do h[#h + 1] = carte(r) end
    h[#h + 1] = '</ol>'
  end
  return { O.raw(table.concat(h, '\n')) }
end

-- Lexique complet (page mémo), groupé par propriétaire -----------------------------------------------
function M.lexique(div)
  local ordre = { 'git', 'gitlab', 'github', 'vscode', 'pratique', 'outil' }
  local titres = {
    git = 'Git : sur votre machine, sans serveur',
    gitlab = 'GitLab : la plateforme',
    github = 'GitHub : l\'équivalent',
    vscode = 'VS Code : l\'interface',
    pratique = 'Pratiques et conventions d\'équipe',
    outil = 'Outils de l\'écosystème',
  }
  local niveaux = { pratiquer = 'à pratiquer', comprendre = 'à comprendre', reconnaitre = 'à reconnaître' }
  local h = {}
  for _, pid in ipairs(ordre) do
    local items = {}
    for _, t in ipairs(D.liste_termes()) do
      if D.proprios(t)[1] == pid then
        local e = D.etape(t.etape)
        items[#items + 1] = '<div class="gf-lexique__entree" id="t-' .. O.esc(t.id) .. '"><dt><span class="gf-lexique__terme">' .. O.texte(t.terme) .. '</span>'
          .. N.badges(D.proprios(t))
          .. (t.en and ('<span class="gf-lexique__en">' .. t.en .. '</span>') or '')
          .. '</dt><dd><p>' .. t.def .. '</p>'
          .. (t.piege and ('<p class="gf-lexique__piege"><span class="gf-label">Piège</span> ' .. t.piege .. '</p>') or '')
          .. '<p class="gf-lexique__meta"><span class="gf-niveau gf-niveau--' .. O.esc(t.niveau) .. '">' .. (niveaux[t.niveau] or '') .. '</span>'
          .. (e and (' · <a href="' .. O.url(O.texte(e.fichier)) .. '">introduit en E' .. O.texte(e.numero) .. '</a>') or '')
          .. (t.revise and ' · déjà vu au niveau 1' or '')
          .. '</p></dd></div>'
      end
    end
    if #items > 0 then
      h[#h + 1] = '<section class="gf-lexique__groupe"><h2 id="groupe-' .. pid .. '">' .. O.esc(titres[pid]) .. '</h2><dl class="gf-lexique">'
        .. table.concat(items) .. '</dl></section>'
    end
  end
  return { O.raw(table.concat(h, '\n')) }
end

-- Tableau « Git ou GitLab ? » -------------------------------------------------------------------------
function M.git_ou_gitlab(div)
  local cols = { git = {}, gitlab = {} }
  for _, t in ipairs(D.liste_termes()) do
    for _, p in ipairs(D.proprios(t)) do
      if cols[p] then
        cols[p][#cols[p] + 1] = '<li><a href="' .. O.url('memos/lexique.qmd', 't-' .. t.id) .. '">' .. O.texte(t.terme) .. '</a></li>'
      end
    end
  end
  return { O.raw('<div class="gf-deux-mondes gf-large">'
    .. '<section class="gf-monde gf-monde--git"><h3>' .. I.svg('commit') .. 'Git</h3><p>Installé sur votre machine. Fonctionne sans réseau. Connaît les commits, les branches, les tags, les remotes.</p><ul>' .. table.concat(cols.git) .. '</ul></section>'
    .. '<section class="gf-monde gf-monde--gitlab"><h3>' .. I.svg('serveur') .. 'GitLab</h3><p>Un serveur qui héberge des dépôts Git et ajoute la collaboration : issues, MR, review, pipelines, protections, Releases.</p><ul>' .. table.concat(cols.gitlab) .. '</ul></section>'
    .. '</div>') }
end

return M
