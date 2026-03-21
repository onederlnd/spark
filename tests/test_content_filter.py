# tests/test_content_filter.py


def test_teacher_can_add_word(teacher_client):
    response = teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": "badword"},
        follow_redirects=True,
    )
    assert b"badword" in response.data


def test_added_word_is_lowercase(teacher_client):
    teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": "BadWord"},
        follow_redirects=True,
    )
    response = teacher_client.get("/classrooms/filter/words")
    assert b"badword" in response.data


def test_teacher_can_remove_word(teacher_client):
    teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": "badword"},
    )
    response = teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "remove", "word": "badword"},
        follow_redirects=True,
    )
    assert b"removed from filter" in response.data
    assert b"removed from filter" in response.data

    # Confirm it's gone from the list on a fresh GET
    response = teacher_client.get("/classrooms/filter/words")
    assert b"badword" not in response.data


def test_duplicate_word_rejected(teacher_client):
    teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": "badword"},
    )
    response = teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": "badword"},
        follow_redirects=True,
    )
    assert b"already exists" in response.data


def test_duplicate_word_case_insensitive(teacher_client):
    teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": "badword"},
    )
    response = teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": "BADWORD"},
        follow_redirects=True,
    )
    assert b"already exists" in response.data


def test_empty_word_rejected(teacher_client):
    response = teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": ""},
        follow_redirects=True,
    )
    assert b"empty" in response.data


def test_student_cannot_access_filter_page(student_client):
    response = student_client.get("/classrooms/filter/words")
    assert response.status_code == 403


def test_student_cannot_add_word(student_client):
    response = student_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": "badword"},
    )
    assert response.status_code == 403


def test_word_appears_in_list(teacher_client):
    teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": "testword"},
    )
    response = teacher_client.get("/classrooms/filter/words")
    assert b"testword" in response.data


def test_removed_word_no_longer_filters(teacher_client):
    from app.utils.content_filter import add_word, remove_word, check_content

    add_word("sneaky", user_id=1)
    assert check_content("this is sneaky content") != []

    remove_word("sneaky")
    assert check_content("this is sneaky content") == []


def test_check_content_matches_custom_word(teacher_client):
    from app.utils.content_filter import add_word, check_content

    add_word("forbidden", user_id=1)
    matches = check_content("this contains forbidden text")
    assert "forbidden" in matches


def test_check_content_whole_word_only(teacher_client):
    from app.utils.content_filter import add_word, check_content

    add_word("class", user_id=1)
    matches = check_content("this is about classroom management")
    assert "class" not in matches


def test_check_content_clean_text(teacher_client):
    from app.utils.content_filter import check_content

    matches = check_content("this is perfectly fine text")
    assert matches == []


def test_check_content_empty_string():
    from app.utils.content_filter import check_content

    assert check_content("") == []


def test_check_content_none():
    from app.utils.content_filter import check_content

    assert check_content(None) == []
