import sys
import os
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

def generate_dynamic_stamp(base_stamp_path, output_stamp_path):
    """Pastes today's date using 'Agency FB Bold' into the blank stamp template."""
    img = Image.open(base_stamp_path).convert("RGBA")
    w, h = img.size
    
    # Format today's date (e.g., "23 JUL 2026")
    today_str = datetime.now().strftime("%d %b %Y").upper()
    
    # Create transparent layer for rotated text
    txt_layer = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_layer)
    
    font_size = int(w * 0.125)
    bold_font_names = [
        "agencyb.ttf", "AGENCYB.TTF", 
        "agencyr.ttf", "AGENCYR.TTF", "agency fb.ttf"
    ]
    
    font = None
    used_font_path = ""
    for f_name in bold_font_names:
        try:
            font = ImageFont.truetype(f_name, font_size)
            used_font_path = f_name
            break
        except IOError:
            continue
            
    if font is None:
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\agencyb.ttf", font_size)
            used_font_path = "agencyb.ttf"
        except IOError:
            try:
                font = ImageFont.truetype("C:\\Windows\\Fonts\\agencyr.ttf", font_size)
                used_font_path = "agencyr.ttf"
            except IOError:
                font = ImageFont.load_default()

    red_color = (235, 15, 15, 255)
    
    bbox = txt_draw.textbbox((0, 0), today_str, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    text_x = (w - text_w) / 2
    text_y = (h - text_h) / 2 - (h * 0.05)
    
    if "agencyb" not in used_font_path.lower():
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                txt_draw.text((text_x + dx, text_y + dy), today_str, fill=red_color, font=font)
    else:
        txt_draw.text((text_x, text_y), today_str, fill=red_color, font=font)
    
    # Rotate text ~6 degrees counter-clockwise
    rotated_txt = txt_layer.rotate(6, resample=Image.BICUBIC, center=(w/2, h/2))
    
    final_stamp = Image.alpha_composite(img, rotated_txt)
    final_stamp.save(output_stamp_path)
    return output_stamp_path


def apply_stamp_to_pdf(pdf_path, stamp_image_path):
    """Applies stamp directly to the target PDF and overwrites the original file."""
    doc = fitz.open(pdf_path)
    
    for page in doc:
        # Placement location on the A4 paper
        x0 = 350.0
        y0 = 460.0
        stamp_size = 125.0
        
        stamp_rect = fitz.Rect(x0, y0, x0 + stamp_size, y0 + stamp_size)
        page.insert_image(stamp_rect, filename=stamp_image_path, overlay=True)
        
    # Save to a temporary file then safely replace original
    temp_pdf = f"{pdf_path}.tmp"
    doc.save(temp_pdf)
    doc.close()
    
    os.replace(temp_pdf, pdf_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Error: Missing input PDF argument.")
        print("Usage: python stamp_script.py <path_to_pdf>")
        sys.exit(1)
        
    pdf_file = sys.argv[1]
    
    if not os.path.exists(pdf_file):
        print(f"❌ Error: File '{pdf_file}' not found.")
        sys.exit(1)

    base_stamp = "Stamp.png"
    if not os.path.exists(base_stamp):
        print(f"❌ Error: Base stamp file '{base_stamp}' is missing in directory.")
        sys.exit(1)

    temp_stamp_path = "today_stamp.png"
    
    generate_dynamic_stamp(base_stamp, temp_stamp_path)
    apply_stamp_to_pdf(pdf_file, temp_stamp_path)
    
    if os.path.exists(temp_stamp_path):
        os.remove(temp_stamp_path)

    print(f"✅ Stamped and updated file: {pdf_file}")