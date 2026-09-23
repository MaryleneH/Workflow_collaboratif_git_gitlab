-- Outils partagés : échappement HTML, blocs bruts, chemins, journalisation.
local M = {}

function M.esc(s)
  s = tostring(s or '')
  return (s:gsub('&', '&amp;'):gsub('<', '&lt;'):gsub('>', '&gt;'):gsub('"', '&quot;'))
end

-- Retire les balises d'un fragment HTML (pour attributs et textes alternatifs).
function M.texte(html)
  local s = tostring(html or ''):gsub('<[^>]+>', '')
  s = s:gsub('&lt;', '<'):gsub('&gt;', '>'):gsub('&quot;', '"'):gsub('&#39;', "'"):gsub('&amp;', '&')
  return s
end

-- Valeur d'attribut sûre à partir d'un fragment HTML.
function M.attr(html)
  return M.esc(M.texte(html))
end

function M.raw(html)
  return pandoc.RawBlock('html', html)
end

function M.raw_inline(html)
  return pandoc.RawInline('html', html)
end

function M.avertir(msg)
  quarto.log.warning('[formation] ' .. msg)
end

-- Convertit des blocs Pandoc en HTML (utilisé pour des contenus courts).
function M.blocs_html(blocs)
  return (pandoc.write(pandoc.Pandoc(blocs), 'html'):gsub('\n$', ''))
end

function M.inlines_html(inlines)
  return (pandoc.write(pandoc.Pandoc({ pandoc.Plain(inlines) }), 'html'):gsub('\n$', ''))
end

-- Chemin relatif vers la racine du site pour la page en cours ('' ou '../').
function M.racine()
  local offset = quarto.project.offset or '.'
  if offset == '.' or offset == '' then return '' end
  return offset .. '/'
end

-- Chemin du fichier en cours relatif au projet (séparateurs '/').
function M.fichier_courant()
  local input = quarto.doc.input_file or ''
  local dir = quarto.project.directory or ''
  local rel = input
  if dir ~= '' and input:sub(1, #dir) == dir then
    rel = input:sub(#dir + 2)
  end
  return (rel:gsub('\\', '/'))
end

-- URL relative d'un fichier .qmd du projet depuis la page en cours.
function M.url(fichier, ancre)
  local u = M.racine() .. fichier:gsub('%.qmd$', '.html')
  if ancre then u = u .. '#' .. ancre end
  return u
end

function M.profil()
  local p = quarto.project.profile
  if p then
    for _, v in ipairs(p) do
      if v == 'formateur' then return 'formateur' end
    end
  end
  return 'stagiaire'
end

function M.a_classe(el, classe)
  return el.classes and el.classes:includes(classe)
end

function M.minutes(n)
  n = tonumber(n) or 0
  if n >= 60 then
    local h, m = math.floor(n / 60), n % 60
    if m == 0 then return h .. ' h' end
    return string.format('%d h %02d', h, m)
  end
  return n .. ' min'
end

return M
