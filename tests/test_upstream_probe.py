"""An unreadable upstream response must never be evidence of absence."""

import io
import urllib.error

import pytest

from tools import probe_upstream_bfiles as upstream


def response(monkeypatch, body):
    def open_response(*args, **kwargs):
        return io.BytesIO(body)

    monkeypatch.setattr(upstream.urllib.request, "urlopen", open_response)


def test_probe_preserves_indices_values_and_row_count(monkeypatch):
    # Out-of-order rows distinguish max(index) from the last row and min(index).
    response(monkeypatch, b"# comment\n\n4 900000000000000000000000000001\n2 -7\n3 0\n")
    assert upstream.probe("A000000") == (
        3, 4, {2: -7, 3: 0, 4: 900000000000000000000000000001},
    )


@pytest.mark.parametrize("body", [b"", b"# no data\n\n", b"<HTML>rate limited</HTML>"])
def test_empty_or_html_response_is_unknown(monkeypatch, body):
    response(monkeypatch, body)
    assert upstream.probe("A000000") == (None, None, None)


@pytest.mark.parametrize("body", [b"2 5\n3", b"2 5\n3\n4 9\n"])
def test_truncated_row_invalidates_the_entire_response(monkeypatch, body):
    response(monkeypatch, body)
    assert upstream.probe("A000000") == (None, None, None)


@pytest.mark.parametrize("failure", ["timeout", "not_found"])
def test_failed_fetch_is_unknown_even_for_404(monkeypatch, failure):
    def fail(*args, **kwargs):
        if failure == "timeout":
            raise TimeoutError("simulated timeout")
        raise urllib.error.HTTPError("https://example.invalid", 404, "missing", {}, None)

    monkeypatch.setattr(upstream.urllib.request, "urlopen", fail)
    assert upstream.probe("A000000") == (None, None, None)
