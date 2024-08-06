#!/usr/bin/env python3

import os
import json
import requests
import time
from urllib.parse import quote
from InquirerPy import prompt

CONFIG_FILE = 'config.json'
CACHE_FILE = 'search_cache.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as file:
        json.dump(cache, file, indent=4)

def get_user_input():
    config = load_config()

    if 'access_token' in config:
        change_token = prompt([{"type": "confirm", "name": "change_token", "message": "Change access token?", "default": False}])["change_token"]
        if change_token:
            config['client_id'] = prompt({"type": "input", "name": "client_id", "message": "Trakt Client ID:"})["client_id"]
            config['client_secret'] = prompt({"type": "input", "name": "client_secret", "message": "Trakt Client Secret:"})["client_secret"]
            del config['access_token']
    else:
        if 'client_id' not in config:
            config['client_id'] = prompt({"type": "input", "name": "client_id", "message": "Trakt Client ID:"})["client_id"]
        if 'client_secret' not in config:
            config['client_secret'] = prompt({"type": "input", "name": "client_secret", "message": "Trakt Client Secret:"})["client_secret"]

    if 'username' not in config:
        config['username'] = prompt({"type": "input", "name": "username", "message": "Trakt Username:"})["username"]
    else:
        use_stored_username = prompt([{"type": "confirm", "name": "use_stored_username", "message": f"Use stored username '{config['username']}'?", "default": True}])["use_stored_username"]
        if not use_stored_username:
            config['username'] = prompt({"type": "input", "name": "username", "message": "Trakt Username:"})["username"]

    save_config(config)
    return config

def get_authorization_code(client_id, redirect_uri):
    auth_url = f"https://trakt.tv/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
    print(f"Authorize the app by visiting: {auth_url}")
    return prompt({"type": "input", "name": "auth_code", "message": "Authorization Code:"})["auth_code"]

def get_access_token(client_id, client_secret, redirect_uri, auth_code):
    response = requests.post("https://trakt.tv/oauth/token", data={
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    })
    response.raise_for_status()
    return response.json()

def reauthorize(client_id, client_secret, redirect_uri):
    auth_code = get_authorization_code(client_id, redirect_uri)
    tokens = get_access_token(client_id, client_secret, redirect_uri, auth_code)
    return tokens['access_token']

def read_media_list(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            return [line.strip() for line in file.readlines()]
    return []

def search_media(media_title, media_type, headers, cache):
    if media_title in cache:
        return cache[media_title]

    search_url = f"https://api.trakt.tv/search/{'show' if media_type == 'tv' else 'movie'}"
    response = requests.get(search_url, params={"query": media_title}, headers=headers)
    response.raise_for_status()
    results = response.json()
    if results:
        media_id = results[0]['show' if media_type == 'tv' else 'movie']['ids']['trakt']
        cache[media_title] = media_id
        return media_id
    return None

def get_existing_list_items(username, list_name, headers):
    encoded_list_name = quote(list_name)
    get_list_url = f"https://api.trakt.tv/users/{username}/lists/{encoded_list_name}/items"
    response = requests.get(get_list_url, headers=headers)
    if response.status_code == 404:
        return set()  # Return an empty set if the list is not found
    response.raise_for_status()
    existing_items = {item['movie']['ids']['trakt'] if 'movie' in item else item['show']['ids']['trakt'] for item in response.json()}
    return existing_items

def add_media_to_list(media_ids, headers, add_to_list_url):
    payload = {
        "movies": [{"ids": {"trakt": media_id}} for media_type, media_id, _ in media_ids if media_type == 'movie'],
        "shows": [{"ids": {"trakt": media_id}} for media_type, media_id, _ in media_ids if media_type == 'tv']
    }

    print(f"Payload: {payload}")  # Debug statement

    response = requests.post(add_to_list_url, json=payload, headers=headers)
    print(f"Response Status Code: {response.status_code}")  # Debug statement
    print(f"Response Content: {response.content}")  # Debug statement
    
    response.raise_for_status()
    return response.json()

def create_new_list(username, headers):
    answers = prompt([
        {"type": "input", "name": "list_name", "message": "New List Name:"},
        {"type": "input", "name": "list_description", "message": "Description:"},
        {"type": "list", "name": "list_privacy", "message": "Privacy:", "choices": ["private", "public"]}
    ])
    
    payload = {
        "name": answers["list_name"],
        "description": answers["list_description"],
        "privacy": answers["list_privacy"],
        "display_numbers": False,
        "allow_comments": True,
        "sort_by": "rank",
        "sort_how": "asc"
    }
    
    create_list_url = f"https://api.trakt.tv/users/{username}/lists"
    response = requests.post(create_list_url, json=payload, headers=headers)
    
    if response.status_code == 201:
        print(f"Created list: {answers['list_name']}")
        return answers["list_name"]
    elif response.status_code == 420:
        raise Exception("Received 420 Client Error from Trakt API. Please check your payload or try again later.")
    else:
        response.raise_for_status()

def list_exists(username, list_name, headers):
    encoded_list_name = quote(list_name.lower().replace(" ", "-"))
    check_list_url = f"https://api.trakt.tv/users/{username}/lists/{encoded_list_name}"
    response = requests.get(check_list_url, headers=headers)
    return response.status_code == 200

def get_media_items(list_name):
    items_file = f"{list_name}_items.txt"
    use_existing = prompt([{"type": "confirm", "name": "use_existing", "message": f"Use the items file '{items_file}'?", "default": True}])["use_existing"]
    if use_existing:
        return read_media_list(items_file)
    print("Enter your media items (type 'done' when finished):")
    items = []
    while True:
        item = input()
        if item.lower() == 'done':
            break
        items.append(item)
    with open(items_file, 'w') as file:
        file.write("\n".join(items) + "\n")
    return items

def get_user_lists(username, headers):
    response = requests.get(f"https://api.trakt.tv/users/{username}/lists", headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    config = get_user_input()
    cache = load_cache()
    CLIENT_ID = config.get('client_id')
    CLIENT_SECRET = config.get('client_secret')
    USERNAME = config['username']
    REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

    if 'access_token' in config:
        ACCESS_TOKEN = config['access_token']
        print("Using stored access token.")
    else:
        auth_code = get_authorization_code(CLIENT_ID, REDIRECT_URI)
        tokens = get_access_token(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, auth_code)
        ACCESS_TOKEN = tokens['access_token']
        config['access_token'] = ACCESS_TOKEN
        save_config(config)

    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "trakt-api-version": "2",
        "trakt-api-key": CLIENT_ID,
    }

    try:
        choice = prompt([{
            "type": "list",
            "name": "menu_choice",
            "message": "Select an option:",
            "choices": [
                {"name": "Create new list", "value": "create"},
                {"name": "Update existing list", "value": "update"}
            ]
        }])["menu_choice"]

        if choice == "create":
            LIST_NAME = create_new_list(USERNAME, HEADERS)
            config['list_name'] = LIST_NAME
            save_config(config)
        elif choice == "update":
            if 'list_name' in config:
                print(f"Stored list: {config['list_name']}")
                use_stored = prompt([{"type": "confirm", "name": "use_stored", "message": "Use this list?", "default": True}])["use_stored"]
                if use_stored:
                    LIST_NAME = config['list_name']
                else:
                    user_lists = get_user_lists(USERNAME, HEADERS)
                    list_choices = [{"name": l['name'], "value": l['name']} for l in user_lists]
                    LIST_NAME = prompt([{"type": "list", "name": "list_name", "message": "Select the list to update:", "choices": list_choices}])["list_name"]
                    config['list_name'] = LIST_NAME
                    save_config(config)
            else:
                user_lists = get_user_lists(USERNAME, HEADERS)
                list_choices = [{"name": l['name'], "value": l['name']} for l in user_lists]
                LIST_NAME = prompt([{"type": "list", "name": "list_name", "message": "Select the list to update:", "choices": list_choices}])["list_name"]
                config['list_name'] = LIST_NAME
                save_config(config)

            if not list_exists(USERNAME, LIST_NAME, HEADERS):
                print(f"List '{LIST_NAME}' does not exist. Creating it.")
                LIST_NAME = create_new_list(USERNAME, HEADERS)
                config['list_name'] = LIST_NAME
                save_config(config)

        media_items = get_media_items(LIST_NAME)
        media_type = prompt([{"type": "list", "name": "media_type", "message": "Items are:", "choices": ["movie", "tv"]}])["media_type"]

        LIST_SLUG = LIST_NAME.lower().replace(" ", "-")
        ADD_TO_LIST_URL = f"https://api.trakt.tv/users/{USERNAME}/lists/{quote(LIST_SLUG)}/items"
        print(f"Using URL for adding items: {ADD_TO_LIST_URL}")  # Debug statement

        existing_items = get_existing_list_items(USERNAME, LIST_SLUG, HEADERS)
        print(f"Existing items in the list: {existing_items}")  # Debug statement

        media_ids = []
        not_found = []
        for item in media_items:
            media_title = item.strip()
            print(f"Searching for {media_type}: {media_title}")  # Debug statement
            media_id = search_media(media_title, media_type, HEADERS, cache)
            if media_id:
                if media_id not in existing_items:
                    media_ids.append((media_type, media_id, media_title))
                else:
                    print(f"{media_type} already in list: {media_title}")
            else:
                not_found.append(media_title)
                print(f"{media_type} not found: {media_title}")

        save_cache(cache)  # Save the cache after all searches

        for i in range(0, len(media_ids), 10):
            batch = media_ids[i:i+10]
            print(f"Adding batch: {batch}")  # Debug statement
            result = add_media_to_list(batch, HEADERS, ADD_TO_LIST_URL)
            print(f"Result: {result}")  # Debug statement
            time.sleep(5)

        print("\nSummary:")
        print("Items added:")
        for _, _, title in media_ids:
            print(f"- {title}")

        if not_found:
            print("\nItems not found:")
            for title in not_found:
                print(f"- {title}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("Access forbidden. Reauthorizing...")
            ACCESS_TOKEN = reauthorize(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
            config['access_token'] = ACCESS_TOKEN
            save_config(config)
            print("Reauthorization successful. Please restart the script.")
        else:
            raise

if __name__ == "__main__":
    main()
