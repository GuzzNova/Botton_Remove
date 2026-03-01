import bpy
import os
import bpy.utils.previews

_botton_icons = None
botton_t_icon_id = 0
botton_history_icon_id = 0
botton_geometry_icon_id = 0 
botton_collections_icon_id = 0
botton_node_groups_icon_id = 0  
botton_materials_icon_id = 0
botton_quick_cleanup_icon_id = 0
botton_orphan_data_icon_id = 0
botton_Clean_material_duplicates_icon_id = 0
botton_Clean_empty_slots_icon_id = 0


def load_icons():
    global _botton_icons, botton_t_icon_id, botton_history_icon_id, botton_geometry_icon_id, botton_collections_icon_id, botton_node_groups_icon_id, botton_materials_icon_id, botton_quick_cleanup_icon_id, botton_orphan_data_icon_id, botton_Clean_material_duplicates_icon_id, botton_Clean_empty_slots_icon_id
    _botton_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    
    print("="*50)
    print("CARGANDO ICONOS DESDE:", icons_dir)
    print("="*50)
    
    if not os.path.isdir(icons_dir):
        print("❌ ERROR: La carpeta 'icons' NO existe en la ruta:", icons_dir)
        print("   Asegúrate de que la carpeta esté dentro del addon y tenga los archivos PNG.")
        return
    
    icon_files = [
        ("botton_t", "Botton_T.png", "botton_t_icon_id"),
        ("botton_history", "Botton_History.png", "botton_history_icon_id"),
        ("botton_geometry", "Botton_Geometry.png", "botton_geometry_icon_id"),
        ("botton_collections", "Botton_Collections.png", "botton_collections_icon_id"),
        ("botton_node_groups", "Botton_NodeGroups.png", "botton_node_groups_icon_id"),
        ("botton_materials", "Botton_Materials.png", "botton_materials_icon_id"),
        ("botton_quick_cleanup", "Botton_QuickCleanup.png", "botton_quick_cleanup_icon_id"),
        ("botton_orphan_data", "Botton_OrphanData.png", "botton_orphan_data_icon_id"),
        ("botton_clean_material_duplicates", "Botton_CleanMaterialDuplicates.png", "botton_Clean_material_duplicates_icon_id"),
        ("botton_clean_empty_slots", "Botton_CleanEmptySlots.png", "botton_Clean_empty_slots_icon_id"),
    ]
    
    for name, filename, var_name in icon_files:
        icon_path = os.path.join(icons_dir, filename)
        if os.path.exists(icon_path):
            try:
                _botton_icons.load(name, icon_path, 'IMAGE')
                icon_id = _botton_icons[name].icon_id

                globals()[var_name] = icon_id
                print(f"✅ {filename} cargado correctamente (ID: {icon_id})")
            except Exception as e:
                print(f"❌ Error al cargar {filename}: {e}")
                globals()[var_name] = 0
        else:
            print(f"❌ Archivo no encontrado: {icon_path}")
            globals()[var_name] = 0
    
    print("="*50)
    print("RESUMEN DE ICONOS:")
    for var_name in [v[2] for v in icon_files]:
        print(f"   {var_name}: {globals()[var_name]}")
    print("="*50)  

def get_botton_icon_id():
    return botton_t_icon_id

def get_botton_history_icon_id():
    return botton_history_icon_id

def get_botton_geometry_icon_id():
    return botton_geometry_icon_id

def get_botton_collections_icon_id():
    return botton_collections_icon_id

def get_botton_node_groups_icon_id():
    return botton_node_groups_icon_id

def get_botton_materials_icon_id():
    return botton_materials_icon_id

def get_botton_quick_cleanup_icon_id():
    return botton_quick_cleanup_icon_id

def get_botton_orphan_data_icon_id():
    return botton_orphan_data_icon_id

def get_botton_Clean_material_duplicates_icon_id():
    return botton_Clean_material_duplicates_icon_id

def get_botton_Clean_empty_slots_icon_id():     
    return botton_Clean_empty_slots_icon_id

def unload_icons():
    global _botton_icons
    if _botton_icons:
        bpy.utils.previews.remove(_botton_icons)
        _botton_icons = None