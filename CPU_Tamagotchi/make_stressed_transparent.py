import os
import shutil
from PIL import Image, ImageSequence

def make_transparent_rgba(gif_path, original_path, png_path):
    if os.path.exists(original_path):
        shutil.copy(original_path, gif_path)
    
    img = Image.open(gif_path)
    
    # Target Background Color: (100, 177, 219)
    bg_color = (100, 177, 219)
    print(f"Targeting background color: {bg_color}")
    
    frames = []
    for frame in ImageSequence.Iterator(img):
        f = frame.convert('RGBA')
        data = f.getdata()
        
        new_data = []
        for item in data:
            r, g, b, a = item
            # Target Background Color with a reasonable tolerance for compression noise
            if abs(r - bg_color[0]) <= 8 and abs(g - bg_color[1]) <= 8 and abs(b - bg_color[2]) <= 8:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
                
        f.putdata(new_data)
        frames.append(f)
        
    if frames:
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=img.info.get('duration', 100),
            loop=0,
            disposal=2,
            transparency=0
        )
        print("Successfully applied RGBA global transparency to GIF!")
        
        # Overwrite the PNG explicitly without deleting the file
        frames[0].save(png_path)
        print("Successfully overwrote stressed.png with the transparent first frame!")

if __name__ == "__main__":
    assets_path = r'C:\Users\naira\OneDrive\Desktop\tamagotchi\CPU_Tamagotchi\assets\stressed.gif'
    dl_path = r'C:\Users\naira\Downloads\crankygif.gif'
    png_path = r'C:\Users\naira\OneDrive\Desktop\tamagotchi\CPU_Tamagotchi\assets\stressed.png'
    make_transparent_rgba(assets_path, dl_path, png_path)
