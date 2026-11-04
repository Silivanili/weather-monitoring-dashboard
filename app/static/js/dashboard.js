"use strict";

// JavaScript ersetzt nur die Daten; der Browser muss die Seite nicht neu laden.
const dashboard = document.querySelector(".dashboard");
const searchForm = document.getElementById("location-search-form");
const searchInput = document.getElementById("location");
const searchFeedback = document.getElementById("location-search-feedback");
const searchResults = document.getElementById("location-results");
const searchSection = document.querySelector(".search-section");
const SEARCH_DELAY_MS = 300;
let searchTimer = null;
let activeResultIndex = -1;
const weatherPanel = document.getElementById("current-weather-panel");
const forecastGrid = document.querySelector(".forecast-days-grid");
const forecastFeedback = document.getElementById("forecast-feedback");
const chartContainer = document.getElementById("forecast-chart");
const currentLocationElement = document.getElementById("current-location");

const initialCoordinates = {
    latitude: Number(dashboard.dataset.latitude),
    longitude: Number(dashboard.dataset.longitude)
};
const initialLocation = dashboard.dataset.locationName
    ? { name: dashboard.dataset.locationName, country: dashboard.dataset.locationCountry || "" }
    : null;

// Ortsnamen sind Metadaten aus der Suche; Wetterdaten werden separat abgerufen.
// sessionStorage uebersteht einen Reload im selben Browser-Tab.
const LOCATION_CACHE_KEY = "weather-dashboard:locations:v1";
const locationCache = new Map();

function coordinatesKey(latitude, longitude) {
    return `${latitude.toFixed(5)},${longitude.toFixed(5)}`;
}

try {
    if (typeof sessionStorage !== "undefined") {
        const saved = JSON.parse(sessionStorage.getItem(LOCATION_CACHE_KEY) || "[]");
        if (Array.isArray(saved)) {
            for (const [key, location] of saved) {
                if (typeof key === "string" && location && typeof location.name === "string"
                    && typeof location.country === "string") {
                    locationCache.set(key, location);
                }
            }
        }
    }
} catch (error) {
    // Eingeschraenkter oder defekter Browser-Speicher verhindert keine Wetteranzeige.
}

function cachedLocation(latitude, longitude) {
    return locationCache.get(coordinatesKey(latitude, longitude)) || null;
}

function rememberLocation(latitude, longitude, location) {
    if (!location || typeof location.name !== "string" || typeof location.country !== "string") return;
    const key = coordinatesKey(latitude, longitude);
    locationCache.delete(key);
    locationCache.set(key, { name: location.name, country: location.country });
    while (locationCache.size > 20) locationCache.delete(locationCache.keys().next().value);
    try {
        if (typeof sessionStorage !== "undefined") {
            sessionStorage.setItem(LOCATION_CACHE_KEY, JSON.stringify([...locationCache]));
        }
    } catch (error) {
        // Auch ohne persistierten Cache bleibt die aktuelle Auswahl im Speicher.
    }
}
let activeSearchRequest = null;
let activeWeatherRequest = null;
let activeForecastRequest = null;
let activeLocation = null;

// Dieselbe WMO-Wettercode-Zuordnung fuer aktuelle Werte und Tageskarten.
function getWeatherCondition(code) {
    if (code === 0) return { icon: "sun", text: "Sonnig" };
    if (code === 1 || code === 2) return { icon: "partly", text: "Teilweise bewölkt" };
    if (code === 3) return { icon: "cloud", text: "Bedeckt" };
    if (code === 45 || code === 48) return { icon: "fog", text: "Nebel" };
    if ([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(code)) {
        return { icon: "rain", text: "Regen" };
    }
    if ([71, 73, 75, 77, 85, 86].includes(code)) return { icon: "snow", text: "Schnee" };
    if ([95, 96, 99].includes(code)) return { icon: "storm", text: "Gewitter" };
    return { icon: "cloud", text: "Wetterlage unbekannt" };
}

const measurementFormat = new Intl.NumberFormat("de-CH", { maximumFractionDigits: 1 });
const forecastWeekdayFormat = new Intl.DateTimeFormat("de-CH", { weekday: "short" });
const forecastMonthShort = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];

function displayMeasurement(value) {
    if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) {
        return "--";
    }
    return measurementFormat.format(Number(value));
}

// Provider-Zeit ist lokal zum gewählten Ort (inklusive Offset).
function displayWeatherTime(value) {
    const match = typeof value === "string"
        ? value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/)
        : null;
    return match ? `${match[3]}.${match[2]}.${match[1]} · ${match[4]}:${match[5]}` : "--";
}

function displayLocation(location) {
    if (!location || (!location.name && !location.country)) {
        return "Standort wird geladen ...";
    }
    return [location.name, location.country].filter(Boolean).join(", ");
}

function setCurrentLocation(location) {
    activeLocation = location && (location.name || location.country) ? location : null;
    currentLocationElement.textContent = displayLocation(activeLocation);
}

function parseForecastDate(value) {
    const [year, month, day] = String(value).split("-").map(Number);
    return new Date(year, month - 1, day, 12, 0, 0);
}

function formatForecastWeekday(date) {
    return forecastWeekdayFormat.format(date).replace(/\.$/, "");
}

function formatForecastDate(date) {
    const day = String(date.getDate()).padStart(2, "0");
    return `${day}. ${forecastMonthShort[date.getMonth()]}`;
}

function isValidCoordinates(latitude, longitude) {
    return Number.isFinite(latitude) && Number.isFinite(longitude)
        && Math.abs(latitude) <= 90 && Math.abs(longitude) <= 180;
}

function weatherUrl(path, latitude, longitude) {
    const params = new URLSearchParams({ latitude: String(latitude), longitude: String(longitude) });
    return `${path}?${params}`;
}

function resetWeather(latitude, longitude, location = activeLocation) {
    weatherPanel.dataset.state = "loading";
    weatherPanel.setAttribute("aria-busy", "true");
    document.getElementById("weather-status").textContent = "DATEN LADEN";
    setCurrentLocation(location);
    if (!location) currentLocationElement.textContent = `${latitude.toFixed(3)}, ${longitude.toFixed(3)}`;
    for (const id of ["temperature", "precipitation", "humidity", "wind-speed", "weather-time", "weather-source"]) {
        document.getElementById(id).textContent = "--";
    }
    document.getElementById("weather-condition").textContent = "Wird geladen ...";
    document.getElementById("current-weather-icon").setAttribute("href", "#wx-cloud");
}

async function loadWeather(latitude, longitude, signal) {
    try {
        const response = await fetch(weatherUrl("/api/weather", latitude, longitude), { signal });
        if (!response.ok) throw new Error(`HTTP-Fehler: ${response.status}`);
        const data = await response.json();
        if (signal.aborted) return;

        const current = data.current;
        const meta = data.meta || {};
        const condition = getWeatherCondition(current.weather_code);
        // Ein vom Benutzer ausgewaehlter Ortsname hat Vorrang vor API-Metadaten.
        if (!activeLocation && data.location) {
            setCurrentLocation(data.location);
            rememberLocation(latitude, longitude, data.location);
        }
        document.getElementById("temperature").textContent = displayMeasurement(current.temperature_celsius);
        document.getElementById("precipitation").textContent = displayMeasurement(current.precipitation_mm);
        document.getElementById("humidity").textContent = displayMeasurement(current.relative_humidity_percent);
        document.getElementById("wind-speed").textContent = displayMeasurement(current.wind_speed_kmh);
        document.getElementById("weather-condition").textContent = condition.text;
        document.getElementById("current-weather-icon").setAttribute("href", `#wx-${condition.icon}`);
        document.getElementById("weather-source").textContent = meta.source || "--";
        document.getElementById("weather-time").textContent = displayWeatherTime(current.time);
        weatherPanel.dataset.state = meta.stale ? "stale" : meta.cached ? "cached" : "ready";
        document.getElementById("weather-status").textContent = meta.stale
            ? "VERALTETER CACHE" : meta.cached ? "AUS CACHE" : "AKTUELL";
    } catch (error) {
        if (signal.aborted) return;
        console.error("Aktuelles Wetter konnte nicht geladen werden:", error);
        weatherPanel.dataset.state = "error";
        document.getElementById("weather-condition").textContent = "Nicht verfügbar";
        document.getElementById("weather-status").textContent = "FEHLER";
    } finally {
        if (!signal.aborted) weatherPanel.setAttribute("aria-busy", "false");
    }
}

function resetForecast() {
    forecastGrid.replaceChildren();
    forecastFeedback.textContent = "Prognose wird geladen ...";
    if (typeof Plotly !== "undefined" && chartContainer.classList.contains("js-plotly-plot")) {
        Plotly.purge(chartContainer);
    }
    const placeholder = document.createElement("div");
    placeholder.className = "chart-placeholder";
    placeholder.textContent = "Diagramm wird geladen ...";
    chartContainer.replaceChildren(placeholder);
}

async function loadForecast(latitude, longitude, signal) {
    try {
        const response = await fetch(weatherUrl("/api/weather/forecast", latitude, longitude), { signal });
        if (!response.ok) throw new Error(`HTTP-Fehler: ${response.status}`);
        const data = await response.json();
        if (signal.aborted) return;

        const cards = document.createDocumentFragment();
        data.daily.forEach(day => {
            const card = document.createElement("article");
            card.classList.add("card", "forecast-day");

            const header = document.createElement("div");
            header.classList.add("forecast-day-header");
            const date = parseForecastDate(day.date);
            const weekday = document.createElement("p");
            weekday.classList.add("forecast-weekday");
            weekday.textContent = formatForecastWeekday(date);
            const dateLabel = document.createElement("p");
            dateLabel.classList.add("forecast-date");
            dateLabel.textContent = formatForecastDate(date);
            header.append(weekday, dateLabel);

            const weather = document.createElement("div");
            weather.classList.add("forecast-weather");
            const condition = getWeatherCondition(day.weather_code);
            const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            icon.classList.add("forecast-icon");
            icon.setAttribute("aria-hidden", "true");
            const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
            use.setAttribute("href", `#wx-${condition.icon}`);
            icon.appendChild(use);
            const description = document.createElement("span");
            description.classList.add("forecast-weather-text");
            description.textContent = condition.text;
            weather.append(icon, description);

            const stats = document.createElement("div");
            stats.classList.add("forecast-stats");

            const maxStat = document.createElement("div");
            maxStat.classList.add("forecast-stat");
            const maxLabel = document.createElement("span");
            maxLabel.classList.add("forecast-stat-label");
            maxLabel.textContent = "MAX";
            const maxTemperature = document.createElement("p");
            maxTemperature.classList.add("forecast-max");
            maxTemperature.textContent = `${displayMeasurement(day.temperature_max_celsius)} °C`;
            maxStat.append(maxLabel, maxTemperature);

            const minStat = document.createElement("div");
            minStat.classList.add("forecast-stat");
            const minLabel = document.createElement("span");
            minLabel.classList.add("forecast-stat-label");
            minLabel.textContent = "MIN";
            const minTemperature = document.createElement("p");
            minTemperature.classList.add("forecast-min");
            minTemperature.textContent = `${displayMeasurement(day.temperature_min_celsius)} °C`;
            minStat.append(minLabel, minTemperature);

            const rainStat = document.createElement("div");
            rainStat.classList.add("forecast-stat");
            rainStat.style.gridColumn = "1 / -1";
            const rainLabel = document.createElement("span");
            rainLabel.classList.add("forecast-stat-label");
            rainLabel.textContent = "REGENWAHRSCHEINLICHKEIT";
            const precipitation = document.createElement("p");
            precipitation.classList.add("forecast-rain");
            precipitation.textContent = `${displayMeasurement(day.precipitation_probability_percent)} %`;
            rainStat.append(rainLabel, precipitation);

            stats.append(maxStat, minStat, rainStat);
            card.append(header, weather, stats);
            cards.appendChild(card);
        });
        forecastGrid.replaceChildren(cards);
        forecastFeedback.textContent = "";

        if (typeof Plotly === "undefined") {
            const placeholder = chartContainer.querySelector(".chart-placeholder");
            if (placeholder) placeholder.textContent = "Diagramm momentan nicht verfügbar.";
            return;
        }
        const dates = data.daily.map(day => day.date);
        const dateLabels = dates.map(date => formatForecastDate(parseForecastDate(date)));
        const hoverDates = dates.map(date => {
            const parsed = parseForecastDate(date);
            return `${formatForecastWeekday(parsed)}, ${formatForecastDate(parsed)}`;
        });
        const maxTrace = {
            x: dates,
            y: data.daily.map(day => day.temperature_max_celsius),
            customdata: hoverDates,
            type: "scatter", mode: "lines+markers", name: "Höchsttemperatur",
            line: { color: "#FFAC7A", width: 4 },
            marker: { color: "#FFAC7A", size: 9, symbol: "square" },
            hovertemplate: "%{customdata}<br>Max: %{y:.1f} °C<extra></extra>"
        };
        const minTrace = {
            x: dates,
            y: data.daily.map(day => day.temperature_min_celsius),
            customdata: hoverDates,
            type: "scatter", mode: "lines+markers", name: "Tiefsttemperatur",
            line: { color: "#7ED1EB", width: 4 },
            marker: { color: "#7ED1EB", size: 9, symbol: "square" },
            hovertemplate: "%{customdata}<br>Min: %{y:.1f} °C<extra></extra>"
        };
        // Plotly erzeugt eine eigene SVG-Grafik: CSS allein faerbt den Plot nicht um.
        await Plotly.react(chartContainer, [maxTrace, minTrace], {
            autosize: true,
            paper_bgcolor: "#101A2F",
            plot_bgcolor: "#13243C",
            font: { family: '"Pixelify Sans", "Courier New", monospace', color: "#E8E5D5", size: 15 },
            margin: { l: 70, r: 24, t: 70, b: 64 },
            hovermode: "x unified",
            hoverlabel: {
                bgcolor: "#17243E",
                bordercolor: "#FFD66D",
                font: { color: "#E8E5D5", family: '"Pixelify Sans", "Courier New", monospace', size: 15 }
            },
            legend: {
                orientation: "h", x: 0, y: 1.13,
                bgcolor: "rgba(0,0,0,0)", font: { color: "#E8E5D5" }
            },
            xaxis: {
                type: "category", tickvals: dates, ticktext: dateLabels,
                title: { text: "DATUM", font: { color: "#9EB6D3" }, standoff: 14 },
                tickfont: { color: "#E8E5D5" },
                linecolor: "#425779", gridcolor: "#283A54", zeroline: false,
                showline: true, showgrid: true, tickangle: 0
            },
            yaxis: {
                title: { text: "TEMPERATUR (°C)", font: { color: "#9EB6D3" }, standoff: 8 },
                ticksuffix: "°", tickfont: { color: "#E8E5D5" },
                linecolor: "#425779", gridcolor: "#283A54", zerolinecolor: "#425779",
                showline: true, showgrid: true, showzeroline: true
            }
        }, { responsive: true, displaylogo: false, displayModeBar: false });
    } catch (error) {
        if (signal.aborted) return;
        console.error("Prognose konnte nicht geladen werden:", error);
        forecastFeedback.textContent = "Prognose momentan nicht verfügbar.";
        const placeholder = document.createElement("div");
        placeholder.className = "chart-placeholder";
        placeholder.textContent = "Diagramm momentan nicht verfügbar.";
        chartContainer.replaceChildren(placeholder);
    }
}

function loadLocation(latitude, longitude, location = activeLocation) {
    if (!isValidCoordinates(latitude, longitude)) return;
    // Alte Antworten duerfen die Ergebnisse des neu gewaehlten Orts nicht ueberschreiben.
    if (activeWeatherRequest) activeWeatherRequest.abort();
    if (activeForecastRequest) activeForecastRequest.abort();
    activeWeatherRequest = new AbortController();
    activeForecastRequest = new AbortController();
    const knownLocation = location || cachedLocation(latitude, longitude);
    if (knownLocation) rememberLocation(latitude, longitude, knownLocation);
    resetWeather(latitude, longitude, knownLocation);
    resetForecast();
    void loadWeather(latitude, longitude, activeWeatherRequest.signal);
    void loadForecast(latitude, longitude, activeForecastRequest.signal);
}

function addLocationResult(location, index) {
    const item = document.createElement("li");
    item.id = `location-option-${index}`;
    item.setAttribute("role", "option");
    item.setAttribute("aria-selected", "false");
    const link = document.createElement("a");
    const params = new URLSearchParams({
        latitude: String(location.latitude), longitude: String(location.longitude)
    });
    link.href = `/?${params}`; // Direkte URL und Link im No-JavaScript-Fallback.
    link.tabIndex = -1; // Tastatursteuerung erfolgt über das Eingabefeld.
    link.dataset.latitude = String(location.latitude);
    link.dataset.longitude = String(location.longitude);
    link.dataset.locationName = location.name;
    link.dataset.locationCountry = location.country;
    link.textContent = `${location.name}, ${location.country}`;
    const coordinates = document.createElement("span");
    coordinates.className = "location-result-coordinates";
    coordinates.textContent = `${location.latitude}, ${location.longitude}`;
    item.append(link, coordinates);
    return item;
}

function setActiveResult(index) {
    const items = [...searchResults.querySelectorAll('li[role="option"]')];
    if (items.length === 0) {
        activeResultIndex = -1;
        searchInput.removeAttribute("aria-activedescendant");
        return;
    }
    activeResultIndex = (index + items.length) % items.length;
    items.forEach((item, itemIndex) => {
        const isActive = itemIndex === activeResultIndex;
        item.classList.toggle("is-active", isActive);
        item.setAttribute("aria-selected", String(isActive));
    });
    searchInput.setAttribute("aria-activedescendant", items[activeResultIndex].id);
    items[activeResultIndex].scrollIntoView({ block: "nearest" });
}

function hideSuggestions({ clear = false } = {}) {
    searchResults.hidden = true;
    searchInput.setAttribute("aria-expanded", "false");
    searchInput.removeAttribute("aria-activedescendant");
    activeResultIndex = -1;
    if (clear) searchResults.replaceChildren();
}

function cancelPendingSearch() {
    if (searchTimer !== null) {
        clearTimeout(searchTimer);
        searchTimer = null;
    }
    if (activeSearchRequest) {
        activeSearchRequest.abort();
        activeSearchRequest = null;
    }
    searchForm.setAttribute("aria-busy", "false");
}

async function searchLocations(query) {
    cancelPendingSearch();
    const request = new AbortController();
    activeSearchRequest = request;
    searchForm.setAttribute("aria-busy", "true");
    searchFeedback.textContent = "Standorte werden gesucht ...";

    try {
        const response = await fetch(`/api/locations/search?q=${encodeURIComponent(query)}`, {
            signal: request.signal
        });
        if (!response.ok) throw new Error(`HTTP-Fehler: ${response.status}`);
        const locations = await response.json();
        // Ausstehende oder abgebrochene Antworten dürfen die Eingabe nicht überholen.
        if (request.signal.aborted || activeSearchRequest !== request || searchInput.value.trim() !== query) return;
        searchResults.replaceChildren(...locations.map(addLocationResult));
        searchResults.hidden = locations.length === 0;
        searchInput.setAttribute("aria-expanded", String(locations.length > 0));
        if (locations.length > 0) setActiveResult(0);
        searchFeedback.textContent = locations.length === 0 ? "Keine Standorte gefunden." : "";
    } catch (error) {
        if (request.signal.aborted || activeSearchRequest !== request) return;
        console.error("Standortsuche fehlgeschlagen:", error);
        hideSuggestions({ clear: true });
        searchFeedback.textContent = "Standortsuche momentan nicht verfügbar.";
    } finally {
        if (activeSearchRequest === request) {
            searchForm.setAttribute("aria-busy", "false");
            activeSearchRequest = null;
        }
    }
}

function queueLocationSearch() {
    cancelPendingSearch();
    hideSuggestions({ clear: true });
    const query = searchInput.value.trim();
    searchFeedback.textContent = "";
    if (query.length < 2) return;
    if (query.length > 100) {
        searchFeedback.textContent = "Bitte höchstens 100 Zeichen eingeben.";
        return;
    }
    // Debounce: erst nach einer Tipp-Pause wird der Geocoding-Dienst abgefragt.
    searchTimer = setTimeout(() => {
        searchTimer = null;
        void searchLocations(query);
    }, SEARCH_DELAY_MS);
}

function selectLocation(link) {
    const latitude = Number(link.dataset.latitude);
    const longitude = Number(link.dataset.longitude);
    if (!isValidCoordinates(latitude, longitude)) return false;
    cancelPendingSearch();
    hideSuggestions({ clear: true });
    const location = {
        name: link.dataset.locationName,
        country: link.dataset.locationCountry
    };
    history.pushState({ location }, "", link.href);
    searchInput.value = location.name;
    searchFeedback.textContent = `Standort ausgewählt: ${location.name}, ${location.country}.`;
    loadLocation(latitude, longitude, location);
    return true;
}

searchInput.addEventListener("input", queueLocationSearch);

searchInput.addEventListener("keydown", event => {
    if (event.key === "Escape") {
        cancelPendingSearch();
        hideSuggestions();
        searchFeedback.textContent = "";
        return;
    }
    if (searchResults.hidden || searchResults.children.length === 0) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        const step = event.key === "ArrowDown" ? 1 : -1;
        setActiveResult(activeResultIndex + step);
    }
});

// Enter waehlt den markierten (standardmaessig ersten) Vorschlag.
// Falls noch kein Vorschlag sichtbar ist, wird sofort gesucht.
searchForm.addEventListener("submit", event => {
    event.preventDefault();
    if (!searchResults.hidden && searchResults.children.length > 0) {
        const links = searchResults.querySelectorAll('li[role="option"] a');
        if (selectLocation(links[Math.max(activeResultIndex, 0)])) return;
    }
    const query = searchInput.value.trim();
    if (query.length < 2 || query.length > 100) {
        searchFeedback.textContent = "Bitte mindestens 2 und höchstens 100 Zeichen eingeben.";
        return;
    }
    void searchLocations(query);
});

searchResults.addEventListener("click", event => {
    const option = event.target.closest('li[role="option"]');
    const link = option?.querySelector("a[data-latitude][data-longitude]");
    if (!link || event.defaultPrevented || event.button !== 0 || event.ctrlKey
        || event.metaKey || event.altKey || event.shiftKey) return;
    if (selectLocation(link)) event.preventDefault();
});

// Klick ausserhalb / Tab aus dem Suchbereich schliesst die Vorschlagsliste.
document.addEventListener("pointerdown", event => {
    if (searchSection.contains(event.target)) return;
    cancelPendingSearch();
    hideSuggestions();
});
searchSection.addEventListener("focusout", () => {
    // Klicks auf die Liste erst vollenden lassen (besonders auf Touch-Geräten).
    setTimeout(() => {
        if (searchSection.contains(document.activeElement)) return;
        cancelPendingSearch();
        hideSuggestions();
    }, 0);
});

// Bei einer GET-Suche ohne JavaScript bleiben schon gerenderte Links verwendbar.
if (!searchResults.hidden && searchResults.children.length > 0) setActiveResult(0);

// Zurueck/Vorwaerts aktualisiert ebenfalls nur die Daten.
window.addEventListener("popstate", () => {
    const query = new URLSearchParams(window.location.search);
    const latitude = query.has("latitude") ? Number(query.get("latitude")) : initialCoordinates.latitude;
    const longitude = query.has("longitude") ? Number(query.get("longitude")) : initialCoordinates.longitude;
    const location = history.state?.location || cachedLocation(latitude, longitude);
    if (isValidCoordinates(latitude, longitude)) loadLocation(latitude, longitude, location);
    cancelPendingSearch();
    searchInput.value = history.state?.location?.name || query.get("q") || "";
    hideSuggestions({ clear: true });
    searchFeedback.textContent = "";
});

loadLocation(initialCoordinates.latitude, initialCoordinates.longitude,
    history.state?.location || cachedLocation(initialCoordinates.latitude, initialCoordinates.longitude)
    || initialLocation);
