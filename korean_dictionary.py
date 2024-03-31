"""
Korean Dictionary Module

This module provides functions to interact with the Korean dictionary Open API. It allows users to search for Korean words and retrieve their definitions and translations.

Provide a word as input to the 'get_word_info' function to receive a list of dictionaries containing information about the word.
"""

import os
import requests
import xmltodict
from dotenv import load_dotenv

load_dotenv()

URL = "https://krdict.korean.go.kr/api/search"

def get_word_info(word):
    params = dict(key=os.getenv("KOREAN_DICT_API_KEY"), type_search="search", q=word, part="word", sort="dict", translated="y", trans_lang="1")
    results = []

    try:
        response = requests.get(URL, params)
        response.raise_for_status()
        
    except requests.exceptions.HTTPError as errh:
        return "HTTP Error: " + str(errh)
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting: " + str(errc)
    except requests.exceptions.Timeout as errt:
        return "Timeout Error: " + str(errt)
    except requests.exceptions.RequestException as err:
        return "Oops: Something Else " + str(err)
    
    else:
        dict_data = xmltodict.parse(response.content)["channel"]
        if dict_data["total"] == "0":
            return None
        
        sense_data = dict_data["item"][0]["sense"] if isinstance(dict_data["item"], list) else dict_data["item"]["sense"]
        print(sense_data)
        
        if not isinstance(sense_data, list):
            # turn sense_data into a list of size 1
            sense_data = [sense_data]
            
        for word in sense_data:
            word_obj = {
                "korean_word": dict_data["item"][0]["word"],
                "korean_dfn": word["definition"],
                "trans_word": word["translation"]["trans_word"],
                "trans_dfn": word["translation"]["trans_dfn"],
            }
            results.append(word_obj)
            
        return results
