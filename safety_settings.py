import bpy
import json
import time
import bmesh


def get_addon_prefs(context):
    """Helper function to safely get addon preferences"""
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

class BOTTON_OT_delete_to_history(bpy.types.Operator):
    """Delete selected objects but save them to Botton Remove history for recovery"""
    bl_idname = "botton.delete_to_history"
    bl_label = "Delete to History"
    bl_description = "Move selected objects to hidden trash collection (recoverable)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and len(context.selected_objects) > 0

    def execute(self, context):
        prefs = get_addon_prefs(context)
        if not prefs:
            self.report({'WARNING'}, "Could not access addon preferences")
            return {'CANCELLED'}

        if prefs.permanent_delete:
            obj_names = [obj.name for obj in context.selected_objects]
            for obj_name in obj_names:
                if obj_name in bpy.data.objects:
                    bpy.data.objects.remove(bpy.data.objects[obj_name], do_unlink=True)
            self.report({'INFO'}, f"Permanently deleted {len(obj_names)} object(s) [NO HISTORY]")
            return {'FINISHED'}

        trash_coll = self.get_trash_collection(context)

        selected_objects = list(context.selected_objects)
        obj_names = []
        original_collections_map = {}

        for obj in selected_objects:
            obj_names.append(obj.name)
            original_colls = [coll.name for coll in obj.users_collection if coll != trash_coll]
            original_collections_map[obj.name] = original_colls

            for coll in list(obj.users_collection):
                coll.objects.unlink(obj)
            trash_coll.objects.link(obj)

            obj.hide_viewport = True
            obj.hide_render = True

        if not obj_names:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        backup_data = {
            "method": "hide",
            "original_collections": original_collections_map,
            "timestamp": time.time()
        }
        backup_json = json.dumps(backup_data)

        try:
            from . import operators
            DeletionHistoryManager = operators.DeletionHistoryManager
            entry = DeletionHistoryManager.add_history_entry(
                context.scene,
                'GEOMETRY',
                obj_names,
                len(obj_names),
                backup_json
            )
            if entry and hasattr(entry, 'source'):
                entry.source = 'HOTKEY'
        except Exception as e:
            print(f"Error adding history entry: {e}")

        self.report({'INFO'}, f"Moved {len(obj_names)} object(s) to hidden trash collection (recoverable)")
        return {'FINISHED'}

    def get_trash_collection(self, context):
        """Obtain or create the hidden collection WITHOUT linking it to the scene"""
        TRASH_NAME = "Trash Collection"
        for coll in bpy.data.collections:
            if coll.name == TRASH_NAME:
                coll.hide_viewport = True
                coll.hide_render = True
                return coll
        trash = bpy.data.collections.new(TRASH_NAME)

        trash.hide_viewport = True
        trash.hide_render = True
        return trash

class BOTTON_OT_permanent_delete(bpy.types.Operator):
    """Delete selected objects permanently without saving to history"""
    bl_idname = "botton.permanent_delete"
    bl_label = "Permanent Delete"
    bl_description = "Delete selected objects permanently - NO history backup, NO recovery possible"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects and len(context.selected_objects) > 0
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context):
        obj_names = [obj.name for obj in context.selected_objects]
        count = len(obj_names)
        
        for obj_name in obj_names:
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                bpy.data.objects.remove(obj, do_unlink=True)
        
        self.report({'WARNING'}, f"PERMANENTLY deleted {count} object(s) - NOT recoverable!")
        return {'FINISHED'}


addon_delete_keymaps = []


def register_delete_keymap():
    """Register X/Delete keymaps to intercept object deletion"""
    prefs = get_addon_prefs(bpy.context)
    if not prefs or not prefs.delete_to_history:
        return
    
    wm = bpy.context.window_manager
    if not hasattr(wm, 'keyconfigs') or not wm.keyconfigs or not wm.keyconfigs.addon:
        return
    
    keymap_configs = [
        {'name': 'Object Mode', 'space_type': 'EMPTY'},
    ]
    
    for config in keymap_configs:
        try:
            km = wm.keyconfigs.addon.keymaps.new(
                name=config['name'],
                space_type=config['space_type'],
                region_type='WINDOW',
            )
            
            kmi = km.keymap_items.new(
                "botton.delete_to_history",
                type='X',
                value='PRESS',
                shift=False,
                ctrl=False,
                alt=False,
            )
            kmi.active = True
            addon_delete_keymaps.append((km, kmi))
            
            kmi2 = km.keymap_items.new(
                "botton.delete_to_history",
                type='DEL',
                value='PRESS',
                shift=False,
                ctrl=False,
                alt=False,
            )
            kmi2.active = True
            addon_delete_keymaps.append((km, kmi2))
            
            print(f"  Delete-to-History: X/Del registered in {config['name']}")
            
        except Exception as e:
            print(f"  Error registering delete keymap in {config['name']}: {e}")


def unregister_delete_keymap():
    """Remove Delete-to-History keymaps"""
    for km, kmi in addon_delete_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except:
            pass
    addon_delete_keymaps.clear()



classes = [
    BOTTON_OT_delete_to_history,
    BOTTON_OT_permanent_delete,
]


def register():
    """Register safety settings classes and keymaps"""
    print("\n" + "=" * 50)
    print("REGISTERING SAFETY SETTINGS MODULE")
    print("=" * 50)
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"  Registered: {cls.__name__}")
        except Exception as e:
            print(f"  Error registering {cls.__name__}: {e}")
    
    try:
        register_delete_keymap()
    except Exception as e:
        print(f"  Error registering delete keymaps: {e}")
    
    print("SAFETY SETTINGS MODULE READY")
    print("=" * 50)


def unregister():
    """Unregister safety settings classes and keymaps"""
    print("\nUnregistering safety settings module...")
    
    unregister_delete_keymap()
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            print(f"  Unregistered: {cls.__name__}")
        except Exception as e:
            print(f"  Error unregistering {cls.__name__}: {e}")
    
    print("Safety settings module deactivated")