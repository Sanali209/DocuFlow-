import os
import difflib
import requests
import time
from pathlib import Path

# Configuration
OCR_URL = "http://localhost:8000/documents/scan" # Going through the main backend proxy to test full flow
# Alternatively test direct: "http://localhost:7860/process" 

TEST_DATA_DIR = Path("verification/test_data")

def calculate_cer(reference, hypothesis):
    """
    Calculate Character Error Rate (CER).
    CER = (S + D + I) / N
    S = Substitution, D = Deletion, I = Insertion, N = Number of characters in reference
    """
    if not reference:
        return 1.0 if hypothesis else 0.0
    
    matcher = difflib.SequenceMatcher(None, reference, hypothesis)
    return 1.0 - matcher.ratio()

def run_benchmark():
    if not TEST_DATA_DIR.exists():
        print(f"Test data directory {TEST_DATA_DIR} does not exist.")
        print("Please place pairs of images (.png/.jpg) and ground truth text (.txt) in this folder.")
        # Create dummy data for demonstration
        TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
        # We would need to generate a real image with text to benchmark properly. 
        # For now, we will just warn.
        return

    image_files = list(TEST_DATA_DIR.glob("*.png")) + list(TEST_DATA_DIR.glob("*.jpg"))
    
    print(f"Found {len(image_files)} test images.")
    
    total_cer = 0
    count = 0
    
    for img_path in image_files:
        txt_path = img_path.with_suffix(".txt")
        if not txt_path.exists():
            print(f"Skipping {img_path}: No ground truth .txt file found.")
            continue
            
        with open(txt_path, "r", encoding="utf-8") as f:
            reference_text = f.read().strip()
            
        print(f"Processing {img_path}...")
        
        try:
            with open(img_path, "rb") as f:
                files = {"file": (img_path.name, f, "image/png" if img_path.suffix == ".png" else "image/jpeg")}
                start_time = time.time()
                # adjusting for common proxy endpoint or direct service
                # If testing backend proxy
                response = requests.post(OCR_URL, files=files) 
                
                # If testing direct service, response format might be different
                # response = requests.post("http://localhost:7860/process", files=files)
                
                if response.status_code != 200:
                    print(f"Error: {response.status_code} - {response.text}")
                    continue
                
                result = response.json()
                hypothesis_text = result.get("content", "") # or "markdown" if direct service
                
                duration = time.time() - start_time
                
                cer = calculate_cer(reference_text, hypothesis_text)
                total_cer += cer
                count += 1
                
                print(f"  CER: {cer:.4f} ({duration:.2f}s)")
                
        except Exception as e:
            print(f"  Failed: {e}")

    if count > 0:
        print(f"\nAverage CER: {total_cer / count:.4f}")
    else:
        print("\nNo valid test pairs processed.")

if __name__ == "__main__":
    run_benchmark()
