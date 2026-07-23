import os
import io
from flask import Flask, render_template, request, send_file, send_from_directory
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

app = Flask(__name__)

# Serve Stamp.png to HTML template
@app.route('/static/Stamp.png')
def serve_logo():
    return send_from_directory('.', 'Stamp.png')

def generate_dynamic_stamp(base_stamp_path):
    img = Image.open(base_stamp_path).convert("RGBA")
    w, h = img.size
    
    today_str = datetime.now().strftime("%d %b %Y").upper()
    txt_layer = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_layer)
    
    font_size = int(w * 0.125)
    bold_font_names = ["agencyb.ttf", "AGENCYB.TTF", "agencyr.ttf", "AGENCYR.TTF", "agency fb.ttf"]
    
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
    
    rotated_txt = txt_layer.rotate(6, resample=Image.BICUBIC, center=(w/2, h/2))
    final_stamp = Image.alpha_composite(img, rotated_txt)
    
    # Save to memory buffer
    img_byte_arr = io.BytesIO()
    final_stamp.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stamp', methods=['POST'])
def stamp_pdf():
    if 'pdf_file' not in request.files:
        return "No file uploaded", 400
        
    file = request.files['pdf_file']
    if file.filename == '':
        return "No selected file", 400

    # Load PDF from request memory
    pdf_stream = file.read()
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    
    # Generate stamp dynamically in memory
    stamp_bytes = generate_dynamic_stamp("Stamp.png")
    
    # Stamp coordinates (matching INV001297)
    x0, y0, stamp_size = 350.0, 610.0, 160.0
    stamp_rect = fitz.Rect(x0, y0, x0 + stamp_size, y0 + stamp_size)
    
    for page in doc:
        page.insert_image(stamp_rect, stream=stamp_bytes.getvalue(), overlay=True)
        
    # Save stamped PDF to memory buffer
    output_pdf_stream = io.BytesIO()
    doc.save(output_pdf_stream)
    doc.close()
    output_pdf_stream.seek(0)
    
    return send_file(
        output_pdf_stream,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"signed_{file.filename}"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)