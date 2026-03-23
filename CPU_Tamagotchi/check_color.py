import collections
from PIL import Image

def get_most_common_colors(image_path):
    img = Image.open(image_path)
    img = img.convert('RGBA')
    colors = collections.Counter(img.getdata())
    with open('color_output_utf8.txt', 'w', encoding='utf-8') as f:
        f.write("Most common colors (R, G, B, A):\n")
        for color, count in colors.most_common(5):
            f.write(f"{color}: {count}\n")

if __name__ == "__main__":
    get_most_common_colors(r'C:\Users\naira\OneDrive\Desktop\tamagotchi\CPU_Tamagotchi\assets\sleepy.gif')
