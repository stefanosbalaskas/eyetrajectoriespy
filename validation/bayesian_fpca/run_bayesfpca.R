#!/usr/bin/env Rscript

# External bayesFPCA comparator runner for post-1.1 sensitivity evidence.
#
# This script uses only the documented public bayesFPCA API. No bayesFPCA
# implementation source is copied or translated into eyetrajectoriespy.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) {
  stop("usage: run_bayesfpca.R <evidence-directory>")
}

root <- normalizePath(args[[1]], mustWork = TRUE)
manifest <- read.csv(file.path(root, "manifest.csv"), stringsAsFactors = FALSE)

expected_sha <- Sys.getenv("BAYESFPCA_COMMIT")
if (!nzchar(expected_sha)) {
  stop("BAYESFPCA_COMMIT must be set")
}

if (!identical(as.character(utils::packageVersion("bayesFPCA")), "0.1.0")) {
  stop("unexpected bayesFPCA package version")
}

suppressPackageStartupMessages(library(bayesFPCA))

read_dimension <- function(path, ids) {
  frame <- read.csv(path, stringsAsFactors = FALSE)
  required <- c("curve_id", "time", "value")
  if (!all(required %in% names(frame))) {
    stop(sprintf("%s is missing required observation columns", path))
  }
  split_by_id <- function(column) {
    out <- lapply(ids, function(id) {
      values <- frame[frame$curve_id == id, column]
      as.numeric(values)
    })
    names(out) <- ids
    out
  }
  list(time = split_by_id("time"), value = split_by_id("value"))
}

write_mean <- function(path, time_g, mu_hat, dimensions) {
  mu <- as.matrix(mu_hat)
  if (nrow(mu) != length(time_g) || ncol(mu) != length(dimensions)) {
    stop("bayesFPCA mean shape does not match declared grid/dimensions")
  }
  frame <- data.frame(time = as.numeric(time_g))
  for (j in seq_along(dimensions)) {
    frame[[dimensions[[j]]]] <- as.numeric(mu[, j])
  }
  write.csv(frame, path, row.names = FALSE)
}

write_functions <- function(path, time_g, list_Psi_hat, dimensions, L) {
  rows <- list()
  index <- 1
  univariate_matrix <- length(dimensions) == 1 && is.matrix(list_Psi_hat)
  if (univariate_matrix &&
      (nrow(list_Psi_hat) != length(time_g) || ncol(list_Psi_hat) < L)) {
    stop("bayesFPCA univariate eigenfunction matrix has an unexpected shape")
  }
  for (l in seq_len(L)) {
    if (univariate_matrix) {
      psi <- matrix(list_Psi_hat[, l], ncol = 1)
    } else {
      psi <- as.matrix(list_Psi_hat[[l]])
    }
    if (nrow(psi) != length(time_g) || ncol(psi) != length(dimensions)) {
      stop("bayesFPCA eigenfunction shape does not match declared grid/dimensions")
    }
    for (j in seq_along(dimensions)) {
      rows[[index]] <- data.frame(
        component = l,
        dimension = dimensions[[j]],
        time = as.numeric(time_g),
        value = as.numeric(psi[, j])
      )
      index <- index + 1
    }
  }
  write.csv(do.call(rbind, rows), path, row.names = FALSE)
}

write_scores <- function(path, scores, ids, L) {
  scores <- as.matrix(scores)
  if (nrow(scores) != length(ids) || ncol(scores) < L) {
    stop("bayesFPCA score shape does not match fixture")
  }
  frame <- data.frame(curve_id = ids, stringsAsFactors = FALSE)
  for (l in seq_len(L)) {
    frame[[paste0("PC", l)]] <- as.numeric(scores[, l])
  }
  write.csv(frame, path, row.names = FALSE)
}

write_score_covariance <- function(path, covariances, ids, L) {
  rows <- list()
  index <- 1
  for (i in seq_along(ids)) {
    covariance <- as.matrix(covariances[[i]])
    if (!all(dim(covariance) >= c(L, L))) {
      stop("bayesFPCA score covariance shape does not match fixture")
    }
    for (a in seq_len(L)) {
      for (b in seq_len(L)) {
        rows[[index]] <- data.frame(
          curve_id = ids[[i]],
          component_i = a,
          component_j = b,
          covariance = as.numeric(covariance[a, b])
        )
        index <- index + 1
      }
    }
  }
  write.csv(do.call(rbind, rows), path, row.names = FALSE)
}

for (row_index in seq_len(nrow(manifest))) {
  entry <- manifest[row_index, ]
  scenario <- as.character(entry$scenario)
  design <- as.character(entry$design)
  L <- as.integer(entry$n_components)
  K_value <- as.integer(entry$spline_basis_size)
  scenario_dir <- file.path(root, "scenarios", scenario)

  truth <- read.csv(file.path(scenario_dir, "truth_grid.csv"))
  time_g <- as.numeric(truth$time)
  x_frame <- read.csv(
    file.path(scenario_dir, "observations_x.csv"),
    stringsAsFactors = FALSE
  )
  ids <- unique(as.character(x_frame$curve_id))
  x <- read_dimension(file.path(scenario_dir, "observations_x.csv"), ids)

  if (identical(design, "univariate")) {
    time_obs <- x$time
    Y <- x$value
    K <- K_value
    dimensions <- c("x")
  } else {
    y <- read_dimension(file.path(scenario_dir, "observations_y.csv"), ids)
    time_obs <- lapply(seq_along(ids), function(i) {
      list(x$time[[i]], y$time[[i]])
    })
    Y <- lapply(seq_along(ids), function(i) {
      list(x$value[[i]], y$value[[i]])
    })
    names(time_obs) <- ids
    names(Y) <- ids
    for (i in seq_along(ids)) {
      names(time_obs[[i]]) <- c("x", "y")
      names(Y[[i]]) <- c("x", "y")
    }
    K <- rep(K_value, 2)
    dimensions <- c("x", "y")
  }

  names(time_obs) <- ids
  names(Y) <- ids
  set.seed(41000 + row_index)

  elapsed <- system.time({
    result <- run_mfvb_fpca(
      time_obs = time_obs,
      Y = Y,
      L = L,
      K = K,
      tol = 1e-4,
      maxit = 1500,
      rel_crit = TRUE,
      plot_elbo = FALSE,
      n_g = NULL,
      time_g = time_g,
      fixed_score_variance = TRUE,
      verbose = FALSE,
      seed = 51000 + row_index,
      check_elbo = TRUE
    )
  })

  result_time <- as.numeric(result$time_g)
  if (length(result_time) != length(time_g) ||
      max(abs(result_time - time_g)) > 1e-12) {
    stop("bayesFPCA did not retain the declared evaluation grid")
  }

  write_mean(
    file.path(scenario_dir, "bayesfpca_mean.csv"),
    result_time,
    result$mu_hat,
    dimensions
  )
  write_functions(
    file.path(scenario_dir, "bayesfpca_eigenfunctions.csv"),
    result_time,
    result$list_Psi_hat,
    dimensions,
    L
  )
  write_scores(
    file.path(scenario_dir, "bayesfpca_scores.csv"),
    result$Zeta_hat,
    ids,
    L
  )
  write.csv(
    data.frame(
      component = seq_len(L),
      eigenvalue = as.numeric(result$eigenvalues[seq_len(L)])
    ),
    file.path(scenario_dir, "bayesfpca_eigenvalues.csv"),
    row.names = FALSE
  )
  write_score_covariance(
    file.path(scenario_dir, "bayesfpca_score_covariance.csv"),
    result$Cov_zeta_hat,
    ids,
    L
  )

  elbo <- as.numeric(result$elbo)
  final_elbo <- if (length(elbo)) tail(elbo, 1) else NA_real_
  write.csv(
    data.frame(
      scenario = scenario,
      algorithm = "run_mfvb_fpca",
      package_version = as.character(utils::packageVersion("bayesFPCA")),
      remote_sha = expected_sha,
      elapsed_seconds = as.numeric(elapsed[["elapsed"]]),
      n_iter = as.integer(result$n_iter),
      final_elbo = final_elbo,
      fixed_score_variance = TRUE,
      stringsAsFactors = FALSE
    ),
    file.path(scenario_dir, "bayesfpca_metadata.csv"),
    row.names = FALSE
  )
}
