from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pytesseract
import io
from pyzbar import pyzbar
import numpy as np
import cv2
import re

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_INDEX = BASE_DIR / "frontend" / "index.html"

app = FastAPI(title="OCR IO", version="6.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=500, detail="Frontend not found")
    return HTMLResponse(content=FRONTEND_INDEX.read_text(encoding="utf-8"))


def detect_qr_barcodes(image):
    """Detect QR codes and barcodes"""
    try:
        img_array = np.array(image)
        decoded_objects = pyzbar.decode(img_array)
        results = []
        for obj in decoded_objects:
            data = obj.data.decode('utf-8', errors='ignore')
            results.append(f"[{obj.type}] {data}")
        return results
    except:
        return []


def preprocess_method_1(img):
    """Method 1: High contrast binary"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def preprocess_method_2(img):
    """Method 2: Adaptive threshold"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.GaussianBlur(gray, (5, 5), 0)
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return binary


def preprocess_method_3(img):
    """Method 3: CLAHE + morphology"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    return cleaned


def is_valid_text(text):
    """Check if extracted text is valid (not garbled)"""
    if not text or len(text) < 3:
        return False
    
    # Count alphanumeric characters
    alnum_count = sum(c.isalnum() or c.isspace() for c in text)
    total_chars = len(text)
    
    # If less than 50% are valid characters, it's probably garbled
    if total_chars > 0 and (alnum_count / total_chars) < 0.5:
        return False
    
    # Check for excessive special characters
    special_count = sum(not c.isalnum() and not c.isspace() and c not in '.,!?@#$%&*()-_=+[]{}:;"\'' for c in text)
    if special_count > (total_chars * 0.3):
        return False
    
    return True


def clean_text(text):
    """Clean extracted text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove lines with too many special characters
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip() and is_valid_text(line):
            cleaned_lines.append(line.strip())
    return '\n'.join(cleaned_lines)


def extract_text_multi_method(image):
    """Try multiple preprocessing methods and return best result"""
    # Convert PIL to OpenCV
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    # Upscale
    height, width = img.shape[:2]
    if width < 2000 or height < 2000:
        scale = max(2000 / width, 2000 / height)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    results = []
    
    # Try method 1
    try:
        processed = preprocess_method_1(img.copy())
        config = '--oem 3 --psm 1'
        text = pytesseract.image_to_string(processed, config=config)
        if is_valid_text(text):
            results.append(('method1', clean_text(text)))
    except:
        pass
    
    # Try method 2
    try:
        processed = preprocess_method_2(img.copy())
        config = '--oem 3 --psm 3'
        text = pytesseract.image_to_string(processed, config=config)
        if is_valid_text(text):
            results.append(('method2', clean_text(text)))
    except:
        pass
    
    # Try method 3
    try:
        processed = preprocess_method_3(img.copy())
        config = '--oem 3 --psm 6'
        text = pytesseract.image_to_string(processed, config=config)
        if is_valid_text(text):
            results.append(('method3', clean_text(text)))
    except:
        pass
    
    # Try with original (minimal processing)
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        config = '--oem 3 --psm 1'
        text = pytesseract.image_to_string(gray, config=config)
        if is_valid_text(text):
            results.append(('original', clean_text(text)))
    except:
        pass
    
    if not results:
        return ""
    
    # Return longest valid result
    best = max(results, key=lambda x: len(x[1]))
    return best[1]


@app.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...)):
    """Multi-method OCR with validation"""
    
    try:
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Load image
        image = Image.open(io.BytesIO(raw))
        
        # Auto-orient
        image = ImageOps.exif_transpose(image)
        
        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Detect QR/barcodes
        qr_barcode_data = detect_qr_barcodes(image)
        
        # Extract text with multiple methods
        ocr_text = extract_text_multi_method(image)
        
        # Combine results
        result_parts = []
        
        if qr_barcode_data:
            result_parts.append("=== QR CODES / BARCODES ===")
            result_parts.extend(qr_barcode_data)
            result_parts.append("")
        
        if ocr_text:
            if qr_barcode_data:
                result_parts.append("=== TEXT CONTENT ===")
            result_parts.append(ocr_text)
        
        final_text = "\n".join(result_parts).strip()
        
        if not final_text:
            return {"text": "(No clear text detected. Image quality may be too low or text is too small/blurry)"}
        
        return {"text": final_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "version": "6.0.0", "engine": "Multi-Method OCR"}
