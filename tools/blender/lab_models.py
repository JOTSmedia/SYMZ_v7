"""Exploded View lab, rendered in Blender (Cycles): the sword, the name plaque and the controller dock, each built
part by part (same parts, homes and explode offsets as the site's interactive version), shot at 9 explode steps.
Also writes per-frame screen positions of the labelled parts (for the site's tags) and the print extent.
Geometry is authored in three.js space (y up) under a root rotated +90deg about X, so the numbers match the old code.
env: OUT, W, H, SAMPLES, MODEL (blade|plaque|dock), STEPS (default 9), FONT_BOLD, FONT_SCRIPT"""
import bpy, bmesh, math, os, json
from mathutils import Vector, Euler, Matrix
from bpy_extras.object_utils import world_to_camera_view
OUT = os.environ.get('OUT', '/tmp/claude-0/scratch/lab/out'); os.makedirs(OUT, exist_ok=True)
RW, RH = int(os.environ.get('W', '900')), int(os.environ.get('H', '1000'))
SAMPLES = int(os.environ.get('SAMPLES', '32')); MODEL = os.environ.get('MODEL', 'blade'); STEPS = int(os.environ.get('STEPS', '9'))
ONLY = [int(v) for v in os.environ.get('ONLY', '').split(',') if v != '']
FB = os.environ.get('FONT_BOLD', '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheroscn-bold.otf')
FS = os.environ.get('FONT_SCRIPT', '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrechorus-mediumitalic.otf')

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.device = 'CPU'; cy.samples = SAMPLES; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.03; cy.use_denoising = True
try: cy.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
cy.max_bounces = 6; cy.glossy_bounces = 4; cy.diffuse_bounces = 3; cy.sample_clamp_indirect = 3
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RW, RH, 100
sc.render.film_transparent = True; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
for vt in ('AgX', 'Filmic'):
    try: sc.view_settings.view_transform = vt; break
    except Exception: pass
for lk in ('AgX - Medium High Contrast', 'Medium High Contrast', 'None'):
    try: sc.view_settings.look = lk; break
    except Exception: pass
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.02, 0.018, 0.02, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1

ROOT = bpy.data.objects.new('root', None); sc.collection.objects.link(ROOT); ROOT.rotation_euler = (math.pi / 2, 0, 0)
GRP = bpy.data.objects.new('model', None); sc.collection.objects.link(GRP); GRP.parent = ROOT; GRP.rotation_mode = 'ZYX'

# ---------------- materials ----------------
def hexc(h): return tuple(((h >> s) & 255) / 255.0 for s in (16, 8, 0))
def srgb2lin(c): return tuple((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)
MATS = {}
def mat(color, rough=0.42, metal=0.08, emit=None, es=0.0, axis='Z', pitch=0.03, coat=0.0):
    key = (color, rough, metal, emit, axis, pitch)
    if key in MATS: return MATS[key]
    m = bpy.data.materials.new('m%d' % len(MATS)); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; p = N['Principled BSDF']
    p.inputs['Base Color'].default_value = (*srgb2lin(hexc(color)), 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if coat: p.inputs['Coat Weight'].default_value = coat
    if emit is not None: p.inputs['Emission Color'].default_value = (*srgb2lin(hexc(emit)), 1); p.inputs['Emission Strength'].default_value = es
    # printed layer lines along the print axis (world space)
    geo = N.new('ShaderNodeNewGeometry'); sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], sep.inputs[0])
    mu = N.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 2 * math.pi / (pitch * 0.33)
    L.new(sep.outputs[axis], mu.inputs[0]); sn = N.new('ShaderNodeMath'); sn.operation = 'SINE'; L.new(mu.outputs[0], sn.inputs[0])
    b = N.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.0 if metal > 0.5 else 0.22; b.inputs['Distance'].default_value = 0.004
    L.new(sn.outputs[0], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    MATS[key] = m; return m
RED, BONE, BLACK, STEEL = 0xe3141b, 0xf0e9e4, 0x161416, 0xc4c8cf

# ---------------- primitives (three.js space) ----------------
def obj_from_bm(name, bm, m, smooth=False, bev=0.0):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = smooth
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.rotation_mode = 'ZYX'
    if m: o.data.materials.append(m)
    if bev:
        md = o.modifiers.new('bev', 'BEVEL'); md.width = bev; md.segments = 2; md.limit_method = 'ANGLE'
    return o
def box(w, h, d, m, bev=0.012):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(w, h, d), verts=bm.verts); return obj_from_bm('box', bm, m, False, bev)
def cyl(rt, rb, h, seg, m, bev=0.008):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=rb, radius2=rt, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, 'X'))   # z -> y
    return obj_from_bm('cyl', bm, m, seg > 12, bev if seg <= 12 else 0)
def sphere(r, m, seg=32, rings=16):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r); return obj_from_bm('sph', bm, m, True)
def octa(r, m):
    bm = bmesh.new(); P = [bm.verts.new(v) for v in ((r, 0, 0), (-r, 0, 0), (0, r, 0), (0, -r, 0), (0, 0, r), (0, 0, -r))]
    for a, b, c in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)): bm.faces.new((P[a], P[b], P[c]))
    return obj_from_bm('oct', bm, m, False)
def torus(R, r, m, rs=10, ts=32):
    bm = bmesh.new(); rows = []
    for i in range(ts):
        u = 2 * math.pi * i / ts; row = []
        for j in range(rs):
            v = 2 * math.pi * j / rs; row.append(bm.verts.new(((R + r * math.cos(v)) * math.cos(u), (R + r * math.cos(v)) * math.sin(u), r * math.sin(v))))
        rows.append(row)
    for i in range(ts):
        for j in range(rs): bm.faces.new((rows[i][j], rows[(i + 1) % ts][j], rows[(i + 1) % ts][(j + 1) % rs], rows[i][(j + 1) % rs]))
    return obj_from_bm('tor', bm, m, True)
class Shape:
    def __init__(s): s.pts = []; s.holes = []
    def moveTo(s, x, y): s.pts.append((x, y)); return s
    def lineTo(s, x, y): s.pts.append((x, y)); return s
    def quad(s, cx, cy, x, y, n=12):
        x0, y0 = s.pts[-1]
        for i in range(1, n + 1):
            t = i / n; s.pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y))
        return s
    def bez(s, c1x, c1y, c2x, c2y, x, y, n=14):
        x0, y0 = s.pts[-1]
        for i in range(1, n + 1):
            t = i / n; a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            s.pts.append((a * x0 + b * c1x + c * c2x + d * x, a * y0 + b * c1y + c * c2y + d * y))
        return s
    def arc(s, cx, cy, r, n=72, rev=False):
        s.pts = [(cx + r * math.cos(2 * math.pi * i / n * (-1 if rev else 1)), cy + r * math.sin(2 * math.pi * i / n * (-1 if rev else 1))) for i in range(n)]; return s
def extrude(shape, depth, m, bevel=0.03):
    cu = bpy.data.curves.new('ex', 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'; cu.extrude = depth / 2; cu.bevel_depth = bevel; cu.bevel_resolution = 3; cu.resolution_u = 1
    for poly in [shape.pts] + [h.pts for h in shape.holes]:
        pts = poly[:-1] if len(poly) > 2 and abs(poly[0][0] - poly[-1][0]) < 1e-6 and abs(poly[0][1] - poly[-1][1]) < 1e-6 else poly
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for i, (x, y) in enumerate(pts): sp.points[i].co = (x, y, 0, 1)
        sp.use_cyclic_u = True
    o = bpy.data.objects.new('ex', cu); sc.collection.objects.link(o)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get())); bpy.data.objects.remove(o)
    ob = bpy.data.objects.new('ex', me); sc.collection.objects.link(ob); ob.rotation_mode = 'ZYX'; ob.data.materials.append(m); return ob
def text(body, font, size, depth, m, layers_bev=0.004):
    cu = bpy.data.curves.new('tx', 'FONT'); cu.body = body; cu.font = bpy.data.fonts.load(font); cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.extrude = depth / 2; cu.bevel_depth = layers_bev; cu.bevel_resolution = 2
    o = bpy.data.objects.new('tx', cu); sc.collection.objects.link(o)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get())); bpy.data.objects.remove(o)
    ob = bpy.data.objects.new('tx', me); sc.collection.objects.link(ob); ob.rotation_mode = 'ZYX'; ob.data.materials.append(m)
    return ob
def group(*children):
    g = bpy.data.objects.new('g', None); sc.collection.objects.link(g); g.rotation_mode = 'ZYX'
    for c in children: c.parent = g
    return g
def at(o, x=0, y=0, z=0, rx=0, ry=0, rz=0, s=None):
    o.location = (x, y, z); o.rotation_euler = (rx, ry, rz)
    if s is not None: o.scale = s
    return o
PARTS = []
def part(o, off, label=None, rot=(0, 0, 0), pin=False):
    o.parent = GRP; PARTS.append(dict(o=o, home=Vector(o.location), r0=Vector(o.rotation_euler), off=Vector(off), rot=Vector(rot), label=label, pin=pin, s0=Vector(o.scale))); return o

# ---------------- the three models (ported from the site) ----------------
def build_blade():
    steel = mat(STEEL, 0.28, 0.75); red = mat(RED, 0.35); blk = mat(BLACK, 0.55); dark = mat(0x2b2a2f, 0.35, 0.6)
    pom = group(octa(0.2, red), at(torus(0.17, 0.045, dark), rx=math.pi / 2)); at(pom, 0, 0.22, 0); part(pom, (0, 0, 0), 'Pommel')
    kids = [cyl(0.11, 0.13, 0.95, 24, blk)] + [at(torus(0.125, 0.028, dark), 0, -0.4 + i * 0.133, 0, rx=math.pi / 2) for i in range(7)]
    grip = group(*kids); at(grip, 0, 0.9, 0); part(grip, (0, 0.45, 0), 'Wrapped grip', (0, 0.6, 0))
    gs = Shape().moveTo(0, -.16).quad(.5, -.2, .95, .02).quad(1.18, .18, 1.2, .42).quad(.98, .2, .62, .14).quad(.3, .12, .16, .22).lineTo(0, .3)
    gs.lineTo(-.16, .22).quad(-.3, .12, -.62, .14).quad(-.98, .2, -1.2, .42).quad(-1.18, .18, -.95, .02).quad(-.5, -.2, 0, -.16)
    gem_m = mat(0xff3b3b, 0.15, 0.3, emit=0x9a0008, es=2.0)
    g1 = at(octa(0.13, gem_m), 0, .06, .14, s=(1, 1.3, .6)); g2 = at(octa(0.13, gem_m), 0, .06, -.14, s=(1, 1.3, .6))
    guard = group(extrude(gs, .16, red, .04), g1, g2); at(guard, 0, 1.55, 0); part(guard, (0, .95, .15), 'Crossguard', (0, 0, .15))
    hw = lambda y: .27 - .03 * (y / 2.6) if y < 2.6 else .24 * (1 - (y - 2.6) / .9)
    for i, (a, b) in enumerate(((0, 1.2), (1.2, 2.4), (2.4, 3.5))):
        s = Shape(); st = 10; s.moveTo(-hw(a), a)
        for k in range(st + 1): y = a + (b - a) * k / st; s.lineTo(hw(y), y)
        if i == 2: s.lineTo(0, 3.5)
        for k in range(st, -1, -1):
            if i == 2 and k == st: continue
            y = a + (b - a) * k / st; s.lineTo(-hw(y), y)
        kids = [extrude(s, .05, steel, .045)]
        fl = min(b, 3.0) - a - .12
        if fl > 0: kids.append(at(box(.07, fl, .16, dark, .01), 0, a + .06 + fl / 2, 0))
        seg = group(*kids); at(seg, 0, 1.78, 0)
        part(seg, (0, 1.45 + i * .48, 0), ['Blade section A', 'Blade section B', 'Tip section'][i], (0, -.25 if i % 2 else .25, 0))
    for i, (y, o) in enumerate(((1.35, .6), (1.72, 1.2), (2.98, 1.68), (4.18, 2.16))):
        pin = at(cyl(.035, .035, .26, 12, mat(RED, .3), 0), 0, y, 0, s=(.001, .001, .001)); part(pin, (0, o, 0), 'Alignment pin' if i == 2 else None, pin=True)
    return dict(frame=(2.2, 3.3, 10.5, 13.4), layers=265, axis='Z')
def star(r1, r2, n=5):
    s = Shape()
    for i in range(n * 2 + 1):
        r = r2 if i % 2 else r1; a = math.pi / 2 + i * math.pi / n
        (s.lineTo if i else s.moveTo)(math.cos(a) * r, math.sin(a) * r)
    return s
def build_plaque():
    white = mat(BONE, axis='Y', pitch=.022); pink = mat(0xff6fae, axis='Y', pitch=.022); lil = mat(0xb9a6ff, axis='Y', pitch=.022)
    yel = mat(0xffc93c, axis='Y', pitch=.022); red = mat(RED, axis='Y', pitch=.022); blk = mat(BLACK); namec = mat(0xff4f9a, .45, axis='Y', pitch=.022); blue = mat(0x2fb6d6, .45, axis='Y', pitch=.022)
    cy_ = 1.92
    foot = at(box(1.9, .16, .75, blk), 0, .08, 0); part(foot, (0, 0, 0), 'Stand')
    disc = at(cyl(1.7, 1.7, .14, 96, white), 0, cy_, 0, rx=math.pi / 2); part(disc, (0, .15, -.35), 'Base disc')
    rs = Shape().arc(0, 0, 1.72); h = Shape().arc(0, 0, 1.54, rev=True); rs.holes.append(h)
    ring = at(extrude(rs, .06, pink, .025), 0, cy_, .1); part(ring, (0, .15, .35), 'Color rim')
    cl = [at(cyl(r, r, .1, 48, lil), x, y, 0, rx=math.pi / 2) for x, y, r in ((-.45, 0, .32), (0, .12, .42), (.45, 0, .32), (-.2, -.08, .3), (.2, -.08, .3))]
    cloud = group(*cl); at(cloud, 0, cy_ - 1.02, .12); part(cloud, (0, .05, .8), 'Cloud layer')
    name = at(text('Ava', FS, 1.05, .13, namec, .006), 0, cy_ + .25, .14); part(name, (0, .25, 1.35), 'Name, 10 layers')
    stats = at(text('06:48 AM · 7 LB 4 OZ · 19 IN', FB, .17, .07, blue, .003), 0, cy_ - .45, .1); part(stats, (0, .1, 1.05), 'Birth stats')
    for i, (x, y, r) in enumerate(((-1.0, .85, .17), (-.62, 1.15, .11), (1.02, .8, .14))):
        s = at(extrude(star(r, r * .45), .06, yel, .02), x, cy_ + y - .1, .12, rz=i * .4); part(s, (x * .15, .2 + y * .1, 1.6), 'Stars' if i == 0 else None, (0, 0, .6))
    hs = Shape().moveTo(0, -.2).bez(-.05, -.15, -.26, 0, -.26, .12).bez(-.26, .24, -.12, .3, 0, .18).bez(.12, .3, .26, .24, .26, .12).bez(.26, 0, .05, -.15, 0, -.2)
    heart = at(extrude(hs, .06, red, .02), 1.0, cy_ - .95, .12); part(heart, (.15, .1, 1.9), 'Heart charm', (0, .5, 0))
    return dict(frame=(1.95, 2.1, 10.4, 11.8), layers=180, axis='Y')
def capsule(r, ln, m):
    return group(cyl(r, r, ln, 32, m), at(sphere(r, m), 0, ln / 2, 0), at(sphere(r, m), 0, -ln / 2, 0))
def build_dock():
    red = mat(RED); blk = mat(BLACK, .5); bone = mat(BONE, .38); gray = mat(0x6d6a70)
    base = at(cyl(1.25, 1.4, .38, 6, blk, .03), 0, .19, 0, ry=math.pi / 6); part(base, (0, 0, 0), 'Hex base')
    tx = at(text('SYMZ', FB, .42, .03, mat(BONE, .4)), 0, .045, 0, rx=-math.pi / 2)
    ringG = group(at(cyl(1.08, 1.08, .08, 6, red, .02), ry=math.pi / 6), tx); at(ringG, 0, .42, 0); part(ringG, (0, .35, 0), 'Logo inlay')
    for i, sg in enumerate((-1, 1)):
        pr = group(box(.24, 1.05, .34, red, .02), at(box(.44, .12, .5, red, .02), sg * -.08, .52, 0)); at(pr, sg * .62, .98, 0)
        part(pr, (sg * .7, .5, 0), 'Cradle arm' if i else None, (0, 0, sg * .25))
    ctrl = bpy.data.objects.new('ctrl', None); sc.collection.objects.link(ctrl); ctrl.parent = GRP; ctrl.location = (0, 1.95, 0)
    def cpart(o, off, label=None, rot=(0, 0, 0)):
        p = part(o, off, label, rot); o.parent = ctrl; return p
    body = at(sphere(1, bone, 64, 32), s=(1.05, .42, .36)); cpart(body, (0, 1.35, 0), 'Controller shell')
    for sg in (-1, 1):
        gr = at(capsule(.27, .5, bone), sg * .78, -.32, -.02, rz=sg * .5); cpart(gr, (sg * .55, 1.2, 0), None, (0, 0, sg * .3))
    for i, sg in enumerate((-1, 1)):
        tr = at(box(.42, .14, .3, red, .02), sg * .62, .4, -.08, rz=sg * -.18); cpart(tr, (sg * .25, 2.05, -.2), 'Triggers' if i else None)
    dp = group(box(.32, .1, .08, blk, .01), box(.1, .32, .08, blk, .01)); at(dp, -.52, .06, .33); cpart(dp, (0, 1.35, .95), 'D-pad')
    bcol = (RED, BONE, BLACK, 0x6d6a70)
    for i, (x, y) in enumerate(((0, .13), (.13, 0), (0, -.13), (-.13, 0))):
        b = at(cyl(.065, .065, .1, 24, mat(bcol[i])), .52 + x, .06 + y, .33, rx=math.pi / 2); cpart(b, (x * .8, 1.35 + y * .8, 1.15), 'Face buttons' if i == 0 else None)
    for i, sg in enumerate((-1, 1)):
        st = group(at(cyl(.06, .06, .16, 16, gray), rx=math.pi / 2), at(cyl(.13, .12, .06, 32, blk), 0, 0, .09, rx=math.pi / 2)); at(st, sg * .26, -.16, .3)
        cpart(st, (0, 1.3, 1.4), 'Thumbsticks' if i else None)
    return dict(frame=(1.35, 2.2, 8.8, 10.8), layers=212, axis='Z')
INFO = {'blade': build_blade, 'plaque': build_plaque, 'dock': build_dock}[MODEL]()

# ---------------- build plate ----------------
plate_img = os.environ.get('PLATE', '/tmp/claude-0/scratch/lab/plate.png')
pm = bpy.data.materials.new('plate'); pm.use_nodes = True; pn = pm.node_tree.nodes; pp = pn['Principled BSDF']
pp.inputs['Roughness'].default_value = 0.72; pp.inputs['Metallic'].default_value = 0.05
if os.path.exists(plate_img):
    t = pn.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(plate_img); pm.node_tree.links.new(t.outputs['Color'], pp.inputs['Base Color'])
side = mat(0x0e0c0d, .5, .6)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(7, .16, 7), verts=bm.verts)
uvl = bm.loops.layers.uv.new()
for f in bm.faces:
    for l in f.loops: l[uvl].uv = (l.vert.co.x / 7 + .5, -l.vert.co.z / 7 + .5)
plate = obj_from_bm('plate', bm, pm, False, .02); plate.data.materials.append(side)
for f in plate.data.polygons: f.material_index = 0 if f.normal.y > 0.9 else 1
plate.parent = ROOT; plate.location = (0, -.08, 0)

# ---------------- lights (studio softboxes + brand red rim) ----------------
def area(name, loc, size, power, color=(1, 1, 1), tgt=(0, 0, 2)):
    Lg = bpy.data.lights.new(name, 'AREA'); Lg.size = size; Lg.energy = power; Lg.color = color
    o = bpy.data.objects.new(name, Lg); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
area('key', (5, -7, 9), 5, 2600, (1.0, 0.97, 0.94))
area('fill', (-7, -5, 4), 6, 700, (0.92, 0.95, 1.0))
area('rim', (-6, 6, 5), 3, 1000, (1.0, 0.12, 0.1))
area('top', (0, 1, 12), 4, 900)
# camera
cam = bpy.data.cameras.new('cam'); cam.lens_unit = 'FOV'; cam.sensor_fit = 'VERTICAL'; cam.angle_y = math.radians(32)
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
GRP.rotation_euler = (0, float(os.environ.get('YAW', '-0.5')), 0)
def sm(a, b, x):
    t = min(1, max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
meta = {'model': MODEL, 'w': RW, 'h': RH, 'layers': INFO['layers'], 'frames': []}
labels = [p['label'] for p in PARTS]
meta['labels'] = [l for l in labels if l]
for i in range(STEPS):
    ex = i / (STEPS - 1)
    for p in PARTS:
        o = p['o']; o.location = p['home'] + p['off'] * ex; o.rotation_euler = tuple(p['r0'][k] + p['rot'][k] * ex for k in range(3))
        if p['pin']: s = max(.001, sm(.05, .4, ex)); o.scale = (s, s, s)
    y0, y1, d0, d1 = INFO['frame']; asp = RW / RH; narrow = asp < .8
    d = (d0 + (d1 - d0) * ex) * (1.3 if narrow else 1.0); ty = y0 + (y1 - y0) * ex; el = .2
    co.location = (0, -math.cos(el) * d, ty + math.sin(el) * d)   # three (0, ty+sin*d, cos*d) -> blender (x, -z, y)
    co.rotation_euler = (Vector((0, 0, ty)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    tags = []
    for p in PARTS:
        if not p['label']: continue
        v = world_to_camera_view(sc, co, p['o'].matrix_world.translation); tags.append([round(v.x, 4), round(1 - v.y, 4)])
    # print extent (assembled): bottom = plate contact, top = highest point of the model
    if i == 0:
        ys = []
        for p in PARTS:
            for ob in [p['o']] + list(p['o'].children_recursive):
                if ob.type != 'MESH': continue
                for c in ob.bound_box: ys.append(1 - world_to_camera_view(sc, co, ob.matrix_world @ Vector(c)).y)
        meta['print'] = [round(min(ys), 4), round(max(ys), 4)]
        meta['bed'] = round(1 - world_to_camera_view(sc, co, Vector((0, 0, 0))).y, 4)
    meta['frames'].append({'ex': round(ex, 4), 'tags': tags})
    if ONLY and i not in ONLY: continue
    sc.render.filepath = os.path.join(OUT, '%s-%02d.png' % (MODEL, i)); bpy.ops.render.render(write_still=True); print('rendered', MODEL, i, flush=True)
# plate only, with the assembled camera: the print-in animation reveals the model over this
if not ONLY or 'plate' in os.environ.get('EXTRA', 'plate'):
    y0, y1, d0, d1 = INFO['frame']; d = d0 * (1.3 if RW / RH < .8 else 1.0); el = .2
    co.location = (0, -math.cos(el) * d, y0 + math.sin(el) * d); co.rotation_euler = (Vector((0, 0, y0)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    for p in PARTS:
        for ob in [p['o']] + list(p['o'].children_recursive): ob.hide_render = True
    sc.render.filepath = os.path.join(OUT, '%s-plate.png' % MODEL); bpy.ops.render.render(write_still=True); print('rendered plate', flush=True)
meta['parts'] = sum(1 for p in PARTS if not p['pin']); meta['pins'] = any(p['pin'] for p in PARTS)
json.dump(meta, open(os.path.join(OUT, '%s.json' % MODEL), 'w'))
print('meta', MODEL, len(meta['frames']), flush=True)
