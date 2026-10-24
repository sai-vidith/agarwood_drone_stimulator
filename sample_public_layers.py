"""Sample public forest layers at each tree's coordinate (values only added, never changed)."""
import rasterio, json, sys, time, threading, pandas as pd, numpy as np
from rasterio.windows import Window
from pyproj import Transformer
from shapely.geometry import shape, Point
from concurrent.futures import ThreadPoolExecutor

META = "https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/alsgedi_global_v6_float/chm/{}.tif"
WC = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N{:02d}E{:03d}_Map.tif"
HANSEN = "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/Hansen_GFC-2023-v1.11_treecover2000_30N_090E.tif"

d = pd.read_excel("nagaland_agarwood_10000_sample_dataset.xlsx")
import os, urllib.request
if not os.path.exists("meta_tiles.geojson"):
    urllib.request.urlretrieve("https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/alsgedi_global_v6_float/tiles.geojson", "meta_tiles.geojson")
tiles = [(x["properties"]["tile"], shape(x["geometry"])) for x in json.load(open("meta_tiles.geojson"))["features"]]
tiles = [t for t in tiles if t[1].intersects(shape({"type": "Polygon", "coordinates": [[[93, 25], [96, 25], [96, 27.5], [93, 27.5], [93, 25]]]}))]
local = threading.local()

def ds(url):
    if not hasattr(local, "h"):
        local.h = {}
        local.tr = Transformer.from_crs(4326, 3857, always_xy=True)
    if url not in local.h:
        local.h[url] = rasterio.open("/vsicurl/" + url)
    return local.h[url]

def sample(i):
    r = d.iloc[i]
    lon, lat = float(r.Longitude), float(r.Latitude)
    out = {"Tree_ID": r.Tree_ID}
    for attempt in range(3):
        try:
            tile = next(k for k, s in tiles if s.contains(Point(lon, lat)))
            s = ds(META.format(tile)); x, y = local.tr.transform(lon, lat); row, col = s.index(x, y)
            a = s.read(1, window=Window(col - 60, row, 121, 1))[0].astype(float)  # 1 m pixels, ±60 m transect
            out.update(pub_chm_center_m=a[60], pub_chm_mean_m=round(a.mean(), 2),
                       pub_chm_p95_m=float(np.percentile(a, 95)), pub_canopy_cover=round((a >= 5).mean(), 3))
            s = ds(WC.format(int(lat // 3) * 3, int(lon // 3) * 3)); row, col = s.index(lon, lat)
            w = s.read(1, window=Window(col - 5, row - 5, 11, 11))
            vals, cnt = np.unique(w, return_counts=True)
            out.update(pub_worldcover_center=int(w[5, 5]), pub_worldcover_mode=int(vals[cnt.argmax()]),
                       pub_worldcover_tree_frac=round((w == 10).mean(), 3))
            s = ds(HANSEN); row, col = s.index(lon, lat)
            h = s.read(1, window=Window(col - 3, row, 7, 1))[0]
            out.update(pub_hansen_treecover2000=int(h[3]), pub_hansen_mean=round(float(h.mean()), 1))
            return out
        except Exception as e:
            err = str(e); time.sleep(2)
    out["error"] = err
    return out

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else len(d)
    t = time.time(); res = []
    with ThreadPoolExecutor(24) as ex:
        for k, o in enumerate(ex.map(sample, range(n))):
            res.append(o)
            if k % 500 == 0: print(k, round(time.time() - t), flush=True)
    pd.DataFrame(res).to_csv("public_layers.csv", index=False)
    print("done", round(time.time() - t))
