# <pep8 compliant>

import json

from domain import *
import g3dj_encoder
import g3db_encoder
import simpleubjson

"""
tests available only within blender context, 
because they create blender structures such as Matrix, Vector etc.
"""

def _build_g3d() -> G3D:

    g3d = G3D()

    mesh = GMesh([
        GVertexAttribute('POS', 3),
        GVertexAttribute('NORM', 3),
        GVertexAttribute('UV', 2)
    ])
    g3d.meshes.append(mesh)

    for i in range(2):
        part = GMeshPart(f"_part{i}", 'TRIANGLE')
        mesh.parts.append(part)
        part.indices = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        mesh.vertices = [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0],
        ]

    for i in range(2):
        mat = GMaterial(f"mat{i}", i)
        g3d.materials.append(mat)
        mat.diffuse = [0.0, 0.0, 0.0]
        mat.ambient = mat.diffuse
        mat.emissive = mat.diffuse
        mat.opacity = 0.0
        mat.reflection = mat.diffuse
        mat.shininess = 0.0
        mat.specular = mat.diffuse
        mat.textures = [
            GTexture("tex0", "TYPE", "filename.jpeg"),
            GTexture("tex0", "TYPE", "filename.jpeg"),
        ]

    for i in range(2):
        node = GNode(f"node{i}", None)
        g3d.nodes.append(node)
        for j in range(2):
            part = GNodePart('mat', 'mesh')
            node.parts.append(part)
            part.bones = [
                GBoneMatrix('node', i, Matrix.Identity(4)),
                GBoneMatrix('node', i, Matrix.Identity(4)),
            ]

        for q in range(2):
            child = GNode(f"child{q}", None)
            node.children.append(child)
            for j in range(2):
                part = GNodePart('mat', 'mesh')
                child.parts.append(part)
                part.bones = [
                    GBoneMatrix('node', i, Matrix.Identity(4)),
                    GBoneMatrix('node', i, Matrix.Identity(4)),
                ]

    for i in range(2):
        anim = GAnimation(f'anim{i}')
        g3d.animations.append(anim)

        for j in range(2):
            bone = GBoneAnimation('bone')
            bone.keyframes = [
                GBoneKeyframe(0, Matrix.Identity(4)),
                GBoneKeyframe(1, Matrix.Identity(4)),
                GBoneKeyframe(2, Matrix.Identity(4)),
            ]
            anim.bones.append(bone)

    return g3d


def test_g3dj():
    print(g3dj_encoder.encode(_build_g3d()))


def test_g3db():    
    data = g3db_encoder.encode(_build_g3d())
    simpleubjson.pprint(data)


def test_shapes():
    g3d = G3D()

    for i in range(2):
        shape = GShape(f'mesh{i}', None)
        g3d.shapes.append(shape)

        for j in range(2):
            key = GShapeKey(f'key{j}', None)
            key.positions = [
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
            ]
            shape.keys.append(key)

    print(g3dj_encoder.encode({"shapes": g3d.shapes}))
