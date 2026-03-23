import os
import shutil
from PIL import Image

def fix_gif_via_palette(gif_path, original_path):
    if os.path.exists(original_path):
        shutil.copy(original_path, gif_path)
    
    img = Image.open(gif_path)
    
    # Check the top-left corner index of the first frame
    bg_index = img.getpixel((0, 0))
    print(f"Background index determined as: {bg_index}")
    
    frames = []
    import PIL.ImageSequence as ImageSequence
    for frame in ImageSequence.Iterator(img):
        # frame is in P mode
        # Copy the frame so we can modify its info
        new_frame = frame.copy()
        
        # We can explicitly set transparency to this index
        new_frame.info['transparency'] = bg_index
        frames.append(new_frame)
    
    if frames:
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            loop=0,
            disposal=2,
            transparency=bg_index
        )
        print(f"Successfully cleaned via palette index {bg_index}!")

if __name__ == "__main__":
    assets_path = r'C:\Users\naira\OneDrive\Desktop\tamagotchi\CPU_Tamagotchi\assets\sleepy.gif'
    dl_path = r'C:\Users\naira\Downloads\sleepinggif.gif'
    fix_gif_via_palette(assets_path, dl_path)
