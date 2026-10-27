import time
import requests
from pathlib import Path
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"

def test_full_api_workflow():
    print("=" * 65)
    print("🚀 Testing Full API Integration Workflow via HTTP")
    print("=" * 65)

    # 1. Health check
    res = requests.get(f"{BASE_URL}/api/health")
    print(f"1️⃣ API Health: {res.status_code} -> {res.json()}")
    assert res.status_code == 200

    # 2. Upload video
    video_path = Path("samples/sample_telugu_video.mp4")
    assert video_path.exists(), "Sample video missing!"

    print(f"2️⃣ Uploading {video_path} to /api/upload...")
    with open(video_path, "rb") as f:
        files = {"file": ("sample_telugu_video.mp4", f, "video/mp4")}
        data = {"whisper_model": "base", "language": "te"}
        up_res = requests.post(f"{BASE_URL}/api/upload", files=files, data=data)

    print(f"   Upload response: {up_res.status_code} -> {up_res.json()}")
    assert up_res.status_code == 200
    job_id = up_res.json()["job_id"]

    # 3. Poll status until completed
    print(f"3️⃣ Polling job status for {job_id}...")
    start_time = time.time()
    while True:
        st_res = requests.get(f"{BASE_URL}/api/status/{job_id}")
        st_data = st_res.json()
        status = st_data["status"]
        progress = st_data["progress"]
        msg = st_data["stage_message"]
        print(f"   [{time.time()-start_time:.1f}s] Status: {status} ({progress}%) - {msg}")

        if status == "COMPLETED":
            break
        elif status == "FAILED":
            raise RuntimeError(f"Job failed: {st_data.get('error_message')}")
        time.sleep(2)

    # 4. Fetch full job details
    print(f"4️⃣ Fetching Job Details for {job_id}...")
    job_res = requests.get(f"{BASE_URL}/api/job/{job_id}")
    job_data = job_res.json()
    segments = job_data["segments"]
    print(f"   Segments count: {len(segments)}")
    for s in segments:
        print(f"   - [{s['start']}s - {s['end']}s] {s['text']}")
        if s.get("telugu_text"):
            print(f"     Telugu: {s['telugu_text']}")

    # 5. Test Mode Switching
    print("5️⃣ Testing Mode Switching (Telugu -> English -> Tenglish)...")
    mode_res = requests.post(f"{BASE_URL}/api/job/{job_id}/switch-mode", json={"mode": "telugu"})
    print(f"   Telugu mode text: {mode_res.json()['segments'][0]['text']}")
    mode_res2 = requests.post(f"{BASE_URL}/api/job/{job_id}/switch-mode", json={"mode": "tenglish"})
    print(f"   Tenglish mode text: {mode_res2.json()['segments'][0]['text']}")

    # 6. Test SRT & VTT Export
    print("6️⃣ Testing SRT and VTT Exports...")
    srt_res = requests.get(f"{BASE_URL}/api/export/{job_id}/srt")
    print(f"   SRT export: {srt_res.status_code}, Length: {len(srt_res.text)} chars")
    assert srt_res.status_code == 200
    assert "-->" in srt_res.text

    vtt_res = requests.get(f"{BASE_URL}/api/export/{job_id}/vtt")
    print(f"   VTT export: {vtt_res.status_code}, Length: {len(vtt_res.text)} chars")
    assert vtt_res.status_code == 200
    assert "WEBVTT" in vtt_res.text

    # 7. Test Video Burning with Reels Karaoke Highlight
    print("7️⃣ Testing FFmpeg Video Burning with Reels Highlight...")
    burn_payload = {
        "style": {
            "preset": "reels_highlight",
            "font_name": "Arial",
            "font_size": 28,
            "primary_color": "#FFFFFF",
            "highlight_color": "#A855F7",
            "outline_color": "#000000",
            "outline_width": 2.5,
            "is_reels": True,
            "position": "bottom"
        },
        "segments": segments
    }
    burn_res = requests.post(f"{BASE_URL}/api/export/{job_id}/burn-video", json=burn_payload)
    print(f"   Burn trigger: {burn_res.status_code} -> {burn_res.json()}")
    assert burn_res.status_code == 200

    # Poll burning status
    print("   Polling burning status...")
    while True:
        b_res = requests.get(f"{BASE_URL}/api/export/{job_id}/burn-status")
        b_data = b_res.json()
        b_status = b_data["burn_status"]
        print(f"   Burn Status: {b_status} (Ready: {b_data['is_ready']})")
        if b_data["is_ready"]:
            print(f"   Download URL: {b_data['download_url']}")
            break
        elif b_status == "FAILED":
            raise RuntimeError("Burn failed!")
        time.sleep(2)

    # 8. Test Downloading Burned Video
    print("8️⃣ Verifying Download of Burned Video...")
    dl_res = requests.get(f"{BASE_URL}/api/export/{job_id}/download-burned", stream=True)
    print(f"   Download response: {dl_res.status_code}, Content-Type: {dl_res.headers.get('content-type')}")
    assert dl_res.status_code == 200
    content_len = len(dl_res.content)
    print(f"   Downloaded video size: {content_len} bytes")
    assert content_len > 10000

    print("=" * 65)
    print("🎉 ALL API & PIPELINE WORKFLOW TESTS PASSED PERFECTLY!")
    print("=" * 65)

if __name__ == "__main__":
    test_full_api_workflow()
