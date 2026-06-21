"""Property-based tests using Hypothesis for key utility functions."""

from __future__ import annotations

import re
from collections.abc import Mapping

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nz_legislation_corpus.cli import _raw_content_type_for_url, _raw_suffix_for_content_type
from nz_legislation_corpus.nz_api import HTTPResponse, NZLegislationClient
from nz_legislation_corpus.utils import slug_for_path

# ── slug_for_path ──────────────────────────────────────────────────────────


@pytest.mark.hypothesis
@given(st.text())
def test_slug_is_always_filesystem_safe(value: str) -> None:
    slug = slug_for_path(value)
    assert re.fullmatch(r"[A-Za-z0-9_.=-]*", slug), f"Unsafe slug: {slug!r}"
    assert len(slug) <= 160
    assert len(slug) >= 1


@pytest.mark.hypothesis
@given(st.text(max_size=500))
def test_slug_length_never_exceeds_max(value: str) -> None:
    slug = slug_for_path(value, max_len=50)
    assert len(slug) <= 50


# ── _parse_int_header ──────────────────────────────────────────────────────


@pytest.mark.hypothesis
@given(st.integers(min_value=0, max_value=10**9))
def test_parse_int_header_valid(valid_int: int) -> None:
    result = NZLegislationClient._parse_int_header(str(valid_int))
    assert result == valid_int


@pytest.mark.hypothesis
@given(st.one_of(st.none(), st.text(alphabet="abcxyz!@#$%^&*", min_size=1)))
def test_parse_int_header_invalid_returns_none(invalid_value: str | None) -> None:
    result = NZLegislationClient._parse_int_header(invalid_value)
    assert result is None


@pytest.mark.hypothesis
@given(st.text(min_size=1))
def test_parse_int_header_whitespace_handling(raw: str) -> None:
    """Whitespace around a valid int should still parse correctly."""
    stripped = raw.strip()
    result = NZLegislationClient._parse_int_header(raw)
    # Check if stripped text represents a valid integer (ASCII digits only)
    if stripped and re.fullmatch(r"[+-]?\d+", stripped):
        assert result is not None
        assert isinstance(result, int)
    else:
        assert result is None


# ── _retry_after_seconds ───────────────────────────────────────────────────


@pytest.mark.hypothesis
@given(st.floats(min_value=0.0, max_value=120.0, allow_nan=False, allow_infinity=False))
def test_retry_after_seconds_valid_float(delay: float) -> None:
    response = _make_response(headers={"Retry-After": str(delay)})
    result = NZLegislationClient._retry_after_seconds(response, fallback_attempt=0)
    assert result == delay


@pytest.mark.hypothesis
@given(st.floats(min_value=0.0, max_value=120.0, allow_nan=False, allow_infinity=False))
def test_retry_after_seconds_valid_int_as_float(delay: float) -> None:
    response = _make_response(headers={"Retry-After": str(int(delay))})
    result = NZLegislationClient._retry_after_seconds(response, fallback_attempt=0)
    assert result == int(delay)


@pytest.mark.hypothesis
@given(
    st.text(alphabet="abcxyz!@#$%^&*", min_size=1),
    st.integers(min_value=0, max_value=5),
)
def test_retry_after_seconds_invalid_falls_back(invalid: str, attempt: int) -> None:
    response = _make_response(headers={"Retry-After": invalid})
    result = NZLegislationClient._retry_after_seconds(response, fallback_attempt=attempt)
    lower = min(120, 2**attempt)
    upper = min(120, 2**attempt + 1)
    assert lower <= result <= upper


# ── _raw_content_type_for_url ──────────────────────────────────────────────


@pytest.mark.hypothesis
@given(st.text(min_size=1))
def test_raw_content_type_for_url_always_returns_string(url: str) -> None:
    ct = _raw_content_type_for_url(url)
    assert ct in ("application/xml", "text/html"), f"Unexpected content type: {ct!r}"


@pytest.mark.hypothesis
@given(st.from_regex(r".*\.xml.*", fullmatch=True))
def test_raw_content_type_for_url_xml_pattern(url_with_xml: str) -> None:
    ct = _raw_content_type_for_url(url_with_xml)
    assert ct == "application/xml"


@pytest.mark.hypothesis
@given(st.from_regex(r".*\.html.*", fullmatch=True))
def test_raw_content_type_for_url_html_pattern(url_with_html: str) -> None:
    ct = _raw_content_type_for_url(url_with_html)
    if ".xml" in url_with_html.lower():
        assert ct == "application/xml"
    else:
        assert ct == "text/html"


# ── _raw_suffix_for_content_type ───────────────────────────────────────────


@pytest.mark.hypothesis
@given(st.text())
def test_raw_suffix_for_content_type_always_returns_expected(content_type: str) -> None:
    suffix = _raw_suffix_for_content_type(content_type)
    assert suffix in (".xml", ".html"), f"Unexpected suffix: {suffix!r}"


@pytest.mark.hypothesis
@given(st.just("application/xml"))
def test_raw_suffix_for_xml(xml_ct: str) -> None:
    assert _raw_suffix_for_content_type(xml_ct) == ".xml"


@pytest.mark.hypothesis
@given(st.text().filter(lambda s: s != "application/xml"))
def test_raw_suffix_for_non_xml(content_type: str) -> None:
    assert _raw_suffix_for_content_type(content_type) == ".html"


# ── helpers ────────────────────────────────────────────────────────────────


class _FakeResponse:
    """Minimal HTTPResponse Protocol implementor for property-based tests."""

    status_code: int = 200
    headers: Mapping[str, str]
    content: bytes = b""
    text: str = ""

    def __init__(self, headers: Mapping[str, str] | None = None) -> None:
        self.headers = headers or {}

    def json(self) -> object:
        return {}

    def raise_for_status(self) -> None:
        pass


def _make_response(*, headers: dict[str, str] | None = None) -> HTTPResponse:
    """Build a minimal response-like object satisfying the HTTPResponse Protocol."""
    return _FakeResponse(headers=headers)


@pytest.mark.hypothesis
@given(st.text(alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")), min_size=1))
def test_slug_preserves_safe_characters(value: str) -> None:
    slug = slug_for_path(value, max_len=500)
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.=-")
    for ch in slug:
        assert ch in allowed, f"Character {ch!r} not allowed in slug {slug!r}"
