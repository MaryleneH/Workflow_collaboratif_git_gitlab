# Charge les fonctions du projet (R/*.R) avant l'exécution des tests.
# Lancer les tests depuis la racine : Rscript -e 'testthat::test_dir("tests/testthat")'
racine_projet <- normalizePath(file.path(testthat::test_path(), "..", ".."))
for (fichier in list.files(file.path(racine_projet, "R"), pattern = "[.]R$", full.names = TRUE)) {
  source(fichier, encoding = "UTF-8")
}
