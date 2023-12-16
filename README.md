Electronics Datasheet Tracker
=============================

Input Digikey and Mouser order history, output a folder full of descriptively-named datasheet PDFs.

There are other projects that try to do the same thing (e.g., [digikey library](https://github.com/reinderien/digikey), [DigiGlass](https://github.com/mplewis/digiglass), [python-digikey](https://github.com/forrestv/python-digikey)), but none of them work anymore. The main reason for that, I think, is that most websites implemented anti-scraping measures that significantly increase the cost and complexity of scraping these websites.

Features:

* **Fully resumable** - if you interrupt and restart any of the scrapers, they'll keep going from where they left off.
    * You can also re-run it, and it'll only scrape items that it hasn't previously scraped.
* **Anti-bot protection bypass** - uses [ScrapingBee](https://www.scrapingbee.com/)'s residential proxies and headless browsers to skip CAPTCHA pages.
    * As of 2023, the free trial plan was enough for a few hundred datasheets.
    * I'd prefer not to rely on a third-party service here, but even if I integrated local headless browsing, it would still rely on a third-party residential proxy provider. For now, the scripts are short enough that I'd just rewrite them when ScrapingBee raises prices or goes out of business.
* **No API access needed, just screen scraping** - no waiting for approval or permission.
    * The API application process for all major distributors is far too slow and annoying, taking multiple days and human review.
* Also grabs an HTML mirror of the product page (including pricing and logistics info).
* About 100 lines of code per scraper - if you want more features it'll be really easy to add them yourself.

Rationale
---------

* Open hardware distributions should include everything you could reasonably need to continue developing the project, even if its dependencies have disappeared from the internet. That includes datasheets, source code for every included library, mirrors of key support pages, etc.
* Datasheets go offline, especially for more niche components. Manufacturers go out of business, websites disappear, and the Internet Archive doesn't capture everything. What if you come back to a project after a decade and critical info is missing?
* Previously, I was downloading and organizing datasheets by hand. This was tedious and time-consuming, and the effort was wasted if I decided against using the corresponding component later. Now I just run these scripts once a month.

Usage
-----

### Digikey

1. Export your parts history using the "Download" button under the "Products" tab on https://www.digikey.ca/OrderHistory/List. The result will be a CSV file named something like `DK_PRODUCTS.csv`.
2. Obtain a [ScrapingBee](https://www.scrapingbee.com/) API key and set the `SCRAPINGBEE_API_KEY` environment variable to that value.
3. Run `./scrape-digikey.py DK_PRODUCTS.csv` (replace `DK_PRODUCTS.csv` with the actual name of the CSV file).

### Mouser

1. Export your parts history using the "Export This Page To Excel" button on https://www.mouser.ca/account/orders/parts. The result will be an XLS file named something like `MouserSearch1728PM.xls`.
2. Obtain a [ScrapingBee](https://www.scrapingbee.com/) API key and set the `SCRAPINGBEE_API_KEY` environment variable to that value.
3. Run `./scrape-mouser.py MouserSearch1728PM.xls` (replace `MouserSearch1728PM.xls` with the actual name of the XLS file).

License
-------

I release everything in this repository under the [Creative Commons CC0 license](https://creativecommons.org/public-domain/cc0/) ("No Rights Reserved").
