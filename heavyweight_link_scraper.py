# import general packages
import requests
import time
import logging

# import HTML parser
from bs4 import BeautifulSoup

# setup logging function to check for errors whilst scraping
logging.basicConfig(
    filename='heavyweight_link_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# define URLs
BASE_URL = "https://en.wikipedia.org"
CATEGORY_URL = "https://en.wikipedia.org/wiki/Category:Heavyweight_boxers"


# return a soup object from any requested URL
def make_soup(url):
    try:
        logging.info(f"fetching URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return None


# parse the heavyweight category pages and extract boxer profile links
def parse_links(url):
    soup = make_soup(url)
    if not soup:
        logging.error(f"Unable to make soup from {url}. Aborting operation")
        return []

    boxer_urls = []

    # extract the fighter links from the category block
    while True:
        cat_block = soup.find("div", class_="mw-category")
        if not cat_block:
            logging.warning("No category block found.")
            break

        # for each boxer, extract the URL
        for link in cat_block.find_all("a", href=True):
            complete_url = BASE_URL + link["href"]
            if complete_url not in boxer_urls:
                boxer_urls.append(complete_url)

        # extract the next page link and store it as the soup variable
        next_page = soup.find("a", string="next page")
        if next_page and 'href' in next_page.attrs:
            next_url = BASE_URL + next_page["href"]
            soup = make_soup(next_url)
            # crawl delay to avoid denied access
            time.sleep(1)
        else:
            break

    logging.info(f"{len(boxer_urls)} URLs extracted")
    return boxer_urls


# check whether the page contains a professional fight table
def contains_fight_table(url):
    soup = make_soup(url)
    if not soup:
        logging.error(f"Unable to make soup from {url}. Aborting operation")
        return False

    # search for specific columns that comprise the pro boxing record header
    # if present, then the fighter is a professional heavyweight and not solely an amateur
    try:
        for table in soup.find_all("table", class_="wikitable"):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if "Result" in headers and "Opponent" in headers and "Date" in headers:
                return True
    except Exception as e:
        logging.warning(f"unable to parse record table in {url}. {e}")

    return False

# execution of scrape and writing of links to urls.txt
def main():
    print('initiating scrape')

    # gather all links from the heavyweight category pages
    url_list = parse_links(CATEGORY_URL)
    pro_urls = []

    # ensure that all URLs are those of professional boxers
    for url in url_list:
        if contains_fight_table(url):
            pro_urls.append(url)
            logging.info(f"pro boxer added: {url}")
        # crawl delay to avoid denied access
        time.sleep(1)

    # write URLs to urls.txt
    # encode in UTF-8 to handle non-ASCII characters in the fighter names
    try:
        with open("urls.txt", "w", encoding="utf-8") as f:
            for link in pro_urls:
                f.write(link + "\n")
        logging.info(f"added {len(pro_urls)} fighter URLs to urls.txt.")
    except Exception as e:
        logging.error(f"unable to write URLs to urls.txt: {e}")

    print('scraping complete')

if __name__ == "__main__":
    main()
