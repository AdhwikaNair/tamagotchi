from PIL import Image
import os

gif_path = r"c:\Users\naira\OneDrive\Desktop\tamagotchi\CPU_Tamagotchi\assets\catsleeping.gif"

with Image.open(gif_path) as img:
    width, height = img.size
    dpi = img.info.get('dpi', (96, 96))
    print(f"Dimensions: {width}x{height}")
    print(f"DPI: {dpi}")
