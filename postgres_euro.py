from datetime import datetime
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests
import pandas as pd
import math
import time
import psycopg2
from psycopg2.extras import Json

headers = {
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
url = 'https://www.europris.no/'

current_date = datetime.now()
today_is = current_date.strftime("%Y/%m/%d")
date_now = current_date.strftime("%Y-%m-%d %H:%M:%S")
#timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Database connection parameters
DB_NAME = ""
DB_USER = ""
DB_PASSWORD = ""
DB_HOST = ""
DB_PORT = "5432"


def create_db_table():
    """Create the europris table if it doesn't exist"""
    conn = None
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        
        cursor = conn.cursor()
        
        # Set timezone to Oslo time
        cursor.execute("SET timezone TO 'Europe/Oslo';")
        
        # Create table with sku as primary key
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS europris (
            sku VARCHAR(50) PRIMARY KEY,
            name TEXT,
            product_information TEXT,
            price DECIMAL(10,2),
            old_price VARCHAR(50),
            members_price TEXT,
            discount TEXT,
            discount_members_offer TEXT,
            offer_valid_from VARCHAR(50),
            offer_valid_to VARCHAR(50),
            product_url TEXT,
            category_url TEXT,
            date TEXT,
            updated TEXT,
            gtin VARCHAR(50),
            rating VARCHAR(50),
            votes VARCHAR(50),
            image_url TEXT,
            description TEXT,
            sub_name TEXT,
            full_name TEXT,
            price_pro VARCHAR(50),
            category_pro TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        conn.commit()
        print("Table created successfully")
        
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

def insert_product(product_data):
    """Insert or update a product in the database"""
    conn = None
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        
        # Set timezone to Oslo time for this connection
        cursor = conn.cursor()
        cursor.execute("SET timezone TO 'Europe/Oslo';")
        
        # Convert 'N/A' to None for numeric fields
        for key in ['price', 'old_price', 'price_pro']:
            if product_data[key] == 'N/A':
                product_data[key] = None
            elif product_data[key] is not None and product_data[key] != 'N/A':
                try:
                    product_data[key] = float(product_data[key])
                except ValueError:
                    product_data[key] = None
        
        # Handle empty ratings and votes
        for key in ['rating', 'votes']:
            if product_data[key] is None or product_data[key] == 'None':
                product_data[key] = None
        
        # SQL for insert with ON CONFLICT (upsert)
        sql = """
        INSERT INTO europris (
            sku, name, product_information, price, old_price, members_price, 
            discount, discount_members_offer, offer_valid_from, offer_valid_to, 
            product_url, category_url, date, updated, gtin, rating, votes, 
            image_url, description, sub_name, full_name, price_pro, category_pro
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (sku) 
        DO UPDATE SET
            name = EXCLUDED.name,
            product_information = EXCLUDED.product_information,
            price = EXCLUDED.price,
            old_price = EXCLUDED.old_price,
            members_price = EXCLUDED.members_price,
            discount = EXCLUDED.discount,
            discount_members_offer = EXCLUDED.discount_members_offer,
            offer_valid_from = EXCLUDED.offer_valid_from,
            offer_valid_to = EXCLUDED.offer_valid_to,
            product_url = EXCLUDED.product_url,
            category_url = EXCLUDED.category_url,
            date = EXCLUDED.date,
            updated = EXCLUDED.updated,
            gtin = EXCLUDED.gtin,
            rating = EXCLUDED.rating,
            votes = EXCLUDED.votes,
            image_url = EXCLUDED.image_url,
            description = EXCLUDED.description,
            sub_name = EXCLUDED.sub_name,
            full_name = EXCLUDED.full_name,
            price_pro = EXCLUDED.price_pro,
            category_pro = EXCLUDED.category_pro,
            updated_at = CURRENT_TIMESTAMP
        """
        
        # Execute the SQL with product data
        cursor.execute(sql, (
            product_data['sku'],
            product_data['name'],
            product_data['product-information'],
            product_data['price'],
            product_data['old_price'],
            product_data['members_price'],
            product_data['discount'],
            product_data['discount_members_offer'],
            product_data['offer_valid_from'],
            product_data['offer_valid_to'],
            product_data['product_url'],
            product_data['category_url'],
            product_data['date'],
            product_data['updated'],
            product_data['GTIN'],
            product_data['rating'],
            product_data['votes'],
            product_data['image_url'],
            product_data['description'],
            product_data['sub_name'],
            product_data['full_name'],
            product_data['price_pro'],
            product_data['category_pro']
        ))
        
        conn.commit()
        print(f"Product with SKU {product_data['sku']} inserted/updated successfully")
        
    except Exception as e:
        print(f"Error inserting product with SKU {product_data.get('sku', 'unknown')}: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

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
        
        # Insert product into database
        insert_product(item)
  
  return prd
  
if __name__ == "__main__":
  # Create the database table first
  create_db_table()
  
  # Print the current time to verify
  print(f"Script running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  
  urls=[]
  with open('europris_categories-deep.txt','r') as f:
    urls = [line.split(' ')[1].strip('\n') for line in f if line.strip()]
  
  for url in urls:
    try:
      products = product(url)
      print(f"Processed {len(products)} products from {url}")
    except Exception as e:
      print(f"Error processing URL {url}: {e}")
    time.sleep(1)  # Small delay to avoid overwhelming the server
