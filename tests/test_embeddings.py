from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nz_legislation_corpus.embeddings import compute_all_three_embeddings


@pytest.mark.unit
def test_compute_all_three_embeddings_empty():
    res = compute_all_three_embeddings("")
    assert res == {"dense": [], "lexical_weights": {}, "colbert_multivector": []}


@patch("nz_legislation_corpus.embeddings.get_bge_m3_model")
@pytest.mark.unit
def test_compute_all_three_embeddings_mocked(mock_get_model):
    mock_model = MagicMock()
    # Mocking BGE-M3 model output
    mock_model.encode.return_value = {
        "dense_embeds": [[0.1, 0.2, 0.3]],
        "sparse_embeds": [{"101": 0.5, "202": 0.8}],
        "colbert_embeds": [[[0.1, 0.2], [0.3, 0.4]]],
    }
    mock_get_model.return_value = mock_model

    res = compute_all_three_embeddings("sample text")

    assert res["dense"] == [0.1, 0.2, 0.3]
    assert res["lexical_weights"] == {"101": 0.5, "202": 0.8}
    assert res["colbert_multivector"] == [[0.1, 0.2], [0.3, 0.4]]

    mock_model.encode.assert_called_once_with(
        ["sample text"], return_dense=True, return_sparse=True, return_colbert=True
    )
