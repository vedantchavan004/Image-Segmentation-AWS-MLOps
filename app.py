import os
import sys
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ultralytics import YOLO
from PIL import Image

# ✅ Initialize FastAPI app
app = FastAPI()

# ✅ Load YOLO model (ensure the correct path)
MODEL_PATH = "yolo11s-seg.pt"
if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Model file '{MODEL_PATH}' not found!")
model = YOLO(MODEL_PATH)

# ✅ Ensure 'static' directory exists
os.makedirs("static", exist_ok=True)

# ✅ Serve static files (like images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ Setup Jinja2 templates for rendering HTML pages
templates = Jinja2Templates(directory="templates")

# ✅ Debugging: Show system details inside FastAPI
@app.get("/debug/")
async def debug():
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "numpy_version": np.__version__,
        "current_directory": os.getcwd(),
        "env_variables": dict(os.environ),
    }

# ✅ Serve index.html at root "/"
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ✅ Prediction endpoint
@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    try:
        # ✅ Log Python & NumPy details before processing
        print(f"Running on Python: {sys.executable}")
        print(f"Python Version: {sys.version}")
        print(f"NumPy Version: {np.__version__}")

        # ✅ Save uploaded image
        file_path = os.path.join("static", file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # ✅ Read image
        image = Image.open(file_path).convert("RGB")
        img_array = np.array(image)

        # ✅ Run YOLO inference
        results = model(img_array)

        # ✅ Save the result image
        result_filename = "result.jpg"
        result_path = os.path.join("static", result_filename)
        result_img = results[0].plot()
        cv2.imwrite(result_path, result_img)

        # ✅ Collect detections
        detections = []
        for result in results:
            for bbox, cls in zip(result.boxes.xyxy, result.boxes.cls):
                detections.append({
                    "class": result.names[int(cls)],
                    "bbox": bbox.tolist(),
                })

        return {"output_image": result_filename, "detections": detections}

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
