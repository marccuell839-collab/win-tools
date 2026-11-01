"""Generate original JARVIS Windows icon and runtime PNG without external assets.

Run from repository root: python tools/make_icon.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)
S = 1024
C = S // 2
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Rounded app tile. Keep fully opaque so Windows pinning looks clean.
d.rounded_rectangle((18, 18, S - 18, S - 18), radius=220, fill=(3, 11, 23, 255))
d.rounded_rectangle((28, 28, S - 28, S - 28), radius=215, outline=(30, 95, 153, 255), width=9)

glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
g = ImageDraw.Draw(glow)
for radius, width in [(358, 28), (294, 26), (220, 27)]:
    g.arc((C-radius,C-radius,C+radius,C+radius), 18, 342,
          fill=(0, 189, 255, 170), width=width)
glow = glow.filter(ImageFilter.GaussianBlur(32))
img = Image.alpha_composite(img, glow)
d = ImageDraw.Draw(img)
d.ellipse((170,170,854,854), outline=(12,58,91,255), width=9)
d.arc((164,164,860,860), 208, 333, fill=(0,200,255,255), width=19)
d.arc((164,164,860,860), 28, 157, fill=(23,121,217,255), width=19)
d.arc((209,209,815,815), 15, 165, fill=(74,221,255,255), width=22)
d.arc((209,209,815,815), 194, 345, fill=(4,125,255,255), width=22)

# Discrete tech panels in the perimeter.
for i in range(12):
    angle = math.radians(i * 30 - 90)
    r1, r2 = 358, 388
    p1 = (round(C+r1*math.cos(angle)),round(C+r1*math.sin(angle)))
    p2 = (round(C+r2*math.cos(angle)),round(C+r2*math.sin(angle)))
    d.line((p1,p2), fill=(30,150,224,255), width=15)

# Central black reactor housing.
d.ellipse((298,298,726,726), fill=(3,15,30,255), outline=(50,143,197,255), width=18)
d.ellipse((329,329,695,695), outline=(0,210,255,255), width=16)

# The original stylised cyan JARVIS reactor: an inverted triangular core.
outer = [(512,378),(668,442),(511,646),(356,442)]
inner = [(512,420),(617,463),(512,589),(407,463)]
d.polygon(outer, fill=(4,94,162,255))
d.line(outer+[outer[0]], fill=(54,223,255,255), width=17, joint="curve")
d.polygon(inner, fill=(2,13,31,255))
d.polygon([(512,425),(573,467),(512,548),(451,467)], fill=(0,171,255,255))
d.polygon([(512,443),(548,467),(512,517),(476,467)], fill=(197,251,255,255))
d.line([(401,470),(512,609),(624,470)], fill=(11,154,255,255), width=16, joint="curve")
# Top light strip.
d.rounded_rectangle((417,378,607,399), radius=11, fill=(117,243,255,255))

# ICO contains multiple Windows-supported resolutions; app also uses PNG.
img.save(OUT / "jarvis.png", "PNG")
img.save(OUT / "jarvis.ico", format="ICO",
         sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("Wrote assets/jarvis.ico and assets/jarvis.png")
