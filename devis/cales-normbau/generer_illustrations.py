"""Illustrations de principe : cale pleine vs cale évidée (rendu z-buffer maison)."""
import math
import sys
import numpy as np
from manifold3d import Manifold, CrossSection, JoinType
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1]
SEG = 96

# --- Géométrie générique (illustration, pas les cotes réelles) ---
L, W, H = 64.0, 28.0, 18.0
R_CORNER = 2.5
HOLE_X = 14.0
HOLE_R = 2.9
WALL, FLOOR, RIB = 2.4, 3.0, 2.0
BOSS_R = 6.0


def rounded_block(l, w, h, r):
    cs = CrossSection.square((l - 2 * r, w - 2 * r), center=True).offset(r, JoinType.Round, circular_segments=SEG)
    return Manifold.extrude(cs, h)


def holes():
    m = None
    for x in (-HOLE_X, HOLE_X):
        c = Manifold.cylinder(H + 2, HOLE_R, circular_segments=SEG).translate((x, 0, -1))
        cs = Manifold.cylinder(1.2, HOLE_R + 1.2, HOLE_R, circular_segments=SEG).translate((x, 0, H - 1.2 + 0.001))
        c = c + cs
        m = c if m is None else m + c
    return m


def cale_pleine():
    return rounded_block(L, W, H, R_CORNER) - holes()


def cale_evidee():
    outer = rounded_block(L, W, H, R_CORNER)
    pocket = rounded_block(L - 2 * WALL, W - 2 * WALL, H, max(R_CORNER - WALL, 0.6)).translate((0, 0, FLOOR))
    body = outer - pocket
    ribs = Manifold.cube((L - 2 * WALL, RIB, H - FLOOR), center=False).translate((-(L - 2 * WALL) / 2, -RIB / 2, FLOOR))
    for x in (-HOLE_X, 0.0, HOLE_X):
        ribs = ribs + Manifold.cube((RIB, W - 2 * WALL, H - FLOOR)).translate((x - RIB / 2, -(W - 2 * WALL) / 2, FLOOR))
    bosses = None
    for x in (-HOLE_X, HOLE_X):
        b = Manifold.cylinder(H - FLOOR, BOSS_R, circular_segments=SEG).translate((x, 0, FLOOR))
        bosses = b if bosses is None else bosses + b
    return (body + ribs + bosses) - holes()


# --- Rendu ---
def render(man, size=(1500, 1000), scale=17.0, az=-38, el=32):
    mesh = man.to_mesh()
    V = np.asarray(mesh.vert_properties)[:, :3].astype(float)
    T = np.asarray(mesh.tri_verts).astype(int)
    a, e = math.radians(az), math.radians(el)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    # vue : x écran, y écran (haut), z profondeur (vers la caméra)
    P = V - V.mean(axis=0)
    P = P @ Rz.T
    # basculer : on regarde depuis le dessus/avant
    P = np.stack([P[:, 0], P[:, 1] * math.sin(e) + P[:, 2] * math.cos(e), -P[:, 1] * math.cos(e) + P[:, 2] * math.sin(e)], axis=1)
    w, h = size
    sx = P[:, 0] * scale + w / 2
    sy = -P[:, 1] * scale + h / 2
    sz = P[:, 2]
    tri3 = P[T]
    n = np.cross(tri3[:, 1] - tri3[:, 0], tri3[:, 2] - tri3[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    light = np.array([-0.35, 0.55, 0.75]); light /= np.linalg.norm(light)
    light2 = np.array([0.6, -0.2, 0.5]); light2 /= np.linalg.norm(light2)
    shade = 0.38 + 0.52 * np.clip(n @ light, 0, 1) + 0.12 * np.clip(n @ light2, 0, 1)

    zbuf = np.full((h, w), -np.inf)
    col = np.zeros((h, w))
    nbuf = np.zeros((h, w, 3))
    mask = np.zeros((h, w), bool)
    for i, (i0, i1, i2) in enumerate(T):
        if n[i, 2] <= 0:
            continue
        x0, x1, x2 = sx[[i0, i1, i2]]
        y0, y1, y2 = sy[[i0, i1, i2]]
        xmin, xmax = int(max(min(x0, x1, x2), 0)), int(min(max(x0, x1, x2) + 1, w - 1))
        ymin, ymax = int(max(min(y0, y1, y2), 0)), int(min(max(y0, y1, y2) + 1, h - 1))
        if xmax < xmin or ymax < ymin:
            continue
        xs, ys = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(d) < 1e-9:
            continue
        b0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / d
        b1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / d
        b2 = 1 - b0 - b1
        inside = (b0 >= -1e-6) & (b1 >= -1e-6) & (b2 >= -1e-6)
        if not inside.any():
            continue
        z = b0 * sz[i0] + b1 * sz[i1] + b2 * sz[i2]
        sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
        upd = inside & (z > sub)
        sub[upd] = z[upd]
        col[ymin:ymax + 1, xmin:xmax + 1][upd] = shade[i]
        nbuf[ymin:ymax + 1, xmin:xmax + 1][upd] = n[i]
        mask[ymin:ymax + 1, xmin:xmax + 1][upd] = True

    # arêtes : discontinuités de normale ou de profondeur
    edge = np.zeros((h, w), bool)
    for dy, dx in ((0, 1), (1, 0)):
        nb = np.roll(nbuf, (-dy, -dx), axis=(0, 1))
        mb = np.roll(mask, (-dy, -dx), axis=(0, 1))
        zb = np.roll(zbuf, (-dy, -dx), axis=(0, 1))
        dot = (nbuf * nb).sum(axis=2)
        e1 = mask & mb & ((dot < 0.93) | (np.abs(np.where(np.isfinite(zbuf - zb), zbuf - zb, 0)) > 0.8))
        e2 = mask ^ mb
        edge |= e1 | e2
    return col, mask, edge


def to_image(col, mask, edge, base=(118, 126, 138)):
    h, w = col.shape
    img = np.full((h, w, 3), 255.0)
    c = np.clip(col, 0, 1.15)[..., None] * np.array(base)[None, None, :] / 0.85
    img[mask] = np.clip(c[mask], 0, 255)
    im = Image.fromarray(img.astype(np.uint8))
    em = Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
    dark = Image.new("RGB", im.size, (35, 38, 44))
    im.paste(dark, mask=em)
    return im


FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def card(man, title, accent, path):
    SS = 2
    col, mask, edge = render(man, size=(1500 * SS, 1000 * SS), scale=17.0 * SS)
    part = to_image(col, mask, edge).resize((1500, 1000), Image.LANCZOS)
    bbox = Image.fromarray((~np.all(np.asarray(part) > 250, axis=2)).astype(np.uint8) * 255).getbbox()
    pad = Image.new("RGB", (part.width + 200, part.height + 200), (255, 255, 255))
    pad.paste(part, (100, 100))
    part = pad.crop((bbox[0] + 60, bbox[1] + 60, bbox[2] + 140, bbox[3] + 140))

    W_, H_ = 1400, 820
    canvas = Image.new("RGB", (W_, H_), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, W_, 14), fill=accent)
    d.text((60, 50), title, font=ImageFont.truetype(FONT_B, 54), fill=(30, 33, 40))
    maxw, maxh = W_ - 120, 600
    k = min(maxw / part.width, maxh / part.height, 1.0)
    part = part.resize((int(part.width * k), int(part.height * k)), Image.LANCZOS)
    canvas.paste(part, ((W_ - part.width) // 2, 160 + (maxh - part.height) // 2))
    canvas.save(path)


card(cale_pleine(), "Version cale pleine", (40, 90, 160), f"{OUT}/cale_version_A_pleine.png")
card(cale_evidee(), "Version cale évidée nervurée", (200, 110, 30), f"{OUT}/cale_version_B_evidee.png")
print("ok")
