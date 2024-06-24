# Trakt Auto List

This Python script allows you to create and update Trakt lists with movies or TV shows. You can either create a new list or update an existing one, and the script supports adding items from a text file or manually entering them.

## Prerequisites

- Python 3.x
- `requests` library (`pip install requests`)

## Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/morganzero/TraktAutoList.git
    cd TraktAutoList
    ```

2. **Install the required libraries:**

    ```bash
    pip install requests
    ```

3. **Prepare your `items.txt` file:**

    - Create a text file named `items.txt` in the same directory as the script.
    - List each media item on a new line. You can include both movies and TV shows. Example:

    ```
    Moon (2009)
    TV: Breaking Bad (2008)
    Coherence (2013)
    TV: The Expanse (2015)
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
        - Enter the necessary details (username, list slug, etc.) as prompted.
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
Go to the following URL in your browser and authorize the application:
https://trakt.tv/oauth/authorize?response_type=code&client_id=your_client_id&redirect_uri=urn:ietf:wg:oauth:2.0:oob
Enter the authorization code you received: your_authorization_code
1: Create new list
2: Update existing list
Choose an option (1 or 2): 1
Enter your Trakt Username: your_username
Enter the name of the new list: Sci-Fi Movies
Enter the description of the new list: A list of underrated sci-fi movies.
Enter the privacy of the new list (private/public): private
Enter the slug for the new list: sci-fi-movies
Do you want to use the items.txt file? (yes/no): yes
Are these items Movies or TV Shows? (movie/tv): movie
Searching for movie: Moon (2009)
Found movie ID: 12345
Searching for movie: Coherence (2013)
Found movie ID: 67890
...
Adding batch: [('movie', 12345), ('movie', 67890), ...]
Result: {'added': {'movies': 10, 'shows': 0}, 'existing': {'movies': 0, 'shows': 0}, 'not_found': {'movies': [], 'shows': []}}
```

## Notes
- Ensure your items.txt file is correctly formatted with each media item on a new line.
- The script handles both movies and TV shows, prompting you to specify the type for correct API usage.

## License
- This project is licensed under the MIT License. See the LICENSE file for details.
