import io

from leaklens import cli


class Terminal(io.StringIO):
    def isatty(self):
        return True


def test_severity_label_colors_terminal_output(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(cli.sys, "stdout", Terminal())
    assert cli._severity_label("high") == "\x1b[31m[HIGH]\x1b[0m"
    assert cli._severity_label("medium") == "\x1b[33m[MEDIUM]\x1b[0m"
    assert cli._severity_label("low") == "\x1b[36m[LOW]\x1b[0m"


def test_severity_label_respects_no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "")
    monkeypatch.setattr(cli.sys, "stdout", Terminal())
    assert cli._severity_label("high") == "[HIGH]"


def test_severity_label_disables_color_for_piped_output(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(cli.sys, "stdout", io.StringIO())
    assert cli._severity_label("medium") == "[MEDIUM]"


def test_severity_label_leaves_unknown_labels_plain(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(cli.sys, "stdout", Terminal())
    assert cli._severity_label("info") == "[INFO]"
