# Calcul de l'âge des salariés et des classes d'âge du panorama.

#' Âge en années révolues à une date de référence
#'
#' @param date_naissance vecteur de dates de naissance (Date ou "AAAA-MM-JJ").
#' @param date_reference date à laquelle l'âge est calculé.
#' @return un vecteur d'entiers.
age_revolu <- function(date_naissance, date_reference) {
  date_naissance <- as.Date(date_naissance)
  date_reference <- as.Date(date_reference)
  annees <- as.integer(format(date_reference, "%Y")) -
    as.integer(format(date_naissance, "%Y"))
  pas_encore <- format(date_reference, "%m%d") < format(date_naissance, "%m%d")
  annees - as.integer(pas_encore)
}

#' Âge des salariés en fin d'année
#'
#' @param date_naissance vecteur de dates de naissance.
#' @param annee millésime des données (année de référence).
#' @return un vecteur d'entiers.
age_fin_annee <- function(date_naissance, annee) {
  date_reference <- as.Date(paste0(annee + 1, "-06-30")) # date d'extraction des fichiers
  age_revolu(date_naissance, date_reference)
}

#' Classe d'âge quinquennale utilisée dans le panorama
#'
#' @param age vecteur d'âges en années révolues.
#' @return un facteur ordonné (NA si l'âge est manquant).
classe_age <- function(age) {
  cut(
    age,
    breaks = c(-Inf, 25, 30, 35, 40, 45, 50, 55, 60, Inf),
    labels = c(
      "moins de 25 ans", "25-29 ans", "30-34 ans", "35-39 ans", "40-44 ans",
      "45-49 ans", "50-54 ans", "55-59 ans", "60 ans ou plus"
    ),
    right = FALSE,
    ordered_result = TRUE
  )
}
