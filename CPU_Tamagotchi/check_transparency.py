from PIL import Image

def analyze_transparency(gif_path):
    img = Image.open(gif_path)
    img = img.convert('RGBA')
    data = list(img.getdata())
    
    transparent_count = sum(1 for item in data if item[3] < 255)
    
    with open('transparency_output_utf8.txt', 'w', encoding='utf-8') as f:
        f.write(f"Total pixels in frame 1: {len(data)}\n")
        f.write(f"Transparent pixels: {transparent_count}\n")
        
        if transparent_count == 0:
            import collections
            colors = collections.Counter(data)
            f.write("Most common colors after saving:\n")
            for color, count in colors.most_common(5):
                f.write(f"{color}: {count}\n")

if __name__ == "__main__":
    analyze_transparency(r'C:\Users\naira\OneDrive\Desktop\tamagotchi\CPU_Tamagotchi\assets\sleepy.gif')
