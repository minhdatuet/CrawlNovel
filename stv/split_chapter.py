import os

def split_and_save_chapters(content_file, output_folder):
    # Đọc nội dung của file
    with open(content_file, 'r', encoding='utf-8') as f:
        content_lines = f.readlines()

    # Khởi tạo các biến
    chapter_content = []  # Lưu nội dung của chương hiện tại
    chapter_index = 1  # Đếm chương
    os.makedirs(output_folder, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại

    # Duyệt qua các dòng trong file nội dung
    for line in content_lines:
        if line.strip().startswith('='):  # Gặp dòng toàn dấu '=' thì chia chương
            # Nếu đã có nội dung của chương hiện tại, lưu nó vào file
            if chapter_content:
                chapter_file_path = os.path.join(output_folder, f'{chapter_index:04d}_chapter.txt')
                with open(chapter_file_path, 'w', encoding='utf-8') as chapter_file:
                    chapter_file.writelines(chapter_content)
                chapter_content = []  # Reset nội dung chương
                chapter_index += 1  # Tăng chỉ số chương
        else:
            chapter_content.append(line)  # Thêm dòng vào chương hiện tại

    # Lưu chương cuối cùng nếu có
    if chapter_content:
        chapter_file_path = os.path.join(output_folder, f'{chapter_index:04d}_chapter.txt')
        with open(chapter_file_path, 'w', encoding='utf-8') as chapter_file:
            chapter_file.writelines(chapter_content)

# Đường dẫn đến file nội dung và thư mục lưu trữ các file chương nhỏ
content_file = 'cv.txt'  # Đường dẫn đến file nội dung
output_folder = 'cv'  # Thư mục để lưu các file chương

# Gọi hàm để cắt và lưu các chương
split_and_save_chapters(content_file, output_folder)
