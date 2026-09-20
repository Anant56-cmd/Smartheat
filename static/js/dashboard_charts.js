document.addEventListener('DOMContentLoaded', function () {
  fetch('/dashboard/api/chart-data')
    .then(response => response.json())
    .then(data => {
      // 1. Temperature & Heat Index Trend Line Chart
      const trendCtx = document.getElementById('tempTrendChart');
      if (trendCtx && data.trends) {
        new Chart(trendCtx, {
          type: 'line',
          data: {
            labels: data.trends.labels,
            datasets: [
              {
                label: 'Mean Temperature (°C)',
                data: data.trends.avg_temp,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
              },
              {
                label: 'Calculated Heat Index (°C)',
                data: data.trends.avg_hi,
                borderColor: '#ea580c',
                borderDash: [5, 5],
                borderWidth: 2,
                tension: 0.3,
                fill: false
              },
              {
                label: 'Max Peak Temp (°C)',
                data: data.trends.max_temp,
                borderColor: '#dc2626',
                backgroundColor: 'transparent',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 3
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
              mode: 'index',
              intersect: false
            },
            plugins: {
              legend: {
                position: 'top',
                labels: { boxWidth: 12, font: { size: 12 } }
              },
              tooltip: {
                callbacks: {
                  label: function (context) {
                    return ` ${context.dataset.label}: ${context.raw}°C`;
                  }
                }
              }
            },
            scales: {
              y: {
                title: { display: true, text: 'Temperature (°C)' },
                min: 20
              }
            }
          }
        });
      }

      // 2. Risk Level Distribution Doughnut Chart
      const riskCtx = document.getElementById('riskDistChart');
      if (riskCtx && data.risk_distribution) {
        new Chart(riskCtx, {
          type: 'doughnut',
          data: {
            labels: data.risk_distribution.labels,
            datasets: [{
              data: data.risk_distribution.data,
              backgroundColor: [
                '#10b981', // Low
                '#f59e0b', // Moderate
                '#ea580c', // High
                '#dc2626'  // Extreme
              ],
              borderWidth: 2,
              borderColor: '#ffffff'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: { boxWidth: 12, padding: 14 }
              }
            },
            cutout: '65%'
          }
        });
      }

      // 3. Feature Importance Bar Chart
      const featCtx = document.getElementById('featureImpChart');
      if (featCtx && data.feature_importance) {
        new Chart(featCtx, {
          type: 'bar',
          data: {
            labels: data.feature_importance.labels,
            datasets: [{
              label: 'Importance (%)',
              data: data.feature_importance.data,
              backgroundColor: '#0284c7',
              borderRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: {
                beginAtZero: true,
                title: { display: true, text: 'Contribution Weight (%)' }
              }
            }
          }
        });
      }

      // 4. Ground-Level Vulnerability Horizontal Bar Chart
      const vulnCtx = document.getElementById('vulnDistChart');
      if (vulnCtx && data.vulnerability) {
        new Chart(vulnCtx, {
          type: 'bar',
          data: {
            labels: data.vulnerability.labels,
            datasets: [{
              label: 'Vulnerability Score (0-100)',
              data: data.vulnerability.scores,
              backgroundColor: data.vulnerability.scores.map(s => {
                if (s >= 75) return '#dc2626';
                if (s >= 50) return '#ea580c';
                if (s >= 25) return '#f59e0b';
                return '#10b981';
              }),
              borderRadius: 4
            }]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              x: {
                beginAtZero: true,
                max: 100,
                title: { display: true, text: 'Vulnerability Index' }
              }
            }
          }
        });
      }
    })
    .catch(err => {
      console.error('Error fetching dashboard chart data:', err);
    });
});
