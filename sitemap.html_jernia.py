import requests
from bs4 import BeautifulSoup
import re

def fetch_sitemap_links(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}, status code: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]
    
    # Filter links that end with /c/number
    pattern = re.compile(r"/c/\d+$")
    filtered_links = [link for link in links if pattern.search(link)]
    
    return filtered_links

def save_links_to_file(links, filename="sitemap_links.txt"):
    with open(filename, "w", encoding="utf-8") as file:
        for link in links:
            file.write(link + "\n")
    print(f"Saved {len(links)} links to {filename}")

if __name__ == "__main__":
    sitemap_url = "https://www.jernia.no/sitemap.html"
    links = fetch_sitemap_links(sitemap_url)
    if links:
        save_links_to_file(links)

