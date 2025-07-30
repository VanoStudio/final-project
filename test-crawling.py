from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
import time

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

film = "Conjuring"  # nanti bisa ganti dari input user
search_url = f"https://www.rottentomatoes.com/search?search={urllib.parse.quote(film)}"
driver.get(search_url)

time.sleep(2)  # beri waktu page load, bisa diganti WebDriverWait

# Ambil link hasil pertama
first_result = driver.find_element(By.CSS_SELECTOR, 'search-page-media-row a')
film_url = first_result.get_attribute("href")
print("Link film:", film_url)

# Tambahkan /reviews
review_url = film_url.rstrip("/") + "/reviews"
print("Link review:", review_url)

# Pergi ke halaman review
driver.get(review_url)

# Contoh: ambil semua review snippet
reviews = driver.find_elements(By.CSS_SELECTOR, '.review-text')
for r in reviews:
    print("-", r.text)

driver.quit()
