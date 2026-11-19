from app.knowledge import Entry, KnowledgeBase, is_persian, tokenize


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


def make_fa_kb() -> KnowledgeBase:
    return KnowledgeBase([
        Entry("هزینه ارسال چقدر است؟", "ارسال برای سفارش‌های بالای ۲ میلیون تومان رایگان است."),
        Entry("آیا امکان مرجوع کردن کالا وجود دارد؟", "تا ۷ روز پس از تحویل می‌توانید مرجوع کنید."),
        Entry("چطور سفارشم را پیگیری کنم؟", "کد رهگیری برایتان پیامک می‌شود."),
        Entry("آیا محصولات گارانتی دارند؟", "همه محصولات ۱۸ ماه گارانتی دارند."),
    ])


def test_tokenize_persian_removes_stop_words_and_punctuation():
    assert tokenize("آیا امکان مرجوع کردن کالا وجود دارد؟") == ["امکان", "مرجوع", "کردن", "کالا", "وجود"]


def test_tokenize_joins_half_spaces_and_fixes_arabic_letters():
    assert tokenize("پيگيري سفارش‌ها") == ["پیگیری", "سفارش"]
    assert tokenize("مي‌شود") == tokenize("میشود")


def test_tokenize_converts_persian_digits():
    assert tokenize("۱۸ ماه") == ["18", "ماه"]


def test_persian_questions_find_the_right_answer():
    kb = make_fa_kb()
    assert kb.search("هزینه ارسال چقدره؟")[0].entry.question == "هزینه ارسال چقدر است؟"
    assert kb.search("میخوام کالا رو مرجوع کنم")[0].entry.question.startswith("آیا امکان مرجوع")
    assert kb.search("گارانتی محصولات")[0].entry.question == "آیا محصولات گارانتی دارند؟"


def test_arabic_keyboard_still_matches():
    assert kb_question(make_fa_kb().search("پيگيري سفارش")) == "چطور سفارشم را پیگیری کنم؟"


def test_unrelated_persian_query_returns_nothing():
    assert make_fa_kb().search("سلام خوبی؟") == []


def test_is_persian():
    assert is_persian("سلام")
    assert not is_persian("hello")


def kb_question(matches):
    return matches[0].entry.question if matches else None
