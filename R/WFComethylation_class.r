#### WFComethylation class definition ####
# Peter Hickey
# 30/01/2013
# WFComethylation class for storing *.wf files

#### WARNINGS ####
# Initially I used 'setClassUnion("vectorOrNULL", c("vector", "NULL"))' for the NIML slot in WFComethylation. Unfortunately, this causes problems with the 'Rle' function as so I have replaced this slot by a numeric, whereby NA_integer is equivalent to NULL in the original definition

#### Definition ####
# setClassUnion("vectorOrNULL", c("vector", "NULL")) ## This line breaks the showMethods('Rle'), meaning I can't construct GRanges

setClass("WFComethylation", contains = "hasGRanges",
         representation(
           positions = "matrix",
           ntuples = "matrix",
           #NIML = "vectorOrNULL", ## 
           NIML = "numeric",
           sampleName = "character",
           methylationType = "character"
         ))

#### Valiity checker ####
setValidity("WFComethylation", function(object) {
  msg <- NULL
  nNTuples <- length(object@gr)
  if(nNTuples != nrow(object@ntuples) || nNTuples != nrow(object@positions))
    msg <- c(msg, "length of the 'gr' slot is not equal to the nrows of the 'ntuples' or 'positions' slots")
  if (any(object@ntuples < 0))
    msg <- c(msg, "the 'ntuples' slot has negative entries")
  if (!is.na(object@NIML))
    if ((length(object@NIML)) != nrow(object@positions))
      msg <- c(msg, "length of the 'NIML' slot is not equal to nrow of the 'positions' slot")
  if (length(object@sampleName) != 1)
    msg <- c(msg, "length of 'sampleName' is not equal to 1")
  if (!(object@methylationType %in% c("CpG", "CHG", "CHH")))
    msg <- c(msg, "'methylationType' must be one of 'CpG', 'CHG' or 'CHH'")
  if(is.null(msg)) TRUE else msg
})

#### Methods ####
setMethod("show", signature(object = "WFComethylation"),
          function(object) {
            cat("Sample:", object@sampleName, "\n")
            cat("An object of type 'WFComethylation' with\n")
            cat(paste0(" ", nrow(object), " ", object@methylationType, " ", ncol(object), "-tuples\n"))
          })
setMethod("dim", "WFComethylation", function(x) {
  dim(x@positions)
})
setMethod("nrow", "WFComethylation", function(x) {
  nrow(x@positions)
})
setMethod("ncol", "WFComethylation", function(x) {
  ncol(x@positions)
})

setMethod("[", "WFComethylation", function(x, i, ...) {
  if (missing(drop))
    drop <- FALSE
  if (missing(i))
    stop("need [i] for subsetting")
  x@gr <- getWFComethylation(x, "gr")[i, , drop = FALSE]
  x@positions <- getWFComethylation(x, "positions")[i, , drop = FALSE]
  x@ntuples <- getWFComethylation(x, "ntuples")[i, , drop = FALSE]
  if (!is.na(x@NIML)){
    x@NIML <- getWFComethylation(x, "NIML")[i, drop = FALSE]
  }
  x
})

## A 'countOverlaps' method for WFComethylation objects.
## IMPORTANT: Uses the first & last methylation loci in the n-tuple (i.e. the 'gr' slot of the WFComethylation object) to determine ranges.
setMethod("countOverlaps", signature(query = "WFComethylation", subject = "GRanges"), function(query, subject, ...) {
  countOverlaps(getWFComethylation(query, "gr"), subject, ...)
})

setMethod("combine", signature(x = "WFComethylation", y = "WFComethylation"), function(x, y, ...) {
  ## All of this assumes that x and y belong to the same sample and that x and y do not share any methylation loci n-tuples
  if (class(x) != class(y))
    stop(paste("objects must be the same class, but are ",
               class(x), ", ", class(y), sep=""))
  if (x@sampleName != y@sampleName)
    stop("'x' and 'y' have different 'sampleName' slots. Are you sure these are from the same sample?")
  if (x@methylationType != y@methylationType)
    stop(paste0("'x' and 'y' must have the same 'methylationType' slot, but 'x' uses ", x@methylationType, " and 'y' uses ", y@methylationType))
  if (ncol(x@ntuples) != ncol(y@ntuples))
    stop(paste0("'x' and 'y' must use the same size n-tuples, but 'x' uses ", 
         ncol(x@ntuples), "-tuples and 'y' uses ", ncol(y@ntuples), "-tuples"))
  if ((is.na(x@NIML) & !is.na(y@NIML)) || ((!is.na(x@NIML) & is.na(y@NIML))))
    stop("If the 'NIML' slot is non-NA then it must be non-NA for both 'x' and 'y'")
  if (identical(x, y))
    stop("'x' and 'y' appear to be the same object")
  gr <- c(x@gr, y@gr)
  positions <- rbind(x@positions, y@positions)
  ntuples <- rbind(x@ntuples, y@ntuples)
  if (!is.na(x@NIML) & !is.na(y@NIML)){
    NIML <- rbind(x@NIML, y@NIML)
  } else{
    NIML <- NULL
  }
  sampleName <- x@sampleName
  methylationType <- x@methylationType
  WFComethylation(gr = gr, positions = positions, ntuples = ntuples, NIML = NIML, sampleName = sampleName, methylationType = methylationType)
})

# Adapted from bsseq:::combineList()
combineList <- function(x, ...) {
  ## Check validity of each element of x to ensure they can be combined meaningfully and sensibly
  if (!is.list(x)) {
    stop("'x' must be a list of 'WFComethylation' objects")
  }
  if (!all(sapply(x, class) == "WFComethylation")) {
    stop("All elements of 'x' must be 'WFComethylation' objects")
  }
  if (!all(sapply(x, getWFComethylation, type = "methylationType")[1] == sapply(x, getWFComethylation, type = "methylationType"))) {
    stop("All elements of 'x' must have the same 'methylationType'")
  }
  if (!all(sapply(x, getWFComethylation, type = "sampleName")[1] == sapply(x, getWFComethylation, type = "sampleName"))) {
    stop("All elements must have the same 'sampleName'. Are you sure these are all from the same sample?")
  }
  if (!all(sapply(x, ncol)[1] == sapply(x, ncol))) {
    stop("All elements must use the same size n-tuples.")
  }
  if (!any(sapply(X = lapply(x, getWFComethylation, type = "NIML"), FUN = is.na)[1] == sapply(X = lapply(x, getWFComethylation, type = "NIML"), FUN = is.na))) {
    stop("All elements must have 'NIML' set uniformly as NA or as non-NA")    
  }
  ## Construct the combined WFComethylation object
  gr <- do.call(c, lapply(unname(x), function(xx) {getWFComethylation(xx, "gr")})) # unname() is necessary otherwise c() doesn't work on a list of GRanges
  positions <- do.call(rbind, lapply(x, function(xx) {getWFComethylation(xx, "positions")}))
  ntuples <- do.call(rbind, lapply(x, function(xx) {getWFComethylation(xx, "ntuples")}))
  if (all(sapply(X = lapply(x, getWFComethylation, type = "NIML"), FUN = function(x){!is.na(x)}))){
    NIML <- do.call(dbind, lapply(x, function(xx) {getWFComethylation(xx, "NIML")}))
  } else{
    NIML <- NA_real_
  }
  sampleName <- getWFComethylation(x[[1]], type = "sampleName")
  methylationType <- getWFComethylation(x[[1]], type = "methylationType")
  WFComethylation(gr = gr, positions = positions, ntuples = ntuples, NIML = NIML, sampleName = sampleName, methylationType = methylationType )
}
  
## Mainly for internal use
getWFComethylation <- function(WFComethylation, type = c("positions", "ntuples", "gr", "NIML", "sampleName", "methylationType")) {
  type <- match.arg(type)
  switch(type,
         "positions" = {
           return(WFComethylation@positions)
         },
         "ntuples" = {
           return(WFComethylation@ntuples)
         },
         "gr" = {
           return(WFComethylation@gr)
         },
         "NIML" = {
           return(WFComethylation@NIML)
         },
         "sampleName" = {
           return(WFComethylation@sampleName)
         },
         "methylationType" = {
           return(WFComethylation@methylationType)
         })
}


#### Constructor ####
WFComethylation <- function(gr = gr, positions = NULL, ntuples = NULL, NIML = NA_real_, sampleName = NULL, methylationType = NULL) {
  ## TODO: Need to think through carefully all the checks necessary to ensure the WFComethylation object is valid
  if (!is(gr, "GRanges"))
    stop("'gr' needs to be a GRanges object")
  if (!all.equal(start(gr), positions[, 1]))
    stop("'gr' start positions must be the first methylation loci in the n-tuple")
  if (!all.equal(end(gr), positions[, ncol(positions)]))
    stop("'gr' end positions must be the last methylation loci in the n-tuple")
  if (is.null(positions) || is.null(ntuples))
    stop("Need 'positions' and 'ntuples'")
  if (!is.matrix(ntuples))
    stop("'ntuples' needs to be a matrix")
  if (!is.matrix(positions))
    stop("'positions' needs to be a matrix")
  if (!is.na(NIML))
      if (!is.numeric(NIML) || any(NIML) < 0)
    stop("'NIML' needs to be a vector of non-negative integers or set to 'NA_real_'")
  if (!is.na(NIML))
    if (length(NIML) != length(gr))
      stop("'gr' and 'NIML' need to have the same length if 'NIML' is not NULL")
  if (length(gr) != nrow(ntuples) || length(gr) != nrow(positions))
    stop("'gr', 'ntuples' and 'positions' need to the same number of rows")
  if (!is.null(rownames(positions)))
    rownames(positions) <- NULL
  if (!is.null(rownames(ntuples)))
    rownames(ntuples) <- NULL
  if (!is.null(names(gr)))
    names(gr) <- NULL
  if (is.null(sampleName) || length(sampleName) != 1)
    stop("'sampleName' needs to be a single character string")
  if (is.null(methylationType))
    stop("methylationType' must be one of 'CpG', 'CHG' or 'CHH'")
  WFComethylation <- new("WFComethylation", gr = gr, positions = positions, ntuples = ntuples, NIML = NIML, sampleName = sampleName, methylationType = methylationType)
  WFComethylation
}