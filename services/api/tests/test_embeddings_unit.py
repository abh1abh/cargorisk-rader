def test_embed_shape_and_unit_norm(embedding_model):
    v = embedding_model.embed_text("container detention and demurrage calculation")
    assert isinstance(v, list) and len(v) == 384
    s = sum(x*x for x in v)
    assert 0.98 <= s <= 1.02
