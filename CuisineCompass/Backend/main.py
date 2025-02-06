from datetime import datetime
from fastapi import FastAPI, Query
import requests
import pytesseract
import cv2
import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import re
import os
from dotenv import load_dotenv
import io
import logging

# Configure logging at the start of your script
logging.basicConfig(
    level=logging.DEBUG,  # Log everything (DEBUG level)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]  # Print to console
)
logger = logging.getLogger("CuisineCompass")

# Google Places API Key - from .env
load_dotenv()
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

app = FastAPI()

# Function to fetch nearby restaurants
def get_nearby_restaurants(dish_name: str):
    logger.info(f"\n\n Fetching nearby restaurants for dish: {dish_name}")
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=40.755450,-73.985638&radius=50&type=restaurant&keyword=restaurant&key={GOOGLE_PLACES_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Google Places API failed: {response.status_code}")
        return []
    data = response.json()
    logger.debug(f"\n\n API response: {data}")
    if 'results' in data:
        logger.info(f"\n\n Found {len(data['results'])} restaurants")
        result = []
        for i in range(len(data['results'])):
            if data['results'][i]['rating'] > 4.0:
                result.append(data['results'][i])
                if len(result) == 2:
                    break
        return result
    else:
        logger.warning("\n\n $$ No restaurants found in API response")
        return []

def save_image_from_url(img_url: str, save_path: str):
    try:
        img_data = requests.get(img_url).content
        with open(save_path, 'wb') as f:
            f.write(img_data)
        logger.info(f"Image saved to {save_path}")
    except Exception as e:
        logger.error(f"Failed to save image: {str(e)}")

def upscale_image_url(url: str) -> str:
    """
    Given an image URL from Google Maps (e.g. containing "w236-h298-k-no"),
    replace the resolution with higher values.
    Adjust "w800-h600-k-no" as desired.
    """
    new_url = re.sub(r"w\d+-h\d+-k-no", "w800-h600-k-no", url)
    return new_url

def scrape_menu_images(place_id: str, rname: str):
    logger.info(f"\n\n Scraping menu for place_id: {place_id}")
    options = Options()
    options.headless = True  # Set to False to visually check
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    menu_image_urls = []

    try:
        url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        driver.get(url)
        logger.debug("Google Maps page loaded")
        
        # Wait for the "Photos & videos" section heading and scroll to it.
        photos_heading = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(., 'Photos & videos')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", photos_heading)
        logger.info("\n\n Scrolled to 'Photos & videos' section")
        
        # Wait for the Menu button in the carousel.
        # The Menu button is identified by a button element whose aria-label attribute is "Menu"
        menu_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Menu']//img[@class='DaSXdd']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", menu_button)
        menu_button.click()
        logger.info("\n\n Clicked 'Menu' button")
        
        # After clicking
        # After clicking the Menu button...
        try:
            # Wait for the image grid to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'OKAoZd') and @data-photo-index]"))
            )
            
            # Get all photo elements with data-photo-index
            photo_elements = driver.find_elements(By.XPATH, "//a[contains(@class, 'OKAoZd') and @data-photo-index]")
            
            # Extract URLs from first 4 photos (indexes 0-3)
            for i in range(3):  # Get first 4 images
                try:
                    photo_element = photo_elements[i]
                    style = photo_element.find_element(By.XPATH, ".//div[@class='U39Pmb']").get_attribute("style")
                    
                    # Extract URL from background-image property
                    url_match = re.search(r'url\("(.*?)"\)', style)
                    if url_match:
                        img_url = url_match.group(1)
                        # Convert to high-res version if possible
                        if "=w" in img_url and "-k-no" in img_url:
                            img_url = re.sub(r"=w\d+", "=w1600", img_url)
                            img_url = re.sub(r"-h\d+", "-h1200", img_url)
                        menu_image_urls.append(img_url)
                        logger.info(f"Found menu image {i+1}: {img_url[:60]}...")
                except Exception as e:
                    logger.warning(f"Couldn't extract image {i+1}: {str(e)}")
                    continue

        except TimeoutException:
            logger.error("Timed out waiting for menu images to load")
        except Exception as e:
            logger.error(f"Error extracting menu images: {str(e)}")

        save_paths = []

        # Save the collected URLs
        if menu_image_urls:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            for idx, img_url in enumerate(menu_image_urls):
                if img_url.startswith("http"):
                    save_path = f"images/menu_image_{place_id}_{timestamp}_{idx+1}.jpg"
                    save_image_from_url(img_url, save_path)
                    save_paths.append(save_path)
        
        for img_url in save_paths:
            print(f"\n\n  Image URL: {img_url}\n\n")

        return save_paths
    except Exception as e:
        logger.error(f" # Scraping failed: {str(e)}", exc_info=True)
        return None
    finally:
        driver.quit()

def extract_text_from_image(image_path: str, dish: str):
    try:
        # Read image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not read image at {image_path}")
            return []

        # Preprocess image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 160, 275, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # OCR processing
        text = pytesseract.image_to_string(thresh).lower()
        logger.debug(f"OCR extracted from {image_path}: {text}")
        
        # Find full dish names containing the search term
        dish_matches = []
        for line in text.split('\n'):
            line = line.strip()
            if dish.lower() in line.lower():
                # Extract full dish name (assuming price comes after name)
                dish_name = line.split('$')[0].strip() if '$' in line else line
                dish_matches.append(dish_name)
                
        return dish_matches

    except Exception as e:
        logger.error(f"OCR failed for {image_path}: {str(e)}")
        return []
    
@app.get("/search")
def search_dish(dish: str = Query(..., min_length=2)):
    logger.info(f"\n\n Received search request for dish: {dish}")
    restaurants = get_nearby_restaurants(dish)
    print(f"\n\n Result from get_nearby_restaurants: {restaurants}")
    results = []
    
    if not restaurants:
        logger.warning("\n\n $$ No restaurants to process")
        return {"results": results}
    
    for restaurant in restaurants:
        place_id = restaurant.get("place_id")
        logger.info(f"\n\n Processing restaurant: {restaurant.get('name')} (ID: {place_id})")
        
        menu_image_paths = scrape_menu_images(place_id, restaurant.get("name"))
        if not menu_image_paths:
            logger.warning(f"\n\n $$ Skipping restaurant (no menu image): {restaurant.get('name')}")
            continue
        
        # Check all images for dish matches
        found_dishes = []
        for img_path in menu_image_paths:
            if os.path.exists(img_path):
                dish_matches = extract_text_from_image(img_path, dish)
                found_dishes.extend(dish_matches)
       
        results.append({
            "restaurant": restaurant.get("name"),
            "address": restaurant.get("vicinity"),
            "matching_dishes": list(set(found_dishes)),
            "rating": restaurant.get("rating")
        })
    
    logger.info(f"\n\n Returning {len(results)} results")
    return {"results": results}
