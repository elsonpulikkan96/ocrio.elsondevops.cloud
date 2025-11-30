from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import io
from pyzbar import pyzbar
import numpy as np
import cv2
import re

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_INDEX = BASE_DIR / "frontend" / "index.html"
STATIC_DIR = BASE_DIR / "app" / "static"

app = FastAPI(title="OCR IO", version="8.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


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


def preprocess_image(img, method='adaptive'):
    """Advanced preprocessing with error handling"""
    try:
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        if method == 'otsu':
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
        
        elif method == 'adaptive':
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            return binary
        
        elif method == 'clahe':
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            return cleaned
        
        elif method == 'sharpen':
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(gray, -1, kernel)
            _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
        
        return gray
    except Exception as e:
        return gray if 'gray' in locals() else img


def clean_ocr_text(text):
    """Enhanced text cleaning and formatting"""
    if not text:
        return ""
    
    # Remove excessive spaces
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Fix common OCR errors
    text = text.replace('|', 'I')  # Common pipe/I confusion
    text = text.replace('0', 'O') if text.isupper() else text  # 0/O in uppercase
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
    
    lines = text.split('\n')
    cleaned = []
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 2:
            continue
        
        # Remove lines with too many special characters
        special_count = sum(not c.isalnum() and not c.isspace() for c in line)
        if len(line) > 0 and (special_count / len(line)) > 0.5:
            continue
        
        # Keep lines with reasonable alphanumeric content
        alnum = sum(c.isalnum() or c.isspace() for c in line)
        if len(line) > 0 and (alnum / len(line)) >= 0.4:
            cleaned.append(line)
    
    result = '\n'.join(cleaned)
    
    # Fix spacing around punctuation
    result = re.sub(r'\s+([.,!?;:])', r'\1', result)
    result = re.sub(r'([.,!?;:])\s*([a-zA-Z])', r'\1 \2', result)
    
    return result


def extract_text_advanced(image):
    """Enhanced OCR with better preprocessing"""
    try:
        img = np.array(image)
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        
        # Aggressive upscaling for better quality
        h, w = img.shape[:2]
        if w < 1500 or h < 1500:
            scale = min(1500 / w, 1500 / h)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Enhance contrast with CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Adaptive thresholding
        binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # Run Tesseract with best config
        custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
        text = pytesseract.image_to_string(cleaned, config=custom_config)
        
        return clean_ocr_text(text)
    except Exception as e:
        return f"Processing error: {str(e)[:50]}"


@app.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...)):
    """Enhanced OCR with robust error handling"""
    try:
        # Validate file
        if not file.filename:
            return {"text": "(No file provided)"}
        
        # Check file extension
        ext = file.filename.lower().split('.')[-1]
        if ext not in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp']:
            return {"text": f"(Unsupported format: {ext}. Use JPG, PNG, BMP, TIFF, or WEBP)"}
        
        raw = await file.read()
        if not raw or len(raw) < 100:
            return {"text": "(File is empty or too small)"}
        
        # Size check
        if len(raw) > 10 * 1024 * 1024:
            return {"text": "(File too large. Max 10MB)"}
        
        # Load image
        try:
            image = Image.open(io.BytesIO(raw))
        except Exception as e:
            return {"text": f"(Cannot open image: {str(e)[:50]})"}
        
        # Fix orientation
        image = ImageOps.exif_transpose(image)
        
        # Convert to RGB
        if image.mode not in ['RGB', 'L']:
            try:
                image = image.convert('RGB')
            except:
                return {"text": "(Cannot convert image format)"}
        
        # Detect QR/Barcodes
        qr_data = detect_qr_barcodes(image)
        
        # Extract text
        ocr_text = extract_text_advanced(image)
        
        # Build output
        output = []
        if qr_data:
            output.append("=== QR CODES / BARCODES ===")
            output.extend(qr_data)
            output.append("")
        
        if ocr_text and not ocr_text.startswith("Processing error"):
            if qr_data:
                output.append("=== EXTRACTED TEXT ===")
            output.append(ocr_text)
        elif ocr_text.startswith("Processing error"):
            output.append(ocr_text)
        
        final = "\n".join(output).strip()
        
        if not final:
            return {"text": "(No readable text detected. Try:\n• Higher resolution image\n• Better lighting\n• Clearer text\n• Different angle)"}
        
        return {"text": final}
        
    except Exception as e:
        return {"text": f"(Error: {str(e)[:100]}. Please try a different image)"}



@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "8.0.0",
        "engine": "Advanced OCR v8",
        "features": ["Multi-method processing", "Auto-deskew", "Smart upscaling", "Enhanced error handling"]
    }
