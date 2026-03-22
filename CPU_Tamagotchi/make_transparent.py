import os
from PIL import Image, ImageSequence

def process_gif(gif_path):
    img = Image.open(gif_path)
    frames = []
    
    # Iterate through frames
    for frame in ImageSequence.Iterator(img):
        # DO NOT RESIZE. Keep the original quality and size.
        f = frame.convert('RGBA')
        
        data = f.getdata()
        
        # 1. Target Blue Background transparency
        new_data = []
        for item in data:
            r, g, b, a = item
            # Target "Blue-ish" pixels
            if b > 100 and b > r + 20 and b > g + 20: 
                new_data.append((255, 255, 255, 0)) # Make Transparent
            else:
                new_data.append(item)
        
        f.putdata(new_data)
        frames.append(f)
    
    # Save back as transparent GIF
    if frames:
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=img.info.get('duration', 100),
            loop=0,
            disposal=2
        )
        print(f"Successfully cleaned {gif_path} (No Resizing)!")

if __name__ == "__main__":
    path = r'C:\Users\naira\OneDrive\Desktop\tamagotchi\CPU_Tamagotchi\assets\chillin.gif'
    if os.path.exists(path):
        process_gif(path)
    else:
        print(f"Error: {path} not found.")
