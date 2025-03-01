import xml.etree.ElementTree as ET
import re

def filter_sitemap_urls(filepath):
    """
    Reads an XML sitemap file, extracts URLs ending with '-number', and prints them.

    Args:
        filepath (str): The path to the XML sitemap file.
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        namespaces = {
            'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'image': 'http://www.google.com/schemas/sitemap-image/1.1'
        }

        pattern = re.compile(r'-\d+$')  # Regex to match "-number" at the end

        filtered_urls = []

        for url_element in root.findall('sitemap:url', namespaces):
            loc = url_element.find('sitemap:loc', namespaces).text
            if pattern.search(loc):
                filtered_urls.append(loc)

        for i, url in enumerate(filtered_urls, start=1):
            print(f"{i}. {url}")

        return filtered_urls

    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return []
    except ET.ParseError:
        print(f"Error: Could not parse XML from '{filepath}'.")
        return []
    except AttributeError as e:
        print(f"Error: XML structure might be incorrect. {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

# Example usage:
filepath = "/home/yosief/Downloads/europrissitemap.xml" # Replace with your file path

filtered_url_list = filter_sitemap_urls(filepath)
#example of using the returned list.
count=0
with open('europris_links_products.txt', 'w', encoding='utf-8') as f:
    for i, url in enumerate(filtered_url_list, start=1):
        if url.startswith('https://www.europris.no/p-'):
            f.write(f"{i}. {url}\n")
            count+=1

print(f"Number of filtered urls: {count}")
        
    

