from ..app.services.embeddings import embed_text


def test_embed_shape_and_unit_norm():
    v = embed_text("container detention and demurrage calculation")
    assert isinstance(v, list) and len(v) == 384
    s = sum(x*x for x in v)
    # unit norm within tolerance
    assert 0.98 <= s <= 1.02
