# Usar uma imagem Python como base
FROM python:3.12-slim

# Instalar dependências necessárias
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Adicionar o repositório do Google Chrome e instalar o Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable

# Instalar dependências Python
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do aplicativo
COPY . /app

# Expôr a porta do Flask
EXPOSE 8080

# Comando para iniciar o aplicativo
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
