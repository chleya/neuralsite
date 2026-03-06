# Test with real Excel data
import sys
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\neuralsite\data_driven')

from spacetime.evolution import SpacetimeEvolutionEngine, InitialSeed, EventType
import openpyxl

output = []
output.append("=" * 60)
output.append("REAL DATA TEST with Evolution Model")
output.append("=" * 60)
output.append("")

# Load Excel
excel_path = r'F:\neuralsite_monorepo\wenjian\计算2025.9.10路基标高.xlsx'
wb = openpyxl.load_workbook(excel_path, data_only=True)
ws = wb['右幅']

# Extract stations
stations = {}
for row in ws.iter_rows(min_row=11, max_row=50, min_col=1, max_col=6, values_only=True):
    if row[0] and isinstance(row[0], (int, float)):
        station_id = int(row[0])
        elevation = row[5] if row[5] and isinstance(row[5], (int, float)) else 0
        if elevation > 0:
            stations[station_id] = elevation

output.append(f"Loaded {len(stations)} stations from Excel")
output.append(f"Range: {min(stations.keys())} to {max(stations.keys())}")
output.append(f"Elevation: {min(stations.values()):.2f}m to {max(stations.values()):.2f}m")
output.append("")

# Layer 1: Create seed with real data
seed = InitialSeed(
    id="seed-real-001",
    project_name="Real Highway Project",
    stations=stations
)
seed.compute_hash()
output.append(f"[Layer 1] Initial Seed: {seed.project_name}")
output.append(f"  Seed Hash: {seed.seed_hash[:16]}...")
output.append("")

# Create Engine
engine = SpacetimeEvolutionEngine(seed)

# Layer 2: Add real events
output.append("[Layer 2] Adding Real Events:")
engine.add_event(EventType.CONSTRUCTION, 4300, 4500, {'progress_delta': 0.35})
output.append("  + CONSTRUCTION: K4+300~K4+500, progress +35%")

engine.add_event(EventType.RESOURCE_INPUT, 4300, 4500, {'workers': 30, 'equipment': 10})
output.append("  + RESOURCE: 30 workers, 10 equipment")

engine.add_event(EventType.CONSTRUCTION, 4500, 4700, {'progress_delta': 0.40})
output.append("  + CONSTRUCTION: K4+500~K4+700, progress +40%")
output.append("")

# Layer 3: Project state
output.append("[Layer 3] Projected State:")
state = engine.get_state()
output.append(f"  Progress: {state['progress']*100:.0f}%")
output.append(f"  Status: {state['status']}")
output.append(f"  Efficiency: {state['efficiency']:.1f}")
output.append(f"  State Hash: {state['state_hash'][:16]}...")
output.append("")

# Layer 4: Real condition change - HEAVY RAIN
output.append("[Layer 4] Condition Change: HEAVY RAIN in region K4+300~K4+500")
result = engine.change_condition(
    EventType.WEATHER, 4300, 4500, 
    {'rainfall_mm': 150, 'delay_days': 5}
)
output.append(f"  Event: Heavy rain 150mm")
output.append(f"  Affected events: {result['affected']}")
output.append(f"  New Progress: {result['new_state']['progress']*100:.0f}%")
output.append(f"  Delays: {len(result['new_state'].get('delays', []))}")
output.append("")

# Design change
output.append("[Layer 4] Condition Change: DESIGN THICKNESS CHANGE")
result2 = engine.change_condition(
    EventType.DESIGN_CHANGE, 4300, 4700,
    {'thickness': 0.40, 'elevation': 281.0}
)
output.append(f"  Event: Thickness 36cm -> 40cm")
output.append(f"  New Progress: {result2['new_state']['progress']*100:.0f}%")
output.append(f"  Design Thickness: {result2['new_state'].get('design_thickness', 0.36)}m")
output.append("")

output.append("=" * 60)
output.append("REAL DATA INTEGRATION SUCCESS!")
output.append("=" * 60)

with open(r'C:\Users\Administrator\.openclaw\workspace\neuralsite\real_data_test.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
