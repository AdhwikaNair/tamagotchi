from PIL import Image

def examine(gif_path):
    img = Image.open(gif_path)
    rgba = img.convert('RGBA')
    top_left = rgba.getpixel((0,0))
    print(f"Top left RGBA: {top_left}")
    
    # Are there transparent pixels?
    data = list(rgba.getdata())
    trans = sum(1 for p in data if p[3] < 255)
    print(f"Transparent pixels in frame 1: {trans} / {len(data)}")

if __name__ == "__main__":
    examine(r'C:\Users\naira\Downloads\eatinggif.gif')
