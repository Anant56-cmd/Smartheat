document.addEventListener('DOMContentLoaded', function () {
  const mapElement = document.getElementById('gis-map');
  if (!mapElement) return;

  // 1. Initialize Map with Pan-India National Scope
  const indiaCenter = [22.8, 79.5];
  const initialZoom = 5;

  const map = L.map('gis-map', {
    center: indiaCenter,
    zoom: initialZoom,
    zoomControl: true
  });

  // OpenStreetMap Tile Layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | SMARTHEAT GIS'
  }).addTo(map);

  // 2. Layer Groups
  const riskLayer = L.layerGroup().addTo(map);
  const hospitalLayer = L.layerGroup().addTo(map);
  const coolingLayer = L.layerGroup().addTo(map);
  const waterLayer = L.layerGroup().addTo(map);

  // Colors mapping for risk levels
  const riskColors = {
    'LOW': '#10b981',
    'MODERATE': '#f59e0b',
    'HIGH': '#ea580c',
    'EXTREME': '#dc2626'
  };

  // 3. Fetch Map Data
  fetch('/map/api/data')
    .then(res => res.json())
    .then(data => {
      // Add Monitored Heat-Risk Locations
      if (data.locations) {
        data.locations.forEach(loc => {
          const color = riskColors[loc.risk_level] || '#3b82f6';
          
          const marker = L.circleMarker([loc.lat, loc.lng], {
            radius: loc.risk_level === 'EXTREME' ? 16 : (loc.risk_level === 'HIGH' ? 14 : 11),
            fillColor: color,
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.85
          });

          // Popup Content
          const alertBanner = loc.has_active_alert
            ? `<div class="p-1 mb-2 bg-danger text-white rounded small text-center fw-bold"><i class="bi bi-bell-fill"></i> ACTIVE EARLY WARNING</div>`
            : '';

          const recsHtml = loc.recommendations && loc.recommendations.length > 0
            ? loc.recommendations.map(r => `<li class="small text-muted">${r}</li>`).join('')
            : '<li class="small text-muted">Routine monitoring advisories.</li>';

          const popupContent = `
            <div style="min-width: 240px; padding: 2px;">
              ${alertBanner}
              <div class="map-popup-title">${loc.name} <span class="text-muted small fw-normal">(${loc.state})</span></div>
              <div class="d-flex justify-content-between mb-1">
                <span>Observed Temp:</span> <strong>${loc.temperature}°C</strong>
              </div>
              <div class="d-flex justify-content-between mb-1">
                <span>NOAA Heat Index:</span> <strong class="text-danger">${loc.heat_index}°C</strong>
              </div>
              <div class="d-flex justify-content-between mb-1">
                <span>Vulnerability Score:</span> <span>${loc.vulnerability_score}/100</span>
              </div>
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span>Composite Risk:</span>
                <span class="badge-risk-${loc.risk_level.toLowerCase()}">${loc.risk_level} (${loc.total_risk_score}/100)</span>
              </div>
              <div class="border-top pt-2 mt-2">
                <div class="fw-bold small text-secondary mb-1">Response Action:</div>
                <ul class="ps-3 mb-0">${recsHtml}</ul>
              </div>
            </div>
          `;

          marker.bindPopup(popupContent);
          riskLayer.addLayer(marker);
        });
      }

      // Add Critical Facilities (Hospitals, Cooling Shelters, Water Points)
      if (data.facilities) {
        data.facilities.forEach(fac => {
          let iconHtml = '';
          let targetLayer = null;

          if (fac.facility_type === 'Hospital') {
            iconHtml = `<div style="background-color:#ef4444; color:white; width:26px; height:26px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:14px; box-shadow:0 2px 4px rgba(0,0,0,0.3); border:2px solid white;">✚</div>`;
            targetLayer = hospitalLayer;
          } else if (fac.facility_type === 'Cooling Center') {
            iconHtml = `<div style="background-color:#2563eb; color:white; width:26px; height:26px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:14px; box-shadow:0 2px 4px rgba(0,0,0,0.3); border:2px solid white;">❄</div>`;
            targetLayer = coolingLayer;
          } else { // Water Point
            iconHtml = `<div style="background-color:#06b6d4; color:white; width:26px; height:26px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:14px; box-shadow:0 2px 4px rgba(0,0,0,0.3); border:2px solid white;">💧</div>`;
            targetLayer = waterLayer;
          }

          const customIcon = L.divIcon({
            html: iconHtml,
            className: 'custom-facility-icon',
            iconSize: [26, 26],
            iconAnchor: [13, 13],
            popupAnchor: [0, -13]
          });

          const fMarker = L.marker([fac.lat, fac.lng], { icon: customIcon });
          const fPopup = `
            <div style="min-width: 200px;">
              <div class="map-popup-title">${fac.name}</div>
              <div class="small text-muted mb-1"><i class="bi bi-tag"></i> <strong>${fac.facility_type}</strong></div>
              <div class="small mb-1">Serving: <strong>${fac.location_name}</strong></div>
              <div class="small mb-1">Capacity: <strong>${fac.capacity} Persons/Day</strong></div>
              <div class="small"><i class="bi bi-telephone"></i> Emergency Helpline: <strong>${fac.contact_phone}</strong></div>
            </div>
          `;
          fMarker.bindPopup(fPopup);
          if (targetLayer) targetLayer.addLayer(fMarker);
        });
      }
    })
    .catch(err => console.error('Error loading GIS data:', err));

  // 4. Map Legend Control
  const legend = L.control({ position: 'bottomright' });
  legend.onAdd = function () {
    const div = L.DomUtil.create('div', 'map-legend');
    div.innerHTML = `
      <div class="fw-bold mb-1 border-bottom pb-1">Heat-Risk Legend</div>
      <div><span class="legend-color" style="background: #10b981;"></span> Low Risk (0–25)</div>
      <div><span class="legend-color" style="background: #f59e0b;"></span> Moderate (26–50)</div>
      <div><span class="legend-color" style="background: #ea580c;"></span> High Risk (51–75)</div>
      <div><span class="legend-color" style="background: #dc2626;"></span> Extreme Risk (76–100)</div>
      <hr class="my-1">
      <div class="fw-bold mb-1">Emergency Infrastructure</div>
      <div><span style="color:#ef4444; font-weight:bold;">✚</span> Hospital / Heat Ward</div>
      <div><span style="color:#2563eb; font-weight:bold;">❄</span> Public Cooling Shelter</div>
      <div><span style="color:#06b6d4; font-weight:bold;">💧</span> Water Tanker Facility</div>
    `;
    return div;
  };
  legend.addTo(map);

  // 5. Layer Toggle Checkbox Events
  document.getElementById('layerRisk').addEventListener('change', function () {
    if (this.checked) map.addLayer(riskLayer); else map.removeLayer(riskLayer);
  });
  document.getElementById('layerHospitals').addEventListener('change', function () {
    if (this.checked) map.addLayer(hospitalLayer); else map.removeLayer(hospitalLayer);
  });
  document.getElementById('layerCooling').addEventListener('change', function () {
    if (this.checked) map.addLayer(coolingLayer); else map.removeLayer(coolingLayer);
  });
  document.getElementById('layerWater').addEventListener('change', function () {
    if (this.checked) map.addLayer(waterLayer); else map.removeLayer(waterLayer);
  });

  // 6. Center Map Button
  const resetBtn = document.getElementById('btnResetView');
  if (resetBtn) {
    resetBtn.addEventListener('click', function () {
      map.setView(initialCenter, initialZoom);
    });
  }

  // 7. Dynamic City Search & Mapping
  const mapSearch = document.getElementById('mapCitySearch');
  const searchResults = document.getElementById('mapSearchResults');
  let searchTimer = null;

  if (mapSearch && searchResults) {
    mapSearch.addEventListener('input', function () {
      clearTimeout(searchTimer);
      const query = this.value.trim();
      if (query.length < 2) {
        searchResults.classList.add('d-none');
        searchResults.innerHTML = '';
        return;
      }

      searchTimer = setTimeout(function () {
        fetch(`/weather/api/search-city?q=${encodeURIComponent(query)}`)
          .then(res => res.json())
          .then(data => {
            searchResults.innerHTML = '';
            if (data.results && data.results.length > 0) {
              searchResults.classList.remove('d-none');
              data.results.forEach(city => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'list-group-item list-group-item-action py-2 text-start small';
                btn.innerHTML = `<i class="bi bi-geo-alt me-1 text-primary"></i> <strong>${city.name}</strong>, <span class="text-muted">${city.state}</span>`;
                btn.addEventListener('click', function () {
                  addAndMapCity(city);
                });
                searchResults.appendChild(btn);
              });
            } else {
              searchResults.classList.remove('d-none');
              searchResults.innerHTML = '<div class="p-2 text-muted small">No matching cities found.</div>';
            }
          })
          .catch(err => console.error('Search error:', err));
      }, 300);
    });

    // Close on click outside
    document.addEventListener('click', function (e) {
      if (!mapSearch.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.classList.add('d-none');
      }
    });
  }

  function addAndMapCity(city) {
    searchResults.classList.add('d-none');
    mapSearch.value = city.name;

    fetch('/weather/api/add-city', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: city.name,
        state: city.state,
        latitude: city.latitude,
        longitude: city.longitude
      })
    })
      .then(res => res.json())
      .then(resp => {
        if (resp.success && resp.data) {
          const d = resp.data;
          const color = riskColors[d.risk_level] || '#3b82f6';

          const marker = L.circleMarker([d.latitude, d.longitude], {
            radius: 15,
            fillColor: color,
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
          });

          const popupHtml = `
            <div style="min-width: 220px;">
              <div class="map-popup-title">${d.name} <span class="text-muted small fw-normal">(${d.state})</span></div>
              <div class="small mb-1"><span class="badge bg-success-subtle text-success border border-success-subtle">Live WMO Feed</span></div>
              <div class="d-flex justify-content-between mb-1">
                <span>Current Temp:</span> <strong>${d.temperature}°C</strong>
              </div>
              <div class="d-flex justify-content-between mb-1">
                <span>Heat Index:</span> <strong class="text-danger">${d.heat_index}°C</strong>
              </div>
              <div class="d-flex justify-content-between align-items-center mb-1">
                <span>Risk Level:</span>
                <span class="badge-risk-${d.risk_level.toLowerCase()}">${d.risk_level} (${d.risk_score}/100)</span>
              </div>
            </div>
          `;

          marker.bindPopup(popupHtml);
          riskLayer.addLayer(marker);

          // Fly to the newly added city
          map.flyTo([d.latitude, d.longitude], 10, { duration: 1.5 });
          setTimeout(() => marker.openPopup(), 1600);
        } else {
          alert('Could not add and map city: ' + (resp.error || 'Unknown error'));
        }
      })
      .catch(err => {
        console.error('Error adding city:', err);
        alert('Network error while adding city.');
      });
  }
});

