from evaluation.defect_detector import DefectDetector


def test_detect_defects_thresholds():
    """Test that low scores (1.0) trigger threshold defects D01-D04."""
    scores = {"reasoning": 1.0, "accuracy": 1.0, "tone": 1.0, "completeness": 1.0}
    defects = DefectDetector.detect_defects("some text", scores)
    assert "D01" in defects
    assert "D02" in defects
    assert "D03" in defects
    assert "D04" in defects


def test_detect_defects_redundancy():
    """Test that repetitive text triggers redundancy defect D05."""
    # Repetitive text - 30 occurrences of "word"
    text = "word " * 30
    defects = DefectDetector.detect_defects(text, {"reasoning": 5.0})
    assert "D05" in defects


def test_detect_defects_no_defects():
    """Test that high-quality text with high scores returns no defects."""
    text = "This is a unique and high quality response with many different words."
    scores = {"reasoning": 5.0, "accuracy": 5.0, "tone": 5.0, "completeness": 5.0}
    defects = DefectDetector.detect_defects(text, scores)
    assert defects == []


def test_detect_defects_normalized_scores():
    """Test that normalized scores (0.2 * 5 = 1.0) trigger threshold defects."""
    scores = {
        "score_reasoning": 0.2,  # 0.2 * 5 = 1.0
    }
    defects = DefectDetector.detect_defects("text", scores)
    assert "D01" in defects


def test_detect_defects_refusal():
    """Test that AI refusal phrases trigger refusal defect D06."""
    text = "As an AI model, I cannot fulfill this request."
    defects = DefectDetector.detect_defects(text, {"reasoning": 5.0})
    assert "D06" in defects


def test_detect_defects_hallucination_warning():
    """Test that hallucination warning phrases trigger D07."""
    text = "To the best of my knowledge, the earth is flat."
    defects = DefectDetector.detect_defects(text, {"reasoning": 5.0})
    assert "D07" in defects


def test_get_score_conversion_exceptions():
    """Test that invalid score conversions default to 5.0 (no defect)."""
    # Test norm exception inside get_score: norm is not a valid float
    scores = {"score_reasoning": "invalid_float_val"}
    defects = DefectDetector.detect_defects("text", scores)
    # val becomes None, then get_score returns 5.0 (no defect)
    assert "D01" not in defects

    # Test outer conversion exception: val is a list, raising TypeError/ValueError in float(val)
    scores2 = {"reasoning": [1, 2, 3]}
    defects2 = DefectDetector.detect_defects("text", scores2)
    # returns 5.0, so no defect
    assert "D01" not in defects2


def test_redundancy_edge_cases():
    """Test edge cases for redundancy detection."""
    # 1. More than 20 words, all are punctuation/spaces.
    # Words list has 25 periods. All strip to "". Unique set is {""}.
    # Unique ratio is 1 / 25 = 0.04 < 0.5. So D05 is appended.
    text_empty_normalized = ". " * 25
    defects = DefectDetector.detect_defects(text_empty_normalized, {"reasoning": 5.0})
    assert "D05" in defects

    # 2. More than 20 words, but unique_ratio is high (>= 0.5)
    text_unique = " ".join([f"word{i}" for i in range(25)])
    defects2 = DefectDetector.detect_defects(text_unique, {"reasoning": 5.0})
    assert "D05" not in defects2
