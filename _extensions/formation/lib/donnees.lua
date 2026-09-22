-- Lecture des sources structurées (assets/data/*.yml).
-- Le YAML est lu par Pandoc lui-même (bloc de métadonnées) : aucune
-- dépendance externe. Les chaînes deviennent du HTML (Markdown en ligne
-- autorisé : `code`, *italique*, **gras**), les booléens restent booléens.
local O = dofile(quarto.utils.resolve_path('lib/outils.lua'))

local M = {}
local cache = {}

local function vers_lua(v)
  local t = pandoc.utils.type(v)
  if t == 'Inlines' then
    return O.inlines_html(v)
  elseif t == 'Blocks' then
    -- Un scalaire multiligne (>-) produit un seul paragraphe : on le déballe.
    if #v == 1 and (v[1].t == 'Para' or v[1].t == 'Plain') then
      return O.inlines_html(v[1].content)
    end
    return O.blocs_html(v)
  elseif t == 'List' then
    local r = {}
    for i, x in ipairs(v) do r[i] = vers_lua(x) end
    return r
  elseif t == 'Meta' or t == 'table' then
    local r = {}
    for k, x in pairs(v) do r[k] = vers_lua(x) end
    return r
  end
  return v
end

function M.lire(chemin_relatif)
  if cache[chemin_relatif] then return cache[chemin_relatif] end
  local chemin = pandoc.path.join({ quarto.project.directory, 'assets', 'data', chemin_relatif })
  local f = io.open(chemin, 'r')
  if not f then
    O.avertir('fichier de données introuvable : assets/data/' .. chemin_relatif)
    cache[chemin_relatif] = {}
    return cache[chemin_relatif]
  end
  local texte = f:read('a')
  f:close()
  -- Markdown en ligne sans typographie « intelligente » ni exposants/indices,
  -- pour que les commandes (--force-with-lease, HEAD~1, df$x) restent intactes.
  local format = 'markdown-smart-subscript-superscript-tex_math_dollars-tex_math_single_backslash-raw_tex-raw_html-strikeout'
  local doc = pandoc.read('---\n' .. texte .. '\n---\n', format)
  local r = vers_lua(doc.meta)
  cache[chemin_relatif] = r
  return r
end

-- Accès indexés -------------------------------------------------------------

function M.parcours() return M.lire('parcours.yml') end

function M.etapes() return M.parcours().etapes or {} end

function M.etape(id)
  for i, e in ipairs(M.etapes()) do
    if e.id == id then return e, i end
  end
  return nil
end

function M.approfondissement(id)
  for _, a in ipairs(M.parcours().approfondissements or {}) do
    if a.id == id then return a end
  end
  return nil
end

function M.jour(id)
  for _, j in ipairs(M.parcours().jours or {}) do
    if j.id == id then return j end
  end
  return nil
end

function M.mouvement(id)
  for _, m in ipairs(M.parcours().mouvements or {}) do
    if m.id == id then return m end
  end
  return nil
end

function M.personas()
  local r = {}
  for _, p in ipairs(M.lire('personas.yml').personas or {}) do r[p.id] = p end
  return r
end

function M.persona(id) return M.personas()[id] end

function M.termes()
  if cache['@termes'] then return cache['@termes'] end
  local index = {}
  for _, t in ipairs(M.lire('lexique.yml').termes or {}) do
    index[t.id] = t
  end
  cache['@termes'] = index
  return index
end

function M.liste_termes() return M.lire('lexique.yml').termes or {} end

-- Retrouve un terme par identifiant ou par sa forme affichée.
function M.terme(cle)
  if not cle then return nil end
  local index = M.termes()
  if index[cle] then return index[cle] end
  local bas = pandoc.text.lower(cle)
  for _, t in pairs(index) do
    if pandoc.text.lower(O.texte(t.terme)) == bas then return t end
  end
  return nil
end

function M.regles() return M.lire('regles.yml').regles or {} end

function M.regle(id)
  for i, r in ipairs(M.regles()) do
    if r.id == id then return r, i end
  end
  return nil
end

function M.principe(id)
  for _, p in ipairs(M.lire('regles.yml').principes or {}) do
    if p.id == id then return p end
  end
  return nil
end

function M.composants() return M.lire('composants.yml') end

-- Liste des propriétaires d'un terme (toujours une liste).
function M.proprios(t)
  local p = t and t.proprio
  if type(p) == 'table' then return p end
  if p then return { p } end
  return {}
end

return M
