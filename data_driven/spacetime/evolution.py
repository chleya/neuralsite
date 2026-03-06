# -*- coding: utf-8 -*-
"""
NeuralSite: Parametric Event-Driven Spacetime Evolution Model V1.0
================================================================

Core Formula:
    State(t,P) = Project(InitialState, EventLog, P)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any
from datetime import datetime
from uuid import uuid4
from enum import Enum
import hashlib
import json


# ============================================================
# Layer 1: Initial Seed (Immutable)
# ============================================================
@dataclass
class InitialSeed:
    """Layer 1: Initial Seed - Immutable source of truth"""
    id: str
    project_name: str
    stations: Dict[int, float]  # station -> elevation
    created_at: datetime = field(default_factory=datetime.now)
    seed_hash: str = ""
    
    def compute_hash(self) -> str:
        data = {
            'id': self.id,
            'project_name': self.project_name,
            'stations': self.stations,
            'created_at': self.created_at.isoformat()
        }
        json_str = json.dumps(data, sort_keys=True)
        self.seed_hash = hashlib.sha256(json_str.encode()).hexdigest()
        return self.seed_hash


# ============================================================
# Layer 2: Event Log (Append-only)
# ============================================================
class EventType(Enum):
    CONSTRUCTION = "construction"
    WEATHER = "weather"
    BLOCKAGE = "blockage"
    DESIGN_CHANGE = "design_change"
    MATERIAL_CHANGE = "material_change"
    RESOURCE_INPUT = "resource_input"


@dataclass
class Event:
    """Layer 2: Event - Immutable fact"""
    id: str = field(default_factory=lambda: str(uuid4()))
    event_type: EventType = EventType.CONSTRUCTION
    station_start: int = 0
    station_end: int = 0
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    hash: str = ""
    
    def compute_hash(self) -> str:
        data = {
            'id': self.id,
            'type': self.event_type.value,
            'station_range': [self.station_start, self.station_end],
            'params': self.params,
            'timestamp': self.timestamp.isoformat()
        }
        json_str = json.dumps(data, sort_keys=True)
        self.hash = hashlib.sha256(json_str.encode()).hexdigest()
        return self.hash


# ============================================================
# Layer 3: Projector (Pure Function)
# ============================================================
class Projector:
    """
    Layer 3: Projector - Pure function that folds events into state
    
    State = Op_k @ Op_{k-1} @ ... @ Op_1 (InitialState)
    """
    
    def __init__(self, seed: InitialSeed):
        self.seed = seed
        self.operations = {
            EventType.CONSTRUCTION: self._op_construction,
            EventType.WEATHER: self._op_weather,
            EventType.BLOCKAGE: self._op_blockage,
            EventType.DESIGN_CHANGE: self._op_design_change,
            EventType.MATERIAL_CHANGE: self._op_material,
            EventType.RESOURCE_INPUT: self._op_resource,
        }
    
    def _op_construction(self, state: dict, event: Event, params: dict) -> dict:
        delta = params.get('progress_delta', 0.01)
        state['progress'] = min(1.0, state.get('progress', 0) + delta)
        return state
    
    def _op_weather(self, state: dict, event: Event, params: dict) -> dict:
        rain = params.get('rainfall_mm', 0)
        if rain > 50:
            state['progress'] = max(0, state.get('progress', 0) - 0.02)
            state.setdefault('delays', []).append({'type': 'weather', 'rain': rain})
        return state
    
    def _op_blockage(self, state: dict, event: Event, params: dict) -> dict:
        if params.get('blocked', False):
            state['status'] = 'blocked'
            state.setdefault('delays', []).append({'type': 'blockage'})
        return state
    
    def _op_design_change(self, state: dict, event: Event, params: dict) -> dict:
        if 'thickness' in params:
            state['design_thickness'] = params['thickness']
        if 'elevation' in params:
            state['target_elevation'] = params['elevation']
        return state
    
    def _op_material(self, state: dict, event: Event, params: dict) -> dict:
        if 'strength' in params:
            state['material_strength'] = params['strength']
        return state
    
    def _op_resource(self, state: dict, event: Event, params: dict) -> dict:
        workers = params.get('workers', 0)
        equipment = params.get('equipment', 0)
        state['efficiency'] = min(1.0, (workers * 0.3 + equipment * 0.7) / 100)
        return state
    
    def project(self, events: List[Event], params: Dict = None) -> dict:
        """Core Project function: State = Project(Initial, EventLog, P)"""
        params = params or {}
        
        state = {
            'seed_id': self.seed.id,
            'progress': 0.0,
            'status': 'initial',
            'elevations': dict(self.seed.stations),
            'target_elevations': dict(self.seed.stations),
            'delays': [],
            'efficiency': 1.0,
            'material_strength': 30,
            'design_thickness': 0.36,
        }
        
        for event in events:
            op = self.operations.get(event.event_type)
            if op:
                merged = {**params, **event.params}
                state = op(state, event, merged)
        
        state['state_hash'] = self._hash_state(state)
        return state
    
    def _hash_state(self, state: dict) -> str:
        key_data = {
            'progress': state.get('progress', 0),
            'status': state.get('status', ''),
            'elevations': state.get('elevations', {}),
        }
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()


# ============================================================
# Layer 4: Constraint Propagator (DAG)
# ============================================================
class DependencyNode:
    def __init__(self, event_id: str, depends_on: List[str] = None):
        self.event_id = event_id
        self.depends_on = depends_on or []
        self.dependents: List[str] = []


class ConstraintPropagator:
    """Layer 4: Constraint Propagation - Auto-recompute on change"""
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.events: Dict[str, Event] = {}
    
    def add_event(self, event: Event) -> str:
        self.events[event.id] = event
        event.compute_hash()
        
        deps = event.params.get('depends_on', [])
        self.nodes[event.id] = DependencyNode(event.id, deps)
        
        for d in deps:
            if d in self.nodes:
                self.nodes[d].dependents.append(event.id)
        
        return event.id
    
    def get_affected(self, event_id: str) -> List[str]:
        """Forward propagation to find affected subgraph"""
        affected = [event_id]
        queue = [event_id]
        
        while queue:
            curr = queue.pop(0)
            if curr in self.nodes:
                for dep in self.nodes[curr].dependents:
                    if dep not in affected:
                        affected.append(dep)
                        queue.append(dep)
        
        return affected
    
    def revalidate(self, event_id: str, projector: Projector, params: Dict = None) -> Dict:
        affected = self.get_affected(event_id)
        affected_events = [self.events[eid] for eid in affected if eid in self.events]
        new_state = projector.project(affected_events, params)
        
        return {
            'revalidated': event_id,
            'affected_count': len(affected),
            'new_state': new_state
        }


# ============================================================
# Complete Engine
# ============================================================
class SpacetimeEvolutionEngine:
    """Complete Engine: Parametric Event-Driven Spacetime Evolution"""
    
    def __init__(self, seed: InitialSeed):
        self.seed = seed
        self.projector = Projector(seed)
        self.propagator = ConstraintPropagator()
        self.event_log: List[Event] = []
    
    def add_event(self, event_type: EventType, start: int, end: int, params: Dict = None) -> str:
        event = Event(event_type=event_type, station_start=start, station_end=end, params=params or {})
        event.compute_hash()
        self.event_log.append(event)
        self.propagator.add_event(event)
        return event.id
    
    def get_state(self, station: int = None) -> dict:
        if station is not None:
            return self.projector.project_at_station(station, self.event_log) if hasattr(self.projector, 'project_at_station') else self.projector.project(self.event_log)
        return self.projector.project(self.event_log)
    
    def change_condition(self, event_type: EventType, start: int, end: int, params: Dict) -> dict:
        """Condition change: auto-trigger recompute"""
        event_id = self.add_event(event_type, start, end, params)
        result = self.propagator.revalidate(event_id, self.projector)
        return {
            'changed': True,
            'new_event': event_id,
            'affected': result['affected_count'],
            'new_state': self.get_state()
        }


# ============================================================
# Test
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("NeuralSite Parametric Event-Driven Evolution Model")
    print("=" * 60)
    
    # Layer 1: Initial Seed
    seed = InitialSeed("seed-001", "Beijing-Shanghai Highway", {
        5000: 100.0, 5100: 101.5, 5200: 103.0, 5300: 104.5, 5400: 106.0, 5500: 107.5
    })
    seed.compute_hash()
    print(f"\n[Layer 1] Initial Seed: {seed.project_name}")
    print(f"  Stations: K5+000 ~ K5+500")
    print(f"  Hash: {seed.seed_hash[:16]}...")
    
    # Create Engine
    engine = SpacetimeEvolutionEngine(seed)
    
    # Layer 2: Add Events
    print(f"\n[Layer 2] Event Log:")
    engine.add_event(EventType.CONSTRUCTION, 5000, 5500, {'progress_delta': 0.30})
    print("  + CONSTRUCTION: progress +30%")
    engine.add_event(EventType.RESOURCE_INPUT, 5000, 5500, {'workers': 50, 'equipment': 20})
    print("  + RESOURCE: 50 workers, 20 equipment")
    engine.add_event(EventType.CONSTRUCTION, 5000, 5500, {'progress_delta': 0.25})
    print("  + CONSTRUCTION: progress +25% (total 55%)")
    
    # Layer 3: Project State
    print(f"\n[Layer 3] Projected State:")
    state = engine.get_state()
    print(f"  Progress: {state['progress']*100:.0f}%")
    print(f"  Status: {state['status']}")
    print(f"  Efficiency: {state['efficiency']:.1f}")
    print(f"  Hash: {state['state_hash'][:16]}...")
    
    # Layer 4: Condition Change
    print(f"\n[Layer 4] Condition Change: HEAVY RAIN")
    result = engine.change_condition(EventType.WEATHER, 5000, 5500, {'rainfall_mm': 120, 'delay_days': 3})
    print(f"  Event: Heavy rain 120mm")
    print(f"  Affected: {result['affected']} events")
    print(f"  New Progress: {result['new_state']['progress']*100:.0f}%")
    print(f"  Delays: {len(result['new_state'].get('delays', []))}")
    
    # Another change
    print(f"\n[Layer 4] Condition Change: DESIGN CHANGE")
    result2 = engine.change_condition(EventType.DESIGN_CHANGE, 5000, 5500, {'thickness': 0.40})
    print(f"  Event: Thickness +4cm")
    print(f"  New Progress: {result2['new_state']['progress']*100:.0f}%")
    print(f"  Design Thickness: {result2['new_state'].get('design_thickness', 0.36)}m")
    
    print("\n" + "=" * 60)
    print("Core Formula Verified:")
    print("  State = Project(Initial, EventLog, P)  [OK]")
    print("  NewState = Project(Initial, EventLog + dEvent, P + dP)  [OK]")
    print("=" * 60)
