library(cluster)
library(factoextra)

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# PAM

# 1. Load data ---------------------------
data <- read.csv("models/british_columbia/vancouver/pam/data.csv")

# Scaling
df <- scale(data)

# 2. Clustering ---------------------------
fviz_nbclust(df, pam, method = "silhouette") + 
  theme_classic()

k <- 5
pam.res <- pam(data, k = k, metric = 'manhattan', stand = TRUE)

fviz_cluster(pam.res,
             repel = FALSE,
             ggtheme = theme_classic()
)

labels <- data.frame(pam.res$clustering)
write.csv(x = labels, file = "models/british_columbia/vancouver/pam/5_cluster_labels.csv")