import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Response, Body
from fastapi.responses import FileResponse, StreamingResponse
from app.config import (
    UPLOADS_DIR, EXPORTS_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES,
    DEFAULT_WHISPER_MODEL, GEMINI_API_KEY
)
from app.jobs.job_manager import job_manager
from app.speech.audio_extractor import extract_audio
from app.speech.whisper_engine import transcribe_audio
from app.speech.gemini_engine import transcribe_with_gemini
from app.transliteration.tenglish_engine import convert_segments
from app.video.ffmpeg_subtitles import (
    generate_srt_content, generate_vtt_content, burn_subtitles_to_video
)
from app.api.schemas import (
    UpdateSegmentsRequest, SwitchModeRequest, BurnVideoRequest
)

router = APIRouter(prefix="/api")

@router.get("/config")
async def get_app_config():
    """Returns app configuration including default Gemini settings."""
    return {
        "has_gemini_key": bool(GEMINI_API_KEY and GEMINI_API_KEY.strip())
    }

def process_transcription_pipeline(job_id: str, model_name: str, language: str, gemini_api_key: Optional[str] = None):
    """Background task to extract audio, run transcription (Gemini or Whisper), and transliterate."""
    job = job_manager.get_job(job_id)
    if not job:
        return

    try:
        # Stage 1: Extract Audio
        job_manager.update_job(job_id, {
            "status": "EXTRACTING_AUDIO",
            "stage_message": "Extracting audio from video...",
            "progress": 20
        })
        video_path = job["video_path"]
        audio_path = str(Path(video_path).with_suffix(".wav"))
        extract_audio(video_path, audio_path)

        active_key = (gemini_api_key or GEMINI_API_KEY or "").strip()
        tenglish_segments = []

        if active_key:
            # Stage 2: High-accuracy Google Gemini Multimodal Speech Transcription
            job_manager.update_job(job_id, {
                "audio_path": audio_path,
                "status": "TRANSCRIBING",
                "stage_message": "Transcribing speech using Google Gemini AI (99% Native Telugu/Tenglish Accuracy)...",
                "progress": 60
            })
            try:
                result = transcribe_with_gemini(audio_path, api_key=active_key)
                tenglish_segments = result.get("segments", [])
            except Exception as e:
                print(f"Notice: Gemini transcription encountered: {e}. Falling back to local Whisper...")
                job_manager.update_job(job_id, {
                    "stage_message": "Gemini unavailable. Falling back to local Whisper AI...",
                    "progress": 50
                })
                result = transcribe_audio(
                    audio_path=audio_path,
                    model_name=model_name or "base",
                    language=language or "te",
                    include_word_timestamps=True,
                    generate_translation=False
                )
                segments = result.get("segments", [])
                job_manager.update_job(job_id, {
                    "status": "CONVERTING_TENGLISH",
                    "stage_message": "Converting Telugu script to natural Tenglish...",
                    "progress": 85
                })
                tenglish_segments = convert_segments(segments, mode="tenglish")
        else:
            # Stage 2: Local Whisper Speech Recognition
            job_manager.update_job(job_id, {
                "audio_path": audio_path,
                "status": "TRANSCRIBING",
                "stage_message": "Transcribing speech using local Whisper AI...",
                "progress": 50
            })

            result = transcribe_audio(
                audio_path=audio_path,
                model_name=model_name,
                language=language,
                include_word_timestamps=True,
                generate_translation=False
            )

            segments = result.get("segments", [])

            # Stage 3: Conversion to Tenglish
            job_manager.update_job(job_id, {
                "status": "CONVERTING_TENGLISH",
                "stage_message": "Converting Telugu script to natural Tenglish...",
                "progress": 85
            })

            tenglish_segments = convert_segments(segments, mode="tenglish")

        # Stage 4: Completed
        job_manager.update_job(job_id, {
            "status": "COMPLETED",
            "stage_message": "Processing complete! Captions ready for preview.",
            "progress": 100,
            "segments": tenglish_segments,
            "caption_mode": "tenglish"
        })

    except Exception as e:
        print(f"Error in transcription pipeline for job {job_id}: {e}")
        job_manager.update_job(job_id, {
            "status": "FAILED",
            "stage_message": f"Processing failed: {str(e)}",
            "error_message": str(e),
            "progress": 0
        })

def process_video_burn_pipeline(job_id: str, style_dict: dict, segments: list):
    """Background task for burning styled subtitles into the video."""
    job = job_manager.get_job(job_id)
    if not job:
        return

    try:
        job_manager.update_job(job_id, {
            "burn_status": "BURNING",
            "burn_progress": 30
        })

        video_path = job["video_path"]
        job_folder = Path(video_path).parent
        output_name = f"captioned_{Path(video_path).stem}.mp4"
        output_path = str(job_folder / output_name)

        burn_subtitles_to_video(
            video_path=video_path,
            output_video_path=output_path,
            segments=segments,
            style=style_dict,
            timeout=400
        )

        job_manager.update_job(job_id, {
            "burn_status": "COMPLETED",
            "burn_progress": 100,
            "burned_video_path": output_path
        })

    except Exception as e:
        print(f"Error burning video for job {job_id}: {e}")
        job_manager.update_job(job_id, {
            "burn_status": "FAILED",
            "burn_progress": 0,
            "error_message": f"Subtitle burning failed: {str(e)}"
        })


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    whisper_model: str = Form(DEFAULT_WHISPER_MODEL),
    language: str = Form("te"),
    gemini_api_key: Optional[str] = Form(None)
):
    """Handles video upload and kicks off transcription job."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Create job
    job_id = job_manager.create_job(file.filename, ext)
    job = job_manager.get_job(job_id)
    video_path = job["video_path"]

    # Save uploaded file safely
    try:
        size = 0
        with open(video_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE_BYTES:
                    # Clean up
                    buffer.close()
                    os.remove(video_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")

    # Launch background processing
    background_tasks.add_task(process_transcription_pipeline, job_id, whisper_model, language, gemini_api_key)

    return {
        "job_id": job_id,
        "filename": file.filename,
        "status": "QUEUED",
        "message": "Video uploaded successfully. Transcription started."
    }


@router.post("/job/{job_id}/retranscribe-gemini")
async def retranscribe_existing_job(job_id: str, payload: Optional[Dict[str, Any]] = Body(default={})):
    """Re-transcribes an existing uploaded job using Google Gemini AI."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    payload = payload or {}
    api_key = payload.get("gemini_api_key") or GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is required.")

    video_path = job.get("video_path")
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Original video file not found.")

    audio_path = job.get("audio_path")
    if not audio_path or not os.path.exists(audio_path):
        audio_path = str(Path(video_path).with_suffix(".wav"))
        extract_audio(video_path, audio_path)
        job_manager.update_job(job_id, {"audio_path": audio_path})

    try:
        result = transcribe_with_gemini(audio_path, api_key=api_key)
        segments = result.get("segments", [])
        job_manager.update_job(job_id, {
            "status": "COMPLETED",
            "segments": segments,
            "caption_mode": "tenglish"
        })
        return {
            "status": "SUCCESS",
            "message": "Captions generated successfully with Gemini AI!",
            "segments": segments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini transcription failed: {str(e)}")


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Returns current status and progress of the job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "stage_message": job["stage_message"],
        "progress": job["progress"],
        "error_message": job.get("error_message"),
        "segments_count": len(job.get("segments", [])),
        "caption_mode": job.get("caption_mode", "tenglish")
    }


@router.get("/job/{job_id}")
async def get_job_details(job_id: str):
    """Returns full job details including segments, media URL, and styles."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Return safe metadata without sensitive server paths
    return {
        "job_id": job["job_id"],
        "filename": job["original_filename"],
        "status": job["status"],
        "progress": job["progress"],
        "stage_message": job["stage_message"],
        "segments": job.get("segments", []),
        "caption_mode": job.get("caption_mode", "tenglish"),
        "style": job.get("style", {}),
        "burn_status": job.get("burn_status", "IDLE"),
        "burn_progress": job.get("burn_progress", 0),
        "has_burned_video": bool(job.get("burned_video_path") and os.path.exists(job["burned_video_path"]))
    }


@router.api_route("/job/{job_id}/video", methods=["GET", "HEAD"])
async def get_job_video(job_id: str):
    """Serves the uploaded source video with range support for seeking."""
    job = job_manager.get_job(job_id)
    if not job or not os.path.exists(job["video_path"]):
        raise HTTPException(status_code=404, detail="Video file not found.")

    ext = Path(job["video_path"]).suffix.lower()
    media_type = f"video/{ext.lstrip('.')}"
    if ext == ".mov":
        media_type = "video/quicktime"

    return FileResponse(job["video_path"], media_type=media_type)


@router.post("/job/{job_id}/segments")
async def save_segments(job_id: str, payload: UpdateSegmentsRequest):
    """Updates segments after user edits start/end timestamps or text."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Convert Pydantic models to dicts
    segments_data = [seg.model_dump() for seg in payload.segments]
    job_manager.update_segments(job_id, segments_data)

    return {"message": "Segments updated successfully.", "count": len(segments_data)}


@router.post("/job/{job_id}/switch-mode")
async def switch_mode(job_id: str, payload: SwitchModeRequest):
    """Switches caption display mode between Tenglish, Telugu script, and English."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    mode = payload.mode.lower()
    if mode not in ["tenglish", "telugu", "english"]:
        raise HTTPException(status_code=400, detail="Mode must be 'tenglish', 'telugu', or 'english'.")

    segments = job.get("segments", [])
    updated_segments = convert_segments(segments, mode=mode)

    job_manager.update_job(job_id, {
        "caption_mode": mode,
        "segments": updated_segments
    })

    return {
        "mode": mode,
        "segments": updated_segments
    }


@router.get("/export/{job_id}/srt")
async def export_srt(job_id: str):
    """Generates and downloads standard SRT subtitle file."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    segments = job.get("segments", [])
    srt_content = generate_srt_content(segments)

    filename = f"{Path(job['original_filename']).stem}_{job.get('caption_mode', 'tenglish')}.srt"
    return Response(
        content=srt_content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export/{job_id}/vtt")
async def export_vtt(job_id: str):
    """Generates and downloads WebVTT subtitle file."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    segments = job.get("segments", [])
    vtt_content = generate_vtt_content(segments)

    filename = f"{Path(job['original_filename']).stem}_{job.get('caption_mode', 'tenglish')}.vtt"
    return Response(
        content=vtt_content,
        media_type="text/vtt; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/export/{job_id}/burn-video")
async def start_burn_video(
    job_id: str,
    payload: BurnVideoRequest,
    background_tasks: BackgroundTasks
):
    """Triggers burning custom styled captions directly into the video."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Save segments if provided in request
    if payload.segments is not None:
        segments_data = [seg.model_dump() for seg in payload.segments]
        job_manager.update_segments(job_id, segments_data)
        segments = segments_data
    else:
        segments = job.get("segments", [])

    if not segments:
        raise HTTPException(status_code=400, detail="Cannot burn video with empty segments.")

    # Update style if provided
    style_dict = job.get("style", {})
    if payload.style is not None:
        style_dict.update(payload.style.model_dump(exclude_unset=True))
        job_manager.update_job(job_id, {"style": style_dict})

    # Start background burning process
    job_manager.update_job(job_id, {
        "burn_status": "BURNING",
        "burn_progress": 15
    })
    background_tasks.add_task(process_video_burn_pipeline, job_id, style_dict, segments)

    return {"message": "Subtitle burning started.", "job_id": job_id}


@router.get("/export/{job_id}/burn-status")
async def get_burn_status(job_id: str):
    """Checks progress of video burning."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    has_video = bool(job.get("burned_video_path") and os.path.exists(job["burned_video_path"]))
    return {
        "burn_status": job.get("burn_status", "IDLE"),
        "burn_progress": job.get("burn_progress", 0),
        "is_ready": has_video,
        "download_url": f"/api/export/{job_id}/download-burned" if has_video else None
    }


@router.api_route("/export/{job_id}/download-burned", methods=["GET", "HEAD"])
async def download_burned_video(job_id: str):
    """Serves the rendered captioned video for download."""
    job = job_manager.get_job(job_id)
    if not job or not job.get("burned_video_path") or not os.path.exists(job["burned_video_path"]):
        raise HTTPException(status_code=404, detail="Burned video is not ready or not found.")

    filename = f"captioned_{Path(job['original_filename']).stem}.mp4"
    return FileResponse(
        job["burned_video_path"],
        media_type="video/mp4",
        filename=filename
    )
