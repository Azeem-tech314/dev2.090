#!/usr/bin/env python3
"""Analyze 3 SEMrush keyword CSVs and produce a semantic-clustered SEO plan.

- Dedupes across all 3 files by keyword
- Filters out: brand names (per-brand pages), city names (per-city pages),
  recipe/cooking intent (not our niche), unrelated (movie, cereal, etc.)
- Clusters by intent: homepage, category, chain-generic, breakfast-food
- Assigns priority based on SV × (100-KD) score
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

# Brand names -> route to per-brand pages, exclude from homepage plan
BRANDS = ['mcdonald', 'mcdonalds', 'mcd', "mickey d", 'starbucks', 'sbux',
          'chick-fil-a', 'chick fil a', 'chickfila', 'cfa',
          "wendy", "wendys", 'burger king', 'bk ', 'taco bell', 'tbell',
          "hardee", "carl's jr", 'carls jr', 'sonic', 'whataburger',
          'panera', 'jack in the box', 'jib', 'ihop', "arby's", 'arbys',
          'cracker barrel', 'golden corral', "denny's", 'dennys', 'dunkin',
          'dunkin donuts', "bojangle", "bob evans", 'first watch', 'subway',
          'waffle house', 'krispy kreme', 'tim hortons', 'perkins',
          'village inn', 'corner bakery', 'metro diner', 'snooze',
          "braum's", 'braums', 'dairy queen', "casey's", 'caseys',
          'einstein', 'kneaders', 'another broken egg', "shoney's",
          'chipotle', 'kfc', "popeye", "hardee's", 'jamba', 'wawa',
          'sheetz', 'circle k', 'quiktrip', '7 eleven', '7-eleven',
          'panda express', 'chilis', "applebee", "denny", 'olive garden',
          'sheetz', 'buc-ees', 'buc ee', 'dutch bros']

# City / state names -> route to per-city pages
CITIES = ['new york', 'nyc', 'los angeles', ' l.a. ', 'chicago', 'houston',
          'phoenix', 'philadelphia', 'san antonio', 'san diego', 'dallas',
          'austin', 'jacksonville', 'fort worth', 'columbus', 'charlotte',
          'indianapolis', 'san francisco', 'seattle', 'denver', 'washington dc',
          'boston', 'nashville', 'el paso', 'detroit', 'oklahoma city',
          'portland', 'las vegas', 'memphis', 'louisville', 'baltimore',
          'milwaukee', 'albuquerque', 'tucson', 'fresno', 'sacramento',
          'kansas city', 'atlanta', 'miami', 'raleigh', 'omaha', 'long beach',
          'virginia beach', 'oakland', 'minneapolis', 'tulsa', 'tampa',
          'new orleans', 'wichita', 'cleveland', 'honolulu', 'asheville',
          'savannah', 'charleston', 'orlando', 'salt lake', 'knoxville',
          'chattanooga', 'madison', 'boise', 'pittsburgh', 'myrtle beach',
          'brooklyn', 'queens', 'bronx', 'manhattan', 'st. louis', 'st louis',
          'st. paul', 'st paul', 'ft. lauderdale', 'ft lauderdale', 'fort lauderdale',
          'des moines', 'grand rapids', 'ann arbor', 'birmingham', 'jackson',
          'reno', 'spokane', 'tacoma', 'anchorage', 'lubbock',
          # state codes require comma before to avoid matching "near me" or similar
          ', tx', ', ca', ', fl', ', ny', ', ga', ', nc', ', sc', ', va',
          ', pa', ', mi', ', oh', ', il', ', in', ', tn', ', ky', ', mo',
          ', ks', ', ar', ', la', ', ms', ', al', ', az', ', nv', ', ut',
          ', co', ', nm', ', or', ', wa', ', id', ', mt', ', wy', ', nd',
          ', sd', ', ne', ', ia', ', mn', ', wi', ', me', ', vt', ', nh',
          ', ma', ', ri', ', ct', ', nj', ', de', ', md', ', dc', ', hi',
          ', ak', ', ok']

# Recipe/cooking intent -> not our niche
RECIPES = ['recipe', 'ideas', 'how to make', 'how to cook', 'homemade',
           'meal prep', 'meal plan', 'menu ideas', 'breakfast for dinner',
           'protein breakfast', 'breakfast smoothie', 'breakfast bar',
           'breakfast bowl', 'breakfast casserole', 'crockpot',
           'oatmeal', 'egg recipe', 'pancake', 'french toast',
           'muffin', 'waffle recipe', 'breakfast burrito recipe',
           'toast recipe', 'bagel recipe', 'skillet recipe', 'quinoa',
           'chia', 'overnight oat', 'granola', 'high protein',
           'low carb breakfast', 'keto breakfast', 'diabetic breakfast',
           'breakfast tacos', 'breakfast burrito', 'breakfast burritos',
           'breakfast sandwich', 'breakfast sandwiches', 'breakfast pizza',
           'breakfast potato', 'breakfast sausage', 'breakfast muffin',
           'breakfast quiche', 'breakfast pastry', 'breakfast fruit',
           'breakfast dish', 'breakfast food', 'breakfast foodstuff',
           'egg muffins', 'sausage links', 'sausage patty', 'sausage patties',
           'frozen breakfast', 'breakfast egg', 'breakfast baconator',
           'protein dish', 'family breakfast recipe', 'kid breakfast recipe']

# Food/beverage terms — not location search
FOODS = ['english breakfast tea', 'english breakfast', 'irish breakfast tea',
         'irish breakfast', 'full english', 'turkish breakfast',
         'italian breakfast', 'chinese breakfast', 'japanese breakfast',
         'korean breakfast', 'balkan breakfast', 'portuguese breakfast',
         'american breakfast', 'french breakfast', 'greek breakfast',
         'jewish breakfast', 'mexican breakfast', 'southern breakfast',
         'continental breakfast', 'breakfast shot', 'breakfast time cereal',
         'breakfast blend', 'breakfast drink', 'breakfast smoothie',
         'breakfast tea', 'breakfast juice', 'breakfast coffee',
         'wedding breakfast']  # British term for post-wedding meal

# Lodging / furniture / non-restaurant
LODGING_FURNITURE = ['bed and breakfast', 'bed & breakfast', 'bed breakfast',
                     'b&b', 'breakfast nook', 'breakfast table',
                     'breakfast in bed', 'breakfast bar stool',
                     'breakfast bar chair', 'inn breakfast', 'hotel breakfast']

# Product/grocery — not our niche
PRODUCTS = ['cereal', 'jimmy dean', 'kelloggs', "kellogg's", 'general mills',
            'quaker', 'nature valley', 'clif bar', 'special k', 'lucky charm',
            'cheerios', 'frosted flake', 'cocoa puff', 'cornflake',
            'breakfast bar', 'protein bar', 'granola bar', 'nutrigrain',
            'coco puff']

# Unrelated (movie, book, song, celeb, event, image search)
UNRELATED = ['breakfast club', 'breakfast at tiffany', 'kellogg breakfast plate',
             'pretty in pink', 'brat pack', 'anthony michael hall',
             'molly ringwald', 'judd nelson', 'ally sheedy', 'song lyric',
             'movie', 'film', 'soundtrack', 'billy joel', 'audrey hepburn',
             'lyrics', 'chords', 'sheet music', 'meaning of', 'quote',
             'monologue', 'script', 'poem', 'book', 'novel', 'the breakfast',
             'filetype:', 'breakfast photo', 'breakfast sketch',
             'breakfast image', 'breakfast wallpaper', 'breakfast png',
             'breakfast gif', 'breakfast clipart', 'breakfast drawing',
             'breakfast animation', 'breakfast cartoon']

# Independent brand names extra (chains not in our primary list but should route)
INDIE_BRANDS = ['big bad breakfast', 'huckleberry', "salt's cure", 'salts cure',
                'breakfast republic', 'breakfast station', "portillo's",
                'portillos', 'the breakfast klub', 'breakfast klub', 'ihop menu',
                'first watch menu', 'einstein bagels', 'jamba juice']

# Recipe-style intent words to demote
DEMOTE = ['recipe', 'cook', 'make', 'baking', 'boil', 'fry', 'bake']

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
                # keep highest-volume entry across duplicates
                if k not in seen or seen[k]['vol'] < vol:
                    seen[k] = {'kw': k, 'vol': vol, 'kd': kd, 'cpc': cpc, 'intent': intent}
    return list(seen.values())

def classify(k):
    kw = ' ' + k + ' '  # pad so ' tx ' matches
    # Reject in strict order
    for u in UNRELATED:
        if u in kw: return 'unrelated'
    for l in LODGING_FURNITURE:
        if l in kw: return 'lodging'
    for r in RECIPES:
        if r in kw: return 'recipe'
    for f in FOODS:
        if f in kw: return 'food-cuisine'
    for p in PRODUCTS:
        if p in kw: return 'product'
    for b in BRANDS:
        if b in kw: return 'brand'
    for ib in INDIE_BRANDS:
        if ib in kw: return 'indie-brand'
    # City = route to per-city pages
    for c in CITIES:
        if c in kw: return 'city'
    # STRICT homepage semantic gate — must be about finding a place
    finder_signals = ['near me', ' places', ' restaurants', ' spots',
                      ' place ', ' restaurant ', ' spot ', 'near you',
                      'closest', 'nearest', 'nearby', 'best breakfast',
                      'good breakfast', 'top breakfast', 'popular breakfast',
                      'open now', 'places to eat', 'where to eat',
                      'where to get', 'find breakfast', 'fast food breakfast',
                      'breakfast open', 'breakfast near']
    is_finder = any(s in kw for s in finder_signals) or k == 'breakfast'
    # Exclusions even if finder-like
    if 'shop' in k and 'coffee shop' not in k: is_finder = False
    if 'restaurants tag' in k or 'in the world' in k: is_finder = False
    if not is_finder and k not in ['breakfast', 'breakfast places', 'breakfast restaurants',
                                    'breakfast spots', 'breakfast places open', 'breakfast time',
                                    'breakfast now', 'breakfast open']:
        # Not a location-finder query → check content buckets
        pass
    # Category modifiers -> category pages
    if 'buffet' in k: return 'cat-buffet'
    if '24 hour' in k or '24-hour' in k or 'open 24' in k or 'all night' in k or 'late night breakfast' in k: return 'cat-24hr'
    if 'all day breakfast' in k or 'all-day breakfast' in k: return 'cat-allday'
    if 'brunch' in k: return 'cat-brunch'
    if 'cheap' in k or 'cheapest' in k or 'affordable' in k or 'under $' in k or 'under 5' in k or 'under 10' in k or 'dollar breakfast' in k: return 'cat-cheap'
    if 'healthy' in k or 'diet ' in k or 'clean eating' in k: return 'cat-healthy'
    if 'vegan' in k: return 'cat-vegan'
    if 'gluten' in k or 'gluten-free' in k: return 'cat-gf'
    if 'halal' in k: return 'cat-halal'
    if 'kid ' in k or 'kids ' in k or 'family friendly' in k or 'family-friendly' in k or 'kid friendly' in k or 'kid-friendly' in k: return 'cat-kids'
    if 'drive thru' in k or 'drive-thru' in k or 'drive through' in k: return 'cat-drive'
    if 'delivery' in k: return 'cat-delivery'
    if 'catering' in k or 'caterer' in k: return 'cat-catering'
    if 'takeout' in k or 'take out' in k or 'take-out' in k or 'to go' in k: return 'cat-takeout'
    if 'buffet' in k: return 'cat-buffet'
    if 'mexican breakfast' in k or 'huevos' in k or 'chilaquiles' in k: return 'cat-mexican'
    if 'southern breakfast' in k or 'grits' in k or 'biscuits and gravy' in k: return 'cat-southern'
    if 'jewish' in k or 'bagel' in k or 'lox' in k or 'kosher breakfast' in k: return 'cat-jewish'
    if 'french' in k or 'crepe' in k or 'croissant' in k: return 'cat-french'
    if 'mediterranean breakfast' in k or 'shakshuka' in k: return 'cat-mediterranean'
    if 'buffet' in k: return 'cat-buffet'
    # Finder / homepage keywords (strict — must contain finder signals)
    if is_finder:
        if 'best breakfast' in k or 'good breakfast' in k or 'top breakfast' in k or 'popular breakfast' in k:
            return 'homepage-primary'
        if 'places near me' in k or 'restaurants near me' in k or 'spots near me' in k or 'near me now' in k or 'open near me' in k or 'places to eat' in k:
            return 'homepage-primary'
        if k in ['breakfast near me', 'breakfast places', 'breakfast restaurants',
                 'breakfast spots', 'breakfast place', 'breakfast restaurant',
                 'breakfast spot', 'places to eat breakfast', 'breakfast']:
            return 'homepage-primary'
        return 'homepage-secondary'
    # Question-style content pages
    if k.startswith('what time') or 'what time does' in k: return 'q-hours'
    if k.startswith('when does') or 'when do' in k: return 'q-hours'
    if 'breakfast hours' in k: return 'q-hours'
    if 'time for breakfast' in k or 'time is breakfast' in k: return 'q-hours'
    if 'why is breakfast' in k or 'what is breakfast' in k or 'meaning of breakfast' in k: return 'q-content'
    if 'breakfast menu' in k or 'breakfast prices' in k: return 'q-content'
    if 'best time to eat' in k or 'when to eat' in k or 'benefits of breakfast' in k or 'skip breakfast' in k: return 'q-content'
    # Time-based
    if 'sunday' in k or 'saturday' in k or 'weekend' in k or 'weekday' in k: return 'q-hours'
    if 'early morning' in k or 'morning' in k: return 'homepage-secondary' if is_finder else 'other'
    # Default: not homepage material
    return 'other'

def priority(row):
    """0-100 score. Weights volume heavily, penalizes KD, boosts commercial intent."""
    vol = row['vol']
    kd = row['kd']
    score = (vol ** 0.5) * (100 - kd)
    if 'T' in row['intent'] or 'C' in row['intent']:  # Transactional/Commercial
        score *= 1.3
    return score

def priority_label(score, max_score):
    p = score / max_score * 100 if max_score else 0
    if p >= 60: return 'P0 · Ship first'
    if p >= 30: return 'P1 · Ship soon'
    if p >= 10: return 'P2 · Ship after top pages'
    return 'P3 · Later / long tail'

def main():
    all_kws = load_all()
    print(f'Loaded {len(all_kws)} unique keywords across 3 CSVs')
    for r in all_kws: r['bucket'] = classify(r['kw'])
    buckets = defaultdict(list)
    for r in all_kws: buckets[r['bucket']].append(r)
    total_by_bucket = {b: sum(x['vol'] for x in v) for b,v in buckets.items()}
    print('\nBucket distribution:')
    for b, v in sorted(buckets.items(), key=lambda x: -total_by_bucket[x[0]]):
        print(f'  {b:25s} {len(v):5d} kws  {total_by_bucket[b]:>12,d} SV')

    # Homepage cluster = homepage-primary + homepage-secondary
    homepage = sorted(buckets['homepage-primary'] + buckets['homepage-secondary'], key=priority, reverse=True)
    # Filter out sub-100 SV to keep list actionable
    homepage_actionable = [r for r in homepage if r['vol'] >= 100]
    homepage_top = homepage_actionable[:60]

    # For all other buckets, keep for separate pages, dedupe by exact keyword
    per_bucket = {}
    for b in ['cat-buffet','cat-24hr','cat-allday','cat-brunch','cat-cheap',
              'cat-healthy','cat-vegan','cat-gf','cat-halal','cat-kids',
              'cat-drive','cat-delivery','cat-catering','cat-takeout',
              'cat-mexican','cat-southern','cat-jewish','cat-french',
              'cat-mediterranean','q-hours','q-content']:
        if b in buckets:
            rows = sorted(buckets[b], key=priority, reverse=True)
            per_bucket[b] = [r for r in rows if r['vol'] >= 50]

    # Compute max priority for labeling
    max_score = priority(homepage_top[0]) if homepage_top else 1

    # Write MD
    out = ROOT / 'docs' / 'SEO_KEYWORDS.md'
    out.parent.mkdir(exist_ok=True)
    lines = []
    lines.append('# BreakfastPlaces.us — Semantic SEO Keyword Plan\n')
    lines.append(f'**Source**: 3 SEMrush Keyword Magic exports (breakfast, breakfast near me, breakfast places), deduplicated to {len(all_kws):,} unique keywords.\n')
    lines.append(f'**Method**: semantic clustering by intent. Every keyword lives in exactly one destination — no cannibalization. Brand + city + recipe + product + movie keywords are routed to their own page types, not the homepage.\n\n')
    lines.append('---\n\n')

    lines.append('## 🏠 HOMEPAGE — semantic cluster to target on `/`\n\n')
    lines.append('One page ranks for all of these because they share the same intent: *"find breakfast places near me now"*. Weave the top-10 keywords into H1, H2s, first paragraph, meta title, meta description. The rest sit naturally inside content, tables, FAQ.\n\n')
    lines.append(f'Total homepage cluster: **{len(homepage_actionable):,} keywords · {sum(r["vol"] for r in homepage_actionable):,} SV**\n\n')
    lines.append('| # | Keyword | SV | KD | CPC | Intent | Priority | Where to use on homepage |\n')
    lines.append('|---|---|---:|---:|---:|---|---|---|\n')
    for i, r in enumerate(homepage_top[:60], 1):
        prio = priority_label(priority(r), max_score)
        placement = 'H1 + meta title' if i<=2 else ('H2 headers + intro' if i<=8 else ('FAQ / table headings' if i<=25 else 'body content, naturally'))
        lines.append(f'| {i} | {r["kw"]} | {r["vol"]:,} | {r["kd"]} | ${r["cpc"]:.2f} | {r["intent"]} | {prio} | {placement} |\n')
    lines.append('\n')

    lines.append('### Recommended homepage META title / description\n\n')
    lines.append('**Title** (max 60 chars):  \n`Breakfast Places Near Me: 82K+ Real US Spots Live`\n\n')
    lines.append('**Meta description** (max 155 chars):  \n`Find breakfast places, restaurants, and spots open near you right now. 32 chains + 130 hand-picked diners with live serving status, hours, prices, directions.`\n\n')
    lines.append('**H1**: `Find the Best Breakfast Places Near You` (already live — keep it)\n\n')
    lines.append('---\n\n')

    lines.append('## 📚 SEPARATE PAGES — no overlap with homepage or each other\n\n')
    lines.append('Each cluster below is one dedicated URL. Semantically distinct from homepage: users searching these want a *filtered* view, not the whole map.\n\n')

    bucket_meta = {
        'cat-24hr': ('/24-hour-breakfast/', '24-Hour Breakfast Places Open All Night'),
        'cat-allday': ('/all-day-breakfast/', 'All-Day Breakfast Restaurants'),
        'cat-cheap': ('/cheap-breakfast/', 'Cheap Breakfast Under $10'),
        'cat-healthy': ('/healthy-breakfast/', 'Healthy Breakfast Places'),
        'cat-vegan': ('/vegan-breakfast/', 'Vegan Breakfast Restaurants'),
        'cat-gf': ('/gluten-free-breakfast/', 'Gluten-Free Breakfast Places'),
        'cat-halal': ('/halal-breakfast/', 'Halal Breakfast Restaurants'),
        'cat-kids': ('/kid-friendly-breakfast/', 'Kid-Friendly Breakfast Places'),
        'cat-drive': ('/drive-thru-breakfast/', 'Drive-Thru Breakfast Near Me'),
        'cat-delivery': ('/breakfast-delivery/', 'Breakfast Delivery Near Me'),
        'cat-catering': ('/breakfast-catering/', 'Breakfast Catering Services'),
        'cat-takeout': ('/breakfast-takeout/', 'Breakfast Takeout Near Me'),
        'cat-buffet': ('/breakfast-buffet/', 'Breakfast Buffet Near Me'),
        'cat-brunch': ('/brunch-near-me/', 'Brunch Restaurants Near Me'),
        'cat-mexican': ('/mexican-breakfast/', 'Mexican Breakfast Places'),
        'cat-southern': ('/southern-breakfast/', 'Southern Breakfast Restaurants'),
        'cat-jewish': ('/jewish-breakfast-bagels/', 'Jewish Breakfast & Bagel Spots'),
        'cat-french': ('/french-breakfast/', 'French Breakfast & Croissant Cafés'),
        'cat-mediterranean': ('/mediterranean-breakfast/', 'Mediterranean Breakfast Spots'),
        'q-hours': ('/breakfast-hours/', 'Breakfast Hours by Chain (Live Cutoffs)'),
        'q-content': ('/what-is-breakfast/', 'What Is Breakfast? Menus, Prices, Meaning'),
    }
    for b, rows in sorted(per_bucket.items(), key=lambda x: -sum(r['vol'] for r in x[1])):
        if not rows: continue
        url, title = bucket_meta.get(b, (f'/{b}/', b.title()))
        total_sv = sum(r['vol'] for r in rows)
        lines.append(f'### `{url}` — {title}\n')
        lines.append(f'{len(rows)} keywords · {total_sv:,} monthly searches combined\n\n')
        lines.append('| Keyword | SV | KD | CPC | Priority |\n|---|---:|---:|---:|---|\n')
        for r in rows[:30]:
            prio = priority_label(priority(r), max_score)
            lines.append(f'| {r["kw"]} | {r["vol"]:,} | {r["kd"]} | ${r["cpc"]:.2f} | {prio} |\n')
        if len(rows) > 30:
            lines.append(f'| _…and {len(rows)-30} long-tail variants (weave into body)_ | | | | |\n')
        lines.append('\n')

    # Excluded summary
    lines.append('---\n\n## 🚫 EXCLUDED — routed to other page types\n\n')
    lines.append('These clusters do NOT belong on the homepage or category pages. Each has its own page-type plan:\n\n')
    lines.append('| Cluster | Count | Total SV | Where to target |\n|---|---:|---:|---|\n')
    excluded = {
        'brand': ('Brand-specific (mcdonalds breakfast, starbucks menu…)', 'Per-brand pages: `/mcdonalds-breakfast-hours/`, `/starbucks-breakfast-menu/`, etc. (32 pages)'),
        'indie-brand': ('Independent chain names (Big Bad Breakfast, Breakfast Republic…)', 'Optional per-brand pages if we onboard those brands to our data'),
        'city': ('City-specific (breakfast in dallas, atlanta breakfast…)', 'Per-city pages: `/breakfast-in-dallas-tx/`, `/breakfast-in-atlanta-ga/`, etc. (100+ pages)'),
        'recipe': ('Recipe intent (breakfast recipes, meal prep, breakfast burrito recipe…)', 'NOT OUR NICHE — skip; not competing with Allrecipes/BBCGoodFood'),
        'food-cuisine': ('Cuisine/food-item terms (english breakfast tea, breakfast pizza, italian breakfast…)', 'NOT OUR NICHE — food/beverage articles, not location finder'),
        'lodging': ('Lodging & furniture (bed and breakfast, breakfast nook…)', 'NOT OUR NICHE — B&B lodging + furniture, entirely different market'),
        'product': ('Grocery products (cereal brands, jimmy dean…)', 'NOT OUR NICHE — skip'),
        'unrelated': ('Movie / book / song / image search (Breakfast Club film, breakfast clipart…)', 'Skip'),
        'other': ('Long-tail with no clear intent match', 'Skip or use for content ideation later'),
    }
    for b, (label, where) in excluded.items():
        if b in buckets:
            c = len(buckets[b])
            sv = total_by_bucket[b]
            lines.append(f'| {label} | {c:,} | {sv:,} | {where} |\n')
    lines.append('\n')

    # Grand totals
    kept_sv = sum(r['vol'] for r in homepage_actionable)
    for b, rows in per_bucket.items():
        kept_sv += sum(r['vol'] for r in rows)
    lines.append(f'---\n\n## 📊 GRAND TOTALS\n\n')
    lines.append(f'- Homepage target: **{sum(r["vol"] for r in homepage_actionable):,} SV**\n')
    lines.append(f'- Category pages combined: **{sum(sum(r["vol"] for r in rows) for rows in per_bucket.values()):,} SV**\n')
    lines.append(f'- **Total SV your site can realistically capture across all page types**: {kept_sv:,}\n')
    lines.append(f'- Brand + city page SV (separate plan): **{total_by_bucket.get("brand",0) + total_by_bucket.get("city",0):,} SV**\n')
    lines.append(f'- Grand total addressable market (before recipes/products): **{kept_sv + total_by_bucket.get("brand",0) + total_by_bucket.get("city",0):,} SV/month**\n')

    out.write_text(''.join(lines))
    print(f'\nWrote {out} ({out.stat().st_size//1024} KB)')

if __name__ == '__main__':
    main()
