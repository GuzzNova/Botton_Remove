bl_info = {
    "name": "Botton Remove free",
    "author": "Arq. Gustavo Garcia",
    "description": "Remove materials, geometry objects, node groups, and collections with advanced selection tools, deletion history, unlimited restore, delete-to-history, and permanent delete modes",
    "blender": (4, 5, 0),
    "version": (1, 0, 0),
    "location": "Outliner Header (LEFT SIDE) / 3D View > Header / Properties Editor / Scene Properties",
    "warning": "This is a new Blender tool, I hope you like it",
    "doc_url": "",
    "tracker_url": "",
    "category": "Material"
}

import bpy
import sys
import traceback
import os
import bpy.utils.previews

# Import icons 
from . import icons

# Load icons 
icons.load_icons()
botton_t_icon_id = icons.botton_t_icon_id
botton_history_icon_id = icons.botton_history_icon_id
botton_geometry_icon_id = icons.botton_geometry_icon_id
botton_collections_icon_id = icons.botton_collections_icon_id
botton_node_groups_icon_id = icons.botton_node_groups_icon_id
botton_materials_icon_id = icons.botton_materials_icon_id
botton_quick_cleanup_icon_id = icons.botton_quick_cleanup_icon_id
botton_orphan_data_icon_id = icons.botton_orphan_data_icon_id
botton_Clean_material_duplicates_icon_id = icons.botton_Clean_material_duplicates_icon_id
botton_Clean_empty_slots_icon_id = icons.botton_Clean_empty_slots_icon_id

from . import properties, operators, panels

HOTKEY_AVAILABLE = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_addon_prefs(context):
    """Helper function to get addon preferences"""
    try:
        addon_name = __package__
        if addon_name in context.preferences.addons:
            return context.preferences.addons[addon_name].preferences
        
        for addon_id in context.preferences.addons.keys():
            if 'botton' in addon_id.lower() or 'remove' in addon_id.lower():
                return context.preferences.addons[addon_id].preferences
    except:
        pass
    return None

# ============================================================================
# Safery hadler
# ============================================================================

def save_pre_handler(dummy):
    """Clear the history before saving according to your preferences"""
    try:
        from . import properties, operators
        prefs = properties.get_addon_prefs(bpy.context)

        for scene in bpy.data.scenes:
            operators.DeletionHistoryManager.auto_clean_history(scene)

        if prefs and not prefs.save_history_with_file:
            for scene in bpy.data.scenes:
                if hasattr(scene, 'deletion_history'):
                    scene.deletion_history.clear()
    except Exception as e:
        print(f"Error en save_pre_handler: {e}")

# ============================================================================
# MENU DEFINITIONS
# ============================================================================

class VIEW3D_MT_botton_remove_menu(bpy.types.Menu):
    """Botton Remove menu in 3D View header"""
    bl_label = "Botton Remove"
    bl_idname = "VIEW3D_MT_botton_remove_menu"

    def draw(self, context):
        layout = self.layout
        global botton_t_icon_id, botton_history_icon_id
        
        layout.label(text="Botton Remove Tools", icon_value=botton_t_icon_id)
        layout.separator()
        
        layout.operator("material.remove_materials_dialog", 
                       text="Tavo Material Eliminator", 
                       icon_value=botton_materials_icon_id)
        
        layout.operator("material.remove_geometry_dialog", 
                       text="Tavo Geometry Eliminator", 
                       icon_value=botton_geometry_icon_id)
        
        layout.operator("material.remove_node_groups_dialog", 
                       text="Tavo Node Groups Eliminator", 
                       icon_value=botton_node_groups_icon_id)
        
        layout.operator("material.remove_collections_dialog", 
                       text="Tavo Collections Eliminator", 
                       icon_value=botton_collections_icon_id)
        
        layout.separator()
        
        layout.label(text="Quick Cleanup", icon_value=botton_quick_cleanup_icon_id)
        layout.separator()
        
        layout.operator("material.remove_unused_materials_fast", 
                       text="Remove Unused Materials", 
                       icon='ORPHAN_DATA')
        
        layout.operator("material.clean_orphan_fast", 
                       text="Clean Orphan Data",  
                       icon_value=botton_orphan_data_icon_id)
        
        layout.operator("material.clean_empty_slots", 
                       text="Clean Empty Slots", 
                       icon_value=botton_Clean_empty_slots_icon_id)
        
        layout.operator("material.clean_material_duplicates", 
                       text="Clean Material Duplicates", 
                       icon_value=botton_Clean_material_duplicates_icon_id)
        

        botton_Clean_material_duplicates_icon_id
        layout.separator()
        
        if hasattr(context.scene, 'deletion_history') and len(context.scene.deletion_history) > 0:
            op_text = f"Deletion History ({len(context.scene.deletion_history)})"
        else:
            op_text = "Deletion History"
        
        if botton_history_icon_id:
            layout.operator("material.view_deletion_history", text=op_text, icon_value=botton_history_icon_id)
        else:
            layout.operator("material.view_deletion_history", text=op_text, icon='TIME')
        
        prefs = get_addon_prefs(context)
        if prefs:
            layout.separator()
            layout.label(text="Safety Status:", icon='PREFERENCES')
            
            if getattr(prefs, 'delete_to_history', False):
                layout.label(text="  [X/Del] -> History (ON)", icon='IMPORT')
            
            if getattr(prefs, 'permanent_delete', False):
                layout.label(text="  PERMANENT DELETE (ON)", icon='ERROR')
            
            if getattr(prefs, 'allow_unlimited_restore', True):
                layout.label(text="  Unlimited Restore (ON)", icon='FILE_REFRESH')
            
class VIEW3D_MT_botton_remove_tpanel(bpy.types.Menu):
    """Botton Remove menu in 3D View T-panel"""
    bl_label = "Botton Remove"
    bl_idname = "VIEW3D_MT_botton_remove_tpanel"
    
    def draw(self, context):
        layout = self.layout
        global botton_t_icon_id, botton_history_icon_id
        
        layout.label(text="Botton Remove Tools", icon_value=botton_t_icon_id)
        layout.separator()
        
        row = layout.row()
        row.scale_y = 1.3
        row.operator("material.remove_materials_dialog", 
                    text="Tavo Material Eliminator", 
                    icon_value=botton_materials_icon_id)
        
        row = layout.row()
        row.scale_y = 1.3
        row.operator("material.remove_geometry_dialog", 
                    text="Tavo Geometry Eliminator", 
                    icon_value=botton_geometry_icon_id)
        
        row = layout.row()
        row.scale_y = 1.3
        row.operator("material.remove_node_groups_dialog", 
                    text="Tavo Node Groups Eliminator", 
                    icon_value=botton_node_groups_icon_id)
        
        row = layout.row()
        row.scale_y = 1.3
        row.operator("material.remove_collections_dialog", 
                    text="Tavo Collections Eliminator", 
                    icon_value=botton_collections_icon_id)
        
        layout.separator()
        
        layout.label(text="Quick Cleanup", icon_value=botton_quick_cleanup_icon_id)
        layout.separator()

        row = layout.row()
        row.scale_y = 1.3
        row.operator("material.remove_unused_materials_fast", 
                    text="Unused Mats", 
                    icon='ORPHAN_DATA')
    
        row = layout.row()
        row.scale_y = 1.3
        row.operator("material.clean_orphan_fast", 
                    text="Clean Orphan Data", 
                    icon_value=botton_orphan_data_icon_id)
        
        row = layout.row()
        row.scale_y = 1.3
        row.operator("material.clean_empty_slots", 
                    text="Clean Empty Slots", 
                    icon_value=botton_Clean_empty_slots_icon_id)       
   
        row = layout.row()
        row.scale_y = 1.3
        row.operator("material.clean_material_duplicates", 
                    text="Clean Material Duplicates", 
                    icon_value=botton_Clean_material_duplicates_icon_id)
        
        row = layout.row()
        row.scale_y = 1.3

        if hasattr(context.scene, 'deletion_history') and len(context.scene.deletion_history) > 0:
            op_text = f"Deletion History ({len(context.scene.deletion_history)})"
        else:
            op_text = "Deletion History"
        
        if botton_history_icon_id:
            layout.operator("material.view_deletion_history", text=op_text, icon_value=botton_history_icon_id)
        else:
            layout.operator("material.view_deletion_history", text=op_text, icon='TIME')
        
        prefs = get_addon_prefs(context)
        if prefs:
            layout.separator()
            layout.label(text="Safety Status:", icon='PREFERENCES')
            
            if getattr(prefs, 'delete_to_history', False):
                layout.label(text="  [X/Del] -> History (ON)", icon='IMPORT')
            
            if getattr(prefs, 'permanent_delete', False):
                layout.label(text="  PERMANENT DELETE (ON)", icon='ERROR')
            
            if getattr(prefs, 'allow_unlimited_restore', True):
                layout.label(text="  Unlimited Restore (ON)", icon='FILE_REFRESH')
        
def view3d_tpanel_draw(self, context):
    """Draw Botton Remove button in 3D View T-panel"""
    prefs = get_addon_prefs(context)
    if prefs and prefs.show_3dview_tpanel:
        layout = self.layout
        
        layout.separator()
        
        row = layout.row()
        row.scale_y = 1.2
        row.menu("VIEW3D_MT_botton_remove_tpanel", 
                text="Botton Remove", 
                icon_value=botton_t_icon_id)

# ============================================================================
# PANEL DEFINITIONS 
# ============================================================================

class PROPERTIES_PT_botton_remove_scene(bpy.types.Panel):
    """Botton Remove panel in Scene Properties"""
    bl_label = "Botton Remove"
    bl_idname = "PROPERTIES_PT_botton_remove_scene"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_category = "Scene"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        return prefs and prefs.show_properties_panel and prefs.panel_position in ['SCENE', 'MULTI']

    def draw(self, context):
        layout = self.layout
        global botton_t_icon_id, botton_history_icon_id
        
        box = layout.box()
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text="Botton Remove Tools", icon_value=botton_t_icon_id)
        row = box.row()
        row.alignment = 'CENTER'
        row.scale_y = 0.8
        row.label(text="Complete cleanup and management tools")
        
        box = layout.box()
        box.label(text="Main Tools", icon='TOOL_SETTINGS')
        
        grid = box.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        grid.scale_y = 1.4
        
        grid.operator("material.remove_materials_dialog", 
                     text="Tavo Material Eliminator", 
                     icon_value=botton_materials_icon_id)
        
        grid.operator("material.remove_geometry_dialog", 
                     text="Tavo Geometry Eliminator", 
                     icon_value=botton_geometry_icon_id)
        
        grid.operator("material.remove_node_groups_dialog", 
                     text="Tavo Node Groups Eliminator", 
                     icon_value=botton_node_groups_icon_id)
        
        grid.operator("material.remove_collections_dialog", 
                     text="Tavo Collections Eliminator", 
                     icon_value=botton_collections_icon_id)
        
        box = layout.box()
        box.label(text="Quick Cleanup", icon_value=botton_quick_cleanup_icon_id)
        
        grid = box.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        grid.scale_y = 1.2
        
        grid.operator("material.remove_unused_materials_fast", 
                     text="Unused Materials", 
                     icon='ORPHAN_DATA')
        
        grid.operator("material.clean_orphan_fast", 
                     text="Clean Orphan Data", 
                     icon_value=botton_orphan_data_icon_id)
        
        grid.operator("material.clean_empty_slots", 
                     text="Clean Empty Slots", 
                     icon_value=botton_Clean_empty_slots_icon_id)
        
        grid.operator("material.clean_material_duplicates", 
                     text="Clean Material Duplicates", 
                     icon_value=botton_Clean_material_duplicates_icon_id)
        
        box = layout.box()
        
        if hasattr(context.scene, 'deletion_history') and len(context.scene.deletion_history) > 0:
            row = box.row()
            row.scale_y = 1.3
            if botton_history_icon_id:
                row.operator("material.view_deletion_history", 
                            text=f"Deletion History ({len(context.scene.deletion_history)})", 
                            icon_value=botton_history_icon_id)
            else:
                row.operator("material.view_deletion_history", 
                            text=f"Deletion History ({len(context.scene.deletion_history)})", 
                            icon='TIME')
            
            history_box = box.box()
            history_box.label(text="Recent Actions:", icon='INFO')
            col = history_box.column(align=True)
            col.scale_y = 0.7
            
            count = 0
            for entry in reversed(context.scene.deletion_history):
                if count >= 3:
                    break
                
                type_icons = {
                    'MATERIAL': 'MATERIAL',
                    'GEOMETRY': 'MESH_CUBE',
                    'NODE_GROUP': 'NODETREE',
                    'COLLECTION': 'OUTLINER_COLLECTION',
                }
                
                icon = type_icons.get(entry.deletion_type, 'QUESTION')
                items = entry.item_names
                if len(items) > 20:
                    items = items[:17] + "..."
                
                row = col.row()
                row.label(text="", icon=icon)
                row.label(text=f"{items}")
                
                count += 1
        else:
            row = box.row()
            row.scale_y = 1.3
            if botton_history_icon_id:
                row.operator("material.view_deletion_history", 
                            text="Deletion History", 
                            icon_value=botton_history_icon_id)
            else:
                row.operator("material.view_deletion_history", 
                            text="Deletion History", 
                            icon='TIME')

class PROPERTIES_PT_botton_remove_tool(bpy.types.Panel):
    """Botton Remove panel in Tool Properties"""
    bl_label = "Botton Remove"
    bl_idname = "PROPERTIES_PT_botton_remove_tool"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_category = "Tool"
    bl_order = 100

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        return prefs and prefs.show_properties_panel and prefs.panel_position in ['TOOL', 'MULTI']

    def draw(self, context):
        return PROPERTIES_PT_botton_remove_scene.draw(self, context)

# ============================================================================
# Properties icons in view3d
# ============================================================================

class OBJECT_PT_botton_remove(bpy.types.Panel):
    """Botton Remove panel in Object Properties"""
    bl_label = "Botton Remove"
    bl_idname = "OBJECT_PT_botton_remove"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = "Object"
    bl_order = 100

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        return prefs and prefs.show_properties_panel and context.object is not None

    def draw(self, context):
        layout = self.layout
        global botton_t_icon_id, botton_history_icon_id
        
        box = layout.box()
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text="🗑️ Botton Remove", icon_value=botton_t_icon_id)
        
        obj = context.object
        if obj:
            info_box = box.box()
            row = info_box.row()
            row.label(text=f"Active: {obj.name}", icon='OBJECT_DATA')
            
            if hasattr(obj, 'material_slots') and obj.material_slots:
                row = info_box.row()
                row.label(text=f"Materials: {len([s for s in obj.material_slots if s.material])}", icon='MATERIAL')
        
        box = layout.box()
        box.label(text="Quick Actions", icon='PLAY')
        
        col = box.column(align=True)
        col.scale_y = 1.2
        
        if obj and obj.type == 'MESH':
            col.operator("material.remove_materials_dialog", 
                        text="Remove Object Materials", 
                        icon_value=botton_materials_icon_id) 
        
        col.operator("material.remove_geometry_dialog", 
                    text="Tavo Geometry Eliminator", 
                    icon_value=botton_geometry_icon_id) 
        
        col.operator("material.remove_node_groups_dialog", 
                    text="Tavo Node Groups Eliminator", 
                    icon_value=botton_node_groups_icon_id)
        
        box = layout.box()
        box.label(text="Quick Clean", icon='BRUSH_DATA')
        
        col = box.column(align=True)
        col.scale_y = 1.1
        
        col.operator("material.remove_unused_materials_fast", 
                    text="Unused Materials", 
                    icon='ORPHAN_DATA')
        
        col.operator("material.clean_orphan_fast", 
                    text="Clean Orphan Data", 
                    icon_value=botton_orphan_data_icon_id)
        
        if hasattr(context.scene, 'deletion_history') and len(context.scene.deletion_history) > 0:
            box = layout.box()
            row = box.row()
            row.scale_y = 1.2
            if botton_history_icon_id:
                row.operator("material.view_deletion_history", 
                            text=f"History ({len(context.scene.deletion_history)})", 
                            icon_value=botton_history_icon_id)
            else:
                row.operator("material.view_deletion_history", 
                            text=f"History ({len(context.scene.deletion_history)})", 
                            icon='TIME')

# ============================================================================
# PANEL EN VIEW3D SIDEBAR 
# ============================================================================

class VIEW3D_PT_botton_remove(bpy.types.Panel):
    """Botton Remove panel in 3D View sidebar"""
    bl_label = "Botton Remove"
    bl_idname = "VIEW3D_PT_botton_remove"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_context = "objectmode"
    bl_order = 100

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        return prefs and prefs.show_properties_panel

    def draw(self, context):
        layout = self.layout
        global botton_t_icon_id, botton_history_icon_id
        
        box = layout.box()
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text="🗑️", icon_value=botton_t_icon_id)
        
        flow = layout.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        flow.scale_y = 1.3
        
        flow.operator("material.remove_materials_dialog", 
                     text="", 
                     icon='MATERIAL')
        
        flow.operator("material.remove_geometry_dialog", 
                     text="", 
                     icon='MESH_CUBE')
        
        flow.operator("material.remove_node_groups_dialog", 
                     text="", 
                     icon='NODETREE')
        
        flow.operator("material.remove_collections_dialog", 
                     text="", 
                     icon_value=botton_collections_icon_id)
        
        layout.separator()
        box = layout.box()
        box.label(text="Clean", icon='BRUSH_DATA')
        
        flow = box.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        flow.scale_y = 1.2
        
        flow.operator("material.remove_unused_materials_fast", 
                     text="", 
                     icon='ORPHAN_DATA')
        
        flow.operator("material.clean_orphan_fast", 
                     text="", 
                     icon='BRUSH_DATA')
        
        flow.operator("material.clean_empty_slots", 
                     text="", 
                     icon='MATERIAL')
        
        flow.operator("material.clean_material_duplicates", 
                     text="Clean Material Duplicates", 
                     icon_value=botton_Clean_material_duplicates_icon_id)
        
        if hasattr(context.scene, 'deletion_history') and len(context.scene.deletion_history) > 0:
            layout.separator()
            row = layout.row()
            row.scale_y = 1.2
            if botton_history_icon_id:
                row.operator("material.view_deletion_history", 
                            text=f"History ({len(context.scene.deletion_history)})", 
                            icon_value=botton_history_icon_id)
            else:
                row.operator("material.view_deletion_history", 
                            text=f"History ({len(context.scene.deletion_history)})", 
                            icon='TIME')
# ============================================================================
# Debug_Iconos
# ============================================================================
class BOTTON_OT_debug_icons(bpy.types.Operator):
    """Verificar el estado de los iconos del addon"""
    bl_idname = "botton.debug_icons"
    bl_label = "Depurar Iconos de Botton Remove"
    
    def execute(self, context):
        print("\n" + "="*60)
        print("DEPURACIÓN DE ICONOS - BOTTON REMOVE")
        print("="*60)
        
        try:
            from . import icons
            icons.unload_icons()
            icons.load_icons()
        except Exception as e:
            print(f"Error al recargar iconos: {e}")
        
        print("\nIDs de iconos registrados:")
        print(f"  botton_t_icon_id: {icons.botton_t_icon_id}")
        print(f"  botton_history_icon_id: {icons.botton_history_icon_id}")
        print(f"  botton_geometry_icon_id: {icons.botton_geometry_icon_id}")
        print(f"  botton_collections_icon_id: {icons.botton_collections_icon_id}")
        print(f"  botton_node_groups_icon_id: {icons.botton_node_groups_icon_id}")
        print(f"  botton_materials_icon_id: {icons.botton_materials_icon_id}")
        print(f"  botton_quick_cleanup_icon_id: {icons.botton_quick_cleanup_icon_id}")
        print(f"  botton_orphan_data_icon_id: {icons.botton_orphan_data_icon_id}")
        print(f"  botton_Clean_material_duplicates_icon_id: {icons.botton_Clean_material_duplicates_icon_id}")
        print(f"  botton_Clean_empty_slots_icon_id: {icons.botton_Clean_empty_slots_icon_id}")
        
        self.report({'INFO'}, "Revisa la consola de Blender para ver el resultado")
        return {'FINISHED'}
    
# ============================================================================
# HEADER BUTTONS
# ============================================================================

def view3d_header_draw(self, context):
    """Draw button in 3D View header"""
    prefs = get_addon_prefs(context)
    if prefs and prefs.show_outliner_button and prefs.show_3dview_menu:
        layout = self.layout
        global botton_t_icon_id, botton_history_icon_id
        
        split = layout.split(factor=0.01)
        left = split.row()
        left.separator()
        
        main = split.row()
        
        row = main.row(align=True)
        
        row.menu("VIEW3D_MT_botton_remove_menu", 
                text="", 
                icon_value=botton_t_icon_id)
        
        if prefs.show_history_button and hasattr(context.scene, 'deletion_history'):
            history_count = len(context.scene.deletion_history)
            history_text = f" ({history_count})" if history_count > 0 else ""
            if botton_history_icon_id:
                row.operator("material.view_deletion_history", 
                            text=history_text, 
                            icon_value=botton_history_icon_id, 
                            emboss=True)
            else:
                row.operator("material.view_deletion_history", 
                            text=history_text, 
                            icon='TIME', 
                            emboss=True)

# ============================================================================
# Node_editor header button
# ===========================================================================
def node_editor_header_draw(self, context):
    """Draw button in Node Editor header"""
    prefs = get_addon_prefs(context)
    if prefs and prefs.show_outliner_button and prefs.show_node_editor_button:
        layout = self.layout
        
        split = layout.split(factor=0.01)
        left = split.row()
        left.separator()
        
        main = split.row()
        
        row = main.row(align=True)
        
        node_tree = getattr(context.space_data, 'node_tree', None)
        if node_tree and node_tree.type == 'GEOMETRY':

            op_id = "material.remove_node_groups_dialog"
            icon_id = botton_node_groups_icon_id
            fallback_icon = 'NODETREE'
        else:
            op_id = "material.remove_materials_dialog"
            icon_id = botton_materials_icon_id
            fallback_icon = 'MATERIAL'
        
        if icon_id:
            row.operator(op_id, text="", icon_value=icon_id, emboss=True)
        else:
            row.operator(op_id, text="", icon=fallback_icon, emboss=True)
        
        if prefs.show_history_button and hasattr(context.scene, 'deletion_history'):
            history_count = len(context.scene.deletion_history)
            history_text = f" ({history_count})" if history_count > 0 else ""
            if botton_history_icon_id:
                row.operator("material.view_deletion_history", 
                            text=history_text, 
                            icon_value=botton_history_icon_id, 
                            emboss=True)
            else:
                row.operator("material.view_deletion_history", 
                            text=history_text, 
                            icon='TIME', 
                            emboss=True)

# ============================================================================
# REGISTRATION 
# ============================================================================

def register():
    print("\n" + "="*60)
    print("REGISTERING BOTTON REMOVE v1.0.0")
    print("="*60)
    
    try:
        # Register menu classes
        bpy.utils.register_class(VIEW3D_MT_botton_remove_menu)
        bpy.utils.register_class(VIEW3D_MT_botton_remove_tpanel)
        
        # Register panel classes
        bpy.utils.register_class(PROPERTIES_PT_botton_remove_scene)
        bpy.utils.register_class(PROPERTIES_PT_botton_remove_tool)
        bpy.utils.register_class(OBJECT_PT_botton_remove)
        bpy.utils.register_class(VIEW3D_PT_botton_remove)
        bpy.utils.register_class(BOTTON_OT_debug_icons)

        # Register handler for saving
        bpy.app.handlers.save_pre.append(save_pre_handler)
        
        # Register base modules
        properties.register()
        operators.register()
        panels.register()
        
        # ==============================================================
        # Register footer menu
        # ==============================================================
        try:
            from . import pie_menu
            pie_menu.register()
            print("✓ registered footer menu system")
        except Exception as e:
            print(f"⚠️ Error with footer menu: {e}")
        # ==============================================================
        
        # Register header handlers
        bpy.types.VIEW3D_HT_header.append(view3d_header_draw)
        bpy.types.NODE_HT_header.append(node_editor_header_draw)
        
        # Register in T-Panel
        try:
            bpy.types.VIEW3D_PT_tools_object_options.append(view3d_tpanel_draw)
            bpy.types.VIEW3D_PT_tools_active.append(view3d_tpanel_draw)
            bpy.types.VIEW3D_PT_object_item.append(view3d_tpanel_draw)
            print("✓ T-Panel menu registered")
        except Exception as e:
            print(f"⚠️ T-Panel: {e}")
        
        # ==============================================================
        # Register Safety Settings (Delete-to-History + Permanent Delete)
        # ==============================================================
        try:
            from . import safety_settings
            safety_settings.register()
            print("✓ Safety Settings module registered")
        except Exception as e:
            print(f"⚠️ Error with Safety Settings: {e}")
            traceback.print_exc()
        
        # ==============================================================
        # HOTKEY - Now supports both menu types
        # ==============================================================
        print("\n--- HOTKEY SYSTEM ---")
        try:
            from . import hotkey
            hotkey.register()
            global HOTKEY_AVAILABLE
            HOTKEY_AVAILABLE = True
            
            print("✓ Hotkey system loaded")
            print(f"✓ Supports: Circular Menu and Pie Menu")
                
        except Exception as e:
            print(f"✗ ERROR with hotkey system: {e}")
            traceback.print_exc()
            print("⚠️ Hotkey disabled, but the addon works")
        # ==============================================================
        
        print("\n" + "="*60)
        print("BOTTON REMOVE v1.0.0 SUCCESSFULLY LOADED!")
        print("="*60)
        print("AVAILABLE LOCATIONS:")
        print("  1. Outliner Header (LEFT)")
        print("  2. 3D View Header (TRASH menu)")
        print("  3. Properties Editor → Scene tab")
        print("  4. Properties Editor → Tool tab")
        print("  5. Properties Editor → Object tab")
        print("  6. Node Editor Header")
        print("  7. 3D View T-Panel (presiona T)")
        print("")
        print("UNIQUE HOTKEY (Shift+X):")
        print("  • Circular Menu: Visual interface with colors")
        print("  • Pie Menu: Blender's native menu (faster)")
        print("")
        print("QUICK KEYS FROM THE MENU (when visible):")
        print("  M = Materials | G = Geometry | N = Nodes")
        print("  C = Collections | H = History | A = Clear all")
        print("")
        print("SAFETY SETTINGS:")
        print("  • Unlimited Restore: Restore from your history as many times as you want")
        print("  • Delete to History: X/Del sends to history (checkbox)")
        print("  • Permanent Delete: delete without going through history (checkbox)")
        print("  • Preview in Hotkeys: Visual Status Indicators")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ ERROR CRÍTICO: {e}")
        traceback.print_exc()
        print("="*60)
        # ==============================================================

def unregister():
    print("\n" + "="*50)
    print("UNREGISTERING BOTTON REMOVE")
    print("="*50)
    
    try:
        try:
            bpy.types.VIEW3D_HT_header.remove(view3d_header_draw)
        except:
            pass
            
        try:
            bpy.types.NODE_HT_header.remove(node_editor_header_draw)
        except:
            pass
        
        try:
            bpy.types.VIEW3D_PT_tools_object_options.remove(view3d_tpanel_draw)
        except:
            pass
            
        try:
            bpy.types.VIEW3D_PT_tools_active.remove(view3d_tpanel_draw)
        except:
            pass
            
        try:
            bpy.types.VIEW3D_PT_object_item.remove(view3d_tpanel_draw)
        except:
            pass

        if save_pre_handler in bpy.app.handlers.save_pre:
            bpy.app.handlers.save_pre.remove(save_pre_handler)
        
        global HOTKEY_AVAILABLE
        if HOTKEY_AVAILABLE:
            try:
                from . import hotkey
                hotkey.unregister()
                print("✓ unregistered hotkey system")
            except Exception as e:
                print(f"⚠️ Error unregistering hotkey: {e}")
        
        # ==============================================================
        # Unregister Safety Settings
        # ==============================================================
        try:
            from . import safety_settings
            safety_settings.unregister()
            print("✓ Safety Settings module unregistered")
        except Exception as e:
            print(f"⚠️ Error unregistering Safety Settings: {e}")
        # ==============================================================
        
        # ==============================================================
        # Unregister pie menu
        # ==============================================================
        try:
            from . import pie_menu
            pie_menu.unregister()
            print("✓ Pie menu system unregistered")
        except Exception as e:
            print(f"⚠️ Error unregistering pie menu: {e}")
        # ==============================================================
        
        # ==============================================================
        # Liberar íconos personalizados
        # ==============================================================
        try:
            from . import icons
            icons.unload_icons()
            print("✓ Íconos liberados")
        except Exception as e:
            print(f"⚠️ Error liberando íconos: {e}")
        # ==============================================================
        
        # Unregister in reverse order
        panels.unregister()
        operators.unregister()
        properties.unregister()
        
        # Unregister classes
        bpy.utils.unregister_class(BOTTON_OT_debug_icons)
        bpy.utils.unregister_class(VIEW3D_PT_botton_remove)
        bpy.utils.unregister_class(OBJECT_PT_botton_remove)
        bpy.utils.unregister_class(PROPERTIES_PT_botton_remove_tool)
        bpy.utils.unregister_class(PROPERTIES_PT_botton_remove_scene)
        bpy.utils.unregister_class(VIEW3D_MT_botton_remove_tpanel)
        bpy.utils.unregister_class(VIEW3D_MT_botton_remove_menu)
        
        print("✓ Button Remove completely deactivated")
        print("="*50)
        
    except Exception as e:
        print(f"✗ Error deactivating Button Remove: {e}")
        traceback.print_exc()