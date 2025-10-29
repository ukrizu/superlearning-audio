from PIL import Image

# Optimize the new Spanish flag
flag_path = 'static/flags/es.png'
target_height = 30

img = Image.open(flag_path)

# Calculate width to maintain aspect ratio
aspect_ratio = img.width / img.height
target_width = int(target_height * aspect_ratio)

# Resize with high-quality resampling
img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

# Save optimized version
img_resized.save(flag_path, optimize=True, quality=95)
print(f"Optimized es.png: {img.width}x{img.height} -> {target_width}x{target_height}")
