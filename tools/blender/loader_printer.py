"""Photoreal Cycles render of a 3D printer printing the SYMZ CUSTOMZ logo sign.
env: OUT (dir), W, H, SAMPLES, PROGRESS (comma list 0..1), NX (comma list: nozzle x offsets in mm per frame, optional)"""
import bpy, bmesh, json, math, os
from mathutils import Vector

OUT = os.environ.get('OUT', '/tmp/claude-0/scratch/blend/out'); os.makedirs(OUT, exist_ok=True)
RW, RH = int(os.environ.get('W', '960')), int(os.environ.get('H', '600'))
SAMPLES = int(os.environ.get('SAMPLES', '32'))
PROG = [float(x) for x in os.environ.get('PROGRESS', '0.55').split(',')]
LOGO = json.load(open('/tmp/claude-0/scratch/blend/logo.json'))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.device = 'CPU'; cy.samples = SAMPLES; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.03
cy.use_denoising = True
try: cy.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 4; cy.transmission_bounces = 4; cy.sample_clamp_indirect = 4
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RW, RH, 100
sc.render.image_settings.file_format = 'PNG'
for vt in ('Filmic', 'AgX'):
    try: sc.view_settings.view_transform = vt; break
    except Exception: pass
for lk in ('High Contrast', 'Medium High Contrast', 'AgX - Punchy', 'None'):
    try: sc.view_settings.look = lk; break
    except Exception: pass
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.006, 0.005, 0.0055, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1

# ---------------- materials ----------------
def P(m): return m.node_tree.nodes['Principled BSDF']
def mat(name, color, metal=0.0, rough=0.5, coat=0.0, trans=0.0, emit=None, es=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = P(m)
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Metallic'].default_value = metal; p.inputs['Roughness'].default_value = rough
    if coat: p.inputs['Coat Weight'].default_value = coat
    if trans: p.inputs['Transmission Weight'].default_value = trans
    if emit: p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = es
    return m
def bump(m, kind, strength=0.3, dist=0.0003, scale=1.0, period=0.0004, axis='Z', rough_var=0.0):
    nt = m.node_tree; N = nt.nodes; L = nt.links; p = P(m)
    b = N.new('ShaderNodeBump'); b.inputs['Strength'].default_value = strength; b.inputs['Distance'].default_value = dist
    if kind == 'layers':        # printed layer lines: sine of world height
        g = N.new('ShaderNodeNewGeometry'); sp = N.new('ShaderNodeSeparateXYZ'); L.new(g.outputs['Position'], sp.inputs[0])
        mu = N.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 2 * math.pi / period; L.new(sp.outputs[axis], mu.inputs[0])
        sn = N.new('ShaderNodeMath'); sn.operation = 'SINE'; L.new(mu.outputs[0], sn.inputs[0]); src = sn.outputs[0]
    elif kind == 'noise':       # powder coat / cast texture
        tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6
        L.new(tc.outputs['Object'], nz.inputs['Vector']); src = nz.outputs['Fac']
    elif kind == 'brushed':     # brushed / extruded aluminium: noise stretched along one axis
        tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale * 0.02) if axis == 'Z' else ((scale * 0.02, scale, scale) if axis == 'X' else (scale, scale * 0.02, scale))
        nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1; nz.inputs['Detail'].default_value = 8
        L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs['Vector'], nz.inputs['Vector']); src = nz.outputs['Fac']
    L.new(src, b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    if rough_var:
        r0 = p.inputs['Roughness'].default_value
        mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = max(0, r0 - rough_var); mr.inputs['To Max'].default_value = r0 + rough_var
        L.new(src, mr.inputs['Value']); L.new(mr.outputs['Result'], p.inputs['Roughness'])
    return m

ANOD = bump(mat('anodised', (0.018, 0.018, 0.02), 1.0, 0.32), 'brushed', 0.08, 0.0002, 900, axis='Z', rough_var=0.08)
ANODX = bump(mat('anodisedX', (0.018, 0.018, 0.02), 1.0, 0.32), 'brushed', 0.08, 0.0002, 900, axis='X', rough_var=0.08)
ANODY = bump(mat('anodisedY', (0.018, 0.018, 0.02), 1.0, 0.32), 'brushed', 0.08, 0.0002, 900, axis='Y', rough_var=0.08)
ALU = bump(mat('alu', (0.78, 0.79, 0.8), 1.0, 0.28), 'brushed', 0.1, 0.0002, 1200, axis='X', rough_var=0.06)
STEEL = mat('steel', (0.85, 0.86, 0.87), 1.0, 0.16)
LEAD = bump(mat('leadscrew', (0.75, 0.62, 0.42), 1.0, 0.25), 'layers', 0.6, 0.0008, period=0.002, axis='Z')
BRASS = mat('brass', (0.93, 0.68, 0.32), 1.0, 0.18)
SOCK = mat('silicone', (0.55, 0.03, 0.03), 0.0, 0.62)
REDABS = bump(mat('redabs', (0.42, 0.006, 0.01), 0.0, 0.42, coat=0.15), 'noise', 0.06, 0.0002, scale=2500)
BLACKP = bump(mat('blackplastic', (0.012, 0.012, 0.013), 0.0, 0.5), 'noise', 0.06, 0.0002, scale=2500)
POM = mat('pom', (0.02, 0.02, 0.022), 0.0, 0.28)
RUBBER = mat('rubber', (0.01, 0.01, 0.01), 0.0, 0.75)
PTFE = mat('ptfe', (0.92, 0.92, 0.9), 0.0, 0.18, trans=0.6)
LABEL = mat('label', (0.85, 0.85, 0.83), 0.0, 0.45)
FLOOR = bump(mat('floor', (0.012, 0.011, 0.011), 0.0, 0.32), 'noise', 0.05, 0.001, scale=60, rough_var=0.12)
WALL = mat('wall', (0.01, 0.009, 0.009), 0.0, 0.8)
# textured PEI (powder-coated spring steel, gold)
PEI = mat('pei', (0.3, 0.18, 0.05), 0.45, 0.62)
_n = PEI.node_tree.nodes; _l = PEI.node_tree.links
_tc = _n.new('ShaderNodeTexCoord'); _nz = _n.new('ShaderNodeTexNoise'); _nz.inputs['Scale'].default_value = 4200; _nz.inputs['Detail'].default_value = 4
_l.new(_tc.outputs['Object'], _nz.inputs['Vector'])
_b = _n.new('ShaderNodeBump'); _b.inputs['Strength'].default_value = 0.55; _b.inputs['Distance'].default_value = 0.00025
_l.new(_nz.outputs['Fac'], _b.inputs['Height']); _l.new(_b.outputs['Normal'], P(PEI).inputs['Normal'])
_ramp = _n.new('ShaderNodeValToRGB'); _ramp.color_ramp.elements[0].color = (0.16, 0.085, 0.022, 1); _ramp.color_ramp.elements[1].color = (0.36, 0.22, 0.07, 1)
_l.new(_nz.outputs['Fac'], _ramp.inputs['Fac']); _l.new(_ramp.outputs['Color'], P(PEI).inputs['Base Color'])
# printed PLA with layer lines (0.2 mm layers, slightly exaggerated so they read on camera)
LAYER = 0.0003
for _m in ('pla_red', 'pla_white', 'pla_black'): pass
PLA_RED = bump(mat('pla_red', (0.62, 0.012, 0.02), 0.0, 0.36), 'layers', 0.35, 0.00012, period=LAYER)
PLA_WHITE = bump(mat('pla_white', (0.82, 0.8, 0.77), 0.0, 0.4), 'layers', 0.35, 0.00012, period=LAYER)
PLA_BLACK = bump(mat('pla_black', (0.007, 0.007, 0.008), 0.0, 0.5), 'layers', 0.45, 0.00012, period=LAYER)
for m in (PLA_RED, PLA_WHITE, PLA_BLACK): P(m).inputs['Subsurface Weight'].default_value = 0.05 if m is not PLA_BLACK else 0.0
for _m in (PLA_RED, PLA_WHITE, PLA_BLACK):
    try: P(_m).inputs['Specular IOR Level'].default_value = 0.22; P(_m).inputs['Roughness'].default_value = 0.55
    except Exception as e: print('spec', e)
HOT = mat('hot', (1, 0.4, 0.1), 0, 0.5, emit=(1.0, 0.38, 0.08), es=6)
SCREEN = mat('screen', (0.02, 0.03, 0.05), 0, 0.15, emit=(0.25, 0.55, 1.0), es=1.2)

# ---------------- geometry helpers ----------------
def link(o, m=None):
    sc.collection.objects.link(o)
    if m: o.data.materials.append(m)
    return o
def from_bm(name, bm, m=None, smooth=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth is not None:
        for poly in me.polygons: poly.use_smooth = smooth(poly)
    return link(bpy.data.objects.new(name, me), m)
def bevel(o, w=0.0006, seg=2):
    md = o.modifiers.new('bev', 'BEVEL'); md.width = w; md.segments = seg; md.limit_method = 'ANGLE'; return o
def box(name, size, loc, m, bev=0.0006, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    o = from_bm(name, bm, m); o.location = loc; o.rotation_euler = rot
    return bevel(o, bev) if bev else o
def cyl(name, r, depth, loc, m, seg=48, rot=(0, 0, 0), r2=None, bev=0.0004):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    o = from_bm(name, bm, m, smooth=lambda p: abs(p.normal.z) < 0.9); o.location = loc; o.rotation_euler = rot
    return bevel(o, bev, 2) if bev else o
def vslot(name, length, axis, loc, m=None):
    """20x20 V-slot aluminium extrusion"""
    h = 0.01; side = [(-0.01, -0.01), (-0.0041, -0.01), (-0.0031, -0.009), (-0.0031, -0.0045), (0.0031, -0.0045), (0.0031, -0.009), (0.0041, -0.01)]
    pts = []
    for k in range(4):
        a = k * math.pi / 2; c, s = math.cos(a), math.sin(a)
        pts += [(x * c - y * s, x * s + y * c) for (x, y) in side]
    bm = bmesh.new(); vs = [bm.verts.new((x, y, -length / 2)) for x, y in pts]; f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); top = [e for e in ex['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, length), verts=top); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cv = bm.verts.new((0, 0, 0))  # (unused)
    bm.verts.remove(cv)
    o = from_bm(name, bm, m or {'x': ANODX, 'y': ANODY, 'z': ANOD}[axis]); o.location = loc
    if axis == 'x': o.rotation_euler = (0, math.pi / 2, 0)
    elif axis == 'y': o.rotation_euler = (math.pi / 2, 0, 0)
    return bevel(o, 0.0004, 1)
def curve_shape(name, contours, depth, m, to_xy, z_rot=True):
    """filled, extruded 2D shape from pixel contours -> mesh"""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'; cu.extrude = depth / 2; cu.resolution_u = 1
    cu.bevel_depth = 0.00025; cu.bevel_resolution = 1
    for c in contours:
        sp = cu.splines.new('POLY'); sp.points.add(len(c) - 1)
        for i, (px, py) in enumerate(c):
            x, y = to_xy(px, py); sp.points[i].co = (x, y, 0, 1)
        sp.use_cyclic_u = True
    o = bpy.data.objects.new(name + '_cu', cu); sc.collection.objects.link(o)
    deps = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(deps))
    bpy.data.objects.remove(o); mo = link(bpy.data.objects.new(name, me), m)
    for poly in me.polygons: poly.use_smooth = False
    return mo

# ---------------- studio ----------------
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2.5); link(bpy.data.objects.new('floor', bpy.data.meshes.new('floor')), FLOOR); bm.to_mesh(sc.objects['floor'].data); bm.free()
wall = box('wall', (5, 0.02, 3), (0, 1.1, 1.4), WALL, 0)

def area(name, loc, target, size, power, color=(1, 1, 1), sy=None):
    L = bpy.data.lights.new(name, 'AREA'); L.shape = 'RECTANGLE'; L.size = size; L.size_y = sy or size; L.energy = power; L.color = color
    o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.location = loc
    d = Vector(target) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); return o
T = (0, 0, 0.28)
area('key', (-0.42, -0.55, 0.72), T, 0.55, 70, (1.0, 0.97, 0.93), 0.38)
area('fill', (0.7, -0.5, 0.3), T, 0.6, 14, (0.95, 0.97, 1.0))
area('rimred', (0.32, 0.5, 0.46), (0, 0, 0.28), 0.32, 26, (1.0, 0.06, 0.05))
area('top', (0.0, 0.25, 0.85), (0, 0, 0.1), 0.45, 22)
area('kick', (-0.5, 0.35, 0.3), (0, 0, 0.26), 0.3, 5, (1.0, 0.2, 0.16))

# ---------------- printer ----------------
for x in (-0.2, 0.2): vslot('baseY%+.1f' % x, 0.42, 'y', (x, 0, 0.03))
for y in (-0.19, 0.19): vslot('baseX%+.2f' % y, 0.38, 'x', (0, y, 0.03))
for x in (-0.012, 0.012): vslot('bedrail%+.3f' % x, 0.42, 'y', (x, 0, 0.03))
for x in (-0.2, 0.2):
    for y in (0.0, 0.02): vslot('up%+.1f%.2f' % (x, y), 0.47, 'z', (x, y, 0.275))
vslot('topbar', 0.44, 'x', (0, 0.01, 0.52))
for x in (-0.2, 0.2):
    for y in (-0.19, 0.19): cyl('foot', 0.012, 0.02, (x, y, 0.01), RUBBER, 32)
# motors (Y at back, Z left, E on top)
def motor(name, loc, rot=(0, 0, 0)):
    o = box(name, (0.042, 0.042, 0.04), loc, BLACKP, 0.0015, rot)
    box(name + 'cap', (0.0425, 0.0425, 0.008), (loc[0], loc[1], loc[2] + 0.016), ALU, 0.0008, rot)
    box(name + 'lab', (0.03, 0.0005, 0.02), (loc[0], loc[1] - 0.0213, loc[2] - 0.005), LABEL, 0)
motor('ymotor', (0, 0.235, 0.06)); motor('zmotor', (-0.175, 0.01, 0.065))
cyl('leadscrew', 0.004, 0.43, (-0.175, 0.01, 0.31), LEAD, 24)
cyl('coupler', 0.0095, 0.025, (-0.175, 0.01, 0.1), ALU, 32)
# control box + screen on the front right
pass  # (control screen removed: it blocked the foreground)
pass
pass
# heated bed
BED = 0.078
box('bedplate', (0.235, 0.235, 0.003), (0, 0, BED - 0.0023), ALU, 0.0008)
box('pei', (0.235, 0.235, 0.0008), (0, 0, BED - 0.0004), PEI, 0.0003)
box('carriage', (0.2, 0.2, 0.004), (0, 0, 0.052), ANOD, 0.0008)
for x in (-0.105, 0.105):
    for y in (-0.105, 0.105):
        cyl('knob', 0.012, 0.009, (x, y, 0.045), REDABS, 40)
        cyl('spring', 0.0045, 0.018, (x, y, 0.062), mat('springy', (0.9, 0.75, 0.15), 1.0, 0.3), 16)

# ---------------- camera (placed first: the sign height is solved from what it sees) ----------------
from bpy_extras.object_utils import world_to_camera_view
cam = bpy.data.cameras.new('cam'); cam.lens = 41; cam.dof.use_dof = True; cam.dof.aperture_fstop = 4.0
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
co.location = (0.43, -1.02, 0.36); tgt = Vector((0.0, 0.02, 0.30))
co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()
def img_y(pt): return world_to_camera_view(sc, co, Vector(pt)).y
FRAME_TOP = 0.53                                   # top face of the top extrusion
# ---------------- the print: SYMZ CUSTOMZ sign, hovering halfway up the frame ----------------
W0, H0, PAD = LOGO['W'], LOGO['H'], LOGO['pad']
HS = 0.24; WS = HS * W0 / H0
want = (img_y((0, 0, BED)) + img_y((0, 0.01, FRAME_TOP))) / 2   # halfway between platform and frame top, on screen
lo, hi = BED + 0.05, FRAME_TOP - 0.1
for _ in range(40):
    mid = (lo + hi) / 2
    if img_y((0, -0.003, mid)) < want: lo = mid
    else: hi = mid
SIGN0 = (lo + hi) / 2 - HS / 2
print('sign centre z', round(SIGN0 + HS / 2, 4), flush=True)
cam.dof.focus_distance = (Vector((0, 0, SIGN0 + HS / 2)) - co.location).length
def xy(px, py, pad=0): return ((px - pad) / W0 - 0.5) * WS, (1 - (py - pad) / H0) * HS
parts = []
# no stand: the sign hovers mid-frame and prints in mid-air (on purpose)
import numpy as _np, cv2 as _cv2
_pts = _np.array([p for c in LOGO['back'] for p in c], _np.float32); _x0, _y0 = _pts.min(0); _x1, _y1 = _pts.max(0); _r = 26
_hull = []                                                       # clean rounded-rectangle plate behind the logo
for _cx, _cy, _a0 in ((_x1 - _r, _y0 + _r, -90), (_x1 - _r, _y1 - _r, 0), (_x0 + _r, _y1 - _r, 90), (_x0 + _r, _y0 + _r, 180)):
    for _k in range(9):
        _a = math.radians(_a0 + _k * 90 / 8); _hull.append([_cx + _r * math.cos(_a), _cy + _r * math.sin(_a)])
back = curve_shape('backing', [_hull], 0.004, PLA_BLACK, lambda px, py: xy(px, py, PAD))
red = curve_shape('red', LOGO['red'], 0.0024, PLA_RED, xy)
white = curve_shape('white', LOGO['white'], 0.0024, PLA_WHITE, xy)
for o, yoff in ((back, 0.0), (red, -0.0031), (white, -0.0031)):
    o.rotation_euler = (math.pi / 2, 0, 0); o.location = (0, yoff, SIGN0); parts.append(o)

# ---------------- gantry + toolhead (positioned per frame) ----------------
head = []
def H(o): head.append((o, Vector(o.location))); return o
H(cone_ := cyl('nozzle', 0.0062, 0.006, (0, 0, 0.003), BRASS, 6, r2=0.0062, bev=0.0003))
H(cyl('nozzletip', 0.0009, 0.004, (0, 0, -0.001), BRASS, 32, r2=0.0035, bev=0))
H(box('sock', (0.024, 0.019, 0.013), (0, 0.001, 0.0125), SOCK, 0.003))
H(cyl('heatbreak', 0.0025, 0.007, (0, 0, 0.0225), STEEL, 24))
for i in range(9): H(cyl('fin%d' % i, 0.0115, 0.0011, (0, 0, 0.029 + i * 0.0027), ALU, 48, bev=0.0002))
H(cyl('core', 0.006, 0.026, (0, 0, 0.04), ALU, 32))
H(box('shroud', (0.052, 0.03, 0.05), (0, -0.026, 0.038), REDABS, 0.004))
H(cyl('fanring', 0.018, 0.002, (0, -0.0415, 0.04), BLACKP, 48, rot=(math.pi / 2, 0, 0)))
H(cyl('fanhub', 0.007, 0.003, (0, -0.042, 0.04), BLACKP, 32, rot=(math.pi / 2, 0, 0)))
for i in range(3): H(cyl('grill%d' % i, 0.006 + i * 0.005, 0.0012, (0, -0.0428, 0.04), STEEL, 48, rot=(math.pi / 2, 0, 0)))
H(box('duct', (0.034, 0.012, 0.01), (0, -0.016, 0.008), REDABS, 0.002))
H(box('plate', (0.07, 0.005, 0.07), (0, 0.022, 0.04), ANOD, 0.0015))
for (dx, dz) in ((-0.024, 0.062), (0.024, 0.062), (0, 0.016)): H(cyl('wheel', 0.012, 0.01, (dx, 0.03, dz), POM, 48, rot=(math.pi / 2, 0, 0)))
H(box('belt', (0.36, 0.006, 0.0015), (0, 0.04, 0.05), RUBBER, 0))
xrail = vslot('xrail', 0.38, 'x', (0, 0.04, 0.04)); head.append((xrail, Vector(xrail.location)))
xm = box('xmotor', (0.042, 0.042, 0.042), (-0.205, 0.045, 0.04), BLACKP, 0.0015); head.append((xm, Vector(xm.location)))
glow = bpy.data.lights.new('glow', 'POINT'); glow.energy = 0.35; glow.color = (1, 0.45, 0.15); glow.shadow_soft_size = 0.002
go = bpy.data.objects.new('glow', glow); sc.collection.objects.link(go); go.location = (0, -0.004, -0.0005); head.append((go, Vector(go.location)))
hotdot = cyl('hotdot', 0.0012, 0.0004, (0, 0, -0.0012), HOT, 16, bev=0); head.append((hotdot, Vector(hotdot.location)))

# PTFE tube (bezier) from the heatsink up to the extruder on the top bar
ext = box('extruder', (0.045, 0.04, 0.042), (-0.16, 0.0, 0.552), BLACKP, 0.002); box('lever', (0.008, 0.035, 0.03), (-0.135, -0.005, 0.56), REDABS, 0.002)
tube_cu = bpy.data.curves.new('ptfe', 'CURVE'); tube_cu.dimensions = '3D'; tube_cu.bevel_depth = 0.002; tube_cu.bevel_resolution = 3
tube = link(bpy.data.objects.new('ptfe', tube_cu), PTFE)
def set_tube(a):
    tube_cu.splines.clear(); sp = tube_cu.splines.new('BEZIER'); sp.bezier_points.add(1)
    p0, p1 = sp.bezier_points
    p0.co = a; p0.handle_left = a - Vector((0, 0, 0.05)); p0.handle_right = a + Vector((0, 0, 0.18))
    p1.co = Vector((-0.16, 0.0, 0.575)); p1.handle_left = p1.co + Vector((0.12, 0, 0.12)); p1.handle_right = p1.co + Vector((-0.05, 0, 0.0))

# cutter for the partial print
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); cutter = from_bm('cutter', bm); cutter.hide_render = True; cutter.display_type = 'WIRE'
for o in parts:
    md = o.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cutter; md.solver = 'EXACT'

def height(p): return (HS + 0.002) * p
NX = [float(x) for x in os.environ.get('NX', '').split(',')] if os.environ.get('NX') else None
START = int(os.environ.get('START', '0'))
for i, p in enumerate(PROG):
    if i < START: continue
    cut = SIGN0 + max(0.0004, height(p))
    cutter.location = (0, 0, cut + 0.5); cutter.scale = (1.0, 1.0, 1.0)
    for o in parts: o.hide_render = p <= 0.0
    nx = (NX[i] / 1000.0) if NX else 0.03 * math.sin(i * 2.3)
    nz = cut + 0.0004 + (0.004 if p >= 1 else 0)   # big sign: the carriage only just clears the top bar at the end
    for o, base in head:
        if o.name.startswith(('xrail', 'xmotor')): o.location = (base.x, base.y, base.z + nz)
        else: o.location = (base.x + nx, base.y, base.z + nz)
    hotdot.hide_render = p >= 1; glow.energy = 0.08 if p >= 1 else 0.35
    set_tube(Vector((nx, 0.0, nz + 0.055)))
    sc.render.filepath = os.path.join(OUT, 'frame-%02d.png' % i)
    bpy.ops.render.render(write_still=True)
    print('rendered', i, p, flush=True)
