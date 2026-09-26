#!/usr/bin/env python3
"""Merge all data/brands/*.geojson into compact per-brand JSON files.

Filters out closed/vacant/disused/demolished entries.
Trims to fields needed by the map tool.
Emits data/compact/<brand>.json + data/compact/index.json.
"""
import json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "brands"
DST = ROOT / "data" / "compact"
DST.mkdir(parents=True, exist_ok=True)

# brand slug -> display metadata (breakfast policy)
BRAND_META = {
 "McDonalds":       {"name":"McDonald's",       "start":"05:00","end":"10:30","wend":"11:00","allDay":False,"h24":False,"sig":"Egg McMuffin","price":"$3-$8","color":"#FFC72C","drive":True,"kid":True},
 "Chick_fil_A":     {"name":"Chick-fil-A",      "start":"06:30","end":"10:30","allDay":False,"h24":False,"sig":"Chicken Biscuit","price":"$4-$9","color":"#DD0031","drive":True,"kid":True,"closedSun":True,"healthy":True},
 "Wendys":          {"name":"Wendy's",          "start":"06:30","end":"10:30","allDay":False,"h24":False,"sig":"Breakfast Baconator","price":"$4-$8","color":"#E2231A","drive":True,"kid":True},
 "Taco_Bell":       {"name":"Taco Bell",        "start":"07:00","end":"11:00","allDay":False,"h24":False,"sig":"Breakfast Crunchwrap","price":"$3-$7","color":"#702F8A","drive":True,"partial":True,"vegan":True},
 "Burger_King":     {"name":"Burger King",      "start":"06:00","end":"10:30","allDay":False,"h24":False,"sig":"Croissan'wich","price":"$4-$8","color":"#EC1C24","drive":True,"kid":True},
 "Hardees":         {"name":"Hardee's",         "start":"06:00","end":"10:30","allDay":False,"h24":False,"sig":"Loaded Omelet Biscuit","price":"$4-$9","color":"#FE7C1B","drive":True},
 "Panera_Bread":    {"name":"Panera Bread",     "start":"06:00","end":"10:30","wend":"11:00","allDay":False,"h24":False,"sig":"Cinnamon Crunch Bagel","price":"$5-$10","color":"#008751","healthy":True,"kid":True},
 "Whataburger":     {"name":"Whataburger",      "start":"23:00","end":"11:00","allDay":False,"h24":False,"sig":"Taquito","price":"$4-$8","color":"#FF7F00","drive":True,"extended":True},
 "Sonic":           {"name":"Sonic",            "allDay":True,"h24":False,"sig":"SuperSONIC Breakfast Burrito","price":"$3-$7","color":"#FFD100","drive":True},
 "Starbucks":       {"name":"Starbucks",        "allDay":True,"h24":False,"sig":"Bacon Gouda Sandwich","price":"$4-$9","color":"#00704A","healthy":True,"drive":True},
 "Jack_in_the_Box": {"name":"Jack in the Box",  "allDay":True,"h24":True, "sig":"Breakfast Jack","price":"$3-$8","color":"#B31B1B","drive":True},
 "IHOP":            {"name":"IHOP",             "allDay":True,"h24":False,"sig":"Original Buttermilk Pancakes","price":"$8-$16","color":"#0071CE","kid":True},
 "Arbys":           {"name":"Arby's",           "start":"06:00","end":"10:30","allDay":False,"h24":False,"sig":"Sausage Gravy Biscuit","price":"$4-$8","color":"#E11A2C","drive":True,"partial":True},
 "Cracker_Barrel":  {"name":"Cracker Barrel",   "start":"06:00","end":"11:00","allDay":False,"h24":False,"sig":"Momma's Pancake Breakfast","price":"$8-$14","color":"#5B1A18","kid":True,"brunch":True},
 "Golden_Corral":   {"name":"Golden Corral",    "start":"07:30","end":"14:00","allDay":False,"h24":False,"sig":"Weekend Breakfast Buffet","price":"$10-$16","color":"#EA1D2C","buffet":True,"kid":True,"weekendOnly":True},
 "Dennys":          {"name":"Denny's",          "allDay":True,"h24":True, "sig":"Grand Slam","price":"$7-$14","color":"#FFCC00","kid":True},
 "Dunkin_Donuts":   {"name":"Dunkin'",          "allDay":True,"h24":False,"sig":"Bacon Egg Cheese Wake-Up Wrap","price":"$3-$7","color":"#FF671F","drive":True},
 "Bojangles":       {"name":"Bojangles",        "allDay":True,"h24":False,"sig":"Cajun Filet Biscuit","price":"$4-$9","color":"#F6981E","drive":True},
 "Bob_Evans":       {"name":"Bob Evans",        "allDay":True,"h24":False,"sig":"Farmhouse Feast","price":"$8-$14","color":"#C8102E","kid":True},
 "First_Watch":     {"name":"First Watch",      "start":"07:00","end":"14:30","allDay":False,"h24":False,"sig":"Chickichanga","price":"$10-$16","color":"#93C540","healthy":True,"brunch":True,"kid":True,"vegan":True,"gf":True},
 "Subway":          {"name":"Subway",           "start":"07:00","end":"11:30","allDay":False,"h24":False,"sig":"Bacon Egg Cheese Wrap","price":"$4-$8","color":"#008C15","partial":True},
 "Waffle_House":    {"name":"Waffle House",     "allDay":True,"h24":True, "sig":"All-Star Special","price":"$7-$13","color":"#FFDC00"},
 "Tim_Hortons":     {"name":"Tim Hortons",      "allDay":True,"h24":False,"sig":"Breakfast Sandwich + Coffee","price":"$3-$7","color":"#C8102E","drive":True},
 "Braums":          {"name":"Braum's",          "start":"06:00","end":"10:30","allDay":False,"h24":False,"sig":"Breakfast Burrito + Shake","price":"$3-$7","color":"#F58026","drive":True,"kid":True},
 "Dairy_Queen":     {"name":"Dairy Queen",      "start":"06:00","end":"10:30","allDay":False,"h24":False,"sig":"Breakfast Chillers + Sandwiches","price":"$3-$7","color":"#EB1C2D","drive":True,"kid":True,"partial":True},
 "Caseys_General_Store": {"name":"Casey's",     "allDay":True,"h24":True,"sig":"Breakfast Pizza + Donuts","price":"$3-$6","color":"#DE1B26","drive":False,"kid":True},
 # NEW brands added Sep 26 based on SEO audit (replaced 6 low-SV brands)
 "Carls_Jr":        {"name":"Carl's Jr",        "start":"06:00","end":"10:30","wend":"11:00","allDay":False,"h24":False,"sig":"Made From Scratch Biscuit","price":"$4-$9","color":"#FED31C","drive":True,"kid":True},
 "Popeyes":         {"name":"Popeyes",          "start":"06:00","end":"10:30","allDay":False,"h24":False,"sig":"Chicken Waffle Sandwich","price":"$4-$9","color":"#F2822B","drive":True,"partial":True},
 "Portillos":       {"name":"Portillo's",       "start":"10:00","end":"11:00","allDay":False,"h24":False,"sig":"Chocolate Cake Shake + Breakfast Sandwich","price":"$5-$10","color":"#D71E28","drive":True,"kid":True,"partial":True},
 "Huckleberrys":    {"name":"Huckleberry's",    "start":"07:00","end":"15:00","allDay":False,"h24":False,"sig":"Southern Breakfast Skillet","price":"$10-$16","color":"#8B0000","kid":True,"brunch":True},
 "Kekes":           {"name":"Keke's Breakfast Cafe","start":"07:00","end":"14:30","allDay":False,"h24":False,"sig":"Belgian Waffles + Crepes","price":"$9-$15","color":"#F4A300","kid":True,"healthy":True,"brunch":True},
}

# Regex helpers
PHONE_RE = re.compile(r"[^\d+]+")
CLOSED_KEYS = ("disused:amenity","abandoned:amenity","demolished:amenity","demolished:building","construction:amenity","was:amenity","closed:amenity")

def is_active(props):
    """Filter closed/vacant/demolished/construction/disused."""
    if props.get("vacant") == "yes":
        return False
    if props.get("second_hand") == "only":  # (Golden Corral file had a used-car shop mistagged)
        return False
    for k in CLOSED_KEYS:
        if k in props:
            return False
    note = (props.get("note","") + " " + props.get("description","")).lower()
    if any(w in note for w in ("closed permanently","permanently closed","vacant","for lease","building is vacant")):
        return False
    # Also skip if amenity was removed and only brand:wikidata remains
    if not props.get("amenity") and not props.get("shop") and not props.get("name"):
        return False
    return True

def flags(props):
    """Bit flags encoded as string for compactness."""
    f = ""
    if props.get("drive_through") == "yes": f += "d"
    if props.get("takeaway") == "yes": f += "t"
    if props.get("delivery") == "yes": f += "l"
    if props.get("wheelchair") in ("yes","limited"): f += "w"
    if props.get("outdoor_seating") == "yes": f += "o"
    if props.get("internet_access") in ("wlan","yes"): f += "i"
    if props.get("diet:vegan") == "yes": f += "v"
    if props.get("diet:vegetarian") == "yes": f += "g"
    if props.get("diet:gluten_free") == "yes": f += "f"
    if props.get("air_conditioning") == "yes": f += "a"
    return f

def normalize_phone(p):
    if not p: return ""
    d = PHONE_RE.sub("", p)
    if d.startswith("+1") and len(d) == 12: return f"({d[2:5]}) {d[5:8]}-{d[8:12]}"
    if len(d) == 10: return f"({d[0:3]}) {d[3:6]}-{d[6:10]}"
    if len(d) == 11 and d.startswith("1"): return f"({d[1:4]}) {d[4:7]}-{d[7:11]}"
    return p.strip()

def build_addr(props):
    n = props.get("addr:housenumber","")
    s = props.get("addr:street","")
    return f"{n} {s}".strip() if (n or s) else ""

def process_brand(slug, meta):
    src_path = SRC / f"{slug}.geojson"
    if not src_path.exists():
        return None
    with open(src_path, "r") as f:
        gj = json.load(f)
    features = gj.get("features", [])
    out = []
    for feat in features:
        props = feat.get("properties", {})
        if not is_active(props): continue
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates")
        if not coords or len(coords) < 2: continue
        lng, lat = coords[0], coords[1]
        # Skip clearly invalid coords
        if not (-180 <= lng <= 180 and -90 <= lat <= 90): continue
        addr = build_addr(props)
        city = props.get("addr:city","")
        state = props.get("addr:state","")
        # Skip if we have absolutely nothing to show (no street AND no city)
        if not addr and not city:
            # Keep only if it has a phone or website (still useful data)
            if not (props.get("phone") or props.get("contact:phone") or props.get("website")):
                continue
        row = [
            round(lat, 5),
            round(lng, 5),
            addr,
            city,
            state,
            props.get("addr:postcode",""),
            normalize_phone(props.get("phone") or props.get("contact:phone","")),
            props.get("opening_hours",""),
            (props.get("website") or props.get("contact:website","")).replace("https://","").replace("http://","")[:60],
            flags(props)
        ]
        out.append(row)
    return out

def main():
    index = []
    total = 0
    for slug, meta in BRAND_META.items():
        rows = process_brand(slug, meta)
        if rows is None:
            print(f"[skip] {slug}: source not found")
            continue
        # deduplicate by rounded coord
        seen = set(); dedup = []
        for r in rows:
            key = (r[0], r[1])
            if key in seen: continue
            seen.add(key); dedup.append(r)
        rows = dedup
        out_path = DST / f"{slug}.json"
        payload = {"m": meta, "r": rows}
        with open(out_path, "w") as f:
            json.dump(payload, f, separators=(",", ":"))
        size_kb = out_path.stat().st_size // 1024
        print(f"[ok] {slug:24s} {len(rows):6,d} pins  {size_kb:5d} KB")
        index.append({"slug": slug, "name": meta["name"], "count": len(rows), "color": meta.get("color"), "size_kb": size_kb, **{k:v for k,v in meta.items() if k in ("allDay","h24","start","end","wend","sig","price","closedSun","weekendOnly","partial","extended")}})
        total += len(rows)
    with open(DST / "index.json", "w") as f:
        json.dump({"total": total, "brands": index}, f, separators=(",", ":"))
    print(f"\nTOTAL: {total:,} active breakfast locations across {len(index)} brands")

if __name__ == "__main__":
    main()
