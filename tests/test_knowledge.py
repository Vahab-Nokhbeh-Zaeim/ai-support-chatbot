from app.knowledge import Entry, KnowledgeBase, tokenize


def make_kb() -> KnowledgeBase:
    return KnowledgeBase([
        Entry("How long does shipping take?", "Delivery takes 2 to 4 business days."),
        Entry("Can I return a product?", "Returns are accepted within 7 days."),
        Entry("Which payment methods do you accept?", "We accept bank cards."),
    ])


def test_tokenize_removes_stop_words_and_punctuation():
    assert tokenize("How do I RETURN a product?") == ["return", "product"]


def test_best_match_comes_first():
    matches = make_kb().search("I want to return my product")
    assert matches[0].entry.question == "Can I return a product?"


def test_shipping_question():
    matches = make_kb().search("when will my delivery arrive")
    assert matches[0].entry.question == "How long does shipping take?"


def test_unrelated_query_returns_nothing():
    assert make_kb().search("favourite football team") == []


def test_top_k_limits_results():
    assert len(make_kb().search("product payment shipping", top_k=2)) <= 2
