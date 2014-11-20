# io_mesh_three_object - Three.js Object Exporter

bl_info = {
    "name": "Export Three.js Object Format 4.3 (.json)",
    "author": "satori99",
    "version": (0, 0, 1),
    "blender": (2, 72, 0),
    "location": "File > Export > Three.js Object (.json)",
    "description":
        "Exports Three.js Object Format 4.3 JSON files",
    "warning": "",
    "wiki_url": "https://github.com/satori99/"
        "tree/master/utils/exporters/blender",
    "tracker_url": "https://github.com/satori99/"
        "blender-threejs-object-export/issues",
    "category": "Import-Export",
}

# reload local modules
if "bpy" in locals():
    import imp
    if "geometry" in locals():
        imp.reload(geometry)
    if "json" in locals():
        imp.reload(json)
    if "three" in locals():
        imp.reload(three)
    if "object" in locals():
        imp.reload(object)

import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       FloatProperty,
                       IntProperty)


class ExportThreeObject(bpy.types.Operator):

    bl_idname = "export_three_object.json"

    bl_label = "Export Three.js Object"

    bl_options = {"PRESET"}

    filename_ext = ".json"

    # export options

    filepath = StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        maxlen=1024,
        subtype="FILE_PATH",
        options={"SKIP_SAVE"}
        )

    global_scale = FloatProperty(
        name="Global Scale",
        description="Apply uniform scale to all exported objects",
        default=1.0,
        min=0.01,
        max=100,
        )

    selected_only = BoolProperty(
        name="Selected Only",
        description="Export selected scene objects only",
        default=False
        )

    apply_modifiers = BoolProperty(
        name="Apply Modifiers",
        description="Apply mesh modifiers to exported geometry",
        default=True
        )

    split_by_material = BoolProperty(
        name="Split by Material",
        description="Split exported geometry by material",
        default=True
        )

    export_normals = BoolProperty(
        name="Export Normals",
        description="Export BufferGeometry normal attribute",
        default=True
        )

    export_uvs = BoolProperty(
        name="Export UVs",
        description="Export BufferGeometry uv attributes",
        default=True
        )

    export_colors = BoolProperty(
        name="Export Colors",
        description="Export BufferGeometry color attribute",
        default=True
        )

    export_index = BoolProperty(
        name="Export Index",
        description="Export BufferGeometry index attribute",
        default=True
        )

    morph_animation = BoolProperty(
        name="Export morph animations",
        description="Export MorphTarget animations",
        default=True
        )

    sample_rate = FloatProperty(
        name="Sample Rate",
        description="Morph animation sample rate",
        default=1.0,
        min=1,
        max=10,
        )

    morph_animation_in_userdata = BoolProperty(
        name="Store Morphtargets in userData",
        description="Store morphtarget data in mesh userData object",
        default=True
        )

    float_precision = IntProperty(
        name="Float Precision",
        description="JSON floating point number precision",
        default=8,
        min=3,
        max=10,
        )

    # Operator methods

    def invoke(self, context, event):
        # set default filepath
        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if not blend_filepath:
                blend_filepath = "untitled"
            else:
                blend_filepath = \
                    bpy.path.display_name_from_filepath(blend_filepath)
            self.filepath = blend_filepath + self.filename_ext
        # open file select window
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):

        layout = self.layout
        layout.label(text="Select a preset, or set custom options below")

        layout.separator()
        row = layout.row()
        row.prop(self.properties, "global_scale")
        row = layout.row()
        row.prop(self.properties, "selected_only")
        row = layout.row()
        row.prop(self.properties, "apply_modifiers")
        row = layout.row()
        row.prop(self.properties, "split_by_material")

        layout.separator()
        row = layout.row()
        row.prop(self.properties, "export_normals")
        row = layout.row()
        row.prop(self.properties, "export_uvs")
        row = layout.row()
        row.prop(self.properties, "export_colors")
        row = layout.row()
        row.prop(self.properties, "export_index")

        layout.separator()
        row = layout.row()
        row.prop(self.properties, "morph_animation")
        row = layout.row()
        row.prop(self.properties, "sample_rate")

        layout.separator()
        layout.label(text="Advanced Options")
        row = layout.row()
        row.prop(self.properties, "morph_animation_in_userdata")
        row = layout.row()
        row.prop(self.properties, "float_precision")

    def execute(self, context):
        print("\nExporting Three.js Object '%s' ...\n" % (self.filepath))
        try:
            from . import object
            keywords = self.as_keywords(ignore=("", ))
            return object.save(self, context, **keywords)
        except:
            # todo: nice error message popups
            raise

    @classmethod
    def poll(cls, context):
        return context.active_object is not None


# register addon
def menu_func(self, context):
    text = "Three.js Object (%s)" % (ExportThreeObject.filename_ext)
    self.layout.operator(ExportThreeObject.bl_idname, text=text)


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
