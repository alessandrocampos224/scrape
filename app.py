from flask import Flask, render_template, request, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import io

app = Flask(__name__)

def scrape_urls(urls):
    # Configuração do Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    product_data = []
    for url in urls:
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            title = driver.find_element(By.CLASS_NAME, "vtex-store-components-3-x-productNameContainer").text.strip()
            price = driver.find_element(By.CLASS_NAME, "vtex-product-price-1-x-sellingPrice").text.strip()
            description = driver.find_element(By.CLASS_NAME, "spec_text").text.strip()

            product_data.append({
                "Título": title,
                "Preço": price,
                "Descrição": description,
                "URL": url
            })
        except Exception as e:
            product_data.append({
                "Título": "Erro ao processar",
                "Preço": "Erro ao processar",
                "Descrição": str(e),
                "URL": url
            })

    driver.quit()
    return product_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_csv():
    urls = request.form.get("urls").splitlines()  # Recebe as URLs do formulário
    if not urls:
        return "Por favor, insira ao menos uma URL", 400

    # Faz o scraping
    data = scrape_urls(urls)

    # Gera o CSV na memória
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)

    # Retorna o CSV para download
    return send_file(output, as_attachment=True, download_name="produtos.csv", mimetype='text/csv')

if __name__ == '__main__':
    app.run(debug=True)
