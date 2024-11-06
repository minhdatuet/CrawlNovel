# image_to_text.py

import requests
import time
import re
from PIL import Image
import os
import cv2
import numpy as np

def split_image_smart(image_path, target_ratio_width=1920, target_ratio_height=1080):
    # Load the image using OpenCV
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply binary thresholding to create a binary image (black text on white background)
    _, binary_image = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Calculate target slice height based on the 1920:1080 ratio
    img_width = image.shape[1]
    slice_height = int(img_width * target_ratio_height / target_ratio_width)

    # Sum up the pixel values along each row (to find horizontal lines with no text)
    horizontal_projection = np.sum(binary_image, axis=1)

    image_parts = []
    current_top = 0

    while current_top < image.shape[0]:
        # Calculate the bottom boundary of the slice based on target ratio
        proposed_bottom = min(current_top + slice_height, image.shape[0])

        # Look for the closest white space below the proposed bottom boundary
        white_space_indices = np.where(horizontal_projection[proposed_bottom:] <= 10)[0]

        if len(white_space_indices) > 0:
            nearest_white_space = proposed_bottom + white_space_indices[0]
            bottom = nearest_white_space
        else:
            bottom = proposed_bottom  # If no white space found, use the proposed boundary

        # Crop the image from current_top to bottom
        cropped_image = image[current_top:bottom, :]
        image_parts.append(Image.fromarray(cropped_image))

        # Move to the next part of the image
        current_top = bottom

    return image_parts

def upload_image_to_google_lens(image_path, retries=2):
    # Set the boundary for multipart request
    boundary = "----WebKitFormBoundary"
    
    # Read the image file content
    with open(image_path, 'rb') as file:
        content_file = file.read()

    # Prepare the post data
    post_data = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="encoded_image"; filename="image.jpg"\r\n'
        'Content-Type: image/jpeg\r\n\r\n'
    ).encode('utf-8') + content_file + f"\r\n--{boundary}--\r\n".encode('utf-8')
    
    # Generate a timestamp in milliseconds
    timestamp = int(time.time() * 1000)

    # Google Lens API URL (unofficial, subject to changes)
    url = f"https://lens.google.com/v3/upload?hl=en-VN&re=df&stcs={timestamp}&ep=subb"

    # Prepare headers
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Referer': 'https://lens.google.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    attempt = 0
    while attempt <= retries:
        # Send the post request
        response = requests.post(url, headers=headers, data=post_data)

        # Check the response
        if response.status_code == 200:
            # Process the response using regex to extract the necessary information
            match = re.search(r'"\,\[\[\[(.*?)\]\]\,\"', response.text)
            
            if match:
                all_text = match.group(1)
                all_text_list = eval(f"[{all_text}]")
                
                # Sử dụng ký tự xuống dòng để nối chuỗi
                new_text = "\n\n".join(all_text_list)
                return {"result": new_text}
            else:
                attempt += 1  # Increase attempt count
                if attempt > retries:
                    return {"failed": "Không thể nhận dạng được văn bản sau khi thử lại."}
        else:
            attempt += 1  # Increase attempt count
            if attempt > retries:
                return {"failed": "Request failed sau khi thử lại."}

        # Thêm khoảng chờ giữa các yêu cầu để tránh vấn đề tốc độ
        time.sleep(2)  # Chờ 2 giây trước khi gửi lại yêu cầu


def save_image_parts(image_parts, base_filename="image_part"):
    # Ensure a folder to save the parts exists
    if not os.path.exists('image_parts'):
        os.makedirs('image_parts')
    
    part_filenames = []
    
    for i, part in enumerate(image_parts):
        # Chuyển đổi từ RGBA sang RGB nếu cần
        if part.mode == 'RGBA':
            part = part.convert('RGB')
        
        part_filename = f"image_parts/{base_filename}_{i}.jpg"
        part.save(part_filename)
        part_filenames.append(part_filename)
    
    return part_filenames

def process_image_parts(image_path):
    # Step 1: Split the image intelligently based on target ratio and white spaces
    image_parts = split_image_smart(image_path)
    
    # Step 2: Save the image parts and get their filenames
    part_filenames = save_image_parts(image_parts)
    
    # Step 3: Send each part to Google Lens and collect results
    all_results = []
    
    for part_filename in part_filenames:
        result = upload_image_to_google_lens(part_filename)
        
        if "result" in result:
            all_results.append(result['result'])
        else:
            all_results.append(result['failed'])
        
        # Thêm khoảng chờ giữa các yêu cầu để tránh vấn đề tốc độ

    # Step 4: Return the combined results
    return "\n\n".join(all_results)

def process_images_in_directory(directory_path, output_file="temp.txt"):
    # Mở file ghi kết quả
    with open(output_file, 'w', encoding='utf-8') as file_output:
        # Duyệt qua các ảnh trong thư mục
        for image_filename in os.listdir(directory_path):
            image_path = os.path.join(directory_path, image_filename)
            
            # Kiểm tra nếu file là ảnh
            if image_filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                # In ra tên ảnh để tiện theo dõi
                print(f"Processing {image_filename}...")
                
                # Thực hiện xử lý ảnh và nhận về nội dung result
                result = process_image_parts(image_path)
                
                # Ghi tên ảnh và nội dung result vào file output
                file_output.write(f"{image_filename}\n'{result}'\n\n")
    
