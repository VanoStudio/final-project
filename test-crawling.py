from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

url = "https://www.rottentomatoes.com/m/superman_2025/reviews"
driver.get(url)

# Ambil semua elemen dengan data-qa="review-text"
title = driver.find_element(By.CSS_SELECTOR, 'a[data-qa="sidebar-media-link"]')
# reviews = driver.find_elements(By.CSS_SELECTOR, 'rt-text[data-qa="review-text"]')
print(title.text)

# Loop untuk ambil text dari masing-masing elemen
# for r in reviews:
#     print(r.text)

driver.quit()
