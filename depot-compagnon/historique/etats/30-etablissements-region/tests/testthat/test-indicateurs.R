test_that("part_seniors applique le seuil et exclut les apprentis", {
  jeu <- data.frame(
    sous_filiere = "naval",
    age = c(52, 58, 30, 60),
    contrat = c("CDI", "CDI", "CDI", "apprenti")
  )
  res <- part_seniors(jeu, sous_filiere, seuil = 50)
  expect_equal(res$effectif, 3)
  expect_equal(res$part_seniors, 2 / 3)
})

test_that("part_seniors applique le seuil demandé", {
  jeu <- data.frame(age = c(30, 50, 54, 55, 61), contrat = "CDI")
  expect_equal(part_seniors(jeu)$part_seniors, 2 / 5)
  expect_equal(part_seniors(jeu, seuil = 50)$part_seniors, 4 / 5)
})

test_that("les parts par PCS somment à 1 dans chaque établissement", {
  jeu <- data.frame(
    id_etab = rep(c("ETB-00001", "ETB-00002"), times = c(6, 4)),
    pcs = c("37", "47", "62", "62", "67", "67", "54", "62", "62", "67")
  )
  sommes <- repartition_pcs(jeu) |>
    dplyr::summarise(total = sum(part), .by = id_etab)
  expect_equal(sommes$total, rep(1, nrow(sommes)))
})

test_that("repartition_pcs compte chaque salarié une fois", {
  jeu <- data.frame(
    id_etab = rep(c("ETB-00001", "ETB-00002"), times = c(6, 4)),
    pcs = c("37", "47", "62", "62", "67", "67", "54", "62", "62", "67")
  )
  expect_equal(sum(repartition_pcs(jeu)$effectif), nrow(jeu))
})

test_that("part_seniors exclut les apprentis et renvoie l'effectif", {
  jeu <- data.frame(
    age = c(19, 22, 56, 60, 40),
    contrat = c("apprenti", "apprenti", "CDI", "CDI", "CDD")
  )
  res <- part_seniors(jeu)
  expect_equal(res$effectif, 3)
  expect_equal(res$part_seniors, 2 / 3)
})

test_that("taux_recrutement est un rapport des sommes, hors non-réponses", {
  recrutements <- data.frame(
    id_etab = c("ETB-00001", "ETB-00002", "ETB-00003"),
    metier = "soudeur·se",
    recrutements = c(6, 100, NA)
  )
  effectifs <- data.frame(
    id_etab = c("ETB-00001", "ETB-00002", "ETB-00003"),
    metier = "soudeur·se",
    effectif = c(12, 2000, 88)
  )
  res <- taux_recrutement(recrutements, effectifs, metier)
  expect_equal(res$taux_recrutement, 106 / 2012)
  expect_equal(res$taux_reponse, 2012 / 2100)
})

test_that("etablissements_par_region compte chaque établissement une fois", {
  jeu <- data.frame(
    id_etab = c("ETB-00001", "ETB-00001", "ETB-00002", "ETB-00003"),
    region = c("76", "76", "76", "53")
  )
  res <- etablissements_par_region(jeu)
  expect_equal(res$etablissements[res$region == "76"], 2)
  expect_equal(sum(res$part), 1)
})
