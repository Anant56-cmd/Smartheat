from database.models import ResponseRecommendation

def get_recommendations_for_level(risk_level):
    """
    Retrieve rule-based disaster response actions for a specific risk level.
    """
    level = risk_level.upper() if risk_level else 'LOW'
    sops = ResponseRecommendation.query.filter_by(risk_level=level).order_by(ResponseRecommendation.priority.asc()).all()
    
    # If database not populated yet, provide fallback rules
    if not sops:
        return get_fallback_recommendations(level)
        
    return [sop.to_dict() for sop in sops]

def get_all_recommendations_grouped():
    """
    Retrieve all disaster response recommendations grouped by risk level.
    """
    all_sops = ResponseRecommendation.query.order_by(ResponseRecommendation.priority.asc()).all()
    grouped = {'LOW': [], 'MODERATE': [], 'HIGH': [], 'EXTREME': []}
    for sop in all_sops:
        if sop.risk_level in grouped:
            grouped[sop.risk_level].append(sop.to_dict())
    return grouped

def get_fallback_recommendations(level):
    """Fallback disaster response standard operating procedures."""
    fallbacks = {
        'LOW': [
            {'risk_level': 'LOW', 'priority': 'P3', 'target_sector': 'Public', 'title': 'Routine Hydration & Sun Awareness', 'description': 'Advise citizens to maintain regular hydration, carry umbrellas or hats during peak solar hours.'},
            {'risk_level': 'LOW', 'priority': 'P3', 'target_sector': 'Health', 'title': 'Routine Facility Monitoring', 'description': 'Ensure primary health centers maintain adequate inventory of oral rehydration salts (ORS) and IV fluids.'},
            {'risk_level': 'LOW', 'priority': 'P3', 'target_sector': 'Municipal', 'title': 'Public Fountain & Park Access', 'description': 'Ensure public water fountains and shaded urban parks remain accessible.'}
        ],
        'MODERATE': [
            {'risk_level': 'MODERATE', 'priority': 'P2', 'target_sector': 'Public', 'title': 'Issue Yellow Heat Advisory', 'description': 'Broadcast advisory warning vulnerable citizens (elderly, infants) to avoid direct sun exposure between 11 AM and 4 PM.'},
            {'risk_level': 'MODERATE', 'priority': 'P2', 'target_sector': 'Labor', 'title': 'Adjust Outdoor Labor Timings', 'description': 'Reschedule heavy outdoor construction to morning and late afternoon hours.'},
            {'risk_level': 'MODERATE', 'priority': 'P2', 'target_sector': 'Health', 'title': 'Heat-Cramp First-Aid Readiness', 'description': 'Staff emergency clinics with designated heat-exhaustion observation beds and distribute free ORS packets.'},
            {'risk_level': 'MODERATE', 'priority': 'P2', 'target_sector': 'Municipal', 'title': 'Deploy Municipal Water Kiosks', 'description': 'Ensure all public water distribution points in marketplaces and transit stations are operational.'}
        ],
        'HIGH': [
            {'risk_level': 'HIGH', 'priority': 'P1', 'target_sector': 'Public', 'title': 'Issue Orange Heat Warning', 'description': 'Issue multi-channel broadcast warnings. Postpone non-essential open-air public events.'},
            {'risk_level': 'HIGH', 'priority': 'P1', 'target_sector': 'Labor', 'title': 'Mandate Cease-Work During Peak Hours', 'description': 'Enforce mandatory suspension of direct-sun construction and heavy manual labor between 12:00 PM and 3:30 PM.'},
            {'risk_level': 'HIGH', 'priority': 'P1', 'target_sector': 'Health', 'title': 'Activate Hospital Heat Stroke Wards', 'description': 'Open specialized cooling wards equipped with ice packs, air conditioning, and emergency cooling baths.'},
            {'risk_level': 'HIGH', 'priority': 'P1', 'target_sector': 'Municipal', 'title': 'Dispatch Emergency Water Tankers', 'description': 'Direct municipal water tankers to high-density informal settlements and labor colonies experiencing water stress.'}
        ],
        'EXTREME': [
            {'risk_level': 'EXTREME', 'priority': 'P1', 'target_sector': 'Public', 'title': 'Declare Red Alert & Emergency Protocol', 'description': 'Activate State Disaster Management Authority emergency heat protocol. Advise citizens to stay indoors.'},
            {'risk_level': 'EXTREME', 'priority': 'P1', 'target_sector': 'Municipal', 'title': 'Activate All Civic Cooling Shelters 24/7', 'description': 'Open government community halls, transit hubs, and commercial centers as public air-conditioned relief shelters.'},
            {'risk_level': 'EXTREME', 'priority': 'P1', 'target_sector': 'Labor', 'title': 'Total Ban on Outdoor Physical Work', 'description': 'Enforce complete prohibition of outdoor manual labor, delivery services without AC, and heavy construction.'},
            {'risk_level': 'EXTREME', 'priority': 'P1', 'target_sector': 'Health', 'title': 'Mass Casualty Heat-Stroke Preparedness', 'description': 'Put ambulance networks on high alert with on-board cooling pads, rapid rehydration systems, and real-time bed tracking.'}
        ]
    }
    return fallbacks.get(level, fallbacks['LOW'])
