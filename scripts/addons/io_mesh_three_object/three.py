import uuid
from mathutils import Matrix
from collections import OrderedDict


def create_object(type="Object",
                  version=4.3,
                  generator="Blender Three.js Object Exporter"
                  ):
    '''
    '''
    obj = OrderedDict()

    metadata = obj["metadata"] = OrderedDict()
    metadata["type"] = type
    metadata["version"] = version
    metadata["generator"] = generator

    obj["object"] = None
    obj["materials"] = None
    obj["geometries"] = None

    return obj


def create_object3d(object_name,
                    matrix=Matrix.Identity(4),
                    ):
    '''
    Creates an OrderedDict that represents a THREE.Object3D instance
    '''
    obj = OrderedDict()

    obj["name"] = object_name
    obj["type"] = "Object3D"
    obj["uuid"] = uuid.uuid4()
    obj["matrix"] = matrix
    obj["userData"] = {}
    obj["children"] = []

    return obj


def create_mesh(mesh_name,
                matrix=Matrix.Identity(4),
                geometry_uuid=None,
                material_uuid=None,
                ):

    obj = create_object3d(mesh_name, matrix=matrix)
    obj["type"] = "Mesh"
    obj["geometry"] = geometry_uuid
    obj["material"] = material_uuid

    return obj


def create_buffergeometry(geometry_name,
                          positions,
                          normals,
                          uvs,
                          colors,
                          indices,
                          ):
    '''
    Creates an OrderedDict that represents a THREE.BufferGeometry instance
    '''

    def create_attribute(array, type, itemSize):
        attr = OrderedDict()
        attr["type"] = type
        attr["itemSize"] = itemSize
        attr["array"] = array
        return attr

    obj = OrderedDict()

    obj["name"] = geometry_name
    obj["type"] = "BufferGeometry"
    obj["uuid"] = uuid.uuid4()
    data = obj["data"] = OrderedDict()
    attr = data["attributes"] = OrderedDict()

    if positions:
        attr["position"] = create_attribute(positions, "Float32Array", 3)

    if normals:
        attr["normal"] = create_attribute(normals, "Float32Array", 3)

    if uvs:
        attr["uv"] = create_attribute(uvs, "Float32Array", 2)

    if colors:
        attr["color"] = create_attribute(colors, "Float32Array", 3)

    if indices:
        attr["index"] = create_attribute(indices, "Uint32Array", 1)

    return obj


def create_material(material, material_uuid=uuid.uuid4()):
    '''
    '''

    def color_to_int(color, intensity=1.0):
        '''Converts a blender color object to an integer value'''
        return int(color.r * intensity * 255) << 16 ^ \
            int(color.g * intensity * 255) << 8 ^ \
            int(color.b * intensity * 255)

    obj = OrderedDict()

    obj["name"] = material.name
    obj["type"] = None
    obj["uuid"] = material_uuid

    obj["vertexColors"] = material.use_vertex_color_paint
    obj["transparent"] = bool(material.use_transparency)
    obj["opacity"] = material.alpha if material.use_transparency else 1.0
    obj["color"] = color_to_int(material.diffuse_color,
                                material.diffuse_intensity)

    if material.use_shadeless:

        # MeshBasicMaterial has no further properties to parse
        obj["type"] = "MeshBasicMaterial"

    else:

        # common attributes for Lambert and Phong types
        obj["ambient"] = color_to_int(material.diffuse_color,
                                      material.ambient)
        obj["emissive"] = color_to_int(material.diffuse_color,
                                       material.emit)

        if material.specular_intensity == 0:

            # materials with no specular value are
            # exported as Lambert material type
            obj["type"] = "MeshLambertMaterial"

        else:

            # all other materials are exported as Phong material type
            obj["type"] = "MeshPhongMaterial"
            obj["specular"] = color_to_int(material.specular_color,
                                           material.specular_intensity)
            obj["shininess"] = int(material.specular_hardness / 10)

    return obj
