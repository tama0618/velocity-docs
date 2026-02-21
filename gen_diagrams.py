from PIL import Image, ImageDraw, ImageFont
import math, os

out = "C:/Users/Tama/Downloads/racing-site/img"
font_path = "C:/Windows/Fonts/meiryo.ttc"
font = ImageFont.truetype(font_path, 18, index=0)
font_sm = ImageFont.truetype(font_path, 14, index=0)
font_lg = ImageFont.truetype(font_path, 22, index=1)

BG = (24, 28, 38, 255)
GRID = (50, 55, 70, 255)
RED = (230, 80, 80)
BLUE = (80, 160, 255)
GREEN = (80, 220, 180)
GOLD = (255, 200, 60)
WHITE = (230, 230, 240)
GRAY = (140, 140, 160)

def make_graph(w, h, title, xlabel, ylabel, curves, xlabels=None, ylabels=None, fname="graph.png"):
    img = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(img)

    mx, my = 70, 40  # margins
    mr, mb = 30, 50
    gw, gh = w - mx - mr, h - my - mb

    # Title
    d.text((w//2, 12), title, fill=WHITE, font=font_lg, anchor="mt")

    # Axes
    d.line([(mx, my), (mx, my+gh), (mx+gw, my+gh)], fill=GRID, width=2)

    # Grid
    for i in range(1, 5):
        y = my + gh - int(gh * i / 4)
        d.line([(mx, y), (mx+gw, y)], fill=(40, 44, 55, 255), width=1)
    for i in range(1, 6):
        x = mx + int(gw * i / 5)
        d.line([(x, my), (x, my+gh)], fill=(40, 44, 55, 255), width=1)

    # Labels
    d.text((w//2, h-8), xlabel, fill=GRAY, font=font_sm, anchor="mb")
    # Y label rotated would need special handling, just put at top-left
    for li, line in enumerate(ylabel.split("\n")):
        d.text((8, my + li * 18), line, fill=GRAY, font=font_sm)

    # X labels
    if xlabels:
        for i, lbl in enumerate(xlabels):
            x = mx + int(gw * i / (len(xlabels)-1))
            d.text((x, my+gh+6), lbl, fill=GRAY, font=font_sm, anchor="mt")

    # Y labels
    if ylabels:
        for i, lbl in enumerate(ylabels):
            y = my + gh - int(gh * i / (len(ylabels)-1))
            d.text((mx-8, y), lbl, fill=GRAY, font=font_sm, anchor="rm")

    # Curves
    for pts, color, label in curves:
        coords = []
        for px, py in pts:
            x = mx + int(gw * px)
            y = my + gh - int(gh * py)
            coords.append((x, y))
        if len(coords) > 1:
            d.line(coords, fill=color, width=3)
        # Label at end
        if label and len(coords) > 0:
            lx, ly = coords[-1]
            d.text((lx+5, ly-10), label, fill=color, font=font_sm)

    img.save(os.path.join(out, fname), "PNG")
    print(f"Saved {fname}")

# 1. Torque Curve
torque_pts = [(0.0, 0.3), (0.35, 0.8), (0.55, 1.0), (0.8, 0.95), (1.0, 0.7)]
# Interpolate smoothly
def interp_curve(pts, n=50):
    result = []
    for i in range(n+1):
        t = i / n
        # find segment
        for j in range(len(pts)-1):
            if pts[j][0] <= t <= pts[j+1][0]:
                f = (t - pts[j][0]) / (pts[j+1][0] - pts[j][0])
                v = pts[j][1] + (pts[j+1][1] - pts[j][1]) * f
                result.append((t, v))
                break
    return result

make_graph(560, 340, "Engine Torque Curve", "RPM", "Torque\nMultiplier",
    [(interp_curve(torque_pts), RED, "Torque")],
    xlabels=["0", "1400", "2800", "4200", "5600", "7000"],
    ylabels=["0", "25%", "50%", "75%", "100%"],
    fname="torque_curve.png")

# 2. Friction Curve (Forward + Sideways)
def friction_curve(exSlip, exVal, asSlip, asVal, n=50):
    pts = []
    for i in range(n+1):
        slip = i / n  # 0 to 1 mapped to 0 to 0.8 actual
        actual_slip = slip * 0.8
        if actual_slip <= exSlip:
            f = actual_slip / exSlip
            val = f * exVal
        elif actual_slip <= asSlip:
            f = (actual_slip - exSlip) / (asSlip - exSlip)
            val = exVal + (asVal - exVal) * f
        else:
            val = asVal
        pts.append((slip, val / 2.0))  # normalize to 0-2 range displayed as 0-1
    return pts

fwd_curve = friction_curve(0.14, 1.35, 0.35, 1.15)
side_curve = friction_curve(0.28, 1.85, 0.65, 1.55)

make_graph(560, 340, "Tire Friction Curves (AI)", "Slip Ratio", "Force",
    [(fwd_curve, BLUE, "Forward"), (side_curve, RED, "Sideways")],
    xlabels=["0", "0.16", "0.32", "0.48", "0.64", "0.80"],
    ylabels=["0", "0.5", "1.0", "1.5", "2.0"],
    fname="friction_curves.png")

# 3. Player friction curves
pfwd = friction_curve(0.14, 1.15, 0.35, 0.95)
pside = friction_curve(0.22, 1.45, 0.55, 1.3)

make_graph(560, 340, "Tire Friction Curves (Player)", "Slip Ratio", "Force",
    [(pfwd, BLUE, "Forward"), (pside, RED, "Sideways")],
    xlabels=["0", "0.16", "0.32", "0.48", "0.64", "0.80"],
    ylabels=["0", "0.5", "1.0", "1.5", "2.0"],
    fname="friction_curves_player.png")

# 4. Gear Speed Diagram
gear_limits = [0, 65, 100, 135, 176, 230]
gear_torques = [0, 4200, 2800, 2100, 1600, 1300]
img4 = Image.new("RGBA", (560, 280), BG)
d4 = ImageDraw.Draw(img4)
d4.text((280, 12), "Gear Speed Ranges & Torque", fill=WHITE, font=font_lg, anchor="mt")

bar_colors = [(230,80,80), (230,160,60), (200,200,60), (80,200,120), (80,160,255)]
mx, my = 70, 50
gw, gh = 460, 180

for i in range(1, 6):
    x1 = mx + int(gw * gear_limits[i-1] / 230)
    x2 = mx + int(gw * gear_limits[i] / 230)
    y = my + (i-1) * 34
    h = 28
    d4.rounded_rectangle([(x1, y), (x2, y+h)], radius=4, fill=bar_colors[i-1]+(180,))
    d4.text((x1+6, y+4), f"Gear {i}: {gear_torques[i]}Nm", fill=(20,20,30), font=font_sm)
    d4.text((x2+4, y+6), f"{gear_limits[i]}km/h", fill=GRAY, font=font_sm)

# X axis
d4.line([(mx, my+175), (mx+gw, my+175)], fill=GRID, width=1)
for spd in [0, 50, 100, 150, 200, 230]:
    x = mx + int(gw * spd / 230)
    d4.text((x, my+178), str(spd), fill=GRAY, font=font_sm, anchor="mt")

img4.save(os.path.join(out, "gear_diagram.png"), "PNG")
print("Saved gear_diagram.png")

# 5. Steering hybrid diagram
img5 = Image.new("RGBA", (560, 300), BG)
d5 = ImageDraw.Draw(img5)
d5.text((280, 12), "Hybrid Steering Smoothing", fill=WHITE, font=font_lg, anchor="mt")

mx, my = 60, 50
gw, gh = 460, 200

# Axes
d5.line([(mx, my), (mx, my+gh), (mx+gw, my+gh)], fill=GRID, width=2)
d5.text((mx+gw//2, my+gh+25), "Time (frames)", fill=GRAY, font=font_sm, anchor="mt")
d5.text((8, my+10), "Steering", fill=GRAY, font=font_sm)

# Target line
target_y = my + 30
d5.line([(mx, target_y), (mx+gw, target_y)], fill=GOLD+(100,), width=1)
d5.text((mx+gw+3, target_y-8), "Target", fill=GOLD, font=font_sm)

# Lerp curve (exponential approach)
start = my + gh - 20
lerp_pts = []
moved_pts = []
hybrid_pts = []
for i in range(50):
    t = i / 49
    x = mx + int(gw * t)
    # Lerp: exponential decay
    lerp_val = start + (target_y - start) * (1 - math.exp(-t * 4))
    lerp_pts.append((x, int(lerp_val)))
    # MoveTowards: linear approach
    moved_val = max(target_y, start - (start - target_y) * t * 1.8)
    moved_pts.append((x, int(moved_val)))
    # Hybrid: pick closer to target
    lv = abs(target_y - lerp_val)
    mv = abs(target_y - moved_val)
    hybrid_pts.append((x, int(lerp_val if lv < mv else moved_val)))

d5.line(lerp_pts, fill=BLUE+(120,), width=2)
d5.line(moved_pts, fill=GREEN+(120,), width=2)
d5.line(hybrid_pts, fill=RED, width=3)

d5.text((mx+gw-80, my+gh-60), "Lerp", fill=BLUE, font=font_sm)
d5.text((mx+gw-80, my+gh-40), "MoveTowards", fill=GREEN, font=font_sm)
d5.text((mx+gw-80, my+gh-20), "Hybrid (used)", fill=RED, font=font_sm)

img5.save(os.path.join(out, "steering_hybrid.png"), "PNG")
print("Saved steering_hybrid.png")

# 6. Look-ahead visualization
img6 = Image.new("RGBA", (560, 300), BG)
d6 = ImageDraw.Draw(img6)
d6.text((280, 12), "Dynamic Look-Ahead System", fill=WHITE, font=font_lg, anchor="mt")

# Speed vs look-ahead time
mx, my = 70, 50
gw, gh = 440, 200
d6.line([(mx, my), (mx, my+gh), (mx+gw, my+gh)], fill=GRID, width=2)

# Base line
pts_base = []
for i in range(50):
    t = i / 49
    x = mx + int(gw * t)
    spd = t  # 0-180km/h
    la = 0.3 + (0.4 - 0.3) * min(spd / 1.0, 1.0)
    y = my + gh - int(gh * la / 0.5)
    pts_base.append((x, y))
d6.line(pts_base, fill=BLUE, width=3)

# With curve reduction
pts_curve = []
for i in range(50):
    t = i / 49
    x = mx + int(gw * t)
    spd = t
    la = 0.3 + 0.1 * min(spd, 1.0)
    la *= 0.5  # 50% reduction for 60deg curve
    y = my + gh - int(gh * la / 0.5)
    pts_curve.append((x, y))
d6.line(pts_curve, fill=RED, width=2)

# Off-track
pts_off = []
for i in range(50):
    t = i / 49
    x = mx + int(gw * t)
    la = (0.3 + 0.1 * min(t, 1.0)) * 0.4
    y = my + gh - int(gh * la / 0.5)
    pts_off.append((x, y))
d6.line(pts_off, fill=GREEN, width=2)

d6.text((mx+gw-120, my+10), "Normal", fill=BLUE, font=font_sm)
d6.text((mx+gw-120, my+28), "Sharp Curve", fill=RED, font=font_sm)
d6.text((mx+gw-120, my+46), "Off-Track", fill=GREEN, font=font_sm)

d6.text((mx+gw//2, my+gh+8), "Speed (km/h)", fill=GRAY, font=font_sm, anchor="mt")
d6.text((8, my+10), "Look-\nahead(s)", fill=GRAY, font=font_sm)
for i, lbl in enumerate(["0", "45", "90", "135", "180"]):
    x = mx + int(gw * i / 4)
    d6.text((x, my+gh+4), lbl, fill=GRAY, font=font_sm, anchor="mt")

img6.save(os.path.join(out, "lookahead_diagram.png"), "PNG")
print("Saved lookahead_diagram.png")

# 7. Rank boost diagram
img7 = Image.new("RGBA", (560, 280), BG)
d7 = ImageDraw.Draw(img7)
d7.text((280, 12), "Rank-Based Rubber Band Boost", fill=WHITE, font=font_lg, anchor="mt")

mx, my = 70, 50
gw, gh = 440, 180
d7.line([(mx, my), (mx, my+gh), (mx+gw, my+gh)], fill=GRID, width=2)

for i in range(1, 4):
    y = my + gh - int(gh * i / 3)
    d7.line([(mx, y), (mx+gw, y)], fill=(40, 44, 55), width=1)

# Torque line
pts_t = [(mx + int(gw*i/16), my+gh - int(gh * (1.0 + 0.35*i/16 - 1.0) / 0.4)) for i in range(17)]
d7.line(pts_t, fill=RED, width=3)
# Grip line
pts_g = [(mx + int(gw*i/16), my+gh - int(gh * (1.0 + 0.20*i/16 - 1.0) / 0.4)) for i in range(17)]
d7.line(pts_g, fill=BLUE, width=3)
# Speed line
pts_s = [(mx + int(gw*i/16), my+gh - int(gh * (1.0 + 0.15*i/16 - 1.0) / 0.4)) for i in range(17)]
d7.line(pts_s, fill=GREEN, width=3)

d7.text((mx+gw-100, my+5), "Torque x1.35", fill=RED, font=font_sm)
d7.text((mx+gw-100, my+23), "Grip x1.20", fill=BLUE, font=font_sm)
d7.text((mx+gw-100, my+41), "Speed x1.15", fill=GREEN, font=font_sm)

d7.text((mx+gw//2, my+gh+8), "Position (1st -> Last)", fill=GRAY, font=font_sm, anchor="mt")
for i, lbl in enumerate(["x1.0", "x1.1", "x1.2", "x1.35"]):
    y = my + gh - int(gh * i / 3)
    d7.text((mx-8, y), lbl, fill=GRAY, font=font_sm, anchor="rm")

img7.save(os.path.join(out, "rank_boost.png"), "PNG")
print("Saved rank_boost.png")

print("\nAll diagrams generated!")
