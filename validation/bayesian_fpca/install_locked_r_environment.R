#!/usr/bin/env Rscript

# Executable environment lock for the external bayesFPCA comparator.
#
# R itself is pinned by actions/setup-r in the workflow. This script installs
# exact source releases for the non-recommended CRAN Imports used by the pinned
# bayesFPCA checkout. It first tries the current src/contrib location and then
# the CRAN Archive location, so future reruns do not silently upgrade packages.

options(repos = c(CRAN = "https://cloud.r-project.org"))

locked <- list(
  ellipse = list(version = "0.5.0", tarball = "ellipse_0.5.0.tar.gz"),
  magic = list(version = "1.6.1.1", tarball = "magic_1.6-1-1.tar.gz"),
  matrixcalc = list(version = "1.0.6", tarball = "matrixcalc_1.0-6.tar.gz"),
  pracma = list(version = "2.4.6", tarball = "pracma_2.4.6.tar.gz")
)

download_exact <- function(package, tarball) {
  candidates <- c(
    sprintf("https://cloud.r-project.org/src/contrib/%s", tarball),
    sprintf(
      "https://cloud.r-project.org/src/contrib/Archive/%s/%s",
      package,
      tarball
    )
  )
  destination <- file.path(tempdir(), tarball)
  for (url in candidates) {
    status <- try(
      utils::download.file(
        url,
        destination,
        mode = "wb",
        quiet = TRUE
      ),
      silent = TRUE
    )
    if (!inherits(status, "try-error") && file.exists(destination)) {
      return(destination)
    }
  }
  stop(sprintf("could not retrieve locked source tarball %s", tarball))
}

for (package in names(locked)) {
  spec <- locked[[package]]
  tarball <- download_exact(package, spec$tarball)
  utils::install.packages(
    tarball,
    repos = NULL,
    type = "source",
    quiet = TRUE
  )
  installed <- as.character(utils::packageVersion(package))
  if (!identical(installed, spec$version)) {
    stop(
      sprintf(
        "%s version mismatch: expected %s, got %s",
        package,
        spec$version,
        installed
      )
    )
  }
}

expected_recommended <- c(
  MASS = "7.3.65",
  lattice = "0.22.9"
)
for (package in names(expected_recommended)) {
  installed <- as.character(utils::packageVersion(package))
  if (!identical(installed, expected_recommended[[package]])) {
    stop(
      sprintf(
        "%s recommended-package version mismatch: expected %s, got %s",
        package,
        expected_recommended[[package]],
        installed
      )
    )
  }
}

locked_versions <- vapply(
  locked,
  function(spec) spec$version,
  character(1)
)
write.csv(
  data.frame(
    package = c(names(locked), names(expected_recommended)),
    version = c(locked_versions, unname(expected_recommended)),
    stringsAsFactors = FALSE
  ),
  file = "bayesian-fpca-b2-b3/r-environment-lock-resolved.csv",
  row.names = FALSE
)
