import re


def filter_urls(urls):
    """
    Filter URLs based on multiple criteria.
    
    Args:
        urls: List of URL strings
    
    Returns:
        List of filtered URLs
    """
    # Process URLs to extract digit patterns
    url_data = []
    
    # First pass: collect data about each URL
    for url in urls:
        match = re.search(r'/c/(\d+)$', url)
        if match:
            digits = match.group(1)
            url_parts = url.strip('/').split('/')
            url_data.append((url, digits, url_parts))
    
    # Find URLs to exclude based on both criteria
    exclude_urls = set()
    
    # Criterion 1: Exclude URLs with shorter digit sequences
    for url1, digits1, parts1 in url_data:
        for url2, digits2, parts2 in url_data:
            if url1 == url2:
                continue
            
            # If the digits of url2 start with the digits of url1 and are longer
            if digits2.startswith(digits1) and len(digits2) > len(digits1):
                exclude_urls.add(url1)
                break
    
    # Criterion 2: Exclude URLs with length 3 when split by '/' and last part in 200s range
    for url, digits, parts in url_data:
        # Check if the URL has 3 parts when split by '/'
        if len(parts) == 3:
            # Check if the digits are in the 200s range (201-299)
            if digits.isdigit() and 201 <= int(digits) <= 299:
                exclude_urls.add(url)
    
    # Return only URLs that should not be excluded
    return [url for url in urls if url not in exclude_urls]



def main():
    input_file = "sitemap_links.txt"  # Set default input file name
    output_file = "nested_links_sitemap.txt"  # Set default output file name

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        filtered_urls = filter_urls(urls)

        with open(output_file, 'w', encoding='utf-8') as f:
            for url in filtered_urls:
                f.write(f"{url}\n")

        print(f"Filtered URLs written to {output_file}")
        print(f"Original count: {len(urls)}, Filtered count: {len(filtered_urls)}")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        # No sys.exit(1) here as it's not a fatal error if you want to create a default file.
    except Exception as e:
        print(f"Error: {e}")
        # no sys.exit(1) here as it's not a fatal error if you want to create a default file.

if __name__ == "__main__":
    main()
