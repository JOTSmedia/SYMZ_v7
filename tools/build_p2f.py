"""Build the Photo -> Figure animation layers from the two photos.
Inputs: background-removed cutouts of img_5978 (customer photo) and img_5997 (finished figure), made with rembg (isnet-general-use).
Outputs in img/p2f/: cut.webp (person), edge.webp (cut-line glow), mesh.webp (scan mesh), clay.webp (grey model), fig.webp (printed figure),
all on one shared canvas so they line up, plus p2f.json with how that canvas sits on the original photo."""
import sys, json, numpy as np, cv2
from PIL import Image
from scipy.spatial import Delaunay
SRC_CUT, SRC_FIG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TH = 1000                                   # shared canvas: subject height in px
def load(p): return np.asarray(Image.open(p).convert('RGBA')).astype(np.float32)
def bbox(a, t=40):
    ys, xs = np.where(a[..., 3] > t); return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
P = load(SRC_CUT); F = load(SRC_FIG)
def marks(A):
    """feet line, leg centre and head top: used to line the figure up with the person (the raised horn differs)"""
    m = A[..., 3] > 40; ys, xs = np.where(m); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    legx = np.where(m[int(y1 - (y1 - y0) * 0.25):y1])[1].mean(); w = (x1 - x0) * 0.12
    head = np.where(m[:, int(legx - w):int(legx + w)].any(1))[0].min()
    return dict(x0=x0, y0=y0, x1=x1, y1=y1, legx=legx, head=head)
mp, mf = marks(P), marks(F)
BODY = 1.0
sp, sf = BODY / (mp['y1'] - mp['head']), BODY / (mf['y1'] - mf['head'])     # same body height for both
up = max((mp['y1'] - mp['y0']) * sp, (mf['y1'] - mf['y0']) * sf)             # tallest reach (horn) above the feet
left = max((mp['legx'] - mp['x0']) * sp, (mf['legx'] - mf['x0']) * sf); right = max((mp['x1'] - mp['legx']) * sp, (mf['x1'] - mf['legx']) * sf)
k = TH / up; sp *= k; sf *= k; left *= k; right *= k
M = 40; CW = int(left + right + 2 * M); CH = TH + 2 * M; AX, AY = M + left, M + TH
def place(img, mk, s):
    big = cv2.resize(img, (int(round(img.shape[1] * s)), int(round(img.shape[0] * s))), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    ox = int(round(AX - mk['legx'] * s)); oy = int(round(AY - mk['y1'] * s))
    out = np.zeros((CH, CW, 4), np.float32)
    xs0, ys0 = max(0, -ox), max(0, -oy); xd0, yd0 = max(0, ox), max(0, oy)
    ww = min(big.shape[1] - xs0, CW - xd0); hh = min(big.shape[0] - ys0, CH - yd0)
    out[yd0:yd0 + hh, xd0:xd0 + ww] = big[ys0:ys0 + hh, xs0:xs0 + ww]
    return np.clip(out, 0, 255), ox, oy
cut, pox, poy = place(P, mp, sp)
fig, _, _ = place(F, mf, sf)
a = cut[..., 3] / 255.0; mask = (a > 0.5).astype(np.uint8)
def save(arr, name, q=86):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/{name}.webp', 'WEBP', quality=q, method=6)
save(cut, 'cut'); save(fig, 'fig')
# --- cut-line glow (where the background was cut away)
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
ring = cv2.dilate(mask, k, iterations=2) - cv2.erode(mask, k, iterations=1)
glow = cv2.GaussianBlur(ring.astype(np.float32), (0, 0), 3) * 1.6 + ring * 0.9
e = np.zeros((CH, CW, 4), np.float32); e[..., 0] = 255; e[..., 1] = 255; e[..., 2] = 255; e[..., 3] = np.clip(glow, 0, 1) * 255
save(e, 'edge', 80)
# --- grey "clay" model: shading from a height field built from the photo's luminance
rgb = cut[..., :3]; lum = (0.3 * rgb[..., 0] + 0.59 * rgb[..., 1] + 0.11 * rgb[..., 2]) / 255.0
lum = cv2.bilateralFilter(lum.astype(np.float32), 9, 0.12, 6)
dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5); dist = np.sqrt(dist / (dist.max() + 1e-6))     # rounded body volume
hgt = cv2.GaussianBlur(lum, (0, 0), 1.3) * 0.9 + cv2.GaussianBlur(dist, (0, 0), 5) * 1.5
gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=5) * 0.045; gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=5) * 0.045
n = np.dstack([-gx, -gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
L = np.array([-0.45, -0.6, 0.66]); L /= np.linalg.norm(L)
diff = np.clip((n * L).sum(2), 0, 1); rim = np.clip(1 - n[..., 2], 0, 1) ** 2
Hh = np.array([0, 0, 1.0]) + L; Hh /= np.linalg.norm(Hh); spec = np.clip((n * Hh).sum(2), 0, 1) ** 40
ao = np.clip(0.55 + 0.45 * cv2.GaussianBlur(lum, (0, 0), 7) / (lum.mean() + 1e-6) * 0.6, 0.45, 1.05)
base = np.array([196, 192, 188.0])
detail = np.clip(1 + 1.6 * (cv2.GaussianBlur(lum, (0, 0), 1.0) - cv2.GaussianBlur(lum, (0, 0), 6)), 0.55, 1.35)
clay = base * (0.1 + 0.9 * diff)[..., None] * ao[..., None] * detail[..., None] + 255 * (0.3 * spec + 0.1 * rim)[..., None]
c = np.dstack([np.clip(clay, 0, 255), cut[..., 3]]); save(c, 'clay')
# --- scan mesh: faceted low-poly surface + red wireframe
g8 = (lum * 255).astype(np.uint8)
pts = cv2.goodFeaturesToTrack(g8, 900, 0.01, 12, mask=mask)[:, 0, :]
cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
edge_pts = np.vstack([c[::14, 0, :] for c in cs if len(c) > 50]).astype(np.float32)
yy, xx = np.mgrid[0:CH:26, 0:CW:26]; rng = np.random.default_rng(4)
grid = np.dstack([xx + rng.uniform(-6, 6, xx.shape), yy + rng.uniform(-6, 6, yy.shape)]).reshape(-1, 2)
grid = grid[(grid[:, 0] >= 0) & (grid[:, 0] < CW) & (grid[:, 1] >= 0) & (grid[:, 1] < CH)]
grid = grid[mask[grid[:, 1].astype(int), grid[:, 0].astype(int)] > 0]
V = np.vstack([pts, edge_pts, grid]); tri = Delaunay(V)
S = 2; big = np.zeros((CH * S, CW * S, 4), np.uint8); NT = 0
facet = np.zeros((CH * S, CW * S, 3), np.uint8)
for t in tri.simplices:
    q = V[t]; c0 = q.mean(0); ci = (int(c0[1]), int(c0[0]))
    if not (0 <= ci[0] < CH and 0 <= ci[1] < CW) or not mask[ci]: continue
    if max(np.linalg.norm(q[0] - q[1]), np.linalg.norm(q[1] - q[2]), np.linalg.norm(q[2] - q[0])) > 60: continue
    NT += 1; v = int(np.clip(clay[ci][0] * 0.62, 26, 175)); poly = (q * S).astype(np.int32)
    cv2.fillConvexPoly(facet, poly, (v, int(v * 0.96), int(v * 0.95)), cv2.LINE_AA)
    cv2.polylines(big, [poly], True, (255, 58, 50, 255), 2, cv2.LINE_AA)
for p in V:
    if mask[min(CH - 1, int(p[1])), min(CW - 1, int(p[0]))]: cv2.circle(big, (int(p[0] * S), int(p[1] * S)), 2, (255, 225, 220, 200), -1, cv2.LINE_AA)
facet = cv2.resize(facet, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32)
wire = cv2.resize(big, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32)
wa = wire[..., 3:4] / 255.0
col = facet * (1 - wa) + wire[..., :3] * wa
alpha = np.maximum(mask * 255 * 0.92, wire[..., 3])
save(np.dstack([col, alpha]), 'mesh', 84)
json.dump({'w': CW, 'h': CH, 'feet': int(AY), 'ax': int(AX), 'points': int(len(V)), 'tris': int(NT), 'photo': {'src': 'img/img_5978.jpg', 'scale': round(sp, 5), 'x': pox, 'y': poy}}, open(f'{OUT}/p2f.json', 'w'))
print('canvas', CW, CH, 'photo scale', round(sp, 3), 'offset', pox, poy)
