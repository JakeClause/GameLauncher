import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def format_game_title(game_title):
    # Replace underscores with spaces
    return game_title.replace('_', ' ')

def download_game_cover(game_title):
    url = f"https://en.wikipedia.org/wiki/{game_title.replace(' ', '_')}"
    save_directory = './game_covers/'
    
    # Specify a user agent header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the infobox table
        infobox_table = soup.find('table', class_='infobox')
        
        if infobox_table:
            # Find the specific line with the class 'infobox-image'
            infobox_image_line = infobox_table.find('td', class_='infobox-image')
            
            if infobox_image_line:
                # Find the image URL within the infobox-image line
                image_tag = infobox_image_line.find('img')
                if image_tag:
                    image_url = image_tag['src']
                    
                    # Handle URLs starting with '//'
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    
                    # Download the image
                    image_response = requests.get(image_url, headers=headers)
                    image_response.raise_for_status()
                    
                    # Determine the filename to save
                    filename = f"{format_game_title(game_title)}.jpg"
                    filepath = os.path.join(save_directory, filename)
                    
                    # Save the image locally
                    with open(filepath, 'wb') as f:
                        f.write(image_response.content)
                    
                    print(f"Successfully downloaded and saved '{game_title}' cover image as '{filename}' in '{save_directory}'")
                else:
                    print(f"No image found in 'infobox-image' line for '{game_title}' on Wikipedia")
            else:
                print(f"No 'infobox-image' line found in infobox table for '{game_title}' on Wikipedia")
        else:
            print(f"No infobox table found for '{game_title}' on Wikipedia")
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching or downloading cover image: {e}")
