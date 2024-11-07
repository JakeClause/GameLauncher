import os
from cover_downloader import download_game_cover, format_game_title
from img_resizer import resize_images

def main():
    # Directory settings
    game_title = input("Enter the title of the game (e.g., The Sims 3): ")
    input_folder = "./game_covers/"
    output_folder = "./game_covers/resized_imgs/"
    width = 320
    height = 400

    # Download cover image
    download_game_cover(game_title)

    # Resize downloaded image
    resize_images(input_folder, output_folder, width, height)
    print("Images resized and saved to", output_folder)

if __name__ == "__main__":
    main()
