# Indicateurs du panorama. Chaque fonction prend une table de salariés
# (une ligne par salarié présent au 31 décembre) et renvoie une table.

#' Part des salariés de 55 ans ou plus
#'
#' Les apprentis sont exclus du champ de l'indicateur (#13) : très jeunes et en
#' forte hausse dans certaines sous-filières, ils faussent les comparaisons.
#' La fonction renvoie aussi l'effectif du champ retenu.
#'
#' @param salaries table des salariés, avec une colonne `age` (âge au 31 décembre).
#' @param ... variables de regroupement, par exemple `sous_filiere`.
#' @param seuil âge à partir duquel un salarié est compté comme senior (toujours nommé).
#' @return une ligne par groupe, avec la colonne `part_seniors`.
part_seniors <- function(salaries, ..., seuil = 55) {
  salaries |>
    dplyr::filter(contrat != "apprenti") |>
    dplyr::group_by(...) |>
    dplyr::summarise(effectif = dplyr::n(), part_seniors = mean(age >= seuil), .groups = "drop")
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

#' Taux de recrutement
#'
#' Rapport des sommes : recrutements de l'année / effectif au 31 décembre, sur les
#' seuls établissements répondants. Chaque établissement pèse donc selon son
#' effectif. Les non-réponses (NA) sont exclues, et non remplacées par zéro ; le
#' taux de réponse (part de l'effectif couverte par les répondants) accompagne
#' toujours le taux.
#'
#' @param recrutements table `id_etab`, `metier`, `recrutements` (NA si non-réponse).
#' @param effectifs table `id_etab`, `metier`, `effectif`.
#' @param ... variables de regroupement, par exemple `metier`.
#' @return une ligne par groupe : `etablissements`, `taux_reponse`, `taux_recrutement`.
taux_recrutement <- function(recrutements, effectifs, ...) {
  recrutements |>
    dplyr::inner_join(effectifs, by = c("id_etab", "metier")) |>
    dplyr::group_by(...) |>
    dplyr::summarise(
      etablissements = dplyr::n_distinct(id_etab),
      taux_reponse = sum(effectif[!is.na(recrutements)]) / sum(effectif),
      taux_recrutement = sum(recrutements, na.rm = TRUE) / sum(effectif[!is.na(recrutements)]),
      .groups = "drop"
    )
}

#' Répartition des établissements par région
#'
#' @param salaries table des salariés, avec les colonnes `id_etab` et `region`.
#' @return une ligne par région, avec le nombre d'établissements et leur part.
etablissements_par_region <- function(salaries) {
  salaries |>
    dplyr::distinct(id_etab, region) |>
    dplyr::count(region, name = "etablissements") |>
    dplyr::mutate(part = etablissements / sum(etablissements))
}
