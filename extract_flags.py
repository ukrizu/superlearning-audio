from PIL import Image
import os

# Load the image with all flags
img = Image.open('attached_assets/image_1761723736298.png')

# Define crop regions for each flag (left, top, right, bottom)
# Measured from the image - approximate positions
flags = {
    'cz': (72, 88, 132, 118),      # Czech Republic
    'de': (528, 88, 588, 118),     # Germany
    'fr': (328, 88, 388, 118),     # France
    'es': (200, 310, 260, 340),    # Spain
    'gb': (528, 310, 588, 340)     # United Kingdom (UK)
}

# Create directory for flag images
os.makedirs('static/flags', exist_ok=True)

# Extract and save each flag
for country_code, coords in flags.items():
    flag = img.crop(coords)
    # Resize to a reasonable size (e.g., 32x24 pixels for UI)
    flag = flag.resize((32, 24), Image.Resampling.LANCZOS)
    flag.save(f'static/flags/{country_code}.png')
    print(f"Saved flag: {country_code}.png")

print("All flags extracted successfully!")
