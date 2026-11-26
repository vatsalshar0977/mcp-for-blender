#!/usr/bin/env python3
"""Build a refined, directly openable TYTO Blender scene.

This is the source used to regenerate tyto_scene.blend. The .blend itself is
the deliverable; this script is optional and does not need to be run by the user.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
BLEND_PATH = ROOT / "blender" / "tyto_scene.blend"
RENDER_DIR = ROOT / "renders" / "blender"

# Spiral is drawn on the front XZ face; Y is the shallow product depth.
CENTER = Vector((0.0, 0.0, 1.16))
R_IN = 0.10
R_OUT = 1.72
TURNS = 1.48
FINAL_ANGLE = -0.22
PHASE = FINAL_ANGLE + TURNS * 2.0 * math.pi


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--save", action="store_true")
    p.add_argument("--still", action="store_true")
    p.add_argument("--animate", action="store_true")
    p.add_argument("--video", action="store_true")
    p.add_argument("--draft", action="store_true")
    p.add_argument("--ultra", action="store_true")
    p.add_argument("--samples", type=int, default=256)
    p.add_argument("--frame", type=int, default=170)
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--end", type=int, default=240)
    return p.parse_args(argv)


def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def socket(node, name, fallback=0):
    return node.inputs.get(name) if name in node.inputs else node.inputs[fallback]


def output(node, name, fallback=0):
    return node.outputs.get(name) if name in node.outputs else node.outputs[fallback]


def collection(scene, name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


def move(obj, coll):
    for c in tuple(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def new_material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    t.nodes.clear()
    out = t.nodes.new("ShaderNodeOutputMaterial")
    out.location = (620, 0)
    bsdf = t.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (340, 0)
    t.links.new(output(bsdf, "BSDF"), socket(out, "Surface"))
    return m, t, bsdf


def bronze_material():
    m, t, b = new_material("TYTO · satin dark bronze")
    set_input(b, "Base Color", (0.19, 0.112, 0.064, 1.0))
    set_input(b, "Metallic", 1.0)
    set_input(b, "Roughness", 0.32)
    set_input(b, "Anisotropic", 0.10)
    n = t.nodes.new("ShaderNodeTexNoise")
    set_input(n, "Scale", 165.0)
    set_input(n, "Detail", 2.0)
    rng = t.nodes.new("ShaderNodeMapRange")
    set_input(rng, "From Min", 0.0)
    set_input(rng, "From Max", 1.0)
    set_input(rng, "To Min", 0.27)
    set_input(rng, "To Max", 0.37)
    t.links.new(output(n, "Fac"), socket(rng, "Value"))
    t.links.new(output(rng, "Result"), socket(b, "Roughness"))
    bump = t.nodes.new("ShaderNodeBump")
    set_input(bump, "Strength", 0.045)
    set_input(bump, "Distance", 0.005)
    t.links.new(output(n, "Fac"), socket(bump, "Height"))
    t.links.new(output(bump, "Normal"), socket(b, "Normal"))
    m.diffuse_color = (0.19, 0.112, 0.064, 1.0)
    return m


def soft_touch_material():
    m, t, b = new_material("TYTO · matte black spiral channel")
    set_input(b, "Base Color", (0.012, 0.011, 0.010, 1.0))
    set_input(b, "Metallic", 0.0)
    set_input(b, "Roughness", 0.72)
    set_input(b, "Sheen Weight", 0.10)
    n = t.nodes.new("ShaderNodeTexNoise")
    set_input(n, "Scale", 80.0)
    bump = t.nodes.new("ShaderNodeBump")
    set_input(bump, "Strength", 0.06)
    set_input(bump, "Distance", 0.004)
    t.links.new(output(n, "Fac"), socket(bump, "Height"))
    t.links.new(output(bump, "Normal"), socket(b, "Normal"))
    return m


def configure_wave(w, direction, scale):
    if hasattr(w, "wave_type"):
        w.wave_type = "BANDS"
    if hasattr(w, "bands_direction"):
        w.bands_direction = direction
    if hasattr(w, "wave_profile"):
        w.wave_profile = "SIN"
    set_input(w, "Scale", scale)
    set_input(w, "Distortion", 0.0)
    set_input(w, "Detail", 0.0)


def knurled_bronze_material():
    m, t, b = new_material("TYTO · crisp diamond knurl")
    set_input(b, "Metallic", 1.0)
    set_input(b, "Roughness", 0.24)
    set_input(b, "Anisotropic", 0.20)
    tex = t.nodes.new("ShaderNodeTexCoord")
    ma = t.nodes.new("ShaderNodeMapping")
    mb = t.nodes.new("ShaderNodeMapping")
    set_input(ma, "Rotation", (0.0, 0.0, math.radians(45.0)))
    set_input(mb, "Rotation", (0.0, 0.0, math.radians(-45.0)))
    t.links.new(output(tex, "Object"), socket(ma, "Vector"))
    t.links.new(output(tex, "Object"), socket(mb, "Vector"))
    wa = t.nodes.new("ShaderNodeTexWave")
    wb = t.nodes.new("ShaderNodeTexWave")
    configure_wave(wa, "X", 72.0)
    configure_wave(wb, "X", 72.0)
    t.links.new(output(ma, "Vector"), socket(wa, "Vector"))
    t.links.new(output(mb, "Vector"), socket(wb, "Vector"))
    maximum = t.nodes.new("ShaderNodeMath")
    maximum.operation = "MAXIMUM"
    t.links.new(output(wa, "Fac"), maximum.inputs[0])
    t.links.new(output(wb, "Fac"), maximum.inputs[1])
    ramp = t.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.34
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.66
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    t.links.new(maximum.outputs[0], socket(ramp, "Fac"))
    mix = t.nodes.new("ShaderNodeMixRGB")
    mix.inputs[1].default_value = (0.17, 0.098, 0.052, 1.0)
    mix.inputs[2].default_value = (0.48, 0.300, 0.155, 1.0)
    t.links.new(output(ramp, "Color"), mix.inputs[0])
    t.links.new(output(mix, "Color"), socket(b, "Base Color"))
    bump = t.nodes.new("ShaderNodeBump")
    set_input(bump, "Strength", 0.60)
    set_input(bump, "Distance", 0.014)
    t.links.new(output(ramp, "Color"), socket(bump, "Height"))
    t.links.new(output(bump, "Normal"), socket(b, "Normal"))
    return m


def woven_grille_material():
    m, t, b = new_material("TYTO · visible woven mic mesh")
    set_input(b, "Metallic", 0.22)
    set_input(b, "Roughness", 0.62)
    set_input(b, "Sheen Weight", 0.08)
    tex = t.nodes.new("ShaderNodeTexCoord")
    checker = t.nodes.new("ShaderNodeTexChecker")
    set_input(checker, "Scale", 72.0)
    checker.inputs[1].default_value = (0.018, 0.017, 0.016, 1.0)
    checker.inputs[2].default_value = (0.135, 0.128, 0.120, 1.0)
    t.links.new(output(tex, "Object"), socket(checker, "Vector"))
    wx = t.nodes.new("ShaderNodeTexWave")
    wy = t.nodes.new("ShaderNodeTexWave")
    configure_wave(wx, "X", 120.0)
    configure_wave(wy, "Y", 126.0)
    t.links.new(output(tex, "Object"), socket(wx, "Vector"))
    t.links.new(output(tex, "Object"), socket(wy, "Vector"))
    multiply = t.nodes.new("ShaderNodeMath")
    multiply.operation = "MULTIPLY"
    t.links.new(output(wx, "Fac"), multiply.inputs[0])
    t.links.new(output(wy, "Fac"), multiply.inputs[1])
    t.links.new(output(checker, "Color"), socket(b, "Base Color"))
    bump = t.nodes.new("ShaderNodeBump")
    set_input(bump, "Strength", 0.30)
    set_input(bump, "Distance", 0.010)
    t.links.new(multiply.outputs[0], socket(bump, "Height"))
    t.links.new(output(bump, "Normal"), socket(b, "Normal"))
    return m


def emission_material(name, colour, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    t.nodes.clear()
    e = t.nodes.new("ShaderNodeEmission")
    e.name = "Emission"
    e.inputs["Color"].default_value = colour
    e.inputs["Strength"].default_value = strength
    out = t.nodes.new("ShaderNodeOutputMaterial")
    t.links.new(output(e, "Emission"), socket(out, "Surface"))
    m.diffuse_color = colour
    return m, e


def backdrop_material():
    m, t, b = new_material("Studio · warm-grey gradient")
    set_input(b, "Roughness", 0.45)
    geom = t.nodes.new("ShaderNodeNewGeometry")
    sep = t.nodes.new("ShaderNodeSeparateXYZ")
    rng = t.nodes.new("ShaderNodeMapRange")
    set_input(rng, "From Min", -8.0)
    set_input(rng, "From Max", 4.0)
    ramp = t.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.038, 0.034, 0.031, 1.0)
    ramp.color_ramp.elements[1].color = (0.105, 0.094, 0.084, 1.0)
    t.links.new(output(geom, "Position"), socket(sep, "Vector"))
    t.links.new(output(sep, "Y"), socket(rng, "Value"))
    t.links.new(output(rng, "Result"), socket(ramp, "Fac"))
    t.links.new(output(ramp, "Color"), socket(b, "Base Color"))
    return m


def mesh_object(name, verts, faces, coll, material=None, smooth=True):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    if material:
        mesh.materials.append(material)
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
    return obj


def curve_object(name, coords, coll, material, bevel_depth,
                 radii=None, cyclic=False, parent=None, bevel_resolution=4):
    cu = bpy.data.curves.new(name + " Curve", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 24
    cu.bevel_depth = bevel_depth
    cu.bevel_resolution = bevel_resolution
    cu.use_fill_caps = True
    if hasattr(cu, "bevel_factor_mapping_end"):
        cu.bevel_factor_mapping_end = "SPLINE"
    sp = cu.splines.new("POLY")
    sp.points.add(max(0, len(coords) - 1))
    sp.use_cyclic_u = cyclic
    for i, c in enumerate(coords):
        p = sp.points[i]
        p.co = (c[0], c[1], c[2], 1.0)
        p.radius = radii[i] if radii else 1.0
    obj = bpy.data.objects.new(name, cu)
    coll.objects.link(obj)
    if material:
        cu.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def spiral_xz(t):
    r = R_IN * (R_OUT / R_IN) ** t
    a = PHASE - TURNS * 2.0 * math.pi * t
    return CENTER.x + r * math.cos(a), CENTER.z + r * math.sin(a), r, a


def spiral_frame_xz(t):
    dt = 0.001
    x0, z0, _, _ = spiral_xz(max(0.0, t - dt))
    x1, z1, _, _ = spiral_xz(min(1.0, t + dt))
    tangent = Vector((x1 - x0, 0.0, z1 - z0))
    if tangent.length < 1e-6:
        tangent = Vector((1.0, 0.0, 0.0))
    tangent.normalize()
    normal = Vector((-tangent.z, 0.0, tangent.x))
    return tangent, normal


def build_shell(coll, bronze):
    # Metaballs fuse a large central lobe with a tapered logarithmic-spiral tail.
    mball = bpy.data.metaballs.new("TYTO shell volume")
    mball.resolution = 0.075
    mball.render_resolution = 0.04
    mball.threshold = 0.62
    for e in tuple(mball.elements):
        mball.elements.remove(e)
    for i in range(110):
        t = i / 109.0
        x, z, r, _ = spiral_xz(t)
        e = mball.elements.new()
        e.type = "BALL"
        e.co = (x, 0.05 + 0.34 * t, z)
        e.radius = 0.20 + 0.62 * t
        e.stiffness = 2.15
    for x, y, z, radius in (
        (CENTER.x - 0.20, -0.08, CENTER.z, 0.98),
        (CENTER.x + 0.20, -0.04, CENTER.z - 0.10, 0.86),
        (CENTER.x - 0.48, 0.02, CENTER.z + 0.40, 0.72),
        (CENTER.x + 0.55, 0.18, CENTER.z + 0.68, 0.70),
    ):
        e = mball.elements.new()
        e.type = "BALL"
        e.co = (x, y, z)
        e.radius = radius
        e.stiffness = 2.55
    obj = bpy.data.objects.new("TYTO · solid shell source", mball)
    coll.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    body = bpy.context.object
    body.name = "TYTO · rounded nautilus shell"
    body.data.materials.append(bronze)

    remesh = body.modifiers.new("Clean voxel weld", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = 0.035
    if hasattr(remesh, "use_smooth_shade"):
        remesh.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    relax = body.modifiers.new("Relax surface", "SMOOTH")
    relax.factor = 1.1
    relax.iterations = 5
    bpy.ops.object.modifier_apply(modifier=relax.name)
    subdiv = body.modifiers.new("Pebble fillets", "SUBSURF")
    subdiv.levels = 1
    subdiv.render_levels = 2

    body.scale.y = 0.72
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    min_z = min(v.co.z for v in body.data.vertices)
    body.location.z = -min_z + 0.035
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    bpy.context.view_layer.update()
    min_z = min(v.co.z for v in body.data.vertices)
    max_z = max(v.co.z for v in body.data.vertices)
    return body, min_z, max_z


def front_sampler(body, fallback_y=-0.42):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)

    def front_y(x, z, offset=0.0):
        hit, loc, _n, _i = evaluated.ray_cast(
            Vector((x, -5.0, z)), Vector((0.0, 1.0, 0.0)), distance=10.0
        )
        return (loc.y if hit else fallback_y) + offset

    return front_y, evaluated


def spiral_ribbon(name, points, width_fn, coll, material, front_y):
    verts, faces = [], []
    for i, (x, _y, z) in enumerate(points):
        u = i / max(1, len(points) - 1)
        _tan, normal = spiral_frame_xz(0.18 + 0.77 * u)
        hw = width_fn(u) * 0.5
        ax, az = x + normal.x * hw, z + normal.z * hw
        bx, bz = x - normal.x * hw, z - normal.z * hw
        verts.append((ax, front_y(ax, az, -0.016), az))
        verts.append((bx, front_y(bx, bz, -0.016), bz))
    for i in range(len(points) - 1):
        a = 2 * i
        faces.append((a, a + 1, a + 3, a + 2))
    return mesh_object(name, verts, faces, coll, material, smooth=True)


def build_spiral_details(body, min_z, max_z, coll, bronze, soft, led_material):
    front_y, evaluated = front_sampler(body)
    channel, groove, led, trim = [], [], [], []
    count = 210
    for i in range(count):
        u = i / (count - 1)
        t = 0.18 + 0.77 * u
        x, z, _r, _a = spiral_xz(t)
        _tan, normal = spiral_frame_xz(t)
        channel.append((x, front_y(x, z), z))
        off = 0.105 + 0.025 * u
        gx, gz = x + normal.x * off, z + normal.z * off
        groove.append((gx, front_y(gx, gz, -0.030), gz))
        led.append((gx, front_y(gx, gz, -0.048), gz))
        tx, tz = x - normal.x * (0.095 + 0.02 * u), z - normal.z * (0.095 + 0.02 * u)
        trim.append((tx, front_y(tx, tz, -0.022), tz))

    spiral_ribbon(
        "TYTO · narrow matte spiral channel",
        channel,
        lambda u: 0.15 + 0.04 * u,
        coll,
        soft,
        front_y,
    )
    curve_object("TYTO · shallow LED groove", groove, coll, soft, 0.018)
    curve_object("TYTO · inner machined edge", trim, coll, bronze, 0.008, bevel_resolution=3)
    led_curve = curve_object(
        "TYTO · animated amber spiral LED", led, coll, led_material, 0.012
    )

    # Smooth raised spiral eye: no vertical pin, just a shallow bronze boss.
    eye_points, eye_radii = [], []
    for i in range(100):
        u = i / 99.0
        a = 1.55 * math.pi * u + 0.35
        r = 0.022 + 0.33 * u
        x, z = CENTER.x + r * math.cos(a), CENTER.z + r * math.sin(a)
        eye_points.append((x, front_y(x, z, -0.095 - 0.015 * u), z))
        eye_radii.append(0.42 + 0.58 * u)
    eye_mat = simple_metal_material(
        "TYTO · polished spiral eye", (0.32, 0.19, 0.10, 1.0), 1.0, 0.22
    )
    curve_object(
        "TYTO · raised spiral eye", eye_points, coll, eye_mat, 0.082,
        radii=eye_radii
    )
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=48, ring_count=24, radius=1.0,
        location=(CENTER.x, front_y(CENTER.x, CENTER.z, -0.052), CENTER.z),
    )
    boss = bpy.context.object
    boss.name = "TYTO · spiral eye boss"
    move(boss, coll)
    boss.scale = (0.22, 0.085, 0.22)
    boss.data.materials.append(eye_mat)
    for poly in boss.data.polygons:
        poly.use_smooth = True

    # Short lower-body parting seam, visible only beneath the shell.
    seam_z = min_z + 0.22 * (max_z - min_z)
    seam_points = []
    for i in range(72):
        a = math.pi * (1.08 + 0.84 * i / 71.0)
        x = CENTER.x + 1.02 * math.cos(a)
        z = CENTER.z + 0.82 * math.sin(a)
        y = front_y(x, z, -0.006)
        seam_points.append((x, y, z))
    curve_object(
        "TYTO · lower parting seam", seam_points, coll, soft, 0.006,
        bevel_resolution=3
    )
    return front_y, led, led_curve


def annular_cylinder(name, outer, inner, depth, coll, material, segments=256):
    verts = []
    for z in (depth * 0.5, -depth * 0.5):
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            verts.append((outer * math.cos(a), outer * math.sin(a), z))
    for z in (depth * 0.5, -depth * 0.5):
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            verts.append((inner * math.cos(a), inner * math.sin(a), z))
    faces = []
    n = segments
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
        faces.append((2 * n + i, 3 * n + i, 3 * n + j, 2 * n + j))
        faces.append((i, 2 * n + i, 2 * n + j, j))
        faces.append((n + i, n + j, 3 * n + j, 3 * n + i))
    obj = mesh_object(name, verts, faces, coll, material, smooth=True)
    bevel = obj.modifiers.new("Machined edge bevel", "BEVEL")
    bevel.width = 0.016
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(28.0)
    return obj


def simple_metal_material(name, colour, metallic=1.0, roughness=0.25):
    m, t, b = new_material(name)
    set_input(b, "Base Color", colour)
    set_input(b, "Metallic", metallic)
    set_input(b, "Roughness", roughness)
    return m


def knurl_geometry(name, radius, depth, coll, material, parent,
                   lines=40, points=44):
    cu = bpy.data.curves.new(name + " Curve", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 2
    cu.bevel_depth = 0.0048
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    for sign in (1.0, -1.0):
        for k in range(lines):
            phase = 2.0 * math.pi * k / lines
            sp = cu.splines.new("POLY")
            sp.points.add(points - 1)
            for j in range(points):
                u = j / (points - 1)
                z = -depth * 0.5 + depth * u
                theta = phase + sign * u * 3.0 * math.pi
                pt = sp.points[j]
                pt.co = (radius * math.cos(theta), radius * math.sin(theta), z, 1.0)
    obj = bpy.data.objects.new(name, cu)
    coll.objects.link(obj)
    cu.materials.append(material)
    obj.parent = parent
    return obj


def grille_grid(name, radius, coll, material, parent,
                spacing=0.032, z=0.096):
    cu = bpy.data.curves.new(name + " Curve", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 1
    cu.bevel_depth = 0.0045
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    n = int(radius / spacing)
    for i in range(-n, n + 1):
        c = i * spacing
        if abs(c) >= radius:
            continue
        half = math.sqrt(max(0.0, radius * radius - c * c))
        sp = cu.splines.new("POLY")
        sp.points.add(1)
        sp.points[0].co = (-half, c, z + 0.001, 1.0)
        sp.points[1].co = (half, c, z + 0.001, 1.0)
        sp = cu.splines.new("POLY")
        sp.points.add(1)
        sp.points[0].co = (c, -half, z - 0.001, 1.0)
        sp.points[1].co = (c, half, z - 0.001, 1.0)
    obj = bpy.data.objects.new(name, cu)
    coll.objects.link(obj)
    cu.materials.append(material)
    obj.parent = parent
    return obj


def build_mouth(front_y, coll, bronze, ring_bronze, grille_mat,
                soft, led_mat, tick_mat, led_points):
    x, z, _r, _a = spiral_xz(0.965)
    tail = Vector((x, front_y(x, z, 0.10), z))
    axis = Vector((0.58, -0.76, 0.30)).normalized()
    base_quat = Vector((0.0, 0.0, 1.0)).rotation_difference(axis)
    mouth_center = tail + axis * 0.48

    root = bpy.data.objects.new("TYTO · mouth rig", None)
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 0.35
    coll.objects.link(root)
    root.location = mouth_center
    root.rotation_mode = "QUATERNION"
    root.rotation_quaternion = base_quat

    bpy.ops.mesh.primitive_cone_add(
        vertices=128, radius1=0.80, radius2=0.60, depth=0.82
    )
    neck = bpy.context.object
    neck.name = "TYTO · smoothly flared tail"
    move(neck, coll)
    neck.parent = root
    neck.location = (0.0, 0.0, -0.58)
    neck.data.materials.append(bronze)
    bevel = neck.modifiers.new("Soft fillets", "BEVEL")
    bevel.width = 0.090
    bevel.segments = 6
    for poly in neck.data.polygons:
        poly.use_smooth = True

    depth = 0.44
    ring = annular_cylinder(
        "TYTO · diamond-knurled ring", 0.66, 0.55, depth, coll, ring_bronze
    )
    ring.parent = root
    front_z = depth * 0.5
    bpy.ops.mesh.primitive_torus_add(
        major_segments=192, minor_segments=16,
        major_radius=0.605, minor_radius=0.020,
        location=(0.0, 0.0, front_z + 0.014),
    )
    lip = bpy.context.object
    lip.name = "TYTO · polished front lip"
    move(lip, coll)
    lip.parent = root
    lip.data.materials.append(ring_bronze)
    for poly in lip.data.polygons:
        poly.use_smooth = True

    bpy.ops.mesh.primitive_circle_add(
        vertices=192, radius=0.535, fill_type="NGON",
        location=(0.0, 0.0, 0.090),
    )
    grille = bpy.context.object
    grille.name = "TYTO · woven mic grille"
    move(grille, coll)
    grille.parent = root
    grille.data.materials.append(grille_mat)
    solid = grille.modifiers.new("Mesh thickness", "SOLIDIFY")
    solid.thickness = 0.006
    solid.offset = 0.0
    knurl_wire = simple_metal_material(
        "TYTO · knurl micro-reflections", (0.56, 0.35, 0.18, 1.0), 1.0, 0.18
    )
    mesh_wire = simple_metal_material(
        "TYTO · woven grille wires", (0.24, 0.225, 0.21, 1.0), 0.70, 0.35
    )
    knurl_geometry(
        "TYTO · real diamond knurl", 0.664, depth, coll, knurl_wire, root
    )
    grille_grid(
        "TYTO · real woven grid", 0.525, coll, mesh_wire, root, z=0.096
    )

    world_up = Vector((0.0, 0.0, 1.0))
    up = (world_up - axis * world_up.dot(axis)).normalized()
    local_up = base_quat.inverted() @ up
    a = math.atan2(local_up.y, local_up.x)
    z_tick = front_z + 0.020
    inner = Vector((0.580 * math.cos(a), 0.580 * math.sin(a), z_tick))
    outer = Vector((0.650 * math.cos(a), 0.650 * math.sin(a), z_tick))
    curve_object(
        "TYTO · amber ring tick", [tuple(inner), tuple(outer)], coll,
        tick_mat, 0.012, parent=root
    )
    tick_world = mouth_center + base_quat @ inner

    # Gently arc the LED from the shell to the ring tick.
    last = Vector(led_points[-1])
    connector = []
    for i in range(1, 10):
        u = i / 9.0
        p = last.lerp(tick_world, u)
        p.y -= 0.080 * math.sin(math.pi * u)
        connector.append(tuple(p))
    curve_object(
        "TYTO · groove to ring tick",
        [(px, py + 0.006, pz) for px, py, pz in connector],
        coll, soft, 0.018
    )
    full_led = led_points + connector
    led_curve = curve_object(
        "TYTO · animated amber spiral LED", full_led, coll, led_mat, 0.012
    )
    # Remove the earlier short LED curve; the full spline replaces it.
    for obj in tuple(coll.objects):
        if obj.name.startswith("TYTO · animated amber spiral LED") and obj != led_curve:
            bpy.data.objects.remove(obj, do_unlink=True)
    return root, base_quat, grille, led_curve, tick_mat


def build_cyclorama(coll, material):
    xs = [-10.0, -5.0, 0.0, 5.0, 10.0]
    cross = []
    for i in range(48):
        cross.append((-8.0 + 9.2 * i / 47.0, 0.0))
    for i in range(1, 49):
        a = 0.5 * math.pi * i / 48.0
        cross.append((1.2 + 1.8 * math.sin(a), 1.8 * (1.0 - math.cos(a))))
    for i in range(1, 18):
        cross.append((3.0, 1.8 + 0.45 * i))
    verts = []
    for y, z in cross:
        for x in xs:
            verts.append((x, y, z))
    faces = []
    nx = len(xs)
    for i in range(len(cross) - 1):
        for j in range(nx - 1):
            a = i * nx + j
            faces.append((a, a + 1, (i + 1) * nx + j + 1, (i + 1) * nx + j))
    obj = mesh_object("Studio · seamless cyclorama", verts, faces,
                      coll, material, smooth=True)
    sub = obj.modifiers.new("Smooth seamless sweep", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 2
    return obj


def add_area(name, loc, target, energy, size, coll,
             shape="DISK", size_y=1.0, colour=(1.0, 1.0, 1.0)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = colour
    data.shape = shape
    data.size = size
    if shape == "RECTANGLE":
        data.size_y = size_y
    obj = bpy.data.objects.new(name, data)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def studio(scene, coll, backdrop, focus):
    build_cyclorama(coll, backdrop)
    add_area("Key · large upper-left softbox", (-4.6, -4.6, 6.5), focus,
             1250.0, 5.0, coll, colour=(1.0, 0.94, 0.88))
    add_area("Rim · rear-right strip", (4.8, 3.6, 4.2), focus,
             900.0, 0.25, coll, "RECTANGLE", 4.2, (0.88, 0.93, 1.0))
    add_area("Fill · gentle bounce", (-3.2, 2.6, 3.0), focus,
             300.0, 4.0, coll, colour=(0.96, 0.94, 0.92))
    add_area("Top · rolling highlight", (-0.8, -0.4, 6.2), focus,
             260.0, 0.35, coll, "RECTANGLE", 5.0, (1.0, 0.97, 0.93))
    add_area("Front · soft shaping card", (-2.2, -6.0, 3.2), focus,
             180.0, 3.0, coll, colour=(1.0, 0.96, 0.92))
    world = scene.world or bpy.data.worlds.new("TYTO warm-grey studio")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is None:
        bg = world.node_tree.nodes.new("ShaderNodeBackground")
    wo = world.node_tree.nodes.get("World Output")
    if wo:
        world.node_tree.links.new(bg.outputs["Background"], wo.inputs["Surface"])
    bg.inputs["Color"].default_value = (0.085, 0.078, 0.072, 1.0)
    bg.inputs["Strength"].default_value = 0.22


def camera(scene, coll, focus):
    target = bpy.data.objects.new("Camera · spiral/ring focus", None)
    target.empty_display_type = "SPHERE"
    target.empty_display_size = 0.12
    coll.objects.link(target)
    target.location = focus
    orbit = bpy.data.objects.new("Camera · slow orbit rig", None)
    orbit.empty_display_type = "CIRCLE"
    orbit.empty_display_size = 0.5
    coll.objects.link(orbit)
    orbit.location = focus
    data = bpy.data.cameras.new("TYTO · 85 mm macro")
    data.lens = 85.0
    data.sensor_width = 36.0
    data.clip_end = 100.0
    data.dof.use_dof = True
    data.dof.focus_object = target
    data.dof.aperture_fstop = 5.6
    data.dof.aperture_blades = 9
    cam = bpy.data.objects.new("TYTO · hero camera", data)
    coll.objects.link(cam)
    cam.parent = orbit
    cam.location = Vector((7.4, -11.0, 5.10)) - Vector(focus)
    con = cam.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    scene.camera = cam
    return cam, orbit


def compositor(scene):
    scene.use_nodes = True
    t = scene.node_tree
    t.nodes.clear()
    rl = t.nodes.new("CompositorNodeRLayers")
    glare = t.nodes.new("CompositorNodeGlare")
    if hasattr(glare, "glare_type"):
        glare.glare_type = "FOG_GLOW"
    if hasattr(glare, "threshold"):
        glare.threshold = 3.0
    if hasattr(glare, "quality"):
        glare.quality = "HIGH"
    if hasattr(glare, "size"):
        glare.size = 6
    if hasattr(glare, "mix"):
        glare.mix = 0.0
    comp = t.nodes.new("CompositorNodeComposite")
    t.links.new(output(rl, "Image"), socket(glare, "Image"))
    t.links.new(output(glare, "Image"), socket(comp, "Image"))
    scene.render.use_compositing = True


def linearize(owner):
    try:
        ad = owner.animation_data
        if ad and ad.action:
            for fc in ad.action.fcurves:
                for k in fc.keyframe_points:
                    k.interpolation = "LINEAR"
    except Exception:
        pass


def animate(scene, cam, orbit, root, base_quat, grille, led_curve,
            tick_mat, start, end):
    scene.frame_start = start
    scene.frame_end = max(start + 1, end)
    scene.render.fps = 24
    duration = scene.frame_end - start
    led_start = start + int(duration * 0.17)
    led_end = start + int(duration * 0.62)
    ring_start = start + int(duration * 0.36)
    ring_end = start + int(duration * 0.67)

    orbit.rotation_euler = (0.0, 0.0, -0.10)
    orbit.keyframe_insert(data_path="rotation_euler", frame=start)
    orbit.rotation_euler = (0.0, 0.0, 0.10)
    orbit.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)
    cam.location = Vector((7.4, -11.0, 5.10)) - orbit.location
    cam.keyframe_insert(data_path="location", frame=start)
    cam.location = Vector((7.0, -10.4, 4.90)) - orbit.location
    cam.keyframe_insert(data_path="location", frame=scene.frame_end)
    cam.data.lens = 85.0
    cam.data.keyframe_insert(data_path="lens", frame=start)
    cam.data.lens = 95.0
    cam.data.keyframe_insert(data_path="lens", frame=scene.frame_end)

    data = led_curve.data
    data.bevel_factor_start = 0.0
    data.bevel_factor_end = 0.0
    data.keyframe_insert(data_path="bevel_factor_end", frame=start)
    data.keyframe_insert(data_path="bevel_factor_end", frame=led_start)
    data.bevel_factor_end = 1.0
    data.keyframe_insert(data_path="bevel_factor_end", frame=led_end)
    data.keyframe_insert(data_path="bevel_factor_end", frame=scene.frame_end)
    for f, angle in ((start, -0.040), (ring_start, -0.040),
                     (ring_end, 0.040), (scene.frame_end, 0.040)):
        root.rotation_quaternion = base_quat @ Quaternion((0.0, 0.0, 1.0), angle)
        root.keyframe_insert(data_path="rotation_quaternion", frame=f)
    for f, z in ((start, -0.16), (ring_start, -0.16),
                 (ring_end, 0.10), (scene.frame_end, 0.10)):
        grille.location = (0.0, 0.0, z)
        grille.keyframe_insert(data_path="location", frame=f)
    try:
        strength = tick_mat.node_tree.nodes["Emission"].inputs["Strength"]
        strength.default_value = 0.0
        strength.keyframe_insert(data_path="default_value", frame=start)
        strength.keyframe_insert(data_path="default_value", frame=max(start, led_end - 6))
        strength.default_value = 8.0
        strength.keyframe_insert(data_path="default_value", frame=min(scene.frame_end, led_end + 8))
    except Exception:
        pass
    for owner in (orbit, cam, root, grille, data, tick_mat):
        linearize(owner)


def render_settings(scene, args):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = min(args.samples, 64) if args.draft else args.samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.max_bounces = 8
    if hasattr(scene.cycles, "use_light_tree"):
        scene.cycles.use_light_tree = True
    if hasattr(scene.view_layers[0], "cycles"):
        scene.view_layers[0].cycles.use_denoising = True
    if args.draft:
        scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    elif args.ultra:
        scene.render.resolution_x, scene.render.resolution_y = 7680, 4320
    else:
        scene.render.resolution_x, scene.render.resolution_y = 3840, 2160
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "16"
    scene.render.image_settings.file_format = "PNG"
    scene.render.threads_mode = "AUTO"
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "Medium High Contrast"
    except Exception:
        try:
            scene.view_settings.view_transform = "Filmic"
        except Exception:
            pass
    compositor(scene)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for blocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                   bpy.data.cameras, bpy.data.lights, bpy.data.metaballs):
        for block in tuple(blocks):
            if block.users == 0:
                blocks.remove(block)


def build_scene(args):
    scene = bpy.context.scene
    clear_scene()
    product = collection(scene, "TYTO · product assembly")
    studio_coll = collection(scene, "TYTO · virtual studio")
    bronze = bronze_material()
    soft = soft_touch_material()
    ring_bronze = knurled_bronze_material()
    grille_mat = woven_grille_material()
    led_mat, _ = emission_material("TYTO · amber spiral emission",
                                   (1.0, 0.38, 0.060, 1.0), 10.0)
    tick_mat, _ = emission_material("TYTO · amber tick emission",
                                    (1.0, 0.44, 0.09, 1.0), 8.0)
    backdrop = backdrop_material()

    body, min_z, max_z = build_shell(product, bronze)
    front_y, led_points, _short_led = build_spiral_details(
        body, min_z, max_z, product, bronze, soft, led_mat
    )
    root, base_quat, grille, led_curve, tick_mat = build_mouth(
        front_y, product, bronze, ring_bronze, grille_mat,
        soft, led_mat, tick_mat, led_points
    )
    focus = Vector((0.30, -0.05, 1.08))
    studio(scene, studio_coll, backdrop, focus)
    cam, orbit = camera(scene, studio_coll, focus)
    animate(scene, cam, orbit, root, base_quat, grille, led_curve,
            tick_mat, args.start, args.end)
    render_settings(scene, args)
    return scene


def main():
    args = parse_args()
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    if hasattr(bpy.context.preferences.filepaths, "save_version"):
        bpy.context.preferences.filepaths.save_version = 0
    scene = build_scene(args)
    scene.frame_set(args.frame)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print("Saved", BLEND_PATH)
    if args.still:
        scene.frame_set(args.frame)
        scene.render.filepath = str(RENDER_DIR / "tyto_still.png")
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)
    if args.animate:
        scene.frame_set(args.start)
        if args.video:
            scene.render.image_settings.file_format = "FFMPEG"
            scene.render.ffmpeg.format = "MPEG4"
            scene.render.ffmpeg.codec = "H264"
            scene.render.ffmpeg.constant_rate_factor = "HIGH"
            scene.render.ffmpeg.audio_codec = "NONE"
            scene.render.filepath = str(RENDER_DIR / "tyto_orbit.mp4")
        else:
            scene.render.image_settings.file_format = "PNG"
            scene.render.filepath = str(RENDER_DIR / "tyto_frame_")
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
