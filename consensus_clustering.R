library(diceR)

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# Diverse Cluster Ensemble

# 1. Load data ---------------------------
data = read.csv("data/interim/preprocessed/toronto_short_winsorized.csv")

#df <- scale(data)

df = prepare_data(data, scale = TRUE, type = c("conventional"), min.var = 1)

# 2. Clustering ---------------------------

# Define clustering algorithms to be used
# 1. km - K-Means
# 2. pam - K-Medoids
# 3. hc - Hierarhical clustering
# 4. gmm - Gaussian Mixture Model
# 5. hdbscan - HDBSCAN
algorithms = c("km", "hc", "pam", "gmm", "hdbscan")

# Define distance functions to be used 
distance = c("euclidean", "maximum", "manhattan", "canberra", "binary", "minkowski", "spearman")

p.item = 0.9 # 90% resampling 
reps = 5 # 5 replicates

CC <- consensus_cluster(df, nk = 3:5, p.item = p.item, reps = reps,
                        algorithms = algorithms,
                        distance = distance, scale = TRUE)

co <- capture.output(str(CC))
strwrap(co, width = 80)

# 3. Evaluation ---------------------------

# Explore a single clustering algorithm with k = 4
pam.4 <- CC[, , "PAM_Euclidean", "4", drop = FALSE]

# Create and visualize consensus matrix
cm <- consensus_matrix(pam.4)
dim(cm)
hm <- graph_heatmap(pam.4)

ccomb_matrix <- consensus_combine(CC, element = "matrix")
ccomb_class <- consensus_combine(CC, element = "class")
str(ccomb_matrix, max.level = 2)

# Evaluate the performance
ccomp <- consensus_evaluate(data, CC, trim = TRUE, n = 1)

str(ccomp, max.level = 2)
