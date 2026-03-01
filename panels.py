import bpy
from .icons import get_botton_icon_id, get_botton_history_icon_id, get_botton_materials_icon_id

def get_addon_prefs(context):
    """Helper function to safely get addon preferences"""
    try:
        addon_name = __package__
        return context.preferences.addons[addon_name].preferences
    except:
        return None

def outliner_header_draw(self, context):
    """Draw button in outliner header - LEFT (FORCED)"""
    prefs = get_addon_prefs(context)
    if prefs and prefs.show_outliner_button:
        layout = self.layout
        
        split = layout.split(factor=0.01)
        
        left = split.row()
        left.separator()
        
        main = split.row()
        
        row = main.row(align=True)
        
        row.operator("material.remove_materials_dialog", 
                   text="", 
                   icon_value=get_botton_materials_icon_id(),
                   emboss=True)
        
    if prefs.show_history_button and hasattr(context.scene, 'deletion_history'):
        history_count = len(context.scene.deletion_history)
        history_text = f" ({history_count})" if history_count > 0 else ""
        botton_history_icon_id = get_botton_history_icon_id()
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

def register():
    bpy.types.OUTLINER_HT_header.prepend(outliner_header_draw)

def unregister():
    bpy.types.OUTLINER_HT_header.remove(outliner_header_draw)