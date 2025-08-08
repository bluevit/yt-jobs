FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libappindicator3-1 \
    libgbm1 \
    libvulkan1 \
    xdg-utils \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Google Chrome (v116)
RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_116.0.5845.96-1_amd64.deb && \
    apt-get install -y ./google-chrome-stable_116.0.5845.96-1_amd64.deb && \
    rm google-chrome-stable_116.0.5845.96-1_amd64.deb

# Install ChromeDriver v116
RUN wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/116.0.5845.96/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# Environment variables
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Start the scraper
CMD ["python", "main.py"]
