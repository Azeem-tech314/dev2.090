#!/usr/bin/env python3
"""Semantic SEO plan aligned to user's 3-tier architecture:
  1. HOMEPAGE = ALL breakfast location/finder intent (incl. category+near-me)
  2. BRAND pages = one per chain
  3. CITY pages = one per city
  4. Content pages (later) = menu, hours, what-is-breakfast, brand-menu-Q&A

No cannibalization. Category-near-me queries stay on homepage because the
homepage tool already has filter chips (Healthy, Vegan, GF, 24hr, etc).
"""
import csv, re, json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
UPLOAD = Path('/root/.claude/uploads/9cc2ec04-7b9d-59f5-9da9-f69ee2e0c1e5')
FILES = [
    UPLOAD / '2f8514f9-keyword_magic_breakfast_near_me.csv',
    UPLOAD / '97825b07-keyword_magic_breakfast_places_1.csv',
    UPLOAD / '09966486-keyword_magic_breakfast.csv',
]

# Brand slug -> canonical name (route to per-brand pages)
BRAND_MAP = {
    'mcdonald': "McDonald's", 'mcdonalds': "McDonald's", 'mickey d': "McDonald's",
    'chick-fil-a': 'Chick-fil-A', 'chick fil a': 'Chick-fil-A', 'chickfila': 'Chick-fil-A', 'cfa': 'Chick-fil-A',
    "wendy's": "Wendy's", 'wendys': "Wendy's", "wendy ": "Wendy's",
    'burger king': 'Burger King', ' bk ': 'Burger King',
    'taco bell': 'Taco Bell',
    "hardee's": "Hardee's", "hardees": "Hardee's",
    "carl's jr": "Carl's Jr", 'carls jr': "Carl's Jr",
    'sonic': 'Sonic',
    'whataburger': 'Whataburger',
    'panera': 'Panera Bread',
    'jack in the box': 'Jack in the Box',
    'ihop': 'IHOP',
    "arby's": "Arby's", 'arbys': "Arby's",
    'cracker barrel': 'Cracker Barrel',
    'golden corral': 'Golden Corral',
    "denny's": "Denny's", 'dennys': "Denny's",
    'dunkin': 'Dunkin', 'dunkin donuts': 'Dunkin',
    'bojangle': 'Bojangles',
    'bob evans': 'Bob Evans',
    'first watch': 'First Watch',
    'subway': 'Subway',
    'waffle house': 'Waffle House',
    'krispy kreme': 'Krispy Kreme',
    'tim hortons': 'Tim Hortons',
    'perkins': 'Perkins',
    'village inn': 'Village Inn',
    'corner bakery': 'Corner Bakery',
    'metro diner': 'Metro Diner',
    'snooze': 'Snooze',
    "braum's": "Braum's", 'braums': "Braum's",
    'dairy queen': 'Dairy Queen',
    "casey's": "Casey's", 'caseys': "Casey's",
    'starbucks': 'Starbucks', 'sbux': 'Starbucks',
    # Additional chains from CSV data (route to their own pages if we onboard)
    'einstein': 'Einstein Bros',
    'kneaders': 'Kneaders',
    'another broken egg': 'Another Broken Egg',
    "shoney's": "Shoney's",
    'chipotle': 'Chipotle',
    'kfc': 'KFC',
    "popeye": 'Popeyes',
    'jamba': 'Jamba',
    'wawa': 'Wawa',
    'sheetz': 'Sheetz',
    'circle k': 'Circle K',
    'quiktrip': 'QuikTrip',
    '7 eleven': '7-Eleven', '7-eleven': '7-Eleven',
    'panda express': 'Panda Express',
    'chilis': "Chili's", "chili's": "Chili's",
    "applebee": "Applebee's",
    'olive garden': 'Olive Garden',
    'buc-ees': "Buc-ee's", 'buc ee': "Buc-ee's",
    'dutch bros': 'Dutch Bros',
    'big bad breakfast': 'Big Bad Breakfast',
    'huckleberry': "Huckleberry's",
    "salt's cure": "Salt's Cure", 'salts cure': "Salt's Cure",
    'breakfast republic': 'Breakfast Republic',
    'breakfast station': 'Breakfast Station',
    "portillo's": "Portillo's", 'portillos': "Portillo's",
    'breakfast klub': 'The Breakfast Klub',
    'lou mitchell': "Lou Mitchell's",
    'sarabeth': "Sarabeth's",
    'balthazar': 'Balthazar',
    'russ & daughters': 'Russ & Daughters', 'russ and daughters': 'Russ & Daughters',
    'cafe du monde': 'Cafe du Monde',
    'brennan': "Brennan's",
    'loveless': 'The Loveless Cafe',
    'silver skillet': 'The Silver Skillet',
    'sunny point': 'Sunny Point Café',
    'biscuit head': 'Biscuit Head',
    'wildberry': 'Wildberry Pancakes',
    'yolk': 'Yolk',
    'republique': 'Republique',
    'sqirl': 'Sqirl',
    'hash house': 'Hash House A Go Go',
    'peppermill': 'Peppermill',
    'ruby slipper': 'Ruby Slipper',
    'biscuit love': 'Biscuit Love',
    'pancake pantry': 'Pancake Pantry',
    'kerbey lane': 'Kerbey Lane',
    'magnolia cafe': 'Magnolia Cafe',
    'ellen': "Ellen's",
    'sabrinas': "Sabrina's", "sabrina's": "Sabrina's",
    'mike & patty': "Mike & Patty's",
    'norma': "Norma's",
    'clinton st': 'Clinton St. Baking',
    'zazie': 'Zazie',
    'plow': 'Plow',
    'mama': "Mama's",
    'br guest': 'BR Guest',
    'joe & the juice': 'Joe & The Juice',
    'metro diner': 'Metro Diner',
    'perkins': 'Perkins',
}

# Full state names + city names for city-page routing
CITY_MAP = {
    'new york': 'New York, NY', 'nyc': 'New York, NY', 'manhattan': 'New York, NY',
    'brooklyn': 'New York, NY', 'queens': 'New York, NY', 'bronx': 'New York, NY',
    'los angeles': 'Los Angeles, CA', 'la ': 'Los Angeles, CA', 'l.a.': 'Los Angeles, CA',
    'hollywood': 'Los Angeles, CA', 'santa monica': 'Los Angeles, CA',
    'chicago': 'Chicago, IL', 'houston': 'Houston, TX', 'phoenix': 'Phoenix, AZ',
    'philadelphia': 'Philadelphia, PA', 'san antonio': 'San Antonio, TX',
    'san diego': 'San Diego, CA', 'dallas': 'Dallas, TX', 'austin': 'Austin, TX',
    'jacksonville': 'Jacksonville, FL', 'fort worth': 'Fort Worth, TX',
    'columbus': 'Columbus, OH', 'charlotte': 'Charlotte, NC',
    'indianapolis': 'Indianapolis, IN', 'san francisco': 'San Francisco, CA',
    'seattle': 'Seattle, WA', 'denver': 'Denver, CO', 'washington dc': 'Washington, DC',
    'boston': 'Boston, MA', 'nashville': 'Nashville, TN', 'el paso': 'El Paso, TX',
    'detroit': 'Detroit, MI', 'oklahoma city': 'Oklahoma City, OK',
    'portland': 'Portland, OR', 'las vegas': 'Las Vegas, NV', 'memphis': 'Memphis, TN',
    'louisville': 'Louisville, KY', 'baltimore': 'Baltimore, MD',
    'milwaukee': 'Milwaukee, WI', 'albuquerque': 'Albuquerque, NM',
    'tucson': 'Tucson, AZ', 'fresno': 'Fresno, CA', 'sacramento': 'Sacramento, CA',
    'kansas city': 'Kansas City, MO', 'atlanta': 'Atlanta, GA', 'miami': 'Miami, FL',
    'raleigh': 'Raleigh, NC', 'omaha': 'Omaha, NE', 'long beach': 'Long Beach, CA',
    'virginia beach': 'Virginia Beach, VA', 'oakland': 'Oakland, CA',
    'minneapolis': 'Minneapolis, MN', 'tulsa': 'Tulsa, OK', 'tampa': 'Tampa, FL',
    'new orleans': 'New Orleans, LA', 'wichita': 'Wichita, KS',
    'cleveland': 'Cleveland, OH', 'honolulu': 'Honolulu, HI',
    'asheville': 'Asheville, NC', 'savannah': 'Savannah, GA',
    'charleston': 'Charleston, SC', 'orlando': 'Orlando, FL',
    'salt lake': 'Salt Lake City, UT', 'knoxville': 'Knoxville, TN',
    'chattanooga': 'Chattanooga, TN', 'madison': 'Madison, WI',
    'boise': 'Boise, ID', 'pittsburgh': 'Pittsburgh, PA',
    'myrtle beach': 'Myrtle Beach, SC', 'st. louis': 'St. Louis, MO',
    'st louis': 'St. Louis, MO', 'des moines': 'Des Moines, IA',
    'grand rapids': 'Grand Rapids, MI', 'ann arbor': 'Ann Arbor, MI',
    'birmingham': 'Birmingham, AL', 'reno': 'Reno, NV',
    'spokane': 'Spokane, WA', 'tacoma': 'Tacoma, WA', 'anchorage': 'Anchorage, AK',
    'lubbock': 'Lubbock, TX', 'pigeon forge': 'Pigeon Forge, TN',
    'disney springs': 'Orlando, FL', 'disney world': 'Orlando, FL',
    'gatlinburg': 'Gatlinburg, TN', 'branson': 'Branson, MO',
    'napa': 'Napa, CA', 'sonoma': 'Sonoma, CA', 'palm springs': 'Palm Springs, CA',
    'wildwood': 'Wildwood, NJ', 'ocean city': 'Ocean City, MD',
    'destin': 'Destin, FL', 'sarasota': 'Sarasota, FL', 'naples': 'Naples, FL',
    'key west': 'Key West, FL', 'daytona': 'Daytona, FL',
    'panama city': 'Panama City, FL', 'gulf shores': 'Gulf Shores, AL',
    'outer banks': 'Outer Banks, NC', 'kissimmee': 'Kissimmee, FL',
    'cocoa beach': 'Cocoa Beach, FL', 'st augustine': 'St. Augustine, FL',
    'sedona': 'Sedona, AZ', 'flagstaff': 'Flagstaff, AZ',
    'boulder': 'Boulder, CO', 'colorado springs': 'Colorado Springs, CO',
    'aspen': 'Aspen, CO', 'santa fe': 'Santa Fe, NM',
    'park city': 'Park City, UT', 'jackson hole': 'Jackson, WY',
    'lake tahoe': 'Lake Tahoe, CA', 'monterey': 'Monterey, CA',
    'carmel': 'Carmel, CA', 'annapolis': 'Annapolis, MD',
    'newport': 'Newport, RI', 'martha': 'Martha\'s Vineyard, MA',
    'nantucket': 'Nantucket, MA', 'cape cod': 'Cape Cod, MA',
    'hilton head': 'Hilton Head, SC', 'kiawah': 'Kiawah, SC',
    'st. paul': 'St. Paul, MN', 'st paul': 'St. Paul, MN',
    'buffalo': 'Buffalo, NY', 'rochester': 'Rochester, NY',
    'syracuse': 'Syracuse, NY', 'albany': 'Albany, NY',
}

RECIPES = ['recipe', 'ideas', 'how to make', 'how to cook', 'homemade',
           'meal prep', 'meal plan', 'menu ideas', 'breakfast for dinner',
           'protein breakfast', 'breakfast smoothie', 'breakfast bar',
           'breakfast bowl', 'breakfast casserole', 'crockpot',
           'oatmeal', 'egg recipe', 'pancake', 'french toast',
           'muffin', 'waffle recipe', 'breakfast burrito recipe',
           'toast recipe', 'bagel recipe', 'skillet recipe', 'quinoa',
           'chia', 'overnight oat', 'granola', 'high protein',
           'low carb breakfast', 'keto breakfast', 'diabetic breakfast',
           'breakfast sandwich recipe', 'breakfast pizza recipe',
           'breakfast potato', 'breakfast sausage', 'breakfast muffin',
           'breakfast quiche', 'breakfast pastry', 'breakfast fruit',
           'breakfast dish', 'breakfast food', 'breakfast foodstuff',
           'egg muffins', 'sausage links', 'sausage patty', 'sausage patties',
           'frozen breakfast', 'breakfast egg']

FOODS = ['english breakfast tea', 'irish breakfast tea', 'breakfast tea',
         'breakfast blend', 'breakfast drink', 'breakfast juice',
         'breakfast coffee', 'wedding breakfast', 'breakfast time cereal',
         'continental breakfast']

LODGING_FURNITURE = ['bed and breakfast', 'bed & breakfast', 'bed breakfast',
                     'b&b', 'breakfast nook', 'breakfast table',
                     'breakfast in bed', 'breakfast bar stool',
                     'breakfast bar chair', 'inn breakfast', 'hotel breakfast']

UNRELATED = ['breakfast club', 'breakfast at tiffany', 'kellogg breakfast plate',
             'pretty in pink', 'brat pack', 'anthony michael hall',
             'molly ringwald', 'judd nelson', 'ally sheedy', 'song lyric',
             ' movie ', ' film ', 'soundtrack', 'billy joel', 'audrey hepburn',
             'lyrics', 'chords', 'sheet music', 'meaning of', 'quote',
             'monologue', 'script', 'poem', ' book ', ' novel ',
             'filetype:', 'breakfast photo', 'breakfast sketch',
             'breakfast image', 'breakfast wallpaper', 'breakfast png',
             'breakfast gif', 'breakfast clipart', 'breakfast drawing',
             'breakfast animation', 'breakfast cartoon']

PRODUCTS = ['cereal', 'jimmy dean', 'kelloggs', "kellogg's", 'general mills',
            'quaker', 'nature valley', 'clif bar', 'special k', 'lucky charm',
            'cheerios', 'frosted flake', 'cocoa puff', 'cornflake',
            'protein bar', 'granola bar', 'nutrigrain', 'coco puff']

def load_all():
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
                try: cpc = float(row['CPC'])
                except: cpc = 0
                intent = row.get('Intent','')
                if k not in seen or seen[k]['vol'] < vol:
                    seen[k] = {'kw': k, 'vol': vol, 'kd': kd, 'cpc': cpc, 'intent': intent}
    return list(seen.values())

def detect_brand(k):
    kw = ' ' + k + ' '
    for pattern, name in BRAND_MAP.items():
        if pattern in kw:
            return name
    return None

def detect_city(k):
    kw = ' ' + k + ' '
    for pattern, name in CITY_MAP.items():
        if pattern in kw:
            return name
    return None

def classify(k):
    kw = ' ' + k + ' '
    # Reject rows first (recipes, food-cuisine, lodging, products, unrelated)
    for u in UNRELATED:
        if u in kw: return ('unrelated', None)
    for l in LODGING_FURNITURE:
        if l in kw: return ('lodging', None)
    for r in RECIPES:
        if r in kw: return ('recipe', None)
    for f in FOODS:
        if f in kw: return ('food-cuisine', None)
    for p in PRODUCTS:
        if p in kw: return ('product', None)
    # Brand check
    brand = detect_brand(k)
    if brand:
        return ('brand', brand)
    # City check
    city = detect_city(k)
    if city:
        return ('city', city)
    # Everything else that has any "breakfast" AND doesn't match rejects = HOMEPAGE
    # This includes: healthy breakfast near me, vegan breakfast, halal breakfast,
    # 24 hour breakfast, cheap breakfast, drive thru breakfast, breakfast buffet,
    # brunch, all-day breakfast, etc. — the homepage tool already filters these
    return ('homepage', None)

def priority(row):
    vol, kd = row['vol'], row['kd']
    score = (vol ** 0.5) * (100 - kd)
    if 'T' in row['intent'] or 'C' in row['intent']:
        score *= 1.3
    return score

def priority_label(score, max_score):
    p = score / max_score * 100 if max_score else 0
    if p >= 40: return 'P0'
    if p >= 15: return 'P1'
    if p >= 5: return 'P2'
    return 'P3'

def main():
    all_kws = load_all()
    print(f'Loaded {len(all_kws)} unique keywords')
    for r in all_kws:
        b, target = classify(r['kw'])
        r['bucket'] = b
        r['target'] = target

    buckets = defaultdict(list)
    for r in all_kws:
        buckets[r['bucket']].append(r)

    print('\nBucket totals:')
    for b, v in sorted(buckets.items(), key=lambda x: -sum(r['vol'] for r in x[1])):
        print(f'  {b:15s} {len(v):5d} kws  {sum(r["vol"] for r in v):>12,d} SV')

    # Sort homepage
    homepage = sorted(buckets['homepage'], key=priority, reverse=True)
    max_score = priority(homepage[0]) if homepage else 1

    # Group brand by brand-name
    brand_groups = defaultdict(list)
    for r in buckets['brand']: brand_groups[r['target']].append(r)
    # Group city by city-name
    city_groups = defaultdict(list)
    for r in buckets['city']: city_groups[r['target']].append(r)

    # Write markdown
    out = ROOT / 'docs' / 'SEO_KEYWORDS.md'
    out.parent.mkdir(exist_ok=True)
    L = []
    L.append('# BreakfastPlaces.us — 3-Tier Semantic SEO Roadmap\n')
    L.append(f'**Source**: 3 SEMrush Keyword Magic exports · {len(all_kws):,} unique keywords deduplicated.  \n')
    L.append(f'**Strategy**: build breakfast-location authority first (homepage) → per-brand pages → per-city pages → content deep-dives (menus, hours) later.  \n')
    L.append(f'**Rule**: every keyword lives in ONE destination. Category-with-near-me keywords stay on homepage because the homepage map already filters by Healthy / Vegan / GF / 24hr / Cheap / etc. via its filter chips. No separate category page duplicates that intent.\n\n')
    L.append('---\n\n')

    # HOMEPAGE
    home_sv = sum(r['vol'] for r in homepage)
    home_actionable = [r for r in homepage if r['vol'] >= 100]
    L.append(f'## 🏠 TIER 1 — HOMEPAGE `/`\n\n')
    L.append(f'**One page ranks for all breakfast location & category finder queries.** Combines `breakfast near me` + `healthy breakfast near me` + `24 hour breakfast` + `breakfast buffet near me` + `vegan breakfast near me` + every filter+near-me combo. The map on the homepage already has these as filter chips, so URL stays `/`.  \n\n')
    L.append(f'**Total addressable market**: {len(homepage):,} keywords · **{home_sv:,} monthly searches**  \n')
    L.append(f'**Actionable (≥100 SV)**: {len(home_actionable):,} keywords · {sum(r["vol"] for r in home_actionable):,} SV\n\n')
    L.append('### Top 60 homepage target keywords\n\n')
    L.append('| # | Keyword | SV | KD | CPC | Intent | Priority |\n|---|---|---:|---:|---:|---|:-:|\n')
    for i, r in enumerate(home_actionable[:60], 1):
        L.append(f'| {i} | {r["kw"]} | {r["vol"]:,} | {r["kd"]} | ${r["cpc"]:.2f} | {r["intent"]} | {priority_label(priority(r), max_score)} |\n')
    L.append('\n')

    # Show a sample of category-with-near-me keywords going on homepage
    L.append('### Category-modifier keywords absorbed into homepage (sample)\n\n')
    L.append('These would have been separate pages under the old plan. They belong on the homepage because the map already filters by these categories via chips. **Each maps to an existing filter chip.**  \n\n')
    L.append('| Keyword | SV | Which homepage filter chip serves it |\n|---|---:|---|\n')
    def find_first(hay_terms):
        for r in homepage:
            if any(t in r['kw'] for t in hay_terms):
                return r
        return None
    filter_map = [
        (['healthy'], '🥗 Healthy'),
        (['vegan'], '🌱 Vegan'),
        (['halal'], '🕌 Halal'),
        (['gluten', 'gluten-free', 'gluten free'], '🌾 Gluten-Free'),
        (['24 hour', '24-hour'], '🌙 24-Hour'),
        (['cheap', 'under 10', 'under 5'], '💰 Under $10'),
        (['buffet'], '🍽️ Buffet'),
        (['drive thru', 'drive-thru'], '🚗 Drive-Thru'),
        (['brunch'], '🍹 Brunch'),
        (['all day', 'all-day'], '🕐 All-Day'),
        (['kid', 'family'], '👨‍👩‍👧 Kid-Friendly'),
        (['delivery'], '🛵 Delivery (planned chip)'),
        (['takeout', 'to go'], '🚗 Takeout (planned chip)'),
        (['catering'], '🍱 Catering (planned chip)'),
        (['open now'], '🟢 Serving Now'),
    ]
    for terms, chip in filter_map:
        # Sum SV for all keywords containing these terms
        matches = [r for r in homepage if any(t in r['kw'] for t in terms)]
        if not matches: continue
        top = max(matches, key=lambda x: x['vol'])
        total = sum(r['vol'] for r in matches)
        L.append(f'| {top["kw"]} (+{len(matches)-1} variants, {total:,} combined SV) | {top["vol"]:,} | {chip} |\n')
    L.append('\n---\n\n')

    # TIER 2: BRAND PAGES
    L.append('## 🏪 TIER 2 — BRAND PAGES (one per chain)\n\n')
    L.append(f'**{len(buckets["brand"]):,} brand-specific keywords · {sum(r["vol"] for r in buckets["brand"]):,} SV combined.**  \n')
    L.append('Each brand gets its own URL. Keywords cluster naturally by brand — no cross-brand cannibalization.\n\n')
    L.append('### Brand pages by total search volume\n\n')
    L.append('| # | Brand | URL | Keywords | Total SV | Top query |\n|---|---|---|---:|---:|---|\n')
    ranked_brands = sorted(brand_groups.items(), key=lambda x: -sum(r['vol'] for r in x[1]))
    for i, (brand, rows) in enumerate(ranked_brands[:32], 1):
        slug = re.sub(r"[^a-z0-9]+", '-', brand.lower()).strip('-')
        top_kw = max(rows, key=lambda x: x['vol'])
        L.append(f'| {i} | {brand} | `/{slug}-breakfast-hours/` | {len(rows)} | {sum(r["vol"] for r in rows):,} | {top_kw["kw"]} ({top_kw["vol"]:,}) |\n')
    L.append('\n')
    # Detailed per-brand keywords for top 10 brands
    L.append('### Detailed keyword cluster for top 10 brands\n\n')
    for i, (brand, rows) in enumerate(ranked_brands[:10], 1):
        rows_sorted = sorted(rows, key=priority, reverse=True)
        L.append(f'#### {i}. {brand}\n\n')
        L.append(f'{len(rows)} keywords · {sum(r["vol"] for r in rows):,} SV\n\n')
        L.append('| Keyword | SV | KD | Priority |\n|---|---:|---:|:-:|\n')
        for r in rows_sorted[:20]:
            L.append(f'| {r["kw"]} | {r["vol"]:,} | {r["kd"]} | {priority_label(priority(r), max_score)} |\n')
        if len(rows) > 20:
            L.append(f'| _…and {len(rows)-20} more long-tail variants for body content_ | | | |\n')
        L.append('\n')
    L.append('---\n\n')

    # TIER 3: CITY PAGES
    L.append('## 🌆 TIER 3 — CITY PAGES (one per top-search city)\n\n')
    L.append(f'**{len(buckets["city"]):,} city-specific keywords · {sum(r["vol"] for r in buckets["city"]):,} SV combined.**  \n')
    L.append('Each city page filters the map to that city + adds curated indie picks + neighborhood breakdown.\n\n')
    L.append('### Top 40 cities by search volume\n\n')
    L.append('| # | City | URL | Keywords | Total SV | Top query |\n|---|---|---|---:|---:|---|\n')
    ranked_cities = sorted(city_groups.items(), key=lambda x: -sum(r['vol'] for r in x[1]))
    for i, (city, rows) in enumerate(ranked_cities[:40], 1):
        slug = re.sub(r"[^a-z0-9]+", '-', city.lower()).strip('-')
        top_kw = max(rows, key=lambda x: x['vol'])
        L.append(f'| {i} | {city} | `/breakfast-in-{slug}/` | {len(rows)} | {sum(r["vol"] for r in rows):,} | {top_kw["kw"]} ({top_kw["vol"]:,}) |\n')
    L.append('\n')
    L.append('### Detailed keyword cluster for top 10 cities\n\n')
    for i, (city, rows) in enumerate(ranked_cities[:10], 1):
        rows_sorted = sorted(rows, key=priority, reverse=True)
        L.append(f'#### {i}. {city}\n\n')
        L.append(f'{len(rows)} keywords · {sum(r["vol"] for r in rows):,} SV\n\n')
        L.append('| Keyword | SV | KD | Priority |\n|---|---:|---:|:-:|\n')
        for r in rows_sorted[:15]:
            L.append(f'| {r["kw"]} | {r["vol"]:,} | {r["kd"]} | {priority_label(priority(r), max_score)} |\n')
        if len(rows) > 15:
            L.append(f'| _…and {len(rows)-15} more long-tail variants_ | | | |\n')
        L.append('\n')
    L.append('---\n\n')

    # EXCLUDED
    L.append('## 🚫 EXCLUDED — not any of our page types\n\n')
    L.append('| Cluster | Count | SV | Reason |\n|---|---:|---:|---|\n')
    excluded = {
        'recipe': ('Recipes / cooking / meal prep', 'Not our niche — competing with Allrecipes / BBCGoodFood'),
        'food-cuisine': ('Beverage / food articles (english breakfast tea, breakfast blend)', 'Not our niche — food/beverage editorial'),
        'lodging': ('Lodging + furniture (bed & breakfast, breakfast nook)', 'Not our niche — B&B lodging + furniture market'),
        'product': ('Grocery products (cereal brands, jimmy dean)', 'Not our niche — grocery/retail'),
        'unrelated': ('Movies, books, songs, image searches (Breakfast Club, breakfast png)', 'Skip'),
    }
    for b, (label, reason) in excluded.items():
        if b in buckets:
            L.append(f'| {label} | {len(buckets[b]):,} | {sum(r["vol"] for r in buckets[b]):,} | {reason} |\n')
    L.append('\n---\n\n')

    # TOTALS
    total_captured = home_sv + sum(r['vol'] for r in buckets['brand']) + sum(r['vol'] for r in buckets['city'])
    L.append('## 📊 GRAND TOTALS — REAL DATA, NO GUESSING\n\n')
    L.append(f'- 🏠 **Homepage** (all breakfast finder + category+near-me): **{home_sv:,} SV/month**\n')
    L.append(f'- 🏪 **Brand pages** ({len(brand_groups)} unique brands): **{sum(r["vol"] for r in buckets["brand"]):,} SV/month**\n')
    L.append(f'- 🌆 **City pages** ({len(city_groups)} unique cities): **{sum(r["vol"] for r in buckets["city"]):,} SV/month**\n')
    L.append(f'- ✅ **Grand addressable market across your 3 tiers**: **{total_captured:,} SV/month**\n')
    L.append(f'- 🚫 Excluded (not our niche): {sum(sum(r["vol"] for r in v) for k,v in buckets.items() if k in ("recipe","food-cuisine","lodging","product","unrelated")):,} SV/month → skipped\n\n')

    out.write_text(''.join(L))
    print(f'\nWrote {out} ({out.stat().st_size//1024} KB)')

if __name__ == '__main__':
    main()
