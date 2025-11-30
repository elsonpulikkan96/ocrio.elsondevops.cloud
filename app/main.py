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
    """Multi-method OCR with best result selection"""
    try:
        img = np.array(image)
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        
        # Smart upscaling
        h, w = img.shape[:2]
        if w < 1000 or h < 1000:
            scale = min(1000 / w, 1000 / h)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Deskew
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        coords = np.column_stack(np.where(gray > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) > 0.5:
                (h, w) = img.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        # Try multiple methods
        methods = [
            ('adaptive', '--oem 3 --psm 3'),
            ('clahe', '--oem 3 --psm 6'),
            ('otsu', '--oem 3 --psm 4'),
        ]
        
        results = []
        for method, config in methods:
            try:
                processed = preprocess_image(img, method)
                text = pytesseract.image_to_string(processed, config=config)
                cleaned = clean_ocr_text(text)
                if cleaned:
                    results.append((len(cleaned), cleaned))
            except:
                continue
        
        if results:
            results.sort(reverse=True)
            return results[0][1]
        
        return ""
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
