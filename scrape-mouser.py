#!/usr/bin/env python3

import os
import traceback
import urllib

import xlrd
import requests
import bs4
 

MOUSER_PRODUCTS_EXPORT_CSV = sys.argv[1]
REQUEST_TIMEOUT_SECONDS = 60
SCRAPINGBEE_API_KEY = os.environ["SCRAPINGBEE_API_KEY"]


def scrape_mouser(mouser_product_number, save_file):
    try:
        with open(save_file) as f:
            page_content = f.read()
    except FileNotFoundError:
        r = requests.get("https://app.scrapingbee.com/api/v1", params={
            'premium_proxy': 'true',
            'country_code': 'CA',
            'block_resources': 'false',
            'api_key': SCRAPINGBEE_API_KEY,
            'url': f'https://www.mouser.ca/Search/Refine?Keyword={urllib.parse.quote(mouser_product_number)}',
        }, timeout=REQUEST_TIMEOUT_SECONDS)
        r.raise_for_status()

        # check for search page, if so pick the correct entry
        soup = bs4.BeautifulSoup(r.text, 'lxml')
        search_results = soup.select_one("#search-form")
        if search_results:
            product_page_link = search_results.select_one(f'tr[data-partnumber="{mouser_product_number}"] .mfr-part-num a')
            assert product_page_link
            actual_url = 'https://www.mouser.ca' + product_page_link.get("href")
            print("found search results page for", mouser_product_number, "- selecting correct entry:", actual_url)
            r = requests.get("https://app.scrapingbee.com/api/v1", params={
                'premium_proxy': 'true',
                'country_code': 'CA',
                'block_resources': 'false',
                'api_key': SCRAPINGBEE_API_KEY,
                'url': actual_url,
            }, timeout=REQUEST_TIMEOUT_SECONDS)
            r.raise_for_status()
        with open(save_file, "w") as f:
            f.write(r.text)
        page_content = r.text
    soup = bs4.BeautifulSoup(page_content, 'lxml')
    datasheet_link = soup.select_one('[data-dbdoctype=datasheet] a')
    if not datasheet_link:
        return None
    return datasheet_link.get("href")



def scrape_datasheet(datasheet_url, save_file):
    if os.path.exists(save_file):
        return

    force_scrapingbee = False

    if datasheet_url.startswith("https://www.ti.com/general/docs/suppproductinfo.tsp"):
        datasheet_url = urllib.parse.parse_qs(urllib.parse.urlparse(datasheet_url).query)["gotoUrl"][0]
    if datasheet_url.startswith("https://www.mouser.ca/datasheet/"):
        force_scrapingbee = True

    if not force_scrapingbee:
        try:
            r = requests.get(datasheet_url, timeout=REQUEST_TIMEOUT_SECONDS)
            if r.status_code == 403:
                force_scrapingbee = True
                print("retrying with ScrapingBee:", datasheet_url)
        except requests.exceptions.ReadTimeout:
            force_scrapingbee = True
            print("retrying with ScrapingBee:", datasheet_url)

    if force_scrapingbee:  # try again using ScrapingBee
        r = requests.get("https://app.scrapingbee.com/api/v1", params={
            'premium_proxy': 'true',
            'country_code': 'CA',
            'block_resources': 'false',
            'api_key': SCRAPINGBEE_API_KEY,
            'url': datasheet_url,
        }, timeout=REQUEST_TIMEOUT_SECONDS)
    r.raise_for_status()
    assert r.headers['content-type'] == "application/pdf", r.headers['content-type']
    with open(save_file, "wb") as f:
        f.write(r.content)


os.makedirs('mouser_datasheets', exist_ok=True)
workbook = xlrd.open_workbook(MOUSER_PRODUCTS_EXPORT_CSV)
sheet = workbook.sheet_by_index(0)
titles = [cell.value for cell in sheet.row(0)]
for row_index in range(1, sheet.nrows):
    row = {title: value for title, value in zip(titles, (cell.value for cell in sheet.row(row_index)))}
    file_name = "".join(c if c in '\'"!@#$%^&*()-=_+[]{};,. abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' else '_' for c in f'{row["Mouser Part #"]} {row["Mfr. Part #"]} {row["Description"]}')
    try:
        datasheet_url = scrape_mouser(row["Mouser Part #"], os.path.join('mouser_datasheets', file_name + ".html"))
        if not datasheet_url:
            print("searching for datasheet failed:", row["Mouser Part #"], "- name:", file_name + ".html")
            continue
        try:
            scrape_datasheet(datasheet_url, os.path.join('mouser_datasheets', file_name + ".pdf"))
        except KeyboardInterrupt:
            break
        except:
            print("datasheet download failed:", datasheet_url, "- name:", file_name + ".pdf")
            traceback.print_exc()
            continue
        print("success:", row["Mouser Part #"])
    except KeyboardInterrupt:
        break
    except:
        print("failed:", row["Mouser Part #"])
        traceback.print_exc()
        continue
