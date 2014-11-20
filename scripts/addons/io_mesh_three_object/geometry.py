import bmesh

from collections import defaultdict


# bmesh constants

# MOD_TRIANGULATE_QUAD_BEAUTY = 0
MOD_TRIANGULATE_QUAD_FIXED = 1
# MOD_TRIANGULATE_QUAD_ALTERNATE = 2
# MOD_TRIANGULATE_QUAD_SHORTEDGE = 3
MOD_TRIANGULATE_NGON_BEAUTY = 0
# MOD_TRIANGULATE_NGON_EARCLIP = 1
# DEL_VERTS = 1
# DEL_EDGES = 2
# DEL_ONLYFACES = 3
# DEL_EDGESFACES = 4
DEL_FACES = 5
# DEL_ONLYTAGGED = 6


def map_mesh_object(mesh_object,
                    scene,
                    global_matrix,
                    apply_modifiers=True,
                    split_by_material=True,
                    export_normals=True
                    ):
    '''
    Creates a map of assigned mesh materials to bmesh data for the specified
    mesh object.

    The returned map keys represent assigned mesh materials, and may be None.

    All faces assigned to the same material are mapped together, even if
    the material is set in multiple material slots and the faces have a
    different material_index.

    The returned bmesh data is already triangulated and in a suitable for
    exporting to Three.js. For non-indexed BufferGeometry, it can be exported
    as-is. Indexed BufferGeometry will still need to map the bmesh verts.

    returns: dict (always with at least one key)

    example:
    {
        None: <BMesh(0x000000E9600D8518)>,
        <Material>: <BMesh(0x000000E9600D8518)>,
        <Material.001>: <BMesh(0x000000E9600D8518)>
    }

    '''

    bm = bmesh.new()

    if apply_modifiers:
        # use modified object data
        bm.from_object(mesh_object, scene, render=True, face_normals=False)

    else:
        # use un-modified object data
        bm.from_mesh(mesh_object.data, face_normals=False)

    # transform bmesh verts to three.js coords, and scale
    bm.transform(global_matrix)

    # bake flat faces into the bmesh
    flat_edges = set()
    for face in bm.faces:
        if not face.smooth:
            flat_edges.update(face.edges)
    bmesh.ops.split_edges(bm, edges=list(flat_edges))

    # triangulate bmesh data (gets rid of ngons?)
    bm.calc_tessface()

    bmesh.ops.triangulate(bm,
                          faces=bm.faces,
                          quad_method=MOD_TRIANGULATE_QUAD_FIXED,
                          ngon_method=MOD_TRIANGULATE_NGON_BEAUTY)

    # re-calculate normals
    if export_normals:
        bm.normal_update()

    # determine if the mesh should be split by material.
    materials = mesh_object.data.materials
    num_materials = len(materials)
    if not split_by_material or num_materials <= 1:

        # return bmesh as-is mapped to first material
        bm.verts.index_update()
        bm.faces.index_update()
        material = materials[0] if num_materials else None
        return {material: bm}

    # map unique mesh materials to their slot indexes
    material_map = defaultdict(list)
    for material_index, material in enumerate(materials):
        material_map[material].append(material_index)

    result = {}

    # process each material
    for material, index_list in material_map.items():

        # make a copy of the mesh data
        material_bm = bm.copy()

        # delete unwanted faces
        del_faces = [f for f in material_bm.faces
                     if f.material_index not in index_list]
        bmesh.ops.delete(material_bm, geom=del_faces, context=DEL_FACES)

        if len(material_bm.faces) == 0:

            # no faces left after deleting unwanted faces
            material_bm.free()

        else:

            # reset face material_index
            for f in material_bm.faces:
                f.material_index = 0

            # add material/mesh to map
            material_bm.verts.index_update()
            material_bm.faces.index_update()
            result[material] = material_bm

    # free original bmesh
    bm.free()

    # all done
    return result
