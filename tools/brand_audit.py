#!/usr/bin/env python3
"""Complete brand audit:
  1. Compare 32 map-tool brands vs top-32 SEO brand list
  2. For every map brand, sum SV across all 3 CSVs
  3. Find ALL brand names mentioned in the CSVs (comprehensive scan)
  4. Show which brands we have vs missing vs unmapped
"""
import csv, json, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
UPLOAD = Path('/root/.claude/uploads/9cc2ec04-7b9d-59f5-9da9-f69ee2e0c1e5')
FILES = [
    UPLOAD / '2f8514f9-keyword_magic_breakfast_near_me.csv',
    UPLOAD / '97825b07-keyword_magic_breakfast_places_1.csv',
    UPLOAD / '09966486-keyword_magic_breakfast.csv',
]

# Full comprehensive brand-pattern map (case insensitive, matches in keyword)
# Order matters: longer patterns first to avoid mis-matches
BRAND_PATTERNS = [
    # Big national chains
    ("mcdonald's", "McDonald's"), ("mcdonalds", "McDonald's"), ("mickey d", "McDonald's"),
    ("chick-fil-a", "Chick-fil-A"), ("chick fil a", "Chick-fil-A"), ("chickfila", "Chick-fil-A"), ("chick fila", "Chick-fil-A"),
    ("wendy's", "Wendy's"), ("wendys", "Wendy's"),
    ("burger king", "Burger King"),
    ("taco bell", "Taco Bell"),
    ("hardee's", "Hardee's"), ("hardees", "Hardee's"),
    ("carl's jr", "Carl's Jr"), ("carls jr", "Carl's Jr"), ("carl jr", "Carl's Jr"),
    ("panera bread", "Panera Bread"), ("panera", "Panera Bread"),
    ("whataburger", "Whataburger"),
    ("sonic", "Sonic"),
    ("jack in the box", "Jack in the Box"),
    ("ihop", "IHOP"),
    ("arby's", "Arby's"), ("arbys", "Arby's"),
    ("cracker barrel", "Cracker Barrel"),
    ("golden corral", "Golden Corral"),
    ("denny's", "Denny's"), ("dennys", "Denny's"),
    ("dunkin donuts", "Dunkin"), ("dunkin", "Dunkin"),
    ("bojangles", "Bojangles"), ("bojangle", "Bojangles"),
    ("bob evans", "Bob Evans"),
    ("first watch", "First Watch"),
    ("subway", "Subway"),
    ("waffle house", "Waffle House"),
    ("krispy kreme", "Krispy Kreme"),
    ("tim hortons", "Tim Hortons"),
    ("perkins", "Perkins"),
    ("village inn", "Village Inn"),
    ("corner bakery", "Corner Bakery"),
    ("metro diner", "Metro Diner"),
    ("snooze", "Snooze A.M. Eatery"),
    ("braum's", "Braum's"), ("braums", "Braum's"),
    ("dairy queen", "Dairy Queen"), ("dq ", "Dairy Queen"),
    ("casey's", "Casey's"), ("caseys", "Casey's"),
    ("starbucks", "Starbucks"), ("sbux", "Starbucks"),
    # Additional chains found in CSV data (NOT in current 32-brand map)
    ("einstein bros", "Einstein Bros Bagels"), ("einstein bagel", "Einstein Bros Bagels"),
    ("einstein bros bagels", "Einstein Bros Bagels"), ("einstein noah", "Einstein Bros Bagels"),
    ("kneaders", "Kneaders Bakery"),
    ("another broken egg", "Another Broken Egg"),
    ("shoney's", "Shoney's"), ("shoneys", "Shoney's"),
    ("chipotle", "Chipotle"),
    ("kfc", "KFC"),
    ("popeyes", "Popeyes"), ("popeye's", "Popeyes"),
    ("jamba juice", "Jamba Juice"), ("jamba", "Jamba Juice"),
    ("wawa", "Wawa"),
    ("sheetz", "Sheetz"),
    ("circle k", "Circle K"),
    ("quiktrip", "QuikTrip"), ("qt ", "QuikTrip"),
    ("7-eleven", "7-Eleven"), ("7 eleven", "7-Eleven"),
    ("racetrac", "RaceTrac"),
    ("panda express", "Panda Express"),
    ("chili's", "Chili's"), ("chilis", "Chili's"),
    ("applebee's", "Applebee's"), ("applebees", "Applebee's"),
    ("olive garden", "Olive Garden"),
    ("outback", "Outback Steakhouse"),
    ("texas roadhouse", "Texas Roadhouse"),
    ("longhorn", "LongHorn Steakhouse"),
    ("buc-ee's", "Buc-ee's"), ("buc ee", "Buc-ee's"), ("bucees", "Buc-ee's"),
    ("dutch bros", "Dutch Bros"),
    ("big bad breakfast", "Big Bad Breakfast"),
    ("huckleberry's", "Huckleberry's"), ("huckleberry", "Huckleberry's"),
    ("salt's cure", "Salt's Cure"), ("salts cure", "Salt's Cure"),
    ("breakfast republic", "Breakfast Republic"),
    ("breakfast station", "Breakfast Station"),
    ("portillo's", "Portillo's"), ("portillos", "Portillo's"),
    ("the breakfast klub", "The Breakfast Klub"), ("breakfast klub", "The Breakfast Klub"),
    ("lou mitchell", "Lou Mitchell's"),
    ("sarabeth's", "Sarabeth's"), ("sarabeths", "Sarabeth's"),
    ("balthazar", "Balthazar"),
    ("russ & daughters", "Russ & Daughters"), ("russ and daughters", "Russ & Daughters"),
    ("cafe du monde", "Cafe du Monde"), ("café du monde", "Cafe du Monde"),
    ("brennan's", "Brennan's"),
    ("loveless cafe", "The Loveless Cafe"), ("loveless café", "The Loveless Cafe"),
    ("silver skillet", "The Silver Skillet"),
    ("sunny point", "Sunny Point Café"),
    ("biscuit head", "Biscuit Head"),
    ("wildberry", "Wildberry Pancakes"),
    ("yolk", "Yolk"),
    ("republique", "Republique"), ("république", "Republique"),
    ("sqirl", "Sqirl"),
    ("hash house", "Hash House A Go Go"),
    ("peppermill", "Peppermill Restaurant"),
    ("ruby slipper", "Ruby Slipper"),
    ("biscuit love", "Biscuit Love"),
    ("pancake pantry", "Pancake Pantry"),
    ("kerbey lane", "Kerbey Lane Cafe"),
    ("magnolia cafe", "Magnolia Cafe"), ("magnolia café", "Magnolia Cafe"),
    ("ellen's", "Ellen's"),
    ("sabrina's", "Sabrina's"), ("sabrinas", "Sabrina's"),
    ("mike & patty's", "Mike & Patty's"), ("mike and patty", "Mike & Patty's"),
    ("norma's", "Norma's"), ("normas", "Norma's"),
    ("clinton st", "Clinton St. Baking"),
    ("zazie", "Zazie"),
    ("plow", "Plow"),
    ("mama's on washington", "Mama's on Washington"),
    ("brenda's", "Brenda's French Soul Food"),
    ("brother juniper", "Brother Juniper's"),
    ("blue plate cafe", "Blue Plate Cafe"),
    ("bouchon", "Bouchon Bakery"),
    ("mr mamas", "Mr Mamas Breakfast"), ("mr. mamas", "Mr Mamas Breakfast"),
    ("empire state south", "Empire State South"),
    ("west egg cafe", "West Egg Cafe"), ("west egg café", "West Egg Cafe"),
    ("early girl", "Early Girl Eatery"),
    ("tupelo honey", "Tupelo Honey Cafe"),
    ("snooze am", "Snooze A.M. Eatery"), ("snooze a.m.", "Snooze A.M. Eatery"),
    ("denver biscuit", "Denver Biscuit Company"),
    ("sam's no. 3", "Sam's No. 3"), ("sams no 3", "Sam's No. 3"),
    ("bill smith", "Bill Smith's Cafe"),
    ("bubby's", "Bubby's"), ("bubbys", "Bubby's"),
    ("cafe cluny", "Cafe Cluny"), ("café cluny", "Cafe Cluny"),
    ("ess-a-bagel", "Ess-a-Bagel"), ("ess a bagel", "Ess-a-Bagel"),
    ("jack's wife freda", "Jack's Wife Freda"),
    ("cafe mogador", "Cafe Mogador"), ("café mogador", "Cafe Mogador"),
    ("buvette", "Buvette"),
    ("the smith", "The Smith"),
    ("bongo room", "Bongo Room"),
    ("bottega louie", "Bottega Louie"),
    ("nickel diner", "Nickel Diner"),
    ("sunrise memphis", "Sunrise Memphis"),
    ("ruby slipper", "Ruby Slipper Cafe"),
    ("cafe 21", "Cafe 21 Gaslamp"), ("café 21", "Cafe 21 Gaslamp"),
    ("green eggs cafe", "Green Eggs Cafe"),
    ("honey's sit", "Honey's Sit 'n Eat"),
    ("down home diner", "Down Home Diner"),
    ("trident booksellers", "Trident Booksellers & Cafe"),
    ("tatte bakery", "Tatte Bakery"),
    ("south street diner", "South Street Diner"),
    ("cafe roze", "Café Roze"), ("café roze", "Café Roze"),
    ("bouldin creek", "Bouldin Creek Cafe"),
    ("24 diner", "24 Diner"),
    ("house of pies", "House of Pies"),
    ("le peep", "Le Peep"),
    ("egg harbor", "Egg Harbor Cafe"),
    ("original pancake", "Original Pancake House"),
    ("keke's breakfast", "Keke's Breakfast Cafe"),
    ("skillets", "Skillets"),
    ("mimi's cafe", "Mimi's Cafe"), ("mimis cafe", "Mimi's Cafe"),
    ("black bear diner", "Black Bear Diner"),
    ("cafe rio", "Cafe Rio"), ("café rio", "Cafe Rio"),
    ("panera bread", "Panera Bread"),
    ("noodles and company", "Noodles and Company"),
    ("qdoba", "Qdoba"),
    ("moe's southwest", "Moe's Southwest Grill"), ("moes southwest", "Moe's Southwest Grill"),
    ("del taco", "Del Taco"),
    ("fazoli", "Fazoli's"),
    ("bakers square", "Bakers Square"), ("baker's square", "Bakers Square"),
    ("marie callender", "Marie Callender's"),
    ("coco's", "Coco's"),
    ("shari's cafe", "Shari's Cafe"),
    ("ihop menu", "IHOP"),
]

def scan_brand(k):
    """Return canonical brand name if keyword mentions a brand, else None."""
    kw = ' ' + k.lower() + ' '
    for pattern, name in BRAND_PATTERNS:
        if pattern in kw:
            return name
    return None

def load_kws():
    seen = {}
    for f in FILES:
        with open(f, 'r', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                k = row['Keyword'].strip().lower()
                try: vol = int(row['Volume'])
                except: vol = 0
                try: kd = int(row['KD %'])
                except: kd = 0
                if k not in seen or seen[k]['vol'] < vol:
                    seen[k] = {'kw': k, 'vol': vol, 'kd': kd}
    return list(seen.values())

# Load current 32 map brands
idx = json.load(open(ROOT/'data'/'compact'/'index.json'))
map_brands = set()
for b in idx['brands']:
    n = b['name']
    if n == "Dunkin'": n = 'Dunkin'
    map_brands.add(n)

# Load & classify all keywords by brand
kws = load_kws()
brand_kws = defaultdict(list)
for r in kws:
    b = scan_brand(r['kw'])
    if b:
        brand_kws[b].append(r)

# Compute SV per brand
brand_sv = {b: sum(r['vol'] for r in rows) for b, rows in brand_kws.items()}

# 32 map brands + SV from CSV
print('='*80)
print('MAP TOOL BRANDS (32) — with SEO search volume from CSVs')
print('='*80)
print(f'{"#":<3} {"Brand":<28s} {"Map Loc":>8s} {"SEO SV":>12s} {"# KWs":>7s}')
print('-'*80)
map_data = []
for b in idx['brands']:
    n = b['name']
    key = 'Dunkin' if n == "Dunkin'" else n
    key = 'Snooze A.M. Eatery' if n == 'Snooze A.M. Eatery' else key
    sv = brand_sv.get(key, 0)
    nk = len(brand_kws.get(key, []))
    map_data.append((n, b['count'], sv, nk))
map_data.sort(key=lambda x: -x[2])
for i, (n, loc, sv, nk) in enumerate(map_data, 1):
    print(f'{i:<3} {n:<28s} {loc:>8,d} {sv:>12,d} {nk:>7d}')

# Brands in map but with LOW/ZERO SEO volume (may be niche in map, weak SEO play)
low_sv_map = [x for x in map_data if x[2] < 5000]
if low_sv_map:
    print(f'\n⚠️  Map brands with <5K SEO SV (weak individual page potential):')
    for n, loc, sv, nk in low_sv_map:
        print(f'    {n} — {sv:,} SV · {nk} keywords')

# Brands mentioned in CSV but NOT in map
print('\n')
print('='*80)
print('BRANDS FOUND IN CSVs BUT NOT IN CURRENT 32-BRAND MAP')
print('='*80)
csv_brands = set(brand_kws.keys())
missing = sorted(csv_brands - map_brands, key=lambda b: -brand_sv[b])
print(f'{"#":<3} {"Brand":<32s} {"SEO SV":>12s} {"# KWs":>7s}  Top query')
print('-'*100)
for i, b in enumerate(missing[:60], 1):
    top = max(brand_kws[b], key=lambda x: x['vol'])
    print(f'{i:<3} {b:<32s} {brand_sv[b]:>12,d} {len(brand_kws[b]):>7d}  {top["kw"]} ({top["vol"]:,})')

# ALL brands complete list from CSV
print('\n')
print('='*80)
print(f'FULL BRAND ROSTER FROM CSVs — {len(csv_brands)} unique brand entities detected')
print('='*80)
all_sorted = sorted(brand_kws.items(), key=lambda x: -sum(r['vol'] for r in x[1]))
print(f'Total brand-attributable SV: {sum(brand_sv.values()):,}')

# Save comprehensive brand audit MD
out = ROOT / 'docs' / 'BRAND_AUDIT.md'
L = []
L.append('# Brand Audit: Map Tool vs SEO Keywords\n\n')
L.append(f'**Data**: {len(kws):,} unique keywords across 3 SEMrush CSVs · scanned against {len(BRAND_PATTERNS)} brand patterns.\n\n')
L.append(f'**Detected**: {len(csv_brands)} unique brands in the CSV data · **{sum(brand_sv.values()):,} SV attributed to brand queries**.\n\n')

L.append('## 1. Current 32 map-tool brands — with actual CSV search volume\n\n')
L.append('| # | Map Brand | Map Locations | SEO SV/mo | # KWs | Verdict |\n|---|---|---:|---:|---:|---|\n')
for i, (n, loc, sv, nk) in enumerate(map_data, 1):
    verdict = '🟢 Strong SEO' if sv >= 50000 else ('🟡 Moderate SEO' if sv >= 10000 else ('🟠 Weak SEO' if sv >= 1000 else '🔴 Minimal SEO'))
    L.append(f'| {i} | **{n}** | {loc:,} | {sv:,} | {nk} | {verdict} |\n')
L.append('\n')

L.append('## 2. Missing from map — brands with SEO volume you\'re not covering\n\n')
L.append('These brands appear in the search-keyword data but aren\'t in the current 32-brand map. Adding them (via new GeoJSON pulls) would capture the SV below.\n\n')
L.append('| # | Brand (missing from map) | SEO SV/mo | # KWs | Top query | Recommended action |\n|---|---|---:|---:|---|---|\n')
for i, b in enumerate(missing[:40], 1):
    top = max(brand_kws[b], key=lambda x: x['vol'])
    if brand_sv[b] >= 100000: action = '**Add to map + build page**'
    elif brand_sv[b] >= 25000: action = 'Add to map (Phase 2)'
    elif brand_sv[b] >= 5000: action = 'Optional Phase 3 addition'
    else: action = 'Skip — long tail'
    L.append(f'| {i} | {b} | {brand_sv[b]:,} | {len(brand_kws[b])} | {top["kw"]} ({top["vol"]:,}) | {action} |\n')
L.append('\n')

L.append('## 3. Complete brand roster (every unique brand detected in CSVs)\n\n')
L.append('Ordered by total search volume. First 32 are the strongest per-page candidates.\n\n')
L.append('| # | Brand | In Map? | SEO SV/mo | # KWs | Top query |\n|---|---|:-:|---:|---:|---|\n')
for i, (b, rows) in enumerate(all_sorted, 1):
    in_map = '✅' if b in map_brands else '❌'
    top = max(rows, key=lambda x: x['vol'])
    L.append(f'| {i} | {b} | {in_map} | {brand_sv[b]:,} | {len(rows)} | {top["kw"]} ({top["vol"]:,}) |\n')

L.append('\n---\n\n')
L.append('## 4. Strategic recommendations\n\n')
strong_map = [x for x in map_data if x[2] >= 50000]
weak_map = [x for x in map_data if x[2] < 5000]
strong_missing = [b for b in missing if brand_sv[b] >= 25000]
L.append(f'### Keep + prioritize (already in map, strong SEO)\n')
L.append(f'{len(strong_map)} brands. These get individual brand pages first because they combine real store footprint + real search demand.\n\n')
for n, loc, sv, nk in strong_map[:15]:
    L.append(f'- **{n}** — {loc:,} map locations · {sv:,} SV\n')
L.append('\n')
L.append(f'### Consider dropping from map (low SEO value, taking data space)\n')
L.append(f'{len(weak_map)} brands. Still keep in map for user completeness (people searching for indie diners in specific cities), but don\'t build separate brand pages.\n\n')
for n, loc, sv, nk in weak_map:
    L.append(f'- **{n}** — {loc:,} map locations · only {sv:,} SV\n')
L.append('\n')
L.append(f'### Add to map + page network (missing but high SV)\n')
L.append(f'{len(strong_missing)} brands with ≥25K SV are missing. Adding them would capture significant traffic.\n\n')
for b in strong_missing[:15]:
    top = max(brand_kws[b], key=lambda x: x['vol'])
    L.append(f'- **{b}** — {brand_sv[b]:,} SV · top query "{top["kw"]}" ({top["vol"]:,} SV)\n')
L.append('\n')

out.write_text(''.join(L))
print(f'\n\nWrote {out} ({out.stat().st_size//1024} KB)')
