import osmnx as ox
import pandas as pd
import geopandas as gpd
import pandana as pdna
from pandana.loaders import osm
import pandana as pdna
import matplotlib.pyplot as plt
from shapely import geometry
import fiona
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
import shapely
from shapely.geometry import Polygon
import numpy as np
from matplotlib.patches import RegularPolygon
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import mstats
import requests, zipfile, io
from datetime import datetime
import os


def create_poi_gdf(MAREA = None):
    
    '''Downloads public transport, parks, and urban amenities from OpenStreetMap, classifies them into seven distinct categories, and
    outputs a point geodataframe.
    
    Args: 
        MAREA (GeoDataFrame) : Polygon of boundaries of a given city.
    
    Returns:
        gdf (GeoDataFrame) : Geodataframe consisting of points of interests for a given city.
        
    '''
    
    ##public transport
    #get public transport (rail) network of metro vancouver
    rail = ox.graph_from_polygon(MAREA.iloc[0,0], network_type='all',
                                  infrastructure='way["railway"]', retain_all=True)
    #make rail pois
    rail_gdf = ox.save_load.graph_to_gdfs(rail, nodes=True, edges=False, node_geometry=True, fill_edge_geometry=True)
    rail_gdf['amenity'] = 'transit_stop'
    rail_gdf = rail_gdf[['amenity', 'geometry']]

    #get public bus stops
    bus = ox.footprints.footprints_from_polygon(polygon = MAREA.iloc[0,0], footprint_type = 'public_transport')
    bus['amenity'] = 'public_transport'
    bus['centroid'] = bus.centroid
    bus = bus.set_geometry('centroid')
    bus = bus[['amenity', 'centroid']]
    bus = bus.rename(columns = {"centroid": "geometry"})

    ##amenities pois
    # define your selected amenities
    amenities = ["transit_stop", "bus_station", "bus_stop", "bicycle_parking", "gym", "park", "pub", "bar", "theatre", 
                 "cinema", "nightclub", "events_venue", "restaurant", "cafe", "food_court", "marketplace", "community_centre", 
                 "library", "social_facility", "social_centre", "townhall", "school", "childcare", "child_care", "kindergarten",
                 "university", "college", "pharmacy", "dentist", "clinic", "hospital", "doctors", "bank"]

    #request amenities from the OpenStreetMap API (Overpass)
    pois = ox.pois_from_polygon(MAREA.iloc[0,0])
    pois = pois[pois['amenity'].isin(amenities)]
    pois = pois[['amenity','geometry']]

    #get parks and "leisure" elements
    leisure = ["fitness_centre", "sports_centre", "park", "pitch", "playground", "swimming_pool", "garden", "golf_course", "sports_centre", 
               "ice_rink", "dog_park", "nature_reserve", "fitness_centre", "marina", "recreation_ground", "fitness_station", "skate_park"]

    parks = ox.footprints.footprints_from_polygon(polygon = MAREA.iloc[0,0], footprint_type = 'leisure')
    parks = parks[parks['leisure'].isin(leisure)]
    parks['centroid'] = parks.centroid
    parks = parks.set_geometry('centroid')
    parks = parks[['leisure','centroid']]
    parks = parks.rename(columns = {"leisure":"amenity","centroid": "geometry"})

    #merge all the dataframes together
    #merge dataframes together
    pois_list = [pois,rail_gdf, bus, parks]
    pois_all = pd.concat(pois_list, axis=0, ignore_index=True)

    #create x and y columns for network analysis
    pois_all['x'] = pois_all.centroid.x
    pois_all['y'] = pois_all.centroid.y
    
    pois_all['centroid'] = pois_all.centroid
    pois_all = pois_all.set_geometry('centroid')
    pois_all = pois_all[['amenity', 'x', 'y','centroid']]
    pois_all = pois_all.rename(columns = {"centroid": "geometry"})
    pois_all = pois_all.set_geometry('geometry')
    
    return pois_all


# function to aggregate amenities into categories: USE THIS FOR METHOD NUMBER 1 (agreggate first, then measure access)
def amenity_cat_old(pois_all = None):
    '''Aggregates amenities into seven distinct categories.
    
    Args: 
        pois_all (GeoDataFrame) : Points of interests GeoDataFrame as outputted by the create_access_gdf function.
    
    Returns:
        gdf (GeoDataFrame) : 
    
    '''
    
    # reshape dataframe
#     pois_all = pd.melt(pois_df, id_vars=['osmid', 'geometry', 'x', 'y'], var_name='amenity')
    # define categories
    mobility = ["transit_stop", "bus_station", "bus_stop", "public_transport"]

    active_living = ["bicycle_parking", "gym", "fitness_centre", "sports_centre", "park", "pitch", "playground", "swimming_pool", 
                     "garden", "golf_course", "sports_centre","ice_rink", "dog_park", "nature_reserve", "fitness_centre", "marina", 
                     "recreation_ground", "fitness_station", "skate_park"]

    nightlife = ["pub", "bar", "theatre", "cinema", "nightclub", "events_venue"]

    food_choices = ["restaurant", "cafe", "food_court", "marketplace"]

    community_space = ["community_centre", "library", "social_facility", "social_centre", "townhall"]

    education = ["school", "childcare", "child_care", "kindergarten", "university", "college"]

    health_wellbeing = ["pharmacy", "dentist", "clinic", "hospital", "doctors", "bank"]

    cat_list = [mobility, active_living, nightlife, food_choices, community_space, education, health_wellbeing]
    cat_list_str = ["mobility", "active_living", "nightlife", "food_choices", "community_space", "education", "health_wellbeing"]

    for cat in cat_list:
        cat_index = cat_list.index(cat)
        pois_all.amenity[pois_all['amenity'].isin(cat)] = cat_list_str[cat_index]
        
    # reshape back into original format
#     pois_all = pois_all.groupby(['osmid', 'amenity'])['value'].aggregate('mean').unstack().reset_index()
#     # merge with original df
#     pois_final = pd.merge(access_df, pois_all, on = 'osmid')
    
    return pois_all


#function to compute accessibility indicator for each amenity with regards to each node on the network
def create_access_gdf(MAREA_pois = None, network = None, MAREA = None):
    
    '''Computes walking distances from each street intersection to each of the seven categories of urban amenities
    
    Args: 
        MAREA_pois: Categorized oints of interests GeoDataFrame as outputted by the amenity_cat_old function.
        MAREA (GeoDataFrame) : Polygon of boundaries of a given city.
        network : pedestrian street network of a given city.
    
    Returns:
        gdf (GeoDataFrame) : Point GeoDataFrame consisting of street intersections, each with an assignment walking distance 
        value for each category of amenities.
        
    '''

    cat_list_str = list(MAREA_pois.groupby(['amenity']).mean().reset_index()['amenity'])

    #create dummy dataframe (only way of doing it so far is to run dummy network analysis at 1m)
    for cat in cat_list_str:
        pois_subset = MAREA_pois[MAREA_pois['amenity']==cat]
        network.set_pois(category = cat, maxdist = 1, maxitems=len(pois_subset), x_col=pois_subset['x'], y_col=pois_subset['y'])
        accessibility = network.nearest_pois(distance=1, category=cat) 
        
    #now calculate distances
    for cat in cat_list_str:
        pois_subset = MAREA_pois[MAREA_pois['amenity']==cat]
        network.set_pois(category = cat, maxdist = 10000, maxitems=len(pois_subset), 
                                 x_col=pois_subset['x'], y_col=pois_subset['y'])

        accessibility[str(cat)] = network.nearest_pois(distance=10000, category=cat) 

    #get walking network of Toronto
    walk = ox.graph_from_polygon(MAREA.iloc[0,0], network_type='walk', retain_all=True)
    #convert walking network to tuple with nodes and edges gdfs
    walk_gdf = ox.save_load.graph_to_gdfs(walk, nodes=True, edges=False, node_geometry=True, fill_edge_geometry=True)

    #merge accessibility values with walk nodes ids geodataframe
    access = pd.merge(accessibility,
                               walk_gdf,
                               left_on='id',
                               right_on='osmid',
                               how='left')
    #convert to geodataframe
    access = gpd.GeoDataFrame(access, geometry=gpd.points_from_xy(access.x, access.y))
    #set right crs
    access.crs = {'init' :'epsg:4326'}
    
    #drop unnecessary columns and NaNs
    try:
        access = access.drop([1,'ref','highway'],axis=1)
    except KeyError:
        pass
    
    access = access.dropna()
    access = access[~(access == 10000).any(1)].reset_index().drop('index', axis=1)

    return access

def haversine(coord1, coord2):
    
    '''Defines the haversine function for polygons'''
    
    # Coordinates in decimal degrees (e.g. 43.60, -79.49)
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371000  # radius of Earth in meters
    phi_1 = np.radians(lat1)
    phi_2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi_1) * np.cos(phi_2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a),np.sqrt(1 - a))
    meters = R * c  # output distance in meters
    km = meters / 1000.0  # output distance in kilometers
    meters = round(meters)
    km = round(km, 3)
    #print(f"Distance: {meters} m")
    #print(f"Distance: {km} km")
    return meters

# define function to create hexagons for any city boundaries and any resolution
def make_hexmap(MAREA = None, d = 300):
    
    '''Takes a shapefile and fills it with hexagons of diameter d.
    
    Args: 
        MAREA (GeoDataFrame) : Polygon of boundaries of a given city.
        d : desired hexagon diameter
    
    Returns:
        gdf (GeoDataFrame) : Hexagon grid GeoDataFrame
    '''
    
    xmin,ymin,xmax,ymax = MAREA.total_bounds # lat-long of 2 corners
    #East-West extent of Toronto = 42193 metres
    EW = haversine((xmin,ymin),(xmax,ymin))
    # North-South extent of Toronto = 30519 metres
    NS = haversine((xmin,ymin),(xmin,ymax))
    # diameter of each hexagon in the grid = 900 metres
    d = 300
    # horizontal width of hexagon = w = d* sin(60)
    w = d*np.sin(np.pi/3)
    # Approximate number of hexagons per row = EW/w 
    n_cols = int(EW/w)+1
    # Approximate number of hexagons per column = NS/d
    n_rows = int(NS/d)+ 1
    
    # Make hexagons
    w = (xmax-xmin)/n_cols # width of hexagon
    d = w/np.sin(np.pi/3) #diameter of hexagon
    array_of_hexes = []
    for rows in range(0,n_rows):
        hcoord = np.arange(xmin,xmax,w) + (rows%2)*w/2
        vcoord = [ymax- rows*d*0.75]*n_cols
        for x, y in zip(hcoord, vcoord):#, colors):
            hexes = RegularPolygon((x, y), numVertices=6, radius=d/2, alpha=0.2, edgecolor='k')
            verts = hexes.get_path().vertices
            trans = hexes.get_patch_transform()
            points = trans.transform(verts)
            array_of_hexes.append(Polygon(points))
            #ax.add_patch(hexes)
            
    # make final geodataframe
    hex_grid = gpd.GeoDataFrame({'geometry':array_of_hexes},crs={'init':'epsg:4326'})
    MAREA_hex = gpd.overlay(hex_grid, MAREA)
    #MAREA_hex = hex_grid
    MAREA_hex = gpd.GeoDataFrame(MAREA_hex,geometry='geometry')
    MAREA_hex = MAREA_hex.reset_index()
    
    return MAREA_hex

#function to create accessibility by Hexagon
def create_hex_access(access = None, hexgrid = None, fillna = None, fillna_value = None):
    
    '''Computes average accessibility per hexagon by taking the average of walking distances within each hexagon
        
    Args: 
        access (GeoDataFrame) : Point GeoDataFrame with distance values.
        hexgrid : hexagon grid
    
    Returns:
        gdf (GeoDataFrame) : Hexagon grid GeoDataFrame with averaged distance values for each category of amenities.

    '''
    
    #join transit access points to census
    hexgrid = hexgrid.reset_index()
    hex_access = gpd.sjoin(hexgrid, access, how='left')


    hex_access['index'] = hex_access['index'] 
    hex_access = hex_access.groupby('index').mean()
#     hex_access = hex_access[["mobility", "active_living", "nightlife", "food_choices",
#                                    "community_space", "education", "health_wellbeing"]]
    
    #hex_access = hex_access.fillna(method = 'ffill')
    if fillna_value == None:
        if fillna == None:
            hex_access = hex_access.dropna()
        elif fillna != None:
            hex_access = hex_access.fillna(method = fillna)
    else:
#         hex_access = hex_access.fillna(hex_access.max(), downcast='infer')
        hex_access = hex_access.fillna(value = fillna_value)
#         hex_access = hex_access.fillna(method = 'ffill')

    hex_access = hexgrid.merge(hex_access, on='index')
    hex_access = hex_access.drop('index_right',axis=1)
    
    
    return hex_access


#function to create accessibility by census block
def create_census_access(access = None, census = None, country = None, fillna = None, fillna_value = None):
    
    '''Computes average accessibility by block by taking the average of walking distances within each census block
    
    Args: 
        access (GeoDataFrame) : Point GeoDataFrame with distance values.
        census (GeoDataFrame) : Census geometry (e.g. census block groups) GeoDataFrame.
        country (string) : "Canada" or "USA"
    
    Returns:
        gdf (GeoDataFrame) : GeoDataFrame with distance values for each census geometry.
    
    '''
    if country == 'canada':
        census = census.to_crs(epsg=4326)
        #join transit access points to census
        census_access = gpd.sjoin(census, access, how='left')

        #group-by OBJECTID and calculate mean price_m2 per census block
        census_access['index'] = census_access['id'] 
        census_access = census_access.groupby('id').mean()
        census_access = census_access[["mobility", "active_liv", "nightlife", "food_choic",
                                       "community_", "education", "health_wel"]]
#         census_access = census_access.fillna(method = 'ffill')
        if fillna_value == None:
            if fillna == None:
                census_access = census_access.dropna()
            elif fillna != None:
                census_access = census_access.fillna(method = fillna)
        else:
    #         hex_access = hex_access.fillna(hex_access.max(), downcast='infer')
            census_access = census_access.fillna(value = fillna_value)
        
        census_access = census.merge(census_access, on='id')
#         census_access = census_access[["id","mobility", "active_living", "nightlife", "food_choices",
#                                        "community_space", "education", "health_wellbeing", "geometry"]]
    elif country == 'united_states':
        #join transit access points to census
        census_access = gpd.sjoin(census, access, how='left')

        #group-by OBJECTID and calculate mean price_m2 per census block
        census_access['index'] = census_access['id'] 
        census_access = census_access.groupby('id').mean()
        census_access = census_access[["mobility", "active_liv", "nightlife", "food_choic",
                                       "community_", "education", "health_wel"]]
        
#         census_access = census_access.fillna(method = 'ffill')
        if fillna_value == None:
            if fillna == None:
                census_access = census_access.dropna()
            elif fillna != None:
                census_access = census_access.fillna(method = fillna)
        else:
    #         hex_access = hex_access.fillna(hex_access.max(), downcast='infer')
            census_access = census_access.fillna(value = fillna_value)
    
        census_access = census.merge(census_access, on='id')
#         census_access = census_access[["id","mobility", "active_liv", "nightlife", "food_choic",
#                                        "community_", "education", "health_wel", "geometry"]]

    return census_access


# function for accessibility score
def access_score(access_df = None, outlier_method = None):
    '''Computes accessibility score from walking distances.
    
    Args: 
        access_df (GeoDataFrame) : GeoDataFrame with distance values for seven categories of amenities.
    
    Returns:
        gdf (GeoDataFrame) : GeoDataFrame with accessibility score column.
    
    '''
    
    #compute the accessibility score
    access_df['accessibility'] =  (0.2*(access_df['mobility']) + 
                                   0.1*(access_df['active_liv']) + 
                                   0.1*(access_df['nightlife']) + 
                                   0.15*(access_df['food_choic']) + 
                                   0.1*(access_df['community_']) + 
                                   0.15*(access_df['education']) + 
                                   0.2*(access_df['health_wel']))
    
    #remove outliers and normalize the data
    scaler = MinMaxScaler(feature_range=(0, 1))
    
    # winsorize
    if outlier_method == 'winsorize':
        access_df['accessibility'] = 1 - scaler.fit_transform(mstats.winsorize(access_df[['accessibility']], axis= 0, limits = [0.1,0.1]))
    # log
    elif outlier_method == 'log':
        access_df['accessibility'] = 1 - scaler.fit_transform(np.log1p(access_df[['accessibility']]))
    # no outlier removal
    else:
        access_df['accessibility'] = 1 - scaler.fit_transform(access_df[['accessibility']])
    
    return access_df