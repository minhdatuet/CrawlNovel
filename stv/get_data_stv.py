from seleniumbase import Driver
import time
import base64
import re
from PIL import Image  # Import Pillow to handle image processing
from image_to_text import process_image_parts  # Import the image processing function
from selenium.webdriver.common.by import By
# Initialize the Selenium driver with Chrome options and undetected-chromedriver (uc=True)
driver = Driver(uc=True, headless=False)

# Base URL of the chapters
base_url = 'https://sangtacviet.com/truyen/faloo/1/186351/' # Link đến truyện
text_path = 'vltt.txt' # Tên file
start_keyword = "Vô lại Thiên Tôn"   # Từ khóa bắt đầu

# Function to capture a full-page screenshot using Chrome DevTools Protocol
def capture_full_page_screenshot(driver, output_path):
    driver.execute_cdp_cmd('Page.enable', {})
    screenshot = driver.execute_cdp_cmd('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': True})
    
    # Decode the base64 image data and save it as a file
    with open(output_path, 'wb') as file:
        file.write(base64.b64decode(screenshot['data']))

# Function to crop the image by removing a fixed number of pixels from the left and right margins
def crop_image_margins(image_path, left_margin=50, right_margin=50):
    image = Image.open(image_path)
    width, height = image.size

    # Calculate new dimensions after cropping the left and right margins
    new_left = left_margin
    new_right = width - right_margin

    # Crop the image and save it back to the same file
    cropped_image = image.crop((new_left, 0, new_right, height))
    cropped_image.save(image_path)

# Function to clean text by removing unnecessary Latin characters
def clean_text(text, start_keyword, end_keyword):
    """Clean extracted text by removing unnecessary Latin characters and unwanted phrases."""
    # Tìm lần xuất hiện đầu tiên của từ khóa bắt đầu
    first_start_idx = text.find(start_keyword)

    # Tìm lần xuất hiện thứ hai của từ khóa bắt đầu (nếu có)
    second_start_idx = text.find(start_keyword, first_start_idx + 1)

    # Nếu có lần xuất hiện thứ hai, cắt phần trước nó
    if second_start_idx != -1:
        text = text[second_start_idx + len(start_keyword):].strip()
    elif first_start_idx != -1:
        # Nếu chỉ có một lần xuất hiện, cắt phần trước lần đầu tiên
        text = text[first_start_idx + len(start_keyword):].strip()

    # Tìm vị trí cuối cùng của từ khóa kết thúc và cắt phần sau nó
    end_idx = text.rfind(end_keyword)
    if end_idx != -1:
        text = text[:end_idx].strip()

    # Danh sách các cụm từ cần xóa
    unwanted_phrases = ["< Chương trước", "Mục lục", "Chương sau >", "@Bạn đang đọc bản lưu trong hệ thống"]

    # Xóa các cụm từ không mong muốn khỏi văn bản
    for phrase in unwanted_phrases:
        text = text.replace(phrase, "").strip()

    # Loại bỏ các dòng trống liên tiếp chỉ giữ lại tối đa một dòng trống
    text = re.sub(r'\n\s*\n', '\n\n', text)

    return text

# Function to get text from the current page by taking a screenshot and using OCR
def get_text_from_image_screenshot(driver):
    # Xóa quảng cáo bằng cách sử dụng JavaScript
    driver.execute_script("""
        let relatedAds = document.getElementsByClassName('trc_related_container');
        for (let ad of relatedAds) {
            ad.style.display = 'none';  // Ẩn quảng cáo
            // hoặc: ad.remove();  // Xóa quảng cáo
        }
        
        let adBlocks = document.getElementsByClassName('adBlock');
        for (let ad of adBlocks) {
            ad.style.display = 'none';  // Ẩn quảng cáo
            // hoặc: ad.remove();  // Xóa quảng cáo
        }
                          
        let cmAdPlayer = document.getElementsByClassName('cm-ad-player');
        for (let cm of cmAdPlayer) {
            cm.style.display = 'none';  // Ẩn quảng cáo
            // hoặc: ad.remove();  // Xóa quảng cáo
        }
    """)

    

    screenshot_path = f'full_page_screenshot.png'
    
    # Capture a full-page screenshot
    capture_full_page_screenshot(driver, screenshot_path)

    # Crop the left and right margins of the screenshot
    crop_image_margins(screenshot_path, left_margin=100, right_margin=50)

    # Process the cropped screenshot to extract text using the image-to-text function
    extracted_text = process_image_parts(screenshot_path)
    
    return extracted_text

# Function to recursively crawl the website and record paths
def crawl_website(url):
    # Visit the URL
    driver.get(url)
    languages = driver.find_elements(By.CLASS_NAME, 'seloption')
    if (languages):
        languages[0].click()
        time.sleep(3)
    # Find all the links on the current page
    links = driver.find_elements(By.CLASS_NAME, 'listchapitem')
    i = 0
    curr_chapter = 0
    for link in links:
        i+=1
        if i> curr_chapter:
            driver.find_element(By.ID, 'clicktoexp').click()
            link.click()

            # Wait for the page to load completely
            time.sleep(7)
            # Get the text from the image screenshot
            chapter_text = get_text_from_image_screenshot(driver)

            # Clean the extracted text
            end_keyword = "< Chương trước"    # Từ khóa kết thúc
            cleaned_text = clean_text(chapter_text, start_keyword, end_keyword)

            # Write the cleaned text to a file
            with open(text_path, "a", encoding="utf-8") as file:
                file.write(cleaned_text)
                file.write("\n" + "="*50 + "\n")  # Separator between chapters

            # Go back to the original page
            driver.back()
            driver.find_element(By.ID, 'clicktoexp').click()

crawl_website(base_url)
# Đóng trình duyệt sau khi hoàn thành
driver.quit()
