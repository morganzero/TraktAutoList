import os
import json
import requests
import time

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

def get_user_input():
    config = load_config()

    if 'client_id' not in config:
        config['client_id'] = input("Enter your Trakt Client ID: ")
    else:
        print(f"Using stored Client ID: {config['client_id']}")

    if 'client_secret' not in config:
        config['client_secret'] = input("Enter your Trakt Client Secret: ")
    else:
        print(f"Using stored Client Secret: {config['client_secret']}")

    save_config(config)
    return config['client_id'], config['client_secret']

def get_authorization_code(client_id, redirect_uri):
    auth_url = f"https://trakt.tv/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
    print(f"Go to the following URL in your browser and authorize the application:")
    print(auth_url)
    auth_code = input("Enter the authorization code you received: ")
    return auth_code

def get_access_token(client_id, client_secret, redirect_uri, auth_code):
    token_url = "https://trakt.tv/oauth/token"
    data = {
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    response = requests.post(token_url, data=data)
    
    response.raise_for_status()
    return response.json()

def read_media_list(file_name):
    with open(file_name, 'r') as file:
        items = [line.strip() for line in file.readlines()]
    return items

def search_media(media_title, media_type, headers):
    media_type_plural = 'movies' if media_type == 'movie' else 'shows'
    search_url = f"https://api.trakt.tv/search/{media_type_plural}"
    response = requests.get(search_url, params={"query": media_title}, headers=headers)
    response.raise_for_status()
    results = response.json()
    if results:
        media_key = 'movie' if media_type == 'movie' else 'show'
        return results[0][media_key]['ids']['trakt']
    return None

def add_media_to_list(media_ids, headers, add_to_list_url):
    payload = {
        "movies": [{"ids": {"trakt": media_id}} for media_type, media_id in media_ids if media_type == 'movie'],
        "shows": [{"ids": {"trakt": media_id}} for media_type, media_id in media_ids if media_type == 'show']
    }
    response = requests.post(add_to_list_url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def create_new_list(username, headers):
    list_name = input("Enter the name of the new list: ")
    list_description = input("Enter the description of the new list: ")
    list_privacy = input("Enter the privacy of the new list (private/public): ")
    list_slug = input("Enter the slug for the new list: ")
    
    payload = {
        "name": list_name,
        "description": list_description,
        "privacy": list_privacy,
        "display_numbers": False,
        "allow_comments": True,
        "sort_by": "rank",
        "sort_how": "asc"
    }
    
    create_list_url = f"https://api.trakt.tv/users/{username}/lists"
    response = requests.post(create_list_url, json=payload, headers=headers)
    response.raise_for_status()
    return list_slug

def get_media_items():
    use_existing = input("Do you want to use the items.txt file? (yes/no): ").strip().lower()
    if use_existing == 'yes' and os.path.exists('items.txt'):
        return read_media_list('items.txt')
    else:
        print("Enter your media items (type 'done' when finished):")
        items = []
        while True:
            item = input()
            if item.lower() == 'done':
                break
            items.append(item)
        return items

def main():
    config = load_config()
    CLIENT_ID, CLIENT_SECRET = get_user_input()
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

    print("1: Create new list")
    print("2: Update existing list")
    choice = input("Choose an option (1 or 2): ").strip()

    if choice == '1':
        USERNAME = input("Enter your Trakt Username: ")
        LIST_SLUG = create_new_list(USERNAME, HEADERS)
        config['username'] = USERNAME
        config['list_slug'] = LIST_SLUG
        save_config(config)
    elif choice == '2':
        use_stored = input("Do you want to update the list with values stored in config.json? (yes/no): ").strip().lower()
        if use_stored == 'yes':
            if 'username' in config and 'list_slug' in config:
                USERNAME = config['username']
                LIST_SLUG = config['list_slug']
            else:
                print("No stored values found. Please enter details.")
                USERNAME = input("Enter your Trakt Username: ")
                LIST_SLUG = input("Enter the slug of your Trakt list: ")
                config['username'] = USERNAME
                config['list_slug'] = LIST_SLUG
                save_config(config)
        else:
            USERNAME = input("Enter your Trakt Username: ")
            LIST_SLUG = input("Enter the slug of your Trakt list: ")

    media_items = get_media_items()
    media_type = input("Are these items Movies or TV Shows? (movie/tv): ").strip().lower()

    ADD_TO_LIST_URL = f"https://api.trakt.tv/users/{USERNAME}/lists/{LIST_SLUG}/items"

    media_ids = []
    for item in media_items:
        media_title = item.strip()

        print(f"Searching for {media_type}: {media_title}")
        media_id = search_media(media_title, media_type, HEADERS)
        if media_id:
            media_ids.append((media_type, media_id))
            print(f"Found {media_type} ID: {media_id}")
        else:
            print(f"{media_type} not found: {media_title}")

    # Adding media in batches to avoid rate limiting
    batch_size = 10
    for i in range(0, len(media_ids), batch_size):
        batch = media_ids[i:i+batch_size]
        print(f"Adding batch: {batch}")
        result = add_media_to_list(batch, HEADERS, ADD_TO_LIST_URL)
        print(f"Result: {result}")
        time.sleep(5)  # Adding delay to avoid rate limiting

if __name__ == "__main__":
    main()
