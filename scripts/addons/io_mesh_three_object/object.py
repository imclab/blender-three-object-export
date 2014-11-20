import bpy
import math
import time
import uuid
from collections import OrderedDict
from mathutils import Matrix
from . import geometry
from . import three
from . import json


global_geometries = []

global_materials = {}

global_scale_matrix = Matrix.Identity(4)

global_rotation_matrix = Matrix.Rotation(-math.pi / 2, 4, "X")


def save_geometry(bm,
                  geometry_name,
                  export_normals=True,
                  export_uvs=True,
                  export_colors=True,
                  export_index=True,
                  ):
    '''
    Saves bmesh data as BufferGeometry in the global geomtries list
    '''

    print("    Creating THREE.BufferGeometry: %s ..." % (geometry_name))

    # get uv layer
    if export_uvs:
        uv_layer = bm.loops.layers.uv.active
        export_uvs = export_uvs and uv_layer

    # get color layer
    if export_colors:
        color_layer = bm.loops.layers.color.active
        export_colors = export_colors and color_layer

    # create vertex data->index map
    if export_index:
        vertex_map = {}

    # vertex attribute arrays
    positions = []
    normals = []
    uvs = []
    colors = []
    indices = []

    # process each face loop to populate the vertex attribute arrays
    for face in bm.faces:
        for loop in face.loops:

            # get current vertex data
            position = loop.vert.co.to_tuple()
            normal = loop.vert.normal.to_tuple() if export_normals else None
            uv = loop[uv_layer].uv.to_tuple() if export_uvs else None
            color = None
            if export_colors:
                color = loop[color_layer]
                color = (color.r, color.g, color.b)

            if export_index:

                # Indexed BufferGeometry

                # check vertex map for matching vertex data
                vertex_key = hash((position, normal, uv, color))
                if vertex_key in vertex_map:

                    # get index of existing vertex key
                    vertex_index = vertex_map[vertex_key]

                else:

                    # get new vertex data index
                    vertex_index = len(vertex_map)
                    vertex_map[vertex_key] = vertex_index

                    # append vertex attribute data
                    positions += position
                    if export_normals:
                        normals += normal
                    if export_uvs:
                        uvs += uv
                    if export_colors:
                        colors += color

                # append vertex index attribute data
                indices.append(vertex_index)

            else:

                # Non-indexed BufferGeometry

                # append vertex attribute data
                positions += position
                if export_normals:
                    normals += normal
                if export_uvs:
                    uvs += uv
                if export_colors:
                    colors += color

    # create BufferGeomtry
    geometry = three.create_buffergeometry(geometry_name,
                                           positions,
                                           normals,
                                           uvs,
                                           colors,
                                           indices
                                           )

    # store in global geom list
    global_geometries.append(geometry)

    return geometry["uuid"]


def save_mesh_object(mesh_object,
                     parent_object,
                     scene,
                     apply_modifiers=True,
                     split_by_material=True,
                     export_normals=True,
                     export_uvs=True,
                     export_colors=True,
                     export_index=True,
                     morph_animation=True,
                     sample_rate=True,
                     ):
    '''
    Saves a mesh object
    '''

    def update_material(material):
        '''
        '''
        if not material:
            material_uuid = None
        elif material in global_materials:
            material_uuid = global_materials[material]
        else:
            material_uuid = uuid.uuid4()
            global_materials[material] = material_uuid
        return material_uuid

    print("  Exporting MESH: %s (%s) ..." %
          (mesh_object.name, mesh_object.data.name))

    # map mesh materials -> geometries
    mesh_map = geometry.map_mesh_object(mesh_object,
                                        scene,
                                        global_rotation_matrix *
                                        global_scale_matrix,
                                        apply_modifiers=apply_modifiers,
                                        split_by_material=split_by_material,
                                        export_normals=export_normals,
                                        )

    num_geometries = len(mesh_map)

    if num_geometries == 1:

        # This mesh maps to a single geometry, so it gets saved
        # as a single THREE.Mesh, and single THREE.BufferGeometry

        # save bmesh data into global buffergeometries list
        material, bm = mesh_map.popitem()
        geometry_name = mesh_object.data.name
        geometry_uuid = save_geometry(bm,
                                      geometry_name,
                                      export_normals=export_normals,
                                      export_uvs=export_uvs,
                                      export_colors=export_colors,
                                      export_index=export_index,
                                      )

        # finished with temp mesh data
        bm.free()

        # update global materials map
        material_uuid = update_material(material)

        # create mesh object
        object = three.create_mesh(mesh_object.name,
                                   matrix=mesh_object.matrix_local,
                                   geometry_uuid=geometry_uuid,
                                   material_uuid=material_uuid
                                   )

    else:

        # This mesh maps to multiple geometries, so it gets saved as
        # a parent THREE.Object3D with a child THREE.Mesh and
        # THREE.BufferGeometry for each geometry.

        # create Object3D
        object = three.create_object3d(mesh_object.name,
                                       matrix=mesh_object.matrix_local)
        object_children = object["children"]

        # process each geometry
        for material, bm in mesh_map.items():

            # save bmesh data into global buffergeometries list
            material_name = material.name if material else None
            geometry_name = "%s.%s" % (mesh_object.data.name, material_name)
            geometry_uuid = save_geometry(bm,
                                          geometry_name,
                                          export_normals=export_normals,
                                          export_uvs=export_uvs,
                                          export_colors=export_colors,
                                          export_index=export_index,
                                          )

            # no longer need the bmesh data
            bm.free()

            # update global materials map
            material_uuid = update_material(material)

            # create child mesh object
            child_name = "%s.%s" % (mesh_object.name, material_name)
            child_mesh = three.create_mesh(child_name,
                                           geometry_uuid=geometry_uuid,
                                           material_uuid=material_uuid
                                           )
            object_children.append(child_mesh)

    # append to the parent object
    parent_object["children"].append(object)

    return object["uuid"]


def save(operator,
         context,
         filepath=None,
         global_scale=1.0,
         selected_only=True,
         apply_modifiers=True,
         split_by_material=True,
         export_normals=True,
         export_uvs=True,
         export_colors=True,
         export_index=True,
         morph_animation=True,
         sample_rate=1,
         morph_animation_in_userdata=True,
         float_precision=6,
         ):
    '''
    Saves scene objects to a Three.js Object Format 4.3 JSON file
    '''

    if not filepath:
        raise FileNotFoundError("No export filepath specified")

    start = time.time()

    # reset global geometries list
    global_geometries.clear()

    # reset global unique materials map
    global_materials.clear()

    # set  scale global matrix
    global global_scale_matrix
    global_scale_matrix = Matrix.Scale(global_scale, 4)

    scene = context.scene

    # set object mode
    if scene.objects.active:
        bpy.ops.object.mode_set(mode="OBJECT")

    # save current object selection
    initial_selected_objects = context.selected_objects[:]

    try:

        # select objects to export
        if not selected_only:
            bpy.ops.object.select_all(action="SELECT")

        # root object
        root_object = three.create_object3d("root")

        # parse the selected objects
        for selected_object in context.selected_objects:

            # parse selected mesh object
            if selected_object.type == "MESH":
                save_mesh_object(selected_object,
                                 root_object,
                                 scene,
                                 apply_modifiers=apply_modifiers,
                                 split_by_material=split_by_material,
                                 export_normals=export_normals,
                                 export_uvs=export_uvs,
                                 export_colors=export_colors,
                                 export_index=export_index
                                 )

            else:
                print("  Skipping %s: %s ..." %
                      (selected_object.type, selected_object.name))

    finally:

        # always restore initial object selection
        bpy.ops.object.select_all(action="DESELECT")
        for o in initial_selected_objects:
            o.select = True

    # create output dict
    output = three.create_object()

    # attach root object
    if len(root_object["children"]) == 1:
        output["object"] = root_object["children"][0]
    else:
        output["object"] = root_object

    # parse materials
    materials = output["materials"] = []
    for material, material_uuid in global_materials.items():
        materials.append(three.create_material(material, material_uuid))

    # attach geometries
    output["geometries"] = global_geometries

    # calculate stats
    total_positions = 0
    total_normals = 0
    total_faces = int(0)
    for geometry in global_geometries:
        attributes = geometry["data"]["attributes"]
        total_positions += int(len(attributes["position"]["array"]) / 3)
        if "normal" in attributes:
            total_normals += int(len(attributes["normal"]["array"]) / 3)
        if "index" in attributes:
            total_faces += int(len(attributes["index"]["array"]) / 3)
        else:
            total_faces += int(len(attributes["position"]["array"]) / 3)
    metadata = output["metadata"]
    metadata["total_positions"] = total_positions
    metadata["total_normals"] = total_normals
    metadata["total_faces"] = total_faces

    # save JSON to file
    print("\nWriting %s ... " % (filepath), end="")
    file = open(filepath, "w+", encoding="utf8", newline="\n")
    json.JSON_FLOAT_PRECISION = float_precision
    json.json.dump(output, file, indent=4)
    file.close()

    # import pprint
    # pprint.pprint(output)

    print("done.")

    # export has completed
    end = time.time()

    print("\nCompleted in %ds." % (end - start))

    return {'FINISHED'}
