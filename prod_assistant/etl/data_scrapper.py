import csv
import os
import time
from bs4 import BeautifulSoup
import requests as rq
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class FlipkartScrapper:
    def __init__(self, output_dir="data"):
        """
        Initialize the scraper with an output directory.
        Creates the directory if it doesn't exist.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)  # Ensure output folder exists

    def get_top_reviews(self, product_url, count=2):
        """
        Get top 'count' reviews for a product from its Flipkart URL.
        Returns reviews joined by '||' or a default message if none found.
        """
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Launch undetected Chrome to avoid bot detection
        driver = uc.Chrome(options=options, use_subprocess=True)

        if not product_url.startswith("http"):
            return "No reviews found"  # Invalid URL

        try:
            driver.get(product_url)
            time.sleep(5)  # Wait for page to load

            # Close popup if present (like login or cookie notice)
            try:
                driver.find_element(by=By.XPATH, value="//button[contains(text(), 'X')]").click()
                time.sleep(2)
            except Exception as e:
                print("Error occured while closing cookie popup", e)

            # Scroll down multiple times to load lazy-loaded reviews
                ActionChains(driver).send_keys(Keys.END).perform()
                time.sleep(1.5)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            review_blocks = soup.select("div._27M-vq, div.col.EPCmJX, div._6K-7Co")
            seen = set()
            reviews = []

            for block in review_blocks:
                text = block.get_text(separator=" ", strip=True)
                if text and text not in seen:
                    reviews.append(text)
                    seen.add(text)
                if len(reviews) >= count:
                    break
        except Exception:
            reviews = []

        driver.quit()
        return " || ".join(reviews) if reviews else "No reviews found"
    

    def scrape_flipkart_products(self, query, max_products=1, review_count=2):
        """
        Search Flipkart for a query and scrape product details including top reviews.
        Returns a list of products with [product_id, title, rating, total_reviews, price, top_reviews].
        """
        options = uc.ChromeOptions()
        driver = uc.Chrome(options=options, use_subprocess=True)

        # Build search URL
        search_url = "https://www.flipkart.com/search?q=" + query.replace(" ", "+")
        driver.get(search_url)
        time.sleep(5)

        # Close popup if present
        try:
            driver.find_element(by=By.XPATH, value="//button[contains(text(), 'X')]").click()
            time.sleep(2)
        except Exception as e:
            print("Error occured while closing cookie popup", e)

        time.sleep(2)
        products = []

        # Select top 'max_products' items
        items = driver.find_elements(By.CSS_SELECTOR, "div[data-id]")[:max_products]
        for item in items:
            try:
                # Scrape product details
                title = item.find_element(By.CSS_SELECTOR, "div.KzDlHZ").text.strip()
                price = item.find_element(By.CSS_SELECTOR, "div.Nx9bqj").text.strip()
                rating = item.find_element(By.CSS_SELECTOR, "div.XQDdHH").text.strip()
                reviews_text = item.find_element(By.CSS_SELECTOR, "span.Wphh3N").text.strip()
                
                # Extract number of reviews using regex from reviews_text which will be like "1,234 Reviews"
                match = re.search(r"\d+(,\d+)?(?=\s+Reviews)", reviews_text)
                total_reviews = match.group(0) if match else "N/A"

                # Get product link
                link_el = item.find_element(By.CSS_SELECTOR, "a[href*='/p/']")
                
                href = link_el.get_attribute("href")
                product_link = href if href.startswith("http") else "https://www.flipkart.com" + href

                # Extract product ID from URL
                match = re.findall(r"/p/(itm[0-9A-Za-z]+)", href)
                product_id = match[0] if match else "N/A"
            except Exception as e:
                print(f"Error occurred while processing item: {e}")
                continue

            # Get top reviews for the product
            top_reviews = (
                self.get_top_reviews(product_link, count=review_count)
                if "flipkart.com" in product_link
                else "Invalid product URL"
            )
            
            # Append product info to list
            products.append([product_id, title, rating, total_reviews, price, top_reviews])

        driver.quit()
        return products

    def save_to_csv(self, data, filename="product_reviews.csv"):
        """
        Save scraped data to a CSV file.
        Handles:
        1. Absolute path
        2. Relative path with subfolder (creates folder if needed)
        3. Plain filename (saves inside self.output_dir)
        """
        if os.path.isabs(filename):
            path = filename  # Absolute path given, use directly
        elif os.path.dirname(filename):  # filename includes subfolder like 'data/product_reviews.csv'
            path = filename
            os.makedirs(os.path.dirname(path), exist_ok=True)  # Create folder if it doesn't exist
        else:
            # plain filename like 'output.csv'
            path = os.path.join(self.output_dir, filename)  # Save inside default output folder

        # Write CSV
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write header row
            writer.writerow(["product_id", "product_title", "rating", "total_reviews", "price", "top_reviews"])
            # Write all product rows
            writer.writerows(data)
