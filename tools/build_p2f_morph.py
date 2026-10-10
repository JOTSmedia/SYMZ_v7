"""Wireframe for the Photo -> Figure 'adjust for print' step.
Vertices are placed on the finished figure (img/p2f/fig.webp) and triangulated there (the print version).
Each one also gets a start position inside the scanned person (img/p2f/cut.webp): itself if it already lies in the
person's silhouette, otherwise the nearest point that does. The page animates start -> end, so the scan mesh
reshapes into the print-ready model. Writes a compact JSON: v=[sx,sy,ex,ey,...], t=[i,j,k,...], g=[grey per triangle]."""
import json, sys, numpy as np, cv2
from PIL import Image
from scipy.spatial import Delaunay
from scipy.ndimage import distance_transform_edt
D = sys.argv[1] if len(sys.argv) > 1 else 'img/p2f'
P = np.asarray(Image.open(f'{D}/cut.webp').convert('RGBA')); F = np.asarray(Image.open(f'{D}/fig.webp').convert('RGBA'))
mp = (P[..., 3] > 128).astype(np.uint8); mf = (F[..., 3] > 128).astype(np.uint8); H, W = mf.shape
lum = (0.3 * F[..., 0] + 0.59 * F[..., 1] + 0.11 * F[..., 2]).astype(np.uint8)
pts = cv2.goodFeaturesToTrack(lum, 700, 0.01, 12, mask=mf)[:, 0, :]
cs, _ = cv2.findContours(mf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
edge = np.vstack([c[::13, 0, :] for c in cs if len(c) > 40]).astype(np.float32)
yy, xx = np.mgrid[0:H:24, 0:W:24]; rng = np.random.default_rng(7)
grid = np.dstack([xx + rng.uniform(-5, 5, xx.shape), yy + rng.uniform(-5, 5, yy.shape)]).reshape(-1, 2)
grid = grid[(grid[:, 0] >= 0) & (grid[:, 0] < W) & (grid[:, 1] >= 0) & (grid[:, 1] < H)]
grid = grid[mf[grid[:, 1].astype(int), grid[:, 0].astype(int)] > 0]
E = np.vstack([pts, edge, grid]).astype(np.float32)
E = np.unique(np.round(E), axis=0)
# start: inside the person -> same place; outside -> nearest person pixel
_, (iy, ix) = distance_transform_edt(1 - mp, return_indices=True)
ei = np.clip(E.astype(int), [0, 0], [W - 1, H - 1])
S = np.stack([ix[ei[:, 1], ei[:, 0]], iy[ei[:, 1], ei[:, 0]]], 1).astype(np.float32)
tri = Delaunay(E); T = []; G = []
for t in tri.simplices:
    q = E[t]; c = q.mean(0); cx, cy = int(c[0]), int(c[1])
    if not mf[min(H - 1, cy), min(W - 1, cx)]: continue
    if max(np.linalg.norm(q[0] - q[1]), np.linalg.norm(q[1] - q[2]), np.linalg.norm(q[2] - q[0])) > 56: continue
    T.append(t.tolist()); G.append(int(np.clip(60 + lum[cy, cx] * 0.55, 40, 200)))
used = sorted({i for t in T for i in t}); remap = {o: n for n, o in enumerate(used)}
V = []
for o in used: V += [int(S[o, 0]), int(S[o, 1]), int(E[o, 0]), int(E[o, 1])]
out = {'v': V, 't': [remap[i] for t in T for i in t], 'g': G}
json.dump(out, open(f'{D}/morph.json', 'w'), separators=(',', ':'))
print('verts', len(used), 'tris', len(T), 'bytes', len(json.dumps(out, separators=(',', ':'))))
