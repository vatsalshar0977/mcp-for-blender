#!/usr/bin/env python3
"""Build a procedural TYTO product-film scene in Blender 4.x.

Usage from the repository root:

    blender --background --python tyto-product/blender/build_tyto.py -- --save
    blender --background --python tyto-product/blender/build_tyto.py -- --still --samples 512
    blender --background --python tyto-product/blender/build_tyto.py -- --animate --draft --video

The shell is a look-development proxy, not manufacturing CAD. Replace it with a
STEP assembly for a final commercial film while retaining the look, studio,
camera and compositing setup.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
RENDER_DIR = ROOT / "renders" / "blender"
BLEND_PATH = ROOT / "blender" / "tyto_scene.blend"

# Logarithmic spiral defining the shell centreline. The final angle places the
# tail to the right/front of the frame, where the cylindrical mouth sits.
R_IN = 0.22
R_OUT = 2.60
TURNS = 1.55
FINAL_ANGLE = -0.45
PHASE = FINAL_ANGLE + TURNS * 2.0 * math.pi


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Build and render the TYTO scene")
    parser.add_argument("--save", action="store_true", help="build and save the .blend file")
    parser.add_argument("--still", action="store_true", help="render one still frame")
    parser.add_argument("--animate", action="store_true", help="render the animation")
    parser.add_argument("--video", action="store_true", help="write H.264 instead of PNG frames")
    parser.add_argument("--draft", action="store_true", help="use 1920x1080 and at most 64 samples")
    parser.add_argument("--ultra", action="store_true", help="use 7680x4320 for an 8K still")
    parser.add_argument("--samples", type=int, default=256, help="Cycles samples")
    parser.add_argument("--frame", type=int, default=170, help="frame for --still")
    parser.add_argument("--start", type=int, default=1, help="animation start frame")
    parser.add_argument("--end", type=int, default=240, help="animation end frame")
    return parser.parse_args(argv)


def set_input(node, name: str, value) -> None:
    """Set a shader-node input only when that Blender version exposes it."""
    if name in node.inputs:
        node.inputs[name].default_value = value


def socket(node, name: str, fallback_index: int = 0):
    return node.inputs.get(name) if name in node.inputs else node.inputs[fallback_index]


def output(node, name: str, fallback_index: int = 0):
    return node.outputs.get(name) if name in node.outputs else node.outputs[fallback_index]


def make_collection(scene, name: str):
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    return collection


def move_to_collection(obj, collection) -> None:
    for current in tuple(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def new_material(name: str):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output_node = tree.nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (620, 0)
    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (340, 0)
    tree.links.new(output(bsdf, "BSDF"), socket(output_node, "Surface"))
    return material, tree, bsdf


def bronze_material():
    material, tree, bsdf = new_material("TYTO · bead-blasted dark bronze")
    set_input(bsdf, "Base Color", (0.145, 0.086, 0.049, 1.0))
    set_input(bsdf, "Metallic", 1.0)
    set_input(bsdf, "Roughness", 0.34)
    set_input(bsdf, "Anisotropic", 0.12)

    noise = tree.nodes.new("ShaderNodeTexNoise")
    noise.location = (-620, 80)
    set_input(noise, "Scale", 210.0)
    set_input(noise, "Detail", 2.0)
    set_input(noise, "Roughness", 0.65)

    roughness_range = tree.nodes.new("ShaderNodeMapRange")
    roughness_range.location = (-350, 100)
    set_input(roughness_range, "From Min", 0.0)
    set_input(roughness_range, "From Max", 1.0)
    set_input(roughness_range, "To Min", 0.29)
    set_input(roughness_range, "To Max", 0.39)
    tree.links.new(output(noise, "Fac"), socket(roughness_range, "Value"))
    tree.links.new(output(roughness_range, "Result"), socket(bsdf, "Roughness"))

    bump = tree.nodes.new("ShaderNodeBump")
    bump.location = (-60, -180)
    set_input(bump, "Strength", 0.055)
    set_input(bump, "Distance", 0.006)
    tree.links.new(output(noise, "Fac"), socket(bump, "Height"))
    tree.links.new(output(bump, "Normal"), socket(bsdf, "Normal"))
    material.diffuse_color = (0.145, 0.086, 0.049, 1.0)
    return material


def soft_touch_material():
    material, tree, bsdf = new_material("TYTO · matte black soft-touch")
    set_input(bsdf, "Base Color", (0.017, 0.016, 0.015, 1.0))
    set_input(bsdf, "Metallic", 0.0)
    set_input(bsdf, "Roughness", 0.64)
    set_input(bsdf, "Sheen Weight", 0.12)
    set_input(bsdf, "Sheen Roughness", 0.7)

    noise = tree.nodes.new("ShaderNodeTexNoise")
    set_input(noise, "Scale", 95.0)
    set_input(noise, "Detail", 2.0)
    bump = tree.nodes.new("ShaderNodeBump")
    set_input(bump, "Strength", 0.08)
    set_input(bump, "Distance", 0.004)
    tree.links.new(output(noise, "Fac"), socket(bump, "Height"))
    tree.links.new(output(bump, "Normal"), socket(bsdf, "Normal"))
    return material


def configure_wave(wave, direction: str, scale: float) -> None:
    if hasattr(wave, "wave_type"):
        wave.wave_type = "BANDS"
    if hasattr(wave, "bands_direction"):
        wave.bands_direction = direction
    if hasattr(wave, "wave_profile"):
        wave.wave_profile = "SIN"
    set_input(wave, "Scale", scale)
    set_input(wave, "Distortion", 0.0)
    set_input(wave, "Detail", 0.0)
    set_input(wave, "Detail Scale", 1.0)


def knurled_bronze_material():
    material, tree, bsdf = new_material("TYTO · diamond-knurled bronze")
    set_input(bsdf, "Metallic", 1.0)
    set_input(bsdf, "Roughness", 0.27)
    set_input(bsdf, "Anisotropic", 0.18)

    texcoord = tree.nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-920, 0)
    mapping_a = tree.nodes.new("ShaderNodeMapping")
    mapping_b = tree.nodes.new("ShaderNodeMapping")
    mapping_a.location = (-720, 160)
    mapping_b.location = (-720, -160)
    set_input(mapping_a, "Rotation", (0.0, 0.0, math.radians(45.0)))
    set_input(mapping_b, "Rotation", (0.0, 0.0, math.radians(-45.0)))
    tree.links.new(output(texcoord, "Object"), socket(mapping_a, "Vector"))
    tree.links.new(output(texcoord, "Object"), socket(mapping_b, "Vector"))

    wave_a = tree.nodes.new("ShaderNodeTexWave")
    wave_b = tree.nodes.new("ShaderNodeTexWave")
    wave_a.location = (-500, 170)
    wave_b.location = (-500, -160)
    configure_wave(wave_a, "X", 185.0)
    configure_wave(wave_b, "X", 185.0)
    tree.links.new(output(mapping_a, "Vector"), socket(wave_a, "Vector"))
    tree.links.new(output(mapping_b, "Vector"), socket(wave_b, "Vector"))

    maximum = tree.nodes.new("ShaderNodeMath")
    maximum.operation = "MAXIMUM"
    maximum.location = (-270, 20)
    tree.links.new(output(wave_a, "Fac"), maximum.inputs[0])
    tree.links.new(output(wave_b, "Fac"), maximum.inputs[1])

    ramp = tree.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-70, 20)
    ramp.color_ramp.elements[0].position = 0.38
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    tree.links.new(maximum.outputs[0], socket(ramp, "Fac"))

    colour_mix = tree.nodes.new("ShaderNodeMixRGB")
    colour_mix.location = (120, 150)
    colour_mix.inputs[1].default_value = (0.19, 0.105, 0.055, 1.0)
    colour_mix.inputs[2].default_value = (0.34, 0.205, 0.105, 1.0)
    tree.links.new(output(ramp, "Color"), colour_mix.inputs[0])
    tree.links.new(output(colour_mix, "Color"), socket(bsdf, "Base Color"))

    bump = tree.nodes.new("ShaderNodeBump")
    bump.location = (120, -170)
    set_input(bump, "Strength", 0.32)
    set_input(bump, "Distance", 0.012)
    tree.links.new(output(ramp, "Color"), socket(bump, "Height"))
    tree.links.new(output(bump, "Normal"), socket(bsdf, "Normal"))
    return material


def woven_grille_material():
    material, tree, bsdf = new_material("TYTO · woven black mic mesh")
    set_input(bsdf, "Metallic", 0.12)
    set_input(bsdf, "Roughness", 0.72)
    set_input(bsdf, "Sheen Weight", 0.08)

    texcoord = tree.nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-820, 0)
    wave_x = tree.nodes.new("ShaderNodeTexWave")
    wave_y = tree.nodes.new("ShaderNodeTexWave")
    wave_x.location = (-610, 140)
    wave_y.location = (-610, -140)
    configure_wave(wave_x, "X", 155.0)
    configure_wave(wave_y, "Y", 163.0)
    tree.links.new(output(texcoord, "Object"), socket(wave_x, "Vector"))
    tree.links.new(output(texcoord, "Object"), socket(wave_y, "Vector"))

    multiply = tree.nodes.new("ShaderNodeMath")
    multiply.operation = "MULTIPLY"
    multiply.location = (-380, 0)
    tree.links.new(output(wave_x, "Fac"), multiply.inputs[0])
    tree.links.new(output(wave_y, "Fac"), multiply.inputs[1])

    ramp = tree.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-170, 0)
    ramp.color_ramp.elements[0].position = 0.18
    ramp.color_ramp.elements[0].color = (0.004, 0.004, 0.004, 1.0)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (0.055, 0.052, 0.049, 1.0)
    tree.links.new(multiply.outputs[0], socket(ramp, "Fac"))
    tree.links.new(output(ramp, "Color"), socket(bsdf, "Base Color"))

    bump = tree.nodes.new("ShaderNodeBump")
    bump.location = (90, -160)
    set_input(bump, "Strength", 0.28)
    set_input(bump, "Distance", 0.009)
    tree.links.new(multiply.outputs[0], socket(bump, "Height"))
    tree.links.new(output(bump, "Normal"), socket(bsdf, "Normal"))
    return material


def emission_material(name: str, colour, strength: float):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    emission = tree.nodes.new("ShaderNodeEmission")
    emission.name = "Emission"
    emission.location = (180, 0)
    emission.inputs["Color"].default_value = colour
    emission.inputs["Strength"].default_value = strength
    output_node = tree.nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (420, 0)
    tree.links.new(output(emission, "Emission"), socket(output_node, "Surface"))
    material.diffuse_color = colour
    return material, emission


def backdrop_material():
    material, tree, bsdf = new_material("Studio · warm-grey gradient cyclorama")
    set_input(bsdf, "Metallic", 0.0)
    set_input(bsdf, "Roughness", 0.46)

    geometry = tree.nodes.new("ShaderNodeNewGeometry")
    geometry.location = (-700, 0)
    separate = tree.nodes.new("ShaderNodeSeparateXYZ")
    separate.location = (-500, 0)
    gradient_range = tree.nodes.new("ShaderNodeMapRange")
    gradient_range.location = (-300, 0)
    set_input(gradient_range, "From Min", -8.0)
    set_input(gradient_range, "From Max", 4.0)
    set_input(gradient_range, "To Min", 0.0)
    set_input(gradient_range, "To Max", 1.0)
    ramp = tree.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-80, 0)
    ramp.color_ramp.elements[0].color = (0.031, 0.028, 0.026, 1.0)
    ramp.color_ramp.elements[1].color = (0.086, 0.077, 0.069, 1.0)
    tree.links.new(output(geometry, "Position"), socket(separate, "Vector"))
    tree.links.new(output(separate, "Y"), socket(gradient_range, "Value"))
    tree.links.new(output(gradient_range, "Result"), socket(ramp, "Fac"))
    tree.links.new(output(ramp, "Color"), socket(bsdf, "Base Color"))
    return material


def mesh_object(name, vertices, faces, collection, material=None, smooth=True):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if material is not None:
        mesh.materials.append(material)
    if smooth:
        for polygon in mesh.polygons:
            polygon.use_smooth = True
    return obj


def curve_object(name, coordinates, collection, material, bevel_depth,
                 radii=None, cyclic=False, parent=None, bevel_resolution=4):
    curve = bpy.data.curves.new(name + " Curve", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 24
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = bevel_resolution
    curve.use_fill_caps = True
    if hasattr(curve, "bevel_factor_mapping_end"):
        curve.bevel_factor_mapping_end = "SPLINE"
    spline = curve.splines.new("POLY")
    spline.points.add(max(0, len(coordinates) - 1))
    spline.use_cyclic_u = cyclic
    for index, coordinate in enumerate(coordinates):
        point = spline.points[index]
        point.co = (coordinate[0], coordinate[1], coordinate[2], 1.0)
        point.radius = radii[index] if radii else 1.0
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    if material is not None:
        curve.materials.append(material)
    if parent is not None:
        obj.parent = parent
    return obj


def spiral_xy(t: float):
    radius = R_IN * (R_OUT / R_IN) ** t
    angle = PHASE - TURNS * 2.0 * math.pi * t
    return radius * math.cos(angle), radius * math.sin(angle), radius, angle


def spiral_frame(t: float):
    dt = 0.001
    x0, y0, _, _ = spiral_xy(max(0.0, t - dt))
    x1, y1, _, _ = spiral_xy(min(1.0, t + dt))
    tangent = Vector((x1 - x0, y1 - y0, 0.0))
    if tangent.length < 1e-6:
        tangent = Vector((1.0, 0.0, 0.0))
    tangent.normalize()
    normal = Vector((-tangent.y, tangent.x, 0.0))
    return tangent, normal


def build_shell(collection, bronze):
    coordinates = []
    radii = []
    count = 300
    for index in range(count):
        t = index / (count - 1)
        x, y, radius, _ = spiral_xy(t)
        z = 0.26 + 0.34 * t + 0.035 * math.sin(4.0 * math.pi * t)
        coordinates.append((x, y, z))
        radii.append(min(0.90, 0.55 * radius + 0.16))

    shell_curve = curve_object(
        "TYTO · shell volume source",
        coordinates,
        collection,
        bronze,
        bevel_depth=1.0,
        radii=radii,
        bevel_resolution=5,
    )
    bpy.ops.object.select_all(action="DESELECT")
    shell_curve.select_set(True)
    bpy.context.view_layer.objects.active = shell_curve
    bpy.ops.object.convert(target="MESH")
    body = bpy.context.object
    body.name = "TYTO · rounded nautilus shell"

    remesh = body.modifiers.new("Voxel-weld overlapping coils", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = 0.045
    if hasattr(remesh, "use_smooth_shade"):
        remesh.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier=remesh.name)

    relax = body.modifiers.new("Relax voxel surface", "SMOOTH")
    relax.factor = 0.9
    relax.iterations = 4
    bpy.ops.object.modifier_apply(modifier=relax.name)

    subdiv = body.modifiers.new("Pebble fillets", "SUBSURF")
    subdiv.levels = 1
    subdiv.render_levels = 2

    body.scale.z = 0.78
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    min_z = min(vertex.co.z for vertex in body.data.vertices)
    body.location.z = -min_z + 0.025
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    bpy.context.view_layer.update()

    min_z = min(vertex.co.z for vertex in body.data.vertices)
    max_z = max(vertex.co.z for vertex in body.data.vertices)
    return body, min_z, max_z


def make_surface_sampler(body, fallback_z: float):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)

    def surface_z(x: float, y: float, offset: float = 0.0) -> float:
        hit, location, _normal, _index = evaluated.ray_cast(
            Vector((x, y, 4.0)), Vector((0.0, 0.0, -1.0)), distance=8.0
        )
        return (location.z if hit else fallback_z) + offset

    return surface_z, evaluated


def make_ribbon(name, points, width_function, collection, material, surface_z):
    vertices = []
    faces = []
    for index, (x, y, _z) in enumerate(points):
        u = index / max(1, len(points) - 1)
        _tangent, normal = spiral_frame(0.06 + 0.87 * u)
        half_width = width_function(u) * 0.5
        ax, ay = x + normal.x * half_width, y + normal.y * half_width
        bx, by = x - normal.x * half_width, y - normal.y * half_width
        vertices.append((ax, ay, surface_z(ax, ay, 0.014)))
        vertices.append((bx, by, surface_z(bx, by, 0.014)))
    for index in range(len(points) - 1):
        a = 2 * index
        faces.append((a, a + 1, a + 3, a + 2))
    return mesh_object(name, vertices, faces, collection, material, smooth=True)


def build_spiral_details(body, fallback_z, collection, bronze, soft_touch,
                         led_material):
    surface_z, evaluated = make_surface_sampler(body, fallback_z)
    channel_points = []
    groove_points = []
    led_points = []
    count = 190
    for index in range(count):
        u = index / (count - 1)
        t = 0.06 + 0.87 * u
        x, y, _r, _a = spiral_xy(t)
        _tangent, normal = spiral_frame(t)
        channel_points.append((x, y, surface_z(x, y)))
        offset = 0.17 + 0.055 * u
        gx, gy = x + normal.x * offset, y + normal.y * offset
        groove_points.append((gx, gy, surface_z(gx, gy, 0.027)))
        led_points.append((gx, gy, surface_z(gx, gy, 0.034)))

    make_ribbon(
        "TYTO · matte spiral channel",
        channel_points,
        lambda u: 0.31 + 0.10 * u,
        collection,
        soft_touch,
        surface_z,
    )
    groove = curve_object(
        "TYTO · recessed LED groove",
        groove_points,
        collection,
        soft_touch,
        bevel_depth=0.025,
        bevel_resolution=4,
    )

    # A small raised bronze spiral forms the centre eye.
    eye_points = []
    eye_radii = []
    for index in range(90):
        u = index / 89.0
        angle = 2.35 * math.pi * u + 0.35
        radius = 0.025 + 0.33 * u
        x, y = radius * math.cos(angle), radius * math.sin(angle)
        eye_points.append((x, y, surface_z(x, y, 0.075 + 0.025 * u)))
        eye_radii.append(0.38 + 0.62 * u)
    curve_object(
        "TYTO · raised spiral eye",
        eye_points,
        collection,
        bronze,
        bevel_depth=0.085,
        radii=eye_radii,
        bevel_resolution=4,
    )

    # A radial ray-cast places a fine closed seam on the lower side wall.
    seam_z = min(fallback_z * 0.45, 0.42)
    seam_points = []
    for index in range(180):
        angle = 2.0 * math.pi * index / 180.0
        direction = Vector((math.cos(angle), math.sin(angle), 0.0))
        origin = direction * 5.0 + Vector((0.0, 0.0, seam_z))
        hit, location, normal, _index = evaluated.ray_cast(
            origin, -direction, distance=8.0
        )
        if hit:
            point = location + normal * 0.008
            seam_points.append(tuple(point))
        else:
            seam_points.append((direction.x * 1.85, direction.y * 1.55, seam_z))
    curve_object(
        "TYTO · lower parting seam",
        seam_points,
        collection,
        soft_touch,
        bevel_depth=0.006,
        cyclic=True,
        bevel_resolution=3,
    )
    return surface_z, led_points, groove


def annular_cylinder(name, outer_radius, inner_radius, depth, collection,
                     material, segments=160):
    vertices = []
    for z in (depth * 0.5, -depth * 0.5):
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            vertices.append((outer_radius * math.cos(angle),
                             outer_radius * math.sin(angle), z))
    for z in (depth * 0.5, -depth * 0.5):
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            vertices.append((inner_radius * math.cos(angle),
                             inner_radius * math.sin(angle), z))
    faces = []
    n = segments
    for index in range(n):
        j = (index + 1) % n
        faces.append((index, j, n + j, n + index))                       # outer wall
        faces.append((2 * n + index, 3 * n + index, 3 * n + j, 2 * n + j))  # inner wall
        faces.append((index, 2 * n + index, 2 * n + j, j))               # front cap
        faces.append((n + index, n + j, 3 * n + j, 3 * n + index))       # back cap
    obj = mesh_object(name, vertices, faces, collection, material, smooth=True)
    bevel = obj.modifiers.new("Machined 0.1 mm edge bevel", "BEVEL")
    bevel.width = 0.018
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(28.0)
    if hasattr(bevel, "harden_normals"):
        bevel.harden_normals = True
    return obj


def build_mouth(surface_z, collection, bronze, ring_bronze, grille_material,
                led_material, tick_material, led_points):
    x, y, _r, _a = spiral_xy(0.965)
    tail = Vector((x, y, surface_z(x, y, -0.04)))
    axis = Vector((0.70, -0.66, 0.27)).normalized()
    base_quat = Vector((0.0, 0.0, 1.0)).rotation_difference(axis)
    mouth_center = tail + axis * 0.58

    mouth_root = bpy.data.objects.new("TYTO · mouth axis rig", None)
    mouth_root.empty_display_type = "ARROWS"
    mouth_root.empty_display_size = 0.4
    collection.objects.link(mouth_root)
    mouth_root.location = mouth_center
    mouth_root.rotation_mode = "QUATERNION"
    mouth_root.rotation_quaternion = base_quat

    # The flared tail is a separate object so the ring can rotate independently.
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.86, depth=0.95)
    neck = bpy.context.object
    neck.name = "TYTO · flared tail"
    move_to_collection(neck, collection)
    neck.parent = mouth_root
    neck.location = (0.0, 0.0, -0.72)
    neck.data.materials.append(bronze)
    neck_bevel = neck.modifiers.new("Soft tail fillets", "BEVEL")
    neck_bevel.width = 0.07
    neck_bevel.segments = 4
    for polygon in neck.data.polygons:
        polygon.use_smooth = True

    ring_depth = 0.55
    ring = annular_cylinder(
        "TYTO · diamond-knurled ring", 1.02, 0.86, ring_depth,
        collection, ring_bronze
    )
    ring.parent = mouth_root
    ring.location = (0.0, 0.0, 0.0)

    front_z = ring_depth * 0.5
    bpy.ops.mesh.primitive_torus_add(
        major_segments=160,
        minor_segments=16,
        major_radius=0.945,
        minor_radius=0.032,
        location=(0.0, 0.0, front_z + 0.018),
    )
    lip = bpy.context.object
    lip.name = "TYTO · polished front lip"
    move_to_collection(lip, collection)
    lip.parent = mouth_root
    lip.data.materials.append(ring_bronze)
    for polygon in lip.data.polygons:
        polygon.use_smooth = True

    bpy.ops.mesh.primitive_circle_add(
        vertices=160, radius=0.842, fill_type="NGON",
        location=(0.0, 0.0, 0.10),
    )
    grille = bpy.context.object
    grille.name = "TYTO · woven mic grille"
    move_to_collection(grille, collection)
    grille.parent = mouth_root
    grille.data.materials.append(grille_material)
    solidify = grille.modifiers.new("Mesh thickness", "SOLIDIFY")
    solidify.thickness = 0.006
    solidify.offset = 0.0

    # Put the tick at the visually upper point of the ring's local plane.
    world_up = Vector((0.0, 0.0, 1.0))
    up_projected = (world_up - axis * world_up.dot(axis)).normalized()
    local_up = base_quat.inverted() @ up_projected
    tick_angle = math.atan2(local_up.y, local_up.x)
    tick_inner = 0.895
    tick_outer = 1.015
    tick_z = front_z + 0.026
    tick_local_inner = Vector((
        tick_inner * math.cos(tick_angle),
        tick_inner * math.sin(tick_angle),
        tick_z,
    ))
    tick_local_outer = Vector((
        tick_outer * math.cos(tick_angle),
        tick_outer * math.sin(tick_angle),
        tick_z,
    ))
    curve_object(
        "TYTO · amber ring tick",
        [tuple(tick_local_inner), tuple(tick_local_outer)],
        collection,
        tick_material,
        bevel_depth=0.013,
        parent=mouth_root,
        bevel_resolution=4,
    )
    tick_world = mouth_center + base_quat @ tick_local_inner

    # Extend the LED spline from the shell to the ring tick with a gentle arc.
    last = Vector(led_points[-1])
    connector = []
    for index in range(1, 9):
        u = index / 8.0
        point = last.lerp(tick_world, u)
        point.z += 0.055 * math.sin(math.pi * u)
        connector.append(tuple(point))
    full_led_points = led_points + connector
    groove_connector = [(px, py, pz - 0.007) for px, py, pz in connector]

    curve_object(
        "TYTO · groove to ring tick",
        groove_connector,
        collection,
        soft_touch_material(),
        bevel_depth=0.025,
        bevel_resolution=4,
    )
    led_curve = curve_object(
        "TYTO · animated amber spiral LED",
        full_led_points,
        collection,
        led_material,
        bevel_depth=0.010,
        bevel_resolution=4,
    )
    return mouth_root, base_quat, grille, led_curve, tick_material


def build_cyclorama(collection, material):
    cross_section = []
    for index in range(24):
        y = -8.0 + (9.2 * index / 23.0)
        cross_section.append((y, 0.0))
    for index in range(1, 25):
        angle = 0.5 * math.pi * index / 24.0
        y = 1.2 + 1.8 * math.sin(angle)
        z = 1.8 * (1.0 - math.cos(angle))
        cross_section.append((y, z))
    for index in range(1, 10):
        cross_section.append((3.0, 1.8 + 0.75 * index))
    vertices = []
    for y, z in cross_section:
        vertices.append((-10.0, y, z))
        vertices.append((10.0, y, z))
    faces = []
    for index in range(len(cross_section) - 1):
        a = 2 * index
        faces.append((a, a + 1, a + 3, a + 2))
    return mesh_object("Studio · seamless cyclorama", vertices, faces,
                       collection, material, smooth=True)


def add_area(name, location, target, energy, size, collection,
             shape="DISK", size_y=1.0, colour=(1.0, 1.0, 1.0)):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.color = colour
    data.shape = shape
    data.size = size
    if shape == "RECTANGLE":
        data.size_y = size_y
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj


def set_cycles_visibility(obj, **flags) -> None:
    for key, value in flags.items():
        if hasattr(obj, key):
            try:
                setattr(obj, key, value)
            except Exception:
                pass


def build_studio(scene, studio_collection, backdrop, focus_target):
    build_cyclorama(studio_collection, backdrop)

    card_material, _ = emission_material(
        "Studio · reflection card", (1.0, 0.96, 0.91, 1.0), 0.7
    )
    for name, location, scale in (
        ("Studio · left reflection card", (-5.2, -1.0, 3.2), (3.5, 5.0)),
        ("Studio · right reflection card", (3.6, -3.6, 2.1), (2.0, 3.5)),
    ):
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=location)
        card = bpy.context.object
        card.name = name
        move_to_collection(card, studio_collection)
        card.scale = (scale[0], scale[1], 1.0)
        direction = Vector(focus_target) - card.location
        card.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
        card.data.materials.append(card_material)
        set_cycles_visibility(
            card, visible_camera=False, visible_diffuse=False,
            visible_glossy=True, visible_shadow=False
        )

    add_area(
        "Key · large upper-left softbox", (-4.6, -4.2, 7.0), focus_target,
        950.0, 5.0, studio_collection, colour=(1.0, 0.94, 0.88)
    )
    add_area(
        "Rim · rear-right strip", (4.6, 4.0, 4.4), focus_target,
        720.0, 0.25, studio_collection, shape="RECTANGLE", size_y=4.2,
        colour=(0.88, 0.93, 1.0)
    )
    add_area(
        "Fill · gentle left bounce", (-3.2, 3.6, 3.0), focus_target,
        230.0, 4.0, studio_collection, colour=(0.96, 0.94, 0.92)
    )
    add_area(
        "Top · controlled rolling highlight", (-0.8, 0.2, 6.0), focus_target,
        180.0, 0.35, studio_collection, shape="RECTANGLE", size_y=5.0,
        colour=(1.0, 0.97, 0.93)
    )

    world = scene.world or bpy.data.worlds.new("TYTO warm-grey studio")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is None:
        background = world.node_tree.nodes.new("ShaderNodeBackground")
    world_output = world.node_tree.nodes.get("World Output")
    if world_output is not None:
        world.node_tree.links.new(
            background.outputs["Background"], world_output.inputs["Surface"]
        )
    background.inputs["Color"].default_value = (0.075, 0.069, 0.064, 1.0)
    background.inputs["Strength"].default_value = 0.16


def build_camera(scene, studio_collection, focus_target):
    focus = bpy.data.objects.new("Camera · spiral/ring focus", None)
    focus.empty_display_type = "SPHERE"
    focus.empty_display_size = 0.12
    studio_collection.objects.link(focus)
    focus.location = focus_target

    orbit = bpy.data.objects.new("Camera · slow orbit rig", None)
    orbit.empty_display_type = "CIRCLE"
    orbit.empty_display_size = 0.5
    studio_collection.objects.link(orbit)
    orbit.location = focus_target

    camera_data = bpy.data.cameras.new("TYTO · 85 mm macro")
    camera_data.lens = 85.0
    camera_data.sensor_width = 36.0
    camera_data.clip_end = 100.0
    camera_data.dof.use_dof = True
    camera_data.dof.focus_object = focus
    camera_data.dof.aperture_fstop = 5.6
    camera_data.dof.aperture_blades = 9
    camera = bpy.data.objects.new("TYTO · hero camera", camera_data)
    studio_collection.objects.link(camera)
    camera.parent = orbit
    camera.location = Vector((5.6, -7.4, 5.0)) - Vector(focus_target)

    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.target = focus
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    scene.camera = camera
    return camera, orbit, focus


def setup_compositor(scene):
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()
    render_layers = tree.nodes.new("CompositorNodeRLayers")
    render_layers.location = (-360, 0)
    glare = tree.nodes.new("CompositorNodeGlare")
    glare.location = (-60, 0)
    if hasattr(glare, "glare_type"):
        glare.glare_type = "FOG_GLOW"
    if hasattr(glare, "threshold"):
        glare.threshold = 2.0
    if hasattr(glare, "quality"):
        glare.quality = "HIGH"
    if hasattr(glare, "size"):
        glare.size = 7
    if hasattr(glare, "mix"):
        glare.mix = 0.0
    composite = tree.nodes.new("CompositorNodeComposite")
    composite.location = (220, 0)
    tree.links.new(output(render_layers, "Image"), socket(glare, "Image"))
    tree.links.new(output(glare, "Image"), socket(composite, "Image"))
    scene.render.use_compositing = True


def linearize(owner) -> None:
    try:
        animation = owner.animation_data
        if animation and animation.action:
            for fcurve in animation.action.fcurves:
                for key in fcurve.keyframe_points:
                    key.interpolation = "LINEAR"
    except Exception:
        pass


def setup_animation(scene, camera, orbit, mouth_root, base_quat, grille,
                    led_curve, tick_material, start, end):
    from mathutils import Quaternion

    scene.frame_start = start
    scene.frame_end = max(start + 1, end)
    scene.render.fps = 24
    duration = scene.frame_end - start
    led_start = start + int(duration * 0.17)
    led_end = start + int(duration * 0.62)
    ring_start = start + int(duration * 0.36)
    ring_end = start + int(duration * 0.67)

    orbit.rotation_euler = (0.0, 0.0, -0.12)
    orbit.keyframe_insert(data_path="rotation_euler", frame=start)
    orbit.rotation_euler = (0.0, 0.0, 0.12)
    orbit.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)

    camera.location = Vector((5.6, -7.4, 5.0)) - orbit.location
    camera.keyframe_insert(data_path="location", frame=start)
    camera.location = Vector((5.15, -6.9, 4.72)) - orbit.location
    camera.keyframe_insert(data_path="location", frame=scene.frame_end)
    camera.data.lens = 85.0
    camera.data.keyframe_insert(data_path="lens", frame=start)
    camera.data.lens = 95.0
    camera.data.keyframe_insert(data_path="lens", frame=scene.frame_end)

    led_data = led_curve.data
    led_data.bevel_factor_start = 0.0
    led_data.bevel_factor_end = 0.0
    led_data.keyframe_insert(data_path="bevel_factor_end", frame=start)
    led_data.keyframe_insert(data_path="bevel_factor_end", frame=led_start)
    led_data.bevel_factor_end = 1.0
    led_data.keyframe_insert(data_path="bevel_factor_end", frame=led_end)
    led_data.keyframe_insert(data_path="bevel_factor_end", frame=scene.frame_end)

    for frame, angle in (
        (start, -0.045),
        (ring_start, -0.045),
        (ring_end, 0.045),
        (scene.frame_end, 0.045),
    ):
        mouth_root.rotation_quaternion = (
            base_quat @ Quaternion((0.0, 0.0, 1.0), angle)
        )
        mouth_root.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    for frame, z in (
        (start, -0.18),
        (ring_start, -0.18),
        (ring_end, 0.10),
        (scene.frame_end, 0.10),
    ):
        grille.location = (0.0, 0.0, z)
        grille.keyframe_insert(data_path="location", frame=frame)

    try:
        strength = tick_material.node_tree.nodes["Emission"].inputs["Strength"]
        strength.default_value = 0.0
        strength.keyframe_insert(data_path="default_value", frame=start)
        strength.keyframe_insert(data_path="default_value", frame=max(start, led_end - 6))
        strength.default_value = 12.0
        strength.keyframe_insert(data_path="default_value", frame=min(scene.frame_end, led_end + 8))
    except Exception:
        pass

    for owner in (orbit, camera, mouth_root, grille, led_data, tick_material):
        linearize(owner)


def setup_render(scene, args):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = min(args.samples, 64) if args.draft else args.samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.max_bounces = 8
    if hasattr(scene.cycles, "use_light_tree"):
        scene.cycles.use_light_tree = True
    if hasattr(scene.view_layers[0], "cycles") and hasattr(scene.view_layers[0].cycles, "use_denoising"):
        scene.view_layers[0].cycles.use_denoising = True

    if args.draft:
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080
    elif args.ultra:
        scene.render.resolution_x = 7680
        scene.render.resolution_y = 4320
    else:
        scene.render.resolution_x = 3840
        scene.render.resolution_y = 2160
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
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    setup_compositor(scene)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes, bpy.data.curves, bpy.data.materials,
        bpy.data.cameras, bpy.data.lights,
    ):
        for block in tuple(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def build_scene(args):
    scene = bpy.context.scene
    clear_scene()
    product = make_collection(scene, "TYTO · product assembly")
    studio = make_collection(scene, "TYTO · virtual studio")

    bronze = bronze_material()
    soft_touch = soft_touch_material()
    ring_bronze = knurled_bronze_material()
    grille_material = woven_grille_material()
    led_material, _ = emission_material(
        "TYTO · amber spiral emission", (1.0, 0.34, 0.055, 1.0), 11.0
    )
    tick_material, _ = emission_material(
        "TYTO · amber tick emission", (1.0, 0.40, 0.075, 1.0), 12.0
    )
    backdrop = backdrop_material()

    body, min_z, max_z = build_shell(product, bronze)
    fallback_z = min_z + 0.75 * (max_z - min_z)
    surface_z, led_points, _groove = build_spiral_details(
        body, fallback_z, product, bronze, soft_touch, led_material
    )
    mouth_root, base_quat, grille, led_curve, tick_material = build_mouth(
        surface_z, product, bronze, ring_bronze, grille_material,
        led_material, tick_material, led_points
    )
    focus_target = Vector((0.35, -0.22, surface_z(0.20, 0.02, 0.05)))
    build_studio(scene, studio, backdrop, focus_target)
    camera, orbit, _focus = build_camera(scene, studio, focus_target)
    setup_animation(
        scene, camera, orbit, mouth_root, base_quat, grille,
        led_curve, tick_material, args.start, args.end
    )
    setup_render(scene, args)
    return scene, focus_target


def main() -> None:
    args = parse_args()
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    scene, _focus = build_scene(args)
    scene.frame_set(args.frame)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(f"Saved Blender scene: {BLEND_PATH}")

    if args.still:
        scene.frame_set(args.frame)
        scene.render.filepath = str(RENDER_DIR / "tyto_still.png")
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)
        print(f"Rendered still: {scene.render.filepath}")

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
        print(f"Rendered animation to: {scene.render.filepath}")

    if not (args.save or args.still or args.animate):
        print("Built scene only. Use --still or --animate to render.")


if __name__ == "__main__":
    main()
