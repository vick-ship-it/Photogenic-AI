from typing import Dict, Tuple, Optional


def _format_segment(label: str, value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value_clean = value.strip()
    if not value_clean:
        return None
    return f"{label}: {value_clean}"


def build_prompt(fields: Dict[str, Optional[str]]) -> Tuple[str, str]:
    """
    Build a concise, photorealistic portrait prompt from user-selected categories.

    Returns (positive_prompt, negative_prompt).
    """
    parts = []

    # Core subject
    subject = "a highly photorealistic portrait"
    gender = (fields.get("gender") or "").strip()
    if gender:
        subject += f" of a {gender}"

    parts.append(subject)

    # Optional details
    for label in (
        "expression",
        "pose",
        "outfit",
        "lighting",
        "camera",
        "mood",
        "background",
    ):
        seg = _format_segment(label, fields.get(label))
        if seg:
            parts.append(seg)

    # Animal theme (kept subtle to remain portrait-forward)
    animal = (fields.get("animal") or "").strip()
    if animal:
        parts.append(f"subtle {animal} motif integrated tastefully")

    # Global style hints for realism
    parts.append(
        "ultra-detailed skin texture, realistic lighting, natural tones, shallow depth of field, 4k"
    )
    parts.append("95% photorealistic, cinematic quality")

    positive_prompt = ", ".join(parts)

    negative_prompt = (
        "cartoon, illustration, cgi, plastic skin, over-saturated, low-res, blurry, deformed, "
        "extra fingers, bad anatomy, artifacts, watermark, text, logo"
    )

    return positive_prompt, negative_prompt
