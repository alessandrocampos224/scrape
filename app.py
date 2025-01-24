import csv
import os
from flask import Flask, render_template, request, send_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from fpdf import FPDF

app = Flask(__name__)

# Função para realizar o scraping
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

# Função para gerar PDF
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
        
        # Adiciona a imagem
        if row["Imagem"] != "Erro ao processar":
            try:
                img_path = "temp_image.jpg"
                os.system(f"wget -O {img_path} {row['Imagem']}")
                pdf.image(img_path, x=10, y=None, w=100)
                os.remove(img_path)
            except:
                pdf.cell(200, 10, txt="Imagem não encontrada", ln=True, align="L")

        pdf.cell(0, 10, ln=True)  # Espaçamento

    pdf_file = "produtos_hinode.pdf"
    pdf.output(pdf_file)
    return pdf_file

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

# Rota para gerar CSV, TXT ou PDF
@app.route('/generate', methods=['POST'])
def generate_files():
    urls = request.form.get('urls').splitlines()
    data = scrape_urls(urls)

    # Cria CSV
    csv_file = "produtos_hinode_formatado.csv"
    with open(csv_file, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Título", "Preço", "Descrição", "URL", "Imagem"])
        for row in data:
            writer.writerow([row["Título"], row["Preço"], row["Descrição"], row["URL"], row["Imagem"]])

    # Cria TXT
    txt_file = "produtos_hinode_formatado.txt"
    with open(txt_file, mode='w', encoding='utf-8') as file:
        for row in data:
            file.write(f"Título: {row['Título']}\n")
            file.write(f"Preço: {row['Preço']}\n")
            file.write(f"Descrição: {row['Descrição']}\n")
            file.write(f"URL: {row['URL']}\n")
            file.write(f"Imagem: {row['Imagem']}\n")
            file.write("-" * 50 + "\n")

    # Cria PDF
    pdf_file = generate_pdf(data)

    # Envia o arquivo selecionado
    file_type = request.form.get('file_type')
    if file_type == "csv":
        return send_file(csv_file, as_attachment=True)
    elif file_type == "txt":
        return send_file(txt_file, as_attachment=True)
    elif file_type == "pdf":
        return send_file(pdf_file, as_attachment=True)
    else:
        return "Formato inválido selecionado", 400

if __name__ == '__main__':
    app.run(debug=True)
