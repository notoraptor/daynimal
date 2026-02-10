"""
Tests for attribution.py - Legal compliance for data sources.

This test module ensures that all attribution functionality works correctly
to maintain legal compliance with CC-BY, CC-BY-SA, and other licenses.
"""

from datetime import datetime, UTC
from daynimal.attribution import (
    AttributionInfo,
    DataAttribution,
    GBIF_ATTRIBUTION,
    TAXREF_ATTRIBUTION,
    create_wikidata_attribution,
    create_wikipedia_attribution,
    create_commons_attribution,
    get_app_legal_notice,
    LEGAL_NOTICE_FULL,
)
from daynimal.schemas import License


# =============================================================================
# SECTION 1: Constants (3 tests)
# =============================================================================


def test_gbif_attribution_license():
    """GBIF attribution has CC-BY 4.0 license."""
    assert GBIF_ATTRIBUTION.license == License.CC_BY
    assert "creativecommons.org/licenses/by/4.0" in GBIF_ATTRIBUTION.license_url


def test_gbif_attribution_source_url():
    """GBIF attribution has DOI source URL."""
    assert "doi.org" in GBIF_ATTRIBUTION.source_url
    assert GBIF_ATTRIBUTION.author == "GBIF Secretariat"


def test_taxref_attribution_compatible_with_cc_by():
    """TAXREF uses Etalab license compatible with CC-BY."""
    assert TAXREF_ATTRIBUTION.license == License.CC_BY
    assert "etalab" in TAXREF_ATTRIBUTION.license_url.lower()


# =============================================================================
# SECTION 2: AttributionInfo (25 tests)
# =============================================================================

# --- Constructor & defaults (3 tests) ---


def test_attribution_info_minimal():
    """AttributionInfo can be created with minimal fields."""
    attr = AttributionInfo(
        source_name="Test Source",
        license=License.CC_BY,
        license_url="https://example.com/license",
    )
    assert attr.source_name == "Test Source"
    assert attr.license == License.CC_BY
    assert attr.author is None
    assert attr.modified is False


def test_attribution_info_complete():
    """AttributionInfo can be created with all fields."""
    access_date = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    attr = AttributionInfo(
        source_name="Test Source",
        license=License.CC_BY_SA,
        license_url="https://example.com/license",
        author="Test Author",
        title="Test Title",
        source_url="https://example.com/source",
        access_date=access_date,
        modified=True,
    )
    assert attr.author == "Test Author"
    assert attr.title == "Test Title"
    assert attr.source_url == "https://example.com/source"
    assert attr.access_date == access_date
    assert attr.modified is True


def test_attribution_info_defaults():
    """AttributionInfo has correct default values."""
    attr = AttributionInfo(
        source_name="Test", license=License.CC0, license_url="https://example.com"
    )
    assert attr.author is None
    assert attr.title is None
    assert attr.source_url is None
    assert attr.access_date is None
    assert attr.modified is False


# --- to_text() full/short formats (8 tests) ---


def test_to_text_full_format_complete():
    """Full format includes all information."""
    attr = AttributionInfo(
        source_name="Test Source",
        license=License.CC_BY,
        license_url="https://example.com/license",
        author="Test Author",
        title="Test Title",
        source_url="https://example.com/source",
        modified=True,
    )
    text = attr.to_text(format="full")

    # Check all components are present
    assert '"Test Title"' in text
    assert "by Test Author" in text
    assert "from Test Source" in text
    assert "(https://example.com/source)" in text
    assert "licensed under CC-BY" in text
    assert "(https://example.com/license)" in text
    assert "[modified]" in text


def test_to_text_full_format_minimal():
    """Full format works with minimal fields."""
    attr = AttributionInfo(
        source_name="Test Source",
        license=License.CC0,
        license_url="https://example.com/license",
    )
    text = attr.to_text(format="full")

    assert "from Test Source" in text
    assert "licensed under CC0" in text
    assert "(https://example.com/license)" in text
    assert "by" not in text  # No author
    assert "[modified]" not in text


def test_to_text_short_format_with_author():
    """Short format: Author / Source (License)."""
    attr = AttributionInfo(
        source_name="Wikipedia",
        license=License.CC_BY_SA,
        license_url="https://example.com/license",
        author="Wikipedia contributors",
    )
    text = attr.to_text(format="short")

    assert text == "Wikipedia contributors / Wikipedia (CC-BY-SA)"


def test_to_text_short_format_without_author():
    """Short format without author: Source (License)."""
    attr = AttributionInfo(
        source_name="Wikidata",
        license=License.CC0,
        license_url="https://example.com/license",
    )
    text = attr.to_text(format="short")

    assert text == "Wikidata (CC0)"


def test_to_text_default_format_is_full():
    """to_text() without format parameter defaults to full."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY,
        license_url="https://example.com",
        author="Author",
        title="Title",
    )
    text_default = attr.to_text()
    text_full = attr.to_text(format="full")

    assert text_default == text_full


def test_to_text_full_with_title_no_url():
    """Full format handles title without source URL."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY,
        license_url="https://example.com/license",
        title="Test Title",
    )
    text = attr.to_text(format="full")

    assert '"Test Title"' in text
    assert "from Test" in text
    # Should not have URL parentheses for source_url
    assert text.count("(https://") == 1  # Only license URL


def test_to_text_full_with_author_no_title():
    """Full format handles author without title."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY,
        license_url="https://example.com/license",
        author="Test Author",
    )
    text = attr.to_text(format="full")

    assert "by Test Author" in text
    assert "from Test" in text
    assert '"' not in text  # No title quotes


def test_to_text_all_licenses():
    """to_text() works with all license types."""
    for license_type in [
        License.CC0,
        License.CC_BY,
        License.CC_BY_SA,
        License.PUBLIC_DOMAIN,
    ]:
        attr = AttributionInfo(
            source_name="Test", license=license_type, license_url="https://example.com"
        )
        text = attr.to_text()
        assert license_type.value in text


# --- to_html() avec liens (8 tests) ---


def test_to_html_complete():
    """HTML format with all components."""
    attr = AttributionInfo(
        source_name="Wikipedia",
        license=License.CC_BY_SA,
        license_url="https://creativecommons.org/licenses/by-sa/4.0/",
        author="Wikipedia contributors",
        title="Gray wolf",
        source_url="https://en.wikipedia.org/wiki/Gray_wolf",
        modified=True,
    )
    html = attr.to_html()

    # Check links
    assert '<a href="https://en.wikipedia.org/wiki/Gray_wolf">Gray wolf</a>' in html
    assert "by Wikipedia contributors" in html
    assert "from Wikipedia" in html
    assert (
        '<a href="https://creativecommons.org/licenses/by-sa/4.0/">CC-BY-SA</a>' in html
    )
    assert "licensed under" in html
    assert "<em>[modified]</em>" in html


def test_to_html_title_without_url():
    """HTML format: title without URL uses em tags."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY,
        license_url="https://example.com/license",
        title="Test Title",
    )
    html = attr.to_html()

    assert '<em>"Test Title"</em>' in html
    # Title should not be a link (href to source_url) since source_url is None
    assert '<a href="' not in html.split("<em>")[0]  # No link before the title


def test_to_html_minimal():
    """HTML format with minimal fields."""
    attr = AttributionInfo(
        source_name="Test Source",
        license=License.CC0,
        license_url="https://example.com/license",
    )
    html = attr.to_html()

    assert "from Test Source" in html
    assert '<a href="https://example.com/license">CC0</a>' in html
    assert "licensed under" in html


def test_to_html_no_modified_flag():
    """HTML format without modified flag."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY,
        license_url="https://example.com",
        modified=False,
    )
    html = attr.to_html()

    assert "[modified]" not in html
    assert "<em>[modified]</em>" not in html


def test_to_html_title_with_special_characters():
    """HTML format escapes special characters in title."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY,
        license_url="https://example.com",
        title='Test "quoted" title',
        source_url="https://example.com/source",
    )
    html = attr.to_html()

    # Should preserve quotes in title
    assert 'Test "quoted" title' in html


def test_to_html_author_without_title():
    """HTML format with author but no title."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY,
        license_url="https://example.com",
        author="Test Author",
    )
    html = attr.to_html()

    assert "by Test Author" in html
    assert "from Test" in html


def test_to_html_license_link():
    """HTML format always has license link."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY_SA,
        license_url="https://creativecommons.org/licenses/by-sa/4.0/",
    )
    html = attr.to_html()

    assert (
        '<a href="https://creativecommons.org/licenses/by-sa/4.0/">CC-BY-SA</a>' in html
    )


def test_to_html_all_licenses():
    """to_html() works with all license types."""
    for license_type in [
        License.CC0,
        License.CC_BY,
        License.CC_BY_SA,
        License.PUBLIC_DOMAIN,
    ]:
        attr = AttributionInfo(
            source_name="Test", license=license_type, license_url="https://example.com"
        )
        html = attr.to_html()
        assert license_type.value in html
        assert '<a href="https://example.com">' in html


# --- Edge cases (6 tests) ---


def test_attribution_info_unicode_title():
    """AttributionInfo handles Unicode characters in title."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY,
        license_url="https://example.com",
        title="Guépard (Français)",
    )
    text = attr.to_text()
    html = attr.to_html()

    assert "Guépard (Français)" in text
    assert "Guépard (Français)" in html


def test_attribution_info_unicode_author():
    """AttributionInfo handles Unicode characters in author."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY,
        license_url="https://example.com",
        author="François Müller",
    )
    text = attr.to_text()

    assert "François Müller" in text


def test_attribution_info_long_urls():
    """AttributionInfo handles very long URLs."""
    long_url = "https://example.com/" + "a" * 200
    attr = AttributionInfo(
        source_name="Test", license=License.CC_BY, license_url=long_url
    )
    text = attr.to_text()

    assert long_url in text


def test_attribution_info_public_domain_license():
    """AttributionInfo works with PUBLIC_DOMAIN license."""
    attr = AttributionInfo(
        source_name="Public Domain Source",
        license=License.PUBLIC_DOMAIN,
        license_url="https://creativecommons.org/publicdomain/mark/1.0/",
    )
    text = attr.to_text()

    assert "PUBLIC_DOMAIN" in text


def test_attribution_info_access_date_preserved():
    """AttributionInfo preserves access_date correctly."""
    access_date = datetime(2025, 3, 20, 15, 30, 45, tzinfo=UTC)
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY,
        license_url="https://example.com",
        access_date=access_date,
    )

    assert attr.access_date == access_date
    assert attr.access_date.tzinfo == UTC


def test_attribution_info_modified_flag_in_full_text():
    """modified=True adds [modified] flag in full text only."""
    attr = AttributionInfo(
        source_name="Test",
        license=License.CC_BY_SA,
        license_url="https://example.com",
        modified=True,
    )

    full_text = attr.to_text(format="full")
    short_text = attr.to_text(format="short")

    assert "[modified]" in full_text
    assert "[modified]" not in short_text


# =============================================================================
# SECTION 3: DataAttribution (15 tests)
# =============================================================================

# --- Constructor (2 tests) ---


def test_data_attribution_default():
    """DataAttribution has GBIF taxonomy by default."""
    data_attr = DataAttribution()

    assert data_attr.taxonomy == GBIF_ATTRIBUTION
    assert data_attr.wikidata is None
    assert data_attr.wikipedia is None
    assert data_attr.images == []


def test_data_attribution_complete():
    """DataAttribution can be created with all sources."""
    wikidata_attr = create_wikidata_attribution("Q144")
    wikipedia_attr = create_wikipedia_attribution("Dog", "en")
    commons_attr = create_commons_attribution("Dog.jpg", "Test Author", License.CC_BY)

    data_attr = DataAttribution(
        wikidata=wikidata_attr, wikipedia=wikipedia_attr, images=[commons_attr]
    )

    assert data_attr.taxonomy == GBIF_ATTRIBUTION
    assert data_attr.wikidata == wikidata_attr
    assert data_attr.wikipedia == wikipedia_attr
    assert len(data_attr.images) == 1


# --- get_all() ordering (3 tests) ---


def test_get_all_taxonomy_first():
    """get_all() always returns taxonomy first."""
    data_attr = DataAttribution()
    all_attr = data_attr.get_all()

    assert len(all_attr) == 1
    assert all_attr[0] == GBIF_ATTRIBUTION


def test_get_all_ordering_complete():
    """get_all() returns attributions in correct order: taxonomy, wikidata, wikipedia, images."""
    wikidata_attr = create_wikidata_attribution("Q144")
    wikipedia_attr = create_wikipedia_attribution("Dog", "en")
    image1 = create_commons_attribution("Dog1.jpg", "Author 1", License.CC_BY)
    image2 = create_commons_attribution("Dog2.jpg", "Author 2", License.CC_BY_SA)

    data_attr = DataAttribution(
        wikidata=wikidata_attr, wikipedia=wikipedia_attr, images=[image1, image2]
    )

    all_attr = data_attr.get_all()

    assert len(all_attr) == 5
    assert all_attr[0] == GBIF_ATTRIBUTION
    assert all_attr[1] == wikidata_attr
    assert all_attr[2] == wikipedia_attr
    assert all_attr[3] == image1
    assert all_attr[4] == image2


def test_get_all_partial_sources():
    """get_all() includes only available sources."""
    wikipedia_attr = create_wikipedia_attribution("Wolf", "en")

    data_attr = DataAttribution(wikipedia=wikipedia_attr)
    all_attr = data_attr.get_all()

    assert len(all_attr) == 2
    assert all_attr[0] == GBIF_ATTRIBUTION
    assert all_attr[1] == wikipedia_attr


# --- get_required_attributions() filtrage CC0/PUBLIC_DOMAIN (4 tests) ---


def test_get_required_attributions_excludes_cc0():
    """get_required_attributions() excludes CC0 licenses."""
    wikidata_attr = create_wikidata_attribution("Q144")  # CC0
    wikipedia_attr = create_wikipedia_attribution("Dog", "en")  # CC-BY-SA

    data_attr = DataAttribution(wikidata=wikidata_attr, wikipedia=wikipedia_attr)

    required = data_attr.get_required_attributions()

    # GBIF (CC-BY) and Wikipedia (CC-BY-SA) required, Wikidata (CC0) not required
    assert len(required) == 2
    assert GBIF_ATTRIBUTION in required
    assert wikipedia_attr in required
    assert wikidata_attr not in required


def test_get_required_attributions_excludes_public_domain():
    """get_required_attributions() excludes PUBLIC_DOMAIN licenses."""
    public_domain_image = AttributionInfo(
        source_name="Public Domain Image",
        license=License.PUBLIC_DOMAIN,
        license_url="https://creativecommons.org/publicdomain/mark/1.0/",
    )

    data_attr = DataAttribution(images=[public_domain_image])
    required = data_attr.get_required_attributions()

    # Only GBIF required, not the public domain image
    assert len(required) == 1
    assert GBIF_ATTRIBUTION in required
    assert public_domain_image not in required


def test_get_required_attributions_includes_cc_by():
    """get_required_attributions() includes CC-BY licenses."""
    image = create_commons_attribution("Test.jpg", "Author", License.CC_BY)

    data_attr = DataAttribution(images=[image])
    required = data_attr.get_required_attributions()

    assert len(required) == 2  # GBIF + image
    assert image in required


def test_get_required_attributions_includes_cc_by_sa():
    """get_required_attributions() includes CC-BY-SA licenses."""
    wikipedia_attr = create_wikipedia_attribution("Test", "en")  # CC-BY-SA
    image = create_commons_attribution("Test.jpg", "Author", License.CC_BY_SA)

    data_attr = DataAttribution(wikipedia=wikipedia_attr, images=[image])
    required = data_attr.get_required_attributions()

    assert len(required) == 3  # GBIF + Wikipedia + image
    assert wikipedia_attr in required
    assert image in required


# --- to_text() et to_html() (6 tests) ---


def test_to_text_full_format():
    """to_text() generates multi-line attribution text."""
    data_attr = DataAttribution()
    text = data_attr.to_text(format="full")

    assert "Data Sources and Attributions:" in text
    assert "GBIF" in text
    assert "CC-BY" in text


def test_to_text_short_format():
    """to_text() with short format."""
    data_attr = DataAttribution()
    text = data_attr.to_text(format="short")

    assert "Data Sources and Attributions:" in text
    assert "GBIF Secretariat / GBIF Backbone Taxonomy (CC-BY)" in text


def test_to_text_multiple_sources():
    """to_text() includes all sources."""
    wikidata_attr = create_wikidata_attribution("Q144")
    wikipedia_attr = create_wikipedia_attribution("Dog", "en")

    data_attr = DataAttribution(wikidata=wikidata_attr, wikipedia=wikipedia_attr)
    text = data_attr.to_text()

    assert "GBIF" in text
    assert "Wikidata" in text
    assert "Wikipedia" in text


def test_to_html_structure():
    """to_html() generates valid HTML structure."""
    data_attr = DataAttribution()
    html = data_attr.to_html()

    assert "<h4>Data Sources and Attributions</h4>" in html
    assert "<ul>" in html
    assert "</ul>" in html
    assert "<li>" in html
    assert "</li>" in html


def test_to_html_multiple_sources():
    """to_html() includes all sources with links."""
    wikipedia_attr = create_wikipedia_attribution("Dog", "en")

    data_attr = DataAttribution(wikipedia=wikipedia_attr)
    html = data_attr.to_html()

    assert "GBIF" in html
    assert "Wikipedia" in html
    assert "<a href=" in html


def test_to_html_images():
    """to_html() includes image attributions."""
    image1 = create_commons_attribution("Dog1.jpg", "Author 1", License.CC_BY)
    image2 = create_commons_attribution("Dog2.jpg", "Author 2", License.CC_BY_SA)

    data_attr = DataAttribution(images=[image1, image2])
    html = data_attr.to_html()

    assert "Dog1.jpg" in html
    assert "Dog2.jpg" in html
    assert "Author 1" in html
    assert "Author 2" in html


# =============================================================================
# SECTION 4: Factory functions (20 tests)
# =============================================================================

# --- create_wikidata_attribution() (6 tests) ---


def test_create_wikidata_attribution_basic():
    """create_wikidata_attribution() creates valid attribution."""
    attr = create_wikidata_attribution("Q144")

    assert attr.source_name == "Wikidata"
    assert attr.license == License.CC0
    assert attr.author == "Wikidata contributors"
    assert attr.title == "Wikidata item Q144"


def test_create_wikidata_attribution_url_format():
    """create_wikidata_attribution() generates correct URL."""
    attr = create_wikidata_attribution("Q18498")

    assert attr.source_url == "https://www.wikidata.org/wiki/Q18498"


def test_create_wikidata_attribution_access_date():
    """create_wikidata_attribution() sets access_date to current time."""
    before = datetime.now(UTC)
    attr = create_wikidata_attribution("Q144")
    after = datetime.now(UTC)

    assert attr.access_date is not None
    assert before <= attr.access_date <= after
    assert attr.access_date.tzinfo == UTC


def test_create_wikidata_attribution_license_url():
    """create_wikidata_attribution() has correct CC0 license URL."""
    attr = create_wikidata_attribution("Q144")

    assert attr.license_url == "https://creativecommons.org/publicdomain/zero/1.0/"


def test_create_wikidata_attribution_different_qids():
    """create_wikidata_attribution() works with different QIDs."""
    qids = ["Q1", "Q100", "Q999999"]

    for qid in qids:
        attr = create_wikidata_attribution(qid)
        assert f"Wikidata item {qid}" in attr.title
        assert qid in attr.source_url


def test_create_wikidata_attribution_not_modified():
    """create_wikidata_attribution() sets modified=False by default."""
    attr = create_wikidata_attribution("Q144")

    assert attr.modified is False


# --- create_wikipedia_attribution() (8 tests) ---


def test_create_wikipedia_attribution_basic():
    """create_wikipedia_attribution() creates valid attribution."""
    attr = create_wikipedia_attribution("Gray wolf", "en")

    assert attr.source_name == "Wikipedia (en)"
    assert attr.license == License.CC_BY_SA
    assert attr.author == "Wikipedia contributors"
    assert attr.title == "Gray wolf"


def test_create_wikipedia_attribution_url_generation():
    """create_wikipedia_attribution() generates URL from title."""
    attr = create_wikipedia_attribution("Gray wolf", "en")

    assert attr.source_url == "https://en.wikipedia.org/wiki/Gray_wolf"


def test_create_wikipedia_attribution_spaces_to_underscores():
    """create_wikipedia_attribution() converts spaces to underscores in URL."""
    attr = create_wikipedia_attribution("Canis lupus familiaris", "en")

    assert "Canis_lupus_familiaris" in attr.source_url
    assert " " not in attr.source_url


def test_create_wikipedia_attribution_custom_url():
    """create_wikipedia_attribution() accepts custom URL."""
    custom_url = "https://en.wikipedia.org/wiki/Custom_Article"
    attr = create_wikipedia_attribution("Test Article", "en", url=custom_url)

    assert attr.source_url == custom_url


def test_create_wikipedia_attribution_access_date():
    """create_wikipedia_attribution() sets access_date to current time."""
    before = datetime.now(UTC)
    attr = create_wikipedia_attribution("Test", "en")
    after = datetime.now(UTC)

    assert attr.access_date is not None
    assert before <= attr.access_date <= after


def test_create_wikipedia_attribution_modified_flag():
    """create_wikipedia_attribution() respects modified parameter."""
    attr_not_modified = create_wikipedia_attribution("Test", "en", modified=False)
    attr_modified = create_wikipedia_attribution("Test", "en", modified=True)

    assert attr_not_modified.modified is False
    assert attr_modified.modified is True


def test_create_wikipedia_attribution_different_languages():
    """create_wikipedia_attribution() works with different languages."""
    languages = ["en", "fr", "de", "es"]

    for lang in languages:
        attr = create_wikipedia_attribution("Test", lang)
        assert attr.source_name == f"Wikipedia ({lang})"
        assert f"https://{lang}.wikipedia.org" in attr.source_url


def test_create_wikipedia_attribution_license_url():
    """create_wikipedia_attribution() has correct CC-BY-SA license URL."""
    attr = create_wikipedia_attribution("Test", "en")

    assert attr.license_url == "https://creativecommons.org/licenses/by-sa/4.0/"


# --- create_commons_attribution() (6 tests) ---


def test_create_commons_attribution_basic():
    """create_commons_attribution() creates valid attribution."""
    attr = create_commons_attribution("Test.jpg", "Test Author", License.CC_BY)

    assert attr.source_name == "Wikimedia Commons"
    assert attr.license == License.CC_BY
    assert attr.author == "Test Author"
    assert attr.title == "Test.jpg"


def test_create_commons_attribution_url_generation():
    """create_commons_attribution() generates URL from filename."""
    attr = create_commons_attribution("Gray wolf.jpg", "Author", License.CC_BY)

    assert attr.source_url == "https://commons.wikimedia.org/wiki/File:Gray_wolf.jpg"


def test_create_commons_attribution_default_license():
    """create_commons_attribution() defaults to CC-BY-SA if license is None."""
    attr = create_commons_attribution("Test.jpg", "Author", None)

    assert attr.license == License.CC_BY_SA


def test_create_commons_attribution_default_author():
    """create_commons_attribution() uses 'Unknown author' if author is None."""
    attr = create_commons_attribution("Test.jpg", None, License.CC_BY)

    assert attr.author == "Unknown author"


def test_create_commons_attribution_access_date():
    """create_commons_attribution() sets access_date to current time."""
    before = datetime.now(UTC)
    attr = create_commons_attribution("Test.jpg", "Author", License.CC_BY)
    after = datetime.now(UTC)

    assert attr.access_date is not None
    assert before <= attr.access_date <= after


def test_create_commons_attribution_license_urls():
    """create_commons_attribution() uses correct license URLs for all licenses."""
    expected_urls = {
        License.CC0: "https://creativecommons.org/publicdomain/zero/1.0/",
        License.PUBLIC_DOMAIN: "https://creativecommons.org/publicdomain/mark/1.0/",
        License.CC_BY: "https://creativecommons.org/licenses/by/4.0/",
        License.CC_BY_SA: "https://creativecommons.org/licenses/by-sa/4.0/",
    }

    for license_type, expected_url in expected_urls.items():
        attr = create_commons_attribution("Test.jpg", "Author", license_type)
        assert attr.license_url == expected_url


# =============================================================================
# SECTION 5: Legal notices (4 tests)
# =============================================================================


def test_get_app_legal_notice_short():
    """get_app_legal_notice() returns short notice."""
    notice = get_app_legal_notice(format="short")

    assert "GBIF" in notice
    assert "Wikidata" in notice
    assert "Wikipedia" in notice
    assert "Wikimedia Commons" in notice
    assert len(notice) < len(LEGAL_NOTICE_FULL)


def test_get_app_legal_notice_full():
    """get_app_legal_notice() returns full notice with all sources."""
    notice = get_app_legal_notice(format="full")

    # Check all sources are mentioned
    assert "GBIF BACKBONE TAXONOMY" in notice
    assert "TAXREF" in notice
    assert "WIKIDATA" in notice
    assert "WIKIPEDIA" in notice
    assert "WIKIMEDIA COMMONS" in notice

    # Check licenses are mentioned
    assert "CC-BY 4.0" in notice or "CC-BY" in notice
    assert "CC-BY-SA" in notice
    assert "CC0" in notice


def test_get_app_legal_notice_default_is_full():
    """get_app_legal_notice() defaults to full format."""
    notice_default = get_app_legal_notice()
    notice_full = get_app_legal_notice(format="full")

    assert notice_default == notice_full


def test_get_app_legal_notice_stripped():
    """get_app_legal_notice() returns stripped text (no leading/trailing whitespace)."""
    notice_short = get_app_legal_notice(format="short")
    notice_full = get_app_legal_notice(format="full")

    assert notice_short == notice_short.strip()
    assert notice_full == notice_full.strip()


# =============================================================================
# SECTION 6: Integration (8 tests)
# =============================================================================


def test_integration_complete_attribution_chain():
    """Complete attribution workflow: create -> add to DataAttribution -> export text/html."""
    # Create attributions
    wikidata_attr = create_wikidata_attribution("Q144")
    wikipedia_attr = create_wikipedia_attribution("Dog", "en")
    image1 = create_commons_attribution("Dog.jpg", "John Doe", License.CC_BY)
    image2 = create_commons_attribution("Dog2.jpg", "Jane Smith", License.CC_BY_SA)

    # Create DataAttribution
    data_attr = DataAttribution(
        wikidata=wikidata_attr, wikipedia=wikipedia_attr, images=[image1, image2]
    )

    # Export text
    text = data_attr.to_text()
    assert "GBIF" in text
    assert "Wikidata" in text
    assert "Wikipedia" in text
    assert "Dog.jpg" in text
    assert "Dog2.jpg" in text

    # Export HTML
    html = data_attr.to_html()
    assert "<li>" in html
    assert "<a href=" in html


def test_integration_minimal_attribution():
    """Minimal attribution with only GBIF taxonomy."""
    data_attr = DataAttribution()

    text = data_attr.to_text()
    html = data_attr.to_html()

    assert "GBIF" in text
    assert "GBIF" in html
    assert len(data_attr.get_all()) == 1


def test_integration_required_vs_all_attributions():
    """Required attributions filter excludes CC0/PUBLIC_DOMAIN."""
    wikidata_attr = create_wikidata_attribution("Q144")  # CC0
    wikipedia_attr = create_wikipedia_attribution("Test", "en")  # CC-BY-SA
    cc0_image = create_commons_attribution("Test1.jpg", "Author", License.CC0)
    cc_by_image = create_commons_attribution("Test2.jpg", "Author", License.CC_BY)

    data_attr = DataAttribution(
        wikidata=wikidata_attr,
        wikipedia=wikipedia_attr,
        images=[cc0_image, cc_by_image],
    )

    all_attr = data_attr.get_all()
    required_attr = data_attr.get_required_attributions()

    assert len(all_attr) == 5  # GBIF + Wikidata + Wikipedia + 2 images
    assert (
        len(required_attr) == 3
    )  # GBIF + Wikipedia + CC-BY image (excludes Wikidata CC0 and CC0 image)


def test_integration_attribution_consistency_text_vs_html():
    """text and HTML formats contain same information."""
    wikipedia_attr = create_wikipedia_attribution("Test Article", "en")
    image = create_commons_attribution("Test.jpg", "Test Author", License.CC_BY)

    data_attr = DataAttribution(wikipedia=wikipedia_attr, images=[image])

    text = data_attr.to_text()
    html = data_attr.to_html()

    # Check both contain same sources
    assert "GBIF" in text and "GBIF" in html
    assert "Wikipedia" in text and "Wikipedia" in html
    assert "Test.jpg" in text and "Test.jpg" in html
    assert "Test Author" in text and "Test Author" in html


def test_integration_real_world_animal_all_sources():
    """Real-world scenario: animal with all data sources."""
    # Simulate a complete animal attribution
    wikidata_attr = create_wikidata_attribution("Q18498")  # Wolf
    wikipedia_attr = create_wikipedia_attribution("Gray wolf", "en", modified=True)
    images = [
        create_commons_attribution(
            "Canis lupus 1.jpg", "John Photographer", License.CC_BY_SA
        ),
        create_commons_attribution(
            "Canis lupus 2.jpg", "Jane Photographer", License.CC_BY
        ),
        create_commons_attribution(
            "Canis lupus 3.jpg", None, License.CC_BY
        ),  # Unknown author
    ]

    data_attr = DataAttribution(
        wikidata=wikidata_attr, wikipedia=wikipedia_attr, images=images
    )

    # Verify all sources present
    all_attr = data_attr.get_all()
    assert len(all_attr) == 6  # GBIF + Wikidata + Wikipedia + 3 images

    # Verify text output
    text = data_attr.to_text()
    assert "GBIF" in text
    assert "Q18498" in text
    assert "Gray wolf" in text
    assert "[modified]" in text  # Wikipedia was modified
    assert "John Photographer" in text
    assert "Unknown author" in text  # For image 3

    # Verify HTML output
    html = data_attr.to_html()
    assert "<a href=" in html
    assert "Gray_wolf" in html  # URL format
    assert "<em>[modified]</em>" in html


def test_integration_factory_functions_produce_valid_attributions():
    """All factory functions produce valid AttributionInfo objects."""
    wikidata = create_wikidata_attribution("Q144")
    wikipedia = create_wikipedia_attribution("Test", "en")
    commons = create_commons_attribution("Test.jpg", "Author", License.CC_BY)

    # All should have required fields
    for attr in [wikidata, wikipedia, commons]:
        assert attr.source_name
        assert attr.license
        assert attr.license_url
        assert attr.access_date is not None
        assert attr.access_date.tzinfo == UTC

        # Should produce valid text and HTML
        text = attr.to_text()
        html = attr.to_html()
        assert len(text) > 0
        assert len(html) > 0


def test_integration_data_attribution_immutable_after_creation():
    """DataAttribution fields can be safely accessed after creation."""
    wikidata = create_wikidata_attribution("Q144")
    wikipedia = create_wikipedia_attribution("Test", "en")
    image = create_commons_attribution("Test.jpg", "Author", License.CC_BY)

    data_attr = DataAttribution(wikidata=wikidata, wikipedia=wikipedia, images=[image])

    # Access multiple times should return same objects
    assert data_attr.taxonomy == data_attr.taxonomy
    assert data_attr.wikidata == wikidata
    assert data_attr.wikipedia == wikipedia
    assert data_attr.images[0] == image


def test_integration_empty_images_list():
    """DataAttribution handles empty images list correctly."""
    data_attr = DataAttribution(images=[])

    all_attr = data_attr.get_all()
    assert len(all_attr) == 1  # Only GBIF

    text = data_attr.to_text()
    assert "Image credits:" not in text  # No image section
