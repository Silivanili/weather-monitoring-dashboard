"""Fallback and asset delivery for the JavaScript-powered location search."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_loads_async_search_script():
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="location-search-form"' in response.text
    assert 'id="location-results"' in response.text
    assert "/static/js/dashboard.js" in response.text
    assert 'data-latitude="46.84986"' in response.text

    script = client.get("/static/js/dashboard.js")
    assert script.status_code == 200
    assert "fetch(`/api/locations/search?q=${encodeURIComponent(query)}`" in script.text
    assert "history.pushState(" in script.text


def test_location_search_still_works_without_javascript(monkeypatch):
    def fake_search(query):
        assert query == "Chur"
        return [
            {
                "name": "Chur",
                "country": "Schweiz",
                "latitude": 46.85,
                "longitude": 9.53,
            }
        ]

    monkeypatch.setattr("app.web.routes.search_locations", fake_search)
    response = client.get("/", params={"q": "Chur"})
    assert response.status_code == 200
    assert "Chur, Schweiz</a>" in response.text
    assert "/?latitude=46.85&amp;longitude=9.53" in response.text


def test_direct_location_url_remains_valid():
    response = client.get("/", params={"latitude": 47.1, "longitude": 8.5})
    assert response.status_code == 200
    assert 'data-latitude="47.1"' in response.text
    assert 'data-longitude="8.5"' in response.text


def test_location_autocomplete_is_accessible_and_keeps_noscript_fallback():
    response = client.get("/")
    assert response.status_code == 200
    assert 'role="combobox"' in response.text
    assert 'aria-autocomplete="list"' in response.text
    assert 'aria-expanded="false"' in response.text
    assert 'role="listbox"' in response.text
    assert 'autocomplete="off"' in response.text
    assert '<noscript><button type="submit">Suchen</button></noscript>' in response.text
    assert '<button type="submit">Suchen</button>' not in response.text.replace(
        '<noscript><button type="submit">Suchen</button></noscript>', ""
    )


def test_autocomplete_script_has_debounce_and_keyboard_support():
    script = client.get("/static/js/dashboard.js")
    assert script.status_code == 200
    assert "SEARCH_DELAY_MS = 300" in script.text
    assert 'searchInput.addEventListener("input", queueLocationSearch)' in script.text
    assert 'event.key === "ArrowDown"' in script.text
    assert 'event.key === "ArrowUp"' in script.text
    assert 'event.key === "Escape"' in script.text
    assert "request.signal.aborted || activeSearchRequest !== request" in script.text


def test_location_picker_sits_next_to_branding_in_header():
    """The weather panels should start immediately after the compact header."""
    response = client.get("/")
    assert response.status_code == 200
    header = response.text.split('<header class="site-header">', 1)[1].split("</header>", 1)[0]
    main = response.text.split('<main class="container dashboard"', 1)[1]
    assert '<div class="container header-layout">' in header
    assert '<div class="header-branding">' in header
    assert "<h1>Weather Dashboard</h1>" in header
    assert "Wetterdaten und Prognosen" in header
    assert '<section class="search-section"' in header
    assert 'id="location-search-form"' in header
    assert 'id="location-results"' in header
    assert '<section class="search-section"' not in main
    assert 'class="current-weather-section"' in main


def test_header_location_search_has_responsive_styling():
    stylesheet = client.get("/static/css/styles.css")
    assert stylesheet.status_code == 200
    assert ".header-layout" in stylesheet.text
    assert "display: flex;" in stylesheet.text
    assert "justify-content: space-between;" in stylesheet.text
    assert "@media (max-width: 980px)" in stylesheet.text
    assert ".site-header .search-feedback:empty { display: block; }" in stylesheet.text
    assert ".location-results" in stylesheet.text


def test_current_weather_panel_uses_location_label_and_forecast_has_split_date_header():
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="current-location"' in response.text
    assert "current-location-heading" in response.text
    assert "Gefühlt" not in response.text

    stylesheet = client.get("/static/css/styles.css")
    assert ".forecast-day-header" in stylesheet.text
    assert ".forecast-weekday" in stylesheet.text
    assert ".forecast-date" in stylesheet.text
    assert ".forecast-stats" in stylesheet.text
