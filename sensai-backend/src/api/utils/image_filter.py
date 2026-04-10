"""
Educational image filter using CLIP (open-clip-torch).
Uses raw cosine similarities (not softmax) to avoid bias from label count.
An image must score higher against educational labels than rejection labels.
Model (~150MB) loads lazily on first use, runs on CPU.
"""

import io
from PIL import Image
from api.utils.logging import logger

_model = None
_preprocess = None
_tokenizer = None

EDUCATIONAL_LABELS = [
    "a technical diagram or flowchart for software engineering",
    "a screenshot of source code in a code editor or terminal",
    "a whiteboard with mathematical equations or lecture notes",
    "a page from a textbook or academic paper",
    "a data chart, bar graph, or statistical visualization",
    "a system architecture or network topology diagram",
    "a mathematical formula written on paper or screen",
    "a slide from an educational presentation or lecture",
    "a database schema, ER diagram, or UML diagram",
    "a circuit diagram or electronic schematic",
    "a UI wireframe or technical mockup for a software project",
    "a screenshot of a documentation page or API reference",
]

REJECT_LABELS = [
    "an anime or manga screenshot or illustration",
    "a cartoon or animated character drawing",
    "a video game screenshot or gaming content",
    "a selfie or portrait photograph of a person",
    "a meme, joke image, or funny picture with text overlay",
    "a photo of food, cooking, or a restaurant meal",
    "a photo of a pet, cat, dog, or animal",
    "a scenic landscape, nature, or travel photograph",
    "a celebrity, movie star, or entertainment photograph",
    "a violent, graphic, or disturbing image",
    "an explicit, sexual, or adult content image",
    "a social media post, instagram story, or tiktok screenshot",
    "a promotional advertisement or marketing banner",
    "a sports photograph or athletic event",
    "a fashion, clothing, or beauty photograph",
    "fan art, digital art, or artistic illustration",
    "a movie or TV show screenshot or poster",
]


def _load_model():
    global _model, _preprocess, _tokenizer
    if _model is not None:
        return

    import open_clip

    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k", device="cpu"
    )
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model.eval()
    _model = model
    _preprocess = preprocess
    _tokenizer = tokenizer
    logger.info("CLIP model loaded (ViT-B-32)")


def classify_image(image_bytes: bytes) -> dict:
    """
    Classify an image as educational or not.

    Uses the MAX raw cosine similarity against educational vs rejection labels.
    This avoids softmax bias from unequal label counts.

    Decision:
      - best_edu_sim > best_rej_sim → allowed (educational wins)
      - Otherwise → rejected

    Returns:
        {
            "allowed": bool,
            "category": str,
            "confidence": float,
            "best_educational": str,
            "best_educational_sim": float,
            "best_rejection": str,
            "best_rejection_sim": float,
            "reason": str,
        }
    """
    import torch
    import numpy as np

    _load_model()

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return {
            "allowed": False,
            "category": "invalid",
            "confidence": 0.0,
            "best_educational": "",
            "best_educational_sim": 0.0,
            "best_rejection": "",
            "best_rejection_sim": 0.0,
            "reason": "Could not open image file.",
        }

    all_labels = EDUCATIONAL_LABELS + REJECT_LABELS
    text_inputs = _tokenizer(all_labels)
    image_input = _preprocess(image).unsqueeze(0)

    with torch.no_grad():
        image_features = _model.encode_image(image_input)
        text_features = _model.encode_text(text_inputs)

        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        # Raw cosine similarities (not softmax)
        sims = (image_features @ text_features.T).squeeze(0).cpu().numpy()

    n_edu = len(EDUCATIONAL_LABELS)
    edu_sims = sims[:n_edu]
    rej_sims = sims[n_edu:]

    best_edu_idx = int(np.argmax(edu_sims))
    best_rej_idx = int(np.argmax(rej_sims))

    best_edu_label = EDUCATIONAL_LABELS[best_edu_idx]
    best_rej_label = REJECT_LABELS[best_rej_idx]
    best_edu_sim = float(edu_sims[best_edu_idx])
    best_rej_sim = float(rej_sims[best_rej_idx])

    # Educational must beat rejection by a margin to avoid borderline passes
    MARGIN = 0.02
    allowed = best_edu_sim > (best_rej_sim + MARGIN)

    if allowed:
        category = best_edu_label
        confidence = best_edu_sim
        reason = f"Image classified as educational: {best_edu_label} (score: {best_edu_sim:.2f} vs rejection: {best_rej_sim:.2f})"
    else:
        category = best_rej_label
        confidence = best_rej_sim
        reason = (
            f"Image appears non-educational: {best_rej_label} (score: {best_rej_sim:.2f} vs educational: {best_edu_sim:.2f}). "
            "Only educational images (diagrams, code screenshots, charts, etc.) are allowed."
        )

    return {
        "allowed": allowed,
        "category": category,
        "confidence": round(confidence, 3),
        "best_educational": best_edu_label,
        "best_educational_sim": round(best_edu_sim, 3),
        "best_rejection": best_rej_label,
        "best_rejection_sim": round(best_rej_sim, 3),
        "reason": reason,
    }
