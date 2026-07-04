from evaluation.defect_detector import DefectDetector


def test_detect_defects_thresholds():
    scores = {"reasoning": 1.0, "accuracy": 1.0, "tone": 1.0, "completeness": 1.0}
    defects = DefectDetector.detect_defects("some text", scores)
    assert "D01" in defects
    assert "D02" in defects
    assert "D03" in defects
    assert "D04" in defects


def test_detect_defects_redundancy():
    # Repetitive text
    text = "word " * 30
    defects = DefectDetector.detect_defects(text, {"reasoning": 5.0})
    assert "D05" in defects


def test_detect_defects_no_defects():
    text = "This is a unique and high quality response with many different words."
    scores = {"reasoning": 5.0, "accuracy": 5.0, "tone": 5.0, "completeness": 5.0}
    defects = DefectDetector.detect_defects(text, scores)
    assert defects == []


def test_detect_defects_normalized_scores():
    scores = {
        "score_reasoning": 0.2,  # 0.2 * 5 = 1.0
    }
    defects = DefectDetector.detect_defects("text", scores)
    assert "D01" in defects


def test_detect_defects_refusal():
    text = "As an AI model, I cannot fulfill this request."
    defects = DefectDetector.detect_defects(text, {"reasoning": 5.0})
    assert "D06" in defects


def test_detect_defects_hallucination_warning():
    text = "To the best of my knowledge, the earth is flat."
    defects = DefectDetector.detect_defects(text, {"reasoning": 5.0})
    assert "D07" in defects
