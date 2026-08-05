# FloodGuard Data Processing Pipeline

This document outlines the ingestion, preprocessing, processing, and normalization steps executed by the FloodGuard backend. The platform transforms highly unstructured, disparate API responses into unified, actionable "Flood Events".

---

## 1. Ingestion & Normalization (Source Adapters)

The platform ingests data from four distinct sources via the `backend/app/sources/` adapters. Since each API returns a vastly different JSON structure, the adapters normalize them into standard SQLAlchemy ORM models.

### A. IMD (India Meteorological Department)
- **Input:** 4 separate JSON endpoints (Current Weather, Nowcast, District Rainfall, District Warnings).
- **Preprocessing:** 
  - Parses dates and warning arrays.
  - Maps internal numerical severity codes (1-4) to `success`, `warning`, `danger`.
- **Output:** Unified `ImdObservation`.

### B. CWC (Central Water Commission)
- **Input:** Static station metadata and time-series water level metrics.
- **Preprocessing:** 
  - Standardizes units (e.g., meters for water level, cumecs for discharge).
  - Categorizes levels based on historical "Warning" and "Danger" thresholds.
- **Output:** `CwcStation` and `CwcMeasurement`.

### C. OpenWeatherMap
- **Input:** Standard meteorological weather payload.
- **Preprocessing:** 
  - Converts temperature from Kelvin to Celsius.
  - Normalizes wind speeds from m/s to km/h.
- **Output:** `WeatherObservation`.

### D. RSS News Feeds
- **Input:** XML/RSS feeds from disaster management news outlets.
- **Preprocessing:** 
  - Uses Regex and NLP keyword matching to extract geographical entities (District and State) from the raw article text.
  - Flags articles containing flood-related keyword stems (e.g., "evacuat", "inundat", "overflow").
- **Output:** `NewsObservation`.

---

## 2. Enrichment (`pipeline/enricher.py`)

Raw data often lacks exact geographic identifiers. The enricher resolves this before triggering rules.
- **Standardization:** Normalizes district string names (e.g., mapping "Kamrup Metro" and "Kamrup (M)" to the canonical "Kamrup Metropolitan").
- **Reverse-Geocoding:** If an observation only contains coordinates (latitude/longitude) but no district name, it maps those coordinates to known regional bounding boxes to assign the correct district and state.

---

## 3. Trigger Detection (`pipeline/trigger.py`)

The rule engine acts as the first line of defense. It analyzes every incoming normalized observation against strict thresholds to filter out noise.

- **IMD Rules:** Triggers if the Nowcast color code is Orange or Red (≥ 3) OR if 24-hour rainfall exceeds 64.5mm (Heavy Rainfall threshold).
- **CWC Rules:** Triggers if river levels hit or exceed the predefined "Warning", "Danger", or "Severe" limits.
- **Weather Rules:** Triggers if 1-hour rainfall exceeds 15mm OR wind speed exceeds 50 km/h.
- **News Rules:** Triggers if an article contains ≥ 2 unique flood-related keywords.

*Output: A `TriggerContext` object containing the location, severity, and exact reason for triggering.*

---

## 4. Event Correlation (`pipeline/correlator.py`)

When a trigger fires, the system does not blindly create an alert (which causes alert fatigue). Instead, it attempts to correlate it with existing active incidents.

- **Spatial Matching:** Uses the Haversine formula to search for existing events within a **50km radius**.
- **Temporal Matching:** Limits the correlation window to **24 hours**.
- **Evidence Linking:** If a match is found, the new observation is appended to the event's `evidence` array rather than creating a duplicate alert.
- **Scoring Engine:** Calculates a dynamic `confidence_score` and `risk_score` using an Exponential Moving Average (EMA). 
  - **Source Diversity Bonus:** If multiple *different* sources (e.g., IMD and CWC) report the same incident, the system adds an 8% confidence bonus.
- **Lifecycle Upgrades:** As confidence rises, the event automatically upgrades through severity stages: `potential` → `developing` → `high_risk` → `active`.

---

## 5. AI Summarization (`ai/summarizer.py`)

To provide human-readable context to operators:
- Once the correlator attaches new evidence, it fires an asynchronous task to the LLM via OpenRouter.
- It feeds the LLM the location, current risk score, and a list of all raw trigger reasons (evidence).
- The LLM generates a concise 2-3 sentence situation report, which is saved as the event's `ai_summary`.

---

## 6. Frontend UI Mapping (`backendMapper.js`)

When the React frontend fetches this processed intelligence from the backend REST API, the mapper layer acts as a ViewModel.
- It translates the strict backend schema into visual formats expected by the UI.
- Example: It maps severity string metrics to exact CSS variables (`var(--danger)`, `var(--warning)`) and selects the appropriate Lucide UI icons.
