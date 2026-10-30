from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class WordItem(BaseModel):
    word: str
    start: float
    end: float
    telugu_word: Optional[str] = None
    tenglish_word: Optional[str] = None

class SubtitleSegmentModel(BaseModel):
    id: int
    start: float
    end: float
    text: str
    telugu_text: Optional[str] = None
    tenglish_text: Optional[str] = None
    english_text: Optional[str] = None
    words: Optional[List[WordItem]] = Field(default_factory=list)

class UpdateSegmentsRequest(BaseModel):
    segments: List[SubtitleSegmentModel]

class SwitchModeRequest(BaseModel):
    mode: str = Field(..., description="tenglish, telugu, or english")

class CaptionStyleModel(BaseModel):
    font_name: Optional[str] = "Arial"
    font_size: Optional[int] = 24
    primary_color: Optional[str] = "#FFFFFF"
    highlight_color: Optional[str] = "#A855F7"
    outline_color: Optional[str] = "#000000"
    background_color: Optional[str] = "#000000"
    background_alpha: Optional[int] = 128
    outline_width: Optional[float] = 2.0
    shadow_offset: Optional[float] = 1.0
    position: Optional[str] = "bottom"
    box_background: Optional[bool] = False
    is_reels: Optional[bool] = False
    preset: Optional[str] = "reels_highlight"
    word_zoom: Optional[float] = 1.25
    uppercase: Optional[bool] = False

class BurnVideoRequest(BaseModel):
    style: Optional[CaptionStyleModel] = None
    segments: Optional[List[SubtitleSegmentModel]] = None
