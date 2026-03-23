from PIL import Image

def examine_original(gif_path):
    img = Image.open(gif_path)
    lines = []
    lines.append(f"Format: {img.format}, Mode: {img.mode}")
    lines.append(f"Info: {img.info}")
    
    # Get top left pixel in original mode
    top_left_p = img.getpixel((0, 0))
    lines.append(f"Top-left pixel (original mode): {top_left_p}")
    
    # Convert to RGBA
    rgba = img.convert('RGBA')
    top_left_rgba = rgba.getpixel((0, 0))
    lines.append(f"Top-left pixel (RGBA): {top_left_rgba}")
    
    # Look at palette if it exists
    if img.mode == 'P':
        palette = img.getpalette()
        if palette:
            idx = top_left_p * 3
            lines.append(f"Palette color for top-left: ({palette[idx]}, {palette[idx+1]}, {palette[idx+2]})")

    with open('examine_output_utf8.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    examine_original(r'C:\Users\naira\Downloads\sleepinggif.gif')
