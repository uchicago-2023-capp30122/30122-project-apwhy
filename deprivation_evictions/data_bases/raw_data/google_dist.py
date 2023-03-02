import geopandas as gpd
import random
import shapely.geometry as geometry
import pandas as pd
import requests
from random import randint
from time import sleep

API_KEY = "INSERT API KEY HERE"
ZIPCODE_PATH = "INSERT PATH TO SHAPEFILE HERE"

def define_origin_coor(num_origin):
    '''
    Opens zipcode shapefile, generates num_origin random coordinates as origin

    Inputs: 
    zipcode_path: Geojson Shapefile (path)
    num_origin: number of origin points in a zipcode boundary

    Function:
    Appends (zipcode, latitude, longitude) into a Pandas dataframe
    '''

    # Open geojson shapefile
    zipcodes = gpd.read_file(ZIPCODE_PATH)

    # Instantiate Pandas DF to store data
    points_df = pd.DataFrame(columns=['latitude', 'longitude', 'zipcode'])

    # Loop through each zipcode and generate n. random coordinates representing origin
    for _, zipcode in zipcodes.iterrows():
        for _ in range(num_origin):
            # If random point is not within zipcode boundary, randomize again
            point = None
            while not point:
                point = geometry.Point(random.uniform(zipcode.geometry.bounds[0], 
                                                        zipcode.geometry.bounds[2]),
                                    random.uniform(zipcode.geometry.bounds[1], 
                                                    zipcode.geometry.bounds[3]))
                if zipcode.geometry.contains(point):
                    points_df = points_df.append({'latitude': point.y, 
                                                    'longitude': point.x, 
                                                    'zipcode': zipcode.zip}, 
                                                    ignore_index=True)
    
    return points_df


def get_time_distance(origin, destination):
    '''
    API Call to obtain travel data from Google Distance Matrix API.

    Helper function: 
    --used in update_travel_data

    Inputs: 
    origin: starting coordinates
    destination: ending coordinates

    Returns:
    time: travel time
    distance: travel distance 
    '''
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={origin}&destinations={destination}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    #Key Error Handling: If API returns nothing, 
    #record time, distance as 0 representing missing values
    try:
        time = data['rows'][0]['elements'][0]['duration']['value']
        distance = data['rows'][0]['elements'][0]['distance']['value']
    except KeyError:
        time, distance = 0, 0

    return time, distance

def update_travel_data(destination, num_origin):
    '''
    Updates each observation in pandas df for destination (CBD)

    Inputs: 
    destination: destination either in text, or in (lat, lng)

    Function:
    Appends travel data (time_to_cbd, distance_to_cbd) into the Pandas dataframe
    ''' 
    points_df = define_origin_coor(num_origin)

    points_df['time_to_CBD'] = None
    points_df['distance_to_CBD'] = None

    for i, row in points_df.iterrows():
        origin = f"{row['latitude']},{row['longitude']}"
        while True:
            # Added try-except to handle errors when requesting
            try:
                time, distance = get_time_distance(origin, destination)
                break
            except ValueError:
                points_df = define_origin_coor(num_origin)
                row = points_df.iloc[i]
                origin = f"{row['latitude']},{row['longitude']}"
        points_df.at[i, 'time_to_CBD'] = time
        points_df.at[i, 'distance_to_CBD'] = distance
        sleep(randint(1,4))

    points_df.to_csv("./google_distancematrix.csv")


