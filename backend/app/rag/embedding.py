from sentence_transformers import SentenceTransformer

from app.core.config import settings

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model, device="cpu")
    return _model


def embed_passages(texts: list[str]) -> list[list[float]]:
    prefixed = [f"passage: {t}" for t in texts]
    return get_embedding_model().encode(prefixed, convert_to_numpy=True).tolist()


def embed_query(text: str) -> list[float]:
    return get_embedding_model().encode(f"query: {text}", convert_to_numpy=True).tolist()
