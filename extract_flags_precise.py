from PIL import Image
import os

# Load the image with all flags
img = Image.open('attached_assets/image_1761723736298.png')

# Define crop regions for each flag - more precise cropping to eliminate white borders
# Each flag appears to be roughly 60x40 pixels in the original image
# Adjusting coordinates to crop tighter
flags = {
    'cz': (75, 91, 129, 115),      # Czech Republic - tighter crop
    'de': (531, 91, 585, 115),     # Germany - tighter crop
    'fr': (331, 91, 385, 115),     # France - tighter crop
    'es': (203, 313, 257, 337),    # Spain - tighter crop
    'gb': (531, 313, 585, 337)     # United Kingdom - tighter crop
}

# Create directory for flag images
os.makedirs('static/flags', exist_ok=True)

# Extract and save each flag
for country_code, coords in flags.items():
    flag = img.crop(coords)
    # Resize to 40x30 pixels for better quality at larger sizes
    flag = flag.resize((40, 30), Image.Resampling.LANCZOS)
    flag.save(f'static/flags/{country_code}.png')
    print(f"Saved flag: {country_code}.png (40x30px)")

print("All flags extracted with precise cropping!")
