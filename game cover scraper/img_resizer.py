from PIL import Image
import os

def resize_images(input_folder, output_folder, width, height):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Loop through each file in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):  # Supported image formats
            # Open the image file
            with Image.open(os.path.join(input_folder, filename)) as img:
                # Convert image to RGB mode and remove alpha channel if present
                img = img.convert("RGB")
                # Resize the image
                resized_img = img.resize((width, height), Image.LANCZOS)
                # Determine output filepath
                output_filepath = os.path.join(output_folder, filename)
                # Save the resized image to the output folder
                resized_img.save(output_filepath, quality=95)
                print(f"Resized image saved to {output_filepath}")

                # Delete the original image file
                os.remove(os.path.join(input_folder, filename))
                print(f"Original image deleted: {filename}")