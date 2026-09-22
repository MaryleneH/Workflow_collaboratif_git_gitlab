# Taux de recrutement par métier, pour le panorama annuel

taux_recrutement_metier <- function(annee) {
  rec <- read.csv("/home/tom/Documents/extractions/recrutements_2025.csv")
  sal <- read.csv("data/prepare/salaries_champ.csv")

  effectifs <- sal |>
    dplyr::filter(millesime == annee) |>
    dplyr::count(id_etab, metier, name = "effectif")

  rec |>
    dplyr::filter(millesime == annee) |>
    dplyr::mutate(recrutements = ifelse(is.na(recrutements), 0, recrutements)) |>
    dplyr::inner_join(effectifs, by = c("id_etab", "metier")) |>
    dplyr::filter(effectif >= 10) |>
    dplyr::group_by(metier) |>
    dplyr::summarise(taux = mean(recrutements / effectif), .groups = "drop")
}

intervalle_taux <- function(taux_etab, n_boot = 1000) {
  estimations <- replicate(n_boot, mean(sample(taux_etab, replace = TRUE)))
  quantile(estimations, c(0.025, 0.975))
}
