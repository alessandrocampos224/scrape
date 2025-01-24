from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# Configuração do Selenium
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Executa em modo headless
    return webdriver.Chrome(options=options)
@app.route('/', methods=['GET'])
def home():
    return "<h1>API de Scraping</h1><p>Use a rota <code>/scrape</code> com um POST para enviar URLs.</p>"

# Rota para o scraper
@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if request.method == 'GET':
        return "<h1>Use o método POST para enviar URLs no corpo da requisição.</h1>"

    # Mantém o comportamento atual para POST
    data = request.json
    if not data or "urls" not in data:
        return jsonify({"error": "Por favor, forneça uma lista de URLs no formato {'urls': ['url1', 'url2']}"}), 400

    urls = data['urls']
    results = []
    driver = init_driver()

    for url in urls:
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Captura os dados
            title = driver.find_element(By.CLASS_NAME, "vtex-store-components-3-x-productNameContainer").text.strip()
            price = driver.find_element(By.CLASS_NAME, "vtex-product-price-1-x-sellingPrice").text.strip()
            description = driver.find_element(By.CLASS_NAME, "spec_text").text.strip()

            results.append({
                "url": url,
                "title": title,
                "price": price,
                "description": description
            })
        except Exception as e:
            results.append({"url": url, "error": str(e)})

    driver.quit()
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
