from sklearn.preprocessing import MinMaxScaler
import seaborn as sns
from copy import deepcopy

def kdeplot(data, variable_names, label_name):
    '''Visualize cluster variables with KDE plot. This code is take from 
    
    Args:
        variables (DataFrame) : 
        variable_names (str) : 
        label_name (str)
    
    Returns:
                
    '''
    tidy_db = deepcopy(data)[variable_names + [label_name]]   
    # Index db on cluster ID
    tidy_db = tidy_db.set_index(label_name)
    # Keep only variables used for clustering
    tidy_db = tidy_db[variable_names]
    # Stack column names into a column, obtaining 
    # a "long" version of the dataset
    tidy_db = tidy_db.stack()
    # Take indices into proper columns
    tidy_db = tidy_db.reset_index()
    # Rename column names
    tidy_db = tidy_db.rename(columns={'level_1': 'Attribute', 0: 'Values'})
    # Setup the facets
    facets = sns.FacetGrid(data=tidy_db, col='Attribute', hue=label_name, sharey=False, sharex=False, aspect=2, col_wrap=3)
    # Build the plot from `sns.kdeplot`
    _ = facets.map(sns.kdeplot, 'Values', shade=True).add_legend()