# SMARTHEAT: Pan-India AI Disaster Intelligence & Municipal Logistics Platform

<div align="center">

[![Live Platform](https://img.shields.io/badge/Live%20Demo-smartheat--yxyi.onrender.com-brightgreen?style=for-the-badge&logo=render)](https://smartheat-yxyi.onrender.com)
[![Swagger UI Docs](https://img.shields.io/badge/OpenAPI%203.0-Interactive%20Docs-blue?style=for-the-badge&logo=swagger)](https://smartheat-yxyi.onrender.com/api/docs)
[![Python](https://img.shields.io/badge/Python-3.12-yellow?style=for-the-badge&logo=python)](https://python.org)
[![Accuracy](https://img.shields.io/badge/ML%20Accuracy-92.4%25-orange?style=for-the-badge)](https://smartheat-yxyi.onrender.com/simulator)
[![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

**An End-to-End Civic Intelligence, Explainable AI (XAI), and Capacitated Vehicle Routing (CVRP) Platform for National Heatwave Disaster Management.**

[Explore Live Demo](https://smartheat-yxyi.onrender.com) • [API Documentation](https://smartheat-yxyi.onrender.com/api/docs) • [CAP XML Feed](https://smartheat-yxyi.onrender.com/api/v1/alerts/cap.xml) • [System Health](https://smartheat-yxyi.onrender.com/api/v1/health)

</div>

---

## Table of Contents
1. [Platform Overview](#1-platform-overview)
2. [Pan-India Monitoring Coverage (24 Metropolises)](#2-pan-india-monitoring-coverage-24-metropolises)
3. [Core Capabilities & Modules](#3-core-capabilities--modules)
4. [Machine Learning & Explainable AI (XAI) Pipeline](#4-machine-learning--explainable-ai-xai-pipeline)
5. [Municipal Logistics & CVRP Fleet Optimizer](#5-municipal-logistics--cvrp-fleet-optimizer)
6. [Standards-Compliant Emergency Alerting (OASIS CAP v1.2)](#6-standards-compliant-emergency-alerting-oasis-cap-v12)
7. [System Architecture](#7-system-architecture)
8. [Transparent Heat Risk Formula (0–100)](#8-transparent-heat-risk-formula-0100)
9. [Interactive GIS Heat-Risk Mapping](#9-interactive-gis-heat-risk-mapping)
10. [Database Schema & ER Models](#10-database-schema--er-models)
11. [SRE Telemetry & Prometheus Observability](#11-sre-telemetry--prometheus-observability)
12. [Step-by-Step Local Setup & Execution](#12-step-by-step-local-setup--execution)
13. [Executive Project Pitch](#13-executive-project-pitch)
14. [Technical Interview & Defense Guide](#14-technical-interview--defense-guide)

---

## 1. Platform Overview

Rising global temperatures and intensified Urban Heat Island (UHI) effects have transformed extreme heat waves into one of South Asia's most lethal climatic hazards. Traditional weather broadcasts report raw dry-bulb temperatures, failing to capture compound physiological thermal stress, relative humidity, socio-demographic vulnerability, informal settlement exposure, and municipal healthcare deficits.

**SMARTHEAT** is a production-grade disaster management and municipal logistics platform designed to bridge this operational gap. It combines real-time meteorological ingestion, machine learning risk classification, explainable feature attribution, emergency cell broadcast feeds, and operations research vehicle routing algorithms to protect vulnerable urban populations.

### Key Highlights
- **Pan-India Coverage**: Continuous real-time monitoring across 24 major Indian metropolises spanning all 6 climatic zones.
- **High-Accuracy ML**: Random Forest classifier trained on 10 thermodynamic features achieving **92.4% test accuracy** and **0.91 weighted F1-score**.
- **Explainable AI (XAI)**: Contrastive tree perturbation that decomposes predictions into percentage-level feature contributions and outputs actionable remediation counterfactuals.
- **Logistics Optimization**: Solves the Capacitated Vehicle Routing Problem (CVRP) with 2-Opt local search heuristics and Priority-Greedy Max-Heap scheduling ($O(N \log N)$) to automate municipal water tanker dispatches.
- **OASIS CAP v1.2 Compliance**: Emits validated ITU-T X.1303 / OASIS Common Alerting Protocol XML feeds for national telecom cell broadcasts and NDMA/SDMA integration.
- **Enterprise SRE Architecture**: Sub-millisecond Prometheus telemetry scrapers (`/api/v1/metrics`), liveness/readiness health probes (`/api/v1/health`), and OpenAPI 3.0 Swagger UI documentation (`/api/docs`).

---

## 2. Pan-India Monitoring Coverage (24 Metropolises)

SMARTHEAT ingests meteorological telemetry across all **6 primary Indian climatic zones**:

```
                                  [ INDIA ]
                                      │
         ┌───────────────┬────────────┴───────────┬───────────────┐
         ▼               ▼                        ▼               ▼
   [ NORTH ZONE ]  [ NORTHWEST / ARID ]     [ EAST ZONE ]   [ WEST & CENTRAL ]
   - New Delhi     - Jaipur                 - Rourkela      - Mumbai
   - Lucknow       - Jodhpur                - Bhubaneswar   - Pune
   - Varanasi      - Ahmedabad              - Cuttack       - Bhopal
   - Chandigarh    - Nagpur                 - Jharsuguda    - Raipur
                                            - Sambalpur
                                            - Jamshedpur          ▼
                                            - Ranchi        [ SOUTH ZONE ]
                                            - Kolkata       - Hyderabad
                                            - Patna         - Chennai
                                                            - Bengaluru
```

1. **East Zone & Industrial Belt**: Rourkela, Jharsuguda, Sambalpur, Bhubaneswar, Cuttack, Jamshedpur, Ranchi, Kolkata, Patna.
2. **North Zone & Gangetic Plain**: New Delhi, Lucknow, Varanasi, Chandigarh.
3. **Northwest & Arid Desert Zone**: Jaipur, Jodhpur, Ahmedabad, Nagpur.
4. **West & Central Zone**: Mumbai, Pune, Bhopal, Raipur.
5. **South Zone**: Hyderabad, Chennai, Bengaluru.

---

## 3. Core Capabilities & Modules

| Module | Title | Primary Functionality |
|---|---|---|
| **Module 1** | **Authentication & RBAC** | Username or Gmail login, self-service account registration, role-based access control (Admin / User), Werkzeug password hashing. |
| **Module 2** | **Real-Time Weather Ingestion** | Open-Meteo WMO live synchronization, bounds checking, thermodynamic feature engineering, NOAA Heat Index calculation. |
| **Module 3** | **Universal City Search** | Global geocoding integration allowing operators to query any Indian or international city, fetch live weather, and compute on-demand risk indices. |
| **Module 4** | **Heatwave ML Pipeline** | 10 engineered thermodynamic features, Random Forest classifier, 92.4% test accuracy, serialized `.joblib` model caching. |
| **Module 5** | **Explainable AI (XAI)** | Local contrastive tree perturbation attribution engine decomposing predictions into percentage-level drivers with counterfactual interventions. |
| **Module 6** | **Composite Risk Scoring** | Multi-dimensional 0–100 index combining Hazard (45%), Demographic Vulnerability (30%), Exposure (15%), and Healthcare Deficits (10%). |
| **Module 7** | **Interactive GIS Heat Map** | Pan-India Leaflet.js map with color-coded circular risk markers (Low, Moderate, High, Extreme) and 33 critical facility overlays (Hospitals, Cooling Shelters, Water Hubs). |
| **Module 8** | **Municipal CVRP Optimizer** | Capacitated Vehicle Routing solver with 2-Opt local search and Priority-Greedy Max-Heap scheduling ($O(N \log N)$) for water tanker fleet dispatch. |
| **Module 9** | **OASIS CAP v1.2 Alert Feed** | RFC / ITU-T X.1303-compliant XML emergency alert feed for telecom cell broadcasts and NDMA integration. |
| **Module 10** | **OpenAPI 3.0 Documentation** | Interactive Swagger UI (`/api/docs`) enabling zero-friction developer integration and client testing. |
| **Module 11** | **Early Warning & SOP Engine** | Lifecycle management for Yellow, Orange, and Red warnings with automated multi-sectoral Standard Operating Procedures (Health, Labor, Municipal). |
| **Module 12** | **SRE Observability** | Liveness probe (`/api/v1/health`), Prometheus metrics exposition (`/api/v1/metrics`), p50/p95 request latency middleware. |

---

## 4. Machine Learning & Explainable AI (XAI) Pipeline

### 4.1 Thermodynamic Feature Engineering
Rather than relying solely on dry-bulb temperature, SMARTHEAT constructs **10 domain-specific thermodynamic features**:
1. **NOAA Heat Index ($HI$ in °C)**: Derived via the Rothfusz regression equation with low/high relative humidity boundary adjustments.
2. **Ambient Dry-Bulb Temperature ($T$ in °C)**: Air temperature measurement.
3. **Relative Humidity ($RH$ in %)**: Atmospheric moisture percentage.
4. **Wind Velocity ($\text{km/h}$)**: Convective surface cooling rate.
5. **Precipitation ($\text{mm}$)**: Surface cooling and moisture factor.
6. **Atmospheric Pressure ($\text{hPa}$)**: Detects sinking air masses in persistent high-pressure heat domes.
7. **Temp-Humidity Interaction Product**: $(T \times RH) / 100.0$.
8. **Dew Point Approximation**: Magnus formula approximation: $T - ((100 - RH) / 5.0)$.
9. **Wind Cooling Offset**: $T - (0.05 \times \text{wind\_speed})$.
10. **Vapor Pressure Estimate**: Non-linear saturation pressure formulation.

### 4.2 Target Classification Classes
- **`LOW`**: Heat Index $< 32^\circ\text{C}$ (Normal comfort conditions).
- **`MODERATE`**: Heat Index $32^\circ\text{C} \le HI < 41^\circ\text{C}$ (Caution; fatigue with prolonged exposure).
- **`HIGH`**: Heat Index $41^\circ\text{C} \le HI < 54^\circ\text{C}$ (Orange Warning; heat exhaustion likely, cramps imminent).
- **`EXTREME`**: Heat Index $\ge 54^\circ\text{C}$ or $T \ge 45^\circ\text{C}$ (Red Alert; heat stroke imminent, life-threatening).

### 4.3 Model Validation & Performance
- **Algorithm**: Random Forest Classifier (100 estimators, max depth 10, balanced class weighting).
- **Dataset**: Ingested historical daily meteorological observations from Open-Meteo ERA5 / WMO reanalysis archives across the Pan-India network.
- **Evaluation**:
  - **Test Accuracy**: **92.4%**
  - **Weighted F1-Score**: **0.91**
  - Multi-class Confusion Matrix evaluated across all 4 severity tiers.

### 4.4 Explainable AI (XAI) & Counterfactual Reasoning
To eliminate black-box opacity in disaster response:
- **Local Feature Attribution**: Contrastive tree perturbation measures the marginal probability shift when replacing individual features with an urban neutral baseline ($28^\circ\text{C}, 45\%\text{ RH}$):
  $$\text{Contribution}_j = P(y = \text{Target} \mid \mathbf{x}) - P(y = \text{Target} \mid \mathbf{x}_{-j}, \bar{x}_j)$$
- **Remediation Counterfactuals**: Calculates minimal actionable microclimate adjustments (e.g. wet-bulb reduction via misting or urban canopy shading) required to downgrade a ward's risk category.
- **Endpoint**: `POST /api/v1/predict` returns calibrated probabilities, feature attribution percentages, and counterfactual directives.

---

## 5. Municipal Logistics & CVRP Fleet Optimizer

During peak heat crises, water shortages and dehydration demand rapid municipal intervention. SMARTHEAT implements an operations-research emergency dispatcher:

### 5.1 Formulation
$$\max Z = \sum_{i \in \text{Wards}} \left[ \text{PriorityScore}(i) \times x_i \right]$$

$$\text{Subject to:} \quad \sum_{i} x_i \le K_{\text{fleet}}, \quad 0 \le x_i \le \text{Demand}(i)$$

$$\text{PriorityScore}(i) = \frac{\text{RiskScore}(i)^{1.6} \times \text{VulnerablePopulation}(i)}{\sqrt{1 + \text{DistanceToDepot}(i)}}$$

### 5.2 Algorithmic Implementation
- **Priority-Greedy Max-Heap ($O(N \log N)$)**: Prioritizes wards with the highest composite thermal risk, largest geriatric/slum populations, and closest depot proximity.
- **Capacitated Vehicle Routing (CVRP) with 2-Opt**: Solves tanker capacity constraints (e.g., 10,000L / 12,000L tankers) and optimizes route distances across drop-off clusters using 2-Opt local search heuristics.
- **Endpoint**: `POST /api/v1/optimize/dispatch`

---

## 6. Standards-Compliant Emergency Alerting (OASIS CAP v1.2)

SMARTHEAT implements the international **OASIS Common Alerting Protocol (CAP) v1.2** (ITU-T Recommendation X.1303):
- **Live XML Feed**: Available publicly at `GET /api/v1/alerts/cap.xml`.
- **National Telecom Cell Broadcast**: Compatible with government early warning systems (NDMA, SDMAs) and emergency SMS gateways.
- **Machine-Readable Structure**: Includes standardized XML tags: `<identifier>`, `<sender>`, `<sent>`, `<status>`, `<msgType>`, `<scope>`, `<urgency>`, `<severity>`, `<certainty>`, `<areaDesc>`, and `<circle>` coordinates.

---

## 7. System Architecture

```
                                  [ CLIENT ACCESS ]
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
   [ Bootstrap 5 Portal ]        [ Leaflet.js GIS ]          [ Chart.js Analytics ]
   - Admin/User Auth             - 24-City Pan-India Map     - Temp Trends
   - Emergency Simulator         - 33 Critical Facilities    - Risk Distributions
   - Logistics Dispatch UI       - Hazard Iso-Pins           - XAI Attributions
            │                             │                             │
            └─────────────────────────────┼─────────────────────────────┘
                                          │ (HTTP / JSON / XML)
                                          ▼
                      [ FLASK PRODUCTION WSGI GATEWAY (run.py) ]
       ┌──────────────────────────────────┴──────────────────────────────────┐
       │                                                                     │
       ▼                                                                     ▼
 [ REST API & Blueprint Routing ]                                [ Core Services Layer ]
 - /auth (Login, Gmail Register)                                 - risk_service.py (0-100 Score)
 - /dashboard (KPIs, Charts API)                                 - alert_service.py (CAP v1.2)
 - /weather (WMO Sync, CSV Upload)                               - recommendation_engine.py
 - /simulator (What-If Sliders)                                  - optimizer_routes.py (CVRP)
 - /api/v1/predict (ML + XAI)                                                │
 - /api/v1/optimize/dispatch (CVRP)                                          │
 - /api/v1/alerts/cap.xml (OASIS CAP)                                        │
 - /api/v1/health (SRE Probe)                                                │
 - /api/v1/metrics (Prometheus)                                              │
 - /api/docs (OpenAPI 3.0 Swagger)                                           │
       │                                                                     │
       └──────────────────────────────────┬──────────────────────────────────┘
                                          │
                      ┌───────────────────┴───────────────────┐
                      ▼                                       ▼
         [ INTELLIGENCE & ML ENGINE ]            [ RELATIONAL PERSISTENCE ]
         - ml/preprocessing.py (NOAA HI)         - SQLite / SQLAlchemy ORM
         - ml/predictor.py (92.4% RF)            - Models:
         - ml/xai.py (Tree Perturbation)           * users, locations, weather
         - saved_models/                           * predictions, alerts, risks
           * heatwave_rf_model.pkl                 * critical_facilities
           * scaler.pkl                            * recommendations
```

---

## 8. Transparent Heat Risk Formula (0–100)

SMARTHEAT computes an explainable multi-dimensional Disaster Risk Index:

$$\text{Total Heat Risk Score} = (0.45 \times \text{Hazard}) + (0.30 \times \text{Vulnerability}) + (0.15 \times \text{Exposure}) + (0.10 \times \text{Healthcare Deficit})$$

Where:
- **Hazard Score ($0–100$)**: Evaluates Heat Index severity combined with IMD temperature departure anomalies ($\Delta T \ge 4.5^\circ\text{C}$ adds heatwave penalty).
- **Vulnerability Score ($0–100$)**: Calculated from sensitive demographics:
  $$\text{Sensitive Ratio} = \frac{\text{Elderly (60+)} + \text{Infants (<5)} + \text{Outdoor Labor} + \text{Slum Residents}}{\text{Total Population}}$$
  Adjusted for canopy deficit ($\text{Canopy} < 25\%$).
- **Exposure Score ($0–100$)**: Urban density and spatial zone classification (Arid Urban, Coastal Urban, Plain Urban, Suburban, Rural).
- **Healthcare & Water Deficit ($0–100$)**: Deficit relative to WHO/national standards (hospital beds per 1,000 population and water distribution points per 10,000).

---

## 9. Interactive GIS Heat-Risk Mapping

Built with **Leaflet.js** and **OpenStreetMap**:
- **Pan-India View**: Real-time rendering across all 24 monitored cities and on-demand searched locations.
- **Color-Coded Circular Risk Markers**:
  - 🟢 **Low Risk** ($0–25$): Normal comfort.
  - 🟡 **Moderate Risk** ($26–50$): Precautionary monitoring.
  - 🟠 **High Risk** ($51–75$): Orange Alert, municipal cooling centers opened.
  - 🔴 **Extreme Risk** ($76–100$ with pulse animation): Red Alert, emergency tanker dispatches initiated.
- **Critical Facility Layers (33 Facilities)**:
  - ✚ **Hospitals / Specialized Heat Stroke Wards** (Red cross badge)
  - ❄ **Civic Air-Cooled Shelters** (Blue snowflake badge)
  - 💧 **Emergency Water Tanker Distribution Hubs** (Cyan drop badge)

---

## 10. Database Schema & ER Models

The relational storage layer is managed by **SQLAlchemy ORM**:
- `users`: User authentication, hashed passwords (`werkzeug.security`), role assignment (`admin` or `user`).
- `locations`: 24 Pan-India monitoring stations across 6 climatic zones with coordinates and baseline temperatures.
- `weather_data`: Daily meteorological records (Temp, Humidity, Wind, Rain, Pressure, Heat Index, Simulated flag).
- `vulnerability_data`: Ground demographic counts, hospital beds, water kiosks, tree canopy ratio, computed vulnerability score.
- `predictions`: Inference logs (predicted risk category, confidence probability, model name, timestamp).
- `risk_assessments`: Computed 0–100 multi-criteria risk score with JSON sub-component breakdown.
- `critical_facilities`: Geospatial hospital, cooling center, and water tanker coordinates for GIS mapping.
- `alerts`: Early warnings triggered on High/Extreme risk with Active/Resolved status and resolution timestamp.
- `response_recommendations`: Catalog of standard operating procedures across Health, Labor, Municipal, and Public sectors.

---

## 11. SRE Telemetry & Prometheus Observability

SMARTHEAT adopts Site Reliability Engineering (SRE) standards:
- **Liveness & Readiness Probe (`GET /api/v1/health`)**:
  - Validates active database connectivity.
  - Verifies deserialized machine learning model memory footprint and cache availability.
  - Reports uptime and RSS memory consumption.
- **Prometheus Metrics Endpoint (`GET /api/v1/metrics`)**:
  - Exposes RFC-compliant plain text metrics format for scrapers.
  - Tracks total request counters (`smartheat_http_requests_total`).
  - Measures request latency percentiles (`smartheat_latency_p50`, `smartheat_latency_p95`).
  - Emits active disaster alerts gauge (`smartheat_active_alerts`).

---

## 12. Step-by-Step Local Setup & Execution

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Anant56-cmd/Smartheat.git
cd Smartheat
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database & Seed Pan-India Data
```bash
python database/seed_data.py
```
*(Initializes `smartheat.db`, seeds the 24 Pan-India stations, 33 critical facilities, and primary administrator `Anant10`)*.

### 4. Run Automated Test Suite
```bash
python test_app.py
python test_enterprise_features.py
```
*(Runs 14 automated unit and integration tests — all tests pass with 0 errors)*.

### 5. Launch Application
```bash
python run.py
```
The server will boot locally at:
```text
http://127.0.0.1:5000
```

### Authentication Credentials
- **Primary Administrator:** `Anant10` &nbsp;|&nbsp; Password: `Anant@15`
- **Self-Registration:** Click **"Register New Account"** to create a user or admin account using any Gmail address.

---

## 13. Executive Project Pitch

> *"Extreme heatwaves are India's deadliest climate challenge, yet traditional systems treat a humid 42°C in coastal Odisha the same as a dry 42°C in Rajasthan, ignoring informal settlement density, outdoor labor exposure, and water shortages.*
>
> *I engineered **SMARTHEAT**, an end-to-end disaster intelligence and municipal logistics platform spanning 24 major Indian metropolises across all 6 climatic zones. SMARTHEAT does three things fundamentally differently:*
>
> *1. **Predicts with Explainable AI:** A 92.4% accurate Random Forest model analyzes 10 thermodynamic features. Using contrastive tree perturbation, it explains exactly which meteorological factor drove the risk and provides counterfactual remediation steps.*
> *2. **Optimizes Municipal Logistics:** Beyond risk prediction, it solves the Capacitated Vehicle Routing Problem (CVRP) with 2-Opt heuristics to automate the dispatch of municipal water tankers to hospitals, schools, and vulnerable slum clusters.*
> *3. **Broadcasts via National Standards:** It emits live OASIS CAP v1.2 XML feeds for telecom emergency cell broadcasts and features OpenAPI 3.0 Swagger docs and Prometheus telemetry.*
>
> *The entire system is deployed live on cloud infrastructure with automated CI/CD at [smartheat-yxyi.onrender.com](https://smartheat-yxyi.onrender.com)."*

---

## 14. Technical Interview & Defense Guide

### Q1: Why use a software-based architecture instead of IoT microcontrollers?
**Answer:** Physical IoT sensors (e.g. DHT11 on Arduino) have micro-spatial coverage (a single room or balcony), suffer from sensor drift at >45°C, require battery maintenance, and cannot scale across 24 metropolises. A software-based platform ingests standardized meteorological feeds from WMO stations and reanalysis archives, enabling machine learning pipelines, demographic vulnerability indices, and citywide fleet routing across entire states.

### Q2: Why Random Forest over Deep Neural Networks?
**Answer:** Random Forest excels on tabular thermodynamic data with non-linear feature interactions (temperature × humidity). It achieves 92.4% accuracy with zero GPU requirements, trains in under 2 seconds, runs inference in sub-milliseconds, and enables local tree perturbation for Explainable AI (XAI) feature attribution.

### Q3: How is the municipal logistics solver designed?
**Answer:** We formulate emergency resource allocation as a Capacitated Vehicle Routing Problem (CVRP) with multi-criteria priority scoring. Wards are prioritized in $O(N \log N)$ time using a Max-Heap weighted by thermal risk, vulnerable demographics, and depot distance. Fleet delivery routes are then optimized using 2-Opt local search heuristics to eliminate crossover paths and minimize fuel and turnaround time.

### Q4: What makes this platform standards-compliant for government adoption?
**Answer:** SMARTHEAT adheres to the OASIS Common Alerting Protocol (CAP) v1.2 (ITU-T X.1303), the exact format utilized by India's NDMA and national telecom networks for emergency cell broadcasts. It also exposes OpenAPI 3.0 Swagger documentation and Prometheus metrics for cloud-native SRE monitoring.

---

<div align="center">

**Developed by Anant Ashis Sahoo**  
Pan-India AI Disaster Intelligence & Municipal Logistics Platform  
*Licensed under the [MIT License](LICENSE).*

</div>
