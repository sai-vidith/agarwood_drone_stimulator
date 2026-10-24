"""Build sim_data.json (also merges terrain_layers.csv) for the AgarSaaS drone simulator.

Inputs : nagaland_agarwood_10000_sample_dataset.xlsx  (the project's 10,000 tree records, used as-is)
         public_layers.csv  (made by sample_public_layers.py: Meta/WRI 1 m canopy height,
                             ESA WorldCover 2021, Hansen GFC tree cover 2000, sampled at each tree)
         Admin2.* (datameet India state boundaries, for state lookup and the map outline)
Output : sim_data.json  (columnar), plus a check that every given value is carried over unchanged.
"""
import json, hashlib, sys, pandas as pd, numpy as np, shapefile
from shapely.geometry import shape, Point, mapping
from shapely.prepared import prep

XLSX = sys.argv[1] if len(sys.argv) > 1 else "nagaland_agarwood_10000_sample_dataset.xlsx"
src = pd.read_excel(XLSX)
pub = pd.read_csv("public_layers.csv")
ter = pd.read_csv("terrain_layers.csv")  # sample_terrain.py: Copernicus GLO-30 DEM
assert (ter.Tree_ID.values == src.Tree_ID.values).all()
pub = pub.merge(ter, on="Tree_ID", how="left")
assert len(src) == 10000 and (src.Tree_ID.values == pub.Tree_ID.values).all()

GIVEN = list(src.columns)
GRADES = sorted(src.Assigned_Agarwood_Grade.unique())

# State lookup (the dataset is labelled Nagaland, but its coordinates span a box over Nagaland, Assam and Myanmar)
# Admin2.shp/.shx/.dbf from https://github.com/datameet/maps/tree/master/States
r = shapefile.Reader("Admin2")
NE = ["Nagaland", "Assam", "Manipur", "Arunachal Pradesh", "Meghalaya"]
states = {sr.record[0]: shape(sr.shape.__geo_interface__) for sr in r.iterShapeRecords() if sr.record[0] in NE}
prepd = {k: prep(v) for k, v in states.items()}
STATE_NAMES = NE + ["Outside India (Myanmar)"]
state_idx = []
for la, lo in zip(src.Latitude, src.Longitude):
    p = Point(lo, la)
    state_idx.append(next((STATE_NAMES.index(k) for k in prepd if prepd[k].contains(p)), len(NE)))

outline = {k: mapping(v.simplify(0.004, preserve_topology=True)) for k, v in states.items()}
def rnd(o):
    if isinstance(o, float): return round(o, 4)
    if isinstance(o, (list, tuple)): return [rnd(x) for x in o]
    if isinstance(o, dict): return {k: rnd(v) for k, v in o.items()}
    return o

cols = {}
for c in GIVEN:
    v = src[c]
    cols[c] = [GRADES.index(g) for g in v] if c == "Assigned_Agarwood_Grade" else v.tolist()
for c in pub.columns[1:]:
    cols[c] = pub[c].tolist()
cols["state"] = state_idx

# Check: every given value round-trips exactly
back = pd.DataFrame({c: ([GRADES[i] for i in cols[c]] if c == "Assigned_Agarwood_Grade" else cols[c]) for c in GIVEN})
pd.testing.assert_frame_equal(back, src, check_exact=True)
digest = hashlib.sha256(src.to_csv(index=False).encode()).hexdigest()

out = {
    "given_columns": GIVEN, "grades": GRADES, "states": STATE_NAMES,
    "worldcover": {10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland", 50: "Built-up",
                   60: "Bare / sparse", 80: "Water", 90: "Herbaceous wetland", 95: "Mangroves", 100: "Moss & lichen"},
    "check": {"records": len(src), "values_unchanged": True, "sha256_of_given_values": digest},
    "outline": rnd(outline), "cols": cols,
}
json.dump(out, open("sim_data.json", "w"), separators=(",", ":"))
print("records", len(src), "| all given values unchanged | sha256", digest[:16])
print(pd.Series([STATE_NAMES[i] for i in state_idx]).value_counts().to_string())
