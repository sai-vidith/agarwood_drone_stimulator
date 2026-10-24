# AgarSaaS UAV Mission Simulator

A browser-based drone simulator for the AgarSaaS project. It flies a survey drone over any of the 10,000 trees in `nagaland_agarwood_10000_sample_dataset.xlsx`, at the tree's own latitude and longitude, over real terrain, inside a forest made from public data.

**Everything the drone "sees" is simulated.** No drone has flown over agarwood for this project. Say so in the report and the slides (suggested wording below).

## Run it

Double-click `AgarSaaS_Drone_Simulator.html`. It opens in Chrome or Edge and works offline, because the 3D and map libraries are bundled inside the file. The satellite basemap on the mission map is the only part that needs internet.

On the RTX 4060 laptop, make the browser use the NVIDIA GPU: Windows Settings → System → Display → Graphics → add Chrome (or Edge) → Options → High performance. Then keep **Graphics: High** in the simulator (soft shadows, denser forest, 2× resolution). Use **Low** on a laptop without a dedicated GPU.

## What is real and what is simulated

| Part | Source | Status |
|---|---|---|
| 10,000 tree records (location, height, DBH, crown, NDVI, NDRE, resin, grade…) | Project dataset (xlsx) | Used unchanged; `build_sim_data.py` checks every value |
| Terrain around each tree (±210 m) | Copernicus GLO-30 DEM | Real public data (a surface model, so in dense forest it partly follows the canopy) |
| Surrounding forest height and density | Meta/WRI 1 m canopy height, ESA WorldCover 2021, Hansen tree cover 2000 | Real public data, sampled at each tree |
| State each tree falls in | datameet India boundaries | Real public data |
| Neighbouring agarwood trees (3 m grid) | Sizes drawn from same-age rows of the dataset | Simulated positions |
| Native trees around the plot | Generated from the public canopy height and cover | Simulated |
| Weather, wind, rain, fog, lightning | Seasonal presets for NE India | Simulated |
| Flight physics, battery, LiDAR, NDVI sensor, camera images | Physics model below | Simulated |
| Life-cycle stages (year 1 to 10) | Chapman–Richards growth curve | Projection, marked on screen |

## What the simulator does

- **Mission map** of all 10,000 trees, coloured by grade, state, land cover, canopy cover or elevation. Click any tree to fly there.
- **Survey mission**: lawn-mower pattern from the flight plan (altitude ≤ 120 m AGL for DGCA, speed, overlap), with photo footprints, ground sample distance and coverage.
- **Close inspection**: after the survey the drone orbits the target tree with the camera locked on it. Every quarter second it checks line of sight. When a neighbouring crown blocks the view, it logs which tree is in the way and moves along the orbit or climbs until it can see the target again. The green or red line in the 3D view shows the line of sight.
- **Obstacle avoidance**: the drone looks ahead along its path and climbs to keep 6 m clearance above the canopy (2.5 m during inspection).
- **Views**: FPV (first person, from the gimbal), TPP (third-person chase), Orbit (drag and scroll) and Top. The inset shows the drone's camera feed in RGB or NDVI false colour.
- **Conditions**: season, weather, time of day, wind speed and direction, drone class. A GO / CAUTION / NO-GO verdict explains why. You can still launch on NO-GO to show what goes wrong.
- **Life cycle**: year 1 seedlings, year 3, year 5 (ready for inoculation), year 7 (inoculated trees show stress yellowing and lower NDVI), year 10 (harvest, about a third felled).
- **Moving field**: crowns sway with the wind and gusts, rain falls with the wind, fog closes in, and in storms there is lightning.
- **Route tour**: a multi-tree route to the nearest trees, showing distance, climb, batteries needed and how many legs go beyond visual line of sight.
- **Exports**: flight log, photo list and scene trees as CSV.

### Physics model (per 20 ms step)

- Wind uses a power-law profile, (height / 10 m)^0.2, plus gusts set by the weather (strongest in thunderstorms).
- Air density comes from the DEM elevation and the season's temperature.
- Drag is ½ ρ C_d A |v − w| (v − w), using air speed, not ground speed. Rain adds a little mass and drag.
- A velocity controller tilts the drone, up to its tilt limit, to follow the path and cancel drag. In strong wind it runs out of tilt and drifts, and if it cannot make headway it returns home.
- Power is P_hover · √(1.225 / ρ) · (thrust / weight)^1.5. Cold weather reduces usable battery.
- Safety triggers return home on low battery, lightning, moisture in a drone with no IP rating, or wind it cannot beat.
- The two drone classes are a 0.95 kg multispectral quad (no IP rating) and a 6.5 kg IP55 enterprise quad. Their figures are approximate for the class, not measurements of a specific product.

## Rebuilding the data

```
python sample_public_layers.py      # canopy height, land cover, tree cover at each tree  -> public_layers.csv
python sample_terrain.py            # Copernicus DEM patch around each tree               -> terrain_layers.csv
python build_sim_data.py            # merges with the xlsx, checks values unchanged       -> sim_data.json
python assemble.py                  # builds AgarSaaS_Drone_Simulator.html (offline) and simulator_web.html
```

Requirements: `pandas openpyxl rasterio shapely pyproj pyshp`. The first two scripts read the public rasters over the internet. `assemble.py` expects `lib/three.min.js` (three.js r128), `lib/leaflet.js` and `lib/leaflet.css` (Leaflet 1.9.4).

## Findings about the dataset

The simulator shows two things about the sample dataset that the report should mention:

1. Only 4,795 of the 10,000 "Nagaland" trees fall inside Nagaland. 4,937 are in Assam, 258 in Myanmar, 7 in Arunachal Pradesh and 3 in Manipur. The coordinates are spread evenly over a rectangle (25.65–26.95° N, 93.20–95.15° E), which is what a synthetic sample looks like.
2. Each tree's nearest neighbour is about 0.8 km away on average, so the trees are not grouped into plantations. That is why each scene puts the given tree in a simulated plot of its recorded plot size, and why the route tour needs several batteries and flights beyond visual line of sight.

## Suggested report wording

> We built a UAV mission simulator to test flight planning, sensing and data handling before any field deployment. The simulator places each of the 10,000 sample tree records at its recorded coordinates, without changing any value. Terrain, surrounding canopy height and land cover come from public datasets (Copernicus GLO-30, Meta/WRI 1 m canopy height, ESA WorldCover 2021, Hansen Global Forest Change). Neighbouring trees, weather, flight dynamics and all imagery, LiDAR and multispectral readings are simulated. The results show how the pipeline would behave; they are not field observations of agarwood.
