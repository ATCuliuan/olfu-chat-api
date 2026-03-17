import os
import requests
from bs4 import BeautifulSoup

urls = [
    "https://fatima.edu.ph/our-lady-of-fatima-university-quezon-city/",
    "https://fatima.edu.ph/senior-high-school/",
    "https://fatima.edu.ph/apply-senior-high-school/",
    "https://fatima.edu.ph/contact-us/",
    "https://fatima.edu.ph/history/",
    "https://fatima.edu.ph/mission-vision-core-values/",
    "https://fatima.edu.ph/university-seal/",
    "https://fatima.edu.ph/hymn/"
]

folder_name = "olfu_data"
os.makedirs(folder_name, exist_ok=True)

print("Starting OLFU Data Scraper...")

for url in urls:
    try:
        print(f"Scraping: {url}")
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content = []
            for text_block in soup.find_all(['h1', 'h2', 'h3', 'p', 'li']):
                clean_text = text_block.get_text(strip=True)
                if clean_text:
                    content.append(clean_text)
            
            filename = url.strip("/").split("/")[-1] + ".txt"
            filepath = os.path.join(folder_name, filename)
            
            with open(filepath, "w", encoding="utf-8") as file:
                file.write("\n".join(content))
                
            print(f"Saved: {filepath}")
        else:
            print(f"Failed to access {url}. HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error scraping {url}: {e}")

print("Scraping complete. Data saved to 'olfu_data' directory.")