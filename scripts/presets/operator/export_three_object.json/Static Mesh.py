import bpy
op = bpy.context.active_operator

op.global_scale = 1.0
op.selected_only = False
op.apply_modifiers = True
op.split_by_material = True
