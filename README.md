# Trakt Auto List

This Python script allows you to create and update Trakt lists with movies or TV shows. You can either create a new list or update an existing one. The script supports adding items from a text file or manually entering them. It also caches search results for faster subsequent runs.

## Prerequisites

- Python 3.x
- `requests` library
- `InquirerPy` library

## Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/morganzero/TraktAutoList.git
    cd TraktAutoList
    ```

2. **Install the required libraries:**

    ```bash
    pip install requests InquirerPy
    ```

3. **Prepare your `items.txt` file:**

    - Create a text file named `items.txt` in the same directory as the script.
    - List each media item on a new line. Example:

    ```
    Moon (2009)
    Coherence (2013)
    Breaking Bad (2008)
    The Expanse (2015)
    ```

## Usage

1. **Run the script:**

    ```bash
    python TraktAutoList.py
    ```

2. **Follow the prompts:**

    - **Client ID and Secret:** Enter your Trakt Client ID and Client Secret when prompted. These will be saved for future use.
    - **Authorization:** Follow the link provided to authorize the application and enter the authorization code.
    - **Create or Update List:**
        - Select whether to create a new list or update an existing one.
        - Enter the necessary details (username, list name, etc.) as prompted.
    - **Media Items:**
        - Choose whether to use the `items.txt` file or manually enter media items.
        - Specify whether the items are movies or TV shows.

3. **Script Output:**
    - The script will search for each media item and add it to the specified Trakt list.
    - Progress and results will be printed to the console.

## Example Session

```plaintext
$ python TraktAutoList.py
Enter your Trakt Client ID: your_client_id
Enter your Trakt Client Secret: your_client_secret
Using stored username: your_username
Go to the following URL in your browser and authorize the application:
https://trakt.tv/oauth/authorize?response_type=code&client_id=your_client_id&redirect_uri=urn:ietf:wg:oauth:2.0:oob
Enter the authorization code you received: your_authorization_code
Select an option:
1. Create new list
2. Update existing list
Choice: 1
Enter the name of the new list: Sci-Fi Movies
Enter the description of the new list: A list of underrated sci-fi movies.
Privacy (private/public): private
Use the items file 'Sci-Fi Movies_items.txt'? (yes/no): yes
Items are: movie
Using URL for adding items: https://api.trakt.tv/users/your_username/lists/sci-fi-movies/items
Searching for movie: Moon (2009)
Found movie ID: 12345
Searching for movie: Coherence (2013)
Found movie ID: 67890
...
Adding batch: [('movie', 12345, 'Moon (2009)'), ('movie', 67890, 'Coherence (2013)'), ...]
Result: {'added': {'movies': 10, 'shows': 0}, 'existing': {'movies': 0, 'shows': 0}, 'not_found': {'movies': [], 'shows': []}}

Summary:
Items added:
- Moon (2009)
- Coherence (2013)
...

## Notes
- Ensure your items.txt file is correctly formatted with each media item on a new line.
- The script handles both movies and TV shows, prompting you to specify the type for correct API usage.
- Search results are cached in search_cache.json to improve performance on subsequent runs.

## License
- This project is licensed under the MIT License. See the LICENSE file for details.
