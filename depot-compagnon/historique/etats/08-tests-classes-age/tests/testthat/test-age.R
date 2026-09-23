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
