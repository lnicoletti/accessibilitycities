import pandas as pd
import os
import numpy as np
import itertools
from pprint import pprint
from h3 import h3
import folium
import shapely.geometry
import geopandas as gpd
import requests, zipfile, io
from datetime import datetime

# function to dissolve to obtain city boundaries
def get_citybounds(city = None):
    
    '''Dissolves city polygon into one boundary polygon'''
    
    city['COUNTRY'] = 1
    city = city.dissolve(by='COUNTRY')
    city = city.to_crs({'init' :'epsg:4326'})
    
    return city

def prepare_ca_data(df, gdf, city, city_geo=None):
    '''Prepare data for further modeling.
    
    Args:
        df (DataFrame) : 
        gdf (GeoDataFrame) :
        city (str) : 
        city_geo (int):
    
    Returns:
        df (DataFrame) : 
    
    '''

    # Find ids and geometry of the chosen city
    dauid = gdf[gdf['CCSNAME'] == city]['DAUID']
    n_polygons = dauid.shape[0]
    print(f'The number of polygons in the shape file = {n_polygons}')

    # Select the data
    data = df.set_index('GEO_NAME').loc[dauid, :]

    # Return to initial index and format
    data['GEO_NAME'] = data.index.tolist()
    data.reset_index(drop=True, inplace=True)
    print(f'The number of polygons in data file = {data["GEO_NAME"].unique().shape[0]}')

    # Select the columns of interest: id, variable name and variable value
    columns = ['GEO_NAME', 'DIM: Profile of Dissemination Areas (2247)', 'Dim: Sex (3): Member ID: [1]: Total - Sex']
    data = data[columns]

    # Convert variable values into numeric format
    data['Dim: Sex (3): Member ID: [1]: Total - Sex'] = pd.to_numeric(data['Dim: Sex (3): Member ID: [1]: Total - Sex'], errors='coerce').fillna(0)

    if city == 'Vancouver':
        # How many variables do we have?
        n_variables = data[data['GEO_NAME'] == '59150701'].shape[0]
        print(f'Total number of variables = {n_variables}')
    
    elif city == 'Toronto':
        n_variables = data[data['GEO_NAME'] == '35201588'].shape[0]
        print(f'Total number of variables = {n_variables}')
    
    elif city == 'Montréal':
        n_variables = data[data['GEO_NAME'] == '24661006'].shape[0]
        print(f'Total number of variables = {n_variables}')
    
    else:
        n_variables = data[data['GEO_NAME'] == city_geo].shape[0]
        print(f'Total number of variables = {n_variables}')
        
    # Create a variable id column
    variable_ids = np.arange(1, n_variables + 1)
    data['variable_id'] = np.tile(variable_ids, (n_polygons, 1)).flatten()
    
    return data

def select_ca_variables(city, df, return_names=False, print_selected=False, include_occupation=False, include_commute=False, extended_variables=True):
    '''Select variables of interest out of the whole data set.
    
    Args:
        df (DataFrame) : Data frame with all variables
        return_names (bool) : Return names of chosen variables
        print_selected (bool) : Print chosen variables
    
    Returns:
        result (DataFrame) : Resulting data frame with only the variables of choice
    
    '''
    all_names = pd.read_csv(f'../../data/interim/census/{city.lower()}_variable_names.csv')
    keys = all_names['variable_id'].tolist()
    values = all_names['DIM: Profile of Dissemination Areas (2247)'].tolist()
    d = dict(zip(keys, values))
    
    # Initial set of categories and corresponding indeces
    # Variable - category name, value - variable index in the df
    population_total = [1]
    population_density = [6] # Include?
    land_area = [7]
    age_group_total = [8]
    age_group = np.arange(10, 33).tolist()
    average_age = [39]
    median_age = [40]

    ethnicity = [1136, 1139, 1141, 1142,
                 1279, 1280, 1281, 
                 1290, 1297, 1324]

    household_total = [51]
    # household_sizes = np.arange(51,55 + 1).tolist() # not selected  # !!!: WRONG NUMBER -> NEEDS FIX FROM variable_names.csv file 
    persons_in_household = [57]
    # average_household_size = [57] # not selected # !!!: WRONG NUMBER -> NEEDS FIX FROM variable_names.csv file 
    
    martial_status_total = [59]
    martial_status_persons = [61, 63]

    families_total = [74]
    family_composition = [75, 78]

    language_total = [100]
    language = np.arange(101, 104 + 1).tolist()

    median_household_income = [663]
    average_household_income = [674]

    income_groups_total = [759]
    income_groups = np.arange(760, 779 + 1).tolist() # TODO: Aggregate?
    housing_spendings = [1668, 1669]

    housing_total = [41]
    housing_type = np.arange(42, 50 + 1).tolist()
    n_rooms_total = [1630]
    n_rooms = np.arange(1631, 1635 + 1).tolist()
    n_bedrooms_total = [1624]
    n_bedrooms = np.arange(1625, 1629 + 1).tolist()
    n_rooms_average = [1636]
    housing_ownership = [1618, 1619]
    persons_per_room = [1638, 1639]

    median_housing_price = [1676]
    average_housing_price = [1677]

    median_rent_price = [1681]
    average_rent_price = [1682]

    education_total = [1683]
    education_level = [1684, 1685, 1686]
    education_spec_total = [1713]
    education_spec = [1715, 1717, 1729, 1737, 
                      1741, 1747, 1752, 1760,
                      1763, 1767, 1773]

    employment_status_total = [1865]
    employment = [1867, 1868]

    occupation_total = [1884]
    occupation = np.arange(1887, 1896 + 1).tolist()

    commuting_mode_total = [1930]
    commuting_mode = np.arange(1931, 1936 + 1).tolist()

    # Since largest Candian cities seems to be segregated
    # and we'll have skewed distributions
    # I've decided to use "median" instead of "average"
    
    # However, it brings outliers, let's try average instead
    
    categories_of_choice = [population_density,
                            # land_area,
                            average_age, 
                            # median_age, 
                            ethnicity,
                            persons_in_household,
                            martial_status_persons, 
                            family_composition,
                            language,

                            average_household_income,
                            # median_household_income,

                            housing_spendings,
                            housing_ownership,
                            
                            # median_housing_price,
                            # median_rent_price,
                            average_housing_price,
                            average_rent_price,
                            
                            n_rooms_average,

                            education_level,
                            employment,
                            occupation, 
                            commuting_mode]
    
    if include_commute == False:
        del categories_of_choice[-1]
    
    if include_occupation == False:
        del categories_of_choice[-1]
        
    if extended_variables == False:
        categories_of_choice = [e for e in categories_of_choice if e in (language, ethnicity, average_household_income, education_level, employment)]
        
    # variables_of_choice are ids not the names of the variables
    # Format list of lists to a single list
    variables_of_choice = list(itertools.chain.from_iterable(categories_of_choice))
    
    # Save variable names
    variable_names = [d[key] for key in variables_of_choice]
    
    # Print selected set of variables
    if print_selected:
        pprint(variable_names)

    # Slice initial data frame to get resulting one 
    variables_of_choice = [str(variable) for variable in variables_of_choice]
    result = df.loc[:,variables_of_choice]
    
    if return_names:
        return (variable_names, result)
    else:
        return result

def scale_ca_variables(data):
    
    '''Scale the data by total number of respondents within each census block.

    Args:
        data (DataFrame) : Raw data frame with unselected variables, as outputted by the prepare_variables function.

    Returns:
        result (DataFrame) : Scaled data frame

    '''

    data.columns = data.columns.astype(str)
    
    # marital status
    data[['60', '63']] = (data[['60', '63']].divide(data['59'], axis=0))

    # family status, lone family kids
    data[['75', '78', '79', '80', '88', '89', '90']] = (data[['75', '78', '79', '80', '88', '89', '90']].divide(data['74'], axis=0))

    # language
    data[['101', '102', '103', '104', '107', '108', '109']] = (data[['101', '102', '103', '104', '107', 
                                                                     '108', '109']].divide(data['100'], axis=0))

    # citizenship
    data[['1136', '1139', '1141', '1142']] = (data[['1136', '1139', '1141', '1142']].divide(data['1135'], axis=0))
    # immigrants
    data[['1279', '1280', '1281', '1290', '1297', '1324', '1337']] = (data[['1279', '1280', '1281', '1290', '1297', 
                                                                            '1324', '1337']].divide(data['1278'], axis=0))

    # owner renter
    data[['1618', '1619', '1620', '1638', '1639', '1644',
          '1645', '1646', '1647', '1648', '1649', '1650',
          '1652', '1653', '1668', '1669', '1671', '1678']] = (data[['1618', '1619', '1620', '1638', '1639', '1644',
                                                                    '1645', '1646', '1647', '1648', '1649', '1650',
                                                                    '1652', '1653', '1668', '1669', '1671', '1678']].divide(data['1617'], axis=0))
    # education level 15+
    data[['1684', '1685', '1686', '1687', '1690', '1691',
          '1692', '1693', '1694', '1695', '1696', '1697']] = (data[['1684', '1685', '1686', '1687', '1690', '1691', 
                                                                    '1692', '1693', '1694', '1695', '1696', '1697']].divide(data['1683'], axis=0))
    # major field of study 15+
    data[['1714', '1715', '1717', '1720', 
          '1729', '1737','1741', '1747', 
          '1752', '1760', '1763', '1767', '1773']] = (data[['1714', '1715', '1717', '1720', 
                                                            '1729', '1737','1741', '1747', 
                                                            '1752', '1760', '1763', '1767', '1773']].divide(data['1713'], axis=0))
    # employee/self-empl
    data[['1882', '1883']] = (data[['1882', '1883']].divide(data['1879'], axis=0))

    # occupation
    data[['1887', '1888', '1889', '1890', '1891', 
          '1892', '1893', '1894', '1895', '1896']] = (data[['1887', '1888', '1889', '1890', '1891', 
                                                            '1892', '1893', '1894', '1895', '1896']].divide(data['1884'], axis=0))

    # industry
    data[['1900', '1901', '1902', '1903', '1904', 
          '1905', '1906', '1907', '1908', '1909', 
          '1910', '1911', '1912', '1913', '1914', 
          '1915', '1916', '1917', '1918', '1919']] = (data[['1900', '1901', '1902', '1903', '1904', 
                                                            '1905', '1906', '1907', '1908', '1909', 
                                                            '1910', '1911', '1912', '1913', '1914', 
                                                            '1915', '1916', '1917', '1918', '1919']].divide(data['1897'], axis=0))

    # place of work
    data[['1921', '1922', '1923', '1924']] = (data[['1921', '1922', '1923', '1924']].divide(data['1920'], axis=0))

    # commute destination
    data[['1926', '1927','1928', '1929']] = (data[['1926', '1927','1928', '1929']].divide(data['1925'], axis=0))

    # main mode of commute
    data[['1931', '1932', '1933', 
          '1934', '1935', '1936']] = (data[['1931', '1932', '1933', 
                                            '1934', '1935', '1936']].divide(data['1930'], axis=0))

    # commute duration
    data[['1938', '1939','1940', '1941', '1942']] = (data[['1938', '1939','1940', '1941', '1942']].divide(data['1937'], axis=0))

    # mobility status 1 year ago
    data[['2231', '2232', '2233', '2234', 
          '2235', '2236', '2237', '2238']] = (data[['2231', '2232', '2233', '2234', 
                                                    '2235', '2236', '2237', '2238']].divide(data['2230'], axis=0))
    # mobility status 5 years ago
    data[['2240', '2241', '2242', '2243', 
          '2244', '2245', '2246', '2247']] = (data[['2240', '2241', '2242', '2243', 
                                                    '2244', '2245', '2246', '2247']].divide(data['2239'], axis=0))

    return data

# This code is retrieved from this notebook: https://github.com/willgeary/covid-nyc-dasymetric-map/blob/master/notebook.ipynb
# Creating an H3 Hexagon Grid
def create_hexgrid(polygon, hex_res, geometry_col='geometry', map_zoom=12, buffer=0.000,
                   stroke_weight=0.5, stroke_color='blue', plot=True):
    """ Takes in a geopandas geodataframe, the desired resolution, the specified geometry column
        and some map parameters to create a hexagon grid (and potentially plot the hexgrid
    """
    centroid = list(polygon.centroid.values[0].coords)[0]
    fol_map = folium.Map(location=[centroid[1], centroid[0]], zoom_start=map_zoom,
                         tiles='cartodbpositron')

    # Explode multipolygon into individual polygons
    exploded = polygon.explode().reset_index(drop=True)

    # Master lists for geodataframe
    hexagon_polygon_list = []
    hexagon_geohash_list = []

    # For each exploded polygon
    for poly in exploded[geometry_col].values:

        # Reverse coords for original polygon
        coords = list(poly.exterior.coords)
        reversed_coords = []
        for i in coords:
            reversed_coords.append([i[1], i[0]])

        # Reverse coords for buffered polygon
        buffer_poly = poly.buffer(buffer)
        buffer_coords = list(buffer_poly.exterior.coords)
        reversed_buffer_coords = []
        for i in buffer_coords:
            reversed_buffer_coords.append([i[1], i[0]])

        # Format input to the way H3 expects it
        aoi_input = {'type': 'Polygon', 'coordinates': [reversed_buffer_coords]}

        # Add polygon outline to map
        outline = reversed_coords
        outline.append(outline[0])
        outline = folium.PolyLine(locations=outline, weight=1, color='black')
        fol_map.add_child(outline)

        # Generate list geohashes filling the AOI
        geohashes = list(h3.polyfill(aoi_input, hex_res))

        # Generate hexagon polylines for Folium
        polylines = []
        lat = []
        lng = []
        for geohash in geohashes:
            polygons = h3.h3_set_to_multi_polygon([geohash], geo_json=False)
            outlines = [loop for polygon in polygons for loop in polygon]
            polyline = [outline + [outline[0]] for outline in outlines][0]
            lat.extend(map(lambda x: x[0], polyline))
            lng.extend(map(lambda x: x[1], polyline))
            polylines.append(polyline)
            hexagon_geohash_list.append(geohash)

        # Add the hexagon polylines to Folium map
        for polyline in polylines:
            my_polyline = folium.PolyLine(locations=polyline, weight=stroke_weight,
                                          color=stroke_color)
            fol_map.add_child(my_polyline)

        # Generate hexagon polygons for Shapely
        for geohash in geohashes:
            polygons = h3.h3_set_to_multi_polygon([geohash], geo_json=True)
            outlines = [loop for polygon in polygons for loop in polygon]
            polyline_geojson = [outline + [outline[0]] for outline in outlines][0]
            hexagon_polygon_list.append(shapely.geometry.Polygon(polyline_geojson))

    if plot:
        display(fol_map)

    # Create a geodataframe containing the hexagon geometries and hashes
    hexgrid_gdf = gpd.GeoDataFrame()
    hexgrid_gdf['geometry'] = hexagon_polygon_list
    id_col_name = 'hex_id_' + str(hex_res)
    hexgrid_gdf[id_col_name] = hexagon_geohash_list
    hexgrid_gdf.crs = {'init' :'epsg:4326'}

    # Drop duplicate geometries
    geoms_wkb = hexgrid_gdf["geometry"].apply(lambda geom: geom.wkb)
    hexgrid_gdf = hexgrid_gdf.loc[geoms_wkb.drop_duplicates().index]

    return hexgrid_gdf

def load_processed_data(city = None, country = None, city_initials = None, extended_variables = True):

    if extended_variables == False:

        # Load the names of used variables 
        if country == 'canada':
            variable_names = pd.read_csv(f'../../variables/{city}_short_variable_names.csv')['variable_name'].tolist()
            geometry = gpd.read_file(f'../../data/processed/geometry/{country}/{city}.json')

        if country == 'united_states':
            variable_names = pd.read_csv(f'../../variables/{city}_short.csv').columns.tolist()
            geometry = gpd.read_file(f'../../data/processed/geometry/{country}/{city}.geojson')

    else:
        if country == 'canada':
            variable_names = pd.read_csv(f'../../variables/{city}_variable_names.csv')['variable_name'].tolist()
            geometry = gpd.read_file(f'../../data/processed/geometry/{country}/{city}.json')

        if country == 'united_states':
            variable_names = pd.read_csv(f'../../variables/{city}.csv').columns.tolist()
            geometry = gpd.read_file(f'../../data/processed/geometry/{country}/{city}.geojson')
            
    # Load the census data and accessibility points
    
    if extended_variables == False:

        data = pd.read_csv(f'../../data/interim/preprocessed/{city}_short_winsorized.csv') # CHANGE THIS TO short_winsorized.csv once script run!

        if city == 'montréal':
            city = 'montreal'

        labels = pd.read_csv(f'../../models/{country}/{city}/cc/cluster_labels_short.csv')
    else:
        data = pd.read_csv(f'../../data/interim/preprocessed/{city}_winsorized.csv')

        if city == 'montréal':
            city = 'montreal'

        if country == 'Canada':
            labels = pd.read_csv(f'../../models/{country}/{city}/cc/cluster_labels_no.csv')
        else:
            labels = pd.read_csv(f'../../models/{country}/{city}/cc/cluster_labels.csv')

#     access = gpd.read_file(f'../../data/processed/accessibility/pois/points_access/{city_initials}_access.shp')
    # Assign variable names to data
    data.columns = variable_names

    gdf = pd.merge(geometry, data, left_index=True, right_index=True)
    gdf = gpd.GeoDataFrame(gdf, geometry='geometry')

    if country == 'canada':
        crs = 3347

    if country == 'united_states':
        crs = 4326

    gdf.crs = {'init': f'epsg:{crs}'}

    if city == 'montréal':
        city = 'montreal'

    gdf['kmodes'] = labels['kmodes']
    
    if city == 'houston':
    
        url = 'https://opendata.arcgis.com/datasets/f67fe01244ce4d60add8e99e8e2f3a8c_0.zip'
        r = requests.get(url)
        z = zipfile.ZipFile(io.BytesIO(r.content))

        directory = "../../data/raw/census/united_states/"

        if not os.path.exists(directory):
            print(f'Succefully created new directory {directory}')
            os.makedirs(directory)

        z.extractall(path=directory)

        limits = gpd.read_file(directory + 'City_of_Houston_City_Limits__Full_and_Limited_Purpose_Areas_.shp')
        limits['city'] = 'Houston'
        limits = limits.dissolve('city')
        limits = limits.reset_index()[['OBJECTID_1', 'geometry']].rename(columns={"OBJECTID_1": "id"})

        gdf = gpd.overlay(gdf, limits, how='intersection')
        gdf = gdf.rename(columns = {'id_1': 'id'})
    # gdf['majority'] = labels['majority']
#     print(gdf['kmodes'].value_counts())
    # print(gdf['majority'].value_counts())
    
    return gdf