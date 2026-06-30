from __future__ import annotations

import importlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy load FlagEmbedding to avoid importing torch/transformers during normal metadata syncs
_model = None


def get_bge_m3_model() -> Any:
    global _model
    if _model is None:
        try:
            flag_embedding = importlib.import_module("FlagEmbedding")
            logger.info("Loading BAAI/bge-m3 model (this may take a few seconds)...")
            # Set use_fp16=True if GPU is available to speed up execution
            torch = importlib.import_module("torch")
            use_fp16 = torch.cuda.is_available()
            _model = flag_embedding.BGEM3FlagModel("BAAI/bge-m3", use_fp16=use_fp16)
            logger.info("BAAI/bge-m3 model loaded successfully.")
        except ImportError as e:
            raise ImportError(
                "FlagEmbedding, torch, and transformers are required to generate embeddings. "
                "Install them using `pip install .[embeddings]` or `uv sync --all-extras`."
            ) from e
    return _model


def compute_all_three_embeddings(text: str) -> dict[str, Any]:
    """Compute dense, sparse, and late-interaction embeddings for text.

    Returns a dictionary containing:
      - 'dense': list of 1024 floats
      - 'lexical_weights': dict mapping token/lexical ID to float weight
      - 'colbert_multivector': list of lists of floats (token embeddings)
    """
    if not text.strip():
        return {"dense": [], "lexical_weights": {}, "colbert_multivector": []}

    model = get_bge_m3_model()

    # Run the model's unified encode function
    # It returns a dictionary with keys: 'dense_embeds', 'sparse_embeds', 'colbert_embeds'
    output = model.encode([text], return_dense=True, return_sparse=True, return_colbert=True)

    dense = output["dense_embeds"][0]
    dense = dense.tolist() if hasattr(dense, "tolist") else list(dense)

    # Sparse weights are returned as dict format {token_id: weight} or similar depending on the FlagEmbedding version
    # Convert token weights to simple dictionary mapping string to float
    sparse_data = output["sparse_embeds"][0]
    # In some versions of FlagEmbedding, sparse_embeds is a dictionary. In others, it is a custom class.
    # Let's handle both dictionary/object formats safely:
    if hasattr(sparse_data, "items"):
        lexical_weights = {str(k): float(v) for k, v in sparse_data.items()}
    elif hasattr(sparse_data, "asdict"):
        lexical_weights = {str(k): float(v) for k, v in sparse_data.asdict().items()}
    else:
        lexical_weights = {}

    colbert = output["colbert_embeds"][0]
    if hasattr(colbert, "tolist"):
        colbert = colbert.tolist()
    elif isinstance(colbert, list):
        colbert = [v.tolist() if hasattr(v, "tolist") else list(v) for v in colbert]
    else:
        colbert = list(colbert)

    return {"dense": dense, "lexical_weights": lexical_weights, "colbert_multivector": colbert}
