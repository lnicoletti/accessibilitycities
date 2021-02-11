import itertools
from census_area import Census
import geopandas as gpd
import pandas as pd

## variable codes:
# area name = 'NAME'

### population metrics
# total population = 'B00001_001E'
# Estimate!!Median age --!!Total = 'B01002_001E'
# average household size = 'B25010_001E'
# total households = 'B11001_001E'

### immigration
# Estimate!!Total!!U.S. citizen = 'B05001_002E', 'B05001_003E', 'B05001_004E', 'B05001_005E', 'B05001PR_002E', 'B05001PR_003E', 'B05001PR_004E', 'B05001PR_005E'
# Estimate!!Total!!Not a U.S. citizen = 'B05001_006E', 'B05001PR_006E'

### ethnicity
# Estimate!!Total!!White alone = 'B02001_002E'
# visible minority population = 'B02001_003E', 'B02001_004E', 'B02001_005E', 'B02001_006E', 'B02001_007E', 'B02001_008E', 'B02001_009E'

### Household metrics
# Estimate!!Total!!Family households!!Married-couple family = 'B11001_003E'
# Single parent = 'B11001_005E', 'B11001_006E'
# Estimate!!Total!!Nonfamily households = 'B11001_007E'

### Income
# Estimate!!Median household income in the past 12 months (in 2018 inflation-adjusted dollars) = 'B19013_001E'
# Estimate!!Aggregate household income in the past 12 months (in 2018 inflation-adjusted dollars) = 'B19025_001E'
# Estimate!!Per capita income in the past 12 months (in 2018 inflation-adjusted dollars) = 'B19301_001E'

### language
# Estimate!!Total!!Speak only English = 'B16001_002E'
# Estimate!!Total!!Speak only English = 'B06007_002E'
# Estimate!!Total!!Speak other languages!!Speak English less than "very well" = 'B06007_008E'
# Estimate!!Total!!Speak other languages!!Speak English "very well" = 'B06007_007E'

### housing
# Estimate!!Total (TOTAL POPULATION IN OCCUPIED HOUSING UNITS BY TENURE) = 'B25008_001E'
# Estimate!!Total!!Owner occupied = 'B25008_002E'
# Estimate!!Total!!Renter occupied = 'B25008_003E'
# Estimate!!Median monthly housing costs = 'B25105_001E'
# Estimate!!Median value --!!Total = 'B25107_001E'
# Estimate!!Aggregate value (dollars) = 'B25108_001E'
# Estimate!!Median gross rent = 'B25064_001E'
# Estimate!!Aggregate gross rent = 'B25065_001E'
# Estimate!!Total (gross rent) = 'B25063_001E'
# Estimate!!Total (GROSS RENT AS A PERCENTAGE OF HOUSEHOLD INCOME IN THE PAST 12 MONTHS) = 'B25070_001E'
# spending less than 30% of income on gross rent = 'B25070_002E', 'B25070_003E', 'B25070_004E', 'B25070_005E', 'B25070_006E'
# spending more than 30% of income on gross rent = 'B25070_007E', 'B25070_008E', 'B25070_009E', 'B25070_010E'
# Estimate!!Median gross rent as a percentage of household income = 'B25071_001E'
# Estimate!!Median number of rooms = 'B25018_001E'
# Estimate!!Aggregate number of rooms = 'B25019_001E'

## education
# Estimate!!Total (EDUCATIONAL ATTAINMENT FOR THE POPULATION 25 YEARS AND OVER) = 'B15003_001E'
# less than high school diploma = 'B15003_002E', 'B15003_003E', 'B15003_004E', 'B15003_005E', 'B15003_006E', 'B15003_007E', 'B15003_008E', 'B15003_009E', 'B15003_010E', 'B15003_011E', 'B15003_012E', 'B15003_013E', 'B15003_014E', 'B15003_015E', 'B15003_016E'
# Estimate!!Total!!Regular high school diploma = 'B15003_017E'
# Estimate!!Total!!Associate's degree = 'B15003_021E'
# Estimate!!Total!!Bachelor's degree = 'B15003_022E'
# Estimate!!Total!!Master's degree = 'B15003_023E'
# Estimate!!Total!!Professional school degree = 'B15003_024E'
# Estimate!!Total!!Doctorate degree = 'B15003_025E'

## employment status
# Estimate!!Total (EMPLOYMENT STATUS FOR THE POPULATION 16 YEARS AND OVER) = 'B23025_001E'	
# Estimate!!Total!!In labor force!!Civilian labor force!!Employed = 'B23025_004E'
# Estimate!!Total!!In labor force!!Civilian labor force!!Unemployed = 'B23025_005E'

def retrieve_us_data(cities_geo = None, API_key = "9320d66d590a2cc9bb46c24b1c4144d1bc7eccfb", year = None):
    
    '''Retrieve variables of interest data from the US census API.
    
    Args:
        cities_geo (list of lists) : state and city FIPS code for each city of interest, for example [[17, 14000], [36, 36061]] for Chicago and NYC, 
        (use [[]] for single city)
        API_key (string) : API_key for US census (default is key of Leonardo Nicoletti)
        year (int) : year of interest (default is latest year in acs5 dataset)
    
    Returns:
        list : list of census GeoDataFrames
    
    '''
    name = ['NAME']
    pop_metrics = ['B00001_001E', 'B01002_001E']

    us_citizen = ['B05001_002E', 'B05001_003E', 'B05001_004E', 'B05001_005E', 'B05001PR_002E', 'B05001PR_003E', 'B05001PR_004E', 'B05001PR_005E']
    immigrant = ['B05001_006E', 'B05001PR_006E']

    white = ['B02001_002E']
    minority = ['B02001_003E', 'B02001_004E', 'B02001_005E', 'B02001_006E', 'B02001_007E', 'B02001_008E', 'B02001_009E']

    tot_households = ['B11001_001E']
    average_household_size = ['B25010_001E']
    married_households =['B11001_003E']
    single_parent = ['B11001_005E', 'B11001_006E']
    nonfamily_households = ['B11001_007E']


    median_household_income = ['B19013_001E']
    aggregate_household_income = ['B19025_001E']
    per_capita_income = ['B19301_001E']

    only_english = ['B16001_002E', 'B06007_002E']
    other_languages_bad_english = ['B06007_008E']
    other_languages_good_english = ['B06007_007E']

    tot_pop_in_housing = ['B25008_001E']
    owner = ['B25008_002E']
    renter = ['B25008_003E']
    median_monthly_housing_costs = ['B25105_001E']
    median_house_value = ['B25107_001E']
    aggregate_house_value = ['B25108_001E']
    total_gross_rent = ['B25063_001E']
    median_gross_rent = ['B25064_001E']
    aggregate_gross_rent = ['B25065_001E']
    tot_gross_rent_as_percent_of_income = ['B25070_001E']
    less_than_30_of_income = ['B25070_002E', 'B25070_003E', 'B25070_004E', 'B25070_005E', 'B25070_006E']
    more_than_30_of_income = ['B25070_007E', 'B25070_008E', 'B25070_009E', 'B25070_010E']
    median_gross_rent_as_percent_of_income = ['B25071_001E']
    median_n_rooms = ['B25018_001E']
    aggregate_n_rooms = ['B25019_001E']

    tot_edu_attainment = ['B15003_001E']
    less_than_high_school = ['B15003_002E', 'B15003_003E', 'B15003_004E', 'B15003_005E', 'B15003_006E', 'B15003_007E', 'B15003_008E', 
                             'B15003_009E', 'B15003_010E', 'B15003_011E', 'B15003_012E', 'B15003_013E', 'B15003_014E', 'B15003_015E', 'B15003_016E']
    high_school = ['B15003_017E']
    associates_degree = ['B15003_021E']
    bachelors_degree = ['B15003_022E']
    masters_degree = ['B15003_023E']
    professional_school_degree = ['B15003_024E']
    doctorate_degree = ['B15003_025E']

    tot_employment_status = ['B23025_001E']	
    employed = ['B23025_004E']
    unemployed = ['B23025_005E']

    categories_of_choice = [name,
                            pop_metrics,
                            us_citizen,
                            immigrant, 
                            white,
                            minority,
                            tot_households,
                            average_household_size,
                            married_households, 
                            single_parent,
                            nonfamily_households,
                            median_household_income,
                            aggregate_household_income,
                            per_capita_income,
                            only_english, 
                            other_languages_bad_english,
                            other_languages_good_english, 
                            tot_pop_in_housing,
                            owner,
                            renter,
                            median_monthly_housing_costs,
                            median_house_value, 
                            aggregate_house_value,
                            total_gross_rent,
                            median_gross_rent,
                            aggregate_gross_rent,
                            tot_gross_rent_as_percent_of_income, 
                            less_than_30_of_income,
                            more_than_30_of_income,
                            median_gross_rent_as_percent_of_income,
                            median_n_rooms,
                            aggregate_n_rooms,
                            tot_edu_attainment,
                            less_than_high_school, 
                            high_school,
                            associates_degree,
                            bachelors_degree,
                            masters_degree,
                            professional_school_degree,
                            doctorate_degree,
                            tot_employment_status,
                            employed,
                            unemployed]

    categories_of_choice = list(itertools.chain.from_iterable(categories_of_choice))
    
    # API key for US census and year of interest
    c = Census(API_key, year = year)
        
    cities_census = []

    for city in cities_geo:
        city_census = c.acs5.state_place_blockgroup(tuple(categories_of_choice), city[0], city[1], return_geometry=True)
        city_gdf = gpd.GeoDataFrame.from_features(city_census['features'])
        cities_census.append(city_gdf)
        print("City collected successfully!")
        
    return [city_census for city_census in cities_census]


def prepare_us_data(gdf=None):
    
    '''Prepare data for further modeling.
    
    Args:
        gdf (GeoDataFrame) :
    
    Returns:
        df (DataFrame) : 
    
    '''
    # How many polygons do we have before cleaning?
    n_polygons = gdf.shape[0]
    print(f'The number of polygons in the shape file = {n_polygons}')
    
    # drop geometry
    df = gdf.drop('geometry', axis=1)
    
    # delete null columns and fill missing values
    df = df.dropna(axis = 1, how = 'all').fillna(method = 'ffill')
    
    # drop unwanted columns
    data = df.drop(['MTFCC', 'OID', 'STATE', 'COUNTY', 'TRACT', 'BLKGRP', 'BASENAME','NAME', 'LSADC', 
                    'FUNCSTAT', 'AREAWATER', 'CENTLAT', 'CENTLON', 'INTPTLAT', 'INTPTLON', 'OBJECTID', 'block group'], axis = 1)
    
    # replace -6666666.0 values by 0 (this seems to be a glitch in the census data)
    data.replace(-666666666.0, 0, inplace=True)
    
    # How many polygons do we have after cleaning?
    print(f'The number of polygons in data file = {data["GEOID"].unique().shape[0]}')
    
    # How many variables do we have?
    n_variables = len(data.reset_index().drop('GEOID', axis = 1).columns)
    print(f'Total number of variables = {n_variables}')
    
    return data

def scale_us_variables(data):
    
    '''Scale the data by total number of respondents within each census block.

    Args:
        data (DataFrame) : Raw data frame with unselected variables, as outputted by the prepare_us_data function.

    Returns:
        result (DataFrame) : Scaled data frame

    '''
    
    ## immigration + ethnicity + language
    # US citizen column
#     data['B05001_US'] = data[['B05001_002E', 'B05001_003E', 'B05001_004E', 'B05001_005E', 
#                                 'B05001PR_002E', 'B05001PR_003E', 'B05001PR_004E', 'B05001PR_005E']].sum(axis=1)
    
    # Not US citizen column
#     data['B05001_NUS'] = data[['B05001_006E', 'B05001PR_006E']].sum(axis=1)
    
    # visible minority column
    data['B05001_VM'] = data[['B02001_003E', 'B02001_004E', 'B02001_005E', 
                                'B02001_006E', 'B02001_007E', 'B02001_008E', 'B02001_009E']].sum(axis=1)
    # total sampled ethnicity
    data['B05001_TOT'] = data[['B02001_002E','B05001_VM']].sum(axis=1)
    # immigration + ethnicity + language (divide by total population)
    data[[#'B05001_US', 'B05001_NUS', #'B16001_002E', 'B06007_002E','B06007_008E', 'B06007_007E']] 
          'B02001_002E','B05001_VM']] = (data[[#'B05001_US', 'B05001_NUS', 'B06007_002E','B16001_002E', 'B06007_008E', 'B06007_007E'
                                                  'B02001_002E', 'B05001_VM']].divide(data['B05001_TOT'], axis=0))

    ## housing variables
    # spend more than 30% of income on housing column
    data['B25070_M30'] = data[['B25070_007E', 'B25070_008E', 'B25070_009E', 'B25070_010E']].sum(axis=1)
    
    # spend less than 30% of income on housing column
    data['B25070_L30'] = data[['B25070_002E', 'B25070_003E', 'B25070_004E', 'B25070_005E', 'B25070_006E']].sum(axis=1)
    
    # housing variables (divide by total population sampled)
    data[['B25008_002E', 'B25008_003E', 
          'B25070_M30', 'B25070_L30']] = (data[['B25008_002E', 'B25008_003E', 
                                               'B25070_M30', 'B25070_L30']].divide(data['B25008_001E'], axis=0))

    ## education
    # less than high school column:
    data['B15003_LHS'] = data[['B15003_002E', 'B15003_003E', 'B15003_004E', 
                               'B15003_005E', 'B15003_006E', 'B15003_007E', 
                               'B15003_008E', 'B15003_009E', 'B15003_010E', 
                               'B15003_011E', 'B15003_012E', 'B15003_013E', 
                               'B15003_014E', 'B15003_015E', 'B15003_016E']].sum(axis=1)
         
    # (divide by total population sampled)
    data[['B15003_LHS', 'B15003_017E', 
          'B15003_021E', 'B15003_022E', 
          'B15003_023E', 'B15003_024E', 'B15003_025E']] = (data[['B15003_LHS', 'B15003_017E', 
                                                                 'B15003_021E', 'B15003_022E', 
                                                                 'B15003_023E', 'B15003_024E', 'B15003_025E']].divide(data['B15003_001E'], axis=0))
    
    ## Employment status (divide by total population sampled)
    data[['B23025_004E', 'B23025_005E']] = (data[['B23025_004E', 'B23025_005E']].divide(data['B23025_001E'], axis=0))
    
    ## Marital status (divide by total households)
    # single parent column
#     data['B11001_SP'] = data['B11001_005E', 'B11001_006E'].sum(axis=1)

    data[[#'B11001_SP',
          'B11001_003E', 'B11001_007E']] = (data[[#'B11001_SP', 
                                                  'B11001_003E', 'B11001_007E']].divide(data['B11001_001E'], axis=0))
    
    # Fill NaN values with zeros (result of division by zero as for when tot pop = 0 for example)
    
    data = data.fillna(0)
    
    return data

def select_us_variables(df, print_selected=False, extended_variables = False):
    '''Select variables of interest out of the whole data set.
    
    Args:
        df (DataFrame) : Data frame with all variables
    
    Returns:
        result (DataFrame) : Resulting data frame with only the variables of choice
    
    '''
    
    population = ['B00001_001E']
    age =  ['B01002_001E']

    white = ['B02001_002E']
    minority = ['B05001_VM']

    tot_households = ['B11001_001E']
    average_household_size = ['B25010_001E']
    married_households =['B11001_003E']
#     single_parent = ['B11001_005E', 'B11001_006E']
    nonfamily_households = ['B11001_007E']

    median_household_income = ['B19013_001E']
    aggregate_household_income = ['B19025_001E']
    per_capita_income = ['B19301_001E']

#     only_english = ['B16001_002E', 'B06007_002E']
#     other_languages_bad_english = ['B06007_008E']
#     other_languages_good_english = ['B06007_007E']

#     tot_pop_in_housing = ['B25008_001E']
    owner = ['B25008_002E']
    renter = ['B25008_003E']
#     median_monthly_housing_costs = ['B25105_001E']
    median_house_value = ['B25107_001E']
    aggregate_house_value = ['B25108_001E']
    total_gross_rent = ['B25063_001E']
    median_gross_rent = ['B25064_001E']
    aggregate_gross_rent = ['B25065_001E']
    tot_gross_rent_as_percent_of_income = ['B25070_001E']
    less_than_30_of_income = ['B25070_L30']
    more_than_30_of_income = ['B25070_M30']
    median_gross_rent_as_percent_of_income = ['B25071_001E']
    median_n_rooms = ['B25018_001E']
    aggregate_n_rooms = ['B25019_001E']

    tot_edu_attainment = ['B15003_001E']
    less_than_high_school = ['B15003_LHS']
    high_school = ['B15003_017E']
    associates_degree = ['B15003_021E']
    bachelors_degree = ['B15003_022E']
    masters_degree = ['B15003_023E']
    professional_school_degree = ['B15003_024E']
    doctorate_degree = ['B15003_025E']

    tot_employment_status = ['B23025_001E']	
    employed = ['B23025_004E']
    unemployed = ['B23025_005E']
    
    if extended_variables == True:
        categories_of_choice = [population,
                                age, 
                                white,
                                minority,
                                tot_households,
                                average_household_size,
                                married_households, 
    #                             single_parent,
                                nonfamily_households,
                                median_household_income,
    #                             aggregate_household_income,
    #                             per_capita_income,
    #                             only_english, 
    #                             other_languages_bad_english,
    #                             other_languages_good_english, 
    #                             tot_pop_in_housing,
                                owner,
                                renter,
    #                             median_monthly_housing_costs,
    #                             median_house_value, 
    #                             aggregate_house_value,
    #                             total_gross_rent,
                                median_gross_rent,
    #                             aggregate_gross_rent,
                                tot_gross_rent_as_percent_of_income, 
                                less_than_30_of_income,
                                more_than_30_of_income,
                                median_gross_rent_as_percent_of_income,
                                median_n_rooms,
    #                             aggregate_n_rooms,
                                less_than_high_school, 
                                high_school,
    #                             associates_degree,
                                bachelors_degree,
                                masters_degree,
                                professional_school_degree,
                                doctorate_degree,
    #                             tot_employment_status,
                                employed,
                                unemployed]


    if extended_variables == False:
        categories_of_choice = [white, minority, median_household_income, less_than_high_school,high_school, bachelors_degree, 
                                masters_degree, professional_school_degree,doctorate_degree, employed, unemployed]
        
    categories_of_choice = list(itertools.chain.from_iterable(categories_of_choice))

    if extended_variables == False:
        variable_names = ['white', 'minority', 'median_household_income', 'less_than_high_school', 'high_school', 'bachelors_degree', 
                          'masters_degree', 'professional_school_degree', 'doctorate_degree', 'employed', 'unemployed']
    
    if extended_variables == True:
        variable_names = ['population',
                            'age', 
                            'white',
                            'minority',
                            'tot_households',
                            'average_household_size',
                            'married_households', 
        #                             single_parent,
                            'nonfamily_households',
                            'median_household_income',
        #                             aggregate_household_income,
        #                             per_capita_income,
        #                             only_english, 
        #                             other_languages_bad_english,
        #                             other_languages_good_english, 
        #                             tot_pop_in_housing,
                            'owner',
                            'renter',
        #                             median_monthly_housing_costs,
        #                             median_house_value, 
        #                             aggregate_house_value,
        #                             total_gross_rent,
                            'median_gross_rent',
        #                             aggregate_gross_rent,
                            'tot_gross_rent_as_percent_of_income', 
                            'less_than_30_of_income',
                            'more_than_30_of_income',
                            'median_gross_rent_as_percent_of_income',
                            'median_n_rooms',
        #                             aggregate_n_rooms,
                            'less_than_high_school', 
                            'high_school',
        #                             associates_degree,
                            'bachelors_degree',
                            'masters_degree',
                            'professional_school_degree',
                            'doctorate_degree',
        #                             tot_employment_status,
                            'employed',
                            'unemployed']
    
    data = df[categories_of_choice]
    data.columns = variable_names
    
    # Print selected set of variables
    if print_selected:
        print(data.columns)
        
    return data