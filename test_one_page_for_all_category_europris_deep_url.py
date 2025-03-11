from datetime import datetime
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests
import pandas as pd
import math
import time

headers = {
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
url = 'https://www.europris.no/'

current_date = datetime.now()
today_is = current_date.strftime("%Y/%m/%d")
date_now = current_date.strftime("%Y/%m/%dT%Hhh%Mmm%Sss")

def catagory_product_list():
  url_links = []

  response = requests.get(url, headers=headers)

  soup = BeautifulSoup(response.text, 'html.parser')

  # Find the <nav> element with class "navigation topmenu"
  nav_element = soup.find('nav', class_='navigation topmenu')

  # If <nav> element is found, extract links from <a> tags within it
  if nav_element:
    # Find all <a> tags within the <nav> element
    all_links = nav_element.find_all('a', class_='level-top')

    # Extract href attribute from each <a> tag
    links_href = [link.get('href') for link in all_links]

    # Print the extracted links
    for href in links_href:
      #print(href)
      url_links.append(href)
  else:
    print("Nav element not found.")

  return url_links


def extract_price(html):
  soup = BeautifulSoup(html, 'html.parser')
  price_container = soup.find('span', class_='price-wrapper')
  if price_container:
    price = price_container['data-price-amount']
    return price
  return None


def product(url):
  print(url)
  response = requests.get(url, headers=headers)

  soup = BeautifulSoup(response.text, 'html.parser')

  total_product = soup.find('span', class_='toolbar-number').text

  #pages = math.ceil(int(total_product) / 32)
  pages=1
  prd = []

  for page in range(1, pages+1):
    
    # Fix the URL construction - don't add ?p= if it already exists
    if '?p=' in url:
      page_url = url
    else:
      page_url = f'{url}?p={page}'
    
    print(page_url)
    response = requests.get(page_url, headers=headers)

    soup = BeautifulSoup(response.text, 'html.parser')

    product_list = soup.find_all('li', class_="item product product-item")

    for pro in product_list:
        product_element = pro.find('strong', class_="product name product-item-name")
        product = product_element.find('a').text.strip() 
        product_info = pro.find('span', class_='subname')
        product_info_text = product_info.text.strip() if product_info else "N/A"  

        product_offer = pro.find('div', class_='lbl_deal_value')
        discount_offer=product_offer.find('span').text.strip() if product_offer else "N/A"  

        offer_from=pro.find('input', attrs={"data-role": "valid_from"})
        offer_available_from = offer_from['value'] if offer_from else "N/A"

        offer_to=pro.find('input', attrs={"data-role": "valid_to"}) 
        offer_available_til = offer_to['value'] if offer_to else "N/A"  
        
        # Get product price               
        price_element = pro.find('span', id=lambda x: x and x.startswith('product-price-'))
        price = price_element.get('data-price-amount') if price_element else "N/A"  

        old_price_element = pro.find('span', id=lambda x: x and x.startswith('old-price-'))
        old_price = old_price_element.get('data-price-amount') if old_price_element else "N/A"  

        members_price_element = pro.find('div', class_='member-price')
        members_price = members_price_element.find('span', class_='price-container').text.strip() if members_price_element else "N/A"  
        
        discount_members=pro.find('div', class_='lbl_deal_mer_value')
        discount_members_offer=discount_members.find('span').text.strip() if discount_members else "N/A"  

        product_link = pro.find('a', class_="product-item-link")
        product_href = product_link.get('href').strip() if product_link else "N/A"  
        
        
        
        # Create the item dictionary with the values we have
        item = {
            'product': product,
            'product-information': product_info_text,
            'price': price,
            'old_price': old_price,
            'members_price': members_price,
            'discount': discount_offer,   #if old_price  else 'Discount available',
            #'members_offer': discount_offer,
            'discount_members_offer':discount_members_offer,
            'offer_valid_from': offer_available_from,
            'offer_valid_to': offer_available_til,
            'product-link': product_href,
            'category': url,
            'date': today_is,
            'updated': date_now
        }
        prd.append(item)
  
  return prd
  # Convert to DataFrame and save
  #if prd:
    #df = pd.DataFrame(prd)
    # Uncomment to save to file
    # df.to_csv(f'europris-products/{today_is}_produkter_kategorier.csv', index=False)
    #print(f"Found {len(prd)} products")
    #return prd
  #else:
    #print("No products found")
    #return []

def merge_csv_files(directory):
  # Directory containing the files
  product_lst = []
  # Iterate through files in the directory
  for filename in os.listdir(directory):
    # Check if the entry is a file
    if os.path.isfile(os.path.join(directory, filename)):
      products = pd.read_csv(f'{directory}/{filename}')
      products['produkter_kategorier'] = filename.split('_')[-1].replace(
          '.csv', '')

      product_lst.append(products)

  all_products = pd.concat(product_lst, ignore_index=True)

  all_products.to_csv(
      f'{directory}/all_csv_merged_product_data/products_{today_is}.csv',
      index=False)


if __name__ == "__main__":
  
  #urls=[]
  #with open('europris_categories-deep.txt','r') as f:
    #urls = [line.split(' ')[1].strip('\n') for line in f if line.strip()]
  
  #for url in urls:
    #print(product(url))
    
  urls=[]
  url_1='https://raw.githubusercontent.com/yosief-dev/scrape/refs/heads/main/europris_categories-deep.txt'
  response = requests.get(url_1, headers=headers)
  result=response.text[:-1]
  urls = [line.split(' ')[1] for line in result.split('\n')]
  #print(response.text)
  #print(urls)
  
  for url in urls:
    print(product(url))

