from pathlib import Path


INDEX_HTML = Path("frontend/index.html")
WRONG_BOOK_JS = Path("frontend/assets/js/wrong-book.js")
STYLES = Path("frontend/assets/styles.css")


def test_wrong_book_sidebar_button_and_modal_contract():
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="open-wrong-book-btn"' in html
    assert 'onclick="openWrongBookModal()"' in html
    assert 'aria-controls="wrong-book-modal"' in html
    assert 'aria-haspopup="dialog"' in html
    assert 'id="wb-badge"' not in html
    assert 'class="sb-badge"' not in html
    assert 'id="wrong-book-modal"' in html
    assert 'class="unified-dialog unified-dialog--wrong-book"' in html
    assert 'id="wrong-book-body"' in html
    assert 'id="wrong-book-footer"' in html
    assert '/assets/js/wrong-book.js?v=' in html


def test_wrong_book_opens_before_fetch_and_does_not_depend_on_app_local_modal_helper():
    js = WRONG_BOOK_JS.read_text(encoding="utf-8")

    open_start = js.index("open() {")
    open_end = js.index("close(event)", open_start)
    open_body = js[open_start:open_end]

    assert "this._setOpen(true);" in open_body
    assert "this._showLoading();" in open_body
    assert "this._fetchAndRender();" in open_body
    assert open_body.index("this._setOpen(true);") < open_body.index("this._fetchAndRender();")
    assert "setModalOpen(" not in js
    assert "_updateBadge" not in js
    assert "wb-badge" not in js
    assert "window.WrongBook = WrongBook" in js


def test_wrong_book_uses_aitutor_state_and_renders_grouped_node_fields():
    js = WRONG_BOOK_JS.read_text(encoding="utf-8")

    assert "window.AITutorApp" in js
    assert "state.studentId || state.student_id || 'default_student'" in js
    assert "_groupByNode(items)" in js
    assert "node_name" in js
    assert "target_objective" in js
    assert "wrong_reason" in js
    assert "recommended_review" in js
    assert "wrong_option_analysis" in js
    assert "完整题干" in js
    assert "选项" in js
    assert "讲解" in js
    assert "为什么错" in js
    assert "正确理解" in js
    assert "判断依据" in js
    assert "下一步" in js
    assert "复习建议" in js


def test_wrong_book_exposes_filter_tabs_for_unmastered_and_mastered_items():
    js = WRONG_BOOK_JS.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")

    assert "filter: 'unmastered'" in js
    assert "_renderToolbar()" in js
    assert "wb-filter-tab" in js
    assert "data-filter=\"all\"" in js
    assert "data-filter=\"unmastered\"" in js
    assert "data-filter=\"mastered\"" in js
    assert "this._setFilter(btn.dataset.filter || 'unmastered')" in js
    assert "params.set('mastered', 'false')" in js
    assert "params.set('mastered', 'true')" in js
    assert ".wb-toolbar" in styles
    assert ".wb-filter-tab.active" in styles


def test_wrong_book_master_buttons_read_question_id_from_card_dataset():
    js = WRONG_BOOK_JS.read_text(encoding="utf-8")

    assert "wb-master-toggle" in js
    assert "data-mastered=\"false\"" in js
    assert "data-mastered=\"true\"" in js
    assert "_bindEvents()" in js
    assert "_markMasteredFromButton(btn, mastered)" in js
    assert "closest('.wb-item')" in js
    assert "dataset.qid" in js
    assert 'onclick="WrongBook._markMastered(' not in js
    assert "WrongBook._markMasteredFromButton(this" not in js


def test_wrong_book_styles_are_information_panel_friendly():
    styles = STYLES.read_text(encoding="utf-8")

    assert ".unified-dialog--wrong-book" in styles
    assert "width: min(920px, calc(100vw - 32px))" in styles
    assert "height: min(760px, calc(100vh - 80px))" in styles
    assert ".wb-overview" in styles
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in styles
    assert ".wb-group-progress" in styles
    assert ".wb-item-topline" in styles
    assert ".wb-pill--warn" in styles
    assert ".wb-answer--wrong" in styles
    assert ".wb-option--correct" in styles
    assert "overflow-wrap: anywhere" in styles
    assert ".sb-badge" not in styles
