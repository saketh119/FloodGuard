# AI-Powered Flood Intelligence Platform

## Project Vision

Build a production-style Flood Intelligence Platform that ingests
flood-related information from IMD, CWC, Weather APIs, and RSS News,
detects flood situations, correlates evidence, predicts risk, and
presents unified flood events instead of isolated API responses.

## Core Architecture

``` text
External Sources
    │
    ├── IMD
    ├── CWC
    ├── Weather APIs
    ├── RSS / News
    └── Future Sources
        │
Observation Tables
        │
Trigger Detection Engine
        │
Event Correlation Engine
        │
Flood Events
        ├── Prediction Engine
        ├── AI Summarizer
        └── Dashboard
```

## Philosophy

-   Separate Metadata from Observations.
-   Observations are immutable.
-   Flood Events are derived and evolve over time.
-   Never lose raw source data.

## Source Design

### IMD

Stores warnings and rainfall observations.

### CWC

#### cwc_station (metadata)

-   station_code
-   station_name
-   river
-   basin
-   district
-   state
-   latitude
-   longitude
-   FRL
-   MWL
-   warning_level
-   danger_level
-   telemetric
-   operational
-   raw_metadata

#### cwc_measurement (time-series)

-   id
-   station_code
-   measurement_time
-   datatype_code
-   value
-   validated_value
-   received_at
-   raw_json

### Weather

Periodic observations such as rainfall, humidity, wind speed,
temperature and pressure.

### RSS / News

Article title, content, URL, published time, extraction method and raw
JSON.

## Trigger Detection

Each source has its own rules:

-   IMD: Orange/Red alerts
-   CWC: Warning/Danger water levels
-   Weather: Rainfall thresholds
-   News: Keyword rules (future: LLM extraction)

## Event Correlation

Observation ↓ Find nearby event by location + time

If found: - Attach as evidence - Increase confidence - Update risk -
Update AI summary

Else: - Create new flood event

## Main Tables

### flood_events

-   event_id
-   location
-   category
-   status
-   confidence_score
-   risk_score
-   prediction
-   ai_summary
-   created_at
-   updated_at

### event_evidence

-   event_id
-   source
-   observation_id
-   trigger_reason
-   contribution_score
-   added_at

## CWC Reverse Engineering

Discovered endpoint:

GET /iam/api/layer-station/{stationCode}

Returns station metadata (river, basin, district, FRL, MWL, etc.).

Another endpoint returns time-series measurements, confirming CWC
separates metadata from observations.

The platform mirrors this design.

## Processing Pipeline

Scheduler ↓ Fetch APIs ↓ Store raw observations ↓ Trigger Detection ↓
Event Correlation ↓ Prediction ↓ AI Summary ↓ Dashboard

## NLP Strategy

Version 1: - Structured APIs → Direct mapping - News → Keyword
matching + regex

Future: - LLM extraction - Social media analysis

## Modules

-   Scheduler
-   Data Ingestion
-   Source Adapters
-   Trigger Detection
-   Event Correlation
-   Prediction Engine
-   AI Summarizer
-   RAG Chatbot
-   Dashboard
-   Notification Service

## Goal

Transform independent hydrological observations into continuously
evolving Flood Events that can be searched, predicted, summarized, and
acted upon.
