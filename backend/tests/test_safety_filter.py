from safety_filter import analyze_message


def test_crisis_suicidal_ideation():
    result = analyze_message("I want to kill myself")
    assert result["level"] == "CRISIS"


def test_crisis_self_harm():
    result = analyze_message("I've been cutting myself lately")
    assert result["level"] == "CRISIS"


def test_crisis_end_it():
    result = analyze_message("I just want to end it all")
    assert result["level"] == "CRISIS"


def test_warning_hopeless():
    result = analyze_message("I just can't go on anymore, everything feels hopeless")
    assert result["level"] == "WARNING"


def test_warning_cant_cope():
    result = analyze_message("I don't know how to cope with this")
    assert result["level"] == "WARNING"


def test_safe_message():
    result = analyze_message("I've been feeling stressed at work lately")
    assert result["level"] == "SAFE"


def test_safe_empty():
    result = analyze_message("")
    assert result["level"] == "SAFE"


def test_result_has_message_key():
    result = analyze_message("hello")
    assert "message" in result
