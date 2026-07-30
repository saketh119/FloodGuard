# India Meteorological Department (IMD) API Reference Report

## Executive Summary
This report documents the API endpoints, parameters, field structures, and response schemas published on the official IMD API reference portal (`https://api.imd.gov.in/public/api_reference.html`). 

### Key Observations:
- **Documentation Discrepancy:** The main API Index lists **28 APIs** organized under 10 categories. However, only **20 APIs** are actually implemented and documented in the page's HTML body.
- **Missing APIs:** The following 8 APIs are present in the index but are entirely missing from the documentation body (no endpoints, schemas, or sample responses are provided):
  1. Fishermen Warning (`#api-23`)
  2. All India Weather Forecast Bulletin (`#api-24`)
  3. Radar Image (`#api-25`)
  4. Lightning Data (`#api-26`)
  5. Weather at your location (Mausamgram) (`#api-27`)
  6. Agromet Advisory (`#api-28`)
  7. Highway Nowcast Warning (`#api-21`)
  8. Highway Warning - 5 Days (`#api-22`)
- **Authentication:** Data access is controlled via secure JSON Web Tokens (JWT).

---

## Detailed API Reference (Documented APIs 1-20)

### 1. City Weather Forecast (7 Days)
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/cityforecast`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/cityforecast?id=StationCode` (e.g., `id=42182`)
- **Data Visualization:** `https://city.imd.gov.in`
- **Field Reference:**
  - `Date`: Date of Observation (YYYY-mm-dd)
  - `Station_Code`: Unique identifier for the station
  - `Station_Name`: Name of the station
  - `Today_Max_temp`: Max temp recorded at 1730 hrs IST (°C)
  - `Today_Max_Departure_from_Normal`: Max temp departure from normal (°C)
  - `Previous_Day_Max_temp`: Previous day's max temp recorded at 1730 hrs IST (°C)
  - `Previous_Day_Max_Departure_from_Normal`: Previous day's max temp departure from normal (°C)
  - `Today_Min_temp`: Min temp recorded at 0530 hrs IST (°C)
  - `Today_Min_Departure_from_Normal`: Min temp departure from normal (°C)
  - `Past_24_hrs_Rainfall`: Rainfall recorded from 0830 hrs IST of the previous day to 0830 hrs IST today
  - `Relative_Humidity_at_0830`: Relative humidity recorded at 0830 hrs (%)
  - `Relative_Humidity_at_1730`: Relative humidity recorded at 1730 hrs (%)
  - `Previous_Day_Relative_Humidity_at_1730`: Previous day's relative humidity recorded at 1730 hrs (%)
  - `Sunset_time` / `Sunrise_time` / `Moonset_time` / `Moonrise_time`: Solar/lunar event times
  - `Todays_Forecast_Max_Temp` / `Todays_Forecast_Min_temp`: Day-1 forecasted temps (°C)
  - `Todays_Forecast`: Weather forecast description for Day-1 (Today)
  - `Day_2_Max_Temp` to `Day_7_Forecast`: Forecasts and expected temperature ranges for Days 2 through 7.

### 2. City Weather Forecast (7 Days) with Latitude & Longitude
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/cityforecastloc`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/cityforecastloc?id=StationCode` (e.g., `id=42182`)
- **Data Visualization:** `https://city.imd.gov.in`
- **Mapping Data:** `https://api.imd.gov.in/api/v1/cityforecast_mapping`
- **Field Reference:** Same as API-1 with the addition of:
  - `Latitude`: Latitude of the station
  - `Longitude`: Longitude of the station

### 3. Current Weather API
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/current_wx`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/current_wx?id=StationId`
- **Field Reference:**
  - `Station Id`: Unique station identifier
  - `Station`: Station Name
  - `Date of Observation`: YYYY-mm-dd
  - `Time of Observation`: UTC
  - `M.S.L.P`: Mean Sea Level Pressure (hPa)
  - `Wind Direction`: Wind direction code (0 = Calm, 20 = NNE, 50 = NE, 70 = ENE, etc.)
  - `Wind Speed`: Wind speed in KMPH
  - `Temperature`: Current temperature in °C
  - `Weather Code`: Current weather code (01-99, e.g., 10 = Mist, 11 = Shallow Fog)
  - `Nebulosity`: Cloud coverage on a scale of 0-8
  - `Humidity`: Relative humidity (%)
  - `Last 24 hrs Rainfall`: Precipitation in mm

### 4. District-wise Nowcast
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/nowcast`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/nowcast?id=DistrictId`
- **Data Visualization:** `https://mausam.imd.gov.in/responsive/nowcast.php`
- **Field Reference:**
  - `Station`: Station name
  - `Date`: Date of warning issued (YYYY-mm-dd)
  - `Cat1` to `Cat19`: Weather/warning categories (Cat1 = No weather, Cat12 = Heavy Rain, Cat17 = Thunderstorm with Hail, etc.)
  - `message`: Consolidated warning message text
  - `toi`: Time of issue (HHmm)
  - `Vupto`: Warning validity end time (HHmm)
  - `color`: Overall warning level color code (1 = Green, 2 = Yellow, 3 = Orange, 4 = Red)

### 5. District-wise Rainfall
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/districtrainfall`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/districtrainfall?id=DistrictId` (e.g., `id=164`)
- **Data Visualization:** `https://mausam.imd.gov.in/responsive/rainfallinformation.php`
- **Sample Response Fields:**
  - `OBJ_ID`: Unique district ID
  - `District` / `Date`
  - `Daily Actual` / `Daily Normal` / `Daily Departure Per` / `Daily Category` (NR = No Rain, N = Normal, etc.)
  - `Weekly Actual` / `Weekly Normal` / `Weekly Departure Per` / `Weekly Category`
  - `Cumulative Actual` / `Cumulative Normal` / `Cumulative Departure Per` / `Cumulative Category`
  - `Monthly Actual` / `Monthly Normal` / `Monthly Departure Per` / `Monthly Category`

### 6. District-wise Warnings
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/districtwarning`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/districtwarning?id=DistrictId` (e.g., `id=573`)
- **Data Visualization:** `https://mausam.imd.gov.in/responsive/districtWiseWarningGIS.php`
- **Field Reference:**
  - `Obj_id`: Object ID for the district
  - `Date` / `UTC`: Date and time of issue
  - `District`: District Name
  - `Day_1` to `Day_5`: Multi-comma-separated warning codes (e.g., 2 = Heavy Rain, 4 = Thunderstorm & Lightning, 9 = Heat Wave)
  - `Day1_Color` to `Day5_Color`: Color codes (1 = Green, 2 = Yellow, 3 = Orange, 4 = Red)

### 7. Station-wise Nowcast
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/stationnowcast`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/stationnowcast?id=StationName` (e.g., `id=Adilabad`)
- **Data Visualization:** `https://mausam.imd.gov.in/responsive/stationWiseNowcastGIS.php`
- **Field Reference:** Similar to API-4 (District Nowcast) but specific to weather stations.

### 8. State-wise Rainfall
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/staterainfall`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/staterainfall?id=StateName` (e.g., `id=jammu`)
- **Data Visualization:** `https://mausam.imd.gov.in/responsive/rainfallinformation_state.php`
- **Sample Response Fields:** Same structure as API-5 (District-wise Rainfall) mapped at the State level.

### 9. AWS/ARG Data
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/aws_data`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/aws_data?id=CallSign` (e.g., `id=NDL`) OR `https://api.imd.gov.in/api/v1/aws_data?sid=StateID` (e.g., `sid=7` for Delhi)
- **AWS Mapping Data:** `https://api.imd.gov.in/api/v1/aws_data_mapping`
- **Sample Response Fields:** `ID`, `CALL_SIGN`, `DISTRICT`, `STATE`, `STATION`, `DATE`, `TIME`, `CURR_TEMP`, `DEW_POINT_TEMP`, `RH`, `WIND_DIRECTION`, `WIND_SPEED`, `MSLP`, `MIN_TEMP`, `MAX_TEMP`, `Latitude`, `Longitude`, `WEATHER_CODE`, `NEBULOSITY`, `Feel Like`.

### 10. River Basin (QPF)
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/basinqpf`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/basinqpf?id=BasinId` (e.g., `id=100`)
- **Data Visualization:** `https://mausam.imd.gov.in/responsive/quantPrecipForecast.php`
- **Field Reference:** `Obj_Id`, `Date`, `FMO` (Flood Met Office name), `Basin` (River basin name), `SubBasin` (Sub-basin name), `Area (Sq. Km.)`, `Day1` to `Day5` (Day-1 to Day-5 forecasts), `AAP` (Average Areal Precipitation).

### 11. Port Warning
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/portwarning`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/portwarning?id=PortId`
- **Data Visualization:** `https://rsmcnewdelhi.imd.gov.in/port-warning.php`
- **Field Reference:** `Port Id`, `Port Name`, `Issued By`, `Date of Issue`, `Warning`.

### 12. Sea Area Bulletin
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/seabulletin`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/seabulletin?id=SeaAreaId` (e.g., `id=108`)
- **Data Visualization:** `https://mausam.imd.gov.in/responsive/marine_forecast.php`
- **Sample Response Fields:** `Id`, `Date of Observation`, `Layer` (e.g., "South West Bay"), `Issued by`, `Valid From`, `Validity` (in hours), `TTT Warning`, `Wind`, `Synoptic Situation`, `Weather`, `Visibility`, `Sea Condition`, `Part 4`, `Part 5`, `Part 6`, `Update Time`.

### 13. Coastal Bulletin
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/coastalbulletin`
- **Data Visualization:** `https://mausam.imd.gov.in/responsive/coastal_forecast.php`
- **Sample Response Fields:** `Id`, `Date of Observation`, `Layer` (e.g., "South Tamilnadu coast"), `Issued by`, `Valid From`, `Validity`, `TTT Warning`, `Wind`, `Synoptic Situation`, `Weather`, `Visibility`, `Sea Condition`, `Port Signal`, `Update Time`.

### 14. Subdivisional-wise Warnings
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/subdivisionwarning`
- **Data Visualization:** `https://mausam.imd.gov.in/responsive/subDivisionWiseWarningGIS.php`
- **Sample Response Fields:** `date_obs`, `SUBDIV`, `day1_color` to `day5_color` (hex color values), `day1_warning` to `day5_warning` (warning text).

### 15. Sun Moon (Rise/Set) Time
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/sunmoon`
- **Parameterized URL:** `https://api.imd.gov.in/api/v1/sunmoon?lat=Latitude&lon=Longitude` (e.g., `lat=26.9124&lon=75.7873`)
- **Sample Response Structure:**
  ```json
  {
    "status": true,
    "message": "SunMoon Time",
    "totalCount": null,
    "data": [
      { "sunrise": "06:45", "sunset": "18:31" },
      { "moonrise": "22:14", "moonset": "08:39" }
    ]
  }
  ```
  *(Note: Time in IST)*

### 16. Subdivisional Rainfall Forecast - 7 Days
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/subdivision_rainfall_forecast`
- **Sample Response Fields:** `date_obs`, `SUBDIV`, `day1_color` to `day7_color`, `day1_distribution` to `day7_distribution`, `day1_distribution_percentage` to `day7_distribution_percentage` (e.g., "Stations [76-100]%").

### 17. State District Rainfall Forecast - 5 Days
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/state_district_rainfall_forecast`
- **Sample Response Fields:** `date_obs`, `Obj_id`, `District`, `State`, `day1_color` to `day5_color`, `day1_distribution` to `day5_distribution`, `day1_distribution_percentage` to `day5_distribution_percentage`.

### 18. Cyclone Track
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/cyclone_track`
- **Sample Response Structure:**
  ```json
  {
    "status": true,
    "message": "Cyclone Track",
    "totalCount": { "observed": 9, "forecast": 7 },
    "data": {
      "observed": [
        {
          "CYCLONE_NAME": "BULBUL",
          "Hour": "12",
          "Date/Time": "05.11.19/1200",
          "lat": "13.2",
          "lon": "91.2",
          "MSW range (kmph)": "50-60",
          "Mean MSW (kmph)": "55",
          "MSW (kt)": "29.7",
          "Category": "DEEP DEPRESSION"
        }
      ]
    }
  }
  ```

### 19. Cyclone Wind Warning
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/cyclone_wind`
- **Sample Response Structure:**
  ```json
  {
    "status": true,
    "message": "Cyclone Wind Warning",
    "totalCount": { "27kt": 1, "34kt": 1, "50kt": 1, "64kt": 1 },
    "data": {
      "27kt": {
        "type": "MultiPolygon",
        "coordinates": [[[[80.685399494754, 9.7315954161175], ...]]]
      }
    }
  }
  ```

### 20. Cyclone Cone of Uncertainty
- **Endpoint URL:** `https://api.imd.gov.in/api/v1/cyclone_cou`
- **Sample Response Structure:**
  ```json
  {
    "status": true,
    "message": "Cone of Uncertainty",
    "totalCount": 1,
    "data": {
      "type": "MultiPolygon",
      "coordinates": [[[[80.698599865156, 11.240006126297], ...]]]
    }
  }
  ```
