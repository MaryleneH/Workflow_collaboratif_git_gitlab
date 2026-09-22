-- Navigation-graphe : le parcours est une ligne de commits, HEAD indique
-- la page en cours, les approfondissements sont des branches latérales.
-- Tout est produit en HTML statique : la navigation fonctionne sans JavaScript.
local O = dofile(quarto.utils.resolve_path('lib/outils.lua'))
local D = dofile(quarto.utils.resolve_path('lib/donnees.lua'))
local I = dofile(quarto.utils.resolve_path('lib/icones.lua'))

local M = {}

local function libelle_proprio(id)
  for _, p in ipairs(D.composants().proprios or {}) do
    if p.id == id then return p end
  end
  return { id = id, libelle = id, aide = '' }
end
M.libelle_proprio = libelle_proprio

function M.badges(proprios)
  local out = {}
  for _, id in ipairs(proprios) do
    local p = libelle_proprio(id)
    out[#out + 1] = '<span class="gf-badge gf-badge--' .. O.esc(id) .. '" title="' .. O.attr(p.aide) .. '">'
      .. O.texte(p.libelle) .. '</span>'
  end
  return table.concat(out, '')
end

function M.avatar(id, taille)
  local p = D.persona(id)
  if not p then return '' end
  local initiale = O.texte(p.nom):sub(1, 1)
  -- Gestion des initiales accentuées (UTF-8 sur plusieurs octets)
  local premier = O.texte(p.nom):match('^[%z\1-\127\194-\244][\128-\191]*') or initiale
  return '<span class="gf-avatar gf-avatar--' .. O.esc(p.teinte or 1) .. (taille and (' gf-avatar--' .. taille) or '')
    .. '" aria-hidden="true">' .. O.esc(premier) .. '</span>'
end

-- Numéro d'étape affiché : « E2 »
local function num(e) return 'E' .. O.texte(e.numero) end

-- Liste des approfondissements rattachés à une étape.
local function branches_de(id_etape)
  local r = {}
  for _, a in ipairs(D.parcours().approfondissements or {}) do
    if a.depuis == id_etape then r[#r + 1] = a end
  end
  return r
end

-- Le rail de navigation. `courant` : id d'étape ou d'approfondissement (ou nil).
function M.rail(courant)
  local p = D.parcours()
  local etapes = D.etapes()
  local total = #etapes - 1
  local h = {}
  local courant_etape = D.etape(courant or '')
  local courant_appro = D.approfondissement(courant or '')

  local resume
  if courant_etape then
    resume = num(courant_etape) .. ' / ' .. total .. ' · ' .. O.texte(courant_etape.court)
  elseif courant_appro then
    resume = 'Approfondissement · ' .. O.texte(courant_appro.court)
  else
    resume = 'Le parcours en ' .. total + 1 .. ' étapes'
  end

  h[#h + 1] = '<nav class="gf-rail" aria-label="Parcours de formation">'
  h[#h + 1] = '<details class="gf-rail__plie" open data-gf-rail>'
  h[#h + 1] = '<summary class="gf-rail__resume">' .. I.svg('branche') .. '<span>' .. O.esc(resume) .. '</span></summary>'
  h[#h + 1] = '<div class="gf-rail__corps">'
  h[#h + 1] = '<p class="gf-rail__titre"><a href="' .. O.url('parcours/index.qmd') .. '">Le parcours</a>'
    .. '<span class="gf-rail__avancement" data-gf-avancement hidden></span></p>'

  for _, jour in ipairs(p.jours or {}) do
    h[#h + 1] = '<div class="gf-rail__jour">'
    h[#h + 1] = '<p class="gf-rail__jour-titre"><span class="gf-rail__jour-num">Jour ' .. O.esc(O.texte(jour.numero)) .. '</span> '
      .. O.esc(O.texte(jour.titre)) .. '</p>'
    h[#h + 1] = '<ol class="gf-rail__liste">'
    for _, e in ipairs(etapes) do
      if e.jour == jour.id then
        local est_courant = (e.id == courant)
        local classes = 'gf-noeud'
        if est_courant then classes = classes .. ' gf-noeud--courant' end
        h[#h + 1] = '<li class="' .. classes .. '" data-etape="' .. O.esc(e.id) .. '">'
        h[#h + 1] = '<a class="gf-noeud__lien" href="' .. O.url(O.texte(e.fichier)) .. '"'
          .. (est_courant and ' aria-current="page"' or '') .. '>'
          .. '<span class="gf-noeud__point" aria-hidden="true"></span>'
          .. '<span class="gf-noeud__num">' .. num(e) .. '</span>'
          .. '<span class="gf-noeud__titre">' .. O.esc(O.texte(e.court)) .. '</span>'
          .. '<span class="gf-noeud__etat visually-hidden" data-gf-etat></span>'
          .. '</a>'
        if est_courant then
          h[#h + 1] = '<span class="gf-head" aria-hidden="true"><span class="gf-head__nom">HEAD</span> vous êtes ici</span>'
        end
        local br = branches_de(e.id)
        if #br > 0 then
          h[#h + 1] = '<ol class="gf-rail__branches" aria-label="Approfondissements depuis ' .. num(e) .. '">'
          for _, a in ipairs(br) do
            local a_courant = (a.id == courant)
            h[#h + 1] = '<li class="gf-noeud gf-noeud--branche' .. (a_courant and ' gf-noeud--courant' or '') .. '">'
              .. '<a class="gf-noeud__lien" href="' .. O.url(O.texte(a.fichier)) .. '"'
              .. (a_courant and ' aria-current="page"' or '') .. '>'
              .. '<span class="gf-noeud__point" aria-hidden="true"></span>'
              .. '<span class="gf-noeud__titre">' .. O.esc(O.texte(a.court)) .. '</span></a>'
              .. (a_courant and '<span class="gf-head" aria-hidden="true"><span class="gf-head__nom">HEAD</span> vous êtes ici</span>' or '')
              .. '</li>'
          end
          h[#h + 1] = '</ol>'
        end
        h[#h + 1] = '</li>'
      end
    end
    h[#h + 1] = '</ol></div>'
  end

  h[#h + 1] = '<ul class="gf-rail__annexes">'
  h[#h + 1] = '<li><a href="' .. O.url('memos/carnet-de-regles.qmd') .. '">' .. I.svg('carnet') .. 'Carnet de règles</a></li>'
  h[#h + 1] = '<li><a href="' .. O.url('memos/lexique.qmd') .. '">' .. I.svg('livre') .. 'Lexique</a></li>'
  h[#h + 1] = '<li><a href="' .. O.url('memos/commandes.qmd') .. '">' .. I.svg('terminal') .. 'Commandes</a></li>'
  h[#h + 1] = '</ul>'
  h[#h + 1] = '</div></details></nav>'
  return table.concat(h, '\n')
end

-- Puces des termes introduits à une étape (nouveaux / révisés).
local function termes_etape(id)
  local nouveaux, revises = {}, {}
  for _, t in ipairs(D.liste_termes()) do
    if t.etape == id then
      local item = '<li><a class="gf-puce-terme gf-t--' .. O.esc(D.proprios(t)[1] or 'git') .. '" href="'
        .. O.url('memos/lexique.qmd', 't-' .. t.id) .. '">' .. O.texte(t.terme) .. '</a></li>'
      if t.revise then revises[#revises + 1] = item else nouveaux[#nouveaux + 1] = item end
    end
  end
  return nouveaux, revises
end

-- En-tête d'une étape du parcours.
function M.entete_etape(e, titre_page)
  local jour = D.jour(e.jour) or {}
  local mv = D.mouvement(e.mouvement) or {}
  local total = #D.etapes() - 1
  local h = {}
  h[#h + 1] = '<header class="gf-entete">'
  h[#h + 1] = '<p class="gf-entete__sur">'
    .. '<span class="gf-entete__etape">' .. num(e) .. '<span class="gf-entete__sur-total"> / ' .. total .. '</span></span>'
    .. '<span class="gf-entete__jour">Jour ' .. O.esc(O.texte(jour.numero)) .. '</span>'
    .. '<span class="gf-entete__mouvement">' .. O.esc(O.texte(mv.titre)) .. '</span>'
    .. '<span class="gf-entete__duree">' .. I.svg('horloge') .. O.minutes(e.duree) .. '</span>'
    .. '</p>'
  h[#h + 1] = '<h1 class="gf-entete__titre">' .. O.esc(titre_page or O.texte(e.titre)) .. '</h1>'
  h[#h + 1] = '<div class="gf-entete__probleme"><p class="gf-label">Le problème</p><p class="gf-entete__probleme-texte">'
    .. e.probleme .. '</p></div>'
  h[#h + 1] = '<dl class="gf-entete__cadre">'
  h[#h + 1] = '<div><dt>Ce qui va vous servir</dt><dd>' .. e.outil .. '</dd></div>'
  h[#h + 1] = '<div><dt>À la fin, vous saurez</dt><dd>' .. e.capacite .. '</dd></div>'
  h[#h + 1] = '</dl>'

  -- Équipe du fil rouge à ce stade
  local membres = {}
  local noms = {}
  for _, id in ipairs(e.equipe or {}) do
    local p = D.persona(id)
    if p then
      membres[#membres + 1] = M.avatar(id)
      noms[#noms + 1] = O.texte(p.nom)
    end
  end
  local nouveaux, revises = termes_etape(e.id)
  h[#h + 1] = '<div class="gf-entete__pied">'
  if #membres > 0 then
    h[#h + 1] = '<p class="gf-entete__equipe"><span class="gf-avatars">' .. table.concat(membres) .. '</span>'
      .. '<span><span class="gf-label">L\'équipe</span> ' .. O.esc(table.concat(noms, ', ')) .. ' et vous</span></p>'
  end
  if #nouveaux > 0 or #revises > 0 then
    h[#h + 1] = '<div class="gf-entete__termes">'
    if #nouveaux > 0 then
      h[#h + 1] = '<p class="gf-label">Nouveaux termes</p><ul class="gf-puces">' .. table.concat(nouveaux) .. '</ul>'
    end
    if #revises > 0 then
      h[#h + 1] = '<p class="gf-label">Révisés du niveau 1</p><ul class="gf-puces gf-puces--revises">' .. table.concat(revises) .. '</ul>'
    end
    h[#h + 1] = '</div>'
  end
  h[#h + 1] = '</div></header>'
  return table.concat(h, '\n')
end

-- En-tête simple pour les autres pages.
function M.entete_page(meta, surtitre)
  local titre = meta.title and pandoc.utils.stringify(meta.title) or ''
  local sous = meta.subtitle and pandoc.utils.stringify(meta.subtitle) or nil
  local desc = meta.chapeau and pandoc.utils.stringify(meta.chapeau) or nil
  local h = { '<header class="gf-entete gf-entete--page">' }
  if surtitre then h[#h + 1] = '<p class="gf-entete__sur"><span>' .. O.esc(surtitre) .. '</span></p>' end
  h[#h + 1] = '<h1 class="gf-entete__titre">' .. O.esc(titre) .. '</h1>'
  if sous then h[#h + 1] = '<p class="gf-entete__sous-titre">' .. O.esc(sous) .. '</p>' end
  if desc then h[#h + 1] = '<p class="gf-entete__chapeau">' .. O.esc(desc) .. '</p>' end
  h[#h + 1] = '</header>'
  return table.concat(h, '\n')
end

-- Pont vers la suite (fin d'étape). `contenu` : blocs rédigés (::: pont).
function M.pont(e, contenu)
  local etapes = D.etapes()
  local _, i = D.etape(e.id)
  local suivante = etapes[i + 1]
  local precedente = etapes[i - 1]
  local blocs = {}
  blocs[#blocs + 1] = O.raw('<section class="gf-pont" aria-labelledby="gf-pont-titre">'
    .. '<h2 id="gf-pont-titre" class="gf-pont__titre">' .. I.svg('fusion') .. 'Et maintenant</h2>')
  if contenu and #contenu > 0 then
    blocs[#blocs + 1] = O.raw('<div class="gf-pont__texte">')
    for _, b in ipairs(contenu) do blocs[#blocs + 1] = b end
    blocs[#blocs + 1] = O.raw('</div>')
  end
  local h = {}
  h[#h + 1] = '<div class="gf-pont__actions">'
  h[#h + 1] = '<button type="button" class="gf-bouton gf-bouton--discret gf-etape-faite" data-gf-etape-faite="'
    .. O.esc(e.id) .. '" aria-pressed="false" hidden>' .. I.svg('coche') .. '<span>Marquer l\'étape comme terminée</span></button>'
  h[#h + 1] = '</div>'
  h[#h + 1] = '<div class="gf-pont__nav">'
  if precedente then
    h[#h + 1] = '<a class="gf-pont__lien gf-pont__lien--prec" href="' .. O.url(O.texte(precedente.fichier)) .. '">'
      .. '<span class="gf-pont__sens">' .. I.svg('fleche_g') .. 'Étape précédente · ' .. num(precedente) .. '</span>'
      .. '<span class="gf-pont__cible">' .. O.esc(O.texte(precedente.titre)) .. '</span></a>'
  end
  if suivante then
    h[#h + 1] = '<a class="gf-pont__lien gf-pont__lien--suiv" href="' .. O.url(O.texte(suivante.fichier)) .. '">'
      .. '<span class="gf-pont__sens">Étape suivante · ' .. num(suivante) .. ' · ' .. O.minutes(suivante.duree) .. I.svg('fleche') .. '</span>'
      .. '<span class="gf-pont__cible">' .. O.esc(O.texte(suivante.titre)) .. '</span>'
      .. '<span class="gf-pont__probleme"><span class="gf-label">Le problème</span> ' .. suivante.probleme .. '</span></a>'
  else
    h[#h + 1] = '<a class="gf-pont__lien gf-pont__lien--suiv" href="' .. O.url('memos/notre-workflow.qmd') .. '">'
      .. '<span class="gf-pont__sens">Fin du parcours' .. I.svg('fleche') .. '</span>'
      .. '<span class="gf-pont__cible">Retrouver notre workflow</span></a>'
  end
  h[#h + 1] = '</div></section>'
  blocs[#blocs + 1] = O.raw(table.concat(h, '\n'))
  return blocs
end

-- Pied des approfondissements : retour à l'étape de départ.
function M.pont_approfondissement(a)
  local e = D.etape(a.depuis)
  if not e then return {} end
  return { O.raw('<section class="gf-pont gf-pont--branche"><div class="gf-pont__nav">'
    .. '<a class="gf-pont__lien gf-pont__lien--prec" href="' .. O.url(O.texte(e.fichier)) .. '">'
    .. '<span class="gf-pont__sens">' .. I.svg('fusion') .. 'Revenir sur la ligne principale · ' .. num(e) .. '</span>'
    .. '<span class="gf-pont__cible">' .. O.esc(O.texte(e.titre)) .. '</span></a></div></section>') }
end

-- « Sur cette page » : titres de niveau 2.
function M.anatomie(blocs)
  local items = {}
  for _, b in ipairs(blocs) do
    if b.t == 'Header' and b.level == 2 and b.identifier ~= '' and not b.classes:includes('unlisted') then
      items[#items + 1] = '<li><a href="#' .. O.esc(b.identifier) .. '">' .. O.esc(pandoc.utils.stringify(b.content)) .. '</a></li>'
    end
  end
  if #items < 2 then return '' end
  return '<aside class="gf-anatomie" aria-label="Sur cette page"><p class="gf-anatomie__titre">Sur cette page</p><ol>'
    .. table.concat(items) .. '</ol></aside>'
end

return M
