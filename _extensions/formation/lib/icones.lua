-- Jeu d'icônes au trait, dessiné pour le site (aucune bibliothèque externe).
-- Toutes les icônes : viewBox 24×24, trait « currentColor », décoratives
-- (aria-hidden) : le sens est toujours porté par un texte voisin.
local M = {}

local chemins = {
  commit = '<circle cx="12" cy="12" r="3.5"/><path d="M3 12h5.5M15.5 12H21"/>',
  branche = '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="7" r="2"/><path d="M6 7v10M18 9c0 5-6 4-11.2 8.6"/>',
  fusion = '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="12" r="2"/><path d="M6 7v10M6 7c0 4 5 5 10 5"/>',
  terminal = '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M13 15h4"/>',
  mission = '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
  alerte = '<path d="M12 3 2.5 20h19L12 3z"/><path d="M12 10v4M12 17.2v.1"/>',
  coche = '<path d="m4.5 12.5 4.5 4.5 10-10"/>',
  carnet = '<path d="M6 3h12a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6z"/><path d="M6 3v18M9.5 3v18M12.5 8h3.5M12.5 12h3.5"/>',
  equipe = '<circle cx="9" cy="8" r="3"/><path d="M3.5 19c.8-3.2 3-5 5.5-5s4.7 1.8 5.5 5"/><circle cx="17" cy="9" r="2.3"/><path d="M16 14.2c2.3.1 4 1.7 4.5 4.3"/>',
  serveur = '<rect x="4" y="4" width="16" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="16" height="6.5" rx="1.5"/><path d="M8 7.25h.01M8 16.75h.01"/>',
  fenetre = '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 8.5h18M9 8.5V20"/>',
  cadenas = '<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3"/>',
  etiquette = '<path d="M3.5 12.5V4.5a1 1 0 0 1 1-1h8l8 8-9 9-8-8z"/><circle cx="8.5" cy="8.5" r="1.5"/>',
  fleche = '<path d="M5 12h14M13 6l6 6-6 6"/>',
  fleche_g = '<path d="M19 12H5M11 6l-6 6 6 6"/>',
  horloge = '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  drapeau = '<path d="M5 21V4M5 4c3-1.5 6 1.5 9 0s4-1 5-.5v8c-1-.5-2-1-5 .5s-6-1.5-9 0"/>',
  loupe = '<circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5.5 5.5"/>',
  bulle = '<path d="M4 5h16v11H9l-5 4z"/>',
  engrenage = '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1"/>',
  livre = '<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H12v16H5.5A1.5 1.5 0 0 1 4 18.5zM20 5.5A1.5 1.5 0 0 0 18.5 4H12v16h6.5a1.5 1.5 0 0 0 1.5-1.5z"/>',
  croix = '<path d="M6 6l12 12M18 6 6 18"/>',
  retour = '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/>',
  eclair = '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
  crayon = '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
  personne = '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c1-3.5 3.8-5.5 7-5.5s6 2 7 5.5"/>',
  cible = '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r=".8"/>',
  boussole = '<circle cx="12" cy="12" r="8.5"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>',
}

function M.svg(nom, classe)
  local d = chemins[nom]
  if not d then return '' end
  return '<svg class="gf-icone ' .. (classe or '') .. '" viewBox="0 0 24 24" width="20" height="20" fill="none" '
    .. 'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
    .. 'aria-hidden="true" focusable="false">' .. d .. '</svg>'
end

return M
