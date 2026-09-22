--[[
Extension « formation » : transforme le Markdown des pages en expérience
pédagogique (navigation-graphe, composants, graphe vivant).

Architecture :
  lib/outils.lua      échappement, chemins, profil actif
  lib/donnees.lua     lecture des sources YAML (assets/data)
  lib/icones.lua      icônes SVG au trait
  lib/navigation.lua  rail du parcours, en-têtes, ponts, « sur cette page »
  lib/composants.lua  mission, incident, retenir, règle, décodeur, rosette…
  lib/visuels.lua     graphe Git, atlas, pipeline, review, commandes, termes

Voir docs/GUIDE-AUTEUR.md pour la syntaxe de chaque composant.
]]

local O = dofile(quarto.utils.resolve_path('lib/outils.lua'))
local D = dofile(quarto.utils.resolve_path('lib/donnees.lua'))
local N = dofile(quarto.utils.resolve_path('lib/navigation.lua'))
local C = dofile(quarto.utils.resolve_path('lib/composants.lua'))
local V = dofile(quarto.utils.resolve_path('lib/visuels.lua'))

-- Classe de div → fonction de rendu.
local composants = {
  ['mission'] = C.mission,
  ['incident'] = C.incident,
  ['retenir'] = C.retenir,
  ['regle'] = C.regle,
  ['decodeur'] = C.decodeur,
  ['rosette'] = C.rosette,
  ['vscode'] = C.vscode,
  ['idee-fausse'] = C.idee_fausse,
  ['checkpoint'] = C.checkpoint,
  ['recit'] = C.recit,
  ['situation'] = C.situation,
  ['formateur'] = C.formateur,
  ['corrige'] = C.formateur,
  ['parcours-mr'] = C.parcours_mr,
  ['chaine-confiance'] = C.chaine_confiance,
  ['carnet'] = C.carnet,
  ['lexique'] = C.lexique,
  ['git-ou-gitlab'] = C.git_ou_gitlab,
  ['git-graph'] = V.graphe,
  ['atlas'] = V.atlas,
  ['pipeline'] = V.pipeline,
  ['review'] = V.review,
  ['boussole'] = V.boussole,
  ['carte-parcours'] = V.carte_parcours,
  ['equipe'] = V.equipe,
}

local badges = { git = true, gitlab = true, github = true, vscode = true, pratique = true, outil = true }

-- Typographie française : espace insécable avant « : ; ! ? » » et après « « ».
local NBSP, FINE = '\u{00A0}', '\u{202F}'
local function typographie(inlines)
  local modifie = false
  for i = 1, #inlines - 1 do
    local a, b = inlines[i], inlines[i + 1]
    if a.t == 'Space' and b.t == 'Str' then
      local c = b.text:sub(1, 1)
      if c == ':' or b.text:sub(1, 2) == '»' then
        inlines[i] = pandoc.Str(NBSP); modifie = true
      elseif c == ';' or c == '!' or c == '?' then
        inlines[i] = pandoc.Str(FINE); modifie = true
      end
    elseif a.t == 'Str' and a.text:sub(-2) == '«' and b.t == 'Space' then
      inlines[i + 1] = pandoc.Str(NBSP); modifie = true
    end
  end
  return modifie and inlines or nil
end

local filtre_contenu = {
  Inlines = typographie,
  Span = function(s)
    if s.classes:includes('t') then return V.terme(s) end
    for _, c in ipairs(s.classes) do
      if badges[c] and #s.content == 0 then return V.badge(s, c) end
    end
    return nil
  end,
  CodeBlock = function(cb)
    return V.commande(cb)
  end,
  -- Tableaux : conteneur défilant (jamais de défilement horizontal de la page)
  Table = function(t)
    return {
      pandoc.RawBlock('html', '<div class="gf-table-defile" tabindex="0" role="region" aria-label="Tableau (défilement horizontal possible)">'),
      t,
      pandoc.RawBlock('html', '</div>'),
    }
  end,
  Div = function(div)
    for _, c in ipairs(div.classes) do
      local f = composants[c]
      if f then return f(div) end
    end
    return nil
  end,
}

-- Ressources JavaScript (modules ES) : copiées dans site_libs/ par Quarto.
local function dependances()
  local js = pandoc.path.join({ quarto.project.directory, 'assets', 'js' })
  local fichiers = {}
  for _, nom in ipairs({ 'graphe.js', 'progression.js', 'termes.js', 'onglets.js', 'rail.js', 'review.js' }) do
    fichiers[#fichiers + 1] = { name = nom, path = pandoc.path.join({ js, nom }) }
  end
  quarto.doc.add_html_dependency({
    name = 'formation',
    version = '1.0.0',
    scripts = { { path = pandoc.path.join({ js, 'formation.js' }), attribs = { type = 'module' }, afterBody = true } },
    resources = fichiers,
  })
end

local function contient_blocs(liste)
  return liste and #liste > 0
end

function Pandoc(doc)
  if not quarto.doc.is_format('html') then return doc end
  dependances()

  local meta = doc.meta
  local id_etape = meta.etape and pandoc.utils.stringify(meta.etape) or nil
  local id_appro = meta.approfondissement and pandoc.utils.stringify(meta.approfondissement) or nil
  local type_page = meta['gf-page'] and pandoc.utils.stringify(meta['gf-page']) or nil
  local etape = id_etape and D.etape(id_etape)
  local appro = id_appro and D.approfondissement(id_appro)
  if id_etape and not etape then O.avertir('étape inconnue dans parcours.yml : ' .. id_etape) end

  -- 1. Extraire le pont rédigé (::: pont) avant transformation.
  local pont, blocs = {}, pandoc.Blocks({})
  for _, b in ipairs(doc.blocks) do
    if b.t == 'Div' and b.classes:includes('pont') then
      for _, x in ipairs(b.content) do pont[#pont + 1] = x end
    else
      blocs:insert(b)
    end
  end

  -- 2. Transformer les composants.
  blocs = blocs:walk(filtre_contenu)
  pont = pandoc.Blocks(pont):walk(filtre_contenu)

  -- 3. Mise en page.
  local titre = meta.title and pandoc.utils.stringify(meta.title) or ''
  local r = pandoc.Blocks({})
  local function ajouter(x)
    if type(x) == 'string' then r:insert(O.raw(x))
    elseif x.t then r:insert(x)
    else for _, b in ipairs(x) do r:insert(b) end end
  end

  if type_page == 'accueil' then
    ajouter('<div class="gf-page gf-page--accueil"><main id="contenu" class="gf-main gf-main--accueil" tabindex="-1">')
    ajouter(blocs)
    ajouter('</main></div>')
  else
    local classe = etape and 'gf-page--etape' or (appro and 'gf-page--branche' or 'gf-page--doc')
    ajouter('<div class="gf-page ' .. classe .. '">')
    ajouter(N.rail(id_etape or id_appro))
    ajouter('<main id="contenu" class="gf-main" tabindex="-1">')
    if etape then
      ajouter(N.entete_etape(etape, titre ~= '' and titre or nil))
    elseif appro then
      local depuis = D.etape(appro.depuis)
      ajouter(N.entete_page(meta, 'Approfondissement' .. (depuis and (' · branche partie de E' .. O.texte(depuis.numero)) or '')))
    else
      ajouter(N.entete_page(meta, meta.surtitre and pandoc.utils.stringify(meta.surtitre) or nil))
    end
    ajouter('<div class="gf-contenu">')
    ajouter(blocs)
    ajouter('</div>')
    if etape then
      ajouter(N.pont(etape, pont))
    elseif appro then
      if contient_blocs(pont) then
        ajouter('<section class="gf-pont gf-pont--texte">')
        ajouter(pont)
        ajouter('</section>')
      end
      ajouter(N.pont_approfondissement(appro))
    elseif contient_blocs(pont) then
      ajouter('<section class="gf-pont">')
      ajouter(pont)
      ajouter('</section>')
    end
    ajouter('</main>')
    ajouter(N.anatomie(blocs))
    ajouter('</div>')
  end

  doc.blocks = r
  return doc
end
