from PIL import Image
import sys

def examine(gif_path):
    img = Image.open(gif_path)
    rgba = img.convert('RGBA')
    r,g,b,a = rgba.getpixel((0,0))
    print(f"RGB_BG={r},{g},{b}")

if __name__ == "__main__":
    examine(r'C:\Users\naira\Downloads\crankygif.gif')
