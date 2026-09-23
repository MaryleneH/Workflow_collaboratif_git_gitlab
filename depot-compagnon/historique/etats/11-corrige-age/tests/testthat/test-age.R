# Tests du calcul de l'âge et des classes d'âge (R/age.R)

test_that("classe_age respecte les bornes des classes quinquennales", {
  expect_equal(
    as.character(classe_age(c(18, 24, 25, 29, 50, 54, 55, 59, 60, 66))),
    c(
      "moins de 25 ans", "moins de 25 ans", "25-29 ans", "25-29 ans", "50-54 ans",
      "50-54 ans", "55-59 ans", "55-59 ans", "60 ans ou plus", "60 ans ou plus"
    )
  )
})

test_that("classe_age renvoie un facteur ordonné de neuf classes", {
  classes <- classe_age(c(30, 45))
  expect_true(is.ordered(classes))
  expect_length(levels(classes), 9)
})

test_that("classe_age conserve les âges manquants", {
  expect_true(is.na(classe_age(NA_real_)))
})

test_that("l'âge est calculé au 31 décembre de l'année de référence (#7)", {
  # Née le 15 mars 1971 : 54 ans au 31 décembre 2025, mais 55 ans au 30 juin 2026.
  expect_equal(age_au_31_decembre("1971-03-15", 2025), 54L)
  expect_equal(age_au_31_decembre("1970-12-31", 2025), 55L)
})
