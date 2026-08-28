"""Tests for the discovery layer and the series resolver.

Both were missing entirely before 2026-08-28: the catalog existed but there
was no way to browse or search it without opening series.py, and `series=`
accepted only a dict. These are the conventions the sibling Census_Loader
already followed, and the point of the change is that the two libraries now
behave the same way.

Offline by construction: every one of these paths is pure catalog work with
no network in it.
"""

import pytest

import fred_loader
from fred_loader import ALL_SERIES, CATEGORIES, SUBCATEGORIES
from fred_loader.utils import Config, available, info, resolve_series, search


# ── the discovery surface exists and is reachable from the root ───────────


@pytest.mark.parametrize("name", ["available", "search", "info", "resolve_series"])
def test_discovery_helpers_are_exported(name):
    assert hasattr(fred_loader, name)
    assert name in fred_loader.__all__


# ── resolve_series ────────────────────────────────────────────────────────


def test_none_resolves_to_the_whole_catalog():
    assert resolve_series(None) is ALL_SERIES


def test_a_dict_passes_through_untouched():
    """Backward compatibility: a dict was the only accepted input before."""
    custom = {"CPIAUCSL": ("Headline_CPI", "M")}
    assert resolve_series(custom) is custom


def test_a_single_series_id_resolves():
    out = resolve_series("CPIAUCSL")
    assert list(out) == ["CPIAUCSL"]
    assert out["CPIAUCSL"] == ALL_SERIES["CPIAUCSL"]


def test_a_category_name_resolves_to_that_category():
    assert resolve_series("INFLATION") == CATEGORIES["INFLATION"]


def test_a_subcategory_name_resolves_without_naming_its_parent():
    assert resolve_series("CPI") == SUBCATEGORIES["INFLATION"]["CPI"]


def test_a_list_merges_mixed_tokens():
    out = resolve_series(["CPI", "CPIAUCSL"])
    assert "CPIAUCSL" in out
    for key in SUBCATEGORIES["INFLATION"]["CPI"]:
        assert key in out


def test_resolution_is_case_insensitive():
    assert resolve_series("inflation") == CATEGORIES["INFLATION"]


def test_an_unknown_token_raises_with_a_pointer_to_the_discovery_helpers():
    with pytest.raises(KeyError, match="available"):
        resolve_series("NOT_A_REAL_TOKEN")


def test_a_wrong_type_raises_TypeError():
    with pytest.raises(TypeError):
        resolve_series(42)


# ── Config accepts the widened input ─────────────────────────────────────


def test_config_accepts_a_category_string(tmp_path):
    cfg = Config("out.csv", tmp_path, series="INFLATION")
    assert cfg.SERIES == CATEGORIES["INFLATION"]


def test_config_default_is_the_whole_catalog(tmp_path):
    """It used to store None here, which made a downstream check read every
    default pull as a custom subset and print a message saying so."""
    cfg = Config("out.csv", tmp_path)
    assert cfg.SERIES == ALL_SERIES


def test_config_still_accepts_a_dict(tmp_path):
    custom = {"CPIAUCSL": ("Headline_CPI", "M")}
    cfg = Config("out.csv", tmp_path, series=custom)
    assert cfg.SERIES == custom


# ── the printing helpers say something true ──────────────────────────────


def test_available_lists_every_category(capsys):
    available()
    out = capsys.readouterr().out
    for cat in CATEGORIES:
        assert cat in out


def test_available_drills_into_a_category(capsys):
    available("INFLATION")
    out = capsys.readouterr().out
    assert "Category: INFLATION" in out
    assert "CPIAUCSL" in out


def test_available_drills_into_a_subcategory(capsys):
    available("CPI")
    out = capsys.readouterr().out
    assert "Subcategory: CPI" in out


def test_available_says_so_when_a_name_is_unknown(capsys):
    available("NOT_A_CATEGORY")
    assert "not found" in capsys.readouterr().out


def test_search_matches_the_friendly_name(capsys):
    hits = search("headline")
    capsys.readouterr()
    assert "CPIAUCSL" in hits


def test_search_matches_the_fred_id(capsys):
    hits = search("CPIAUCSL")
    capsys.readouterr()
    assert "CPIAUCSL" in hits


def test_search_returns_empty_and_says_so_when_nothing_matches(capsys):
    hits = search("zzzznotathing")
    assert hits == []
    assert "No series matching" in capsys.readouterr().out


def test_info_reports_the_series_with_its_frequency_and_lineage(capsys):
    info("CPIAUCSL")
    out = capsys.readouterr().out
    assert "CPIAUCSL" in out
    assert "Headline_CPI" in out
    assert "INFLATION" in out          # its category
    assert "CPI" in out                # its subcategory
    assert "monthly" in out            # freq code M decoded
    assert "fred.stlouisfed.org" in out


def test_info_says_so_when_the_series_is_unknown(capsys):
    info("NOT_A_SERIES")
    assert "not found" in capsys.readouterr().out
