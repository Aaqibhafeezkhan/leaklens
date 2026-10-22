from leaklens.bench import evaluate


def test_benchmark_has_no_errors():
    m = evaluate()
    assert m["errors"] == [], m["errors"]
    assert m["n"] >= 25