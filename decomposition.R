setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
library("FactoMineR")
library("factoextra")

# 1. Load data ---------------------------
data <- read.csv("data/interim/data_wo_outliers.csv")
# data <- read.csv("variables/vancouver.csv")

# Scaling
# df <- data
df <- scale(data)

# 2. Decomposition ---------------------------
res.pca <- PCA(df, ncp = 5)

# 3. Visualization and interpretation
fviz_eig(res.pca, addlabels = FALSE, ylim = c(0, 50))

fviz_pca_ind(res.pca,
             geom.ind = "point", # show points only (nbut not "text")
             # col.ind = iris$Species, # color by groups
             # palette = c("#00AFBB", "#E7B800", "#FC4E07"),
             addEllipses = TRUE, # Concentration ellipses
             # legend.title = "Groups"
)
