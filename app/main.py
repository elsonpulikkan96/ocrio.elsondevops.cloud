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

app = FastAPI(title="OCR IO", version="7.0.0")

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
    """Enhanced preprocessing methods"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
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
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        return cleaned
    
    elif method == 'sharpen':
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    return gray


def clean_ocr_text(text):
    """Clean and format OCR output"""
    if not text:
        return ""
    
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    lines = text.split('\n')
    cleaned = []
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 2:
            continue
        
        # More lenient: accept if >25% alphanumeric (was 40%)
        alnum = sum(c.isalnum() or c.isspace() for c in line)
        if len(line) > 0 and (alnum / len(line)) < 0.25:
            continue
        
        cleaned.append(line)
    
    return '\n'.join(cleaned)


def extract_text_advanced(image):
    """Optimized single-method OCR extraction"""
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    # Moderate upscaling
    h, w = img.shape[:2]
    if w < 800 or h < 800:
        scale = min(800 / w, 800 / h)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Single optimized method
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        text = pytesseract.image_to_string(binary, config='--oem 3 --psm 3')
        return clean_ocr_text(text)
    except:
        return ""


@app.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...)):
    """Enhanced OCR processing"""
    try:
        raw = await file.read()
        if not raw:
            return {"text": "(Empty file uploaded)"}
        
        image = Image.open(io.BytesIO(raw))
        image = ImageOps.exif_transpose(image)
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        qr_data = detect_qr_barcodes(image)
        ocr_text = extract_text_advanced(image)
        
        output = []
        if qr_data:
            output.append("=== QR CODES / BARCODES ===")
            output.extend(qr_data)
            output.append("")
        
        if ocr_text:
            if qr_data:
                output.append("=== EXTRACTED TEXT ===")
            output.append(ocr_text)
        
        final = "\n".join(output).strip()
        return {"text": final if final else "(No readable text detected. Try a clearer image)"}
        
    except Exception as e:
        return {"text": f"(Error: {str(e)[:100]})"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "7.0.0", "engine": "Advanced OCR"}
