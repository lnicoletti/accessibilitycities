library(diceR)

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# 1. Load data ---------------------------
data = read.csv("data/interim/preprocessed/seattle_winsorized.csv")

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
distance = c("euclidean", "maximum", "manhattan", "canberra", "binary", "minkowski", "spearman") #"spearman"

# Define consensus functions
cons.funs = c("kmodes") #, "majority", "CSPA", "LCE", "LCA"

reps = 10 # n replicates
seed = 1235 # fix seed for reproducibility

dice.obj <- dice(df, nk = 3:4, reps = reps, algorithms = algorithms, distance = distance, 
                 cons.funs = cons.funs, progress = TRUE, seed = seed, plot = FALSE)



# 3. Save the results ---------------------------

write.csv(x = dice.obj$clusters, file = 'models/united_states/seattle/cc/cluster_labels_3_4k.csv')


