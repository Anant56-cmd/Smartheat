document.addEventListener('DOMContentLoaded', function () {
  const tempRange = document.getElementById('tempRange');
  const tempInput = document.getElementById('tempInput');
  const tempDisplay = document.getElementById('tempDisplay');

  const humRange = document.getElementById('humidityRange');
  const humInput = document.getElementById('humidityInput');
  const humDisplay = document.getElementById('humidityDisplay');

  const form = document.getElementById('predictionForm');
  const predictBtn = document.getElementById('predictBtn');

  // Sliders sync
  if (tempRange && tempInput && tempDisplay) {
    tempRange.addEventListener('input', function () {
      tempInput.value = this.value;
      tempDisplay.innerText = this.value + '°C';
    });
    tempInput.addEventListener('input', function () {
      tempRange.value = this.value;
      tempDisplay.innerText = this.value + '°C';
    });
  }

  if (humRange && humInput && humDisplay) {
    humRange.addEventListener('input', function () {
      humInput.value = this.value;
      humDisplay.innerText = this.value + '%';
    });
    humInput.addEventListener('input', function () {
      humRange.value = this.value;
      humDisplay.innerText = this.value + '%';
    });
  }

  // Real-time Station Weather Fetcher
  const btnLoadLive = document.getElementById('btnLoadLiveWeather');
  const liveBadge = document.getElementById('liveSourceBadge');
  const locationSelect = document.getElementById('predLocation');

  if (btnLoadLive && locationSelect) {
    btnLoadLive.addEventListener('click', function () {
      const locId = locationSelect.value;
      btnLoadLive.disabled = true;
      btnLoadLive.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Querying Open-Meteo API...';

      fetch(`/weather/api/live-station/${locId}`)
        .then(res => res.json())
        .then(resData => {
          btnLoadLive.disabled = false;
          btnLoadLive.innerHTML = '<i class="bi bi-broadcast"></i> Fetch Real-Time Weather for Station';

          if (resData.success && resData.data) {
            const d = resData.data;
            tempInput.value = d.temperature;
            tempRange.value = d.temperature;
            tempDisplay.innerText = d.temperature + '°C';

            humInput.value = d.humidity;
            humRange.value = d.humidity;
            humDisplay.innerText = d.humidity + '%';

            if (document.getElementById('windInput')) document.getElementById('windInput').value = d.wind_speed;
            if (document.getElementById('rainInput')) document.getElementById('rainInput').value = d.rainfall;
            if (document.getElementById('pressureInput')) document.getElementById('pressureInput').value = d.pressure;

            if (liveBadge) {
              liveBadge.classList.remove('d-none');
              liveBadge.innerHTML = `<i class="bi bi-check-circle-fill text-success"></i> Live data loaded for ${d.location_name} (${d.temperature}°C, ${d.humidity}%, ${d.source})`;
            }
          } else {
            alert('Could not retrieve live reading for station.');
          }
        })
        .catch(err => {
          btnLoadLive.disabled = false;
          btnLoadLive.innerHTML = '<i class="bi bi-broadcast"></i> Fetch Real-Time Weather for Station';
          console.error(err);
          alert('Network timeout while querying live weather API.');
        });
    });
  }

  // Prediction submit
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      predictBtn.disabled = true;
      predictBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Computing Prediction...';

      const payload = {
        location_id: document.getElementById('predLocation').value,
        temperature: parseFloat(tempInput.value),
        humidity: parseFloat(humInput.value),
        wind_speed: parseFloat(document.getElementById('windInput').value || 10.0),
        rainfall: parseFloat(document.getElementById('rainInput').value || 0.0),
        pressure: parseFloat(document.getElementById('pressureInput').value || 1013.25)
      };

      fetch('/predictions/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      })
        .then(res => res.json())
        .then(data => {
          predictBtn.disabled = false;
          predictBtn.innerHTML = '<i class="bi bi-lightning-charge-fill me-1"></i> Run Prediction & Risk Score';

          if (!data.success) {
            alert('Error running inference: ' + (data.error || 'Unknown error'));
            return;
          }

          // Unhide result container
          const placeholder = document.getElementById('resultPlaceholder');
          const content = document.getElementById('resultContent');
          if (placeholder) placeholder.classList.add('d-none');
          if (content) content.classList.remove('d-none');

          // Render Risk Category Badge
          const riskBadge = document.getElementById('resRiskBadge');
          const riskLevel = data.prediction.predicted_risk;
          riskBadge.innerText = riskLevel;
          riskBadge.className = 'fs-3 fw-bold my-1 badge-risk-' + riskLevel.toLowerCase();

          // Numerical values
          document.getElementById('resConfidence').innerText = data.prediction.confidence + '%';
          document.getElementById('resHeatIndex').innerText = data.prediction.heat_index + '°C';
          document.getElementById('resTotalScore').innerText = data.risk_assessment.total_risk_score + ' / 100';

          // Component Progress bars
          const hazard = data.risk_assessment.hazard_score;
          const vuln = data.risk_assessment.vulnerability_score;
          const expo = data.risk_assessment.exposure_score;
          const def = data.risk_assessment.deficit_score;

          document.getElementById('resHazardVal').innerText = hazard + ' / 100';
          document.getElementById('resHazardBar').style.width = hazard + '%';

          document.getElementById('resVulnVal').innerText = vuln + ' / 100';
          document.getElementById('resVulnBar').style.width = vuln + '%';

          document.getElementById('resExpoVal').innerText = expo + ' / 100';
          document.getElementById('resExpoBar').style.width = expo + '%';

          document.getElementById('resDeficitVal').innerText = def + ' / 100';
          document.getElementById('resDeficitBar').style.width = def + '%';

          // Early warning alert badge
          const alertBadge = document.getElementById('alertTriggerBadge');
          if (data.alert_triggered) {
            alertBadge.classList.remove('d-none');
          } else {
            alertBadge.classList.add('d-none');
          }

          // Render Explainable AI (XAI) Attribution
          const xaiContainer = document.getElementById('xaiContainer');
          const xaiList = document.getElementById('xaiAttributionList');
          const xaiCounterfactual = document.getElementById('xaiCounterfactual');

          if (xaiContainer && xaiList && data.prediction.explainability && data.prediction.explainability.feature_attributions) {
            xaiContainer.classList.remove('d-none');
            xaiList.innerHTML = '';
            
            const attrs = data.prediction.explainability.feature_attributions.slice(0, 4);
            attrs.forEach(item => {
              const isIncrease = item.direction === 'INCREASES_RISK';
              const badgeClass = isIncrease ? 'text-danger' : 'text-success';
              const icon = isIncrease ? 'bi-arrow-up-circle-fill' : 'bi-arrow-down-circle-fill';
              const barClass = isIncrease ? 'bg-danger' : 'bg-success';

              const div = document.createElement('div');
              div.className = 'mb-2';
              div.innerHTML = `
                <div class="d-flex justify-content-between small">
                  <span><i class="bi ${icon} ${badgeClass} me-1"></i>${item.display_name} (${item.value})</span>
                  <span class="fw-bold ${badgeClass}">${isIncrease ? '+' : '-'}${item.percentage}%</span>
                </div>
                <div class="progress" style="height: 5px;">
                  <div class="progress-bar ${barClass}" style="width: ${item.percentage}%;"></div>
                </div>
              `;
              xaiList.appendChild(div);
            });

            // Counterfactual hint
            const cf = data.prediction.explainability.counterfactuals;
            if (cf && cf.length > 0 && xaiCounterfactual) {
              xaiCounterfactual.classList.remove('d-none');
              xaiCounterfactual.innerHTML = `<strong><i class="bi bi-lightbulb-fill text-warning me-1"></i>Remediation Insight:</strong> ${cf[0].action} &rarr; drops predicted risk to <span class="badge bg-secondary">${cf[0].resulting_tier}</span>.`;
            } else if (xaiCounterfactual) {
              xaiCounterfactual.classList.add('d-none');
            }
          }

          // Recommendations
          const recList = document.getElementById('resRecList');
          recList.innerHTML = '';
          if (data.recommendations && data.recommendations.length > 0) {
            data.recommendations.forEach(rec => {
              const li = document.createElement('li');
              li.className = 'mb-1';
              li.innerHTML = `<strong>[${rec.priority}] ${rec.title}</strong>: ${rec.description}`;
              recList.appendChild(li);
            });
          } else {
            recList.innerHTML = '<li>Routine monitoring advisories apply.</li>';
          }
        })
        .catch(err => {
          predictBtn.disabled = false;
          predictBtn.innerHTML = '<i class="bi bi-lightning-charge-fill me-1"></i> Run Prediction & Risk Score';
          console.error(err);
          alert('Network or server error during prediction.');
        });
    });
  }
});
