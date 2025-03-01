import requests
from bs4 import BeautifulSoup
import re
import time
import random
import csv
import concurrent.futures
import logging
#from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scraper_log.log'
)

def scrape_europris_product(url):
    try:
        # Send request with randomized user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.europris.no/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            logging.warning(f"Failed to retrieve {url}. Status code: {response.status_code}")
            return {"url": url, "error": f"Status code: {response.status_code}"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        product_data = {"url": url}
        
        # Your existing scraping code
        product_info_div = soup.find('div', class_='lipscore-rating-small')
        if product_info_div:
            product_data['product_number'] = product_info_div.get('data-ls-product-id')
            product_data['product_description'] = product_info_div.get('data-ls-description')
        
        title_element = soup.find('h1', class_='page-title')
        if title_element:
            product_data['product_name'] = title_element.text.strip()
        
        price_span = soup.find('span', {'id': re.compile(r'product-price-\d+')})
        if price_span and 'data-price-amount' in price_span.attrs:
            product_data['price'] = price_span['data-price-amount']
            currency_element = soup.find('span', class_='price-currency-symbol')
            if currency_element:
                product_data['currency'] = currency_element.text.strip()
        
        image_element = soup.find('img', {'id': 'product-image'}) or soup.find('img', class_='gallery-placeholder__image')
        if image_element and 'src' in image_element.attrs:
            product_data['image_url'] = image_element['src']
        
        details_div = soup.find('div', class_='product-info-description')
        if details_div:
            product_data['details'] = details_div.text.strip()
        
        breadcrumbs = soup.find('ul', class_='items')
        if breadcrumbs:
            categories = []
            for item in breadcrumbs.find_all('li', class_='item'):
                if item.find('a'):
                    categories.append(item.text.strip())
            product_data['categories'] = categories
        
        stock_element = soup.find('div', class_='stock available') or soup.find('div', class_='stock unavailable')
        if stock_element:
            product_data['stock_status'] = stock_element.text.strip()
        
        sku_element = soup.find('div', class_='product attribute sku')
        if sku_element:
            sku_value = sku_element.find('div', class_='value')
            if sku_value:
                product_data['sku'] = sku_value.text.strip()
        
        # Extract GTIN using the provided CSS selector
        try:
            # Using CSS selector with BeautifulSoup's select_one method
            gtin_element = soup.select_one('#europris_techinfo > div > div:nth-child(2) > div.techinfo_value')
            if gtin_element:
                product_data['gtin'] = gtin_element.text.strip()
            else:
                # Alternative approach if the specific selector doesn't work
                techinfo_div = soup.find(id='europris_techinfo')
                if techinfo_div:
                    # Look for GTIN label and get its value
                    for div in techinfo_div.find_all('div', class_='techinfo_row'):
                        label = div.find('div', class_='techinfo_label')
                        value = div.find('div', class_='techinfo_value')
                        if label and value and 'GTIN' in label.text:
                            product_data['gtin'] = value.text.strip()
                            break
        except Exception as e:
            logging.warning(f"Error extracting GTIN from {url}: {str(e)}")
            product_data['gtin_error'] = str(e)
        
        return product_data
        
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return {"url": url, "error": str(e)}

def save_to_csv(data, filename='product_data.csv'):
    if not data:
        logging.warning("No data to save to CSV")
        return
    
    # Get all possible field names from all records
    fieldnames = set()
    for record in data:
        fieldnames.update(record.keys())
    
    # Convert set to list and ensure 'url' is the first field
    fieldnames = list(fieldnames)
    if 'url' in fieldnames:
        fieldnames.remove('url')
    fieldnames = ['url'] + sorted(fieldnames)
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"Data successfully saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving data to CSV: {str(e)}")

def batch_scrape(urls, max_workers=5, batch_size=100, delay_range=(1, 3)):
    """Scrape URLs in batches using a thread pool."""
    all_results = []
    
    # Process URLs in batches
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i+batch_size]
        batch_results = []
        
        # Process each batch with thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks and create a mapping of futures to URLs
            future_to_url = {executor.submit(scrape_europris_product, url): url for url in batch}
            
            # Process completed futures with a progress bar
            for future in tqdm(concurrent.futures.as_completed(future_to_url), total=len(batch), desc=f"Batch {i//batch_size + 1}/{len(urls)//batch_size + 1}"):
                url = future_to_url[future]
                try:
                    data = future.result()
                    batch_results.append(data)
                except Exception as e:
                    logging.error(f"Exception for {url}: {str(e)}")
                    batch_results.append({"url": url, "error": str(e)})
        
        # Save batch results to temporary file
        batch_filename = f"product_data_batch_{i//batch_size + 1}.csv"
        save_to_csv(batch_results, batch_filename)
        
        # Add to overall results
        all_results.extend(batch_results)
        
        # Delay between batches
        if i + batch_size < len(urls):
            delay = random.uniform(*delay_range)
            logging.info(f"Waiting {delay:.2f} seconds before next batch...")
            time.sleep(delay)
    
    return all_results

# Main execution
"""
if __name__ == "__main__":
    # Load URLs from file (one URL per line)
    try:
        with open('urls.txt', 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        # Log the number of URLs loaded
        logging.info(f"Loaded {len(urls)} URLs for scraping")
        
        # Start scraping
        results = batch_scrape(
            urls, 
            max_workers=5,       # Adjust based on your system capabilities
            batch_size=100,      # Adjust based on website tolerance
            delay_range=(2, 5)   # Delay between batches in seconds
        )
        
        # Save all results to final CSV
        save_to_csv(results, 'product_data_final.csv')
        
        logging.info("Scraping completed successfully")
        
    except Exception as e:
        logging.critical(f"Critical error in main execution: {str(e)}")
        
    """
if __name__ == "__main__":
    print(scrape_europris_product('https://www.europris.no/p-choco-liquorice-110-g-mild-212616') )   
    

