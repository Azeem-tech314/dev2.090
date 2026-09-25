# breakfastplaces.us

Static breakfast-directory site with an interactive map of 82,611 verified
US chain locations across 32 breakfast-serving brands, plus 130 hand-picked
independent diners.

## Files

- `index.html` — the whole page (hero, map tool, tables, cities, FAQ, modals)
- `data/compact/index.json` — brand list + counts + policy metadata
- `data/compact/<Brand>.json` — one file per brand with `{m:meta, r:[[lat,lng,addr,city,st,zip,phone,hours,web,flags],…]}`
- `data/compact/indies.json` — 130 curated indie spots
- `data/brands/*.geojson` — raw OSM source data
- `tools/build_compact.py` — rebuild `data/compact/` from `data/brands/`
- `robots.txt` — blocks all crawlers (remove when ready to launch)
- `vercel.json` — sets `X-Robots-Tag: noindex` header + CORS on JSON

## Rebuild data

```bash
python3 tools/build_compact.py
```

## Keep the Vercel deploy PRIVATE (three ways, all free)

### Method 1 — Robots block (already set up)
`robots.txt` and the `X-Robots-Tag` header in `vercel.json` tell Google/Bing
not to index. Anyone with the URL can still visit, but it won't show in
search results. **Best for build-phase testing.**

### Method 2 — Password-protect via Vercel dashboard (free on Pro; requires paid on Hobby)
1. Vercel dashboard → your project → Settings → Deployment Protection
2. Enable **Vercel Authentication** (only your Vercel account can visit) or
   **Password Protection** (share one password with anyone). Hobby tier
   restricts this to preview deploys only; production stays public.

### Method 3 — Manual private preview (100% free on Hobby)
1. Vercel dashboard → your project → Settings → Git
2. Change **Production Branch** from `main` to something no one will guess,
   e.g. `internal-preview`
3. Push your work to `internal-preview` — Vercel gives it a URL like
   `breakfast-locations-website-git-internal-preview-<user>.vercel.app`
4. Preview deployments on Vercel Hobby are automatically hidden from
   search engines (Vercel sets `X-Robots-Tag: noindex` on all preview URLs)
5. **Don't** attach a custom domain until you're ready to launch — as long
   as it stays on the `*.vercel.app` preview URL with `noindex`, it stays
   invisible to search
6. When ready to launch, either:
   - Rename `internal-preview` to `main` on GitHub, OR
   - In Vercel Settings → Git, switch Production Branch back to `main`

### Ready to launch (undo privacy)
1. Delete `robots.txt` (or replace with `User-agent: *\nAllow: /`)
2. Edit `vercel.json` — change `noindex, nofollow` header to `index, follow`
3. In `index.html` `<head>`, change `<meta name="robots" content="noindex,…">`
   to `<meta name="robots" content="index,follow,max-image-preview:large">`
4. Add back `<link rel="canonical" href="https://breakfastplaces.us/">` line
5. Submit `https://breakfastplaces.us/sitemap.xml` to Google Search Console

## Deploying to WordPress — THE EASY WAY

**Copy the whole file `wordpress.html` and paste it into an Elementor HTML
widget or a Gutenberg "Custom HTML" block. Done. Nothing else.**

`wordpress.html` is a single self-contained block (no `<doctype>`, `<html>`,
`<head>`, or `<body>` wrappers). It loads the 32-brand JSON data live from
a public CDN (jsDelivr, mirroring this GitHub repo), so no FTP upload, no
`.htaccess` tweaks, no theme edits.

Rebuild `wordpress.html` after changing `index.html`:
```bash
python3 tools/build_wordpress.py
```

If you later merge to `main`, edit `tools/build_wordpress.py` and change
`BRANCH = 'claude/confident-carson-feo8dx'` to `BRANCH = 'main'`.

### Fallback: iframe from Vercel
```html
<iframe src="https://your-vercel-url.vercel.app/" style="width:100%;height:100vh;border:0"></iframe>
```
