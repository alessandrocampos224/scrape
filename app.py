import csv
import os
import tempfile
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
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# Configuração de logging
logging.basicConfig(level=logging.ERROR, filename="scraping_errors.log", filemode="a")

app = Flask(__name__)

# Validação de URLs
def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

# Função para realizar o scraping de uma única URL
def process_url(url):
    chromedriver_autoinstaller.install()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    service = Service(chromedriver_autoinstaller.install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Captura os dados do produto
        title = driver.find_element(By.CLASS_NAME, "vtex-store-components-3-x-productNameContainer").text.strip()
        price = driver.find_element(By.CLASS_NAME, "vtex-product-price-1-x-sellingPrice").text.strip()
        description = driver.find_element(By.CLASS_NAME, "spec_text").text.strip()
        image = driver.find_element(By.CLASS_NAME, "vtex-store-components-3-x-productImageTag").get_attribute("src").strip()

        return {
            "Título": title,
            "Preço": price,
            "Descrição": description,
            "Imagem": image,
            "URL": url
        }
    except Exception as e:
        logging.error(f"Erro ao processar URL {url}: {e}")
        return {
            "Título": "Erro ao processar",
            "Preço": "Erro ao processar",
            "Descrição": str(e),
            "Imagem": "Erro ao processar",
            "URL": url
        }
    finally:
        driver.quit()

# Função para realizar o scraping de múltiplas URLs
def scrape_urls(urls):
    with ThreadPoolExecutor(max_workers=5) as executor:
        return list(executor.map(process_url, urls))

# Função para gerar PDF
def generate_pdf(data, temp_dir):
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

        # Adiciona a imagem
        if row["Imagem"] != "Erro ao processar":
            try:
                img_path = os.path.join(temp_dir, "temp_image.jpg")
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(row["Imagem"], headers=headers, stream=True)

                if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
                    with open(img_path, "wb") as img_file:
                        img_file.write(response.content)
                    pdf.image(img_path, x=10, y=None, w=100)
                else:
                    pdf.cell(200, 10, txt="Imagem inválida ou não foi possível baixá-la.", ln=True, align="L")
            except Exception as e:
                pdf.cell(200, 10, txt=f"Erro ao processar imagem: {str(e)}", ln=True, align="L")

        pdf.cell(0, 10, ln=True)  # Espaçamento

    pdf_file = os.path.join(temp_dir, "produtos_hinode.pdf")
    pdf.output(pdf_file)
    return pdf_file

# Função para gerar XML
def generate_xml(data, temp_dir):
    root = ET.Element("Produtos")
    for row in data:
        product = ET.SubElement(root, "Produto")
        for key, value in row.items():
            element = ET.SubElement(product, key)
            element.text = value

    xml_file = os.path.join(temp_dir, "produtos_hinode.xml")
    tree = ET.ElementTree(root)
    tree.write(xml_file, encoding="utf-8", xml_declaration=True)
    return xml_file

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

# Rota para gerar arquivos
@app.route('/generate', methods=['POST'])
def generate_files():
    urls = request.form.get('urls').splitlines()
    urls = [url for url in urls if is_valid_url(url)]

    if not urls:
        return "Nenhuma URL válida fornecida.", 400

    data = scrape_urls(urls)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Cria CSV
        csv_file = os.path.join(temp_dir, "produtos_hinode_formatado.csv")
        with open(csv_file, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Título", "Preço", "Descrição", "URL", "Imagem"])
            for row in data:
                writer.writerow([row["Título"], row["Preço"], row["Descrição"], row["URL"], row["Imagem"]])

        # Cria TXT
        txt_file = os.path.join(temp_dir, "produtos_hinode_formatado.txt")
        with open(txt_file, mode='w', encoding='utf-8') as file:
            for row in data:
                file.write(f"Título: {row['Título']}\n")
                file.write(f"Preço: {row['Preço']}\n")
                file.write(f"Descrição: {row['Descrição']}\n")
                file.write(f"URL: {row['URL']}\n")
                file.write(f"Imagem: {row['Imagem']}\n")
                file.write("-" * 50 + "\n")

        # Cria PDF
        pdf_file = generate_pdf(data, temp_dir)

        # Cria XML
        xml_file = generate_xml(data, temp_dir)

        # Envia o arquivo selecionado
        file_type = request.form.get('file_type')
        if file_type == "csv":
            return send_file(csv_file, as_attachment=True)
        elif file_type == "txt":
            return send_file(txt_file, as_attachment=True)
        elif file_type == "pdf":
            return send_file(pdf_file, as_attachment=True)
        elif file_type == "xml":
            return send_file(xml_file, as_attachment=True)
        else:
            return "Formato inválido selecionado.", 400

if __name__ == '__main__':
    app.run(debug=False)
