document.addEventListener('DOMContentLoaded', function () {
  // 1. Sidebar toggle for mobile devices
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('d-none');
    });
  }

  // 2. Auto dismiss flash alerts after 6 seconds
  const flashAlerts = document.querySelectorAll('.alert-dismissible');
  flashAlerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 6000);
  });

  // 3. Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 4. Universal Navbar City Search Handler
  const navSearch = document.getElementById('navCitySearch');
  const navResults = document.getElementById('navSearchResults');
  let navTimer = null;

  if (navSearch && navResults) {
    navSearch.addEventListener('input', function () {
      clearTimeout(navTimer);
      const query = this.value.trim();
      if (query.length < 2) {
        navResults.classList.add('d-none');
        navResults.innerHTML = '';
        return;
      }

      navTimer = setTimeout(function () {
        fetch(`/weather/api/search-city?q=${encodeURIComponent(query)}`)
          .then(res => res.json())
          .then(data => {
            navResults.innerHTML = '';
            if (data.results && data.results.length > 0) {
              navResults.classList.remove('d-none');
              data.results.forEach(city => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'list-group-item list-group-item-action py-2 text-start small d-flex justify-content-between align-items-center';
                btn.innerHTML = `
                  <div>
                    <i class="bi bi-geo-alt-fill text-danger me-1"></i>
                    <strong>${city.name}</strong>, <span class="text-muted">${city.state}</span>
                  </div>
                  <span class="badge bg-primary-subtle text-primary small">Live</span>
                `;
                btn.addEventListener('click', function () {
                  navResults.classList.add('d-none');
                  navSearch.value = city.name;
                  
                  // Add city and redirect to GIS map
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
                      if (resp.success) {
                        window.location.href = '/map/';
                      } else {
                        alert('Could not add city: ' + resp.error);
                      }
                    });
                });
                navResults.appendChild(btn);
              });
            } else {
              navResults.classList.remove('d-none');
              navResults.innerHTML = '<div class="p-2 text-muted small">No matching cities found.</div>';
            }
          })
          .catch(err => console.error('Navbar search error:', err));
      }, 300);
    });

    document.addEventListener('click', function (e) {
      if (!navSearch.contains(e.target) && !navResults.contains(e.target)) {
        navResults.classList.add('d-none');
      }
    });
  }
});

