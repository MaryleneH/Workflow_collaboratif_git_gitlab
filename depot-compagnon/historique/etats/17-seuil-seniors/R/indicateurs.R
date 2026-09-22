# Indicateurs du panorama. Chaque fonction prend une table de salariés
# (une ligne par salarié présent au 31 décembre) et renvoie une table.

#' Part des salariés de 55 ans ou plus
#'
#' @param salaries table des salariés, avec une colonne `age` (âge au 31 décembre).
#' @param ... variables de regroupement, par exemple `sous_filiere`.
#' @param seuil âge à partir duquel un salarié est compté comme senior (toujours nommé).
#' @return une ligne par groupe, avec la colonne `part_seniors`.
part_seniors <- function(salaries, ..., seuil = 55) {
  salaries |>
    dplyr::group_by(...) |>
    dplyr::summarise(part_seniors = mean(age >= seuil), .groups = "drop")
}

#' Pyramide des âges par sexe
#'
#' @param salaries table des salariés, avec les colonnes `classe_age` et `sexe`.
#' @return une ligne par classe d'âge et par sexe, avec l'effectif et la part.
pyramide_ages <- function(salaries) {
  salaries |>
    dplyr::count(classe_age, sexe, name = "effectif") |>
    dplyr::mutate(part = effectif / sum(effectif)) |>
    dplyr::arrange(classe_age, sexe)
}

#' Répartition des salariés par PCS dans chaque établissement
#'
#' @param salaries table des salariés, avec les colonnes `id_etab` et `pcs`.
#' @return une ligne par établissement et par PCS, avec l'effectif et la part ;
#'   dans chaque établissement, les parts somment à 1.
repartition_pcs <- function(salaries) {
  salaries |>
    dplyr::count(id_etab, pcs, name = "effectif") |>
    dplyr::group_by(id_etab) |>
    dplyr::mutate(part = effectif / sum(effectif)) |>
    dplyr::ungroup()
}
