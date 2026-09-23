# Calcul des indicateurs du panorama pour un millésime.
#
# Usage   : Rscript scripts/03_indicateurs.R 2025   (depuis la racine du projet)
# Entrées : data/prepare/salaries_champ.csv et data/prepare/recrutements.csv
#           (produits par scripts/02_preparer.py)
# Sorties : resultats/indicateurs_<millesime>.csv (format long :
#           indicateur, dimension, modalite, valeur)
#           resultats/pyramide_<millesime>.csv

source(file.path("R", "age.R"))
source(file.path("R", "indicateurs.R"))

args <- commandArgs(trailingOnly = TRUE)
millesime <- if (length(args) >= 1) as.integer(args[[1]]) else 2025L

salaries <- utils::read.csv(
  file.path("data", "prepare", "salaries_champ.csv"),
  colClasses = c(pcs = "character", region = "character"),
  encoding = "UTF-8"
)
if (!all(salaries$millesime == millesime)) {
  stop("data/prepare/ ne contient pas le millésime ", millesime,
       " : relancez scripts/02_preparer.py --millesime ", millesime)
}
salaries$age <- age_au_31_decembre(salaries$date_naissance, millesime)
salaries$classe_age <- classe_age(salaries$age)

# Met une colonne d'une table au format long : indicateur, dimension, modalite, valeur.
en_ligne <- function(table, colonne, indicateur, dimension = "ensemble") {
  modalite <- if (dimension == "ensemble") "ensemble" else as.character(table[[dimension]])
  data.frame(
    indicateur = indicateur,
    dimension = dimension,
    modalite = modalite,
    valeur = table[[colonne]]
  )
}

# -- Effectifs et âges ---------------------------------------------------------
indicateurs <- list(
  data.frame(indicateur = "salaries", dimension = "ensemble", modalite = "ensemble",
             valeur = nrow(salaries)),
  data.frame(indicateur = "etablissements", dimension = "ensemble", modalite = "ensemble",
             valeur = length(unique(salaries$id_etab))),
  en_ligne(part_seniors(salaries), "part_seniors", "part_55_plus"),
  en_ligne(part_seniors(salaries, sous_filiere), "part_seniors", "part_55_plus", "sous_filiere")
)
pyramide <- pyramide_ages(salaries)

# -- Grandes catégories de PCS -------------------------------------------------
parts_pcs <- repartition_pcs(salaries)
ouvriers <- parts_pcs[parts_pcs$groupe_pcs == "ouvrier", ]
indicateurs <- c(indicateurs, list(
  data.frame(indicateur = "part_etab_ouvriers", dimension = "ensemble", modalite = "ensemble",
             valeur = sum(ouvriers$part > 0.5) / length(unique(parts_pcs$id_etab)))
))

# -- Recrutements --------------------------------------------------------------
recrutements <- utils::read.csv(file.path("data", "prepare", "recrutements.csv"),
                                encoding = "UTF-8")
effectifs <- dplyr::count(salaries, id_etab, metier, name = "effectif")
taux_ensemble <- taux_recrutement(recrutements, effectifs)
taux_metier <- taux_recrutement(recrutements, effectifs, metier)
indicateurs <- c(indicateurs, list(
  en_ligne(taux_ensemble, "taux_recrutement", "taux_recrutement"),
  en_ligne(taux_ensemble, "taux_reponse", "taux_reponse"),
  en_ligne(taux_metier, "taux_recrutement", "taux_recrutement", "metier"),
  en_ligne(taux_metier, "taux_reponse", "taux_reponse", "metier")
))

# -- Écriture ------------------------------------------------------------------
indicateurs <- do.call(rbind, indicateurs)
dir.create("resultats", showWarnings = FALSE)
utils::write.csv(indicateurs, file.path("resultats", sprintf("indicateurs_%d.csv", millesime)),
                 row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(pyramide, file.path("resultats", sprintf("pyramide_%d.csv", millesime)),
                 row.names = FALSE, fileEncoding = "UTF-8")
message(nrow(indicateurs), " indicateurs écrits dans resultats/ pour le millésime ", millesime)
