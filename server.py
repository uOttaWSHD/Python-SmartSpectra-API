"""
Vitals Server - FastAPI server for video upload and vitals extraction

Workflow:
1. Python code stores the video
2. Python code writes the video path to data/input.json
3. Python builds and executes C++ file through Docker
4. C++ Code reads input.json, processes video, writes output.json
5. Python reads output.json and returns vitals
"""

import os
import json
import subprocess
import shutil
import logging
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Vitals Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RECORDINGS_DIR = BASE_DIR / "recordings"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
RECORDINGS_DIR.mkdir(exist_ok=True)

# Docker image name
DOCKER_IMAGE = "vitals-processor"


class VitalsResult(BaseModel):
    pulse: list
    breathing: list
    timestamp: list
    video_path: str
    processed: bool
    error: Optional[str] = None


def check_docker_image() -> bool:
    """Check if Docker image exists"""
    result = subprocess.run(
        ["docker", "images", "-q", DOCKER_IMAGE],
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())


def build_docker_image() -> bool:
    """Build the Docker image if not exists"""
    if check_docker_image():
        print(f"Docker image '{DOCKER_IMAGE}' already exists")
        return True
    
    print(f"Building Docker image '{DOCKER_IMAGE}'...")
    result = subprocess.run(
        ["docker", "build", "-f", "Dockerfile.vitals", "-t", DOCKER_IMAGE, "."],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Docker build failed: {result.stderr}")
        return False
    
    print("Docker image built successfully")
    return True


def run_vitals_processor(video_path: str, headless: bool = True) -> dict:
    """
    Run the vitals processor by calling main.py as a subprocess
    
    1. Write input.json with video path
    2. Execute main.py
    3. Read output.json with results
    """
    try:
        api_key = os.getenv("SMARTSPECTRA_API_KEY", "")
        
        # Step 1: Write input.json with absolute path
        input_config = {
            "video_path": str(Path(video_path).absolute())
        }
        
        input_file = DATA_DIR / "input.json"
        with open(input_file, "w") as f:
            json.dump(input_config, f, indent=2)
        
        logger.info(f"Written input.json: {input_config}")
        
        # Step 2: Run main.py as subprocess
        cmd = ["python3", "main.py"]
        logger.info(f"Running command: {' '.join(cmd)} from {BASE_DIR}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(BASE_DIR)
        )
        
        logger.info(f"main.py return code: {result.returncode}")
        logger.info(f"main.py stdout:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"main.py stderr:\n{result.stderr}")
        
        # Step 3: Read output.json
        output_file = DATA_DIR / "output.json"
        
        if result.returncode != 0:
            logger.error(f"main.py failed with return code {result.returncode}")
            return {
                "pulse": [],
                "breathing": [],
                "timestamp": [],
                "error": f"Processing failed: {result.stderr}"
            }
        
        if not output_file.exists():
            logger.error(f"Output file not found at {output_file}")
            return {
                "pulse": [],
                "breathing": [],
                "timestamp": [],
                "error": f"No output file generated"
            }
        
        logger.info(f"Reading output from {output_file}")
        with open(output_file, "r") as f:
            output_data = json.load(f)
        
        logger.info(f"Successfully processed video, got {len(output_data.get('pulse', []))} pulse readings")
        return output_data
    except Exception as e:
        logger.error(f"Error in run_vitals_processor: {e}", exc_info=True)
        return {
            "pulse": [],
            "breathing": [],
            "timestamp": [],
            "error": str(e)
        }


@app.get("/")
async def root():
    """Health check"""
    main_file = BASE_DIR / "main.py"
    return {
        "status": "ok",
        "service": "Vitals Server",
        "main_py_ready": main_file.exists()
    }


@app.post("/api/build")
async def build_image():
    """Build the Docker image"""
    success = build_docker_image()
    if success:
        return {"status": "success", "message": "Docker image built"}
    else:
        raise HTTPException(status_code=500, detail="Failed to build Docker image")


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file and process it immediately
    Saves as vid.mp4 in the recordings directory and runs main.py
    Returns the output.json result
    """
    filename = "vid.mp4"
    filepath = RECORDINGS_DIR / filename
    
    logger.info(f"Uploading video to {filepath}")
    
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    logger.info(f"Saved video: {filepath} ({len(content)} bytes)")
    
    # Run main.py to process the video
    logger.info("Running main.py to process video...")
    result = run_vitals_processor(str(filepath), headless=True)
    
    # Delete the video after processing
    try:
        filepath.unlink()
        logger.info(f"Deleted video: {filepath}")
    except Exception as e:
        logger.warning(f"Failed to delete video: {e}")
    
    # Return the output.json content directly
    return result


@app.post("/api/process/{filename}")
async def process_video(filename: str, headless: bool = True):
    """
    Process a previously uploaded video to extract vitals
    """
    logger.info(f"Processing request for video: {filename}")
    
    video_path = RECORDINGS_DIR / filename
    
    if not video_path.exists():
        logger.error(f"Video not found: {video_path}")
        raise HTTPException(status_code=404, detail=f"Video not found: {filename}")
    
    logger.info(f"Video found at {video_path}")
    
    main_file = BASE_DIR / "main.py"
    if not main_file.exists():
        logger.error(f"main.py not found at {main_file}")
        raise HTTPException(
            status_code=503, 
            detail=f"main.py not found. Please ensure main.py exists."
        )
    
    try:
        logger.info(f"Starting vitals processing for {video_path}")
        result = run_vitals_processor(str(video_path), headless=headless)
        
        # Delete the video after processing
        try:
            video_path.unlink()
            logger.info(f"Deleted video: {video_path}")
        except Exception as e:
            logger.warning(f"Failed to delete video: {e}")
        
        return VitalsResult(
            pulse=result.get("pulse", []),
            breathing=result.get("breathing", []),
            timestamp=result.get("timestamp", []),
            video_path=str(video_path),
            processed=True,
            error=result.get("error")
        )
    except subprocess.TimeoutExpired:
        logger.error("Processing timeout")
        raise HTTPException(status_code=504, detail="Processing timeout")
    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-and-process")
async def upload_and_process(file: UploadFile = File(...), headless: bool = True):
    """
    Upload a video and immediately process it for vitals
    Combined endpoint for convenience
    """
    # Upload
    upload_result = await upload_video(file)
    
    # Process
    process_result = await process_video(upload_result["filename"], headless=headless)
    
    return process_result


@app.get("/api/recordings")
async def list_recordings():
    """List all recorded videos"""
    recordings = []
    for f in RECORDINGS_DIR.glob("*.mp4"):
        recordings.append({
            "filename": f.name,
            "size": f.stat().st_size,
            "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat()
        })
    return {"recordings": recordings}


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Vitals Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
