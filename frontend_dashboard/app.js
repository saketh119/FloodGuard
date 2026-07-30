// Initialize Lucide Icons
lucide.createIcons();

// DOM Elements
const themeToggleBtn = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');
const toggleSidebarBtn = document.getElementById('toggle-sidebar');
const sidebar = document.querySelector('.sidebar');
const locationInput = document.getElementById('location-input');
const btnShareLocation = document.getElementById('btn-share-location');
const activeLocationName = document.getElementById('active-location-name');
const activeCoordinates = document.getElementById('active-coordinates');

// Stats DOM Elements
const statAlertLevel = document.getElementById('stat-alert-level');
const statActiveEvents = document.getElementById('stat-active-events');
const statRainfall = document.getElementById('stat-rainfall');
const statRiskTrend = document.getElementById('stat-risk-trend');
const statTrendIcon = document.getElementById('stat-trend-icon');

// Bottom Cards DOM Elements
const cardWeatherVal = document.getElementById('card-weather-val');
const cardWeatherDesc = document.getElementById('card-weather-desc');
const cardRiverVal = document.getElementById('card-river-val');
const cardRiverDesc = document.getElementById('card-river-desc');
const cardResVal = document.getElementById('card-res-val');
const cardResDesc = document.getElementById('card-res-desc');
const cardShelterVal = document.getElementById('card-shelter-val');
const cardShelterDesc = document.getElementById('card-shelter-desc');

// Containers
const eventsContainer = document.getElementById('events-container');
const predictionsContainer = document.getElementById('predictions-container');

// Location Data Store (Mock Data)
const mockLocationData = {
  "hyderabad": {
    name: "Hyderabad, Telangana",
    coords: "17.3850° N, 78.4867° E",
    alertLevel: "High",
    alertColor: "var(--danger)",
    alertBg: "var(--danger-light)",
    activeEvents: 3,
    rainfall: "112.5 mm",
    trend: "Increasing",
    trendColor: "var(--danger)",
    weatherVal: "25°C",
    weatherDesc: "Light Rain",
    riverVal: "7.2 m",
    riverDesc: "Above Warning Level",
    riverColor: "var(--danger)",
    resVal: "3 / 5",
    resDesc: "Above 80% Capacity",
    resColor: "var(--warning)",
    shelterVal: "12",
    shelterDesc: "Within 10 km",
    events: [
      { title: "Musi River Rising", status: "High", color: "danger", subtitle: "Musi River, Hyderabad", started: "Started: 20 Jul 2026, 06:30 AM", val: "7.2 m", label: "Water Level", icon: "milestone" },
      { title: "Heavy Rainfall Alert", status: "Medium", color: "warning", subtitle: "Hyderabad District", started: "Started: 20 Jul 2026, 08:15 AM", val: "98.4 mm", label: "24h Rainfall", icon: "bell-ring" },
      { title: "Reservoir Inflow High", status: "High", color: "danger", subtitle: "Himayat Sagar Reservoir", started: "Started: 19 Jul 2026, 11:45 PM", val: "85%", label: "Storage Level", icon: "shield-alert" }
    ],
    predictions: [
      { day: "Today, 20 Jul", status: "High", color: "danger", pct: 75 },
      { day: "Tomorrow, 21 Jul", status: "High", color: "danger", pct: 68 },
      { day: "Tue, 22 Jul", status: "Medium", color: "warning", pct: 52 },
      { day: "Wed, 23 Jul", status: "Low", color: "success", pct: 28 },
      { day: "Thu, 24 Jul", status: "Low", color: "success", pct: 18 }
    ]
  },
  "vijayawada": {
    name: "Vijayawada, Andhra Pradesh",
    coords: "16.5062° N, 80.6480° E",
    alertLevel: "Medium",
    alertColor: "var(--warning)",
    alertBg: "var(--warning-light)",
    activeEvents: 1,
    rainfall: "45.2 mm",
    trend: "Stable",
    trendColor: "var(--warning)",
    weatherVal: "28°C",
    weatherDesc: "Cloudy",
    riverVal: "4.8 m",
    riverDesc: "Below Danger Mark",
    riverColor: "var(--success)",
    resVal: "1 / 4",
    resDesc: "Normal Storage",
    resColor: "var(--success)",
    shelterVal: "8",
    shelterDesc: "Within 10 km",
    events: [
      { title: "Krishna River High Discharge", status: "Medium", color: "warning", subtitle: "Prakasam Barrage", started: "Started: 20 Jul 2026, 02:00 AM", val: "4.8 m", label: "Discharge Depth", icon: "waves" }
    ],
    predictions: [
      { day: "Today, 20 Jul", status: "Medium", color: "warning", pct: 45 },
      { day: "Tomorrow, 21 Jul", status: "Medium", color: "warning", pct: 40 },
      { day: "Tue, 22 Jul", status: "Low", color: "success", pct: 30 },
      { day: "Wed, 23 Jul", status: "Low", color: "success", pct: 20 },
      { day: "Thu, 24 Jul", status: "Low", color: "success", pct: 15 }
    ]
  },
  "guntur": {
    name: "Guntur, Andhra Pradesh",
    coords: "16.3067° N, 80.4365° E",
    alertLevel: "Low",
    alertColor: "var(--success)",
    alertBg: "var(--success-light)",
    activeEvents: 0,
    rainfall: "12.0 mm",
    trend: "Decreasing",
    trendColor: "var(--success)",
    weatherVal: "30°C",
    weatherDesc: "Clear Sky",
    riverVal: "2.1 m",
    riverDesc: "Safe Levels",
    riverColor: "var(--success)",
    resVal: "0 / 3",
    resDesc: "Low Storage",
    resColor: "var(--success)",
    shelterVal: "15",
    shelterDesc: "Operational",
    events: [],
    predictions: [
      { day: "Today, 20 Jul", status: "Low", color: "success", pct: 12 },
      { day: "Tomorrow, 21 Jul", status: "Low", color: "success", pct: 10 },
      { day: "Tue, 22 Jul", status: "Low", color: "success", pct: 8 },
      { day: "Wed, 23 Jul", status: "Low", color: "success", pct: 5 },
      { day: "Thu, 24 Jul", status: "Low", color: "success", pct: 2 }
    ]
  },
  "warangal": {
    name: "Warangal, Telangana",
    coords: "17.9689° N, 79.5941° E",
    alertLevel: "High",
    alertColor: "var(--danger)",
    alertBg: "var(--danger-light)",
    activeEvents: 2,
    rainfall: "88.4 mm",
    trend: "Increasing",
    trendColor: "var(--danger)",
    weatherVal: "26°C",
    weatherDesc: "Heavy Rain",
    riverVal: "5.4 m",
    riverDesc: "Approaching Danger",
    riverColor: "var(--warning)",
    resVal: "2 / 3",
    resDesc: "Above 80% Capacity",
    resColor: "var(--warning)",
    shelterVal: "5",
    shelterDesc: "Within 5 km",
    events: [
      { title: "Flash Floods in Low Areas", status: "High", color: "danger", subtitle: "Hunter Road, Warangal", started: "Started: 20 Jul 2026, 09:00 AM", val: "1.2 m", label: "Inundation", icon: "alert-triangle" },
      { title: "Bhadrakali Lake Overflow", status: "Medium", color: "warning", subtitle: "Bhadrakali", started: "Started: 20 Jul 2026, 05:45 AM", val: "94%", label: "Capacity", icon: "droplet" }
    ],
    predictions: [
      { day: "Today, 20 Jul", status: "High", color: "danger", pct: 80 },
      { day: "Tomorrow, 21 Jul", status: "High", color: "danger", pct: 72 },
      { day: "Tue, 22 Jul", status: "Medium", color: "warning", pct: 48 },
      { day: "Wed, 23 Jul", status: "Low", color: "success", pct: 25 },
      { day: "Thu, 24 Jul", status: "Low", color: "success", pct: 12 }
    ]
  },
  "nalgonda": {
    name: "Nalgonda, Telangana",
    coords: "17.0500° N, 79.2700° E",
    alertLevel: "Low",
    alertColor: "var(--success)",
    alertBg: "var(--success-light)",
    activeEvents: 0,
    rainfall: "5.5 mm",
    trend: "Stable",
    trendColor: "var(--success)",
    weatherVal: "31°C",
    weatherDesc: "Sunny",
    riverVal: "1.5 m",
    riverDesc: "Safe Levels",
    riverColor: "var(--success)",
    resVal: "1 / 4",
    resDesc: "Normal Storage",
    resColor: "var(--success)",
    shelterVal: "6",
    shelterDesc: "Operational",
    events: [],
    predictions: [
      { day: "Today, 20 Jul", status: "Low", color: "success", pct: 8 },
      { day: "Tomorrow, 21 Jul", status: "Low", color: "success", pct: 5 },
      { day: "Tue, 22 Jul", status: "Low", color: "success", pct: 5 },
      { day: "Wed, 23 Jul", status: "Low", color: "success", pct: 3 },
      { day: "Thu, 24 Jul", status: "Low", color: "success", pct: 2 }
    ]
  }
};

// Update UI function
function updateDashboard(locationKey) {
  const data = mockLocationData[locationKey.toLowerCase()];
  if (!data) return;

  // Header Details
  activeLocationName.textContent = data.name;
  activeCoordinates.textContent = data.coords;

  // Stats Card
  statAlertLevel.textContent = data.alertLevel;
  statAlertLevel.style.color = data.alertColor;
  statAlertLevel.closest('.stat-card').querySelector('.stat-icon-wrapper').style.backgroundColor = data.alertBg;
  statAlertLevel.closest('.stat-card').querySelector('.stat-icon-wrapper').style.color = data.alertColor;

  statActiveEvents.textContent = data.activeEvents;
  statRainfall.textContent = data.rainfall;
  statRiskTrend.textContent = data.trend;
  statRiskTrend.style.color = data.trendColor;

  // Trend icon change
  const trendWrapper = statRiskTrend.closest('.stat-card').querySelector('.stat-icon-wrapper');
  if (data.trend === "Increasing") {
    statTrendIcon.setAttribute('data-lucide', 'trending-up');
    statTrendIcon.style.color = 'var(--danger)';
    trendWrapper.style.backgroundColor = 'var(--danger-light)';
    trendWrapper.style.color = 'var(--danger)';
  } else if (data.trend === "Stable") {
    statTrendIcon.setAttribute('data-lucide', 'minus');
    statTrendIcon.style.color = 'var(--warning)';
    trendWrapper.style.backgroundColor = 'var(--warning-light)';
    trendWrapper.style.color = 'var(--warning)';
  } else {
    statTrendIcon.setAttribute('data-lucide', 'trending-down');
    statTrendIcon.style.color = 'var(--success)';
    trendWrapper.style.backgroundColor = 'var(--success-light)';
    trendWrapper.style.color = 'var(--success)';
  }

  // Bottom Cards
  cardWeatherVal.textContent = data.weatherVal;
  cardWeatherDesc.textContent = data.weatherDesc;
  cardRiverVal.textContent = data.riverVal;
  cardRiverDesc.textContent = data.riverDesc;
  cardRiverDesc.style.color = data.riverColor;
  cardResVal.textContent = data.resVal;
  cardResDesc.textContent = data.resDesc;
  cardResDesc.style.color = data.resColor;
  cardShelterVal.textContent = data.shelterVal;
  cardShelterDesc.textContent = data.shelterDesc;

  // Render active events
  eventsContainer.innerHTML = '';
  if (data.events.length === 0) {
    eventsContainer.innerHTML = `
      <div style="text-align: center; padding: 32px; color: var(--text-secondary); display: flex; flex-direction: column; align-items: center; gap: 8px;">
        <i data-lucide="shield-check" style="width: 48px; height: 48px; color: var(--success);"></i>
        <strong>No active flood events</strong>
        <span style="font-size: 13px;">Weather conditions and river basins are currently safe in this area.</span>
      </div>
    `;
  } else {
    data.events.forEach(evt => {
      eventsContainer.innerHTML += `
        <div class="event-item">
          <div class="event-left">
            <div class="event-icon-circle" style="background-color: var(--${evt.color}-light); color: var(--${evt.color});">
              <i data-lucide="${evt.icon}"></i>
            </div>
            <div class="event-details">
              <div class="event-title-row">
                <span class="event-title">${evt.title}</span>
                <span class="badge-status" style="background-color: var(--${evt.color}-light); color: var(--${evt.color});">${evt.status}</span>
              </div>
              <span class="event-subtitle">${evt.subtitle}</span>
              <span class="event-time">
                <i data-lucide="clock" style="width: 12px; height: 12px;"></i>
                <span>${evt.started}</span>
              </span>
            </div>
          </div>
          <div class="event-right">
            <div class="event-metric">
              <span class="metric-value">${evt.val}</span>
              <div class="metric-label">${evt.label}</div>
            </div>
            <i data-lucide="chevron-right" style="color: var(--text-muted);"></i>
          </div>
        </div>
      `;
    });
  }

  // Render predictions
  predictionsContainer.innerHTML = '';
  data.predictions.forEach(pred => {
    predictionsContainer.innerHTML += `
      <div class="prediction-row">
        <span class="day-label">${pred.day}</span>
        <span class="badge-status" style="background-color: var(--${pred.color}-light); color: var(--${pred.color}); text-align: center;">${pred.status}</span>
        <div class="bar-container">
          <div class="fill-bar" style="width: ${pred.pct}%; background-color: var(--${pred.color});"></div>
        </div>
        <span class="percentage-val">${pred.pct}%</span>
      </div>
    `;
  });

  // Re-create icons since elements were injected dynamically
  lucide.createIcons();
}

// Event Listeners for Popular Tags
document.querySelectorAll('.popular-tags .tag').forEach(tag => {
  tag.addEventListener('click', (e) => {
    e.preventDefault();
    const loc = tag.getAttribute('data-loc');
    updateDashboard(loc);
  });
});

// Search input handling
locationInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    const query = locationInput.value.trim().toLowerCase();
    if (mockLocationData[query]) {
      updateDashboard(query);
    } else {
      // Fallback/Simulated search logic
      alert(`Simulating search for "${locationInput.value}". Showing results for Vijayawada.`);
      updateDashboard("vijayawada");
    }
  }
});

// Share Location Button simulation
btnShareLocation.addEventListener('click', () => {
  btnShareLocation.disabled = true;
  btnShareLocation.innerHTML = `
    <i data-lucide="loader" class="animate-spin" style="width: 14px; height: 14px;"></i>
    <span>Locating...</span>
  `;
  lucide.createIcons();

  setTimeout(() => {
    btnShareLocation.disabled = false;
    btnShareLocation.innerHTML = `
      <i data-lucide="navigation" style="width: 14px; height: 14px;"></i>
      <span>Share Location</span>
    `;
    lucide.createIcons();
    updateDashboard("hyderabad");
  }, 1000);
});

// Toggle Sidebar (Responsive)
toggleSidebarBtn.addEventListener('click', () => {
  sidebar.classList.toggle('collapsed');
  // Simple styling to slide sidebar on mobile
  if (sidebar.style.display === 'none') {
    sidebar.style.display = 'flex';
  } else if (window.innerWidth <= 900) {
    sidebar.style.display = 'none';
  }
});

// Active menu item toggling
document.querySelectorAll('.sidebar-menu .menu-item').forEach(item => {
  item.addEventListener('click', () => {
    document.querySelector('.sidebar-menu .menu-item.active').classList.remove('active');
    item.classList.add('active');
  });
});

// Theme Toggle (Dark / Light Mode)
themeToggleBtn.addEventListener('click', () => {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  let newTheme = 'light';
  
  if (currentTheme === 'light' || !currentTheme) {
    newTheme = 'dark';
    themeIcon.setAttribute('data-lucide', 'sun');
  } else {
    themeIcon.setAttribute('data-lucide', 'moon');
  }
  
  document.documentElement.setAttribute('data-theme', newTheme);
  lucide.createIcons();
});

// Trigger change location on active bar clicks
document.getElementById('change-location-trigger').addEventListener('click', () => {
  locationInput.focus();
  locationInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
});

// Default initial state
updateDashboard("hyderabad");
