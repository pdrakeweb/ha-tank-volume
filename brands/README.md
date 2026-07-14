# Brand icons

Home Assistant and HACS render an integration's tile icon from the
[`home-assistant/brands`](https://github.com/home-assistant/brands) repository, keyed by
the integration **domain** (`tank_volume`) — **not** from this repo or the release zip.
Until the domain exists in `brands`, the UI shows the "icon not available" placeholder.

This is served by domain from a CDN, so once the brands PR is merged the icon appears for
**every** installed version immediately — you do **not** need to cut a new release for it.

## What's here

`generate_icons.py` produces the icon set (run `python brands/generate_icons.py` from the
repo root). The ready-to-submit files are in:

```
brands/custom_integrations/tank_volume/
├── icon.png        (256x256)
├── icon@2x.png     (512x512)
├── dark_icon.png   (256x256)
└── dark_icon@2x.png(512x512)
```

The same icon is mirrored into `custom_components/tank_volume/{icon,dark_icon,logo}.png`
so the repo's own assets stay in sync.

## Submitting to home-assistant/brands

1. Fork <https://github.com/home-assistant/brands> and clone your fork.
2. Copy this folder into the fork:
   `cp -r brands/custom_integrations/tank_volume <brands>/custom_integrations/tank_volume`
3. From the brands repo, optimize + validate:
   `python3 -m script.optimize` then `python3 -m script.hassfest` (see the brands README).
4. Commit and open a PR titled something like `Add Tank Volume Calculator (tank_volume)`.
   Custom integrations live under `custom_integrations/`, so no core review is needed —
   these PRs are typically merged quickly.
5. After it merges, refresh HACS (⋮ → Update information) or restart Home Assistant; the
   tile icon replaces the placeholder.

Requirements met by these files: square PNGs, transparent background, 256/512 px, with
dark-mode variants for HA's dark theme.
