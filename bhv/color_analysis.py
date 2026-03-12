"""
BHV Fuzzy Color-Emotion Analysis Module
========================================
Inspired by: "Color-Emotion Associations in Art: Fuzzy Approach"

Workflow:
  1. Extract dominant RGB palette from an image using K-means clustering (via Pillow).
  2. Map each dominant color to a set of emotional dimensions using fuzzy membership
     functions — each color contributes a degree (0.0–1.0) to each emotion.
  3. Aggregate across all dominant colors to produce a final per-image emotion vector.

Fuzzy model:
  - Hue angle (HSV) is the primary discriminant.
  - Saturation and Value modulate the membership strength.
  - Emotions covered: joy, sadness, anger, fear, disgust, surprise, trust, anticipation
    (Plutchik's wheel, widely used in art-emotion research).
"""

import io
import math
import colorsys
from typing import List, Dict, Optional

# ---------------------------------------------------------------------------
# Fuzzy membership functions
# ---------------------------------------------------------------------------

def _gaussian(x: float, mu: float, sigma: float) -> float:
    """Gaussian membership function."""
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def _trapezoidal(x: float, a: float, b: float, c: float, d: float) -> float:
    """Trapezoidal membership function (rises a→b, flat b→c, falls c→d)."""
    if x <= a or x >= d:
        return 0.0
    if a < x <= b:
        return (x - a) / (b - a)
    if b < x <= c:
        return 1.0
    # c < x < d
    return (d - x) / (d - c)


def _hue_emotion_memberships(hue_deg: float) -> Dict[str, float]:
    """
    Map a hue (0-360°) to fuzzy emotion memberships.

    Mapping rationale (literature-grounded):
      Red   0-30  / 330-360 → anger, anticipation
      Orange      15-60     → anticipation, joy
      Yellow      45-75     → joy, trust
      Green       90-165    → trust, disgust (dark greens)
      Cyan       165-210    → surprise, trust
      Blue       195-270    → sadness, fear
      Violet/Purple 255-315 → fear, sadness
      Magenta    300-345    → surprise, disgust
    Overlaps model fuzzy transitions.
    """
    h = hue_deg % 360

    # Joy: peaks at yellow-orange (55°)
    joy = max(
        _trapezoidal(h, 25, 45, 75, 95),
        _trapezoidal(h, 280, 300, 330, 350) * 0.3  # pink-joy
    )

    # Trust: green-cyan region (120–200°)
    trust = _trapezoidal(h, 90, 130, 175, 210)

    # Anticipation: orange-yellow (20–80°)
    anticipation = _trapezoidal(h, 10, 25, 65, 90)

    # Anger: red region (0–30°, 340–360°)
    anger = max(
        _trapezoidal(h, 0, 0, 20, 40),
        _trapezoidal(h, 330, 345, 360, 360)
    )

    # Disgust: yellow-green / dark green (75–130°)
    disgust = _trapezoidal(h, 60, 80, 120, 150) * 0.8

    # Surprise: cyan + magenta (165–200°, 300–350°)
    surprise = max(
        _trapezoidal(h, 155, 170, 200, 220),
        _trapezoidal(h, 295, 315, 345, 360)
    )

    # Sadness: blue (200–270°)
    sadness = _trapezoidal(h, 190, 210, 255, 275)

    # Fear: violet-purple (255–320°)
    fear = _trapezoidal(h, 245, 260, 300, 325)

    return {
        "joy": joy,
        "trust": trust,
        "anticipation": anticipation,
        "anger": anger,
        "disgust": disgust,
        "surprise": surprise,
        "sadness": sadness,
        "fear": fear,
    }


def _apply_sv_modulation(
    memberships: Dict[str, float], saturation: float, value: float
) -> Dict[str, float]:
    """
    Modulate emotion memberships using Saturation (S) and Value (V).

    - High saturation → amplifies vivid emotions (joy, anger, surprise)
    - Low saturation (grey/white/black) → dampens most emotions, boosts trust/fear
    - Low value (dark) → boosts fear/sadness, dampens joy
    - High value (bright) → boosts joy/anticipation, dampens fear/sadness
    """
    result = {}
    is_achromatic = saturation < 0.12  # White, Grey, Black
    
    for emotion, deg in memberships.items():
        mod = deg
        
        # Achromatic colors (White/Grey/Black) shouldn't carry intense "Hue" emotions
        if is_achromatic:
            if emotion == "trust":
                # White/Light Grey = High Trust (Peace), Black = Lower
                mod = 0.5 + (0.5 * value)
            elif emotion in ("joy", "anticipation"):
                # Very bright white feels joyful
                mod = 0.4 * value if value > 0.8 else 0.0
            elif emotion == "fear" and value < 0.3:
                # Pure black/dark grey feels like fear
                mod = 0.6 * (1.0 - value)
            else:
                mod = 0.0
        else:
            # Chromatic modulation
            if emotion in ("joy", "anticipation", "surprise"):
                mod = deg * (0.4 + 0.6 * saturation) * (0.5 + 0.5 * value)
            elif emotion in ("anger",):
                mod = deg * (0.5 + 0.5 * saturation)
            elif emotion in ("sadness", "fear"):
                mod = deg * (1.0 - 0.4 * value)  # darker -> stronger
            elif emotion in ("trust",):
                mod = deg * (0.5 + 0.5 * (1.0 - saturation))
            elif emotion in ("disgust",):
                mod = deg * saturation
        
        result[emotion] = min(1.0, mod)
    return result


# ---------------------------------------------------------------------------
# K-means colour extraction (pure Python / Pillow)
# ---------------------------------------------------------------------------

def _extract_palette(image_bytes: bytes, n_colors: int = 5, sample: int = 5000) -> List[tuple]:
    """
    Extract n_colors dominant RGB colours from image_bytes using Pillow's
    built-in quantize (faster than manual K-means for small palettes).
    Returns list of (R, G, B) tuples, each in 0-255 range.
    """
    try:
        from PIL import Image
    except ImportError:
        return []

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # Resize for speed
        img.thumbnail((200, 200))
        # quantize → palette
        quantized = img.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
        palette_raw = quantized.getpalette()  # flat list R,G,B,R,G,B,...
        colors = []
        for i in range(n_colors):
            r, g, b = palette_raw[i * 3], palette_raw[i * 3 + 1], palette_raw[i * 3 + 2]
            colors.append((r, g, b))
        return colors
    except Exception:
        return []


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_image_colors(image_bytes: bytes, n_colors: int = 5) -> Dict:
    """
    Full fuzzy color-emotion analysis pipeline.

    Parameters
    ----------
    image_bytes : bytes
        Raw image file content.
    n_colors : int
        Number of dominant colors to extract (default 5).

    Returns
    -------
    dict with keys:
        palette       : list of dicts {hex, r, g, b, hue, saturation, value}
        emotion_scores: dict mapping emotion → aggregate membership (0.0–1.0)
        dominant_emotion : str — the highest-scoring emotion
        error         : str | None
    """
    palette_rgb = _extract_palette(image_bytes, n_colors=n_colors)
    if not palette_rgb:
        return {
            "palette": [],
            "emotion_scores": {},
            "dominant_emotion": None,
            "error": "Could not extract palette — ensure Pillow is installed and file is a valid image."
        }

    palette_info = []
    emotion_accumulator: Dict[str, float] = {}

    for (r, g, b) in palette_rgb:
        # Convert to HSV
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        hue_deg = h * 360.0

        raw_memberships = _hue_emotion_memberships(hue_deg)
        modulated = _apply_sv_modulation(raw_memberships, s, v)

        palette_info.append({
            "hex": _rgb_to_hex(r, g, b),
            "r": r, "g": g, "b": b,
            "hue": round(hue_deg, 1),
            "saturation": round(s, 3),
            "value": round(v, 3),
            "emotions": {k: round(v2, 3) for k, v2 in modulated.items()},
        })

        for emotion, deg in modulated.items():
            emotion_accumulator[emotion] = emotion_accumulator.get(emotion, 0.0) + deg

    # Normalize by number of colors
    n = len(palette_rgb)
    emotion_scores = {e: round(v / n, 3) for e, v in emotion_accumulator.items()}
    dominant_emotion = max(emotion_scores, key=emotion_scores.get) if emotion_scores else None

    return {
        "palette": palette_info,
        "emotion_scores": emotion_scores,
        "dominant_emotion": dominant_emotion,
        "error": None,
    }


def emotion_score_to_label(score: float) -> str:
    """Convert a 0-1 membership score to a human-readable intensity label."""
    if score >= 0.7:
        return "Strong"
    elif score >= 0.4:
        return "Moderate"
    elif score >= 0.15:
        return "Mild"
    return "Trace"

