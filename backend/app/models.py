from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ImageCandidate(BaseModel):
    url: str
    thumbnail_url: Optional[str] = None
    width: int = 0
    height: int = 0
    file_size: int = 0
    photographer: str = ""
    score: float = 0.0

class ContentPoint(BaseModel):
    point: str
    explanation: str

class ImageSelection(BaseModel):
    query: str = ""
    candidates: List[ImageCandidate] = Field(default_factory=list)
    selected_url: Optional[str] = None
class SlideContent(BaseModel):
    label: str = "Slide"
    notes: str = ""
    objective: str = ""
    points: List[ContentPoint] = Field(default_factory=list)
    stats: List[Dict[str, str]] = Field(default_factory=list)
    chart: Optional[Dict] = None
    timeline: List[Dict[str, str]] = Field(default_factory=list)
    layout_hint: str = "content"
    image_query: str = ""
    image_selection: Optional[ImageSelection] = None

class ConfirmOutlineRequest(BaseModel):

    title: str

    subtitle: str = ""

    presenters: List[str] = Field(
        default_factory=list
    )

    date: Optional[str] = None

    tone: str = "professional"

    palette: Dict[str, str] = Field(
        default_factory=dict
    )

    slides: List[SlideContent] = Field(
        default_factory=list
    )


class OutlineResponse(BaseModel):
    """Returned by /api/outline — user reviews and confirms this."""

    title: str = "Presentation"

    subtitle: str = ""

    presenters: List[str] = Field(default_factory=list)

    date: Optional[str] = None

    palette: Dict[str, str] = Field(default_factory=dict)

    slides: List[SlideContent] = Field(default_factory=list)


class GenerateOutlineRequest(BaseModel):
    prompt: str

    num_slides: int = 8

    tone: str = "professional"


class ConfirmOutlineRequest(BaseModel):
    title: str

    subtitle: str = ""

    presenters: List[str] = Field(default_factory=list)

    date: Optional[str] = None

    tone: str = "professional"

    palette: Dict[str, str] = Field(default_factory=dict)

    slides: List[SlideContent]

class Slide(BaseModel):
    """Full slide after HTML generation."""
    label: str = "Slide"
    notes: str = ""
    content: Optional[str] = None
    layout_hint: Optional[str] = None
    html: str = ""


class Presentation(BaseModel):
    title: str = "Presentation"
    subtitle: str = ""
    palette: Optional[Dict[str, str]] = None
    slides: List[Slide] = Field(default_factory=list)


class RegenerateSlideRequest(BaseModel):
    title: str
    subtitle: str = ""
    current_html: str
    instruction: str = "Improve the visual design while keeping the same content."
    tone: str = "professional"
    palette: Optional[Dict[str, str]] = None


class ExportRequest(BaseModel):
    presentation: Presentation
    format: str = "pptx"  # pptx | html
