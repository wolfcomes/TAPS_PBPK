#!/usr/bin/env Rscript
# Re-run preserved baselines without fitting or modifying parameters.
main <- function() {
  args <- commandArgs(trailingOnly=TRUE)
  if (length(args) < 2 || length(args) > 3)
    stop("Usage: Rscript scripts/run_pbpk.R DXM|MCT|DES NEW_OUTPUT_DIR [pkml|snapshot]")
  case <- toupper(args[[1]])
  mode <- if (length(args) == 3) args[[3]] else "pkml"
  if (!case %in% c("DXM", "MCT", "DES") || !mode %in% c("pkml", "snapshot"))
    stop("Unknown case or mode")
  script <- sub("^--file=", "", commandArgs()[startsWith(commandArgs(), "--file=")])
  root <- normalizePath(file.path(dirname(script), ".."), mustWork=TRUE)
  catalog <- read.csv(file.path(root, "docs/model_catalog.csv"), stringsAsFactors=FALSE)
  catalog <- catalog[catalog$case == case, , drop=FALSE]
  out <- path.expand(args[[2]])
  if (file.exists(out) && !dir.exists(out)) stop("Output path is a file")
  if (dir.exists(out) && length(list.files(out, all.files=TRUE, no..=TRUE)))
    stop("Output must be a new or empty directory: ", out)
  dir.create(out, recursive=TRUE, showWarnings=FALSE)
  out <- normalizePath(out, mustWork=TRUE)
  suppressPackageStartupMessages(library(ospsuite))
  options(digits=17)
  capture.output(sessionInfo(), file=file.path(out, "sessionInfo.txt"))
  started <- format(Sys.time(), tz="UTC", usetz=TRUE)
  file_sha256 <- function(path) {
    if (!nzchar(Sys.which("sha256sum"))) stop("sha256sum is required")
    answer <- system2("sha256sum", shQuote(path), stdout=TRUE)
    hash <- strsplit(answer[[1]], " +")[[1]][[1]]
    if (!grepl("^[a-f0-9]{64}$", hash)) stop("Unable to hash input")
    hash
  }
  scratch <- tempfile("taps_pkml_")
  dir.create(scratch)
  on.exit(unlink(scratch, recursive=TRUE), add=TRUE)
  decompress <- function(input, output) {
    src <- gzfile(input, "rb"); dst <- file(output, "wb")
    on.exit({close(src); close(dst)}, add=TRUE)
    repeat {
      chunk <- readBin(src, "raw", n=1024*1024)
      if (!length(chunk)) break
      writeBin(chunk, dst)
    }
  }
  records <- list()
  if (mode == "snapshot") {
    initPKSim()
    for (rel in unique(catalog$snapshot)) {
      name <- tools::file_path_sans_ext(basename(rel))
      dest <- file.path(out, name)
      dir.create(dest)
      cat("BUILD", name, "\n"); flush.console()
      runSimulationsFromSnapshot(file.path(root, rel), output=dest,
        RunForAllOutputs=TRUE, exportCSV=TRUE, exportPKML=TRUE)
      built <- list.files(dest, pattern="\\.pkml$", full.names=TRUE)
      expected <- sum(catalog$snapshot == rel)
      if (length(built) != expected) stop("Unexpected number of built simulations")
      records[[length(records)+1]] <- list(input=rel,
        input_sha256=file_sha256(file.path(root, rel)),
        built_simulations=length(built), outputs=basename(built))
    }
  } else {
    run_options <- SimulationRunOptions$new(numberOfCores=1,
      checkForNegativeValues=TRUE, showProgress=FALSE)
    for (i in seq_len(nrow(catalog))) {
      row <- catalog[i, ]
      cat("RUN", row$name, "\n"); flush.console()
      input <- file.path(root, row$pkml)
      pkml <- file.path(scratch, paste0(row$name, ".pkml"))
      decompress(input, pkml)
      sim <- loadSimulation(pkml, loadFromCache=FALSE, addToCache=FALSE, resetIds=FALSE)
      quantities <- getAllQuantityPathsIn(sim)
      plasma <- quantities[grepl("^Organism\\|PeripheralVenousBlood\\|[^|]+\\|Plasma \\(Peripheral Venous Blood\\)$", quantities)]
      drug <- switch(case, DXM="Dextromethorphan", DES="Desipramine", MCT="MCT")
      parent <- paste0("Organism|PeripheralVenousBlood|", drug, "|Plasma (Peripheral Venous Blood)")
      if (!parent %in% plasma) stop("Missing parent plasma output")
      local <- quantities[grepl("^Organism\\|Liver\\|(Periportal|Pericentral)\\|Intracellular\\|", quantities) &
        endsWith(quantities, paste0("|", drug, "|Concentration"))]
      paths <- unique(c(parent, plasma, local))
      parameters <- getAllParameterPathsIn(sim)
      sentinels <- parameters[grepl("\\|(Km|kcat|Molecular weight)$", parameters) |
        (grepl("CYP2D6|MCT_TotalMetabolism", parameters) &
        grepl("\\|(Concentration|Relative expression|Reference concentration)$", parameters))]
      audit <- do.call(rbind, lapply(sentinels, function(path) {
        p <- getParameter(path, sim)
        data.frame(path=p$path, value=p$value, unit=p$unit, fixed=p$isFixedValue)
      }))
      clearOutputs(sim); addOutputs(paths, sim)
      result <- runSimulations(list(sim), simulationRunOptions=run_options, stopIfFails=TRUE)[[1]]
      values <- getOutputValues(result, paths)
      d <- values$data
      if (!all(is.finite(as.matrix(d))) || any(diff(d$Time) < 0) ||
          nrow(d) < 2 || min(d$Time) != 0 || min(as.matrix(d[paths])) < -1e-9)
        stop("Invalid numeric output: ", row$name)
      dest <- file.path(out, row$name); dir.create(dest)
      write.csv(d, file.path(dest, "concentrations.csv"), row.names=FALSE)
      write.csv(audit, file.path(dest, "parameter_audit.csv"), row.names=FALSE)
      jsonlite::write_json(values$metaData, file.path(dest, "units.json"),
        pretty=TRUE, auto_unbox=TRUE, digits=17)
      records[[length(records)+1]] <- list(name=row$name, input=row$pkml,
        input_sha256=file_sha256(input),
        reference=row$reference, points=nrow(d),
        time_unit=values$metaData$Time$unit, output_paths=paths,
        minimum_concentration=min(as.matrix(d[paths])))
      cat("DONE", row$name, nrow(d), "points\n"); flush.console()
      rm(sim, result, values); invisible(gc())
    }
  }
  jsonlite::write_json(list(status="complete", case=case, mode=mode,
    started_at=started, completed_at=format(Sys.time(), tz="UTC", usetz=TRUE),
    R=R.version.string, ospsuite=as.character(packageVersion("ospsuite")),
    purpose="Software reproduction only; no fitting or biological validation", runs=records),
    file.path(out, "run_manifest.json"), pretty=TRUE, auto_unbox=TRUE, digits=17)
  cat("Results:", out, "\n")
}
main()
