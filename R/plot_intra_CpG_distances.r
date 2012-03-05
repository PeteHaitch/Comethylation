library(multicore)
library(ggplot2)
options("cores" = 10)
x <- scan("mycount.out", what="character", sep="\n")
y <- strsplit(x, ",")
z <- lapply(X = y, FUN = as.numeric)
d <- unlist(mclapply(X = z, FUN = diff, lag = 1))
qplot(d, binwidth = 10)

df <- data.frame(d)
m <- ggplot(data = df, aes(x=d))
m + geom_histogram(binwidth = 1)
m + geom_histogram(aes(y = ..density..), binwidth = 1) + geom_density()
m + geom_density(kernel = "rectangular") 