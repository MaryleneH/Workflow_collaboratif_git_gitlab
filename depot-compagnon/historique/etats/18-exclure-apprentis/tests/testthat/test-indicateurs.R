test_that("part_seniors compte les salariés de 55 ans ou plus", {
  jeu <- data.frame(
    sous_filiere = c("naval", "naval", "naval", "électronique de défense"),
    age = c(54, 55, 61, 40),
    contrat = "CDI"
  )
  res <- part_seniors(jeu, sous_filiere)
  expect_equal(res$part_seniors[res$sous_filiere == "naval"], 2 / 3)
  expect_equal(res$part_seniors[res$sous_filiere != "naval"], 0)
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
