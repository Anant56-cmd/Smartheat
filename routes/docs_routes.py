"""
OpenAPI 3.0 & Swagger UI Developer Documentation Blueprint
Provides interactive, browser-executable API documentation for SMARTHEAT.
"""

from flask import Blueprint, render_template, jsonify

docs_bp = Blueprint('docs', __name__, url_prefix='/api')

OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "SMARTHEAT National Disaster Intelligence REST API",
        "description": "Production RESTful API specification for real-time heatwave inference with Explainable AI (XAI), OASIS CAP v1.2 emergency cell broadcast feeds, algorithmic resource optimization, and SRE telemetry.",
        "version": "2.2.0",
        "contact": {
            "name": "SMARTHEAT Engineering Team",
            "email": "engineering@smartheat.gov.in"
        }
    },
    "servers": [
        {"url": "/", "description": "Active Application Server"}
    ],
    "paths": {
        "/api/v1/health": {
            "get": {
                "summary": "SRE Liveness & Readiness Health Probe",
                "description": "Returns operational status of database connection, ML model caching, and memory footprint.",
                "responses": {
                    "200": {"description": "System Healthy & Ready"},
                    "503": {"description": "System Degraded"}
                }
            }
        },
        "/api/v1/metrics": {
            "get": {
                "summary": "Prometheus Telemetry Metrics Exposition",
                "description": "Emits RFC-compliant plain text metrics for Prometheus scrapers (p50/p95 latency, requests count, active alerts).",
                "responses": {
                    "200": {"description": "Prometheus Metrics Text Output"}
                }
            }
        },
        "/api/v1/alerts/cap.xml": {
            "get": {
                "summary": "OASIS CAP v1.2 International Emergency Alert Feed",
                "description": "Returns validated ITU-T X.1303 / OASIS CAP v1.2 XML emergency cell broadcast feed used by NDMA and national telecoms.",
                "responses": {
                    "200": {"description": "OASIS CAP v1.2 XML Payload"}
                }
            }
        },
        "/api/v1/predict": {
            "post": {
                "summary": "AI Heat Wave Inference with Local Feature Attribution (XAI)",
                "description": "Performs multi-class heatwave classification with Random Forest, returning risk tier, confidence, and tree feature contributions.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "example": {
                                "temperature": 42.5,
                                "humidity": 55.0,
                                "wind_speed": 10.0,
                                "rainfall": 0.0,
                                "pressure": 1012.0
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Inference and XAI Feature Attribution Result"}
                }
            }
        },
        "/api/v1/optimize/dispatch": {
            "post": {
                "summary": "Priority-Greedy Resource Allocation Optimizer",
                "description": "Calculates optimal municipal water tanker and hospital surge bed distribution across 24 national hubs in O(N log N) time.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "example": {
                                "fleet_water_tankers": 30,
                                "total_ors_kits": 5000,
                                "emergency_beds": 120
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Optimized Municipal Dispatch Schedule"}
                }
            }
        },
        "/api/v1/simulate/climate": {
            "post": {
                "summary": "IPCC Climate Crisis & Blackout Stress-Testing Solver",
                "description": "Simulates multi-variable temperature anomalies (+1C to +4C) combined with power grid blackout and water pipeline ruptures.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "example": {
                                "temp_anomaly": 2.5,
                                "grid_blackout": True,
                                "water_pipeline_rupture": False
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "National Crisis Stress-Testing Results"}
                }
            }
        }
    }
}

@docs_bp.route('/docs')
def swagger_ui():
    """Renders interactive Swagger UI developer portal."""
    return render_template('docs.html')

@docs_bp.route('/v1/openapi.json')
def openapi_json():
    """Serves OpenAPI 3.0 specification JSON."""
    return jsonify(OPENAPI_SPEC)
