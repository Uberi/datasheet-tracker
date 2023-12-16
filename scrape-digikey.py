#!/usr/bin/env python3

import csv
import os
import traceback
import urllib

import requests
import bs4


DIGIKEY_PRODUCTS_EXPORT_CSV = sys.argv[1]
REQUEST_TIMEOUT_SECONDS = 60
SCRAPINGBEE_API_KEY = os.environ["SCRAPINGBEE_API_KEY"]


def scrape_digikey(digikey_product_number, save_file):
    try:
        with open(save_file) as f:
            page_content = f.read()
    except FileNotFoundError:
        r = requests.get("https://app.scrapingbee.com/api/v1", params={
            'premium_proxy': 'true',
            'country_code': 'CA',
            'block_resources': 'false',
            'api_key': SCRAPINGBEE_API_KEY,
            'url': f'https://www.digikey.ca/en/products/result?keywords={urllib.parse.quote(digikey_product_number)}',
        }, timeout=REQUEST_TIMEOUT_SECONDS)
        r.raise_for_status()
        with open(save_file, "w") as f:
            f.write(r.text)
        page_content = r.text
    soup = bs4.BeautifulSoup(page_content, 'lxml')
    datasheet_link = soup.select_one('a[data-testid=datasheet-download]')
    if not datasheet_link:
        return None
    datasheet_url = datasheet_link.get("href")
    if datasheet_url and datasheet_url.startswith("//"):
        datasheet_url = "https:" + datasheet_url
    return datasheet_url


def scrape_datasheet(datasheet_url, save_file):
    if os.path.exists(save_file):
        return
    timed_out = False
    try:
        r = requests.get(datasheet_url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.ReadTimeout:
        timed_out = True
    if timed_out or r.status_code == 403:  # try again using ScrapingBee
        print("retrying with ScrapingBee:", datasheet_url)
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


os.makedirs('digikey_datasheets', exist_ok=True)
with open(DIGIKEY_PRODUCTS_EXPORT_CSV) as f:
    for row in csv.DictReader(f):
        file_name = "".join(c if c in '\'"!@#$%^&*()-=_+[]{};,. abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' else '_' for c in f'{row["Digi-Key Part #"]} {row["Description"]}')
        try:
            datasheet_url = scrape_digikey(row["Digi-Key Part #"], os.path.join('digikey_datasheets', file_name + ".html"))
            if not datasheet_url:
                print("searching for datasheet failed:", row["Digi-Key Part #"], "- name:", file_name + ".html")
                continue
            try:
                scrape_datasheet(datasheet_url, os.path.join('digikey_datasheets', file_name + ".pdf"))
            except KeyboardInterrupt:
                break
            except:
                print("datasheet download failed:", datasheet_url, "- name:", file_name + ".pdf")
                traceback.print_exc()
                continue
            print("success:", row["Digi-Key Part #"])
        except KeyboardInterrupt:
            break
        except:
            print("failed:", row["Digi-Key Part #"])
            traceback.print_exc()
            continue
