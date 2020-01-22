from flask import Flask
import requests
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from time import mktime
from time import gmtime, strptime

# Global Variable Section
WEB_URL = 'https://ghibliapi.herokuapp.com/'
HEADERS = {'Content-Type': 'application/json'}
SERVICE_PORT = 8000
FMT = '%H:%M:%S'
LAST_VISITED = datetime.strptime('00:00:00', FMT)
SINGLE_MINUTE_IN_SECONDS = 60

# Global variable for data structures
title = []
people_dict = {}
movie_people_dict = {}


app = Flask(__name__)


def get_movie_list():
    """
    Get movie list from the website
    """
    try:
        response_movie = requests.get(WEB_URL + 'films',
                                      headers=HEADERS)
    except Exception as excep:
        app.logger.error('Error occurred while getting '
                         'movie list from web site' + str(excep))
    # Convert it to json
    movie_list_json = json.loads(response_movie.text)
    for item in movie_list_json:
        title.append(item['title'])
    return title


def get_movie_name_from_dict(url_list):
    """
    Get movie name from the movie url
    """
    movie_list = []
    try:
        for url in url_list:
            response_movie_name = requests.get(url, headers=HEADERS)
            response_movie_name_json = json.loads(response_movie_name.text)
            movie_list.append(response_movie_name_json['title'])
    except Exception as excep:
        app.logger.error('Error occurred while getting '
                         'movie list from the movie id' + str(excep))
    return movie_list


def get_people_list():
    """
    Get people list from the website and retrieve
    corresponding movie url
    """
    try:
        response_people = requests.get(WEB_URL + 'people',
                                       headers=HEADERS)
    except Exception as excep:
        app.logger.error('Error occurred while getting '
                         'people list from the web site' + str(excep))
    people_list_json = json.loads(response_people.text)
    for item in people_list_json:
        people_dict[item['name']] = get_movie_name_from_dict(item['films'])
    return people_dict


def get_time_diff(new_time):
    """
    Get time difference between consecutive requests
    """
    new_time_formatted = new_time.strftime("%H:%M:%S")
    last_visited_formatted = LAST_VISITED.strftime("%H:%M:%S")
    return datetime.strptime(new_time_formatted, FMT) - datetime.\
        strptime(last_visited_formatted, FMT)


def get_movie_people_relation():
    """
    Get the relation between movie title and
    the corresponding people and return as dict
    """
    for item in title:
        for key in people_dict.keys():
            for movie_title in people_dict[key]:
                if item == movie_title:
                    if item in movie_people_dict.keys():
                        if key not in movie_people_dict[item]:
                            movie_people_dict[item] += ',' + key
                    else:
                        movie_people_dict[item] = key
                else:
                    if item not in movie_people_dict.keys():
                        movie_people_dict[item] = ''
    return movie_people_dict


@app.route('/movies/')
def show_list_of_movies():
    """
    API endpoint to get list of movies
    This operation is done in three steps
    a) First get the list of movies
    b) Get the list of people and their corresponding movies
    c) Get the relationship between Movies and the corresponding people
    d) Show the result in the Rest API
    """
    global LAST_VISITED
    output_json = ""
    new_time = datetime.now()
    time_diff = get_time_diff(new_time)
    # If the time difference between consecutive request
    # is more than a minute, then application will fetch
    # Data from the website
    # Else, it will show the already stored data
    if time_diff.seconds > SINGLE_MINUTE_IN_SECONDS:
        try:
            # Get movie list from the web API
            get_movie_list()
            # Get People list from the API
            get_people_list()
            # Enquire in people_dict for the
            get_movie_people_relation()
            # Assign the latest request time to the variable
            LAST_VISITED = new_time
        except Exception as excep:
            app.logger.error('Error occurred while generating relationship'
                             'between Movie title and people' + str(excep))
    for key_item in movie_people_dict.keys():
        output_json += json.dumps([{'movie_title': key_item,
                                    'people': movie_people_dict[key_item]}],
                                  indent=3)
    return output_json


if __name__ == "__main__":
    # Logging
    handler = RotatingFileHandler('app_logger.log', maxBytes=10000,
                                  backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=SERVICE_PORT)
