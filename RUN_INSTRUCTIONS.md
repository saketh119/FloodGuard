# Running FloodGuard Locally

This guide provides step-by-step instructions on how to start the entire FloodGuard platform locally, including the dummy data servers, the FastAPI backend, and the React frontend dashboard.

## Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- (Optional) **Docker**

---

## Method 1: Running Manually (Recommended for Development)

You need to start three components in separate terminal windows.

### Step 1: Start the Mock API Servers
The backend relies on four separate dummy servers (IMD, CWC, Weather, and RSS) to simulate live data. 
Open a terminal and navigate to the project root:

```bash
cd backend

# Start the servers (you can run these in the background or in separate tabs)
python scripts/mock_imd_server.py &
python scripts/mock_cwc_server.py &
python scripts/mock_weather_server.py &
python scripts/mock_rss_server.py &
```
*(They will bind to ports 8080, 8081, 8082, and 8083).*

### Step 2: Start the FastAPI Backend
In the same or a new terminal window:

```bash
cd backend
# Create and activate virtual environment (if not already done)
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt

# Start the backend server
uvicorn app.main:app --reload --port 8000
```
*The backend will automatically start its scheduler and begin pulling data from the mock servers into the local SQLite database.*
*You can view the raw API output at [http://localhost:8000/api/v1/events](http://localhost:8000/api/v1/events)*

### Step 3: Start the Next.js/Vite Frontend
Open a new terminal window:

```bash
cd dashboard
npm install
npm run dev
```
*The dashboard will be available at [http://localhost:5173](http://localhost:5173).*
*It will automatically communicate with the FastAPI backend on port 8000.*

---

## Method 2: Running with Docker Compose

If you have Docker installed, you can start the entire stack (Mock Servers + Backend + Frontend) with a single command.

```bash
docker-compose up --build
```

- The UI will be available on `http://localhost:5173`
- The API will be available on `http://localhost:8000`

---

## Troubleshooting

- **No Active Events Showing:** Wait up to 1-2 minutes for the backend scheduler to pull the first batch of data from the mock servers and run the correlation engine.
- **Connection Refused:** Ensure the mock servers are actively running on their respective ports. The backend will log warnings if it cannot reach them.
