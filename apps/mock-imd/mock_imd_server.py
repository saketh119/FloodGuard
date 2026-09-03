import os
import uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from datetime import date, datetime

app = FastAPI(
    title="IMD Mock API Server",
    description="A mock server replicating the official India Meteorological Department (IMD) API endpoints for testing and prototyping.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to structure IMD standard envelope
def imd_envelope(data: Any, message: str) -> Dict[str, Any]:
    return {
        "status": True,
        "message": message,
        "totalCount": len(data) if isinstance(data, list) else 1,
        "data": data
    }

# Mock Database / Static Data
DISTRICTS = {
    "164": {"name": "Kamrup Metropolitan", "state": "Assam", "latitude": 26.1445, "longitude": 91.7362},
    "165": {"name": "Dibrugarh", "state": "Assam", "latitude": 27.4728, "longitude": 94.9120},
    "573": {"name": "Ernakulam", "state": "Kerala", "latitude": 9.9816, "longitude": 76.2999},
    "574": {"name": "Wayanad", "state": "Kerala", "latitude": 11.6854, "longitude": 76.1320},
    "201": {"name": "Patna", "state": "Bihar", "latitude": 25.5941, "longitude": 85.1376},
    "202": {"name": "Muzaffarpur", "state": "Bihar", "latitude": 26.1197, "longitude": 85.3910}
}

STATIONS = {
    "42182": {
        "Station_Code": "42182",
        "Station_Name": "Guwahati",
        "district_id": "164",
        "latitude": 26.1445,
        "longitude": 91.7362,
        "elevation": 54
    },
    "43353": {
        "Station_Code": "43353",
        "Station_Name": "Kochi",
        "district_id": "573",
        "latitude": 9.9816,
        "longitude": 76.2999,
        "elevation": 2
    },
    "42492": {
        "Station_Code": "42492",
        "Station_Name": "Patna Airport",
        "district_id": "201",
        "latitude": 25.5941,
        "longitude": 85.1376,
        "elevation": 53
    }
}

BASINS = {
    "100": {"name": "Brahmaputra", "subbasins": ["Lohit", "Dibang", "Subansiri", "Kopili"]},
    "200": {"name": "Ganga", "subbasins": ["Ghaghara", "Gandak", "Kosi", "Sone"]},
    "300": {"name": "Periyar", "subbasins": ["Muvattupuzha", "Idamalayar"]}
}


# --- API Endpoints ---

@app.get("/")
def read_root():
    return {
        "status": "online",
        "provider": "India Meteorological Department (Mock)",
        "endpoints": [
            "/api/v1/cityforecast",
            "/api/v1/cityforecastloc",
            "/api/v1/current_wx",
            "/api/v1/nowcast",
            "/api/v1/districtrainfall",
            "/api/v1/districtwarning",
            "/api/v1/stationnowcast",
            "/api/v1/aws_data",
            "/api/v1/basinqpf"
        ]
    }


# 1 & 2. City Weather Forecast (7 Days) with optional Lat/Lon mapping
@app.get("/api/v1/cityforecast")
@app.get("/api/v1/cityforecastloc")
def get_city_forecast(id: Optional[str] = Query(None, description="Station Code (e.g. 42182)")):
    target_stations = STATIONS.keys() if not id else [id]
    
    forecast_data = []
    for station_code in target_stations:
        if station_code not in STATIONS:
            continue
            
        station = STATIONS[station_code]
        today_str = date.today().isoformat()
        
        # Heavy rain mock scenario for Guwahati (Assam) or Kochi (Kerala) to trigger flood pipelines
        is_flood_prone = station["Station_Name"] in ["Guwahati", "Kochi"]
        
        station_forecast = {
            "Date": today_str,
            "Station_Code": station["Station_Code"],
            "Station_Name": station["Station_Name"],
            "Today_Max_temp": "34.2" if not is_flood_prone else "29.0",
            "Today_Max_Departure_from_Normal": "+1.2" if not is_flood_prone else "-3.5",
            "Previous_Day_Max_temp": "33.5",
            "Previous_Day_Max_Departure_from_Normal": "+0.5",
            "Today_Min_temp": "24.5" if not is_flood_prone else "21.0",
            "Today_Min_Departure_from_Normal": "+0.2" if not is_flood_prone else "-1.5",
            "Past_24_hrs_Rainfall": "0.0" if not is_flood_prone else "142.5",
            "Relative_Humidity_at_0830": "72" if not is_flood_prone else "98",
            "Relative_Humidity_at_1730": "65" if not is_flood_prone else "95",
            "Previous_Day_Relative_Humidity_at_1730": "68",
            "Sunset_time": "18:42",
            "Sunrise_time": "05:24",
            "Moonset_time": "08:15",
            "Moonrise_time": "21:30",
            "Todays_Forecast_Max_Temp": "34.0" if not is_flood_prone else "28.0",
            "Todays_Forecast_Min_temp": "24.0" if not is_flood_prone else "21.0",
            "Todays_Forecast": "Clear Sky" if not is_flood_prone else "Heavy to Very Heavy Rain/Thunderstorms",
            # Include Days 2-7
            "Day_2_Max_Temp": "34.0" if not is_flood_prone else "28.0",
            "Day_2_Min_Temp": "24.0" if not is_flood_prone else "21.0",
            "Day_2_Forecast": "Partly Cloudy" if not is_flood_prone else "Heavy Rain",
            "Day_3_Max_Temp": "35.0" if not is_flood_prone else "27.5",
            "Day_3_Min_Temp": "25.0" if not is_flood_prone else "20.5",
            "Day_3_Forecast": "Partly Cloudy" if not is_flood_prone else "Continuous Heavy Rain",
            "Day_4_Max_Temp": "35.0" if not is_flood_prone else "29.0",
            "Day_4_Min_Temp": "25.0" if not is_flood_prone else "22.0",
            "Day_4_Forecast": "Sunny" if not is_flood_prone else "Thunderstorms",
            "Day_5_Max_Temp": "35.0",
            "Day_5_Min_Temp": "25.0",
            "Day_5_Forecast": "Sunny" if not is_flood_prone else "Light Rain",
            "Day_6_Max_Temp": "36.0",
            "Day_6_Min_Temp": "25.0",
            "Day_6_Forecast": "Sunny" if not is_flood_prone else "Partly Cloudy",
            "Day_7_Max_Temp": "36.0",
            "Day_7_Min_Temp": "26.0",
            "Day_7_Forecast": "Sunny" if not is_flood_prone else "Sunny",
            # Additional keys for cityforecastloc
            "Latitude": station["latitude"],
            "Longitude": station["longitude"]
        }
        forecast_data.append(station_forecast)
        
    if id and not forecast_data:
        raise HTTPException(status_code=404, detail="Station not found")
        
    return imd_envelope(forecast_data, "City Weather Forecast (7 Days)")


# 3. Current Weather API
@app.get("/api/v1/current_wx")
def get_current_weather(id: Optional[str] = Query(None, description="Station ID (e.g. 42182)")):
    target_stations = STATIONS.keys() if not id else [id]
    
    current_data = []
    for station_code in target_stations:
        if station_code not in STATIONS:
            continue
        station = STATIONS[station_code]
        is_flood_prone = station["Station_Name"] in ["Guwahati", "Kochi"]
        
        data = {
            "Station Id": station["Station_Code"],
            "Station": station["Station_Name"],
            "Date of Observation": date.today().isoformat(),
            "Time of Observation": datetime.utcnow().strftime("%H:%M:%S") + " UTC",
            "M.S.L.P": "1008.2" if not is_flood_prone else "995.4",
            "Wind Direction": 90 if not is_flood_prone else 230,
            "Wind Speed": 12 if not is_flood_prone else 48,
            "Temperature": 32.5 if not is_flood_prone else 24.2,
            "Weather Code": "02" if not is_flood_prone else "65",  # 65 = Heavy rain
            "Nebulosity": 2 if not is_flood_prone else 8,
            "Humidity": 68 if not is_flood_prone else 99,
            "Last 24 hrs Rainfall": 0.0 if not is_flood_prone else 112.4
        }
        current_data.append(data)
        
    if id and not current_data:
        raise HTTPException(status_code=404, detail="Station not found")
        
    return imd_envelope(current_data, "Current Weather Observation")


# 4. District-wise Nowcast
@app.get("/api/v1/nowcast")
def get_district_nowcast(id: Optional[str] = Query(None, description="District ID (e.g. 164)")):
    target_districts = DISTRICTS.keys() if not id else [id]
    
    nowcast_data = []
    for dist_id in target_districts:
        if dist_id not in DISTRICTS:
            continue
        dist = DISTRICTS[dist_id]
        is_active_flood = dist["name"] in ["Kamrup Metropolitan", "Ernakulam", "Wayanad"]
        
        cats = {f"Cat{i}": 0 for i in range(1, 20)}
        if is_active_flood:
            cats["Cat12"] = 1  # Cat 12 = Heavy Rain warning
            cats["Cat17"] = 1  # Cat 17 = Thunderstorm warning
            msg = f"Heavy to very heavy rainfall accompanied by lightning and gusty winds is highly likely to continue over {dist['name']} district during the next 3 hours."
            color = 4  # Red Alert
        else:
            cats["Cat1"] = 1  # No Warning
            msg = "No warnings. Weather is clear."
            color = 1  # Green Alert
            
        data = {
            "Station": dist["name"],
            "Date": date.today().isoformat(),
            **cats,
            "message": msg,
            "toi": datetime.now().strftime("%H%M"),
            "Vupto": (datetime.now().replace(hour=(datetime.now().hour + 3) % 24)).strftime("%H%M"),
            "color": color
        }
        nowcast_data.append(data)
        
    if id and not nowcast_data:
        raise HTTPException(status_code=404, detail="District not found")
        
    return imd_envelope(nowcast_data, "District Nowcast Warnings")


# 5. District-wise Rainfall
@app.get("/api/v1/districtrainfall")
def get_district_rainfall(id: Optional[str] = Query(None, description="District ID (e.g. 164)")):
    target_districts = DISTRICTS.keys() if not id else [id]
    
    rainfall_data = []
    for dist_id in target_districts:
        if dist_id not in DISTRICTS:
            continue
        dist = DISTRICTS[dist_id]
        is_wet = dist["name"] in ["Kamrup Metropolitan", "Ernakulam", "Wayanad"]
        
        daily_act = 85.5 if is_wet else 1.2
        daily_norm = 10.5
        weekly_act = 280.2 if is_wet else 15.4
        weekly_norm = 75.0
        
        data = {
            "OBJ_ID": int(dist_id),
            "District": dist["name"],
            "Date": date.today().isoformat(),
            "Daily Actual": daily_act,
            "Daily Normal": daily_norm,
            "Daily Departure Per": round(((daily_act - daily_norm) / daily_norm) * 100, 1),
            "Daily Category": "E" if is_wet else "D",  # Excess vs Deficient
            
            "Weekly Actual": weekly_act,
            "Weekly Normal": weekly_norm,
            "Weekly Departure Per": round(((weekly_act - weekly_norm) / weekly_norm) * 100, 1),
            "Weekly Category": "E" if is_wet else "D",
            
            "Cumulative Actual": weekly_act * 1.5,
            "Cumulative Normal": weekly_norm * 1.5,
            "Cumulative Departure Per": round(((weekly_act * 1.5 - weekly_norm * 1.5) / (weekly_norm * 1.5)) * 100, 1),
            "Cumulative Category": "E" if is_wet else "D",
            
            "Monthly Actual": weekly_act * 2.8,
            "Monthly Normal": weekly_norm * 2.8,
            "Monthly Departure Per": round(((weekly_act * 2.8 - weekly_norm * 2.8) / (weekly_norm * 2.8)) * 100, 1),
            "Monthly Category": "E" if is_wet else "D"
        }
        rainfall_data.append(data)
        
    if id and not rainfall_data:
        raise HTTPException(status_code=404, detail="District not found")
        
    return imd_envelope(rainfall_data, "District Rainfall Information")


# 6. District-wise Warnings (5 Days)
@app.get("/api/v1/districtwarning")
def get_district_warnings(id: Optional[str] = Query(None, description="District ID (e.g. 573)")):
    target_districts = DISTRICTS.keys() if not id else [id]
    
    warning_data = []
    for dist_id in target_districts:
        if dist_id not in DISTRICTS:
            continue
        dist = DISTRICTS[dist_id]
        is_wet = dist["name"] in ["Kamrup Metropolitan", "Ernakulam", "Wayanad"]
        
        data = {
            "Obj_id": int(dist_id),
            "Date": date.today().isoformat(),
            "UTC": datetime.utcnow().strftime("%H:%M:%S"),
            "District": dist["name"],
            
            "Day_1": "2,4" if is_wet else "1",  # 2 = Heavy Rain, 4 = Thunderstorm, 1 = No Warning
            "Day_2": "2,4" if is_wet else "1",
            "Day_3": "2" if is_wet else "1",
            "Day_4": "1",
            "Day_5": "1",
            
            "Day1_Color": 4 if is_wet else 1,  # 4 = Red, 1 = Green
            "Day2_Color": 3 if is_wet else 1,  # 3 = Orange
            "Day3_Color": 2 if is_wet else 1,  # 2 = Yellow
            "Day4_Color": 1,
            "Day5_Color": 1
        }
        warning_data.append(data)
        
    if id and not warning_data:
        raise HTTPException(status_code=404, detail="District not found")
        
    return imd_envelope(warning_data, "District Multi-day Warnings")


# 7. Station-wise Nowcast
@app.get("/api/v1/stationnowcast")
def get_station_nowcast(id: Optional[str] = Query(None, description="Station Name (e.g. Guwahati)")):
    target_stations = STATIONS.values() if not id else [s for s in STATIONS.values() if s["Station_Name"].lower() == id.lower()]
    
    nowcast_data = []
    for station in target_stations:
        is_wet = station["Station_Name"] in ["Guwahati", "Kochi"]
        
        cats = {f"Cat{i}": 0 for i in range(1, 20)}
        if is_wet:
            cats["Cat12"] = 1
            cats["Cat17"] = 1
            msg = f"Severe thunderstorm with intensive rainfall activity expected at station {station['Station_Name']} in next 2 hours."
            color = 4
        else:
            cats["Cat1"] = 1
            msg = "Clear weather."
            color = 1
            
        data = {
            "Station": station["Station_Name"],
            "Date": date.today().isoformat(),
            **cats,
            "message": msg,
            "toi": datetime.now().strftime("%H%M"),
            "Vupto": (datetime.now().replace(hour=(datetime.now().hour + 2) % 24)).strftime("%H%M"),
            "color": color
        }
        nowcast_data.append(data)
        
    if id and not nowcast_data:
        raise HTTPException(status_code=404, detail="Station not found")
        
    return imd_envelope(nowcast_data, "Station Nowcast Warnings")


# 9. AWS/ARG Data
@app.get("/api/v1/aws_data")
def get_aws_data(
    id: Optional[str] = Query(None, description="CallSign (e.g. GHT)"),
    sid: Optional[str] = Query(None, description="State ID (e.g. 7)")
):
    # Mapping state IDs to names
    state_mapping = {"7": "Delhi", "18": "Assam", "19": "Kerala"}
    
    aws_stations = [
        {"ID": 1, "CALL_SIGN": "GHT", "DISTRICT": "Kamrup Metropolitan", "STATE": "Assam", "STATION": "Guwahati AWS", "state_id": "18"},
        {"ID": 2, "CALL_SIGN": "KCH", "DISTRICT": "Ernakulam", "STATE": "Kerala", "STATION": "Kochi AWS", "state_id": "19"},
        {"ID": 3, "CALL_SIGN": "NDL", "DISTRICT": "New Delhi", "STATE": "Delhi", "STATION": "Delhi Safdarjung AWS", "state_id": "7"}
    ]
    
    # Filter list
    if id:
        aws_stations = [s for s in aws_stations if s["CALL_SIGN"].lower() == id.lower()]
    elif sid:
        aws_stations = [s for s in aws_stations if s["state_id"] == sid]
        
    data_list = []
    for s in aws_stations:
        is_wet = s["STATE"] in ["Assam", "Kerala"]
        
        record = {
            "ID": s["ID"],
            "CALL_SIGN": s["CALL_SIGN"],
            "DISTRICT": s["DISTRICT"],
            "STATE": s["STATE"],
            "STATION": s["STATION"],
            "DATE": date.today().isoformat(),
            "TIME": datetime.now().strftime("%H:%M:%S"),
            "CURR_TEMP": 24.2 if is_wet else 32.8,
            "DEW_POINT_TEMP": 23.5 if is_wet else 18.2,
            "RH": 96 if is_wet else 55,
            "WIND_DIRECTION": 240 if is_wet else 90,
            "WIND_SPEED": 35 if is_wet else 8,
            "MSLP": 996.2 if is_wet else 1010.5,
            "MIN_TEMP": 22.0 if is_wet else 25.5,
            "MAX_TEMP": 28.0 if is_wet else 35.2,
            "Latitude": 26.1445 if s["CALL_SIGN"] == "GHT" else (9.9816 if s["CALL_SIGN"] == "KCH" else 28.6139),
            "Longitude": 91.7362 if s["CALL_SIGN"] == "GHT" else (76.2999 if s["CALL_SIGN"] == "KCH" else 77.2090),
            "WEATHER_CODE": "65" if is_wet else "02",
            "NEBULOSITY": 8 if is_wet else 2,
            "Feel Like": 26.5 if is_wet else 36.4
        }
        data_list.append(record)
        
    return imd_envelope(data_list, "AWS/ARG Realtime Weather Data")


# 10. River Basin (QPF)
@app.get("/api/v1/basinqpf")
def get_basin_qpf(id: Optional[str] = Query(None, description="Basin ID (e.g. 100)")):
    target_basins = BASINS.keys() if not id else [id]
    
    qpf_data = []
    for b_id in target_basins:
        if b_id not in BASINS:
            continue
        basin = BASINS[b_id]
        
        for sub in basin["subbasins"]:
            is_wet = basin["name"] in ["Brahmaputra", "Periyar"]
            
            day1_qpf = "50-100" if is_wet else "0-10"
            day2_qpf = "100-200" if is_wet else "0-10"
            aap = 85.6 if is_wet else 2.1
            
            data = {
                "Obj_Id": int(b_id),
                "Date": date.today().isoformat(),
                "FMO": f"Guwahati FMO" if basin["name"] == "Brahmaputra" else "Kochi FMO",
                "Basin": basin["name"],
                "SubBasin": sub,
                "Area (Sq. Km.)": 12500 if basin["name"] == "Brahmaputra" else 5200,
                "Day1": day1_qpf,
                "Day2": day2_qpf,
                "Day3": "50-100" if is_wet else "0-5",
                "Day4": "25-50" if is_wet else "0",
                "Day5": "10-25" if is_wet else "0",
                "AAP": aap
            }
            qpf_data.append(data)
            
    if id and not qpf_data:
        raise HTTPException(status_code=404, detail="Basin not found")
        
    return imd_envelope(qpf_data, "River Basin Quantitative Precipitation Forecast")


if __name__ == "__main__":
    print("Starting IMD Mock API Server on http://localhost:8080...")
    uvicorn.run("mock_imd_server:app", host="0.0.0.0", port=8080, reload=True)
