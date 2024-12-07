from flask import Flask, request, render_template, send_file
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from urllib.parse import urljoin


app = Flask(__name__,
            static_url_path='/', 
            static_folder='static',)

def generate_pdf(headings, url):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Halaman cover
    c.setFillColorRGB(0.2, 0.5, 0.8)
    c.rect(0, 0, width, height, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 2 * inch, "Headings Checker Report")
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 2.5 * inch, f"URL: {url}")
    c.showPage()
    
    # Halaman konten
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 12)
    y_position = height - 40
    c.drawString(30, y_position, "Headings Checker Results")
    y_position -= 30
    
    for heading in headings:
        indent = (int(heading.name[1]) - 1) * 20
        c.drawString(30 + indent, y_position, f"{heading.name}: {heading.get_text()}")
        y_position -= 20
        if y_position < 40:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 40
    
    c.save()
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    headings = []
    alt_attributes = []
    url = ""
    if request.method == 'POST':
        url = request.form.get('url')
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    return render_template('index.html', headings=headings, url=url, alt_attributes=alt_attributes)

@app.route('/check_alt', methods=['GET'])
def check_alt_page():
    return render_template('alttag.html', alt_attributes=[], url="")

@app.route('/check_alt', methods=['POST'])
def check_alt():
    if request.method == 'POST':
        url = request.form['url']
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            images = soup.find_all('img')
            
            alt_attributes = []
            for img in images:
                # Get src and handle None cases
                src = img.get('src', '')
                if src:
                    # Handle relative URLs
                    if not src.startswith(('http://', 'https://', 'data:')):
                        src = urljoin(url, src)
                
                alt_attributes.append({
                    'src': src,
                    'alt': img.get('alt', ''),
                    'has_alt': 'alt' in img.attrs
                })
            
            return render_template('alttag.html', alt_attributes=alt_attributes, url=url)
        except Exception as e:
            return render_template('alttag.html', error=str(e))
    
    return render_template('alttag.html')
@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    url = request.form.get('url')
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    pdf_buffer = generate_pdf(headings, url)
    
    return send_file(pdf_buffer, as_attachment=True, download_name='headings_report.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)