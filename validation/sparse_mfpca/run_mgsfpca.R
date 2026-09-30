args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L) {
  stop("usage: Rscript validation/sparse_mfpca/run_mgsfpca.R <output-dir>")
}

output_dir <- normalizePath(args[[1]], mustWork = TRUE)

if (!requireNamespace("mGSFPCA", quietly = TRUE)) {
  stop("mGSFPCA is not installed; install exact CRAN version 0.2.2")
}
if (as.character(utils::packageVersion("mGSFPCA")) != "0.2.2") {
  stop("0.12 comparator sensitivity requires mGSFPCA 0.2.2 exactly")
}

x <- utils::read.csv(
  file.path(output_dir, "external_fixture_x.csv"),
  stringsAsFactors = FALSE,
  check.names = FALSE
)
y <- utils::read.csv(
  file.path(output_dir, "external_fixture_y.csv"),
  stringsAsFactors = FALSE,
  check.names = FALSE
)

required <- c("ID", "time", "value")
if (!identical(names(x), required) || !identical(names(y), required)) {
  stop("external fixtures must contain exactly ID, time, value columns")
}

original_ids <- unique(as.character(x$ID))
if (length(original_ids) == 0L) {
  stop("external fixture contains no curve IDs")
}
if (!setequal(original_ids, unique(as.character(y$ID)))) {
  stop("x/y external fixtures must contain the same curve IDs")
}

id_mapping <- data.frame(
  original_ID = original_ids,
  numeric_ID = seq_along(original_ids),
  stringsAsFactors = FALSE
)
id_lookup <- stats::setNames(id_mapping$numeric_ID, id_mapping$original_ID)

adapt_fixture <- function(frame, label) {
  original <- as.character(frame$ID)
  if (any(!original %in% names(id_lookup))) {
    stop(paste0(label, " fixture contains an unmapped curve ID"))
  }
  adapted <- data.frame(
    ID = unname(id_lookup[original]),
    time = suppressWarnings(as.numeric(frame$time)),
    value = suppressWarnings(as.numeric(frame$value))
  )
  if (anyNA(adapted) || any(!is.finite(adapted$time)) ||
      any(!is.finite(adapted$value))) {
    stop(paste0(label, " fixture contains non-finite numeric time/value data"))
  }
  adapted
}

x_fit <- adapt_fixture(x, "x")
y_fit <- adapt_fixture(y, "y")

utils::write.csv(
  id_mapping,
  file.path(output_dir, "mgsfpca_id_mapping.csv"),
  row.names = FALSE
)

fit <- mGSFPCA::spMultFPCA(
  dataCell = list(x_fit, y_fit),
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
if (is.null(fit$eigFunctions) || length(fit$eigFunctions) != 2L) {
  stop("mGSFPCA output does not expose two eigenfunction channels")
}

utils::write.csv(
  data.frame(component = seq_along(fit$values), eigenvalue = fit$values),
  file.path(output_dir, "mgsfpca_eigenvalues.csv"),
  row.names = FALSE
)

if (length(original_ids) != nrow(fit$scores)) {
  stop("mGSFPCA score row count does not match fixture subject count")
}
utils::write.csv(
  data.frame(ID = original_ids, as.data.frame(fit$scores)),
  file.path(output_dir, "mgsfpca_scores.csv"),
  row.names = FALSE
)

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

writeLines(
  c(
    "comparator=mGSFPCA",
    paste0("version=", as.character(utils::packageVersion("mGSFPCA"))),
    "function=spMultFPCA",
    "equivalence_claim=false",
    "architecture_winner_selected=false",
    "rank_and_basis_selection=explicit",
    "id_adapter=original_curve_id_to_contiguous_integer",
    "id_mapping=mgsfpca_id_mapping.csv"
  ),
  file.path(output_dir, "mgsfpca_run_metadata.txt")
)
