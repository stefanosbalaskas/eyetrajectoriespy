args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L) {
  stop("usage: Rscript validation/pre012/run_mgsfpca.R <audit-output-dir>")
}

output_dir <- normalizePath(args[[1]], mustWork = TRUE)

if (!requireNamespace("mGSFPCA", quietly = TRUE)) {
  stop("mGSFPCA is not installed; install exact CRAN version 0.2.2")
}
if (as.character(utils::packageVersion("mGSFPCA")) != "0.2.2") {
  stop("pre-0.12 comparator requires mGSFPCA 0.2.2 exactly")
}

x <- utils::read.csv(file.path(output_dir, "external_fixture_x.csv"))
y <- utils::read.csv(file.path(output_dir, "external_fixture_y.csv"))

required <- c("ID", "time", "value")
if (!identical(names(x), required) || !identical(names(y), required)) {
  stop("external fixtures must contain exactly ID, time, value columns")
}

fit <- mGSFPCA::spMultFPCA(
  dataCell = list(x, y),
  r = list(2L, 2L),
  G = list(8L, 8L),
  basis_type = c("bspline", "bspline"),
  nRegGrid = 51L,
  grid_range = list(c(0, 1), c(0, 1)),
  mu_nbasis = 8L,
  M_npc = 4L,
  maxit = 500L,
  optim_tol = 1e-5,
  bin_size = 51L
)

if (is.null(fit$values) || is.null(fit$scores)) {
  stop("mGSFPCA output does not expose expected values/scores fields")
}

utils::write.csv(
  data.frame(component = seq_along(fit$values), eigenvalue = fit$values),
  file.path(output_dir, "mgsfpca_eigenvalues.csv"),
  row.names = FALSE
)
utils::write.csv(
  as.data.frame(fit$scores),
  file.path(output_dir, "mgsfpca_scores.csv"),
  row.names = FALSE
)

if (!is.null(fit$eigFunctions) && length(fit$eigFunctions) == 2L) {
  utils::write.csv(
    as.data.frame(fit$eigFunctions[[1]]),
    file.path(output_dir, "mgsfpca_eigenfunctions_x.csv"),
    row.names = FALSE
  )
  utils::write.csv(
    as.data.frame(fit$eigFunctions[[2]]),
    file.path(output_dir, "mgsfpca_eigenfunctions_y.csv"),
    row.names = FALSE
  )
}

writeLines(
  c(
    "comparator=mGSFPCA",
    paste0("version=", as.character(utils::packageVersion("mGSFPCA"))),
    "function=spMultFPCA",
    "equivalence_claim=false",
    "rank_and_basis_selection=explicit"
  ),
  file.path(output_dir, "mgsfpca_run_metadata.txt")
)
