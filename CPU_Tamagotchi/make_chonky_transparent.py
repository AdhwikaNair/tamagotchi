import os
import shutil
from PIL import Image, ImageSequence

def make_transparent_rgba(gif_path, original_path):
    if os.path.exists(original_path):
        shutil.copy(original_path, gif_path)
    
    img = Image.open(gif_path)
    
    # Try to find the exact background color from top-left:
    sample_img = img.convert('RGBA')
    bg_color = sample_img.getpixel((0, 0))
    print(f"Background color determined as: {bg_color}")
    
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
        print("Successfully applied RGBA global transparency!")

if __name__ == "__main__":
    assets_path = r'C:\Users\naira\OneDrive\Desktop\tamagotchi\CPU_Tamagotchi\assets\chonky.gif'
    dl_path = r'C:\Users\naira\Downloads\eatinggif.gif'
    make_transparent_rgba(assets_path, dl_path)
