from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class QuizQuestion:
    topic: str
    prompt: str
    options: List[str]
    answer_index: int
    explanation: str


PHOTOSHOP_QUESTIONS: List[QuizQuestion] = []
ILLUSTRATOR_QUESTIONS: List[QuizQuestion] = []


_photoshop_templates = [
    (
        "Which tool is best for selecting objects with similar color ranges?",
        ["Magic Wand Tool", "Pen Tool", "Crop Tool", "Hand Tool"],
        0,
        "Magic Wand selects neighboring pixels based on color similarity.",
    ),
    (
        "What does Ctrl/Cmd + J do in Photoshop?",
        ["Merge layers", "Duplicate selected layer", "Create clipping mask", "Save for web"],
        1,
        "Ctrl/Cmd + J duplicates the selected layer or selection into a new layer.",
    ),
    (
        "Which panel is used to adjust hue, saturation, and lightness non-destructively?",
        ["Actions panel", "Adjustments panel", "Navigator panel", "Swatches panel"],
        1,
        "Adjustment layers are managed from the Adjustments panel.",
    ),
    (
        "What is the purpose of Smart Objects?",
        ["Reduce image size", "Apply destructive edits", "Preserve source content for non-destructive edits", "Auto color balance"],
        2,
        "Smart Objects keep original data safe while transforming or filtering.",
    ),
    (
        "Which blend mode is commonly used to remove black backgrounds?",
        ["Screen", "Multiply", "Difference", "Hue"],
        0,
        "Screen brightens and effectively removes black areas.",
    ),
    (
        "Which file format keeps Photoshop layers editable?",
        ["JPG", "PNG", "PSD", "GIF"],
        2,
        "PSD preserves Photoshop-specific data including layers and masks.",
    ),
    (
        "What does the Clone Stamp tool do?",
        ["Moves layers", "Copies pixels from one area to another", "Creates vector paths", "Adds gradients"],
        1,
        "Clone Stamp samples pixels and paints them elsewhere.",
    ),
    (
        "Which feature helps remove blemishes quickly by matching texture and tone?",
        ["Healing Brush", "Lasso Tool", "Direct Selection", "Custom Shape"],
        0,
        "Healing Brush blends sampled texture with destination lighting and color.",
    ),
    (
        "What does a layer mask primarily control?",
        ["Image resolution", "Layer visibility", "Color profile", "Canvas size"],
        1,
        "Masks reveal or hide parts of a layer non-destructively.",
    ),
    (
        "Which color mode is best for print design?",
        ["RGB", "CMYK", "Indexed", "Lab"],
        1,
        "CMYK is used for four-color printing.",
    ),
]

_illustrator_templates = [
    (
        "Which Illustrator tool is primarily used to create precise vector paths?",
        ["Pen Tool", "Blob Brush", "Eraser", "Shaper"],
        0,
        "Pen Tool creates anchor points and Bézier curves with precision.",
    ),
    (
        "What does Ctrl/Cmd + G do in Illustrator?",
        ["Ungroup", "Group selected objects", "Create gradient", "Expand appearance"],
        1,
        "Ctrl/Cmd + G groups selected objects.",
    ),
    (
        "Which panel controls alignment of selected objects?",
        ["Symbols panel", "Align panel", "Links panel", "Info panel"],
        1,
        "Use Align panel for distribute and alignment operations.",
    ),
    (
        "What is the purpose of the Pathfinder panel?",
        ["Rasterize objects", "Combine and cut vector shapes", "Color correction", "Export assets"],
        1,
        "Pathfinder performs boolean shape operations.",
    ),
    (
        "Which file type is native to Adobe Illustrator?",
        ["SVG", "AI", "EPS", "PDF"],
        1,
        "AI is the default editable Illustrator format.",
    ),
    (
        "What does 'Expand' do in Illustrator?",
        ["Zoom in canvas", "Converts effects/strokes into editable vector shapes", "Increase artboard size", "Merge layers"],
        1,
        "Expand turns appearances into concrete vector paths.",
    ),
    (
        "Which tool allows you to edit individual anchor points and handles?",
        ["Selection Tool", "Direct Selection Tool", "Rotate Tool", "Eyedropper"],
        1,
        "Direct Selection edits anchor points and path segments.",
    ),
    (
        "What does the Artboard tool control?",
        ["Brush pressure", "Document pages/work areas", "Stroke profile", "Layer effects"],
        1,
        "Artboards define multiple design surfaces in one document.",
    ),
    (
        "Which option keeps vector quality when scaling?",
        ["Rasterize", "Create outlines", "Use vector paths", "Flatten transparency"],
        2,
        "Vector paths are resolution-independent.",
    ),
    (
        "Which color mode is recommended before sending artwork to print?",
        ["RGB", "CMYK", "HSB", "Grayscale"],
        1,
        "CMYK matches print process colors.",
    ),
]

for i in range(50):
    t = _photoshop_templates[i % len(_photoshop_templates)]
    PHOTOSHOP_QUESTIONS.append(
        QuizQuestion(
            topic="Photoshop",
            prompt=f"[PS-{i + 1}] {t[0]}",
            options=t[1],
            answer_index=t[2],
            explanation=t[3],
        )
    )

for i in range(50):
    t = _illustrator_templates[i % len(_illustrator_templates)]
    ILLUSTRATOR_QUESTIONS.append(
        QuizQuestion(
            topic="Illustrator",
            prompt=f"[AI-{i + 1}] {t[0]}",
            options=t[1],
            answer_index=t[2],
            explanation=t[3],
        )
    )

ALL_QUESTIONS: List[QuizQuestion] = PHOTOSHOP_QUESTIONS + ILLUSTRATOR_QUESTIONS