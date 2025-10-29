from PIL import Image
import os

# Optimize the new flag images to 30px height
flags_dir = 'static/flags'
target_height = 30

for flag_file in ['gb.png', 'de.png', 'fr.png']:
    flag_path = os.path.join(flags_dir, flag_file)
    if os.path.exists(flag_path):
        img = Image.open(flag_path)
        
        # Calculate width to maintain aspect ratio
        aspect_ratio = img.width / img.height
        target_width = int(target_height * aspect_ratio)
        
        # Resize with high-quality resampling
        img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Save optimized version
        img_resized.save(flag_path, optimize=True, quality=95)
        print(f"Optimized {flag_file}: {img.width}x{img.height} -> {target_width}x{target_height}")

print("\nAll flags optimized!")
