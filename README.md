# Company Watch

Company news and exchange-announcement discovery, adapted from the supplied Portfolio Watch package. This is separate from the existing private Portfolio Watch dashboard. It does not change that dashboard or connect to it automatically.

## What changed

- `watchlist.json` contains company name, symbol, ISIN, sector and provider ticker only, plus general policy queries. The supplied quantities, acquisition information, funds, bullion, crypto balances and ULIP details are not copied.
- No portfolio value, allocation, returns or position sizes are calculated or published. No holdings secret is required.
- NSE announcement links, Google News RSS and SEBI RSS are collected once per daily run. The app labels source failures and preserves prior successful items with their actual successful dates.
- Headlines are not an earnings-call review, verified financial analysis or buy/sell recommendation. It does not manufacture moat scores or company conclusions from news headlines.
- The page is encrypted with authenticated AES-256-GCM, a random 12-byte IV and 16-byte salt, and PBKDF2-SHA256 (600,000 iterations). The password must be at least 16 characters. Browser-compatible encryption, wrong-password rejection and tamper detection are tested.
- GitHub Pages receives only `dist/index.html`, not source, caches, unencrypted HTML or the original holdings file. Workflow deployment uses a Pages artifact, not the whole source branch. Nothing is committed by the updater.

## Privacy boundary

This is a public company watchlist with an optional public-hosting plan behind password encryption. It is **not owner-account access control**. Anyone who knows the password can decrypt it, and an attacker can try passwords offline. A public repository exposes the company list and source, and a public Actions cache contains public company news. Use a long unique password. Never add personal financial information to this project.

Keep the old repository PRIVATE because it already contains holdings files in history. Use a NEW repository for this cleaned code. Do not upload the supplied original ZIP or holdings JSON to a public repository. Existing private Portfolio Watch and its independent monitoring tasks are unaffected.

## Setup — after reviewing the local version

1. Create a new `company-watch` GitHub repository. Public is appropriate only if you accept that the company list and news are public. Do not change the old repository's visibility.
2. Upload this folder's source files, including the hidden `.github/workflows/update.yml`. Upload the contents, not the outer directory. The ZIP deliberately excludes live caches, unencrypted output and personal config.
3. Add repository Actions secret `SITE_PASSWORD` (16+ characters; prefer a long unique passphrase). Do NOT add `PORTFOLIO_JSON`.
4. Settings → Pages → Build and deployment → Source: **GitHub Actions**. Do NOT choose “Deploy from a branch”.
5. Actions → Update company research → Run workflow. Inspect the source statuses in the log. A partially successful job can have unavailable NSE filings; the UI explicitly flags these.
6. The deploy job provides the Pages URL. Test in a private browser window: it must show the password screen, wrong passwords must fail, and the right password must unlock the page.
7. Bookmark that verified URL. The scheduled trigger is 03:30 UTC / 09:00 IST daily, subject to GitHub scheduling delays. It runs while the laptop is closed. It is a snapshot, not a live feed.

If every company source fails, the workflow fails before publishing; the previous deployment remains. If some fail, they show stale/unavailable. No failure gets relabelled as a fresh successful retrieval. No claim is made that every primary filing will be accessible from GitHub runners.

## Local testing

Requires Python 3.9+ and Node 22+. No third-party packages.

```
python3 -m unittest discover -s tests -v
python3 fetch_updates.py
python3 build_site.py
node encrypt.cjs
node tests/crypto.cjs
```

Set `SITE_PASSWORD` privately in your environment before encryption; do not put it in a command saved in the repository. Serve `site.html` to preview the research interface. Serve `dist/` over localhost or HTTPS to test the password screen. The included test uses the browser WebCrypto API rather than relying solely on Node's encryption implementation.

## Future connection to private Portfolio Watch

This package does not yet push to the private Site. A separate authenticated server-side research-only bridge is required and must be tested end to end. Never embed a private Site service credential or GitHub token in browser JavaScript. The original portfolio ledger should remain immutable through that bridge.
