import csv
import os
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, send_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from fpdf import FPDF
import requests
import xlwt
from PIL import Image
import io

app = Flask(__name__)

def scrape_urls(urls):
    chromedriver_autoinstaller.install()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)

    product_data = []
    for url in urls:
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            title = driver.find_element(By.CLASS_NAME, "vtex-store-components-3-x-productNameContainer").text.strip()
            price = driver.find_element(By.CLASS_NAME, "vtex-product-price-1-x-sellingPrice").text.strip()
            description = driver.find_element(By.CLASS_NAME, "spec_text").text.strip()
            image = driver.find_element(By.CLASS_NAME, "vtex-store-components-3-x-productImageTag").get_attribute("src").strip()

            product_data.append({
                "Título": title,
                "Preço": price,
                "Descrição": description,
                "Imagem": image,
                "URL": url
            })
        except Exception as e:
            product_data.append({
                "Título": "Erro ao processar",
                "Preço": "Erro ao processar",
                "Descrição": str(e),
                "Imagem": "Erro ao processar",
                "URL": url
            })

    driver.quit()
    return product_data

def generate_pdf(data):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for row in data:
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(200, 10, txt=row["Título"], ln=True, align="L")
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Preço: {row['Preço']}", ln=True, align="L")
        pdf.multi_cell(0, 10, txt=f"Descrição: {row['Descrição']}")
        pdf.cell(200, 10, txt=f"URL: {row['URL']}", ln=True, align="L")

        if row["Imagem"] != "Erro ao processar":
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "image/jpeg,image/png,image/*"
                }
                response = requests.get(row["Imagem"], headers=headers, timeout=10)

                if response.status_code == 200 and response.content:
                    try:
                        img = Image.open(io.BytesIO(response.content))
                        img = img.convert('RGB')
                        img_path = f"temp_image_{hash(row['URL'])}.jpg"
                        img.save(img_path, 'JPEG')
                        
                        pdf.image(img_path, x=10, y=None, w=100)
                        
                        if os.path.exists(img_path):
                            os.remove(img_path)
                    except Exception as e:
                        pdf.cell(200, 10, txt=f"Erro ao processar imagem: {str(e)}", ln=True, align="L")
                else:
                    pdf.cell(200, 10, txt="Falha ao baixar imagem", ln=True, align="L")
            except Exception as e:
                pdf.cell(200, 10, txt=f"Erro ao processar imagem: {str(e)}", ln=True, align="L")
        
        pdf.cell(0, 10, ln=True)

    pdf_file = "produtos_hinode.pdf"
    pdf.output(pdf_file)
    return pdf_file

def generate_xml(data):
    root = ET.Element("Produtos")
    for row in data:
        product = ET.SubElement(root, "Produto")
        for key, value in row.items():
            element = ET.SubElement(product, key)
            element.text = str(value)

    tree = ET.ElementTree(root)
    xml_file = "produtos_hinode.xml"
    tree.write(xml_file, encoding="utf-8", xml_declaration=True)
    return xml_file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_files():
    urls = request.form.get('urls').splitlines()
    data = scrape_urls(urls)

    # Gera CSV
    csv_file = "produtos_hinode_formatado.csv"
    with open(csv_file, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Título", "Preço", "Descrição", "URL", "Imagem"])
        for row in data:
            writer.writerow([row["Título"], row["Preço"], row["Descrição"], row["URL"], row["Imagem"]])

    # Gera TXT
    txt_file = "produtos_hinode_formatado.txt"
    with open(txt_file, mode='w', encoding='utf-8') as file:
        for row in data:
            file.write(f"Título: {row['Título']}\n")
            file.write(f"Preço: {row['Preço']}\n")
            file.write(f"Descrição: {row['Descrição']}\n")
            file.write(f"URL: {row['URL']}\n")
            file.write(f"Imagem: {row['Imagem']}\n")
            file.write("-" * 50 + "\n")

    # Gera PDF
    pdf_file = generate_pdf(data)

    # Gera TSV
    tsv_file = "produtos_hinode_formatado.tsv"
    with open(tsv_file, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["Título", "Preço", "Descrição", "URL", "Imagem"])
        for row in data:
            writer.writerow([row["Título"], row["Preço"], row["Descrição"], row["URL"], row["Imagem"]])

    # Gera Excel
    temp_csv = "temp_produtos.csv"
    with open(temp_csv, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Título", "Preço", "Descrição", "URL", "Imagem"])
        for row in data:
            writer.writerow([
                str(row["Título"])[:32000],
                str(row["Preço"])[:32000],
                str(row["Descrição"])[:32000],
                str(row["URL"])[:32000],
                str(row["Imagem"])[:32000]
            ])

    # Converte CSV para Excel
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Produtos')

    with open(temp_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, val in enumerate(row):
                ws.write(r, c, val)

    xlsx_file = "produtos_hinode_formatado.xls"
    wb.save(xlsx_file)

    # Remove o arquivo temporário CSV
    if os.path.exists(temp_csv):
        os.remove(temp_csv)

    # Gera XML
    xml_file = generate_xml(data)

    # Retorna o arquivo solicitado
    file_type = request.form.get('file_type')
    if file_type == "csv":
        return send_file(csv_file, as_attachment=True)
    elif file_type == "txt":
        return send_file(txt_file, as_attachment=True)
    elif file_type == "pdf":
        return send_file(pdf_file, as_attachment=True)
    elif file_type == "tsv":
        return send_file(tsv_file, as_attachment=True)
    elif file_type == "xlsx" or file_type == "xls":
        return send_file(xlsx_file, as_attachment=True)
    elif file_type == "xml":
        return send_file(xml_file, as_attachment=True)
    else:
        return "Formato inválido selecionado", 400

if __name__ == '__main__':
    app.run(debug=True)
