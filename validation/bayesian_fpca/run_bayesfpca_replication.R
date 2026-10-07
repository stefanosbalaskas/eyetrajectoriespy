#!/usr/bin/env Rscript

# External bayesFPCA runner for B2 replicated recovery and K sensitivity.
#
# The upstream GPL implementation remains isolated in the dedicated evidence
# workflow. This adapter uses documented public APIs and neutral CSV inputs.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) {
  stop("usage: run_bayesfpca_replication.R <evidence-directory>")
}

root <- normalizePath(args[[1]], mustWork = TRUE)
manifest <- read.csv(
  file.path(root, "manifest.csv"),
  stringsAsFactors = FALSE
)

expected_sha <- Sys.getenv("BAYESFPCA_COMMIT")
if (!nzchar(expected_sha)) {
  stop("BAYESFPCA_COMMIT must be set")
}
if (!identical(
  as.character(utils::packageVersion("bayesFPCA")),
  "0.1.0"
)) {
  stop("unexpected bayesFPCA package version")
}

suppressPackageStartupMessages(library(bayesFPCA))


read_dimension <- function(path, ids) {
  frame <- read.csv(path, stringsAsFactors = FALSE)
  required <- c("curve_id", "time", "value")
  if (!all(required %in% names(frame))) {
    stop(sprintf("%s is missing required observation columns", path))
  }

  times <- lapply(ids, function(id) {
    as.numeric(frame[frame$curve_id == id, "time"])
  })
  values <- lapply(ids, function(id) {
    as.numeric(frame[frame$curve_id == id, "value"])
  })
  names(times) <- names(values) <- ids
  list(time = times, value = values)
}


write_mean <- function(path, time_g, mu_hat, dimensions) {
  mu <- as.matrix(mu_hat)
  if (
    nrow(mu) != length(time_g) ||
    ncol(mu) != length(dimensions)
  ) {
    stop("bayesFPCA mean shape does not match declared grid/dimensions")
  }

  frame <- data.frame(time = as.numeric(time_g))
  for (j in seq_along(dimensions)) {
    frame[[dimensions[[j]]]] <- as.numeric(mu[, j])
  }
  write.csv(frame, path, row.names = FALSE)
}


write_functions <- function(
  path,
  time_g,
  list_Psi_hat,
  dimensions,
  L
) {
  rows <- list()
  index <- 1
  univariate_matrix <- (
    length(dimensions) == 1 &&
    is.matrix(list_Psi_hat)
  )

  if (
    univariate_matrix &&
    (
      nrow(list_Psi_hat) != length(time_g) ||
      ncol(list_Psi_hat) < L
    )
  ) {
    stop("bayesFPCA univariate eigenfunction matrix has an unexpected shape")
  }

  for (l in seq_len(L)) {
    if (univariate_matrix) {
      psi <- matrix(list_Psi_hat[, l], ncol = 1)
    } else {
      psi <- as.matrix(list_Psi_hat[[l]])
    }
    if (
      nrow(psi) != length(time_g) ||
      ncol(psi) != length(dimensions)
    ) {
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

  write.csv(
    do.call(rbind, rows),
    path,
    row.names = FALSE
  )
}


write_scores <- function(path, scores, ids, L) {
  scores <- as.matrix(scores)
  if (
    nrow(scores) != length(ids) ||
    ncol(scores) < L
  ) {
    stop("bayesFPCA score shape does not match fixture")
  }

  frame <- data.frame(
    curve_id = ids,
    stringsAsFactors = FALSE
  )
  for (l in seq_len(L)) {
    frame[[paste0("PC", l)]] <- as.numeric(scores[, l])
  }
  write.csv(frame, path, row.names = FALSE)
}


write_covariance <- function(
  path,
  covariances,
  ids,
  L
) {
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

  write.csv(
    do.call(rbind, rows),
    path,
    row.names = FALSE
  )
}


write_fit <- function(
  scenario_dir,
  prefix,
  result,
  ids,
  dimensions,
  L,
  elapsed,
  K
) {
  time_g <- as.numeric(result$time_g)
  write_mean(
    file.path(
      scenario_dir,
      paste0(prefix, "_mean.csv")
    ),
    time_g,
    result$mu_hat,
    dimensions
  )
  write_functions(
    file.path(
      scenario_dir,
      paste0(prefix, "_eigenfunctions.csv")
    ),
    time_g,
    result$list_Psi_hat,
    dimensions,
    L
  )
  write_scores(
    file.path(
      scenario_dir,
      paste0(prefix, "_scores.csv")
    ),
    result$Zeta_hat,
    ids,
    L
  )
  write.csv(
    data.frame(
      component = seq_len(L),
      eigenvalue = as.numeric(
        result$eigenvalues[seq_len(L)]
      )
    ),
    file.path(
      scenario_dir,
      paste0(prefix, "_eigenvalues.csv")
    ),
    row.names = FALSE
  )
  write_covariance(
    file.path(
      scenario_dir,
      paste0(prefix, "_score_covariance.csv")
    ),
    result$Cov_zeta_hat,
    ids,
    L
  )

  elbo <- as.numeric(result$elbo)
  write.csv(
    data.frame(
      status = "ok",
      K = as.integer(K),
      elapsed_seconds = as.numeric(elapsed),
      n_iter = as.integer(result$n_iter),
      final_elbo = if (length(elbo)) {
        tail(elbo, 1)
      } else {
        NA_real_
      },
      stringsAsFactors = FALSE
    ),
    file.path(
      scenario_dir,
      paste0(prefix, "_status.csv")
    ),
    row.names = FALSE
  )
}


write_failure <- function(
  scenario_dir,
  prefix,
  err,
  elapsed,
  K = NA_integer_
) {
  write.csv(
    data.frame(
      status = "failed",
      K = K,
      elapsed_seconds = as.numeric(elapsed),
      n_iter = NA_integer_,
      final_elbo = NA_real_,
      error = conditionMessage(err),
      stringsAsFactors = FALSE
    ),
    file.path(
      scenario_dir,
      paste0(prefix, "_status.csv")
    ),
    row.names = FALSE
  )
}


prepare_input <- function(scenario_dir, design) {
  x_frame <- read.csv(
    file.path(
      scenario_dir,
      "observations_x.csv"
    ),
    stringsAsFactors = FALSE
  )
  ids <- unique(as.character(x_frame$curve_id))
  x <- read_dimension(
    file.path(
      scenario_dir,
      "observations_x.csv"
    ),
    ids
  )

  if (identical(design, "univariate")) {
    names(x$time) <- names(x$value) <- ids
    return(
      list(
        ids = ids,
        time_obs = x$time,
        Y = x$value,
        dimensions = c("x")
      )
    )
  }

  y <- read_dimension(
    file.path(
      scenario_dir,
      "observations_y.csv"
    ),
    ids
  )
  time_obs <- lapply(seq_along(ids), function(i) {
    list(x$time[[i]], y$time[[i]])
  })
  Y <- lapply(seq_along(ids), function(i) {
    list(x$value[[i]], y$value[[i]])
  })
  names(time_obs) <- names(Y) <- ids

  for (i in seq_along(ids)) {
    names(time_obs[[i]]) <- c("x", "y")
    names(Y[[i]]) <- c("x", "y")
  }

  list(
    ids = ids,
    time_obs = time_obs,
    Y = Y,
    dimensions = c("x", "y")
  )
}


run_one <- function(
  time_obs,
  Y,
  L,
  K,
  time_g,
  seed
) {
  run_mfvb_fpca(
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
    seed = seed,
    check_elbo = TRUE
  )
}


for (row_index in seq_len(nrow(manifest))) {
  row <- manifest[row_index, ]
  scenario <- as.character(row$scenario)
  replicate <- as.integer(row$replicate)
  design <- as.character(row$design)
  L <- as.integer(row$n_components)
  K_fixed <- as.integer(row$spline_basis_size)

  scenario_dir <- file.path(
    root,
    "scenarios",
    scenario,
    sprintf("replicate_%03d", replicate)
  )
  time_g <- as.numeric(
    read.csv(
      file.path(
        scenario_dir,
        "truth_grid.csv"
      )
    )$time
  )
  input <- prepare_input(
    scenario_dir,
    design
  )

  fixed_seed <- 610000 + row_index
  start <- proc.time()[[3]]
  result <- tryCatch(
    run_one(
      input$time_obs,
      input$Y,
      L,
      K_fixed,
      time_g,
      fixed_seed
    ),
    error = function(e) e
  )
  elapsed <- proc.time()[[3]] - start

  if (inherits(result, "error")) {
    write_failure(
      scenario_dir,
      "bayesfpca_fixed",
      result,
      elapsed,
      K_fixed
    )
  } else {
    write_fit(
      scenario_dir,
      "bayesfpca_fixed",
      result,
      input$ids,
      input$dimensions,
      L,
      elapsed,
      K_fixed
    )
  }

  fairness <- isTRUE(as.logical(row$fairness))
  if (fairness) {
    sensitivity_rows <- list()
    fits <- list()
    index <- 1

    for (K in 5:9) {
      start <- proc.time()[[3]]
      fit <- tryCatch(
        run_one(
          input$time_obs,
          input$Y,
          L,
          K,
          time_g,
          710000 + row_index * 10 + K
        ),
        error = function(e) e
      )
      elapsed_k <- proc.time()[[3]] - start

      if (inherits(fit, "error")) {
        sensitivity_rows[[index]] <- data.frame(
          K = K,
          status = "failed",
          elapsed_seconds = elapsed_k,
          final_elbo = NA_real_,
          error = conditionMessage(fit),
          stringsAsFactors = FALSE
        )
      } else {
        elbo <- as.numeric(fit$elbo)
        final_elbo <- if (length(elbo)) {
          tail(elbo, 1)
        } else {
          NA_real_
        }
        sensitivity_rows[[index]] <- data.frame(
          K = K,
          status = "ok",
          elapsed_seconds = elapsed_k,
          final_elbo = final_elbo,
          error = "",
          stringsAsFactors = FALSE
        )
        fits[[as.character(K)]] <- fit
      }
      index <- index + 1
    }

    sensitivity <- do.call(
      rbind,
      sensitivity_rows
    )
    write.csv(
      sensitivity,
      file.path(
        scenario_dir,
        "bayesfpca_k_sensitivity.csv"
      ),
      row.names = FALSE
    )

    eligible <- sensitivity[
      sensitivity$status == "ok" &
        is.finite(sensitivity$final_elbo),
      ,
      drop = FALSE
    ]
    if (nrow(eligible) > 0) {
      eligible <- eligible[
        order(
          -eligible$final_elbo,
          eligible$K
        ),
        ,
        drop = FALSE
      ]
      selected_K <- as.integer(
        eligible$K[[1]]
      )
      selected <- fits[[
        as.character(selected_K)
      ]]
      write_fit(
        scenario_dir,
        "bayesfpca_selected",
        selected,
        input$ids,
        input$dimensions,
        L,
        as.numeric(
          eligible$elapsed_seconds[[1]]
        ),
        selected_K
      )
    } else {
      write_failure(
        scenario_dir,
        "bayesfpca_selected",
        simpleError(
          "no successful finite-ELBO K candidate"
        ),
        NA_real_
      )
    }
  }
}
