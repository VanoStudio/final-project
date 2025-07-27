import requests
from bs4 import BeautifulSoup

url = requests.get('https://www.pagani.com/')
response = BeautifulSoup (url.text,"html.parser")
hasil_Scrapping = response.find("h1", class_="block__title-h1")
print(hasil_Scrapping)



