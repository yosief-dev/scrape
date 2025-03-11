import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin

def get_deep_urls(base_url="https://www.europris.no/"):
    """
    Extract deep category URLs from the Europris website.
    """
    # Headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        # Get the main page
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all <a> tags in the navigation menu
        all_links = []
        nav_container = soup.select_one('nav.navigation.topmenu')
        
        if nav_container:
            # Extract all links from all levels - specifically looking for deeper level links
            # We're focusing on level2, level3 etc. links as these are the deep categories
            deep_link_elements = nav_container.select('li.level1 li.level2 a, li.level1 li.level3 a')
            
            for link_element in deep_link_elements:
                href = link_element.get('href')
                if href and href.startswith('https://www.europris.no/'):
                    # Only add links that point to europris.no
                    all_links.append(href)
        
        # Remove duplicates and sort
        unique_links = sorted(list(set(all_links)))
        return unique_links
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

# If we want to go even deeper, we need to visit each category page
def get_all_deep_urls(base_url="https://www.europris.no/"):
    """
    Get all deep URLs by first getting category URLs then visiting each to find product category URLs
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    deep_urls = set()
    processed_urls = set()
    
    # First, get initial set of category URLs from the navigation
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        nav = soup.select_one('nav.navigation.topmenu')
        
        # Get all links from the navigation
        if nav:
            all_links = nav.select('a[href^="https://www.europris.no/"]')
            initial_urls = [link.get('href') for link in all_links if link.get('href')]
            
            # Process each URL to find deeper links
            for url in initial_urls:
                if url not in processed_urls and url.startswith('https://www.europris.no/'):
                    try:
                        processed_urls.add(url)
                        print(f"Checking: {url}")
                        
                        # Delay to be respectful to server
                        time.sleep(1)
                        
                        response = requests.get(url, headers=headers)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Look for category links in the sidebar or breadcrumbs
                        # This varies by site - we're looking for links that indicate deeper categories
                        category_links = soup.select('.categories-menu a, .sidebar-categories a, .category-list a')
                        
                        if not category_links:
                            # Look for any other navigation patterns
                            category_links = soup.select('.subcategory-grid a, .subcategories a')
                        
                        if category_links:
                            for link in category_links:
                                href = link.get('href')
                                if href and href.startswith('https://www.europris.no/'):
                                    # If we found subcategory links, this isn't a leaf category
                                    deep_urls.add(href)
                        else:
                            # If no subcategory links found, this might be a leaf category
                            deep_urls.add(url)
                            
                    except Exception as e:
                        print(f"Error processing {url}: {e}")
    
    except Exception as e:
        print(f"Error fetching main page: {e}")
    
    return sorted(list(deep_urls))

# Execute to get deep URLs from the navigation
print("Getting deep URLs from navigation structure...")
deep_urls = get_deep_urls()

print(f"\nFound {len(deep_urls)} deep category URLs:")
for i, url in enumerate(deep_urls, 1):
    print(f"{i}. {url}")

# Save to file
with open('100_europris_deep_urls.txt', 'w', encoding='utf-8') as f:
    for url in deep_urls:
        f.write(f"{url}\n")

print(f"\nSaved {len(deep_urls)} URLs to europris_deep_urls.txt")

# If you want to go even deeper, uncomment these lines - but be careful with load on their server
# print("\nCrawling deeper into each category page (this will take longer)...")
# all_deep_urls = get_all_deep_urls()
# with open('europris_all_deep_urls.txt', 'w', encoding='utf-8') as f:
#     for url in all_deep_urls:
#         f.write(f"{url}\n")
# print(f"\nSaved {len(all_deep_urls)} URLs to europris_all_deep_urls.txt")
