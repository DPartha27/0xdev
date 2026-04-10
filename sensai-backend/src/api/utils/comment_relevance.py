"""
Comment relevance checker using sentence-transformers.
Uses all-MiniLM-L6-v2 (~80MB, runs on CPU) to compute cosine similarity
between post context and the incoming comment.
Model loads lazily on first use.
"""

from api.utils.logging import logger

_model = None


def _load_model():
    global _model
    if _model is not None:
        return

    from sentence_transformers import SentenceTransformer

    _model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    logger.info("Sentence-transformer loaded (all-MiniLM-L6-v2)")


def check_comment_relevance(
    post_title: str,
    post_content: str | None,
    post_code: str | None,
    comment_text: str,
    comment_code: str | None = None,
    threshold: float = 0.12,
) -> dict:
    """
    Check if a comment is relevant to the post it's being added to.

    Args:
        post_title: The post's title.
        post_content: The post's text content (can be None).
        post_code: The post's code content (can be None).
        comment_text: The comment text being submitted.
        comment_code: Optional code in the comment.
        threshold: Minimum cosine similarity to consider relevant (0-1).
                   0.12 is intentionally lenient — catches spam/gibberish
                   but allows tangential but genuine discussion and reactions.

    Returns:
        {
            "relevant": bool,
            "score": float,      # cosine similarity 0-1
            "reason": str,
        }
    """
    import numpy as np

    stripped = comment_text.strip().lower()

    # Only allow known short reactions — everything else gets checked
    ALLOWED_SHORT = {
        "thanks", "thanks!", "thank you", "thank you!", "ty",
        "got it", "got it!", "helpful", "nice", "nice!",
        "+1", "agree", "agreed", "same", "same here",
        "great", "great!", "awesome", "awesome!", "cool",
        "good point", "well said", "makes sense",
        "interesting", "noted", "ok", "okay",
    }
    if stripped in ALLOWED_SHORT:
        return {"relevant": True, "score": 1.0, "reason": "Recognized short reaction."}

    # Reject very short gibberish (under 3 real words, not in whitelist)
    words = stripped.split()
    if len(words) < 3 and stripped not in ALLOWED_SHORT:
        return {
            "relevant": False,
            "score": 0.0,
            "reason": "Comment is too short. Please write a meaningful reply related to the post.",
        }

    _load_model()

    # Build post context string
    post_parts = [post_title]
    if post_content:
        post_parts.append(post_content[:500])  # cap to avoid huge embeddings
    if post_code:
        post_parts.append(post_code[:300])
    post_context = " ".join(post_parts)

    # Build comment string
    comment_parts = [comment_text]
    if comment_code:
        comment_parts.append(comment_code[:300])
    comment_context = " ".join(comment_parts)

    embeddings = _model.encode([post_context, comment_context], normalize_embeddings=True)
    similarity = float(np.dot(embeddings[0], embeddings[1]))

    relevant = similarity >= threshold

    if relevant:
        reason = f"Comment is relevant to the post (similarity: {similarity:.2f})."
    else:
        reason = (
            f"Your comment doesn't seem related to this post (similarity: {similarity:.2f}). "
            "Please make sure your reply is relevant to the topic being discussed."
        )

    return {
        "relevant": relevant,
        "score": round(similarity, 3),
        "reason": reason,
    }
