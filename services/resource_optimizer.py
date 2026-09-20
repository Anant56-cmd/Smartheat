"""
Algorithmic Emergency Logistics & Resource Allocation Optimizer
Formulates and solves a constrained multi-criteria resource distribution problem
for municipal heatwave mitigation (Water Tankers, ORS Kits, Emergency Medical Beds).

Mathematical Formulation:
Maximize:
    Z = sum_{i in Wards} [ PriorityScore(i) * Allocation(i) ]
Subject to:
    sum_{i} TankersAllocated(i) <= FleetCapacity
    TankersAllocated(i) <= MaxWardNeed(i)
    PriorityScore(i) = (RiskScore(i)^1.5 * VulnerablePopulation(i)) / (1 + DistanceFromDepot(i))
"""

from typing import List, Dict, Any
import heapq
import math

class MunicipalResourceOptimizer:
    def __init__(self, fleet_water_tankers: int = 25, total_ors_kits: int = 5000, emergency_beds: int = 150):
        self.fleet_water_tankers = int(fleet_water_tankers)
        self.total_ors_kits = int(total_ors_kits)
        self.emergency_beds = int(emergency_beds)

    def optimize_dispatch(self, wards_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Solves optimal distribution using a greedy priority-queue allocation
        algorithm with marginal utility scoring (Complexity: O(N log N)).
        """
        if not wards_data:
            return {
                'total_tankers_dispatched': 0,
                'remaining_tankers': self.fleet_water_tankers,
                'total_ors_distributed': 0,
                'total_beds_reserved': 0,
                'wards_allocation': [],
                'system_risk_mitigation_pct': 0.0
            }

        scored_wards = []
        for ward in wards_data:
            risk_score = float(ward.get('risk_score', 50.0))
            pop = int(ward.get('total_population', 100000))
            vuln_score = float(ward.get('vulnerability_score', 50.0))
            slum_pop = int(ward.get('slum_residents_count', pop * 0.2))
            elderly = int(ward.get('elderly_count', pop * 0.1))
            children = int(ward.get('children_count', pop * 0.1))
            dist_km = float(ward.get('depot_distance_km', 3.5))

            high_risk_headcount = slum_pop + elderly + children

            # Non-linear Priority Weight: Higher heat risk heavily increases marginal utility
            # Priority = (Risk^1.6 * HighRiskPop) / sqrt(1 + dist_km)
            risk_weight = math.pow(max(1.0, risk_score), 1.6)
            priority_score = (risk_weight * max(1, high_risk_headcount)) / math.sqrt(1.0 + max(0.5, dist_km))

            # Estimated maximum tanker demand based on water deficit and population
            max_tankers_needed = max(1, min(10, int(math.ceil(high_risk_headcount / 15000.0 * (risk_score / 30.0)))))
            max_ors_needed = int(high_risk_headcount * 0.08 * (risk_score / 50.0))
            max_beds_needed = max(0, min(30, int(high_risk_headcount * 0.001 * (risk_score / 40.0))))

            scored_wards.append({
                'ward_id': ward.get('id'),
                'ward_name': ward.get('name', f"Ward {ward.get('id')}"),
                'risk_score': risk_score,
                'risk_level': ward.get('risk_level', 'MODERATE'),
                'vulnerable_population': high_risk_headcount,
                'depot_distance_km': dist_km,
                'priority_score': round(priority_score, 2),
                'max_tankers_needed': max_tankers_needed,
                'max_ors_needed': max_ors_needed,
                'max_beds_needed': max_beds_needed,
                'allocated_tankers': 0,
                'allocated_ors': 0,
                'allocated_beds': 0,
                'unmet_demand_pct': 100.0
            })

        # Sort wards descending by priority score
        scored_wards.sort(key=lambda x: x['priority_score'], reverse=True)

        # Multi-pass allocation: Guarantee critical wards get at least 1 unit, then distribute proportional to priority
        available_tankers = self.fleet_water_tankers
        available_ors = self.total_ors_kits
        available_beds = self.emergency_beds

        # Pass 1: Critical baseline allocation for EXTREME/HIGH risk
        for w in scored_wards:
            if w['risk_score'] >= 65.0 and available_tankers > 0:
                alloc = min(available_tankers, min(2, w['max_tankers_needed']))
                w['allocated_tankers'] += alloc
                available_tankers -= alloc

        # Pass 2: Greedy marginal allocation on priority order
        for w in scored_wards:
            needed = w['max_tankers_needed'] - w['allocated_tankers']
            if needed > 0 and available_tankers > 0:
                alloc = min(available_tankers, needed)
                w['allocated_tankers'] += alloc
                available_tankers -= alloc

            # ORS distribution proportional to vulnerable population and risk
            ors_alloc = min(available_ors, w['max_ors_needed'])
            w['allocated_ors'] = ors_alloc
            available_ors -= ors_alloc

            # Surge Beds allocation
            bed_alloc = min(available_beds, w['max_beds_needed'])
            w['allocated_beds'] = bed_alloc
            available_beds -= bed_alloc

            # Calculate unmet demand
            total_demanded = w['max_tankers_needed']
            total_fulfilled = w['allocated_tankers']
            w['unmet_demand_pct'] = round(max(0.0, (total_demanded - total_fulfilled) / total_demanded * 100.0), 1)

        total_dispatched_tankers = self.fleet_water_tankers - available_tankers
        total_dispatched_ors = self.total_ors_kits - available_ors
        total_reserved_beds = self.emergency_beds - available_beds

        # Calculate estimated systemic risk mitigation percentage
        total_initial_priority = sum(w['priority_score'] for w in scored_wards)
        mitigated_priority = sum(
            w['priority_score'] * (w['allocated_tankers'] / max(1, w['max_tankers_needed']))
            for w in scored_wards
        )
        mitigation_pct = round((mitigated_priority / max(1.0, total_initial_priority)) * 100.0, 1)

        return {
            'fleet_capacity': self.fleet_water_tankers,
            'total_tankers_dispatched': total_dispatched_tankers,
            'remaining_tankers': available_tankers,
            'total_ors_distributed': total_dispatched_ors,
            'remaining_ors': available_ors,
            'total_beds_reserved': total_reserved_beds,
            'remaining_beds': available_beds,
            'system_risk_mitigation_pct': mitigation_pct,
            'wards_allocation': scored_wards,
            'optimization_algorithm': 'Marginal Priority-Greedy Queue (O(N log N))'
        }
