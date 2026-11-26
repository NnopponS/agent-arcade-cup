# Preview and test the public site

The live site is published from `site/season2/`. GitHub Pages stages `decision-lab-expanded.html` as the home page and `cup100.html` as the replay viewer. `site/index.html` belongs to an earlier study and is not the live home page.

## Preview the GitHub Pages build

From the repository root, run:

```sh
preview="$(mktemp -d)"
bash site/season2/stage-pages.sh "$preview/agent-arcade-cup"
python3 -m http.server 8000 --directory "$preview"
```

Open [the local home page](http://localhost:8000/agent-arcade-cup/) or [the local final replay](http://localhost:8000/agent-arcade-cup/cup100.html?match=R7-01#cup-replay). Use Python 3.10 or later. You do not need FightingICE or model weights to preview the site.

## Verify browser behavior

With Playwright and Chromium installed, run:

```sh
python3 -m pip install playwright
python3 -m playwright install chromium
python3 site/season2/test-cup100-browser.py
```

The test stages the same files as GitHub Pages and serves them under the project subpath. It checks replay search, playback, copy, direct links, retry, and mobile layout. Set `CHROME_PATH` to use an existing Chromium binary.

Keep the published data and replay JSON separate from viewer changes. The historical `kev-bench/cup100_public.py` generator can emit a separate snapshot, but its HTML template is not the maintained public viewer.
