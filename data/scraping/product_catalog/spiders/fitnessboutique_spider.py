import re
from urllib.parse import urljoin

import scrapy


class FitnessBoutiqueSpider(scrapy.Spider):
    name = "fitnessboutique"

    allowed_domains = ["fitnessboutique.fr"]

    start_urls = [
        "https://www.fitnessboutique.fr/collections/musculation-accessoire"
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 5,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "LOG_LEVEL": "INFO",
    }

    source = "fitnessboutique"
    category_code = "MUSCULATION_ACCESSORY"
    category_name = "Accessoires de musculation"

    def parse(self, response):
        self.logger.info("Parsing collection page: %s", response.url)

        products = response.css("product-card")
        self.logger.info("Found %s product cards on page", len(products))

        for product in products:
            item = self.parse_product_card(product, response)

            if not self.is_valid_item(item):
                self.logger.warning(
                    "Skipped incomplete product on page %s: %s",
                    response.url,
                    item,
                )
                continue

            yield item

        next_page = self.get_next_page(response)

        if next_page:
            self.logger.info("Following next page: %s", next_page)
            yield response.follow(next_page, callback=self.parse)
        else:
            self.logger.info("No next page found. Scraping completed.")

    def parse_product_card(self, product, response):
        external_product_id = self.clean_text(
            product.css("input.js-compare-checkbox::attr(data-product-id)").get()
        )

        product_url = self.clean_text(
            product.css("input.js-compare-checkbox::attr(data-product-url)").get()
        )

        brand = self.clean_text(
            product.css(".card__vendor::text").get()
        )

        name = self.clean_text(
            product.css(".card__title a::text").get()
        )

        description = self.clean_text(
            product.css(".card__subtitle::text").get()
        )

        price_text = self.clean_text(
            product.css(".price__current::text").get()
        )

        original_price_text = self.clean_text(
            product.css(".price__was::text").get()
        )

        availability_text = self.clean_text(
            product.css(".product-inventory__status::text").get()
        )

        inventory_level = self.clean_text(
            product.css(".product-inventory__status::attr(data-inventory-level)").get()
        )

        image_url = self.clean_text(
            product.css("img.card__main-image::attr(data-src)").get()
        )

        image_alt = self.clean_text(
            product.css("img.card__main-image::attr(alt)").get()
        )

        return {
            "source": self.source,
            "collection_url": response.url,
            "category_code": self.category_code,
            "category_name": self.category_name,
            "external_product_id": external_product_id,
            "product_url": self.normalize_url(product_url, response),
            "brand": brand,
            "name": name,
            "description": description,
            "price_text": price_text,
            "original_price_text": original_price_text,
            "availability_text": availability_text,
            "inventory_level": inventory_level,
            "image_url": self.normalize_url(image_url, response),
            "image_alt": image_alt,
        }

    def get_next_page(self, response):
        page_links = response.css("a[href*='page=']::attr(href)").getall()

        current_page_number = self.extract_page_number(response.url)

        candidate_pages = []

        for link in page_links:
            page_number = self.extract_page_number(link)

            if page_number is not None and page_number > current_page_number:
                candidate_pages.append((page_number, link))

        if not candidate_pages:
            return None

        next_page_number, next_page_url = sorted(candidate_pages, key=lambda item: item[0])[0]

        self.logger.info(
            "Current page: %s | Next page detected: %s",
            current_page_number,
            next_page_number,
        )

        return next_page_url

    @staticmethod
    def extract_page_number(url):
        match = re.search(r"[?&]page=(\d+)", url)

        if match:
            return int(match.group(1))

        return 1

    @staticmethod
    def clean_text(value):
        if value is None:
            return None

        cleaned_value = " ".join(value.split())
        return cleaned_value.strip() or None

    @staticmethod
    def normalize_url(value, response):
        if value is None:
            return None

        if value.startswith("//"):
            return f"https:{value}"

        return urljoin(response.url, value)

    @staticmethod
    def is_valid_item(item):
        required_fields = [
            "product_url",
            "name",
            "price_text",
            "image_url",
            "category_name",
        ]

        return all(item.get(field) for field in required_fields)