"""Sample Copernicus GLO-30 DEM around each tree: centre elevation + a 15x15 patch (30 m spacing, ±210 m).
Patch stored as int8 metres relative to the centre (clipped to ±127), base64 per tree."""
import rasterio, threading, time, base64, numpy as np, pandas as pd
from rasterio.windows import Window
from concurrent.futures import ThreadPoolExecutor
U = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N{la:02d}_00_E{lo:03d}_00_DEM/Copernicus_DSM_COG_10_N{la:02d}_00_E{lo:03d}_00_DEM.tif"
d = pd.read_excel("nagaland_agarwood_10000_sample_dataset.xlsx")
loc = threading.local()
def ds(u):
    if not hasattr(loc, "h"): loc.h = {}
    if u not in loc.h: loc.h[u] = rasterio.open("/vsicurl/" + u)
    return loc.h[u]
def one(i):
    la, lo = float(d.Latitude[i]), float(d.Longitude[i])
    s = ds(U.format(la=int(la), lo=int(lo)))
    row, col = s.index(lo, la)
    # pixel is 1 arcsec (~31 m N-S, ~28 m E-W here); sample every pixel in a 15x15 window, boundless at tile edges
    w = s.read(1, window=Window(col - 7, row - 7, 15, 15), boundless=True, fill_value=np.nan).astype(float)
    c = float(w[7, 7]) if not np.isnan(w[7, 7]) else (float(np.nanmean(w)) if np.isfinite(w).any() else 0.0)
    w = np.where(np.isnan(w), c, w)
    rel = np.clip(np.round(w - c), -127, 127).astype(np.int8)
    return round(c, 1), base64.b64encode(rel.tobytes()).decode()
t = time.time()
with ThreadPoolExecutor(24) as ex: res = list(ex.map(one, range(len(d))))
pd.DataFrame({"Tree_ID": d.Tree_ID, "pub_elev_m": [r[0] for r in res], "pub_dem_patch": [r[1] for r in res]}).to_csv("terrain_layers.csv", index=False)
print("done", round(time.time() - t), "s")
