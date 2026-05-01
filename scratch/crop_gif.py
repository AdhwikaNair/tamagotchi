from PIL import Image, ImageSequence
import os

input_path = r"c:\Users\naira\OneDrive\Desktop\tamagotchi\CPU_Tamagotchi\assets\catsleeping_original.gif"
output_path = r"c:\Users\naira\OneDrive\Desktop\tamagotchi\CPU_Tamagotchi\assets\catsleeping.gif"

# 1.3 cm at 96 DPI
pixels_to_crop = int(round((1.3 / 2.54) * 96))
print(f"Cropping {pixels_to_crop} pixels from top and bottom.")

with Image.open(input_path) as img:
    frames = []
    durations = []
    
    for frame in ImageSequence.Iterator(img):
        # The crop method takes (left, top, right, bottom)
        # Original size is (720, 1280)
        width, height = frame.size
        new_frame = frame.crop((0, pixels_to_crop, width, height - pixels_to_crop))
        
        # We need to convert to 'RGBA' or keep the palette if we want transparency
        # but GIFs are tricky. Usually, convert to RGBA then back to P or just keep the frame.
        # However, frame.crop() might lose some GIF metadata if not careful.
        
        # To preserve transparency and palette, we should be careful.
        # Let's try converting to RGBA for processing if needed, but GIF frames are P.
        
        # If we just crop, Pillow usually handles the palette correctly.
        frames.append(new_frame.copy())
        durations.append(frame.info.get('duration', 100))

    # Save the frames back as a GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=img.info.get('loop', 0),
        disposal=2 # Often better for transparent GIFs
    )

print(f"Successfully saved cropped GIF to {output_path}")
