import json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BIN = ROOT / "cpp" / "build" / "hello_vitals"

input_data = {
    "session_id": "abc123",
    "video_path": "/mnt/c/data/video.mp4",
    "settings": {
        "fps": 30,
        "window": 10
    }
}

DATA.mkdir(exist_ok=True)

with open(DATA / "input.json", "w") as f:
    json.dump(input_data, f)

result = subprocess.run(
    [str(BIN), str(DATA / "input.json"), str(DATA / "output.json")],
    check=True,
    capture_output=True,
    text=True
)
print("C++ stdout:", result.stdout)
