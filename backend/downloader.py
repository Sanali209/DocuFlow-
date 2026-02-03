import os
import zipfile
import io

def create_folder_zip(folder_path: str) -> io.BytesIO:
    """
    Compresses the contents of a folder into a ZIP archive in memory.
    Returns a BytesIO object containing the ZIP data.
    """
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate relative path for archive
                archive_name = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, archive_name)
                
    zip_buffer.seek(0)
    return zip_buffer
