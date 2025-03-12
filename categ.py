
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
        
        mer_prod_info=pro.find('div', class_='lipscore-rating-small')
        full_name = mer_prod_info.get('data-ls-product-name') if mer_prod_info else "N/A"
        sku = mer_prod_info.get('data-ls-sku') if mer_prod_info else "N/A"
        description = mer_prod_info.get('data-ls-description') if mer_prod_info else "N/A"
        sub_name= mer_prod_info.get('data-ls-brand') if mer_prod_info else "N/A"
        price_pro= mer_prod_info.get('data-ls-price') if mer_prod_info else "N/A"
        category_pro = mer_prod_info.get('data-ls-category') if mer_prod_info else "N/A"
        product_url = mer_prod_info.get('data-ls-product-url') if mer_prod_info else "N/A"
        GTIN = mer_prod_info.get('data-ls-gtin') if mer_prod_info else "N/A"
        image_url = mer_prod_info.get('data-ls-image-url') if mer_prod_info else "N/A"
        votes = mer_prod_info.get('data-ls-product-votes') if mer_prod_info else "N/A"
        rating = mer_prod_info.get('data-ls-rating') if mer_prod_info else "N/A"

        # Create the item dictionary with the values we have
        item = {
            'sku': sku,
            'name': product,
            'product-information': product_info_text,
            'price': price,
            'old_price': old_price,
            'members_price': members_price,
            'discount': discount_offer,   #if old_price  else 'Discount available',
            'discount_members_offer':discount_members_offer,
            'offer_valid_from': offer_available_from,
            'offer_valid_to': offer_available_til,
            'product_url': product_href,
            'category_url': url,
            'date': today_is,
            'updated': date_now,
            'GTIN': GTIN,
            'rating': rating,
            'votes': votes,
            'image_url': image_url,
            'description': description,
            'sub_name': sub_name,
            'full_name': full_name,
            'price_pro': price_pro,
            'category_pro': category_pro


        }
        prd.append(item)
  
  return prd
  
if __name__ == "__main__":
  urls=[]
  with open('europris_categories-deep.txt','r') as f:
    urls = [line.split(' ')[1].strip('\n') for line in f if line.strip()]
     #print(urls)
  
  for url in urls:
    try:
      print(product(url))
    except Exception as e:
      print(e)
    

