from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, Comment
import time
import logging

# Set up logging to capture debug information
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_url(url: str):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    text = ""
    try:
        driver.set_page_load_timeout(15)
        driver.get(url)

        # Wait for the body tag to load to ensure the page is rendered
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        time.sleep(3)  # Allow extra time for JS to render dynamic content
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Remove non-content tags like script, style, navigation, header, footer, and sidebars
        for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'noscript', 'form', 'button', 'svg', 'img']):
            tag.decompose()

        # Remove HTML comments using BeautifulSoup's Comment class
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Extract and clean text
        text = ' '.join(soup.stripped_strings)

        # Debug log the raw extracted text
        logging.debug(f"Raw extracted text from URL ({url}): {text[:500]}...")  # Log first 500 characters for brevity

        # If the extracted text is too short, it's likely not meaningful content
        if len(text) < 100:
            raise ValueError(f"Extracted text is too short (length: {len(text)}).")

    except Exception as e:
        logging.error(f"[URL EXTRACT ERROR] {e}")
        text = ""  # Return an empty string if extraction fails
    finally:
        driver.quit()

    return text, len(text)
