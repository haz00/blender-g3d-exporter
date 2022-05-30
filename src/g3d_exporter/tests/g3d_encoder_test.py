# <pep8 compliant>

from ..model import *
import g3dj_encoder
import g3db_encoder
import simpleubjson

"""
tests available only within blender context, 
because they create blender structures such as Matrix, Vector etc.
"""


def _build_model() -> G3dModel:

    model = G3dModel()

    mesh = GMesh([
        GVertexAttribute('POS', 3),
        GVertexAttribute('NORM', 3),
        GVertexAttribute('UV', 2)
    ])
    model.meshes.append(mesh)

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
        model.materials.append(mat)
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
        model.nodes.append(node)
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
        model.animations.append(anim)

        for j in range(2):
            bone = GBoneAnimation('bone')
            bone.keyframes = [
                GBoneKeyframe(0, Matrix.Identity(4)),
                GBoneKeyframe(1, Matrix.Identity(4)),
                GBoneKeyframe(2, Matrix.Identity(4)),
            ]
            anim.bones.append(bone)

    return model


def test_g3dj():
    print(g3dj_encoder.encode(_build_model()))


def test_g3db():
    data = g3db_encoder.encode(_build_model())
    simpleubjson.pprint(data)


def test_shapes():
    model = G3dModel()

    for i in range(2):
        shape = GShape(f'mesh{i}', None)
        model.shapes.append(shape)

        for j in range(2):
            key = GShapeKey(f'key{j}', None)
            key.positions = [
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
            ]
            shape.keys.append(key)

    print(g3dj_encoder.encode({"shapes": model.shapes}))
