"""
Stylized 3D TyGuy character + scene helpers for Blender (bpy).

Characters are assembled from smooth-shaded primitives (capsule limbs,
rounded torso, sphere head) with Principled BSDF materials, giving a clean
toon-ish 3D look. TyGuy wears his blue hoodie with a white cross.
"""

import math
import bpy
from mathutils import Vector


# --------------------------------------------------------------------------- #
# palettes  (linear-ish sRGB 0..1)
# --------------------------------------------------------------------------- #
def _c(r, g, b):
    return (r / 255, g / 255, b / 255)


TYGUY = {
    "skin": _c(226, 176, 140), "hair": _c(46, 33, 27), "beard": _c(150, 122, 100),
    "hoodie": _c(33, 92, 208), "hoodie_dark": _c(24, 66, 158),
    "pants": _c(26, 28, 36), "shoe": _c(33, 92, 208),
    "beard_on": True, "hair_long": False, "emblem_T": True,
    "shoe_white": True, "quiff": True,
}
MIA = {
    "skin": _c(244, 205, 178), "hair": _c(120, 70, 35), "beard": _c(0, 0, 0),
    "hoodie": _c(70, 175, 120), "hoodie_dark": _c(52, 140, 96),
    "pants": _c(150, 95, 70), "shoe": _c(250, 250, 250),
    "beard_on": False, "hair_long": True,
}
KID_A = {
    "skin": _c(236, 188, 150), "hair": _c(30, 26, 24), "beard": _c(0, 0, 0),
    "hoodie": _c(210, 70, 70), "hoodie_dark": _c(172, 52, 52),
    "pants": _c(45, 50, 65), "shoe": _c(40, 40, 48),
    "beard_on": False, "hair_long": False,
}
KID_B = {
    "skin": _c(214, 162, 122), "hair": _c(90, 60, 35), "beard": _c(0, 0, 0),
    "hoodie": _c(240, 180, 60), "hoodie_dark": _c(205, 150, 45),
    "pants": _c(55, 60, 75), "shoe": _c(240, 240, 245),
    "beard_on": False, "hair_long": False,
}


# --------------------------------------------------------------------------- #
# material cache
# --------------------------------------------------------------------------- #
_mats = {}


def mat(name, color, rough=0.55, sub=0.0):
    key = (name, color, rough, sub)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    if "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = sub
    _mats[key] = m
    return m


def _smooth(obj, subsurf=1):
    for p in obj.data.polygons:
        p.use_smooth = True
    if subsurf:
        mo = obj.modifiers.new("subsurf", "SUBSURF")
        mo.levels = subsurf
        mo.render_levels = subsurf


def _ball(loc, r, m, scale=(1, 1, 1), subsurf=1, coll=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=24, ring_count=16)
    o = bpy.context.active_object
    o.scale = scale
    o.data.materials.append(m)
    _smooth(o, subsurf)
    if coll is not None:
        coll.objects.append(o)
    return o


def _capsule(p0, p1, r, m, subsurf=1, coll=None):
    p0 = Vector(p0)
    p1 = Vector(p1)
    d = p1 - p0
    L = d.length
    mid = (p0 + p1) / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=L, location=mid, vertices=20)
    cyl = bpy.context.active_object
    quat = Vector((0, 0, 1)).rotation_difference(d)
    cyl.rotation_euler = quat.to_euler()
    cyl.data.materials.append(m)
    _smooth(cyl, subsurf)
    objs = [cyl]
    for p in (p0, p1):
        objs.append(_ball(p, r, m, subsurf=subsurf))
    if coll is not None:
        coll += objs
    return objs


def _box(loc, size, m, subsurf=0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.materials.append(m)
    if subsurf:
        _smooth(o, subsurf)
    return o


# --------------------------------------------------------------------------- #
# character builder
# --------------------------------------------------------------------------- #
def build_character(pal, x=0.0, y=0.0, facing=-1, pose=None, name="char"):
    """
    Build a character standing on z=0. `facing` -1 => faces -Y (toward camera).
    pose: dict with arm_l, arm_r (deg, 0=down, +=out), arm_fwd_l/r (deg forward),
          lean (deg), head_turn (deg), parts collected into an Empty parent.
    Returns the parent Empty.
    """
    pose = pose or {}
    fy = facing  # +1 face +Y, -1 face -Y
    skin = mat("skin", pal["skin"], rough=0.5, sub=0.12)
    hair = mat("hair", pal["hair"], rough=0.6)
    hoodie = mat("hoodie", pal["hoodie"], rough=0.65)
    hood_d = mat("hoodied", pal["hoodie_dark"], rough=0.65)
    pants = mat("pants", pal["pants"], rough=0.7)
    shoe = mat("shoe", pal["shoe"], rough=0.5)
    white = mat("white", (0.97, 0.98, 1.0), rough=0.4)
    dark = mat("eyedark", (0.06, 0.05, 0.05), rough=0.3)

    parent = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(parent)
    parts = []
    # build at local origin; the root empty is positioned at the end
    gx, gy = x, y
    x = 0.0
    y = 0.0

    # heights
    HIP = 0.95
    SH = 1.62
    HEAD = 2.02
    HR = 0.40

    # legs
    for sgn in (-1, 1):
        hipp = (x + sgn * 0.16, y, HIP)
        foot = (x + sgn * 0.18, y, 0.06)
        knee = (x + sgn * 0.17, y + fy * 0.02, HIP * 0.5)
        _capsule(hipp, knee, 0.14, pants, coll=parts)
        _capsule(knee, foot, 0.12, pants, coll=parts)
        # shoe (blue upper)
        parts.append(_ball((x + sgn * 0.18, y + fy * 0.12, 0.10), 0.16, shoe,
                           scale=(1.0, 1.5, 0.72)))
        if pal.get("shoe_white"):
            sole = mat("sole", (0.95, 0.96, 1.0), rough=0.5)
            parts.append(_ball((x + sgn * 0.18, y + fy * 0.12, 0.045), 0.165, sole,
                               scale=(1.06, 1.58, 0.34)))   # white sole
            parts.append(_ball((x + sgn * 0.18, y + fy * 0.34, 0.085), 0.10, sole,
                               scale=(1.0, 0.7, 0.85)))      # white toe cap

    # torso (hoodie) - tapered: belly ball + chest ball
    parts.append(_ball((x, y, 1.18), 0.34, hoodie, scale=(1.05, 0.85, 1.0)))
    parts.append(_ball((x, y, 1.5), 0.36, hoodie, scale=(1.15, 0.9, 1.0)))
    # hood collar
    parts.append(_ball((x, y + fy * 0.04, 1.66), 0.2, hood_d, scale=(1.3, 1.0, 0.5)))

    # white "T" emblem on chest (front faces camera at -Y => y + fy*..)
    if pal.get("emblem_T"):
        tmat = mat("emblemwhite", (0.98, 0.99, 1.0), rough=0.35)
        t_b = tmat.node_tree.nodes.get("Principled BSDF")
        if "Emission Color" in t_b.inputs:
            t_b.inputs["Emission Color"].default_value = (0.9, 0.95, 1.0, 1)
            t_b.inputs["Emission Strength"].default_value = 0.2
        cy_ = y + fy * 0.345
        parts.append(_box((x, cy_, 1.30), (0.10, 0.05, 0.34), tmat))      # stem
        parts.append(_box((x, cy_, 1.45), (0.34, 0.05, 0.11), tmat))      # top bar
        # hoodie drawstrings
        smat = mat("string", (0.95, 0.96, 1.0), rough=0.5)
        for sg in (-1, 1):
            sx = x + sg * 0.10
            _capsule((sx, y + fy * 0.30, 1.62), (sx, y + fy * 0.345, 1.42),
                     0.02, smat, subsurf=0, coll=parts)
            parts.append(_ball((sx, y + fy * 0.345, 1.41), 0.032, smat, subsurf=0))

    # arms
    lean = math.radians(pose.get("lean", 0))
    sh_z = SH
    for sgn, akey, fkey in ((-1, "arm_l", "fwd_l"), (1, "arm_r", "fwd_r")):
        ang = math.radians(pose.get(akey, 14))
        fwd = math.radians(pose.get(fkey, 8))
        sh_p = Vector((x + sgn * 0.34, y, sh_z))
        # direction: down(-z), out(+/-x by ang), forward(-fy y by fwd)
        ux = sgn * math.sin(ang)
        uz = -math.cos(ang)
        uy = -fy * math.sin(fwd)
        d = Vector((ux, uy, uz)).normalized()
        elbow = sh_p + d * 0.42
        # forearm bends a bit more forward
        d2 = (d + Vector((0, -fy * 0.25, -0.05))).normalized()
        hand = elbow + d2 * 0.40
        _capsule(sh_p, elbow, 0.12, hoodie, coll=parts)
        _capsule(elbow, hand, 0.105, hoodie, coll=parts)
        parts.append(_ball(hand, 0.13, skin))

    # neck
    _capsule((x, y, 1.66), (x, y, 1.78), 0.1, skin, coll=parts)

    # head
    ht = math.radians(pose.get("head_turn", 0))
    hx = x + math.sin(ht) * 0.0
    head = _ball((x, y, HEAD), HR, skin, scale=(0.95, 1.0, 1.08))
    parts.append(head)
    # ears
    for sgn in (-1, 1):
        parts.append(_ball((x + sgn * HR * 0.95, y, HEAD), 0.1, skin, scale=(0.6, 0.8, 1.0)))

    # beard
    if pal.get("beard_on"):
        parts.append(_ball((x, y + fy * 0.06, HEAD - 0.12), HR * 0.96,
                           mat("beard", pal["beard"], rough=0.8),
                           scale=(0.95, 1.0, 0.85)))
        # carve: put a skin chin-cheek ball slightly forward to suggest mouth area
        parts.append(_ball((x, y + fy * 0.30, HEAD - 0.06), 0.14, skin,
                           scale=(1.1, 0.7, 0.8)))

    # hair cap (sits on top, above the eyes)
    parts.append(_ball((x, y - fy * 0.04, HEAD + 0.30), HR * 0.98, hair,
                       scale=(1.04, 1.08, 0.62)))
    if pal.get("hair_long"):
        parts.append(_ball((x, y - fy * 0.20, HEAD - 0.02), HR * 0.92, hair,
                           scale=(0.95, 0.85, 1.15)))
        parts.append(_ball((x, y - fy * 0.26, HEAD - 0.42), 0.18, hair,
                           scale=(0.9, 0.8, 1.5)))  # ponytail
    # fringe sweep at the front hairline (above the eyes)
    parts.append(_ball((x, y + fy * 0.34, HEAD + 0.22), 0.20, hair,
                       scale=(1.5, 0.6, 0.45)))
    if pal.get("quiff"):
        # raised front quiff / spiky tuft
        parts.append(_ball((x, y + fy * 0.30, HEAD + 0.40), 0.17, hair,
                           scale=(1.45, 0.75, 1.05)))
        for sg in (-1, 0, 1):
            parts.append(_ball((x + sg * 0.13, y + fy * 0.26, HEAD + 0.52),
                               0.07, hair, scale=(0.8, 0.8, 1.5)))

    # face  (front faces the camera at -Y, i.e. y + fy*HR)
    eye_y = y + fy * (HR * 0.86)
    eye_z = HEAD + 0.02
    hi = mat("hilite", (1.0, 1.0, 1.0), rough=0.2)
    for sgn in (-1, 1):
        ex = x + sgn * 0.155
        # eye white
        parts.append(_ball((ex, eye_y, eye_z), 0.10, white, scale=(1.0, 0.6, 1.2)))
        # iris/pupil, pushed forward so it reads from the front
        parts.append(_ball((ex, eye_y + fy * 0.055, eye_z), 0.058, dark,
                           scale=(1.0, 0.7, 1.0)))
        # catch-light
        parts.append(_ball((ex - sgn * 0.02, eye_y + fy * 0.09, eye_z + 0.03),
                           0.018, hi))
        # eyebrow
        parts.append(_box((ex, eye_y + fy * 0.02, eye_z + 0.15),
                          (0.15, 0.05, 0.035), hair))
    # nose
    parts.append(_ball((x, y + fy * (HR * 0.95), HEAD - 0.08), 0.06, skin,
                       scale=(0.8, 0.9, 0.8)))
    # smile (thin dark curved box); for bearded TyGuy it reads as a grin line
    parts.append(_box((x, y + fy * (HR * 0.82), HEAD - 0.20),
                      (0.18, 0.05, 0.03), dark))

    # parent everything to the root empty and place it in the world
    for o in parts:
        o.parent = parent
    parent.location = (gx, gy, 0.0)
    parent.rotation_euler = (0, 0, math.radians(pose.get("rotz", 0)))
    return parent


# --------------------------------------------------------------------------- #
# scene setup helpers
# --------------------------------------------------------------------------- #
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()


def setup_render(res=(1280, 720), samples=80, fps=24):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.fps = fps
    sc.render.film_transparent = False
    # color management
    try:
        sc.view_settings.look = "None"
    except Exception:
        pass
    return sc


def add_camera(loc, look_at, lens=50):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = loc
    direction = Vector(look_at) - Vector(loc)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return cam


def add_lights():
    # key
    k = bpy.data.lights.new("Key", "AREA")
    k.energy = 900
    k.size = 6
    ko = bpy.data.objects.new("Key", k)
    bpy.context.scene.collection.objects.link(ko)
    ko.location = (4, -5, 7)
    ko.rotation_euler = (0.6, 0.2, 0.6)
    # fill
    f = bpy.data.lights.new("Fill", "AREA")
    f.energy = 300
    f.size = 8
    fo = bpy.data.objects.new("Fill", f)
    bpy.context.scene.collection.objects.link(fo)
    fo.location = (-5, -4, 4)
    fo.rotation_euler = (1.0, -0.2, -0.6)
    # rim
    r = bpy.data.lights.new("Rim", "AREA")
    r.energy = 500
    r.size = 4
    ro = bpy.data.objects.new("Rim", r)
    bpy.context.scene.collection.objects.link(ro)
    ro.location = (0, 5, 6)
    ro.rotation_euler = (-0.7, 0, 0)


def set_world(color=(0.10, 0.30, 0.65), strength=0.6):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength


def add_ground(color=(0.75, 0.72, 0.68)):
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    g = bpy.context.active_object
    g.data.materials.append(mat("ground", color, rough=0.9))
    return g
