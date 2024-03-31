"""
Korean Dictionary Module

This module provides functions to interact with the Korean dictionary Open API. It allows users to search for Korean words and retrieve their definitions and translations.

Provide a word as input to the 'get_word_info' function to receive a list of dictionaries containing information about the word.
"""

import os
import requests
import xmltodict
from dotenv import load_dotenv
from class_interaction_objects import SearchObject

load_dotenv()

URL = "https://krdict.korean.go.kr/api/search"

def get_search_results(word):
    search_results = []
    params = {
        "key": os.getenv("KOREAN_DICT_API_KEY"),
        "type_search": "search",
        "q": word,
        "part": "word",
        "sort": "dict",
        "translated": "y",
        "trans_lang": "1"
    }
    
    try:
        response = requests.get(URL, params)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        return f"HTTP Error: {errh}"
    except requests.exceptions.ConnectionError as errc:
        return f"Error Connecting: {errc}"
    except requests.exceptions.Timeout as errt:
        return f"Timeout Error: {errt}"
    except requests.exceptions.RequestException as err:
        return f"Oops: Something Else {err}"
    
    else:
        dict_data = xmltodict.parse(response.content)["channel"]
        
        if dict_data["total"] == "0":
            return None
        
        search_items = dict_data["item"]
        if not isinstance(search_items, list):
            search_items = [search_items]

        sense_data = search_items[0]["sense"]
        if not isinstance(sense_data, list):
            sense_data = [sense_data]
        
        # construct the output as a list of search objects
        for i, sense in enumerate(sense_data):
            search_obj = SearchObject(
                "S-" + search_items[0]["target_code"] + str(i),
                search_items[0]["word"],
                sense["definition"],
                sense["translation"]["trans_word"],
                sense["translation"]["trans_dfn"]
            )
            search_results.append(search_obj)
            
        return search_results
