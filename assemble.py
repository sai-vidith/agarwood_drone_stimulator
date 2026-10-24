"""Assemble the simulator: an offline single file (libraries inlined) and a CDN version for the web."""
import json, os
here = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get("LIBDIR", os.path.join(here, "lib"))
src = open(os.path.join(here, "simulator.src.html")).read()
data = open(os.path.join(here, "sim_data.json")).read().replace("</", "<\\/")
lcss = open(os.path.join(LIB, "leaflet.css")).read()
def build(inline):
    s = src.replace("/*__LEAFLET_CSS__*/", lcss).replace("__DATA__", data)
    if inline:
        s = s.replace("<script>/*__THREE__*/</script>", "<script>" + open(os.path.join(LIB, "three.min.js")).read() + "</script>")
        s = s.replace("<script>/*__LEAFLET_JS__*/</script>", "<script>" + open(os.path.join(LIB, "leaflet.js")).read() + "</script>")
    else:
        s = s.replace("<script>/*__THREE__*/</script>", '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>')
        s = s.replace("<script>/*__LEAFLET_JS__*/</script>", '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>')
    return s
head = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
open(os.path.join(here, "AgarSaaS_Drone_Simulator.html"), "w").write(head + build(True).replace("<div class=\"app\">", "</head><body><div class=\"app\">", 1) + "\n</body></html>\n")
open(os.path.join(here, "simulator_web.html"), "w").write(build(False))
print("built")
