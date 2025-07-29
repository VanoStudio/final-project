from selenium import webdriver
from bs4 import BeautifulSoup

# Inisialisasi browser (pastikan chromedriver sudah ada)
driver = webdriver.Chrome()
driver.get("https://www.detik.com/")

# Ambil HTML hasil render JS
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

# Ambil headline
headline = soup.select("div.media_text a.media_link")
for h in headline:
    print(h.get_text(strip=True), "-", h["href"])

driver.quit()
