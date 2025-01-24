from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

def scrape_urls(urls):
    # Instala o chromedriver automaticamente
    chromedriver_autoinstaller.install()

    # Configuração do Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Modo headless
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    # Serviço do Chrome
    service = Service()  # O Selenium encontrará o chromedriver automaticamente
    driver = webdriver.Chrome(service=service, options=options)

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
