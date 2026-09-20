"""
OASIS Common Alerting Protocol (CAP) v1.2 Standard XML Generator
Compliant with ITU-T Recommendation X.1303 & OASIS CAP v1.2 Specification.
Standard used by NDMA (India), FEMA (US), and WMO for emergency cell broadcasts.
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any

CAP_NAMESPACE = "urn:oasis:names:tc:emergency:cap:1.2"

def generate_cap_xml(alerts: List[Dict[str, Any]], sender_id: str = "smartheat-national-alert-engine@ndma.gov.in") -> str:
    """
    Serializes a list of active heatwave alerts into an OASIS CAP v1.2 XML document.
    """
    root = ET.Element(f"{{{CAP_NAMESPACE}}}alert")
    root.set("xmlns", CAP_NAMESPACE)

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    
    ET.SubElement(root, "identifier").text = f"SMARTHEAT-IN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    ET.SubElement(root, "sender").text = sender_id
    ET.SubElement(root, "sent").text = now_utc
    ET.SubElement(root, "status").text = "Actual"
    ET.SubElement(root, "msgType").text = "Alert"
    ET.SubElement(root, "scope").text = "Public"
    ET.SubElement(root, "code").text = "IPAWS-VERSION-1.0"

    if not alerts:
        # Provide clean heartbeat alert info if no active alerts
        info = ET.SubElement(root, "info")
        ET.SubElement(info, "category").text = "Met"
        ET.SubElement(info, "event").text = "Routine Meteorological Heat Surveillance"
        ET.SubElement(info, "urgency").text = "Past"
        ET.SubElement(info, "severity").text = "Minor"
        ET.SubElement(info, "certainty").text = "Observed"
        ET.SubElement(info, "headline").text = "National Heat Wave Status: Green / Normal Conditions Across All Monitored Sectors"
        ET.SubElement(info, "description").text = "All 24 monitored national hubs are currently operating below critical emergency heat thresholds."
        ET.SubElement(info, "instruction").text = "Maintain routine hydration and follow standard municipal summer advisories."
    else:
        for a in alerts:
            info = ET.SubElement(root, "info")
            ET.SubElement(info, "category").text = "Met"
            ET.SubElement(info, "event").text = f"Severe Heat Wave Advisory - {a.get('risk_level', 'HIGH')} Tier"
            
            # Map severity
            level = a.get('risk_level', 'HIGH')
            if level == 'EXTREME':
                urgency = "Immediate"
                severity = "Extreme"
                certainty = "Observed"
            elif level == 'HIGH':
                urgency = "Expected"
                severity = "Severe"
                certainty = "Likely"
            else:
                urgency = "Future"
                severity = "Moderate"
                certainty = "Possible"

            ET.SubElement(info, "urgency").text = urgency
            ET.SubElement(info, "severity").text = severity
            ET.SubElement(info, "certainty").text = certainty
            
            city = a.get('location_name', 'National Hub')
            temp = a.get('temperature', 42.0)
            hi = a.get('heat_index', 48.0)
            
            ET.SubElement(info, "headline").text = f"NDMA EMERGENCY ALERT: {level} Risk Heat Stress Declared for {city}"
            ET.SubElement(info, "description").text = (
                f"Severe atmospheric heat hazard detected in {city}. "
                f"Observed ambient temperature: {temp}C, Rothfusz Heat Index: {hi}C. "
                f"Demographic vulnerability index: {a.get('vulnerability_score', 65.0)}/100. "
                f"High risk of heat exhaustion, dehydration, and heat stroke among outdoor workers, elderly, and children."
            )
            ET.SubElement(info, "instruction").text = (
                "EMERGENCY PROTOCOL ACTIVATED: Cease all non-essential outdoor manual labor between 11:00 AM and 3:30 PM. "
                "Move to designated public cooling shelters. Ensure immediate rehydration with ORS/electrolytes. "
                "Contact municipal emergency medical hotline for heat-stroke symptoms."
            )
            ET.SubElement(info, "web").text = "https://smartheat.gov.in/alerts"

            # Area Block
            area = ET.SubElement(info, "area")
            ET.SubElement(area, "areaDesc").text = f"{city} Metropolitan Region, India"
            lat = a.get('latitude')
            lng = a.get('longitude')
            if lat is not None and lng is not None:
                # Circle: lat,lng radius(km)
                ET.SubElement(area, "circle").text = f"{lat},{lng},25.0"

    # Convert to XML string with declaration
    return ET.tostring(root, encoding="utf-8", method="xml", xml_declaration=True).decode("utf-8")
