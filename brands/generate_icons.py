"""Generate the brand icon set for the Tank Volume Calculator.

Run from the repo root:  python brands/generate_icons.py

Writes:
  brands/custom_integrations/tank_volume/{icon,icon@2x,dark_icon,dark_icon@2x}.png
      -> the exact files/layout to copy into a home-assistant/brands PR
  custom_components/tank_volume/{icon,dark_icon,logo}.png
      -> the repo's own source assets, kept in sync

Home Assistant and HACS render an integration's tile icon from the
home-assistant/brands repository (by domain), not from this repo, so the brands
submission is what actually removes the "icon not available" placeholder. See
brands/README.md.
"""

from __future__ import annotations

import pathlib

from PIL import Image, ImageChops, ImageDraw

SS = 4  # supersample for antialiasing
ROOT = pathlib.Path(__file__).resolve().parents[1]


def make_icon(px, *, body, liquid, outline, accent, fill_frac=0.52):
    """Render a horizontal-tank icon at ``px`` square with the given colours."""
    s = px * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    margin_x = int(s * 0.10)
    left, right = margin_x, s - margin_x
    height = int(s * 0.42)
    top = int(s * 0.30)
    bottom = top + height
    radius = height // 2
    box = [left, top, right, bottom]
    ow = max(1, int(s * 0.028))

    # Valve/gauge nub on top-center.
    vw, vh = int(s * 0.05), int(s * 0.05)
    vx = (left + right) // 2
    d.rounded_rectangle([vx - vw, top - vh, vx + vw, top + int(vh * 0.4)], radius=int(vw * 0.4), fill=accent)

    # Saddle legs.
    leg_top, leg_bottom = bottom - int(height * 0.10), bottom + int(s * 0.10)
    for cx in (left + int((right - left) * 0.28), left + int((right - left) * 0.72)):
        lw = int(s * 0.05)
        d.polygon(
            [
                (cx - lw, leg_top),
                (cx + lw, leg_top),
                (cx + int(lw * 1.7), leg_bottom),
                (cx - int(lw * 1.7), leg_bottom),
            ],
            fill=accent,
        )

    # Empty body fills the capsule.
    d.rounded_rectangle(box, radius=radius, fill=body)

    # Liquid = amber capsule kept only below the fill line (flat top, curved bottom).
    amber = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(amber).rounded_rectangle(box, radius=radius, fill=liquid)
    fill_line = int(bottom - height * fill_frac)
    below = Image.new("L", (s, s), 0)
    ImageDraw.Draw(below).rectangle([0, fill_line, s, s], fill=255)
    img.paste(liquid, mask=ImageChops.multiply(amber.split()[3], below))

    d.line(
        [left + int(radius * 0.5), fill_line, right - int(radius * 0.5), fill_line],
        fill=(255, 255, 255, 90),
        width=max(1, ow // 2),
    )
    d.rounded_rectangle(box, radius=radius, outline=outline, width=ow)
    return img.resize((px, px), Image.LANCZOS)


LIGHT = {
    "body": (233, 240, 245, 255),
    "liquid": (245, 166, 35, 255),
    "outline": (44, 62, 80, 255),
    "accent": (44, 62, 80, 255),
}
DARK = {
    "body": (210, 221, 231, 255),
    "liquid": (245, 166, 35, 255),
    "outline": (236, 240, 244, 255),
    "accent": (214, 223, 231, 255),
}


def main() -> None:
    """Generate and write all brand icon variants."""
    brands = ROOT / "brands" / "custom_integrations" / "tank_volume"
    integ = ROOT / "custom_components" / "tank_volume"
    brands.mkdir(parents=True, exist_ok=True)

    make_icon(256, **LIGHT).save(brands / "icon.png")
    make_icon(512, **LIGHT).save(brands / "icon@2x.png")
    make_icon(256, **DARK).save(brands / "dark_icon.png")
    make_icon(512, **DARK).save(brands / "dark_icon@2x.png")

    # Keep the repo's own assets in sync (icon at 256; logo reuses the icon mark).
    make_icon(256, **LIGHT).save(integ / "icon.png")
    make_icon(256, **DARK).save(integ / "dark_icon.png")
    make_icon(256, **LIGHT).save(integ / "logo.png")
    print("wrote brand icons to brands/custom_integrations/tank_volume/ and custom_components/tank_volume/")


if __name__ == "__main__":
    main()
