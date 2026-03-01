from multiprocessing import context

import bpy
import time
import datetime
import json
import bmesh
from collections import OrderedDict
from . import icons

botton_t_icon_id = icons.botton_t_icon_id
botton_history_icon_id = icons.botton_history_icon_id
botton_geometry_icon_id = icons.botton_geometry_icon_id
botton_collections_icon_id = icons.botton_collections_icon_id
botton_node_groups_icon_id = icons.botton_node_groups_icon_id
botton_materials_icon_id = icons.botton_materials_icon_id
botton_orphan_data_icon_id = icons.botton_orphan_data_icon_id
botton_Clean_material_duplicates_icon_id = icons.botton_Clean_material_duplicates_icon_id
botton_Clean_empty_slots_icon_id = icons.botton_Clean_empty_slots_icon_id

class MaterialSelectionItem(bpy.types.PropertyGroup):
    """Item for material selection in dialog"""
    name: bpy.props.StringProperty(name="Material Name")
    selected: bpy.props.BoolProperty(name="Selected", default=False)
    users: bpy.props.IntProperty(name="Users", default=0)

class GeometrySelectionItem(bpy.types.PropertyGroup):
    """Item for geometry selection in dialog"""
    name: bpy.props.StringProperty(name="Object Name")
    selected: bpy.props.BoolProperty(name="Selected", default=False)
    type: bpy.props.StringProperty(name="Type", default="MESH")
    hide_viewport: bpy.props.BoolProperty(name="Hide Viewport", default=False)
    hide_viewport_temp: bpy.props.BoolProperty(name="Hide Viewport Temp", default=False)
    hide_render: bpy.props.BoolProperty(name="Hide Render", default=False)
    users: bpy.props.IntProperty(name="Users", default=0)

class NodeGroupSelectionItem(bpy.types.PropertyGroup):
    """Item for node group selection in dialog"""
    name: bpy.props.StringProperty(name="Node Group Name")
    selected: bpy.props.BoolProperty(name="Selected", default=False)
    type: bpy.props.StringProperty(name="Type", default="SHADER")
    users: bpy.props.IntProperty(name="Users", default=0)

class CollectionSelectionItem(bpy.types.PropertyGroup):
    """Item for collection selection in dialog"""
    name: bpy.props.StringProperty(name="Collection Name")
    selected: bpy.props.BoolProperty(name="Selected", default=False)
    object_count: bpy.props.IntProperty(name="Object Count", default=0)
    child_count: bpy.props.IntProperty(name="Child Count", default=0)
    child_collection_count: bpy.props.IntProperty(name="Child Collection Count", default=0)
    is_linked: bpy.props.BoolProperty(name="Is Linked", default=False)
    is_empty: bpy.props.BoolProperty(name="Is Empty", default=False)
    users: bpy.props.IntProperty(name="Users", default=0)
    hide_viewport: bpy.props.BoolProperty(name="Hide Viewport", default=False)
    hide_render: bpy.props.BoolProperty(name="Hide Render", default=False)


class DeletionHistoryManager:

    
    @staticmethod
    def create_collection_backup(collection_names, context=None):
        """Create detailed backups of collections with full hierarchy and objects"""
        try:
            backup_data = {
                "type": "COLLECTIONS_WITH_HIERARCHY",
                "collections": [],
                "hierarchy": [],
                "timestamp": time.time(),
                "version": "1.0",
                "has_hierarchy": True,
                "has_objects": True
            }
            
            processed_collections = set()
            
            def process_collection(collection, parent_path=""):
                """Recursive function to process collection and its children"""
                if collection.name in processed_collections:
                    return
                    
                processed_collections.add(collection.name)
                
                coll_data = {
                    "name": collection.name,  
                    "original_name": collection.name,  
                    "parent": parent_path,
                    "hide_viewport": collection.hide_viewport,
                    "hide_render": collection.hide_render,
                    "color_tag": getattr(collection, 'color_tag', 'NONE'),
                    "objects": [],
                    "children": []
                }
                
                for obj in collection.objects:
                    obj_data = {
                        "name": obj.name,
                        "type": obj.type,
                        "location": [float(v) for v in list(obj.location)] if hasattr(obj, 'location') else [0, 0, 0]
                    }
                    coll_data["objects"].append(obj_data)
                
                backup_data["collections"].append(coll_data)
                
                hierarchy_entry = {
                    "original_name": collection.name, 
                    "parent": parent_path,
                    "children": [child.name for child in collection.children]
                }
                backup_data["hierarchy"].append(hierarchy_entry)
                
                for child in collection.children:
                    process_collection(child, f"{parent_path}/{collection.name}" if parent_path else collection.name)
            
            for coll_name in collection_names:
                if coll_name in bpy.data.collections:
                    coll = bpy.data.collections[coll_name]
                    process_collection(coll)
            
            print(f"✅ Collection backup created: {len(backup_data['collections'])} collections")
            return json.dumps(backup_data, indent=2)
            
        except Exception as e:
            print(f"❌ Error creating collection backup: {e}")
            import traceback
            traceback.print_exc()
            return ""
    @staticmethod
    def auto_clean_history(scene):
        """Remove history entries older than auto_clear_history_minutes (if set)."""
        if not hasattr(scene, 'deletion_history'):
            return
        history = scene.deletion_history
        prefs = DeletionHistoryManager.get_preferences()
        if not prefs or prefs.auto_clear_history_minutes <= 0:
            return
        import time
        current_time = time.time()
        cutoff = current_time - (prefs.auto_clear_history_minutes * 60)
        removed = 0
        for i in range(len(history) - 1, -1, -1):
            if history[i].timestamp < cutoff:
                history.remove(i)
                removed += 1
        if removed > 0:
            print(f"Auto‑cleaned {removed} history entries older than {prefs.auto_clear_history_minutes} minutes")

    @staticmethod
    def create_material_backup(material_names):
        """Crear backup detallado de materiales"""
        try:
            backup_data = {
                "type": "MATERIALS_DETAILED",
                "materials": [],
                "timestamp": time.time(),
                "version": "1.0",
                "has_node_data": True
            }
            
            for mat_name in material_names:
                if mat_name not in bpy.data.materials:
                    continue
                    
                mat = bpy.data.materials[mat_name]
                mat_data = {
                    "name": mat.name,
                    "use_nodes": mat.use_nodes,
                    "properties": {
                        "diffuse_color": [float(v) for v in list(mat.diffuse_color)],
                        "metallic": float(mat.metallic),
                        "roughness": float(mat.roughness),
                        "specular_intensity": float(mat.specular_intensity)
                    },
                    "assignments": []
                }
                
                for obj in bpy.data.objects:
                    if hasattr(obj, 'material_slots') and obj.material_slots:
                        for slot_idx, slot in enumerate(obj.material_slots):
                            if slot.material and slot.material.name == mat_name:
                                assignment = {
                                    "object_name": obj.name,
                                    "slot_index": slot_idx
                                }
                                mat_data["assignments"].append(assignment)
                
                if mat.use_nodes and mat.node_tree:
                    try:
                        nodes_data = []
                        for node in mat.node_tree.nodes:
                            if node.type == 'BSDF_PRINCIPLED':
                                node_data = {
                                    "type": node.type,
                                    "location": [node.location.x, node.location.y],
                                    "inputs": {}
                                }
                                
                                for inp in node.inputs:
                                    try:
                                        if inp.type == 'RGBA':
                                            if hasattr(inp, 'default_value'):
                                                value = list(inp.default_value)
                                                node_data["inputs"][inp.name] = [float(v) for v in value]
                                        elif inp.type == 'VALUE':
                                            if hasattr(inp, 'default_value'):
                                                node_data["inputs"][inp.name] = float(inp.default_value)
                                    except Exception as e:
                                        print(f"    ⚠️ Error saving input {inp.name}: {e}")
                                
                                nodes_data.append(node_data)
                                break  
                        
                        if nodes_data:
                            mat_data["node_tree"] = {
                                "nodes": nodes_data,
                                "tree_type": mat.node_tree.type if hasattr(mat.node_tree, 'type') else 'SHADER'
                            }
                    except Exception as e:
                        print(f"Error saving node tree for {mat.name}: {e}")
                
                backup_data["materials"].append(mat_data)
            
            return json.dumps(backup_data, indent=2)
        except Exception as e:
            print(f"Error creating material backup: {e}")
            import traceback
            traceback.print_exc()
            return ""

    @staticmethod
    def restore_collections_from_backup(backup_json, context):
        """Restore COMPLETE collections with hierarchy and objects"""
        try:
            if not backup_json or not backup_json.strip():
                print("❌ Empty collection backup")
                return False
                
            backup_data = json.loads(backup_json)
            
            if backup_data.get("type") != "COLLECTIONS_WITH_HIERARCHY":
                print("⚠️ Incorrect backup format for collections with hierarchy")
                return False
            
            print(f"🔄 Restoring collections with hierarchy...")
            
            collections_map = {}
            created_collections = []
            
            for coll_data in backup_data.get("collections", []):
                coll_name = coll_data.get("name", "")
                if not coll_name:
                    continue
                
                final_coll_name = coll_name
                counter = 1
                
                while final_coll_name in bpy.data.collections:
                    if counter == 1:
                        final_coll_name = f"{coll_name}_restoun"
                    else:
                        final_coll_name = f"{coll_name}_restoun_{counter:03d}"
                    counter += 1
                
                if final_coll_name != coll_name:
                    print(f"  🔄 Original collection '{coll_name}' already exists, creating as '{final_coll_name}'")
                
                try:
                    coll = bpy.data.collections.new(final_coll_name)
                    created_collections.append(final_coll_name)
                    print(f"  ✅ Collection created: {final_coll_name} (original: {coll_name})")
                except Exception as e:
                    print(f"  ❌ Error creating collection {final_coll_name}: {e}")
                    continue
                
                coll.hide_viewport = coll_data.get("hide_viewport", False)
                coll.hide_render = coll_data.get("hide_render", False)
                
                if "color_tag" in coll_data and hasattr(coll, 'color_tag'):
                    try:
                        coll.color_tag = coll_data["color_tag"]
                    except:
                        pass
                
                collections_map[final_coll_name] = {
                    "collection": coll,
                    "original_name": coll_name,
                    "final_name": final_coll_name,
                    "parent": coll_data.get("parent", ""),
                    "objects": coll_data.get("objects", []),
                    "properties": coll_data
                }
            
            for final_coll_name, coll_info in collections_map.items():
                original_name = coll_info["original_name"]
                parent_path = coll_info["parent"]
                
                if parent_path:
                    parent_original_name = parent_path.split('/')[-1] if '/' in parent_path else parent_path
                    
                    parent_final_name = parent_original_name
                    for coll_final, coll_data in collections_map.items():
                        if coll_data["original_name"] == parent_original_name:
                            parent_final_name = coll_final
                            break
                    
                    if parent_final_name != parent_original_name:
                        new_parent_path = parent_path
                        if '/' in parent_path:
                            parts = parent_path.split('/')
                            parts[-1] = parent_final_name
                            new_parent_path = '/'.join(parts)
                        else:
                            new_parent_path = parent_final_name
                        
                        coll_info["parent"] = new_parent_path
                        print(f"    🔄 Updated parent reference: {original_name} -> {parent_final_name}")
            
            for final_coll_name, coll_info in collections_map.items():
                coll = coll_info["collection"]
                parent_path = coll_info["parent"]
                
                if parent_path:
                    parent_name = parent_path.split('/')[-1] if '/' in parent_path else parent_path
                    
                    if parent_name and parent_name in collections_map:
                        parent_coll = collections_map[parent_name]["collection"]
                        
                        for current_parent in list(coll.users_collection):
                            if current_parent.name != parent_name:
                                try:
                                    current_parent.children.unlink(coll)
                                    print(f"    🔗 Disconnected from: {current_parent.name}")
                                except:
                                    pass
                        
                        is_linked = False
                        for child_coll in parent_coll.children:
                            if child_coll.name == final_coll_name:
                                is_linked = True
                                break
                        
                        if not is_linked:
                            try:
                                parent_coll.children.link(coll)
                                print(f"    📁 Connected: {final_coll_name} → {parent_name}")
                            except Exception as e:
                                print(f"    ⚠️ Error connecting {final_coll_name} to {parent_name}: {e}")
                    else:
                        print(f"    ⚠️ Parent not found: {parent_name} for {final_coll_name}")
            
            for final_coll_name, coll_info in collections_map.items():
                coll = coll_info["collection"]
                
                if len(coll.users_collection) == 0:
                    try:
                        in_scene = False
                        for child_coll in context.scene.collection.children:
                            if child_coll.name == final_coll_name:
                                in_scene = True
                                break
                        
                        if not in_scene:
                            context.scene.collection.children.link(coll)
                            print(f"    📍 Root collection connected to scene: {final_coll_name}")
                    except Exception as e:
                        print(f"    ⚠️ Error connecting root collection {final_coll_name} to scene: {e}")
            
            objects_linked = 0
            objects_created = 0
            for final_coll_name, coll_info in collections_map.items():
                coll = coll_info["collection"]
                objects_data = coll_info["objects"]
                
                for obj_data in objects_data:
                    obj_name = obj_data.get("name", "")
                    if not obj_name:
                        continue
                    
                    obj = None
                    
                    if obj_name in bpy.data.objects:
                        obj = bpy.data.objects[obj_name]
                        
                        is_in_collection = False
                        for coll_obj in coll.objects:
                            if coll_obj.name == obj_name:
                                is_in_collection = True
                                break
                        
                        if not is_in_collection:
                            try:
                                coll.objects.link(obj)
                                objects_linked += 1
                                print(f"    📍 Object linked: {obj_name} → {final_coll_name}")
                            except Exception as e:
                                print(f"    ⚠️ Error linking object {obj_name}: {e}")
                        
                        if "location" in obj_data and len(obj_data["location"]) == 3:
                            try:
                                obj.location = (
                                    float(obj_data["location"][0]),
                                    float(obj_data["location"][1]),
                                    float(obj_data["location"][2])
                                )
                            except:
                                pass
                        
                        obj.hide_viewport = False
                        obj.hide_render = False
                        try:
                            obj.select_set(True)
                        except:
                            pass
                    
                    else:
                        print(f"    ⚠️ Object not found: {obj_name}, creating placeholder...")
                        obj_type = obj_data.get("type", "MESH")
                        try:
                            if obj_type == 'MESH':
                                mesh = bpy.data.meshes.new(name=f"{obj_name}_Mesh")
                                bm_temp = bmesh.new()
                                bmesh.ops.create_cube(bm_temp, size=1.0)
                                bm_temp.to_mesh(mesh)
                                bm_temp.free()
                                mesh.update()
                                obj = bpy.data.objects.new(obj_name, mesh)
                            elif obj_type == 'EMPTY':
                                obj = bpy.data.objects.new(obj_name, None)
                            elif obj_type == 'CAMERA':
                                camera = bpy.data.cameras.new(name=f"{obj_name}_Camera")
                                obj = bpy.data.objects.new(obj_name, camera)
                            elif obj_type == 'LIGHT':
                                light = bpy.data.lights.new(name=f"{obj_name}_Light", type='POINT')
                                obj = bpy.data.objects.new(obj_name, light)
                            elif obj_type == 'CURVE':
                                curve = bpy.data.curves.new(name=f"{obj_name}_Curve", type='CURVE')
                                obj = bpy.data.objects.new(obj_name, curve)
                            elif obj_type == 'ARMATURE':
                                armature = bpy.data.armatures.new(name=f"{obj_name}_Armature")
                                obj = bpy.data.objects.new(obj_name, armature)
                            else:
                                obj = bpy.data.objects.new(obj_name, None)
                            
                            if obj:
                                if "location" in obj_data and len(obj_data["location"]) == 3:
                                    try:
                                        obj.location = (
                                            float(obj_data["location"][0]),
                                            float(obj_data["location"][1]),
                                            float(obj_data["location"][2])
                                        )
                                    except:
                                        pass
                                
                                coll.objects.link(obj)
                                obj.hide_viewport = False
                                obj.hide_render = False
                                objects_created += 1
                                print(f"    ✅ Created and linked object: {obj_name} → {final_coll_name}")
                        except Exception as e:
                            print(f"    ❌ Error creating object {obj_name}: {e}")
            
            print(f"✅ Collections processed: {len(collections_map)}")
            print(f"✅ Collections created (with suffix _restoun if necessary): {len(created_collections)}")
            print(f"✅ Objects linked: {objects_linked}")
            print(f"✅ Objects recreated: {objects_created}")
            
            DeletionHistoryManager.force_view_layer_update(context)
            
            return True
            
        except Exception as e:
            print(f"❌ Error restoring collections from backup: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    @staticmethod
    def force_view_layer_update(context):
        """Force update of View Layer"""
        try:
            print("🔄 Forcing a View Layer Update...")
            
            context.view_layer.update()
            
            for area in context.screen.areas:
                if area.type in ['VIEW_3D', 'OUTLINER']:
                    area.tag_redraw()
            
            bpy.context.evaluated_depsgraph_get().update()
            
            print("✅ View Layer updated")
        except Exception as e:
            print(f"⚠️ Error forcing View Layer update: {e}")

    @staticmethod
    def find_restored_collection(original_name):
        """search for the restored collection by its original name"""
        print(f"  🔍 Looking for a restored collection for: {original_name}")
        
        if original_name in bpy.data.collections:
            coll = bpy.data.collections[original_name]
            print(f"    ✅ Found original collection: {original_name}")
            return coll
        
        for coll in bpy.data.collections:
            if coll.name == f"{original_name}_restoun":
                print(f"    ✅ Found restored collection: {coll.name} (for {original_name})")
                return coll
            elif coll.name.startswith(f"{original_name}_restoun_"):
                print(f"    ✅ Found restored collection with number: {coll.name} (for {original_name})")
                return coll
        
        print(f"    ❌ No restored collection found for: {original_name}")
        return None
            
    @staticmethod
    def create_node_group_backup(node_group_names):
        try:
            backup_data = {
                "type": "NODE_GROUPS_DETAILED",
                "node_groups": [],
                "timestamp": time.time(),
                "version": "1.0",                    
                "has_node_data": True,
                "has_user_data": True,
                "has_modifier_details": True         
            }

            for ng_name in node_group_names:
                if ng_name not in bpy.data.node_groups:
                    continue

                ng = bpy.data.node_groups[ng_name]
                ng_data = {
                    "name": ng.name,
                    "type": ng.type,
                    "users_count": ng.users,
                    "nodes": [],
                    "links": [],
                    "users": {
                        "materials": [],
                        "modifiers": [],               
                        "node_groups": []
                    }
                }

                for node in ng.nodes:
                    node_data = {
                        "name": node.name,
                        "type": node.type,
                        "location": [node.location.x, node.location.y],
                        "width": node.width if hasattr(node, 'width') else 200,
                        "label": node.label if hasattr(node, 'label') else ""
                    }
                    ng_data["nodes"].append(node_data)

                for link in ng.links:
                    link_data = {
                        "from_node": link.from_node.name if link.from_node else "",
                        "from_socket": link.from_socket.name if link.from_socket else "",
                        "to_node": link.to_node.name if link.to_node else "",
                        "to_socket": link.to_socket.name if link.to_socket else ""
                    }
                    ng_data["links"].append(link_data)

                for mat in bpy.data.materials:
                    if mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.type == 'GROUP' and node.node_tree == ng:
                                ng_data["users"]["materials"].append({
                                    "material": mat.name,
                                    "node_name": node.name
                                })

                for obj in bpy.data.objects:
                    for mod in obj.modifiers:
                        if mod.type == 'NODES' and mod.node_group == ng:

                            inputs_data = {}
                            if hasattr(mod, 'node_group') and mod.node_group:

                                try:
                                    if hasattr(mod, 'settings'):
                                        for key in dir(mod.settings):
                                            if not key.startswith('_') and not callable(getattr(mod.settings, key)):
                                                val = getattr(mod.settings, key)
                                                if hasattr(val, '__len__') and not isinstance(val, str):
                                                    inputs_data[key] = list(val)
                                                elif isinstance(val, (int, float, bool, str)):
                                                    inputs_data[key] = val
                                except Exception as e:
                                    print(f"Error capturing modifier inputs: {e}")

                            mod_data = {
                                "object": obj.name,
                                "modifier": mod.name,
                                "type": mod.type,
                                "show_viewport": mod.show_viewport,
                                "show_render": mod.show_render,
                                "node_group_name": ng.name,
                                "inputs": inputs_data
                            }
                            ng_data["users"]["modifiers"].append(mod_data)

                for other_ng in bpy.data.node_groups:
                    if other_ng == ng:
                        continue
                    for node in other_ng.nodes:
                        if node.type == 'GROUP' and node.node_tree == ng:
                            ng_data["users"]["node_groups"].append({
                                "node_group": other_ng.name,
                                "node_name": node.name
                            })

                backup_data["node_groups"].append(ng_data)

            return json.dumps(backup_data, indent=2)
        except Exception as e:
            print(f"Error creating node group backup: {e}")
            import traceback
            traceback.print_exc()
            return ""

    @staticmethod
    def restore_node_groups_from_backup(backup_json):
        """Restore node groups from detailed backup, including node structure and user reassignments.
        Returns number of successfully restored node groups.
        """
        try:
            if not backup_json or not backup_json.strip():
                print("❌ Empty node groups backup")
                return 0

            backup_data = json.loads(backup_json)

            if backup_data.get("type") != "NODE_GROUPS_DETAILED":
                print("⚠️ Incorrect backup format for node groups")
                return 0

            restored_count = 0
            total_node_groups = len(backup_data.get("node_groups", []))

            for ng_data in backup_data.get("node_groups", []):
                ng_name = ng_data.get("name", "")
                ng_type = ng_data.get("type", "SHADER")

                if not ng_name:
                    continue

                print(f"\n🔄 Restoring node group: {ng_name} ({ng_type})")
                group_ok = True  

                if ng_name in bpy.data.node_groups:
                    existing = bpy.data.node_groups[ng_name]
                    existing_name = existing.name  
                    try:

                        for mat in bpy.data.materials:
                            if mat.use_nodes and mat.node_tree:
                                for node in mat.node_tree.nodes:
                                    if node.type == 'GROUP' and node.node_tree == existing:
                                        node.node_tree = None
                        for obj in bpy.data.objects:
                            for mod in obj.modifiers:
                                if mod.type == 'NODES' and mod.node_group == existing:
                                    mod.node_group = None
                        for other_ng in bpy.data.node_groups:
                            if other_ng == existing:
                                continue
                            for node in other_ng.nodes:
                                if node.type == 'GROUP' and node.node_tree == existing:
                                    node.node_tree = None
                        bpy.data.node_groups.remove(existing, do_unlink=True)
                        print(f"  ✅ Existing node group '{existing_name}' removed")
                    except Exception as e:
                        print(f"  ⚠️ Could not remove existing node group '{existing_name}': {e}")
                        group_ok = False

                if not group_ok:
                    print(f"  ❌ Skipping restoration of '{ng_name}' due to previous error")
                    continue

                try:
                    ng = bpy.data.node_groups.new(name=ng_name, type=ng_type)
                    print(f"  ✅ New node group created: {ng_name}")
                except Exception as e:
                    print(f"  ❌ Failed to create node group '{ng_name}': {e}")
                    continue  

                node_map = {}
                nodes_data = ng_data.get("nodes", [])
                for node_data in nodes_data:
                    node_name = node_data.get("name", "")
                    node_type = node_data.get("type", "")
                    try:
                        if node_type == 'GROUP_INPUT':
                            node = ng.nodes.new(type='NodeGroupInput')
                        elif node_type == 'GROUP_OUTPUT':
                            node = ng.nodes.new(type='NodeGroupOutput')
                        elif node_type == 'FRAME':
                            node = ng.nodes.new(type='NodeFrame')
                        elif node_type == 'REROUTE':
                            node = ng.nodes.new(type='NodeReroute')
                        else:
                            try:
                                node = ng.nodes.new(type=node_type)
                            except:
                                node = ng.nodes.new(type='ShaderNodeMath')
                                print(f"    ⚠️ Node type '{node_type}' not available, using fallback")
                        node.name = node_name
                        if "location" in node_data:
                            node.location = node_data["location"]
                        if "width" in node_data:
                            node.width = node_data["width"]
                        if "label" in node_data:
                            node.label = node_data["label"]
                        node_map[node_name] = node
                    except Exception as e:
                        print(f"    ❌ Error creating node {node_name} ({node_type}): {e}")

                links_data = ng_data.get("links", [])
                for link_data in links_data:
                    from_node_name = link_data.get("from_node", "")
                    from_socket_name = link_data.get("from_socket", "")
                    to_node_name = link_data.get("to_node", "")
                    to_socket_name = link_data.get("to_socket", "")
                    if not all([from_node_name, to_node_name, from_socket_name, to_socket_name]):
                        continue
                    if from_node_name not in node_map or to_node_name not in node_map:
                        continue
                    from_node = node_map[from_node_name]
                    to_node = node_map[to_node_name]
                    from_socket = None
                    to_socket = None
                    for socket in from_node.outputs:
                        if socket.name == from_socket_name:
                            from_socket = socket
                            break
                    for socket in to_node.inputs:
                        if socket.name == to_socket_name:
                            to_socket = socket
                            break
                    if from_socket and to_socket:
                        try:
                            ng.links.new(from_socket, to_socket)
                        except Exception as e:
                            print(f"    ⚠️ Could not create link {from_node_name}.{from_socket_name} -> {to_node_name}.{to_socket_name}: {e}")

                users_info = ng_data.get("users", {})

                for mat_info in users_info.get("materials", []):
                    mat_name = mat_info.get("material")
                    node_name = mat_info.get("node_name")
                    if mat_name and mat_name in bpy.data.materials:
                        mat = bpy.data.materials[mat_name]
                        if mat.use_nodes and mat.node_tree:
                            for node in mat.node_tree.nodes:
                                if node.name == node_name and node.type == 'GROUP':
                                    try:
                                        node.node_tree = ng
                                        print(f"    ✅ Assigned to material '{mat_name}'")
                                    except Exception as e:
                                        print(f"    ⚠️ Could not assign to material '{mat_name}': {e}")

                for mod_info in users_info.get("modifiers", []):
                    obj_name = mod_info.get("object")
                    mod_name = mod_info.get("modifier")
                    if obj_name and obj_name in bpy.data.objects:
                        obj = bpy.data.objects[obj_name]
                        mod = obj.modifiers.get(mod_name)
                        if mod and mod.type == 'NODES':
                            try:
                                mod.node_group = ng
                                print(f"    ✅ Assigned to modifier '{mod_name}' on '{obj_name}'")
                            except Exception as e:
                                print(f"    ⚠️ Could not assign to modifier '{mod_name}': {e}")
                        else:

                            try:
                                new_mod = obj.modifiers.new(name=mod_name, type='NODES')
                                new_mod.node_group = ng
                                print(f"    ✅ Created and assigned new modifier '{mod_name}' on '{obj_name}'")
                            except Exception as e:
                                print(f"    ⚠️ Could not create modifier '{mod_name}' on '{obj_name}': {e}")

                for ng_info in users_info.get("node_groups", []):
                    parent_ng_name = ng_info.get("node_group")
                    node_name = ng_info.get("node_name")
                    if parent_ng_name and parent_ng_name in bpy.data.node_groups:
                        parent_ng = bpy.data.node_groups[parent_ng_name]
                        for node in parent_ng.nodes:
                            if node.name == node_name and node.type == 'GROUP':
                                try:
                                    node.node_tree = ng
                                    print(f"    ✅ Assigned to nested group '{parent_ng_name}'")
                                except Exception as e:
                                    print(f"    ⚠️ Could not assign to nested group '{parent_ng_name}': {e}")

                for mod_info in users_info.get("modifiers", []):
                    obj_name = mod_info.get("object")
                    mod_name = mod_info.get("modifier")
                    inputs_data = mod_info.get("inputs", {})
                    if not inputs_data:
                        continue
                    if obj_name and obj_name in bpy.data.objects:
                        obj = bpy.data.objects[obj_name]
                        mod = obj.modifiers.get(mod_name)
                        if mod and mod.type == 'NODES' and hasattr(mod, 'settings'):
                            for input_name, input_value in inputs_data.items():
                                try:
                                    if hasattr(mod.settings, input_name):
                                        current = getattr(mod.settings, input_name)
                                        if isinstance(current, float) and isinstance(input_value, (int, float)):
                                            setattr(mod.settings, input_name, float(input_value))
                                        elif isinstance(current, int) and isinstance(input_value, (int, float)):
                                            setattr(mod.settings, input_name, int(input_value))
                                        elif isinstance(current, bool) and isinstance(input_value, (bool, int)):
                                            setattr(mod.settings, input_name, bool(input_value))
                                        elif hasattr(current, '__len__') and isinstance(input_value, list):
                                            for i, val in enumerate(input_value):
                                                if i < len(current):
                                                    current[i] = float(val)
                                except Exception as e:
                                    print(f"      ⚠️ Could not restore input {input_name}: {e}")

                restored_count += 1
                print(f"  ✅ Node group '{ng_name}' restored successfully")

            print(f"\n📊 Restored {restored_count} out of {total_node_groups} node groups")
            return restored_count

        except Exception as e:
            print(f"❌ Critical error in restore_node_groups_from_backup: {e}")
            import traceback
            traceback.print_exc()
            return 0

    @staticmethod
    def create_simple_node_group(name, ng_type="SHADER"):
        """Create a basic node group for simple restoration"""
        try:
            if name in bpy.data.node_groups:
                print(f"⚠️ Node group {name} ya existe")
                return None
            
            ng = bpy.data.node_groups.new(name=name, type=ng_type)
            
            if ng_type == 'GEOMETRY':
                input_node = ng.nodes.new(type='NodeGroupInput')
                input_node.location = (-300, 0)
                
                output_node = ng.nodes.new(type='NodeGroupOutput')
                output_node.location = (300, 0)
                
            elif ng_type == 'SHADER':
                input_node = ng.nodes.new(type='NodeGroupInput')
                input_node.location = (-400, 0)
                
                bsdf_node = ng.nodes.new(type='ShaderNodeBsdfPrincipled')
                bsdf_node.location = (-100, 0)
                
                output_node = ng.nodes.new(type='NodeGroupOutput')
                output_node.location = (200, 0)
                
                ng.links.new(bsdf_node.outputs[0], output_node.inputs[0])
                
            elif ng_type == 'COMPOSITING':
                input_node = ng.nodes.new(type='CompositorNodeRLayers')
                input_node.location = (-300, 0)
                
                output_node = ng.nodes.new(type='CompositorNodeComposite')
                output_node.location = (100, 0)
                
                ng.links.new(input_node.outputs[0], output_node.inputs[0])
            
            print(f"✅ Successfully created simple node group: {name} ({ng_type})")
            return ng
            
        except Exception as e:
            print(f"❌ Error creating simple node group {name}: {e}")
            return None
            
    @staticmethod
    def link_object_to_restored_collection(obj, original_collection_names, context):
        """Link object to restored collection if one exists"""
        if not original_collection_names:
            return False
        
        print(f"  🔍 Trying to link {obj.name} to restored collection")
        
        for coll_name in original_collection_names:
            print(f"    Searching for collection: {coll_name}")
            
            target_coll = None
            
            if coll_name in bpy.data.collections:
                target_coll = bpy.data.collections[coll_name]
                print(f"      ✅ Found original collection: {coll_name}")
            
            if not target_coll:
                for candidate in bpy.data.collections:
                    if candidate.name == f"{coll_name}_restoun":
                        target_coll = candidate
                        print(f"      ✅ Found restored collection with suffix: {candidate.name}")
                        break
            
            if not target_coll:
                for candidate in bpy.data.collections:
                    if candidate.name.startswith(f"{coll_name}_restoun_"):
                        target_coll = candidate
                        print(f"      ✅ Found restored collection with suffix and number: {candidate.name}")
                        break
            
            if target_coll:
                try:
                    is_linked = False
                    for coll_obj in target_coll.objects:
                        if coll_obj.name == obj.name:
                            is_linked = True
                            print(f"      ℹ️ {obj.name} is already in {target_coll.name}")
                            break
                    
                    if not is_linked:
                        for current_coll in list(obj.users_collection):
                            current_coll.objects.unlink(obj)
                            print(f"      🔗 Unlinked from: {current_coll.name}")
                        
                        target_coll.objects.link(obj)
                        print(f"      ✅ {obj.name} LINKED TO RESTORED COLLECTION: {target_coll.name}")
                        return True
                    else:
                        return True
                        
                except Exception as e:
                    print(f"      ❌ Error linking {obj.name} to {target_coll.name}: {e}")
            else:
                print(f"      ⚠️ Collection {coll_name} not found (neither original nor restored)")
        
        return False

    @staticmethod
    def create_geometry_backup(object_names, context=None):
        """Geometry backup with exact positions and associated materials"""
        try:
            backup_data = {
                "type": "GEOMETRY_WITH_EVERYTHING", 
                "objects": [], 
                "timestamp": time.time(),
                "has_position_data": True,
                "has_material_data": True,
                "has_modifier_data": True 
            }
            
            for obj_name in object_names:
                if obj_name not in bpy.data.objects:
                    continue
                    
                obj = bpy.data.objects[obj_name]
                obj_data = {
                    "name": obj.name, 
                    "type": obj.type,
                    "location": [float(v) for v in list(obj.location)],
                    "rotation_euler": [float(v) for v in list(obj.rotation_euler)] if hasattr(obj, 'rotation_euler') else [0, 0, 0],
                    "scale": [float(v) for v in list(obj.scale)],
                    "collection_names": [col.name for col in obj.users_collection],
                    "hide_viewport": obj.hide_viewport,
                    "hide_render": obj.hide_render,
                    "material_slots": [],
                    "modifiers": [], 
                    "has_mesh_data": False
                }
                
                if hasattr(obj, 'material_slots') and obj.material_slots:
                    for slot_idx, slot in enumerate(obj.material_slots):
                        if slot.material:
                            mat = slot.material
                            obj_data["material_slots"].append({
                                "slot_index": slot_idx,
                                "material_name": mat.name,
                                "material_exists": True
                            })
                
                if hasattr(obj, 'modifiers'):
                    for modifier in obj.modifiers:
                        mod_data = {
                            "name": modifier.name,
                            "type": modifier.type,
                            "show_viewport": modifier.show_viewport,
                            "show_render": modifier.show_render
                        }
                        
                        if modifier.type == 'NODES':
                            if hasattr(modifier, 'node_group') and modifier.node_group:
                                mod_data["node_group_name"] = modifier.node_group.name
                                mod_data["node_group_type"] = getattr(modifier.node_group, 'type', 'GEOMETRY')
                            
                            if hasattr(modifier, 'settings'):
                                try:
                                    inputs_data = {}
                                    if hasattr(modifier.settings, 'items'):
                                        for prop_name, prop_value in modifier.settings.items():
                                            try:
                                                if hasattr(prop_value, '__len__'):
                                                    inputs_data[prop_name] = list(prop_value)
                                                elif hasattr(prop_value, '__float__'):
                                                    inputs_data[prop_name] = float(prop_value)
                                                else:
                                                    inputs_data[prop_name] = str(prop_value)
                                            except:
                                                inputs_data[prop_name] = str(prop_value)
                                    mod_data["inputs"] = inputs_data
                                except Exception as e:
                                    print(f"  ⚠️ Error saving modifier inputs {modifier.name}: {e}")
                        
                        obj_data["modifiers"].append(mod_data)
                
                if obj.type == 'MESH' and obj.data and len(obj.data.vertices) < 1000:
                    mesh = obj.data
                    try:
                        obj_data["vertices"] = [[v.co.x, v.co.y, v.co.z] for v in mesh.vertices]
                        obj_data["polygons"] = [list(p.vertices) for p in mesh.polygons]
                        obj_data["has_mesh_data"] = True
                    except:
                        pass
                
                backup_data["objects"].append(obj_data)
            
            print(f"✅ Geometry Nodes backup created: {len(backup_data['objects'])} objects")
            return json.dumps(backup_data)
            
        except Exception as e:
            print(f"❌ Error in Geometry Nodes backup: {e}")
            import traceback
            traceback.print_exc()
            return ""
        
        finally:
            DeletionHistoryManager.force_view_layer_update(context)
        
    def _do_restore_geometry_nodes_independent(entry, context):
        """Restore objects that had independent Geometry Nodes modifiers."""
        print(f"\n🎯 RESTORING GEOMETRY INDEPENDENT NODES")
        
        if not getattr(entry, 'data_backup', None):
            print("❌ There is no backup available for Geometry Nodes")
            return False
        
        try:
            backup_data = json.loads(entry.data_backup)
            restored_count = 0
            modifiers_restored = 0
            
            for obj_data in backup_data.get("objects", []):
                obj_name = obj_data.get("name", "")
                if not obj_name:
                    continue
                
                print(f"\n🔍 Processing object: {obj_name}")
                
                obj = None
                if obj_name in bpy.data.objects:
                    obj = bpy.data.objects[obj_name]
                    print(f"  ✅ Object already exists: {obj_name}")
                    
                    if obj.hide_viewport or obj.hide_render or len(obj.users_collection) == 0:
                        if len(obj.users_collection) == 0:
                            try:
                                context.collection.objects.link(obj)
                                print(f"  📍 Object linked to current collection")
                            except:
                                pass
                        
                        obj.hide_viewport = False
                        obj.hide_render = False
                        obj.select_set(True)
                else:
                    try:
                        if obj_data.get("type") == 'MESH':
                            mesh = bpy.data.meshes.new(name=f"{obj_name}_mesh")
                            bm = bmesh.new()
                            bmesh.ops.create_cube(bm, size=1.0)
                            bm.to_mesh(mesh)
                            bm.free()
                            mesh.update()
                            
                            obj = bpy.data.objects.new(obj_name, mesh)
                            context.collection.objects.link(obj)
                            print(f"  ✅ Object created: {obj_name}")
                        else:
                            print(f"  ⚠️ Unsupported object type: {obj_data.get('type')}")
                            continue
                    except Exception as e:
                        print(f"  ❌ Error creating object: {e}")
                        continue
                
                if obj:
                    modifiers_data = obj_data.get("modifiers", [])
                    
                    for mod_data in modifiers_data:
                        if mod_data.get("type") == 'NODES':
                            print(f"  🔧 Processing Geometry Nodes: {mod_data.get('name', 'Unnamed')}")
                            
                            existing_mod = None
                            if hasattr(obj, 'modifiers'):
                                existing_mod = obj.modifiers.get(mod_data.get("name", ""))
                            
                            if existing_mod and existing_mod.type == 'NODES':
                                print(f"    ✅Modifier already exists, skipping")
                                continue
                            
                            try:
                                mod_name = mod_data.get("name", "GeometryNodes")
                                new_mod = obj.modifiers.new(name=mod_name, type='NODES')
                                
                                node_group_name = mod_data.get("node_group_name", "")
                                if node_group_name and node_group_name in bpy.data.node_groups:
                                    new_mod.node_group = bpy.data.node_groups[node_group_name]
                                    print(f"    ✅ Assigned node group: {node_group_name}")
                                else:
                                    print(f"    ⚠️ Node group not found: {node_group_name}")
                                
                                new_mod.show_viewport = mod_data.get("show_viewport", True)
                                new_mod.show_render = mod_data.get("show_render", True)
                                
                                inputs_data = mod_data.get("inputs", {})
                                if inputs_data and hasattr(new_mod, 'settings'):
                                    print(f"    🔧 Restoring {len(inputs_data)} input(s)...")
                                    
                                    for input_name, input_value in inputs_data.items():
                                        try:
                                            if hasattr(new_mod.settings, input_name):
                                                try:
                                                    if isinstance(input_value, (int, float)):
                                                        setattr(new_mod.settings, input_name, float(input_value))
                                                    elif isinstance(input_value, list):
                                                        current_attr = getattr(new_mod.settings, input_name)
                                                        if hasattr(current_attr, '__len__'):
                                                            if len(current_attr) == len(input_value):
                                                                for i in range(len(input_value)):
                                                                    current_attr[i] = float(input_value[i])
                                                except Exception as e:
                                                    print(f"      ⚠️ Error en input {input_name}: {e}")
                                        except:
                                            pass
                                
                                modifiers_restored += 1
                                print(f"    ✅ Geometry Nodes restored: {mod_name}")
                                
                            except Exception as e:
                                print(f"    ❌ Error creating Geometry Nodes: {e}")
                                import traceback
                                traceback.print_exc()
                    
                    restored_count += 1
            
            print(f"\n📊 RESULTADOS:")
            print(f"  Processed objects: {restored_count}")
            print(f"  Geometry Nodes restored: {modifiers_restored}")
            
            context.view_layer.update()
            for area in context.screen.areas:
                area.tag_redraw()
            
            return restored_count > 0
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR restoring Geometry Nodes: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def create_materials_backup_for_objects(object_names):
        """Create backup only of the materials used by the objects to be deleted."""
        try:
            materials_data = {}
            
            for obj_name in object_names:
                if obj_name not in bpy.data.objects:
                    continue
                    
                obj = bpy.data.objects[obj_name]
                
                if hasattr(obj, 'material_slots') and obj.material_slots:
                    for slot_idx, slot in enumerate(obj.material_slots):
                        if slot.material:
                            mat = slot.material
                            mat_name = mat.name
                            
                            if mat_name not in materials_data:
                                mat_data = {
                                    "name": mat.name,
                                    "use_nodes": mat.use_nodes,
                                    "properties": {
                                        "diffuse_color": [float(v) for v in list(mat.diffuse_color)],
                                        "metallic": float(mat.metallic),
                                        "roughness": float(mat.roughness),
                                        "specular_intensity": float(mat.specular_intensity)
                                    },
                                    "assignments": []
                                }
                                
                                if mat.use_nodes and mat.node_tree:
                                    try:
                                        nodes_data = []
                                        for node in mat.node_tree.nodes:
                                            if node.type == 'BSDF_PRINCIPLED':
                                                node_data = {
                                                    "type": node.type,
                                                    "location": [node.location.x, node.location.y],
                                                    "inputs": {}
                                                }
                                                
                                                for inp in node.inputs:
                                                    try:
                                                        if inp.type == 'RGBA':
                                                            if hasattr(inp, 'default_value'):
                                                                value = list(inp.default_value)
                                                                node_data["inputs"][inp.name] = [float(v) for v in value]
                                                        elif inp.type == 'VALUE':
                                                            if hasattr(inp, 'default_value'):
                                                                node_data["inputs"][inp.name] = float(inp.default_value)
                                                    except Exception as e:
                                                        print(f"    ⚠️ Error saving input {inp.name}: {e}")
                                                
                                                nodes_data.append(node_data)
                                                break  
                                        
                                        if nodes_data:
                                            mat_data["node_tree"] = {
                                                "nodes": nodes_data,
                                                "tree_type": mat.node_tree.type if hasattr(mat.node_tree, 'type') else 'SHADER'
                                            }
                                    except Exception as e:
                                        print(f"Error saving node tree for {mat.name}: {e}")
                                
                                materials_data[mat_name] = mat_data
                            
                            assignment = {
                                "object_name": obj.name,
                                "slot_index": slot_idx
                            }
                            materials_data[mat_name]["assignments"].append(assignment)
            
            backup_data = {
                "type": "OBJECT_MATERIALS_BACKUP",
                "materials": list(materials_data.values()),
                "objects": object_names,
                "timestamp": time.time(),
                "version": "1.0"
            }
            
            return json.dumps(backup_data, indent=2)
            
        except Exception as e:
            print(f"Error creating backup of materials for objects: {e}")
            import traceback
            traceback.print_exc()
            return ""

    @staticmethod
    def get_history_collection(scene):
        """Get or create the history collection"""
        if not hasattr(scene, 'deletion_history'):
            return None
        return scene.deletion_history
    
    @staticmethod
    def add_history_entry(scene, deletion_type, item_names, count=1, data_backup=""):
        """Add a new entry to the deletion history"""
        if not hasattr(scene, 'deletion_history'):
            print("ERROR: No deletion_history attribute in scene")
            return None

        try:
            import sys
            for module_name in sys.modules:
                if 'botton_remove' in module_name:
                    module = sys.modules[module_name]
                    if hasattr(module, 'get_addon_prefs'):
                        prefs = module.get_addon_prefs(bpy.context)
                        if prefs and not prefs.enable_deletion_history:
                            return None
                        if prefs and getattr(prefs, 'permanent_delete', False):
                            print("PERMANENT DELETE active - skipping history entry")
                            return None
                        break
        except:
            pass

        history = scene.deletion_history

        try:
            prefs = DeletionHistoryManager.get_preferences()
            if prefs and prefs.max_history_actions > 0 and len(history) >= prefs.max_history_actions:
                to_remove = len(history) - prefs.max_history_actions + 1
                for i in range(to_remove):
                    history.remove(0)
        except:
            pass

        try:
            prefs = DeletionHistoryManager.get_preferences()
            if prefs and prefs.auto_clear_history_minutes > 0:
                current_time = time.time()
                cutoff = current_time - (prefs.auto_clear_history_minutes * 60)
                for i in range(len(history) - 1, -1, -1):
                    if history[i].timestamp < cutoff:
                        history.remove(i)
        except Exception as e:
            print(f"Error in auto-clear by minutes: {e}")

        entry = history.add()
        max_id = max([e.deletion_id for e in history], default=-1)
        entry.deletion_id = max_id + 1
        entry.deletion_type = deletion_type
        entry.timestamp = time.time()

        if isinstance(item_names, list):
            item_names_str = ",".join(str(n) for n in item_names)
        elif isinstance(item_names, str):
            item_names_str = item_names
        else:
            item_names_str = str(item_names)

        entry.item_names = item_names_str
        entry.count = count
        entry.data_backup = data_backup
        entry.can_restore = True

        print(f"✓ History entry added: {deletion_type} - {count} items")
        return entry
    
    @staticmethod
    def get_preferences():
        """Get addon preferences"""
        try:
            import sys
            for module_name in sys.modules:
                if module_name.startswith('botton_remove'):
                    module = sys.modules[module_name]
                    if hasattr(module, 'get_addon_prefs'):
                        return module.get_addon_prefs(bpy.context)
        except Exception as e:
            print(f"Error getting preferences: {e}")
        
        try:
            for addon_name in bpy.context.preferences.addons.keys():
                if 'botton' in addon_name.lower() or 'remove' in addon_name.lower():
                    return bpy.context.preferences.addons[addon_name].preferences
        except:
            pass
        
        return None
    
    @staticmethod
    def format_timestamp(timestamp):
        """Format timestamp to readable relative time"""
        try:
            import time
            now = time.time()
            diff = now - timestamp
            
            if diff < 60: 
                return "Just now"
            elif diff < 3600:  
                minutes = int(diff / 60)
                return f"{minutes}m ago"
            elif diff < 86400:  
                hours = int(diff / 3600)
                minutes = int((diff % 3600) / 60)
                return f"{hours}h {minutes}m ago"
            else:  
                days = int(diff / 86400)
                hours = int((diff % 86400) / 3600)
                return f"{days}d {hours}h ago"
        except:
            return "Unknown"
    
    @staticmethod
    def get_history_summary(scene):
        """Get summary of history"""
        if not hasattr(scene, 'deletion_history'):
            return {'total_actions': 0, 'by_type': {}, 'recent': []}
        
        summary = {
            'total_actions': len(scene.deletion_history),
            'by_type': {},
            'recent': []
        }
        
        type_names = {
            'MATERIAL': "Materials",
            'GEOMETRY': "Geometry",
            'NODE_GROUP': "Node Groups",
            'COLLECTION': "Collections",
            'EMPTY_SLOT': "Empty Slots",
            'ORPHAN_DATA': "Clean Orphan Data",
            'ALL_MATERIALS': "All Materials",
            'UNUSED_MATERIALS': "Unused Materials",
        }
        
        for entry in scene.deletion_history:
            summary['by_type'][entry.deletion_type] = summary['by_type'].get(entry.deletion_type, 0) + 1
            
            if len(summary['recent']) < 5:
                summary['recent'].append({
                    'type': type_names.get(entry.deletion_type, entry.deletion_type),
                    'count': entry.count,
                    'time': DeletionHistoryManager.format_timestamp(entry.timestamp),
                    'id': entry.deletion_id
                })
        
        return summary
    
    @staticmethod
    def restore_from_backup(backup_json):
        """Restore items from backup JSON"""
        try:
            if not backup_json:
                return 0
                
            backup_data = json.loads(backup_json)
            restored_count = 0
            
            if backup_data.get("type") == "MATERIALS":
                for mat_data in backup_data.get("materials", []):
                    if mat_data["name"] not in bpy.data.materials:
                        mat = bpy.data.materials.new(name=mat_data["name"])
                        restored_count += 1
            
            print(f"✓ Restored {restored_count} items from backup")
            return restored_count
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return 0

    @staticmethod
    def get_trash_collection(context):
        """Obtain or create the hidden collection WITHOUT linking it to the scene"""
        scene = context.scene if context else bpy.context.scene
        TRASH_COLLECTION_NAME = "Trash Collection"
        
        for coll in bpy.data.collections:
            if coll.name == TRASH_COLLECTION_NAME:
                coll.hide_viewport = True
                coll.hide_render = True
                return coll
        
        trash = bpy.data.collections.new(TRASH_COLLECTION_NAME)

        trash.hide_viewport = True
        trash.hide_render = True
        return trash

    @staticmethod
    def parse_entry_items(entry):
        """Parse entry.item_names into a list of individual item strings (one per deleted item).
        Handles both correct format (comma-separated) and corrupted format from old bug
        where str(list) was used instead of ','.join(list).
        """
        if not entry or not getattr(entry, "item_names", None):
            return []
        
        raw = entry.item_names.strip()
        
        if raw.startswith("[") and raw.endswith("]"):
            raw = raw[1:-1]  
            items = []
            for part in raw.split(","):
                part = part.strip()
                if (part.startswith("'") and part.endswith("'")) or \
                   (part.startswith('"') and part.endswith('"')):
                    part = part[1:-1]
                part = part.strip()
                if part and not (part.startswith("... (+") and part.endswith(" more)")):
                    items.append(part)
            return items
        
        items = []
        for part in raw.split(","):
            part = part.strip()
            if (part.startswith("'") and part.endswith("'")) or \
               (part.startswith('"') and part.endswith('"')):
                part = part[1:-1]
            part = part.strip()
            if part and not (part.startswith("... (+") and part.endswith(" more)")):
                items.append(part)
        return items

    @staticmethod
    def restore_materials_from_backup(backup_json, context):
        """Restore materials from backup if they do not exist."""
        try:
            if not backup_json:
                return 0
                
            backup_data = json.loads(backup_json)
            
            if backup_data.get("type") != "OBJECT_MATERIALS_BACKUP":
                return 0
            
            restored_count = 0
            
            for mat_data in backup_data.get("materials", []):
                mat_name = mat_data.get("name", "")
                if not mat_name:
                    continue
                
                if mat_name in bpy.data.materials:
                    print(f"✓ Material {mat_name} It already exists, there's no need to create it")
                    continue
                
                try:
                    mat = bpy.data.materials.new(name=mat_name)
                    mat.use_nodes = True
                    
                    if "properties" in mat_data and "diffuse_color" in mat_data["properties"]:
                        try:
                            color_data = mat_data["properties"]["diffuse_color"]
                            if len(color_data) >= 3:
                                mat.diffuse_color = color_data
                        except:
                            pass
                    
                    if mat.use_nodes and mat.node_tree:
                        mat.node_tree.nodes.clear()
                        
                        bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
                        bsdf.location = (0, 0)
                        
                        if "node_tree" in mat_data and mat_data["node_tree"]:
                            nodes_data = mat_data["node_tree"].get("nodes", [])
                            for node_data in nodes_data:
                                if node_data.get("type") == 'BSDF_PRINCIPLED':
                                    inputs_data = node_data.get("inputs", {})
                                    
                                    for input_name, input_value in inputs_data.items():
                                        if input_name in bsdf.inputs:
                                            try:
                                                if isinstance(input_value, list):
                                                    if len(input_value) >= 4:
                                                        bsdf.inputs[input_name].default_value = input_value
                                                    elif len(input_value) >= 3:
                                                        bsdf.inputs[input_name].default_value = input_value + [1.0]
                                                else:
                                                    bsdf.inputs[input_name].default_value = input_value
                                            except:
                                                pass
                        
                        output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                        output.location = (300, 0)
                        mat.node_tree.links.new(bsdf.outputs[0], output.inputs[0])
                    
                    restored_count += 1
                    print(f"✅ Restored material: {mat_name}")
                    
                except Exception as e:
                    print(f"❌ Error creating material {mat_name}: {e}")
            
            return restored_count
            
        except Exception as e:
            print(f"❌ Error restoring materials from backup: {e}")
            return 0
    
    @staticmethod
    def restore_geometry_from_backup_simple(backup_json, context):
        """Restoration from backup. If the object still exists (trash or only unlinked), it is reused and simply placed back in the source (modifiers intact)"""
        try:
            if not backup_json or not backup_json.strip():
                print("❌ Backup vacío")
                return False
                
            backup_data = json.loads(backup_json)
            
            print(f"🔄 Restoring from a simple backupRestoring from a simple backup...")
            
            restored_count = 0
            target_coll = context.collection
            
            for obj_data in backup_data.get("objects", []):
                name = obj_data.get("name", "")
                obj_type = obj_data.get("type", "MESH")
                
                if not name:
                    continue
                
                if name in bpy.data.objects:
                    obj = bpy.data.objects[name]
                    for coll in list(obj.users_collection):
                        coll.objects.unlink(obj)
                    target_coll.objects.link(obj)
                    obj.location = (0.0, 0.0, 0.0)
                    obj.rotation_euler = (0.0, 0.0, 0.0)
                    obj.scale = (1.0, 1.0, 1.0)
                    obj.hide_viewport = False
                    obj.hide_render = False
                    restored_count += 1
                    print(f"  ✅ {name} restored in source (existing object, modifiers preserved)")
                    continue
                
                print(f"  Creating: {name} ({obj_type})")
                
                obj = None
                
                try:
                    if obj_type == 'MESH':
                        mesh = bpy.data.meshes.new(name=f"{name}_Mesh")
                        
                        if "vertices" in obj_data and obj_data["vertices"]:
                            vertices = obj_data["vertices"]
                            
                            mesh.vertices.add(len(vertices))
                            for i, co in enumerate(vertices):
                                if len(co) >= 3:
                                    mesh.vertices[i].co = (co[0], co[1], co[2])
                            
                            if "polygons" in obj_data and obj_data["polygons"]:
                                polygons = obj_data["polygons"]
                                for face_verts in polygons:
                                    if len(face_verts) >= 3:
                                        try:
                                            mesh.polygons.add(1)
                                            mesh.polygons[-1].vertices = face_verts
                                        except:
                                            pass
                            
                            mesh.update()
                            mesh.calc_normals()
                        else:
                            bm = bmesh.new()
                            bmesh.ops.create_cube(bm, size=1.0)
                            bm.to_mesh(mesh)
                            bm.free()
                        
                        mesh.update()
                        obj = bpy.data.objects.new(name, mesh)
                        
                    elif obj_type == 'EMPTY':
                        obj = bpy.data.objects.new(name, None)
                    elif obj_type == 'CAMERA':
                        camera = bpy.data.cameras.new(name=f"{name}_Camera")
                        obj = bpy.data.objects.new(name, camera)
                    elif obj_type == 'LIGHT':
                        light = bpy.data.lights.new(name=f"{name}_Light", type='POINT')
                        obj = bpy.data.objects.new(name, light)
                    else:
                        obj = bpy.data.objects.new(name, None)
                    
                    if obj:
                        if "location" in obj_data and len(obj_data["location"]) == 3:
                            try:
                                obj.location = obj_data["location"]
                            except:
                                pass
                        
                        bpy.context.collection.objects.link(obj)
                        restored_count += 1
                        print(f"    ✅ {name} creado")
                        
                except Exception as e:
                    print(f"    ❌ Error creating {name}: {e}")
            
            print(f"✅ Restored: {restored_count} objects from backup")
            
            context.view_layer.update()
            for area in context.screen.areas:
                area.tag_redraw()
            
            return restored_count > 0
            
        except Exception as e:
            print(f"❌ Error in restoration from backup: {e}")
            import traceback
            traceback.print_exc()
            return False

class MATERIAL_OT_clean_material_duplicates(bpy.types.Operator):
    """Delete duplicate materials that were created for backups"""
    bl_idname = "material.clean_material_duplicates"
    bl_label = "Clean Material Duplicates"
    bl_description = "Remove duplicate materials created for backup restoration"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        materials_to_check = list(bpy.data.materials)
        removed_count = 0
        
        for material in materials_to_check:
            if material.users == 0:
                similar_exists = False
                base_name = material.name
                
                if base_name.endswith(".001") or base_name.endswith(".002"):
                    base_name = base_name.rsplit(".", 1)[0]
                
                for other_mat in bpy.data.materials:
                    if other_mat == material:
                        continue
                    
                    other_base = other_mat.name
                    if other_base.endswith(".001") or other_base.endswith(".002"):
                        other_base = other_base.rsplit(".", 1)[0]
                    
                    if other_base == base_name:
                        similar_exists = True
                        break
                
                if similar_exists:
                    try:
                        bpy.data.materials.remove(material)
                        removed_count += 1
                        print(f"✓ Removed duplicate material: {material.name}")
                    except Exception as e:
                        print(f"⚠️ Error removing material {material.name}: {e}")
        
        if removed_count > 0:
            self.report({'INFO'}, f"✓ Removed {removed_count} duplicate material(s)")
        else:
            self.report({'INFO'}, "✓ No duplicate materials found")
        
        return {'FINISHED'}
    
class MATERIAL_OT_view_deletion_history(bpy.types.Operator):
    """View and manage deletion history"""
    bl_idname = "material.view_deletion_history"
    bl_label = "Deletion History"
    bl_description = "View and restore deleted items"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    filter_type: bpy.props.EnumProperty(
        name="Filter Type",
        description="Filter history by deletion type",
        items=[
            ('ALL', "All Types", "Show all deletion types"),
            ('MATERIAL', "Materials", "Show only material deletions"),
            ('GEOMETRY', "Geometry", "Show only geometry deletions"),
            ('NODE_GROUP', "Node Groups", "Show only node group deletions"),
            ('COLLECTION', "Collections", "Show only collection deletions"),
        ],
        default='ALL',
        update=lambda self, context: self._update_dialog(context)
    )
    
    search_filter: bpy.props.StringProperty(
        name="Search",
        description="Search in item names",
        default="",
        update=lambda self, context: self._update_dialog(context)
    )
    
    def _update_dialog(self, context):
        """Force dialog redraw when filters change"""
        for area in context.screen.areas:
            if area.type == 'WINDOW':
                area.tag_redraw()

    def invoke(self, context, event):
        DeletionHistoryManager.auto_clean_history(context.scene)
        return context.window_manager.invoke_props_dialog(self, width=800)

    def execute(self, context):
        return {'FINISHED'}
    
    def is_selected(self, context, entry_id):
        """Check if an entry is selected"""
        sel = getattr(context.scene, "deletion_history_selection", "") or ""
        return str(entry_id) in (sel.split(",") if sel else [])
    
    def get_selected_ids(self):
        """Get list of selected IDs (use scene from bpy.context)"""
        ctx = bpy.context
        if not ctx.scene:
            return []
        sel = getattr(ctx.scene, "deletion_history_selection", "") or ""
        out = []
        for id_str in (sel.split(",") if sel else []):
            id_str = id_str.strip()
            if id_str and id_str.isdigit():
                out.append(int(id_str))
        return out

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        if icons.botton_history_icon_id:
            box.label(text="Deletion History", icon_value=icons.botton_history_icon_id)
        else:
            box.label(text="Deletion History", icon='TIME') 
        
        if not hasattr(context.scene, 'deletion_history') or len(context.scene.deletion_history) == 0:
            box.label(text="No deletion history yet", icon='INFO')
            return
        
        box = layout.box()
        box.label(text="Filters", icon='FILTER')
        
        row = box.row()
        row.prop(self, "search_filter", text="", icon='VIEWZOOM')
        row.prop(self, "filter_type", text="")
        
        row = box.row(align=True)

        all_selected = True
        if hasattr(context.scene, 'deletion_history') and len(context.scene.deletion_history) > 0:
            sel = getattr(context.scene, "deletion_history_selection", "") or ""
            selected_ids = [x.strip() for x in sel.split(",") if x.strip()]
            total_count = len(context.scene.deletion_history)
            
            if len(selected_ids) == total_count and total_count > 0:
                row.operator("material.select_all_history", 
                            text="Deselect All", 
                            icon='CHECKBOX_HLT')
            else:
                row.operator("material.select_all_history", 
                            text="Select All", 
                            icon='CHECKBOX_DEHLT')
        else:
            row.enabled = False
            row.operator("material.select_all_history", 
                        text="Select All", 
                        icon='CHECKBOX_DEHLT')
        
        selected_count = 0
        
        filtered_entries = []
        for entry in context.scene.deletion_history:
            if self.filter_type != 'ALL' and entry.deletion_type != self.filter_type:
                continue
            
            if self.search_filter and self.search_filter.lower() not in entry.item_names.lower():
                continue
            
            filtered_entries.append(entry)
        
        filtered_entries.sort(key=lambda e: e.timestamp, reverse=True)
        
        for entry in filtered_entries:
            is_selected = self.is_selected(context, entry.deletion_id)
            if is_selected:
                selected_count += 1

            row = box.row()
            icon = 'CHECKBOX_HLT' if is_selected else 'CHECKBOX_DEHLT'
            op = row.operator("material.simple_toggle", text="", icon=icon, emboss=False)
            op.entry_id = entry.deletion_id

            col = row.column()
            col.scale_y = 0.8
            type_icons = {
                'MATERIAL': 'MATERIAL',
                'GEOMETRY': 'MESH_CUBE',
                'NODE_GROUP': 'NODETREE',
                'COLLECTION': 'OUTLINER_COLLECTION',
                'EMPTY_SLOT': 'MATERIAL',
                'ORPHAN_DATA': 'BRUSH_DATA',
                'ALL_MATERIALS': 'MATERIAL',
                'UNUSED_MATERIALS': 'MATERIAL',
            }
            type_icon = type_icons.get(entry.deletion_type, 'QUESTION')
            item_display = entry.item_names
            if len(item_display) > 60:
                item_display = item_display[:57] + "..."

            info_row = col.row()
            info_row.label(text="", icon=type_icon)
            source_suffix = " [X]" if (hasattr(entry, 'source') and entry.source == 'HOTKEY') else ""
            info_row.label(text=f"{entry.deletion_type}{source_suffix}: {item_display}")

            time_row = col.row()
            time_row.scale_y = 0.7
            time_str = DeletionHistoryManager.format_timestamp(entry.timestamp)
            full_time = datetime.datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            time_row.label(text=f"Count: {entry.count} | Time: {time_str}")
            op = time_row.operator("wm.tooltip", text="", icon='QUESTION', emboss=False)
            op.tooltip = f"Exact time: {full_time}"

            if is_selected and entry.count > 1:
                sep_row = box.row()
                sep_row.scale_y = 0.9
                sep_op = sep_row.operator(
                    "material.restore_separation",
                    text="Separation - Choose what to restore",
                    icon='EXPORT'
                )
                sep_op.entry_id = entry.deletion_id

        if selected_count > 0:
            box = layout.box()
            box.label(text=f"🔄 {selected_count} item(s) selected", icon='INFO')
            
            row = box.row()
            selected_ids_str = ",".join([str(id) for id in self.get_selected_ids()])
            
            restore_op = row.operator("material.restore_selected_history", 
                                    text=f"Restore at Origin ({selected_count})", 
                                    icon='OBJECT_ORIGIN')
            restore_op.selected_ids_str = selected_ids_str
            restore_op.restore_in_place = False
            
            restore_place_op = row.operator("material.restore_selected_history", 
                                            text=f"Restore at Original Position", 
                                            icon='TRACKING_BACKWARDS_SINGLE')
            restore_place_op.selected_ids_str = selected_ids_str
            restore_place_op.restore_in_place = True
            
            clear_op = row.operator("material.clear_selected_history", 
                                text="Remove from History", 
                                icon='TRASH')
            clear_op.selected_ids_str = selected_ids_str

            has_collection = False
            selected_ids = self.get_selected_ids()
            for entry in context.scene.deletion_history:
                if entry.deletion_id in selected_ids and entry.deletion_type == 'COLLECTION':
                    has_collection = True
                    break

            if has_collection:
                row = box.row()
                row.operator("material.fix_collection_hierarchy", 
                            text="Collection Hierarchy (Only Collection)", 
                            icon='CON_CHILDOF')

        status_box = layout.box()
        status_box.label(text="Safety Settings Status", icon='PREFERENCES')
        
        prefs = DeletionHistoryManager.get_preferences()
        if prefs:
            status_grid = status_box.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
            status_grid.scale_y = 0.8
            
            if getattr(prefs, 'allow_unlimited_restore', True):
                status_grid.label(text="Unlimited Restore: ON", icon='FILE_REFRESH')
            else:
                status_grid.label(text="Unlimited Restore: OFF", icon='CANCEL')
            
            if getattr(prefs, 'remove_entry_after_restore', False):
                status_grid.label(text="Remove After Restore: ON", icon='TRASH')
            else:
                status_grid.label(text="Keep After Restore: ON", icon='PINNED')
            
            if getattr(prefs, 'delete_to_history', False):
                status_grid.label(text="Delete->History: ON [X/Del]", icon='IMPORT')
            else:
                status_grid.label(text="Delete->History: OFF", icon='BLANK1')
            
            if getattr(prefs, 'permanent_delete', False):
                row = status_box.row()
                row.alert = True
                row.label(text="PERMANENT DELETE: ACTIVE - No backups!", icon='ERROR')
        
        layout.separator()
        
        box = layout.box()
        row = box.row()
        row.operator("material.clear_all_history", text="Clear All History", icon='TRASH')


class MATERIAL_OT_simple_toggle(bpy.types.Operator):
    """Toggle selection of one history entry"""
    bl_idname = "material.simple_toggle"
    bl_label = "Toggle Selection"
    bl_options = {'INTERNAL', 'REGISTER'}
    
    entry_id: bpy.props.IntProperty()
    
    def execute(self, context):
        scene = context.scene
        sel = getattr(scene, "deletion_history_selection", "") or ""
        ids = [x.strip() for x in sel.split(",") if x.strip()]
        entry_str = str(self.entry_id)
        
        if entry_str in ids:
            ids.remove(entry_str)
        else:
            ids.append(entry_str)
        
        scene.deletion_history_selection = ",".join(ids)
        
        for area in context.screen.areas:
            area.tag_redraw()
        
        return {'FINISHED'}


class MATERIAL_OT_select_all_history(bpy.types.Operator):
    """Select or deselect all history entries"""
    bl_idname = "material.select_all_history"
    bl_label = "Select/Deselect All"
    bl_options = {'INTERNAL', 'REGISTER'}
    
    def execute(self, context):
        if not getattr(context.scene, "deletion_history", None):
            return {'CANCELLED'}
        
        all_selected = True
        for entry in context.scene.deletion_history:
            entry_id_str = str(entry.deletion_id)
            sel = getattr(context.scene, "deletion_history_selection", "") or ""
            if entry_id_str not in [x.strip() for x in sel.split(",") if x.strip()]:
                all_selected = False
                break
        
        if all_selected:
            context.scene.deletion_history_selection = ""
        else:
            ids = [str(entry.deletion_id) for entry in context.scene.deletion_history]
            context.scene.deletion_history_selection = ",".join(ids)
        
        for area in context.screen.areas:
            area.tag_redraw()
        
        return {'FINISHED'}


class WM_OT_tooltip(bpy.types.Operator):
    """Show a tooltip"""
    bl_idname = "wm.tooltip"
    bl_label = "Tooltip"
    bl_options = {'INTERNAL', 'REGISTER'}
    
    tooltip: bpy.props.StringProperty(
        name="Tooltip",
        description="Tooltip text to display"
    )
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.scale_y = 0.8
        box.label(text=self.tooltip, icon='INFO')


class MATERIAL_OT_restore_selected_history(bpy.types.Operator):
    """Restore selected items from deletion history - VERSIÓN MEJORADA"""
    bl_idname = "material.restore_selected_history"
    bl_label = "Restore Selected"
    bl_description = "Restore selected items from deletion history"
    bl_options = {'REGISTER', 'UNDO'}
    
    selected_ids_str: bpy.props.StringProperty(
        name="Selected IDs",
        description="Comma-separated list of selected history entry IDs",
        default=""
    )
    
    restore_in_place: bpy.props.BoolProperty(
        name="Restore where it was",
        description="Re-assign materials to original object slots and put objects back in their collections",
        default=False
    )
    
    def execute(self, context):
        if not hasattr(context.scene, 'deletion_history'):
            self.report({'ERROR'}, "No deletion history found")
            return {'CANCELLED'}
        
        if not self.selected_ids_str:
            self.selected_ids_str = getattr(context.scene, "deletion_history_selection", "") or ""
        
        if not self.selected_ids_str:
            self.report({'WARNING'}, "No items selected for restoration")
            return {'CANCELLED'}
        
        selected_ids = []
        for id_str in self.selected_ids_str.split(","):
            id_str = id_str.strip()
            if id_str and id_str.isdigit():
                selected_ids.append(int(id_str))
        
        context.scene.deletion_history_selection = ""
        restored_count = 0
        failed_count = 0
        
        print(f"DEBUG: Restoring entries with IDs: {selected_ids}")
        
        for entry in context.scene.deletion_history:
            if entry.deletion_id in selected_ids and entry.can_restore:
                print(f"🔄 Processing input {entry.deletion_id} - {entry.deletion_type}")
                try:
                    restored = _do_restore_entry(entry, restore_in_place=self.restore_in_place, context=context)
                    if restored:
                        restored_count += 1
                        print(f"✅ Entrance {entry.deletion_id} restored successfully")
                    else:
                        failed_count += 1
                        print(f"❌ Entrance {entry.deletion_id} failed to restore")
                        
                        if entry.deletion_type in ['MATERIAL', 'ALL_MATERIALS', 'UNUSED_MATERIALS']:
                            print(f"🔄 Trying an alternative method for materials...")
                            alt_result = _do_restore_materials_simple(entry, self.restore_in_place)
                            if alt_result:
                                restored_count += 1
                                failed_count -= 1
                                print(f"✅ Materials restored with alternative method")
                except Exception as e:
                    print(f"❌ Error restoring entrance {entry.deletion_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    failed_count += 1
        
        prefs = DeletionHistoryManager.get_preferences()
        allow_unlimited = prefs.allow_unlimited_restore if prefs else True
        remove_after = prefs.remove_entry_after_restore if prefs else False
        
        if restored_count > 0:
            restore_msg = f"Restored {restored_count} item(s)"
            if allow_unlimited and not remove_after:
                restore_msg += " [Reusable - restore again anytime]"
            self.report({'INFO'}, f"OK {restore_msg}")
        if failed_count > 0:
            self.report({'WARNING'}, f"Could not restore {failed_count} item(s). Check console for details.")
        
        if remove_after and restored_count > 0:
            entries_to_remove = []
            for i, entry in enumerate(context.scene.deletion_history):
                if entry.deletion_id in selected_ids:
                    entries_to_remove.append(i)
            
            for idx in reversed(entries_to_remove):
                context.scene.deletion_history.remove(idx)
            
            print(f"Removed {len(entries_to_remove)} entries from history after restore")
        
        try:
            DeletionHistoryManager.force_view_layer_update(context)
        except Exception:
            pass
        
        return {'FINISHED'}

def _do_restore_hidden_geometry(entry, context, restore_in_place=True):
    print("\n🔄 Restoring objects from hidden collection")

    backup_json = getattr(entry, 'data_backup', None)
    if not backup_json:
        return False

    try:
        backup_data = json.loads(backup_json)
        original_map = backup_data.get("original_collections", {})
        if not original_map:
            return False

        trash_coll = None
        for coll in bpy.data.collections:
            if coll.name == "Trash Collection":
                trash_coll = coll
                break
        if not trash_coll:
            print("❌ The Trash Collection was not found.")
            return False

        restored_count = 0
        for obj_name, orig_coll_names in original_map.items():
            if obj_name not in bpy.data.objects:
                print(f"⚠️ Objet {obj_name} not found at the scene")
                continue

            obj = bpy.data.objects[obj_name]

            for coll in list(obj.users_collection):
                coll.objects.unlink(obj)

            linked = False
            for coll_name in orig_coll_names:
                if coll_name in bpy.data.collections:
                    target_coll = bpy.data.collections[coll_name]
                    target_coll.objects.link(obj)
                    linked = True
                    print(f"  ✅ {obj_name} linked to collection {coll_name}")

            if not linked:
                context.scene.collection.objects.link(obj)
                print(f"  ✅ {obj_name} linked to scene collection")

            obj.hide_viewport = False
            obj.hide_render = False

            if restore_in_place:
                pass
            else:
                obj.location = (0, 0, 0)
                obj.rotation_euler = (0, 0, 0)
                obj.scale = (1, 1, 1)
                if obj.parent:
                    obj.parent = None
                    print(f"  🧹 Father removed so that {obj_name} remain at the global origin")

            restored_count += 1

        print(f"✅ Restored {restored_count} object(s) from hidden collection")
        return restored_count > 0

    except Exception as e:
        print(f"❌ Error restoring hidden objects: {e}")
        import traceback
        traceback.print_exc()
        return False

def _do_restore_entry(entry, restore_in_place=False, context=None):
    """Restore items from history"""
    
    if context is None:
        context = bpy.context
    
    print(f"\n{'='*50}")
    print(f"INITIATING RESTORATION")
    print(f"Type: {entry.deletion_type}")
    print(f"Mode: {'ORIGINAL POSITION' if restore_in_place else 'ORIGIN'}")
    print(f"{'='*50}")
    
    diagnose_restoration_problem(entry)
    
    if entry.deletion_type in ['MATERIAL', 'ALL_MATERIALS', 'UNUSED_MATERIALS']:
        print(f"🔄 RESTORING MATERIALS")
        if getattr(entry, 'data_backup', None):
            result = _do_restore_materials_with_assignments(entry, restore_in_place)
        else:
            result = _do_restore_materials_with_assignments(entry, False)

    elif entry.deletion_type == 'GEOMETRY':
        backup_json = getattr(entry, 'data_backup', None)
        if backup_json:
            try:
                backup_data = json.loads(backup_json)
                if backup_data.get("method") == "hide":
                    return _do_restore_hidden_geometry(entry, context, restore_in_place)
            except:
                pass
        if restore_in_place:
            result = _do_restore_geometry_with_position(entry, context)
        else:
            result = _do_restore_geometry_simple(entry, context)
        return result
    
    elif entry.deletion_type == 'NODE_GROUP':
        print(f"🔄 RESTORING NODE GROUPS")
        if getattr(entry, 'data_backup', None):
            result = _do_restore_node_groups_simple(entry)
        else:
            result = _do_restore_node_groups_basic(entry)
    
    elif entry.deletion_type == 'COLLECTION':
        print(f"🔄 RESTORING COLLECTIONS WITH FULL HIERARCHY")
        if getattr(entry, 'data_backup', None):
            diagnose_collections_problem(entry)
            
            result = DeletionHistoryManager.restore_collections_from_backup(entry.data_backup, context)
        else:
            result = _do_restore_collections_simple(entry)
    
    else:
        print(f"⚠️ Unsupported restoration type: {entry.deletion_type}")
        result = False
    
    try:
        DeletionHistoryManager.force_view_layer_update(context)
    except:
        pass
    
    return result

def _do_restore_geometry_nodes_independent(entry, context, restore_in_place=True):
    """Restore objects that had independent Geometry Nodes modifiers"""
    print(f"\n🎯 RESTORING GEOMETRY NODES INDEPENDIENTES")
    
    if not getattr(entry, 'data_backup', None):
        print("❌ There is no backup available for Geometry Nodes")
        return False
    
    try:
        backup_data = json.loads(entry.data_backup)
        
        if "geometry" in backup_data and "materials" in backup_data:
            geometry_data = backup_data.get("geometry", {})
        else:
            geometry_data = backup_data
        
        restored_count = 0
        modifiers_restored = 0
        
        for obj_data in geometry_data.get("objects", []):
            obj_name = obj_data.get("name", "")
            if not obj_name:
                continue
            
            print(f"\n🔍 Processing object: {obj_name}")
            
            obj = None
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                print(f"  ✅ Object already exists: {obj_name}")

                if not restore_in_place:
                    obj.location = (0.0, 0.0, 0.0)
                    obj.rotation_euler = (0.0, 0.0, 0.0)
                    obj.scale = (1.0, 1.0, 1.0)
                
                obj.hide_viewport = False
                obj.hide_render = False
                
                if len(obj.users_collection) == 0:
                    try:
                        context.collection.objects.link(obj)
                        print(f"  📍 Object linked to current collection")
                    except:
                        pass
                
                obj.select_set(True)
            else:
                try:
                    if obj_data.get("type") == 'MESH':
                        mesh = bpy.data.meshes.new(name=f"{obj_name}_mesh")
                        bm = bmesh.new()
                        bmesh.ops.create_cube(bm, size=1.0)
                        bm.to_mesh(mesh)
                        bm.free()
                        mesh.update()
                        
                        obj = bpy.data.objects.new(obj_name, mesh)
                        obj.location = (0.0, 0.0, 0.0)
                        context.collection.objects.link(obj)
                        print(f"  ✅ Object created in origin: {obj_name}")
                    else:
                        print(f"  ⚠️ Unsupported object type: {obj_data.get('type')}")
                        continue
                except Exception as e:
                    print(f"  ❌ Error creating object: {e}")
                    continue
            
            if obj:
                modifiers_data = obj_data.get("modifiers", [])
                
                for mod_data in modifiers_data:
                    if mod_data.get("type") == 'NODES':
                        print(f"  🔧 Processing Geometry Nodes: {mod_data.get('name', 'Unnamed')}")
                        
                        existing_mod = None
                        if hasattr(obj, 'modifiers'):
                            existing_mod = obj.modifiers.get(mod_data.get("name", ""))
                        
                        if existing_mod and existing_mod.type == 'NODES':
                            print(f"    ✅ Modifier already exists, skipping")
                            continue
                        
                        try:
                            mod_name = mod_data.get("name", "GeometryNodes")
                            new_mod = obj.modifiers.new(name=mod_name, type='NODES')
                            
                            node_group_name = mod_data.get("node_group_name", "")
                            if node_group_name and node_group_name in bpy.data.node_groups:
                                new_mod.node_group = bpy.data.node_groups[node_group_name]
                                print(f"    ✅ Node group assigned: {node_group_name}")
                            else:
                                print(f"    ⚠️ Node group not found: {node_group_name}")
                            
                            new_mod.show_viewport = mod_data.get("show_viewport", True)
                            new_mod.show_render = mod_data.get("show_render", True)
                            
                            inputs_data = mod_data.get("inputs", {})
                            if inputs_data and hasattr(new_mod, 'settings'):
                                print(f"    🔧 Restoring {len(inputs_data)} input(s)")
                                
                                for input_name, input_value in inputs_data.items():
                                    try:
                                        if hasattr(new_mod.settings, input_name):
                                            try:
                                                if isinstance(input_value, (int, float)):
                                                    setattr(new_mod.settings, input_name, float(input_value))
                                                elif isinstance(input_value, list):
                                                    current_attr = getattr(new_mod.settings, input_name)
                                                    if hasattr(current_attr, '__len__'):
                                                        if len(current_attr) == len(input_value):
                                                            for i in range(len(input_value)):
                                                                current_attr[i] = float(input_value[i])
                                            except Exception as e:
                                                print(f"      ⚠️ Error en input {input_name}: {e}")
                                    except:
                                        pass
                            
                            modifiers_restored += 1
                            print(f"    ✅ Geometry Nodes restored: {mod_name}")
                            
                        except Exception as e:
                            print(f"    ❌ Error creating Geometry Nodes: {e}")
                            import traceback
                            traceback.print_exc()
                
                restored_count += 1
        
        print(f"\n📊 RESULTS:")
        print(f"  Processed objects: {restored_count}")
        print(f"  Geometry Nodes restored: {modifiers_restored}")
        
        context.view_layer.update()
        for area in context.screen.areas:
            area.tag_redraw()
        
        return restored_count > 0
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR restoring Geometry Nodes: {e}")
        import traceback
        traceback.print_exc()
        return False

def diagnose_geometry_nodes_problem(entry):
    """Specific diagnosis for problems with Geometry Nodes"""
    print(f"\n🔍 SPECIFIC DIAGNOSIS GEOMETRY NODES")
    print(f"{'='*60}")
    
    if not getattr(entry, 'data_backup', None):
        print("❌ No backup available")
        return
    
    try:
        backup_data = json.loads(entry.data_backup)
        
        print(f"📦 Type of backup: {backup_data.get('type')}")
        print(f"📦 Objects in backup: {len(backup_data.get('objects', []))}")
        
        for obj_data in backup_data.get("objects", []):
            obj_name = obj_data.get("name", "Unnamed")
            obj_type = obj_data.get("type", "Unknown")
            
            print(f"\n  📍 Objet: {obj_name} ({obj_type})")
            
            if obj_name in bpy.data.objects:
                print(f"    ✅ It exists in the current scene")
                obj = bpy.data.objects[obj_name]
                
                current_mods = []
                if hasattr(obj, 'modifiers'):
                    current_mods = [mod.name for mod in obj.modifiers if mod.type == 'NODES']
                
                if current_mods:
                    print(f"    🔧 Current Geometry Nodes: {', '.join(current_mods)}")
                else:
                    print(f"    ⚠️ It does not currently have Geometry Nodes.")
            else:
                print(f"    ❌ It does not exist in the current scene.")
            
            backup_mods = []
            for mod in obj_data.get("modifiers", []):
                if mod.get("type") == 'NODES':
                    node_group = mod.get("node_group_name", "Unnamed group")
                    backup_mods.append(f"{mod.get('name', 'Unnamed modifier')} ({node_group})")
            
            if backup_mods:
                print(f"    📋 Geometry Nodes in backup: {', '.join(backup_mods)}")
            else:
                print(f"    ℹ️ I didn't have Geometry Nodes in the backup")
    
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")
    
    print(f"{'='*60}\n")

def _do_restore_node_groups_basic(entry):
    """Restore basic node groups when there is no detailed backup"""
    restored = 0
    
    items = []
    for part in (entry.item_names or "").split(","):
        part = part.strip()
        if part.startswith("... (+") and part.endswith(" more)"):
            continue
        if not part:
            continue
        
        if "(" in part and ")" in part:
            try:
                ng_name = part.split("(")[0].strip()
                ng_type = part.split("(")[1].split(")")[0].strip()
            except:
                ng_name = part
                ng_type = "SHADER"
        else:
            ng_name = part
            ng_type = "SHADER"
        
        items.append((ng_name, ng_type))
    
    for ng_name, ng_type in items:
        if not ng_name or ng_name in bpy.data.node_groups:
            continue
        
        try:
            ng = DeletionHistoryManager.create_simple_node_group(ng_name, ng_type)
            if ng:
                restored += 1
        except Exception as e:
            print(f"Error creating node group {ng_name}: {e}")
    
    return restored > 0

def _do_restore_materials_simple(entry, restore_in_place=False):
    """Restore materials in a simple way"""
    restored = 0
    
    if getattr(entry, 'data_backup', None):
        try:
            backup_data = json.loads(entry.data_backup)
            if backup_data.get("type") == "MATERIALS":
                for mat_data in backup_data.get("materials", []):
                    name = mat_data.get("name", "")
                    if not name or name in bpy.data.materials:
                        continue
                    
                    mat = bpy.data.materials.new(name=name)
                    mat.use_nodes = True
                    
                    if "diffuse_color" in mat_data:
                        mat.diffuse_color = mat_data["diffuse_color"]
                    
                    restored += 1
                    print(f"✓ Material restored from backup: {name}")
        except Exception as e:
            print(f"Error restoring from backup: {e}")
    
    for part in (entry.item_names or "").split(","):
        part = part.strip()
        if part.startswith("... (+") and part.endswith(" more)"):
            continue
        if not part or part in bpy.data.materials:
            continue
        
        try:
            mat = bpy.data.materials.new(name=part)
            mat.use_nodes = True
            restored += 1
            print(f"✓ Material created: {part}")
        except Exception as e:
            print(f"Error creating material {part}: {e}")
    
    return restored > 0

def _do_restore_materials_with_assignments(entry, restore_in_place=True):
    """Restore materials with their original object assignments"""
    if not getattr(entry, 'data_backup', None):
        print("❌ There is no backup to restore materials")
        return False
    
    try:
        backup_data = json.loads(entry.data_backup)
        
        if backup_data.get("type") != "MATERIALS_DETAILED_WITH_ASSIGNMENTS":
            print("⚠️ Backup is not in the correct format for detailed materials")
            return _do_restore_materials_simple(entry, restore_in_place)
        
        restored_materials = 0
        assigned_slots = 0
        
        print(f"🔄 Restoring materials with assignments...")
        
        for mat_data in backup_data.get("materials", []):
            mat_name = mat_data.get("name", "")
            if not mat_name:
                continue
            
            if mat_name in bpy.data.materials:
                mat = bpy.data.materials[mat_name]
                print(f"  ✅ Material {mat_name} ya existe")
            else:
                try:
                    mat = bpy.data.materials.new(name=mat_name)
                    mat.use_nodes = True
                    
                    if mat_data.get("use_nodes", False) and mat.node_tree:
                        mat.node_tree.nodes.clear()
                        
                        bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
                        bsdf.location = (0, 0)
                        output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                        output.location = (300, 0)
                        mat.node_tree.links.new(bsdf.outputs[0], output.inputs[0])
                    
                    restored_materials += 1
                    print(f"  ✅ Material {mat_name} created")
                except Exception as e:
                    print(f"  ❌ Error creating material {mat_name}: {e}")
                    continue
            
            if restore_in_place:
                assignments = mat_data.get("assignments", [])
                for assignment in assignments:
                    obj_name = assignment.get("object_name", "")
                    slot_idx = assignment.get("slot_index", 0)
                    
                    if not obj_name or obj_name not in bpy.data.objects:
                        print(f"  ⚠️ Object {obj_name} not found to assign material")
                        continue
                    
                    obj = bpy.data.objects[obj_name]
                    
                    if hasattr(obj, 'material_slots'):
                        while len(obj.material_slots) <= slot_idx:
                            bpy.context.view_layer.objects.active = obj
                            obj.select_set(True)
                            bpy.ops.object.material_slot_add()
                        
                        try:
                            obj.material_slots[slot_idx].material = mat
                            assigned_slots += 1
                            print(f"    📍 {mat_name} assigned to {obj_name}[{slot_idx}]")
                        except Exception as e:
                            print(f"❌ Error assigning material to {obj_name}[{slot_idx}]: {e}")
        
        print(f"✅ Materials restored: {restored_materials}")
        print(f"✅ Slots assigned: {assigned_slots}")
        
        return restored_materials > 0 or assigned_slots > 0
        
    except Exception as e:
        print(f"❌ Critical error restoring materials: {e}")
        import traceback
        traceback.print_exc()
        return False


def restore_geometry_from_backup_simple(backup_json, context):
    """Restoration from backup. If the object still exists (trash or only unlinked)"""
    try:
        if not backup_json or not backup_json.strip():
            print("❌ Empty backup")
            return False
            
        backup_data = json.loads(backup_json)
        
        print(f"🔄 Restoring from simple backup...")
        
        restored_count = 0
        target_coll = context.collection
        
        for obj_data in backup_data.get("objects", []):
            name = obj_data.get("name", "")
            obj_type = obj_data.get("type", "MESH")
            
            if not name:
                continue
            
            if name in bpy.data.objects:
                obj = bpy.data.objects[name]
                for coll in list(obj.users_collection):
                    coll.objects.unlink(obj)
                target_coll.objects.link(obj)
                obj.location = (0.0, 0.0, 0.0)
                obj.rotation_euler = (0.0, 0.0, 0.0)
                obj.scale = (1.0, 1.0, 1.0)
                obj.hide_viewport = False
                obj.hide_render = False
                restored_count += 1
                print(f"  ✅ {name} restored in origin (existing object, modifiers preserved)")
                continue
            
            print(f"  Creating: {name} ({obj_type})")
            
            obj = None
            
            try:
                if obj_type == 'MESH':
                    mesh = bpy.data.meshes.new(name=f"{name}_Mesh")
                    
                    if "vertices" in obj_data and obj_data["vertices"]:
                        vertices = obj_data["vertices"]
                        
                        mesh.vertices.add(len(vertices))
                        for i, co in enumerate(vertices):
                            if len(co) >= 3:
                                mesh.vertices[i].co = (co[0], co[1], co[2])
                        
                        if "polygons" in obj_data and obj_data["polygons"]:
                            polygons = obj_data["polygons"]
                            for face_verts in polygons:
                                if len(face_verts) >= 3:
                                    try:
                                        mesh.polygons.add(1)
                                        mesh.polygons[-1].vertices = face_verts
                                    except:
                                        pass
                        
                        mesh.update()
                        mesh.calc_normals()
                    else:
                        bm = bmesh.new()
                        bmesh.ops.create_cube(bm, size=1.0)
                        bm.to_mesh(mesh)
                        bm.free()
                    
                    mesh.update()
                    obj = bpy.data.objects.new(name, mesh)
                    
                elif obj_type == 'EMPTY':
                    obj = bpy.data.objects.new(name, None)
                elif obj_type == 'CAMERA':
                    camera = bpy.data.cameras.new(name=f"{name}_Camera")
                    obj = bpy.data.objects.new(name, camera)
                elif obj_type == 'LIGHT':
                    light = bpy.data.lights.new(name=f"{name}_Light", type='POINT')
                    obj = bpy.data.objects.new(name, light)
                else:
                    obj = bpy.data.objects.new(name, None)
                
                if obj:
                    if "location" in obj_data and len(obj_data["location"]) == 3:
                        try:
                            obj.location = obj_data["location"]
                        except:
                            pass
                    
                    bpy.context.collection.objects.link(obj)
                    restored_count += 1
                    print(f"    ✅ {name} creado")
                    
            except Exception as e:
                print(f"    ❌ Error creating {name}: {e}")
        
        print(f"✅ Restored: {restored_count} objects from backup")
        
        context.view_layer.update()
        for area in context.screen.areas:
            area.tag_redraw()
        
        return restored_count > 0
        
    except Exception as e:
        print(f"❌ Error in restoration from backup: {e}")
        import traceback
        traceback.print_exc()
        return False
    
def _do_restore_geometry_simple(entry, context):
    """Restore geometry easily 
    Prioritizes reusing existing objects (that were unlinked, not deleted)
    to preserve modifiers, geometry nodes, and all settings"""
    
    print(f"\n{'='*60}")
    print("RESTORING GEOMETRY TO ORIGIN (0,0,0)")
    print(f"Entry ID: {getattr(entry, 'deletion_id', 'N/A')}")
    print(f"{'='*60}")
    
    if not getattr(entry, 'data_backup', None) or not entry.data_backup.strip():
        print("⚠️ No backup available, creating basic objects...")
        return _create_basic_objects_at_origin(entry, context)
    
    try:
        backup_data = json.loads(entry.data_backup)
        
        if "geometry" in backup_data and "materials" in backup_data:
            geometry_data = backup_data.get("geometry", {})
        else:
            geometry_data = backup_data
        
        objects_data = geometry_data.get("objects", [])
        
        if not objects_data:
            print("⚠️ There is no object data in the backup")
            return False
        
        restored_count = 0
        
        print(f"📦 Objects in backup: {len(objects_data)}")
        
        for obj_data in objects_data:
            name = obj_data.get("name", "")
            obj_type = obj_data.get("type", "MESH")
            
            if not name:
                continue
            
            print(f"  🔄 Processing: {name} ({obj_type})")

            if name in bpy.data.objects:
                obj = bpy.data.objects[name]
                
                for coll in list(obj.users_collection):
                    try:
                        coll.objects.unlink(obj)
                    except:
                        pass
                
                target_collection = context.collection if context.collection else context.scene.collection
                
                try:
                    target_collection.objects.link(obj)
                    print(f"    ✅ {name} re-linked to collection: {target_collection.name} (modifiers preserved)")
                except Exception as e:
                    print(f"    ⚠️ Linking error {name}: {e}")
                    try:
                        context.scene.collection.objects.link(obj)
                    except:
                        pass
                
                obj.location = (0.0, 0.0, 0.0)
                obj.rotation_euler = (0.0, 0.0, 0.0)
                obj.scale = (1.0, 1.0, 1.0)
                obj.hide_viewport = False
                obj.hide_render = False
                obj.select_set(True)
                
                restored_count += 1
                print(f"    ✅ {name} restored at origin (existing object, all preserved)")
                continue
            
            try:
                obj = None
                
                if obj_type == 'MESH':
                    mesh = bpy.data.meshes.new(name=f"{name}_Mesh")
                    
                    if "vertices" in obj_data and obj_data.get("has_mesh_data", False):
                        vertices = obj_data["vertices"]
                        
                        mesh.vertices.add(len(vertices))
                        for i, co in enumerate(vertices):
                            mesh.vertices[i].co = (co[0], co[1], co[2])
                        
                        if "polygons" in obj_data and obj_data["polygons"]:
                            for face_verts in obj_data["polygons"]:
                                if len(face_verts) >= 3:
                                    try:
                                        mesh.polygons.add(1)
                                        mesh.polygons[-1].vertices = face_verts
                                    except:
                                        pass
                        
                        mesh.update()
                        try:
                            mesh.calc_normals()
                        except:
                            pass
                    else:
                        bm = bmesh.new()
                        bmesh.ops.create_cube(bm, size=1.0)
                        bm.to_mesh(mesh)
                        bm.free()
                        mesh.update()
                    
                    obj = bpy.data.objects.new(name, mesh)
                    
                elif obj_type == 'EMPTY':
                    obj = bpy.data.objects.new(name, None)
                elif obj_type == 'CAMERA':
                    camera = bpy.data.cameras.new(name=f"{name}_Camera")
                    obj = bpy.data.objects.new(name, camera)
                elif obj_type == 'LIGHT':
                    light = bpy.data.lights.new(name=f"{name}_Light", type='POINT')
                    obj = bpy.data.objects.new(name, light)
                elif obj_type == 'CURVE':
                    curve = bpy.data.curves.new(name=f"{name}_Curve", type='CURVE')
                    obj = bpy.data.objects.new(name, curve)
                elif obj_type == 'ARMATURE':
                    armature = bpy.data.armatures.new(name=f"{name}_Armature")
                    obj = bpy.data.objects.new(name, armature)
                elif obj_type == 'LATTICE':
                    lattice = bpy.data.lattices.new(name=f"{name}_Lattice")
                    obj = bpy.data.objects.new(name, lattice)
                elif obj_type == 'META':
                    meta = bpy.data.metaballs.new(name=f"{name}_Meta")
                    obj = bpy.data.objects.new(name, meta)
                elif obj_type == 'FONT':
                    font = bpy.data.curves.new(name=f"{name}_Font", type='FONT')
                    obj = bpy.data.objects.new(name, font)
                elif obj_type == 'SURFACE':
                    surface = bpy.data.curves.new(name=f"{name}_Surface", type='SURFACE')
                    obj = bpy.data.objects.new(name, surface)
                else:
                    obj = bpy.data.objects.new(name, None)
                
                if obj:
                    obj.location = (0.0, 0.0, 0.0)
                    obj.rotation_euler = (0.0, 0.0, 0.0)
                    obj.scale = (1.0, 1.0, 1.0)
                    
                    target_collection = context.collection if context.collection else context.scene.collection
                    
                    try:
                        target_collection.objects.link(obj)
                        print(f"    ✅ {name} created at origin and linked to collection")
                    except Exception as e:
                        print(f"    ⚠️ Linking error {name}: {e}")
                        try:
                            context.scene.collection.objects.link(obj)
                        except:
                            pass

                    obj.select_set(True)
                    restored_count += 1
                    
                    if "material_slots" in obj_data:
                        for slot_info in obj_data["material_slots"]:
                            mat_name = slot_info.get("material_name", "")
                            slot_idx = slot_info.get("slot_index", 0)
                            
                            if mat_name and mat_name in bpy.data.materials:
                                material = bpy.data.materials[mat_name]
                                
                                if hasattr(obj, 'material_slots'):
                                    while len(obj.material_slots) <= slot_idx:
                                        bpy.context.view_layer.objects.active = obj
                                        obj.select_set(True)
                                        bpy.ops.object.material_slot_add()
                                    
                                    try:
                                        obj.material_slots[slot_idx].material = material
                                        print(f" 🎨 Material assigned: {mat_name} → slot {slot_idx}")
                                    except:
                                        pass
                    
                    if "modifiers" in obj_data:
                        for mod_data in obj_data["modifiers"]:
                            mod_name = mod_data.get("name", "")
                            mod_type = mod_data.get("type", "")
                            
                            if not mod_name or not mod_type:
                                continue
                            
                            existing_mod = obj.modifiers.get(mod_name) if hasattr(obj, 'modifiers') else None
                            if existing_mod:
                                continue
                            
                            try:
                                new_mod = obj.modifiers.new(name=mod_name, type=mod_type)
                                
                                new_mod.show_viewport = mod_data.get("show_viewport", True)
                                new_mod.show_render = mod_data.get("show_render", True)
                                
                                if mod_type == 'NODES':
                                    node_group_name = mod_data.get("node_group_name", "")
                                    if node_group_name and node_group_name in bpy.data.node_groups:
                                        new_mod.node_group = bpy.data.node_groups[node_group_name]
                                        print(f"      🔧 Geometry Nodes assigned: {node_group_name}")
                                
                                print(f"      🔧 Restored modifier: {mod_name} ({mod_type})")
                            except Exception as e:
                                print(f"      ⚠️ Error restoring modifier {mod_name}: {e}")
                
            except Exception as e:
                print(f"    ❌ Error creating {name}: {e}")
                import traceback
                traceback.print_exc()
        
        print("🔄 Checking if any objects remain unrestored")
        if restored_count == 0:
            result = _create_basic_objects_at_origin(entry, context)
        else:
            result = True
        
        DeletionHistoryManager.force_view_layer_update(context)
        
        return result
    
    except Exception as e:
        print(f"❌ Critical error in restoration at source: {e}")
        import traceback
        traceback.print_exc()
        return _create_basic_objects_at_origin(entry, context)
    
    finally:
        DeletionHistoryManager.force_view_layer_update(context)

def _create_basic_objects_at_origin(entry, context):
    """Create basic objects on the source when there is no backup"""
    
    print(f"\n🔨 CREATING BASIC OBJECTS IN SOURCE")
    
    item_names = getattr(entry, 'item_names', '') or ""
    restored_count = 0
    
    for part in item_names.split(","):
        part = part.strip()
        if not part or part.startswith("... (+") or "more)" in part:
            continue
        
        obj_name = part
        obj_type = "MESH"
        
        if "(" in part and ")" in part:
            try:
                obj_name = part.split("(")[0].strip()
                obj_type = part.split("(")[1].split(")")[0].strip().upper()
            except:
                pass
        
        if not obj_name or obj_name in bpy.data.objects:
            print(f"  ⚠️ {obj_name} already exists, skipping")
            continue
        
        print(f"  🔧 Creating: {obj_name} ({obj_type})")
        
        try:
            obj = None
            
            if obj_type == 'MESH':
                mesh = bpy.data.meshes.new(name=f"{obj_name}_mesh")
                bm = bmesh.new()
                bmesh.ops.create_cube(bm, size=2.0)
                bm.to_mesh(mesh)
                bm.free()
                mesh.update()
                obj = bpy.data.objects.new(obj_name, mesh)
                
            elif obj_type == 'EMPTY':
                obj = bpy.data.objects.new(obj_name, None)
                
            elif obj_type == 'CAMERA':
                camera = bpy.data.cameras.new(name=f"{obj_name}_camera")
                obj = bpy.data.objects.new(obj_name, camera)
                
            elif obj_type == 'LIGHT':
                light = bpy.data.lights.new(name=f"{obj_name}_light", type='POINT')
                obj = bpy.data.objects.new(obj_name, light)
                
            else:
                obj = bpy.data.objects.new(obj_name, None)
            
            if obj:
                obj.location = (0.0, 0.0, 0.0)
                obj.rotation_euler = (0.0, 0.0, 0.0)
                obj.scale = (1.0, 1.0, 1.0)
                
                context.collection.objects.link(obj)
                obj.select_set(True)
                restored_count += 1
                
                print(f"    ✅ {obj_name} created in source (0,0,0)")
                
        except Exception as e:
            print(f"    ❌ Error creating {obj_name}: {e}")
    
    print(f"📊 Total created: {restored_count}")
    
    context.view_layer.update()
    for area in context.screen.areas:
        area.tag_redraw()
    
    return restored_count > 0

def _do_restore_geometry_with_position(entry, context, restore_in_place=True):
    """
    Restore geometry objects to their original positions, with materials and modifiers.
    If restore_in_place is True, objects are placed at saved coordinates and materials
    are reassigned to the original slots. If False, objects are placed at origin (0,0,0)
    and no material assignments are restored.
    """
    print(f"\n{'='*60}")
    print("RESTORING GEOMETRY WITH POSITION AND MATERIALS")
    print(f"Entry ID: {getattr(entry, 'deletion_id', 'N/A')}")
    print(f"Entry Type: {getattr(entry, 'deletion_type', 'N/A')}")
    print(f"Mode: {'ORIGINAL POSITION' if restore_in_place else 'ORIGIN'}")
    print(f"{'='*60}")

    restored = 0
    total_objects = 0

    if not getattr(entry, 'data_backup', None) or not entry.data_backup.strip():
        print("✗ No backup available. Falling back to simple restoration.")
        return _do_restore_geometry_simple(entry, context)

    try:
        backup_data = json.loads(entry.data_backup)

        is_combined = "geometry" in backup_data and "materials" in backup_data
        if is_combined:
            geometry_data = backup_data.get("geometry", {})
            materials_data = backup_data.get("materials", {})
            print("📦 Combined backup detected (geometry + materials)")
        else:
            geometry_data = backup_data
            materials_data = {}
            print("📦 Simple geometry backup detected")

        objects_data = geometry_data.get("objects", [])
        total_objects = len(objects_data)
        print(f"📋 Objects to restore: {total_objects}")

        if is_combined and materials_data:
            print("\n🎨 PHASE 1: Restoring missing materials")
            materials_needed = {}

            for obj_data in objects_data:
                for slot in obj_data.get("material_slots", []):
                    mat_name = slot.get("material_name")
                    if mat_name and mat_name not in bpy.data.materials:
                        materials_needed[mat_name] = slot

            if materials_needed:
                print(f"   Missing materials found: {len(materials_needed)}")
                for mat_data in materials_data.get("materials", []):
                    mat_name = mat_data.get("name")
                    if mat_name in materials_needed and mat_name not in bpy.data.materials:
                        try:
                            mat = bpy.data.materials.new(name=mat_name)
                            mat.use_nodes = True

                            print(f"   ✅ Material created: {mat_name}")
                        except Exception as e:
                            print(f"   ❌ Error creating material {mat_name}: {e}")
            else:
                print("   ✅ All materials already exist")

        print("\n PHASE 2: Restoring objects")
        for obj_data in objects_data:
            obj_name = obj_data.get("name", "")
            if not obj_name:
                continue

            try:
                print(f"\n  Processing: {obj_name}")

                if obj_name in bpy.data.objects:
                    obj = bpy.data.objects[obj_name]
                    print(f"    ✅ Object already exists, reusing.")

                    for coll in list(obj.users_collection):
                        try:
                            coll.objects.unlink(obj)
                        except:
                            pass
                else:
                    obj_type = obj_data.get("type", "MESH")
                    print(f"    Creating new {obj_type} object...")

                    if obj_type == 'MESH':
                        mesh = bpy.data.meshes.new(name=f"{obj_name}_Mesh")
                        if "vertices" in obj_data and obj_data.get("has_mesh_data", False):
                            try:
                                vertices = obj_data["vertices"]
                                mesh.vertices.add(len(vertices))
                                for i, co in enumerate(vertices):
                                    mesh.vertices[i].co = (co[0], co[1], co[2])

                                if "polygons" in obj_data:
                                    for face_verts in obj_data["polygons"]:
                                        if len(face_verts) >= 3:
                                            mesh.polygons.add(1)
                                            mesh.polygons[-1].vertices = face_verts
                                mesh.update()
                                mesh.calc_normals()
                                print(f"      ✅ Mesh data restored")
                            except Exception as mesh_err:
                                print(f"      ⚠️ Error restoring mesh data: {mesh_err}")
                                bm = bmesh.new()
                                bmesh.ops.create_cube(bm, size=1.0)
                                bm.to_mesh(mesh)
                                bm.free()
                                mesh.update()
                        else:

                            bm = bmesh.new()
                            bmesh.ops.create_cube(bm, size=1.0)
                            bm.to_mesh(mesh)
                            bm.free()
                            mesh.update()
                        obj = bpy.data.objects.new(obj_name, mesh)

                    elif obj_type == 'EMPTY':
                        obj = bpy.data.objects.new(obj_name, None)

                    elif obj_type == 'CURVE':
                        data = bpy.data.curves.new(f"{obj_name}_Curve", type='CURVE')
                        obj = bpy.data.objects.new(obj_name, data)

                    elif obj_type == 'CAMERA':
                        cam = bpy.data.cameras.new(name=f"{obj_name}_Camera")
                        obj = bpy.data.objects.new(obj_name, cam)

                    elif obj_type == 'LATTICE':
                        data = bpy.data.lattices.new(f"{obj_name}_Lattice")
                        obj = bpy.data.objects.new(obj_name, data)
    
                    elif obj_type == 'SPEAKER':
                        data = bpy.data.speakers.new(f"{obj_name}_Speaker")
                        obj = bpy.data.objects.new(obj_name, data)

                    elif obj_type == 'LIGHT_PROBE':
                        data = bpy.data.lightprobes.new(f"{obj_name}_Probe")
                        obj = bpy.data.objects.new(obj_name, data)

                    elif obj_type == 'GPENCIL':
                        data = bpy.data.grease_pencils.new(f"{obj_name}_GPencil")
                        obj = bpy.data.objects.new(obj_name, data)

                    elif obj_type == 'VOLUME':
                        data = bpy.data.volumes.new(f"{obj_name}_Volume")
                        obj = bpy.data.objects.new(obj_name, data)

                    elif obj_type == 'POINTCLOUD' and hasattr(bpy.data, 'pointclouds'):
                        data = bpy.data.pointclouds.new(f"{obj_name}_PC")
                        obj = bpy.data.objects.new(obj_name, data)
    
                    elif obj_type == 'LIGHT':
                        light = bpy.data.lights.new(name=f"{obj_name}_Light", type='POINT')
                        obj = bpy.data.objects.new(obj_name, light)

                    elif obj_type == 'CURVE':
                        curve = bpy.data.curves.new(name=f"{obj_name}_Curve", type='CURVE')
                        obj = bpy.data.objects.new(obj_name, curve)

                    elif obj_type == 'ARMATURE':
                        arm = bpy.data.armatures.new(name=f"{obj_name}_Armature")
                        obj = bpy.data.objects.new(obj_name, arm)

                    elif obj_type == 'LATTICE':
                        lat = bpy.data.lattices.new(name=f"{obj_name}_Lattice")
                        obj = bpy.data.objects.new(obj_name, lat)

                    elif obj_type == 'META':
                        meta = bpy.data.metaballs.new(name=f"{obj_name}_Meta")
                        obj = bpy.data.objects.new(obj_name, meta)

                    elif obj_type == 'FONT':
                        font = bpy.data.curves.new(name=f"{obj_name}_Font", type='FONT')
                        obj = bpy.data.objects.new(obj_name, font)

                    elif obj_type == 'SURFACE':
                        surf = bpy.data.curves.new(name=f"{obj_name}_Surface", type='SURFACE')
                        obj = bpy.data.objects.new(obj_name, surf)

                    else:
                        obj = bpy.data.objects.new(obj_name, None)

                    if not obj:
                        raise Exception(f"Could not create object of type {obj_type}")

                    print(f"    ✅ Object created")

                target_coll = context.collection if context.collection else context.scene.collection
                try:
                    target_coll.objects.link(obj)
                except RuntimeError:
                    pass

                if restore_in_place:
                    if "location" in obj_data:
                        obj.location = obj_data["location"]
                    if "rotation_euler" in obj_data:
                        obj.rotation_euler = obj_data["rotation_euler"]
                    if "scale" in obj_data:
                        obj.scale = obj_data["scale"]
                else:
                    obj.location = (0.0, 0.0, 0.0)
                    obj.rotation_euler = (0.0, 0.0, 0.0)
                    obj.scale = (1.0, 1.0, 1.0)

                obj.hide_viewport = False
                obj.hide_render = False
                obj.select_set(True)

                if restore_in_place and "material_slots" in obj_data:
                    for slot_info in obj_data["material_slots"]:
                        mat_name = slot_info.get("material_name")
                        slot_idx = slot_info.get("slot_index", 0)
                        if mat_name and mat_name in bpy.data.materials:

                            while len(obj.material_slots) <= slot_idx:
                                obj.select_set(True)
                                bpy.ops.object.material_slot_add()
                            obj.material_slots[slot_idx].material = bpy.data.materials[mat_name]
                            print(f"      🎨 Material assigned: {mat_name} → slot {slot_idx}")

                if "modifiers" in obj_data:
                    for mod_data in obj_data["modifiers"]:
                        mod_name = mod_data.get("name")
                        mod_type = mod_data.get("type")
                        if not mod_name or not mod_type:
                            continue

                        if obj.modifiers.get(mod_name):
                            continue
                        try:
                            new_mod = obj.modifiers.new(name=mod_name, type=mod_type)
                            new_mod.show_viewport = mod_data.get("show_viewport", True)
                            new_mod.show_render = mod_data.get("show_render", True)

                            if mod_type == 'NODES':
                                ng_name = mod_data.get("node_group_name")
                                if ng_name and ng_name in bpy.data.node_groups:
                                    new_mod.node_group = bpy.data.node_groups[ng_name]
                                    print(f"      🔧 Node group assigned: {ng_name}")
                                else:
                                    print(f"      ⚠️ Node group '{ng_name}' not found. Modifier created without it.")

                        except Exception as mod_err:
                            print(f"      ❌ Error creating modifier {mod_name}: {mod_err}")

                restored += 1
                print(f"    ✅ {obj_name} restored successfully.")

            except Exception as obj_err:
                print(f"    ❌ Failed to restore {obj_name}: {obj_err}")
                import traceback
                traceback.print_exc()

        print(f"\n Restored {restored} out of {total_objects} objects.")
        context.view_layer.update()
        for area in context.screen.areas:
            area.tag_redraw()

        return restored > 0

    except Exception as e:
        print(f"❌ Critical error in _do_restore_geometry_with_position: {e}")
        import traceback
        traceback.print_exc()
        return False

def _do_restore_materials_with_assignments(entry, restore_in_place=True):
    """Restore materials with their original assignments"""
    if not getattr(entry, 'data_backup', None):
        print("❌ No hay backup para restaurar materiales")
        return _do_restore_materials_simple(entry, restore_in_place)
    
    try:
        backup_data = json.loads(entry.data_backup)
        
        if backup_data.get("type") not in ["MATERIALS_DETAILED_WITH_ASSIGNMENTS", "MATERIALS_DETAILED"]:
            print("⚠️ Backup is not in the correct format for detailed materials")
            return _do_restore_materials_simple(entry, restore_in_place)
        
        restored_materials = 0
        assigned_slots = 0
        
        materials_data = backup_data.get("materials", [])
        
        print(f"🔄 Restoring {len(materials_data)} materials)...")
        
        for mat_data in materials_data:
            mat_name = mat_data.get("name", "")
            if not mat_name:
                continue
            
            if mat_name in bpy.data.materials:
                mat = bpy.data.materials[mat_name]
                print(f"  ✅ Material {mat_name} already exists, using existing")
            else:
                try:
                    mat = bpy.data.materials.new(name=mat_name)
                    mat.use_nodes = True
                    
                    if "properties" in mat_data and "diffuse_color" in mat_data["properties"]:
                        try:
                            color_data = mat_data["properties"]["diffuse_color"]
                            if len(color_data) >= 3:
                                mat.diffuse_color = color_data
                                print(f"    🎨 Diffuse color restored: {color_data}")
                        except Exception as e:
                            print(f"    ⚠️ Error setting diffuse color: {e}")
                    
                    if mat.use_nodes and mat.node_tree:
                        mat.node_tree.nodes.clear()
                        
                        bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
                        bsdf.location = (0, 0)
                        
                        output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                        output.location = (300, 0)
                        
                        mat.node_tree.links.new(bsdf.outputs[0], output.inputs[0])
                        
                        try:
                            if "node_tree" in mat_data and mat_data["node_tree"]:
                                node_tree_data = mat_data["node_tree"]
                                nodes_data = node_tree_data.get("nodes", [])
                                
                                for node_data in nodes_data:
                                    if node_data.get("type") == 'BSDF_PRINCIPLED':
                                        inputs_data = node_data.get("inputs", {})
                                        
                                        for input_name, input_value in inputs_data.items():
                                            try:
                                                if input_name in bsdf.inputs:
                                                    input_socket = bsdf.inputs[input_name]
                                                    
                                                    if input_socket.type == 'RGBA' and isinstance(input_value, list) and len(input_value) >= 3:
                                                        color_len = len(input_value)
                                                        if color_len >= 4:
                                                            input_socket.default_value = (
                                                                float(input_value[0]),
                                                                float(input_value[1]),
                                                                float(input_value[2]),
                                                                float(input_value[3])
                                                            )
                                                        else:
                                                            input_socket.default_value = (
                                                                float(input_value[0]),
                                                                float(input_value[1]),
                                                                float(input_value[2]),
                                                                1.0
                                                            )
                                                        print(f"    🎨 Input {input_name}: {input_value}")
                                                    
                                                    elif input_socket.type == 'VALUE':
                                                        input_socket.default_value = float(input_value)
                                                        print(f"    🔢 Input {input_name}: {input_value}")
                                                    
                                                    elif input_socket.type == 'VECTOR' and isinstance(input_value, list) and len(input_value) >= 3:
                                                        input_socket.default_value = (
                                                            float(input_value[0]),
                                                            float(input_value[1]),
                                                            float(input_value[2])
                                                        )
                                                        print(f"    📐 Input {input_name}: {input_value}")
                                            except Exception as e:
                                                print(f"    ⚠️ Error configuring input {input_name}: {e}")
                        
                        except Exception as e:
                            print(f"    ⚠️ Error restoring node configuration: {e}")
                    
                    try:
                        if "properties" in mat_data:
                            props = mat_data["properties"]
                            
                            if "metallic" in props:
                                mat.metallic = float(props["metallic"])
                            
                            if "roughness" in props:
                                mat.roughness = float(props["roughness"])
                            
                            if "specular_intensity" in props:
                                mat.specular_intensity = float(props["specular_intensity"])
                    except Exception as e:
                        print(f"    ⚠️ Error restoring basic properties: {e}")
                    
                    restored_materials += 1
                    print(f"  ✅ Material {mat_name} created and configured")
                except Exception as e:
                    print(f"  ❌ Error creating material {mat_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if restore_in_place:
                assignments = mat_data.get("assignments", [])
                for assignment in assignments:
                    obj_name = assignment.get("object_name", "")
                    slot_idx = assignment.get("slot_index", 0)
                    
                    if not obj_name or obj_name not in bpy.data.objects:
                        print(f"  ⚠️ Object {obj_name} not found for assigning material")
                        continue
                    
                    obj = bpy.data.objects[obj_name]
                    
                    if hasattr(obj, 'material_slots'):
                        while len(obj.material_slots) <= slot_idx:
                            bpy.context.view_layer.objects.active = obj
                            obj.select_set(True)
                            bpy.ops.object.material_slot_add()
                        
                        try:
                            obj.material_slots[slot_idx].material = mat
                            assigned_slots += 1
                            print(f"    📍 {mat_name} assigned to {obj_name}[{slot_idx}]")
                        except Exception as e:
                            print(f"    ❌ Error assigning material to {obj_name}[{slot_idx}]: {e}")
        
        print(f"✅ Materials restored: {restored_materials}")
        print(f"✅ Slots assigned: {assigned_slots}")
        
        return restored_materials > 0 or assigned_slots > 0
        
    except Exception as e:
        print(f"❌ Critical error restoring materials: {e}")
        import traceback
        traceback.print_exc()
        return False
        
def diagnose_collections_problem(entry):
    """Specific diagnosis for problems with collections"""
    print(f"\n🔍 DIAGNOSIS OF COLLECTIONS")
    print(f"{'='*60}")
    
    if not getattr(entry, 'data_backup', None):
        print("❌ No backup available")
        return
    
    try:
        backup_data = json.loads(entry.data_backup)
        
        print(f"📦 Backup type: {backup_data.get('type')}")
        print(f"📦 Collections in backup: {len(backup_data.get('collections', []))}")
        
        for coll_data in backup_data.get("collections", []):
            coll_name = coll_data.get("name", "Unnamed")
            parent = coll_data.get("parent", "(root)")
            objects_count = len(coll_data.get("objects", []))
            
            print(f"\n  📁 Collection: {coll_name}")
            print(f"    Parent: {parent}")
            print(f"    Objects: {objects_count}")
            
            if coll_name in bpy.data.collections:
                coll = bpy.data.collections[coll_name]
                current_parents = [p.name for p in coll.users_collection]
                print(f"    ✅ Exists in current scene")
                print(f"    Current parents: {current_parents}")
                print(f"    Current objects: {len(coll.objects)}")
            else:
                print(f"    ❌ Does NOT exist in current scene")
    
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")
    
    print(f"{'='*60}\n")

def _do_restore_node_groups_simple(entry):
    """Restore node groups from detailed backup"""
    if not getattr(entry, 'data_backup', None):
        print("❌ There is no backup to restore node groups")
        return False
    
    try:
        backup_data = json.loads(entry.data_backup)
        
        if backup_data.get("type") != "NODE_GROUPS_DETAILED":
            print("⚠️ Backup is not in the correct format for detailed node groups")
            return False
        
        restored = DeletionHistoryManager.restore_node_groups_from_backup(entry.data_backup)
        
        if restored > 0:
            print(f"✅ Node groups restored: {restored}")
            return True
        else:
            print("⚠️ No node groups were restored")
            return False
            
    except Exception as e:
        print(f"❌ Critical error restoring node groups: {e}")
        import traceback
        traceback.print_exc()
        return False

def _do_restore_node_groups_basic(entry):
    """Restore basic node groups when there is no detailed backup"""
    restored = 0
    items = []
    for part in (entry.item_names or "").split(","):
        part = part.strip()
        if part.startswith("... (+") and part.endswith(" more)"):
            continue
        if not part:
            continue
        
        if "(" in part and ")" in part:
            try:
                ng_name = part.split("(")[0].strip()
                ng_type = part.split("(")[1].split(")")[0].strip()
            except:
                ng_name = part
                ng_type = "SHADER"
        else:
            ng_name = part
            ng_type = "SHADER"
        
        items.append((ng_name, ng_type))
    
    for ng_name, ng_type in items:
        if not ng_name or ng_name in bpy.data.node_groups:
            continue
        
        try:
            ng = DeletionHistoryManager.create_simple_node_group(ng_name, ng_type)
            if ng:
                restored += 1
        except Exception as e:
            print(f"Error creating node group {ng_name}: {e}")
    
    return restored > 0


def _do_restore_collections_simple(entry):
    """Restore collections in a simple way (without hierarchy)"""
    restored = 0
    
    for part in (entry.item_names or "").split(","):
        part = part.strip()
        if part.startswith("... (+") and part.endswith(" more)"):
            continue
        if not part:
            continue
        
        coll_name = part
        if "(" in part and ")" in part:
            try:
                coll_name = part.split("(")[0].strip()
            except:
                coll_name = part
        
        if not coll_name or coll_name in bpy.data.collections:
            continue
        
        try:
            coll = bpy.data.collections.new(coll_name)
            
            try:
                bpy.context.scene.collection.children.link(coll)
                restored += 1
                print(f"✓ Collection created: {coll_name}")
            except Exception as e:
                for parent_coll in bpy.data.collections:
                    if parent_coll.name != coll_name:
                        try:
                            parent_coll.children.link(coll)
                            restored += 1
                            print(f"✓ Collection created as child: {coll_name}")
                            break
                        except:
                            pass
        except Exception as e:
            print(f"Error creating collection {coll_name}: {e}")
    
    return restored > 0


def restore_geometry_from_backup(backup_json, context):
    """Aliases for compatibility"""
    try:
        if not backup_json:
            print("❌ Empty Backup")
            return False
            
        backup_data = json.loads(backup_json)
        
        print(f"🔄 Restoring from backup...")
        
        restored_count = 0
        
        for obj_data in backup_data.get("objects", []):
            name = obj_data.get("name", "")
            obj_type = obj_data.get("type", "MESH")
            
            if not name:
                continue
                
            if name in bpy.data.objects:
                print(f"⚠ {name} already exists")
                continue
            
            print(f"  Creating: {name} ({obj_type})")
            
            obj = None
            
            if obj_type == 'MESH':
                mesh = bpy.data.meshes.new(name=f"{name}_Mesh")
                
                if "vertices" in obj_data and obj_data["vertices"]:
                    vertices = obj_data["vertices"]
                    polygons = obj_data.get("polygons", [])
                    
                    print(f"    📐 Vertices: {len(vertices)}, faces: {len(polygons)}")
                    
                    mesh.vertices.add(len(vertices))
                    for i, co in enumerate(vertices):
                        mesh.vertices[i].co = co
                    
                    if polygons:
                        for face_verts in polygons:
                            if len(face_verts) >= 3:
                                mesh.polygons.add(1)
                                mesh.polygons[-1].vertices = face_verts
                    
                    if "edges" in obj_data and obj_data["edges"]:
                        edges = obj_data["edges"]
                        mesh.edges.add(len(edges))
                        for i, edge_verts in enumerate(edges):
                            mesh.edges[i].vertices = edge_verts
                else:
                    bm = bmesh.new()
                    bmesh.ops.create_cube(bm, size=1.0)
                    bm.to_mesh(mesh)
                    bm.free()
                
                mesh.update()
                mesh.calc_normals()
                obj = bpy.data.objects.new(name, mesh)
                
            elif obj_type == 'EMPTY':
                obj = bpy.data.objects.new(name, None)
            elif obj_type == 'CAMERA':
                camera = bpy.data.cameras.new(name=f"{name}_Camera")
                obj = bpy.data.objects.new(name, camera)
            elif obj_type == 'LIGHT':
                light = bpy.data.lights.new(name=f"{name}_Light", type='POINT')
                obj = bpy.data.objects.new(name, light)
            else:
                obj = bpy.data.objects.new(name, None)
            
            if obj:
                if "location" in obj_data:
                    obj.location = obj_data["location"]
                if "scale" in obj_data:
                    obj.scale = obj_data["scale"]
                
                bpy.context.collection.objects.link(obj)
                restored_count += 1
                print(f"    ✅ {name} created")
        
        print(f"✅ Restored: {restored_count} objects")
        
        context.view_layer.update()
        for area in context.screen.areas:
            area.tag_redraw()
        
        return restored_count > 0
        
    except Exception as e:
        print(f"❌ Error in restoration: {e}")
        import traceback
        traceback.print_exc()
        return restore_geometry_from_backup_simple(backup_json, context)

class SeparationTempItem(bpy.types.PropertyGroup):
    """Temporary property for items in separation dialog"""
    name: bpy.props.StringProperty(name="Name")
    index: bpy.props.IntProperty(name="Index")

class SeparationItemList(bpy.types.UIList):
    """UI List to display items with scroll"""
    bl_idname = "UI_UL_separation_item_list"
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        entry_id = getattr(context.scene, "deletion_separation_entry_id", -1)
        
        sel = getattr(context.scene, "deletion_separation_selection", "") or ""
        selected_ids = [x.strip() for x in sel.split(",") if x.strip()]
        
        is_selected = str(item.index) in selected_ids
        
        row = layout.row(align=True)
        
        icon = 'CHECKBOX_HLT' if is_selected else 'CHECKBOX_DEHLT'
        toggle_op = row.operator("material.separation_toggle", text="", icon=icon, emboss=False)
        toggle_op.entry_id = entry_id
        toggle_op.index = item.index
        
        display_name = item.name if len(item.name) <= 45 else item.name[:42] + "..."
        row.label(text=display_name)
        
        row.label(text=f"[{item.index+1}]")

class MATERIAL_OT_fix_collection_hierarchy(bpy.types.Operator):
    """Fix collection hierarchy after restoration"""
    bl_idname = "material.fix_collection_hierarchy"
    bl_label = "Collection Hierarchy Only Collection"
    bl_description = "Repair collection hierarchy after restoration"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        collections_without_parent = []
        for coll in bpy.data.collections:
            if coll.users == 0 and coll.name != "Scene Collection":
                collections_without_parent.append(coll)
        
        if collections_without_parent:
            for coll in collections_without_parent:
                try:
                    context.scene.collection.children.link(coll)
                    print(f"✅ Collection {coll.name} linked to scene")
                except:
                    pass
        
        objects_without_collection = []
        for obj in bpy.data.objects:
            if len(obj.users_collection) == 0:
                objects_without_collection.append(obj)
        
        if objects_without_collection:
            for obj in objects_without_collection:
                try:
                    context.collection.objects.link(obj)
                    print(f"✅ Object {obj.name} linked to current collection")
                except:
                    pass
        
        total_fixed = len(collections_without_parent) + len(objects_without_collection)
        
        if total_fixed > 0:
            self.report({'INFO'}, f"✓ Repaired {total_fixed} items")
        else:
            self.report({'INFO'}, "✓ All collections and objects are correctly linked")
        
        return {'FINISHED'}

class MATERIAL_OT_restore_separation(bpy.types.Operator):
    """Open panel to choose which items from this history entry to restore"""
    bl_idname = "material.restore_separation"
    bl_label = "Separation - Choose what to restore"
    bl_description = "Choose which items from this deletion to restore"
    bl_options = {'REGISTER', 'UNDO'}
    
    entry_id: bpy.props.IntProperty()
    

    restore_in_place: bpy.props.BoolProperty(
        name="Restore in Place",
        description="Restore at original position (True) or at origin (False)",
        default=False
    )
    
    def invoke(self, context, event):
        context.scene.deletion_separation_entry_id = self.entry_id
        context.scene.deletion_separation_selection = ""
        self.restore_in_place = False
        
        return context.window_manager.invoke_props_dialog(self, width=600) 
    
    def execute(self, context):
        entry_id = getattr(context.scene, "deletion_separation_entry_id", -1)
        if entry_id < 0:
            self.report({'WARNING'}, "No entry selected")
            return {'CANCELLED'}
        
        entry = None
        for e in context.scene.deletion_history:
            if e.deletion_id == entry_id:
                entry = e
                break
        if not entry:
            self.report({'ERROR'}, "History entry not found")
            return {'CANCELLED'}
        
        items = DeletionHistoryManager.parse_entry_items(entry)
        if not items:
            self.report({'WARNING'}, "No items in this entry")
            return {'CANCELLED'}
        
        sel = getattr(context.scene, "deletion_separation_selection", "") or ""
        indices = []
        for x in sel.split(","):
            x = x.strip()
            if x.isdigit():
                indices.append(int(x))
        
        if not indices:
            self.report({'WARNING'}, "Select at least one item to restore")
            return {'CANCELLED'}
        
        selected_items = [items[i] for i in indices if 0 <= i < len(items)]
        if not selected_items:
            self.report({'WARNING'}, "No valid items selected")
            return {'CANCELLED'}
        
        clean_names = []
        for item in selected_items:

            name = item.strip()
            if "(" in name and ")" in name:
                name_part = name.split("(")[0].strip()
                if name_part:
                    name = name_part

            if (name.startswith("'") and name.endswith("'")) or \
               (name.startswith('"') and name.endswith('"')):
                name = name[1:-1]
            if name:
                clean_names.append(name)
        
        if not clean_names:
            self.report({'WARNING'}, "No valid items after cleaning names")
            return {'CANCELLED'}
        
        item_names_str = ",".join(clean_names)
        
        #show restore_selected_items
        ok = _do_restore_selected_items(entry.deletion_type, item_names_str, 
                                        getattr(entry, 'data_backup', None), 
                                        self.restore_in_place)
        
        if ok:
            position_text = "at original position" if self.restore_in_place else "at origin"
            self.report({'INFO'}, f"Restored {len(clean_names)} item(s) {position_text}")
        else:
            self.report({'WARNING'}, "Could not restore selected items (may already exist)")
        
        context.scene.deletion_separation_selection = ""
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        entry_id = getattr(context.scene, "deletion_separation_entry_id", -1)
        entry = None
        for e in context.scene.deletion_history:
            if e.deletion_id == entry_id:
                entry = e
                break

        if not entry:
            layout.label(text="Entry not found", icon='ERROR')
            return

        if entry.deletion_type == 'GEOMETRY' and getattr(entry, 'source', 'DIALOG') == 'HOTKEY':
            box = layout.box()
            box.alert = True
            box.label(text="It cannot be restored individually", icon='ERROR')
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="This geometry was removed using the X/Del key (hotkey)")
            col.label(text="Items deleted in this way are NOT stored with all their data")
            col.label(text="They cannot be restored one by one.")
            col.separator()
            col.label(text="Use the main restore option in the history")
            col.label(text="to restore all objects in this entry at once.")
            return  

        items = DeletionHistoryManager.parse_entry_items(entry)
        if not items:
            layout.label(text="No items in this entry", icon='INFO')
            return
        
        box = layout.box()
        box.label(text=f"Select items from: {entry.deletion_type}", icon='QUESTION')
        
        row = box.row()
        row.scale_y = 0.8
        
        sel = getattr(context.scene, "deletion_separation_selection", "") or ""
        selected_ids = [x.strip() for x in sel.split(",") if x.strip().isdigit()]
        selected_count = len(selected_ids)
        row.label(text=f"Total items: {len(items)} | Selected: {selected_count}")
        
        box = layout.box()
        box.label(text="Items to restore:", icon='CHECKMARK')
        
        scroll_region = box.column(align=True)
        
        for i, item in enumerate(items):
            row = scroll_region.row(align=True)
            
            is_selected = str(i) in selected_ids
            
            icon = 'CHECKBOX_HLT' if is_selected else 'CHECKBOX_DEHLT'
            toggle_op = row.operator("material.separation_toggle", text="", icon=icon, emboss=False)
            toggle_op.entry_id = entry_id
            toggle_op.index = i
            
            display_name = item
            if len(display_name) > 50:
                display_name = display_name[:47] + "..."
            row.label(text=display_name)
            
            row.label(text=f"[{i+1}]")
        
        if len(items) > 30:
            info_row = scroll_region.row()
            info_row.alignment = 'CENTER'
            info_row.scale_y = 0.8
            info_row.label(text=f"Showing all {len(items)} items. Use mouse wheel to scroll.", icon='INFO')
        
        selection_row = box.row()
        selection_row.scale_y = 0.9
        
        if selected_count == len(items):
            select_op = selection_row.operator("material.separation_select_all", 
                                text="Deselect All", 
                                icon='CHECKBOX_HLT')
        else:
            select_op = selection_row.operator("material.separation_select_all", 
                                text="Select All", 
                                icon='CHECKBOX_DEHLT')
        select_op.entry_id = entry_id
        
        layout.separator()
        
        if entry.deletion_type in ['MATERIAL', 'ALL_MATERIALS', 'UNUSED_MATERIALS']:
            position_box = layout.box()
            position_box.label(text="📌 Restoration Position:", icon='MATERIAL')
            
            col = position_box.column(align=True)
            col.scale_y = 0.9
            col.label(text="• Restore at Origin: Creates materials only")
            col.label(text="• Restore at Original Position: Re-assigns to object slots")
        
        elif entry.deletion_type == 'GEOMETRY':
            position_box = layout.box()
            position_box.label(text="📌 Restoration Position:", icon='MESH_CUBE')
            
            col = position_box.column(align=True)
            col.scale_y = 0.9
            col.label(text="• Restore at Origin: Places objects at world origin")
            col.label(text="• Restore at Original Position: Places objects in their original location")
        
        layout.separator()
        
        if selected_count > 0:
            action_box = layout.box()
            action_box.label(text=f"🔄 {selected_count} item(s) selected", icon='INFO')
            
            row = action_box.row()
            row.scale_y = 1.2
            
            restore_origin_op = row.operator("material.restore_separation_execute", 
                                            text=f"Restore at Origin", 
                                            icon='OBJECT_ORIGIN')
            restore_origin_op.entry_id = entry_id
            restore_origin_op.restore_in_place = False
            
            restore_position_op = row.operator("material.restore_separation_execute", 
                                            text=f"Restore at Original Position", 
                                            icon='TRACKING_BACKWARDS_SINGLE')
            restore_position_op.entry_id = entry_id
            restore_position_op.restore_in_place = True       

        else:
            warning_box = layout.box()
            warning_box.label(text="⚠️ No items selected", icon='INFO')
            warning_box.label(text="Select items by clicking the checkboxes")
            

class MATERIAL_OT_separation_select_all(bpy.types.Operator):
    """Select or deselect all items in separation dialog"""
    bl_idname = "material.separation_select_all"
    bl_label = "Select/Deselect All"
    bl_options = {'INTERNAL', 'REGISTER'}
    
    entry_id: bpy.props.IntProperty()
    
    def execute(self, context):
        entry = None
        for e in context.scene.deletion_history:
            if e.deletion_id == self.entry_id:
                entry = e
                break
        
        if not entry:
            return {'CANCELLED'}
        
        items = DeletionHistoryManager.parse_entry_items(entry)
        if not items:
            return {'CANCELLED'}
        
        sel = getattr(context.scene, "deletion_separation_selection", "") or ""
        current_selection = [x.strip() for x in sel.split(",") if x.strip().isdigit()]
        
        all_selected = len(current_selection) == len(items) and len(items) > 0
        
        if all_selected:
            context.scene.deletion_separation_selection = ""
        else:
            all_indices = [str(i) for i in range(len(items))]
            context.scene.deletion_separation_selection = ",".join(all_indices)
        
        for area in context.screen.areas:
            area.tag_redraw()
        
        return {'FINISHED'}

class MATERIAL_OT_separation_toggle(bpy.types.Operator):
    """Toggle one item in the separation dialog"""
    bl_idname = "material.separation_toggle"
    bl_label = "Toggle Item"
    bl_options = {'INTERNAL', 'REGISTER'}
    
    entry_id: bpy.props.IntProperty()
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        scene = context.scene
        sel = getattr(scene, "deletion_separation_selection", "") or ""
        ids = [x.strip() for x in sel.split(",") if x.strip()]
        idx_str = str(self.index)
        
        if idx_str in ids:
            ids.remove(idx_str)
        else:
            ids.append(idx_str)
        
        scene.deletion_separation_selection = ",".join(ids)
        
        for area in context.screen.areas:
            area.tag_redraw()
        
        return {'FINISHED'}
    
class MATERIAL_OT_scroll_separation(bpy.types.Operator):
    """Scroll through the separation list"""
    bl_idname = "material.scroll_separation"
    bl_label = "Scroll"
    bl_options = {'INTERNAL', 'REGISTER'}
    
    entry_id: bpy.props.IntProperty()
    direction: bpy.props.EnumProperty(
        items=[
            ('UP', "Up", "Scroll up"),
            ('DOWN', "Down", "Scroll down"),
        ]
    )
    scroll_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        entry = None
        for e in context.scene.deletion_history:
            if e.deletion_id == self.entry_id:
                entry = e
                break
        
        if not entry:
            return {'CANCELLED'}
        
        items = DeletionHistoryManager.parse_entry_items(entry)
        items_per_page = 50  
        
        if self.direction == 'UP':
            new_offset = max(0, self.scroll_offset - items_per_page)
        else:
            new_offset = min(len(items) - items_per_page, self.scroll_offset + items_per_page)
        
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'WINDOW':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            for handler in area.spaces.active.handlers:
                                if hasattr(handler, 'entry_id') and handler.entry_id == self.entry_id:
                                    handler.scroll_offset = new_offset
                                    break
        
        return {'FINISHED'}
    
class MATERIAL_OT_restore_separation_execute(bpy.types.Operator):
    """Restore only the selected items from the separation dialog"""
    bl_idname = "material.restore_separation_execute"
    bl_label = "Restore selected items"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}
    
    entry_id: bpy.props.IntProperty()
    restore_in_place: bpy.props.BoolProperty(
        name="Restore in Place",
        description="Restore at original position (True) or at origin (False)",
        default=False
    )

    def _do_restore_selected_items(self, deletion_type, item_names_str, data_backup, restore_in_place):
        """Dispatch restoration based on deletion type."""
        if deletion_type == 'GEOMETRY':
            return _do_restore_selected_geometry_items(item_names_str, data_backup, restore_in_place)
        else:
            return _do_restore_selected_other_items(deletion_type, item_names_str, data_backup, restore_in_place)

    def execute(self, context):
        entry_id = self.entry_id
        entry = None
        for e in context.scene.deletion_history:
            if e.deletion_id == entry_id:
                entry = e
                break
        if not entry:
            self.report({'WARNING'}, "Entry not found")
            return {'CANCELLED'}

        if entry.deletion_type == 'GEOMETRY' and getattr(entry, 'source', 'DIALOG') == 'HOTKEY':
            self.report({'ERROR'}, "No se pueden restaurar elementos de geometría individualmente (eliminados por hotkey). Usa la opción principal de restauración.")
            return {'CANCELLED'}

        items = DeletionHistoryManager.parse_entry_items(entry)
        if not items:
            return {'CANCELLED'}
        
        sel = getattr(context.scene, "deletion_separation_selection", "") or ""
        indices = [int(x.strip()) for x in sel.split(",") if x.strip().isdigit()]
        selected_items = [items[i] for i in indices if 0 <= i < len(items)]
        if not selected_items:
            self.report({'WARNING'}, "Select at least one item")
            return {'CANCELLED'}
        
        clean_names = []
        for item in selected_items:
            name = item.strip()
            if "(" in name and ")" in name:
                name_part = name.split("(")[0].strip()
                if name_part:
                    name = name_part
            if (name.startswith("'") and name.endswith("'")) or \
               (name.startswith('"') and name.endswith('"')):
                name = name[1:-1]
            if name:
                clean_names.append(name)
        
        if not clean_names:
            self.report({'WARNING'}, "No valid items after cleaning")
            return {'CANCELLED'}
        
        item_names_str = ",".join(clean_names)
        
        print(f"\n🔧 SEPARATION EXECUTE:")
        print(f"   Tipe: {entry.deletion_type}")
        print(f"   Items cleans: {clean_names}")
        print(f"   Mode: {'ORIGINAL POSITION' if self.restore_in_place else 'ORIGIN'}")
        
        ok = self._do_restore_selected_items(entry.deletion_type, item_names_str, 
                                            getattr(entry, 'data_backup', None), 
                                            self.restore_in_place)
        
        if ok:
            position_text = "at original position" if self.restore_in_place else "at origin"
            self.report({'INFO'}, f"Restored {len(clean_names)} item(s) {position_text}")
        else:
            self.report({'WARNING'}, "Could not restore selected items (may already exist)")
        
        try:
            DeletionHistoryManager.force_view_layer_update(context)
        except:
            pass
        
        context.scene.deletion_separation_selection = ""
        return {'FINISHED'}
    
    def _restore_entry_items(entry_type, item_names_str, data_backup=None, restore_in_place=False):
        ...  
        """Restore items with context"""
        class _FakeEntry:
            pass
        e = _FakeEntry()
        e.deletion_type = entry_type
        e.item_names = item_names_str or ""
        e.data_backup = (data_backup or "")
        e.can_restore = True
        
        return _do_restore_entry(e, restore_in_place=restore_in_place, context=bpy.context)

    def _filter_material_backup_for_selected_items(backup_json, selected_material_names):
        """Filter backup materials to include only the selected ones"""
        try:
            if not backup_json or not selected_material_names:
                return backup_json
            
            backup_data = json.loads(backup_json)
            
            if backup_data.get("type") in ["MATERIALS_DETAILED_WITH_ASSIGNMENTS", "MATERIALS_DETAILED"]:
                selected_set = set([name.strip() for name in selected_material_names if name.strip()])
                
                if "materials" in backup_data:
                    filtered_materials = []
                    for mat_data in backup_data["materials"]:
                        mat_name = mat_data.get("name", "")
                        if mat_name in selected_set:
                            filtered_materials.append(mat_data)
                    
                    backup_data["materials"] = filtered_materials
                
                return json.dumps(backup_data)
            else:
                return backup_json
                
        except Exception as e:
            print(f"Error filtering material backup: {e}")
            return backup_json

    def _do_restore_selected_items(self, entry_type, item_names_str, data_backup=None, restore_in_place=False):
        """Restore ONLY the selected specific items"""
        if not item_names_str:
            return False
        
        print(f"\n🔧 RESTORING SELECTED ITEMS:")
        print(f"   Tipe: {entry_type}")
        print(f"   Items: {item_names_str}")
        print(f"   Mode: {'ORIGINAL POSITION' if restore_in_place else 'ORIGIN'}")
        
        result = False
        
        try:
            if entry_type == 'GEOMETRY':
                result = _do_restore_selected_geometry_items(item_names_str, data_backup, restore_in_place)
            else:
                result = _do_restore_selected_other_items(entry_type, item_names_str, data_backup, restore_in_place)
        
        finally:
            DeletionHistoryManager.force_view_layer_update(bpy.context)
        
        return result


def _clean_item_names(item_names_str):
    """Clean up item names by removing corrupt serialization artifacts.
    Handles both the correct (comma-separated) format and the incorrect format
    which might have been saved as str(list) -> "['item1', 'item2']"
    """
    if not item_names_str:
        return []
    
    raw = item_names_str.strip()
    
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]  
        parts = []
        for part in raw.split(","):
            part = part.strip()
            if (part.startswith("'") and part.endswith("'")) or \
               (part.startswith('"') and part.endswith('"')):
                part = part[1:-1]
            part = part.strip()
            if part and not part.startswith("... (+"):
                parts.append(part)
        return parts
    
    parts = []
    for part in raw.split(","):
        part = part.strip()
        if (part.startswith("'") and part.endswith("'")) or \
           (part.startswith('"') and part.endswith('"')):
            part = part[1:-1]
        part = part.strip()
        if part and not part.startswith("... (+"):
            parts.append(part)
    return parts

def _do_restore_selected_geometry_items(item_names_str, data_backup, restore_in_place):
    """Restore ONLY selected specific geometry objects"""
    print(f"\n🎯 RESTORING SPECIFIC SELECTED GEOMETRY")
    
    selected_object_names = []
    for part in item_names_str.split(","):
        part = part.strip()
        if part and not part.startswith("... (+"):
            if "(" in part and ")" in part:
                obj_name = part.split("(")[0].strip()
            else:
                obj_name = part
            selected_object_names.append(obj_name)
    
    print(f"📋 Selected objects: {selected_object_names}")
    
    if not selected_object_names:
        print("❌ No selected objects")
        return False
    
    if not data_backup or not data_backup.strip():
        print("⚠️ No backup data, creating basic objects...")
        return _create_basic_objects_from_names(selected_object_names)
    
    try:
        backup_data = json.loads(data_backup)
        
        if "geometry" in backup_data and "materials" in backup_data:
            geometry_data = backup_data.get("geometry", {})
            materials_data = backup_data.get("materials", {})
        elif "objects" in backup_data:
            geometry_data = backup_data
            materials_data = {}
        else:
            print("⚠️ Unknown backup format")
            return _create_basic_objects_from_names(selected_object_names)
        
        all_objects = geometry_data.get("objects", [])
        filtered_objects = []
        
        selected_set = set(selected_object_names)
        for obj_data in all_objects:
            obj_name = obj_data.get("name", "")
            if obj_name in selected_set:
                filtered_objects.append(obj_data)
        
        print(f"📦 Backup filtered: {len(filtered_objects)} of {len(all_objects)} objects")
        
        if not filtered_objects:
            print("⚠️ No selected objects found in backup")
            return _create_basic_objects_from_names(selected_object_names)
        
        if "geometry" in backup_data and "materials" in backup_data:
            filtered_geometry = dict(geometry_data)
            filtered_geometry["objects"] = filtered_objects
            
            filtered_backup = {
                "geometry": filtered_geometry,
                "materials": materials_data,
                "timestamp": time.time()
            }
        else:
            filtered_backup = dict(geometry_data)
            filtered_backup["objects"] = filtered_objects
        
        filtered_json = json.dumps(filtered_backup)
        
        class _TempEntry:
            pass
        temp_entry = _TempEntry()
        temp_entry.deletion_type = 'GEOMETRY'
        temp_entry.item_names = item_names_str
        temp_entry.data_backup = filtered_json
        temp_entry.can_restore = True
        temp_entry.count = len(selected_object_names)
        
        if restore_in_place:
            print("📍 Restoring to original position...")
            result = _do_restore_geometry_with_position(temp_entry, bpy.context)
        else:
            print("🎯 Restoring to the source...")
            result = _do_restore_geometry_simple(temp_entry, bpy.context)
        
        return result
        
    except Exception as e:
        print(f"❌ Error restoring selected geometry: {e}")
        import traceback
        traceback.print_exc()
        
        print("🔄 Trying to create basic objects like fallback...")
        return _create_basic_objects_from_names(selected_object_names)

def _do_restore_selected_other_items(deletion_type, item_names_str, data_backup, restore_in_place):
    """RRestore ONLY the selected specific items"""
    if not item_names_str:
        return False
    
    print(f"\n🔧 RESTORING SELECTED ITEMS (INDIVIDUAL):")
    print(f"   Tipe: {deletion_type}")
    print(f"   Items: {item_names_str}")
    print(f"   Mode: {'ORIGINAL POSITION' if restore_in_place else 'ORIGIN'}")
    
    result = False
    
    try:
        if deletion_type in ['MATERIAL', 'ALL_MATERIALS', 'UNUSED_MATERIALS']:
            selected_names = _clean_item_names(item_names_str)
            selected_set = set(selected_names)
            
            print(f"  Selected materials to restore: {selected_names}")
            
            restored_count = 0
            assigned_count = 0
            
            if data_backup and data_backup.strip():
                try:
                    backup_data = json.loads(data_backup)
                    
                    materials_list = backup_data.get("materials", [])
                    
                    for mat_data in materials_list:
                        mat_name = mat_data.get("name", "")
                        if not mat_name or mat_name not in selected_set:
                            continue  
                        
                        if mat_name in bpy.data.materials:
                            mat = bpy.data.materials[mat_name]
                            print(f"  ✅ Material {mat_name} ya existe")
                        else:
                            try:
                                mat = bpy.data.materials.new(name=mat_name)
                                mat.use_nodes = True
                                
                                if "properties" in mat_data:
                                    props = mat_data["properties"]
                                    if "diffuse_color" in props:
                                        try:
                                            mat.diffuse_color = props["diffuse_color"]
                                        except:
                                            pass
                                    if "metallic" in props:
                                        mat.metallic = float(props["metallic"])
                                    if "roughness" in props:
                                        mat.roughness = float(props["roughness"])
                                    if "specular_intensity" in props:
                                        mat.specular_intensity = float(props["specular_intensity"])
                                
                                if mat.use_nodes and mat.node_tree:
                                    mat.node_tree.nodes.clear()
                                    bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
                                    bsdf.location = (0, 0)
                                    output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                                    output.location = (300, 0)
                                    mat.node_tree.links.new(bsdf.outputs[0], output.inputs[0])
                                    
                                    if "node_tree" in mat_data and mat_data["node_tree"]:
                                        for node_data in mat_data["node_tree"].get("nodes", []):
                                            if node_data.get("type") == 'BSDF_PRINCIPLED':
                                                for inp_name, inp_val in node_data.get("inputs", {}).items():
                                                    if inp_name in bsdf.inputs:
                                                        try:
                                                            inp_socket = bsdf.inputs[inp_name]
                                                            if isinstance(inp_val, list):
                                                                if inp_socket.type == 'RGBA':
                                                                    if len(inp_val) >= 4:
                                                                        inp_socket.default_value = tuple(float(v) for v in inp_val[:4])
                                                                    elif len(inp_val) >= 3:
                                                                        inp_socket.default_value = (float(inp_val[0]), float(inp_val[1]), float(inp_val[2]), 1.0)
                                                                elif inp_socket.type == 'VECTOR' and len(inp_val) >= 3:
                                                                    inp_socket.default_value = (float(inp_val[0]), float(inp_val[1]), float(inp_val[2]))
                                                            else:
                                                                inp_socket.default_value = float(inp_val)
                                                        except:
                                                            pass
                                
                                restored_count += 1
                                print(f"  ✅ Material {mat_name} creado")
                            except Exception as e:
                                print(f"  ❌ Error creating material {mat_name}: {e}")
                                continue
                        
                        if restore_in_place:
                            for assignment in mat_data.get("assignments", []):
                                obj_name = assignment.get("object_name", "")
                                slot_idx = assignment.get("slot_index", 0)
                                
                                if not obj_name or obj_name not in bpy.data.objects:
                                    continue
                                
                                obj = bpy.data.objects[obj_name]
                                if hasattr(obj, 'material_slots'):
                                    while len(obj.material_slots) <= slot_idx:
                                        bpy.context.view_layer.objects.active = obj
                                        obj.select_set(True)
                                        bpy.ops.object.material_slot_add()
                                    try:
                                        obj.material_slots[slot_idx].material = mat
                                        assigned_count += 1
                                        print(f"    📍 {mat_name} assigned to {obj_name}[{slot_idx}]")
                                    except Exception as e:
                                        print(f"    ❌ Error assigning: {e}")
                    
                except Exception as e:
                    print(f"   Error processing backup: {e}")
                    import traceback
                    traceback.print_exc()
            
            for mat_name in selected_names:
                if mat_name and mat_name not in bpy.data.materials:
                    try:
                        mat = bpy.data.materials.new(name=mat_name)
                        mat.use_nodes = True
                        restored_count += 1
                        print(f"  ✅ Material {mat_name} created (fallback)")
                    except Exception as e:
                        print(f"  ❌ Error creating fallback material {mat_name}: {e}")
            
            print(f"   ✅ Materials restored: {restored_count}, Assignments: {assigned_count}")
            result = restored_count > 0 or assigned_count > 0
        
        elif deletion_type == 'NODE_GROUP':
            selected_names = _clean_item_names(item_names_str)
            
            parsed_items = []
            for item in selected_names:
                if "(" in item and ")" in item:
                    try:
                        ng_name = item.split("(")[0].strip()
                        ng_type = item.split("(")[1].split(")")[0].strip()
                    except:
                        ng_name = item
                        ng_type = "SHADER"
                else:
                    ng_name = item
                    ng_type = "SHADER"
                parsed_items.append((ng_name, ng_type))
            
            selected_ng_names = set(name for name, _ in parsed_items)
            restored_count = 0
            
            if data_backup and data_backup.strip():
                try:
                    backup_data = json.loads(data_backup)
                    
                    if backup_data.get("type") == "NODE_GROUPS_DETAILED":
                        filtered_ngs = [ng for ng in backup_data.get("node_groups", []) 
                                       if ng.get("name", "") in selected_ng_names]
                        
                        if filtered_ngs:
                            filtered_backup = dict(backup_data)
                            filtered_backup["node_groups"] = filtered_ngs
                            filtered_json = json.dumps(filtered_backup)
                            
                            restored_count = DeletionHistoryManager.restore_node_groups_from_backup(filtered_json)
                except Exception as e:
                    print(f"   ❌ Error restoring node groups from backup: {e}")
            
            for ng_name, ng_type in parsed_items:
                if ng_name and ng_name not in bpy.data.node_groups:
                    try:
                        ng = DeletionHistoryManager.create_simple_node_group(ng_name, ng_type)
                        if ng:
                            restored_count += 1
                    except Exception as e:
                        print(f"   ❌ Error creating fallback node group {ng_name}: {e}")
            
            result = restored_count > 0
        
        elif deletion_type == 'COLLECTION':
            selected_names = [c.strip() for c in item_names_str.split(",") if c.strip()]
            
            parsed_coll_names = []
            for item in selected_names:
                if "(" in item and ")" in item:
                    coll_name = item.split("(")[0].strip()
                else:
                    coll_name = item
                parsed_coll_names.append(coll_name)
            
            selected_coll_set = set(parsed_coll_names)
            restored_count = 0
            
            if data_backup and data_backup.strip():
                try:
                    backup_data = json.loads(data_backup)
                    
                    if backup_data.get("type") == "COLLECTIONS_WITH_HIERARCHY":
                        filtered_collections = []
                        filtered_hierarchy = []
                        
                        for coll_data in backup_data.get("collections", []):
                            coll_name = coll_data.get("name", "")
                            if coll_name in selected_coll_set:
                                filtered_collections.append(coll_data)
                        
                        for hier_entry in backup_data.get("hierarchy", []):
                            if hier_entry.get("original_name", "") in selected_coll_set:
                                filtered_hierarchy.append(hier_entry)
                        
                        if filtered_collections:
                            filtered_backup = dict(backup_data)
                            filtered_backup["collections"] = filtered_collections
                            filtered_backup["hierarchy"] = filtered_hierarchy
                            filtered_json = json.dumps(filtered_backup)
                            
                            success = DeletionHistoryManager.restore_collections_from_backup(filtered_json, bpy.context)
                            if success:
                                restored_count = len(filtered_collections)
                except Exception as e:
                    print(f"   ❌ Error restoring collections from backup: {e}")
            
            for coll_name in parsed_coll_names:
                if coll_name and coll_name not in bpy.data.collections:
                    found = False
                    for c in bpy.data.collections:
                        if c.name == f"{coll_name}_restoun" or c.name.startswith(f"{coll_name}_restoun_"):
                            found = True
                            break
                    
                    if not found:
                        try:
                            coll = bpy.data.collections.new(coll_name)
                            bpy.context.scene.collection.children.link(coll)
                            restored_count += 1
                            print(f"  ✅ Collection {coll_name} created (fallback)")
                        except Exception as e:
                            print(f"  ❌ Error creating collection {coll_name}: {e}")
            
            result = restored_count > 0
        
        else:
            print(f"   ⚠️ restoration type not supported in separation: {deletion_type}")
            result = False
    
    except Exception as e:
        print(f"   ❌ Critical error in individual restoration: {e}")
        import traceback
        traceback.print_exc()
        result = False
    
    print(f"   Resultado: {'✅ SUCCESS' if result else '❌ FAILED'}")
    return result

def _create_basic_objects_from_names(object_names):
    """Create basic objects from names when there is no backup"""
    print(f"🔨 Creating {len(object_names)} basic object(s)...")
    
    created_count = 0
    for obj_name in object_names:
        if not obj_name or obj_name in bpy.data.objects:
            continue
        
        try:
            mesh = bpy.data.meshes.new(name=f"{obj_name}_mesh")
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=2.0)
            bm.to_mesh(mesh)
            bm.free()
            mesh.update()
            
            obj = bpy.data.objects.new(obj_name, mesh)
            bpy.context.collection.objects.link(obj)
            obj.select_set(True)
            created_count += 1
            
            print(f"    ✅ {obj_name} created")
        except Exception as e:
            print(f"    ❌ Error creating {obj_name}: {e}")
    
    print(f"📊 Total created: {created_count}")
    return created_count > 0

class MATERIAL_OT_restore_separation_confirm(bpy.types.Operator):
    """Restore only the selected items from the separation dialog"""
    bl_idname = "material.restore_separation_confirm"
    bl_label = "Restore selected"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}
    
    entry_id: bpy.props.IntProperty()
    restore_in_place: bpy.props.BoolProperty(
        name="Restore in Place",
        description="Restore at original position (True) or at origin (False)",
        default=False
    )
    
    def execute(self, context):
        entry_id = self.entry_id
        entry = None
        for e in context.scene.deletion_history:
            if e.deletion_id == entry_id:
                entry = e
                break
        if not entry:
            self.report({'WARNING'}, "Entry not found")
            return {'CANCELLED'}
        
        items = DeletionHistoryManager.parse_entry_items(entry)
        if not items:
            return {'CANCELLED'}
        
        sel = getattr(context.scene, "deletion_separation_selection", "") or ""
        indices = [int(x.strip()) for x in sel.split(",") if x.strip().isdigit()]
        selected_items = [items[i] for i in indices if 0 <= i < len(items)]
        if not selected_items:
            self.report({'WARNING'}, "Select at least one item")
            return {'CANCELLED'}
        
        clean_names = []
        for item in selected_items:
            name = item.strip()
            if "(" in name and ")" in name:
                name_part = name.split("(")[0].strip()
                if name_part:
                    name = name_part
            if (name.startswith("'") and name.endswith("'")) or \
               (name.startswith('"') and name.endswith('"')):
                name = name[1:-1]
            if name:
                clean_names.append(name)
        
        if not clean_names:
            self.report({'WARNING'}, "No valid items after cleaning")
            return {'CANCELLED'}
        
        item_names_str = ",".join(clean_names)
        ok = self._do_restore_selected_items(entry.deletion_type, item_names_str, 
                                            getattr(entry, 'data_backup', None), 
                                            self.restore_in_place)
        if ok:
            position_text = "at original position" if self.restore_in_place else "at origin"
            self.report({'INFO'}, f"Restored {len(clean_names)} item(s) {position_text}")
        else:
            self.report({'WARNING'}, "Could not restore")
        
        try:
            DeletionHistoryManager.force_view_layer_update(context)
        except:
            pass
        
        context.scene.deletion_separation_selection = ""
        return {'FINISHED'}


def _permanently_delete_entry_items(entry):
    """Permanently delete items from a history entry"""
    if not entry or not getattr(entry, "deletion_type", None):
        return
    deletion_type = entry.deletion_type
    names = []
    if deletion_type == "GEOMETRY" and getattr(entry, "data_backup", None) and entry.data_backup.strip():
        try:
            data = json.loads(entry.data_backup)
            if "geometry" in data and "materials" in data:
                geo_data = data.get("geometry", {})
            else:
                geo_data = data
            names = [o.get("name", "") for o in geo_data.get("objects", []) if o.get("name")]
        except Exception:
            pass
        if not names:
            names = _clean_item_names(getattr(entry, "item_names", "") or "")
    else:
        names = _clean_item_names(getattr(entry, "item_names", "") or "")
    for name in names:
        if not name:
            continue
        try:
            if deletion_type == "GEOMETRY" and name in bpy.data.objects:
                obj = bpy.data.objects[name]
                data_block_name = obj.data.name if obj.data else None
                data_type = None
                if obj.data:
                    if obj.type == "MESH":
                        data_type = "meshes"
                    elif obj.type == "CURVE":
                        data_type = "curves"
                    elif obj.type == "CAMERA":
                        data_type = "cameras"
                    elif obj.type == "LIGHT":
                        data_type = "lights"
                    elif obj.type == "ARMATURE":
                        data_type = "armatures"
                    elif obj.type == "LATTICE":
                        data_type = "lattices"
                    elif obj.type == "META":
                        data_type = "metaballs"
                    elif obj.type == "FONT":
                        data_type = "curves"
                    elif obj.type == "SURFACE":
                        data_type = "curves"
                    elif obj.type == "GPENCIL":
                        data_type = "grease_pencils"
                bpy.data.objects.remove(obj, do_unlink=True)
                if data_block_name and data_type:
                    col = getattr(bpy.data, data_type, None)
                    if col and data_block_name in col and col[data_block_name].users == 0:
                        col.remove(col[data_block_name])
            elif deletion_type == "MATERIAL" and name in bpy.data.materials:
                bpy.data.materials.remove(bpy.data.materials[name])
            elif deletion_type == "NODE_GROUP" and name in bpy.data.node_groups:
                bpy.data.node_groups.remove(bpy.data.node_groups[name])
            elif deletion_type == "COLLECTION" and name in bpy.data.collections:
                coll = bpy.data.collections[name]
                for child in list(coll.objects):
                    coll.objects.unlink(child)
                bpy.data.collections.remove(coll)
        except Exception as e:
            print(f"Permanent delete warning for {deletion_type} '{name}': {e}")


class MATERIAL_OT_clear_selected_history(bpy.types.Operator):
    """Remove selected entries from deletion history"""
    bl_idname = "material.clear_selected_history"
    bl_label = "Clear Selected"
    bl_description = "Remove selected entries from history"
    bl_options = {'REGISTER'}
    
    selected_ids_str: bpy.props.StringProperty(
        name="Selected IDs",
        description="Comma-separated list of selected history entry IDs",
        default=""
    )
    
    def execute(self, context):
        if not hasattr(context.scene, 'deletion_history'):
            self.report({'ERROR'}, "No deletion history found")
            return {'CANCELLED'}
        
        if not self.selected_ids_str:
            self.selected_ids_str = getattr(context.scene, "deletion_history_selection", "") or ""
        
        if not self.selected_ids_str:
            self.report({'WARNING'}, "No items selected for removal")
            return {'CANCELLED'}
        
        selected_ids = []
        for id_str in self.selected_ids_str.split(","):
            id_str = id_str.strip()
            if id_str and id_str.isdigit():
                selected_ids.append(int(id_str))
        
        removed_count = 0
        for i in range(len(context.scene.deletion_history) - 1, -1, -1):
            entry = context.scene.deletion_history[i]
            if entry.deletion_id in selected_ids:
                _permanently_delete_entry_items(entry)
                context.scene.deletion_history.remove(i)
                removed_count += 1
        
        for i, entry in enumerate(context.scene.deletion_history):
            entry.deletion_id = i
        
        context.scene.deletion_history_selection = ""
        
        if removed_count > 0:
            self.report({'INFO'}, f"✓ Removed {removed_count} history entry(s)")
        else:
            self.report({'INFO'}, "No entries removed")
        
        return {'FINISHED'}


class MATERIAL_OT_clear_all_history(bpy.types.Operator):
    """Clear all deletion history"""
    bl_idname = "material.clear_all_history"
    bl_label = "Clear All History"
    bl_description = "Remove all entries from deletion history"
    bl_options = {'REGISTER'}
    
    def invoke(self, context, event):
        if not hasattr(context.scene, 'deletion_history') or len(context.scene.deletion_history) == 0:
            self.report({'INFO'}, "History is already empty")
            return {'CANCELLED'}
        
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context):
        if getattr(context.scene, "deletion_history", None) is not None:
            for entry in list(context.scene.deletion_history):
                _permanently_delete_entry_items(entry)
            context.scene.deletion_history.clear()
            context.scene.deletion_history_selection = ""
            self.report({'INFO'}, "✓ Cleared all deletion history")
        return {'FINISHED'}


class MATERIAL_OT_remove_materials_dialog(bpy.types.Operator):
    """Dialog to select and remove materials"""
    bl_idname = "material.remove_materials_dialog"
    bl_label = "Tavo Material Eliminator"
    bl_options = {'REGISTER', 'INTERNAL'}

    selected_materials: bpy.props.CollectionProperty(
        type=MaterialSelectionItem
    )
    
    search_filter: bpy.props.StringProperty(
        name="Search",
        description="Filter materials by name",
        default=""
    )
    
    select_all_trigger: bpy.props.BoolProperty(
        name="Select All",
        description="Select all materials",
        default=False
    )
    
    select_all_processed: bpy.props.BoolProperty(
        default=False
    )

    def execute(self, context):
        removed_count = 0
        materials_to_remove = []
        
        for item in self.selected_materials:
            if item.selected and item.name in bpy.data.materials:
                materials_to_remove.append(item.name)
        
        backup_data = DeletionHistoryManager.create_material_backup(materials_to_remove)
        
        for mat_name in materials_to_remove:
            if mat_name in bpy.data.materials:
                try:
                    mat = bpy.data.materials[mat_name]
                    
                    bpy.data.materials.remove(mat)
                    removed_count += 1
                    
                except Exception as e:
                    print(f"Error deleting material {mat_name}: {e}")
        
        if removed_count > 0:
            DeletionHistoryManager.add_history_entry(
                context.scene,
                'MATERIAL',
                materials_to_remove,
                removed_count,
                backup_data
            )
            
            self.report({'INFO'}, f"✓ Eliminated {removed_count} material(s) permanently (saved in history for retrieval)")
        else:
            self.report({'INFO'}, "No materials were selected for deletion")
        
        return {'FINISHED'}

    def invoke(self, context, event):
        has_materials = len(bpy.data.materials) > 0
        empty_slots_count = self.count_empty_slots()
        
        if not has_materials and empty_slots_count == 0:
            return bpy.ops.material.remove_geometry_dialog('INVOKE_DEFAULT')
        
        return self.invoke_material_removal(context)

    def invoke_material_removal(self, context):
        """Invoke the material removal dialog"""
        self.selected_materials.clear()
        self.select_all_trigger = False
        self.select_all_processed = False
        
        for material in bpy.data.materials:
            item = self.selected_materials.add()
            item.name = material.name
            item.selected = False
            item.users = material.users
        
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def check_select_all(self):
        """Process select all trigger if needed"""
        if self.select_all_trigger and not self.select_all_processed:
            for item in self.selected_materials:
                if not self.search_filter or self.search_filter.lower() in item.name.lower():
                    item.selected = True
            self.select_all_processed = True
        elif not self.select_all_trigger and self.select_all_processed:
            for item in self.selected_materials:
                if not self.search_filter or self.search_filter.lower() in item.name.lower():
                    item.selected = False
            self.select_all_processed = False

    def draw(self, context):
        layout = self.layout
        
        self.check_select_all()
        
        box = layout.box()
        row = box.row()
        row.alert = True
        row.label(text="PERMANENT MATERIAL DELETION", icon='ERROR')
        row = box.row()
        row.scale_y = 0.8
        row.label(text="Materials will be permanently deleted from the file")
        row = box.row()
        row.scale_y = 0.8
        row.label(text="A backup will be saved in the history for possible recovery")
        
        if len(bpy.data.materials) > 0:
            box = layout.box()
            row = box.row()
            row.label(text="Materials Available:", icon_value=botton_materials_icon_id)

            row = box.row()
            row.prop(self, "search_filter", text="", icon='VIEWZOOM')
            row.prop(self, "select_all_trigger", text="Select All", toggle=True)
            
            box = layout.box() 
            col = box.column(align=True)
            
            search_lower = self.search_filter.lower()
            visible_count = 0
            selected_count = 0
            
            for item in self.selected_materials:
                if item.name in bpy.data.materials:
                    if search_lower and search_lower not in item.name.lower():
                        continue
                    
                    visible_count += 1
                    if item.selected:
                        selected_count += 1
                        
                    material = bpy.data.materials[item.name]
                    row = col.row(align=True)
                    row.prop(item, "selected", text="")
                    
                    row.label(text=item.name, icon='MATERIAL')
                    
                    users_text = f"{material.users}"
                    if material.users == 0:
                        row.label(text=users_text, icon='ORPHAN_DATA')
                    else:
                        row.label(text=users_text, icon='LINKED')
            
            if visible_count > 0:
                if selected_count == visible_count and not self.select_all_trigger:
                    self.select_all_trigger = True
                    self.select_all_processed = True
                elif selected_count == 0 and self.select_all_trigger:
                    self.select_all_trigger = False
                    self.select_all_processed = False
            
            if search_lower:
                row = box.row()
                row.scale_y = 0.8
                row.label(text=f"Showing {visible_count} of {len(self.selected_materials)} materials", icon='INFO')
            
            layout.separator()
        
        empty_slots_count = self.count_empty_slots()
        if empty_slots_count > 0:
            box = layout.box()
            row = box.row()
            row.label(text="Clean Empty Slots:", icon_value=botton_Clean_empty_slots_icon_id)
            
            info_box = box.box()
            col = info_box.column(align=True)
            col.scale_y = 0.8
            col.label(text=f"Found {empty_slots_count} empty material slot(s)", icon='INFO')
            
            objects_with_empty_slots = sum(
                1 for obj in bpy.data.objects 
                if hasattr(obj, 'material_slots') and obj.material_slots and 
                any(slot.material is None for slot in obj.material_slots)
            )
            col.label(text=f"Objects affected: {objects_with_empty_slots}")
            col.label(text="Empty slots will be removed from all objects")
            
            row = box.row()
            row.scale_y = 1.5
            row.operator("material.clean_empty_slots", text="Clean Empty Slots")
            
            layout.separator()
        
        box = layout.box()
        box.label(text="Other Tools", icon='TOOL_SETTINGS')
        
        grid = box.grid_flow(row_major=True, columns=2, align=True)
        grid.scale_y = 1.2
        
        grid.operator("material.remove_geometry_dialog", 
                     text="Tavo Geometry Eliminator", 
                     icon_value=botton_geometry_icon_id)
        
        grid.operator("material.remove_collections_dialog", 
                     text="Tavo Collections Eliminator", 
                     icon_value=botton_collections_icon_id)
        
        grid.operator("material.remove_node_groups_dialog", 
                     text="Tavo Node Groups Eliminator", 
                     icon_value=botton_node_groups_icon_id)
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Statistics:", icon='INFO')
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text=f"Total Materials: {len(bpy.data.materials)}")
        
        if len(bpy.data.materials) > 0:
            selected_count = sum(1 for item in self.selected_materials if item.selected)
            col.label(text=f"Selected for removal: {selected_count}")
            
            unused_count = sum(1 for item in self.selected_materials if item.users == 0)
            col.label(text=f"Unused Materials: {unused_count}")
        
        if empty_slots_count > 0:
            col.label(text=f"Empty Material Slots: {empty_slots_count}", icon='ERROR')
        
        if hasattr(context.scene, 'deletion_history') and len(context.scene.deletion_history) > 0:
            box = layout.box()
            row = box.row()
            row.scale_y = 1.2
            if icons.botton_history_icon_id:
                row.operator("material.view_deletion_history", 
                            text=f"View Deletion History ({len(context.scene.deletion_history)})", 
                            icon_value=icons.botton_history_icon_id)
            else:
                row.operator("material.view_deletion_history", 
                            text=f"View Deletion History ({len(context.scene.deletion_history)})", 
                            icon='HISTORY')
            
            row = box.row()
            row.scale_y = 1.0
            row.operator("material.clean_material_duplicates", 
                        text="Clean Material Duplicates", 
                        icon_value=botton_Clean_material_duplicates_icon_id)


            row = box.row()
            row.scale_y = 0.7
            row.label(text="Removes duplicate materials created during restoration", icon='INFO')
        
        if len(bpy.data.materials) > 0:
            selected_count = sum(1 for item in self.selected_materials if item.selected)
            if selected_count > 0:
                warning_box = layout.box()
                warning_box.alert = True
                warning_box.label(text="This action cannot be undone!", icon='CANCEL')

    def count_empty_slots(self):
        """Count empty material slots in all objects"""
        empty_count = 0
        for obj in bpy.data.objects:
            if hasattr(obj, 'material_slots') and obj.material_slots:
                empty_count += sum(1 for slot in obj.material_slots if slot.material is None)
        return empty_count

    @classmethod
    def poll(cls, context):
        """Always allow opening the dialog"""
        return True

class MATERIAL_OT_remove_all_materials(bpy.types.Operator):
    """Remove all materials with confirmation"""
    bl_idname = "material.remove_all_materials"
    bl_label = "Delete All Materials"
    bl_description = "Delete all materials from the file permanently"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        material_count = len(bpy.data.materials)
        
        if material_count == 0:
            self.report({'INFO'}, "No materials to delete")
            return {'CANCELLED'}
        
        material_names = [mat.name for mat in bpy.data.materials]
        backup_data = DeletionHistoryManager.create_material_backup(material_names)
        
        for material in list(bpy.data.materials):
            bpy.data.materials.remove(material)
        
        DeletionHistoryManager.add_history_entry(
            context.scene,
            'ALL_MATERIALS',
            material_names,
            material_count,
            backup_data
        )
        
        self.report({'INFO'}, f"✓ Permanently deleted {material_count} material(s) (backup saved in history)")
        return {'FINISHED'}

    def invoke(self, context, event):
        if len(bpy.data.materials) == 0:
            self.report({'WARNING'}, "No materials to delete")
            return {'CANCELLED'}
            
        return context.window_manager.invoke_confirm(self, event)


class MATERIAL_OT_remove_unused_materials(bpy.types.Operator):
    """Remove only unused materials"""
    bl_idname = "material.remove_unused_materials"
    bl_label = "Delete Unused Materials"
    bl_description = "Delete only materials not used by any object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed_count = 0
        material_names = []
        
        unused_materials = []
        for material in bpy.data.materials:
            if not material.users:
                unused_materials.append(material)
                material_names.append(material.name)
        
        backup_data = DeletionHistoryManager.create_material_backup(material_names)
        
        for material in unused_materials:
            try:
                bpy.data.materials.remove(material)
                removed_count += 1
            except Exception as e:
                print(f"Error deleting material {material.name}: {e}")
        
        if removed_count > 0:
            DeletionHistoryManager.add_history_entry(
                context.scene,
                'UNUSED_MATERIALS',
                material_names,
                removed_count,
                backup_data
            )
            print(f"✓ History entry added for {removed_count} unused materials")
        
        if removed_count > 0:
            self.report({'INFO'}, f"✓ Permanently deleted {removed_count} unused material(s) (backup saved in history)")
        else:
            self.report({'INFO'}, "✓ No unused materials found")
        
        return {'FINISHED'}

    def invoke(self, context, event):
        unused_count = sum(1 for material in bpy.data.materials if not material.users)
        
        if unused_count == 0:
            self.report({'INFO'}, "No unused materials found")
            return {'CANCELLED'}
            
        return context.window_manager.invoke_confirm(self, event)


class MATERIAL_OT_clean_orphan_data(bpy.types.Operator):
    """Clean orphan data (meshes, curves, etc. not used by any object)"""
    bl_idname = "material.clean_orphan_data"
    bl_label = "Clean Orphan Data"
    bl_description = "Remove orphan data blocks and objects without collections permanently (NOT added to history)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed_counts = {
            'meshes': 0,
            'curves': 0,
            'materials': 0,
            'textures': 0,
            'images': 0,
            'lights': 0,
            'cameras': 0,
            'armatures': 0,
            'lattices': 0,
            'metaballs': 0,
            'grease_pencils': 0,
            'node_groups': 0,
            'collections': 0,
            'orphan_objects': 0,  
        }
        
        print("Looking for non-collection items...")
        
        orphan_objects_to_remove = []
        
        for obj in bpy.data.objects:
            if len(obj.users_collection) == 0:
                orphan_objects_to_remove.append({
                    'name': obj.name,
                    'type': obj.type,
                    'data_name': obj.data.name if obj.data else None,
                    'data_type': self._get_data_type(obj.type),
                    'object_ref': obj 
                })
        
        print(f"Found {len(orphan_objects_to_remove)} object(s) without collection")
        
        for obj_info in orphan_objects_to_remove:
            obj_name = obj_info['name']
            obj_type = obj_info['type']
            data_block_name = obj_info['data_name']
            data_type = obj_info['data_type']
            
            try:
                if obj_name in bpy.data.objects:
                    obj = bpy.data.objects[obj_name]
                    
                    bpy.data.objects.remove(obj, do_unlink=True)
                    removed_counts['orphan_objects'] += 1
                    
                    print(f"✅ Successfully deleted orphan object: {obj_name} ({obj_type})")
                    
                    if data_block_name and data_type:
                        import time
                        time.sleep(0.01)
                        
                        data_col = getattr(bpy.data, data_type, None)
                        if data_col and data_block_name in data_col:
                            data_obj = data_col[data_block_name]
                            if data_obj.users == 0:
                                data_col.remove(data_obj)
                                print(f"  Also deleted data block: {data_block_name}")
                else:
                    print(f"⚠️ Object {obj_name} It no longer exists, jumping...")
                    
            except Exception as e:
                print(f"❌ Error deleting orphan object {obj_name}: {e}")
                import traceback
                traceback.print_exc()
        
        for mesh in list(bpy.data.meshes):
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
                removed_counts['meshes'] += 1
        
        for curve in list(bpy.data.curves):
            if curve.users == 0:
                bpy.data.curves.remove(curve)
                removed_counts['curves'] += 1
        
        for material in list(bpy.data.materials):
            if material.users == 0:
                bpy.data.materials.remove(material)
                removed_counts['materials'] += 1
        
        for texture in list(bpy.data.textures):
            if texture.users == 0:
                bpy.data.textures.remove(texture)
                removed_counts['textures'] += 1
        
        for image in list(bpy.data.images):
            if image.users == 0:
                bpy.data.images.remove(image)
                removed_counts['images'] += 1
        
        for light in list(bpy.data.lights):
            if light.users == 0:
                bpy.data.lights.remove(light)
                removed_counts['lights'] += 1
        
        for camera in list(bpy.data.cameras):
            if camera.users == 0:
                bpy.data.cameras.remove(camera)
                removed_counts['cameras'] += 1
        
        for armature in list(bpy.data.armatures):
            if armature.users == 0:
                bpy.data.armatures.remove(armature)
                removed_counts['armatures'] += 1
        
        for lattice in list(bpy.data.lattices):
            if lattice.users == 0:
                bpy.data.lattices.remove(lattice)
                removed_counts['lattices'] += 1
        
        for metaball in list(bpy.data.metaballs):
            if metaball.users == 0:
                bpy.data.metaballs.remove(metaball)
                removed_counts['metaballs'] += 1
        
        for gpencil in list(bpy.data.grease_pencils):
            if gpencil.users == 0:
                bpy.data.grease_pencils.remove(gpencil)
                removed_counts['grease_pencils'] += 1
        
        for node_group in list(bpy.data.node_groups):
            if node_group.users == 0:
                try:
                    self._safe_unlink_node_group(node_group)
                    bpy.data.node_groups.remove(node_group, do_unlink=True)
                    removed_counts['node_groups'] += 1
                except (RuntimeError, AttributeError):
                    pass
        
        for collection in list(bpy.data.collections):
            if collection.library:
                continue
            
            if collection.name == "Collection" and collection.name == context.scene.collection.name:
                continue
            
            if collection.name == "Trash Collection":
                continue
            
            if len(collection.objects) == 0 and len(collection.children) == 0 and collection.users == 0:
                try:
                    bpy.data.collections.remove(collection)
                    removed_counts['collections'] += 1
                except Exception as e:
                    print(f"Warning: Could not remove collection {collection.name}: {e}")
        
        total_removed = sum(removed_counts.values())
        

        
        if total_removed > 0:
            details = []
            for name, count in removed_counts.items():
                if count > 0:
                    name_trans = {
                        'meshes': 'mallas',
                        'curves': 'curvas',
                        'materials': 'materiales',
                        'textures': 'texturas',
                        'images': 'imágenes',
                        'lights': 'luces',
                        'cameras': 'cámaras',
                        'armatures': 'armaduras',
                        'lattices': 'lattices',
                        'metaballs': 'metaballs',
                        'grease_pencils': 'grease pencils',
                        'node_groups': 'grupos de nodos',
                        'collections': 'colecciones',
                        'orphan_objects': 'objetos sin colección',
                    }
                    details.append(f"{count} {name_trans.get(name, name)}")
            
            details_text = ", ".join(details)
            self.report({'INFO'}, f"✓ PERMANENTLY removed {total_removed} items: {details_text}")
        else:
            self.report({'INFO'}, "✓ No orphan data found")
        
        return {'FINISHED'}
    
    def _get_data_type(self, obj_type):
        """Get the data type of the object"""
        type_map = {
            'MESH': 'meshes',
            'CURVE': 'curves',
            'CAMERA': 'cameras',
            'LIGHT': 'lights',
            'ARMATURE': 'armatures',
            'LATTICE': 'lattices',
            'META': 'metaballs',
            'FONT': 'curves',
            'SURFACE': 'curves',
            'GPENCIL': 'grease_pencils',
        }
        return type_map.get(obj_type, None)
    
    def invoke(self, context, event):
        orphan_count = 0
        
        orphan_objects_count = sum(1 for obj in bpy.data.objects if len(obj.users_collection) == 0)
        orphan_count += orphan_objects_count
        
        orphan_count += sum(1 for mesh in bpy.data.meshes if mesh.users == 0)
        orphan_count += sum(1 for curve in bpy.data.curves if curve.users == 0)
        orphan_count += sum(1 for material in bpy.data.materials if material.users == 0)
        orphan_count += sum(1 for texture in bpy.data.textures if texture.users == 0)
        orphan_count += sum(1 for image in bpy.data.images if image.users == 0)
        orphan_count += sum(1 for node_group in bpy.data.node_groups if node_group.users == 0)
        
        if orphan_count == 0:
            self.report({'INFO'}, "No orphan data found")
            return {'CANCELLED'}
        
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self, context):
        layout = self.layout
        
        orphan_details = []
        
        orphan_objects_count = sum(1 for obj in bpy.data.objects if len(obj.users_collection) == 0)
        if orphan_objects_count > 0:
            orphan_details.append(f"Objects without collections: {orphan_objects_count}")
        
        mesh_count = sum(1 for mesh in bpy.data.meshes if mesh.users == 0)
        if mesh_count > 0:
            orphan_details.append(f"Meshes: {mesh_count}")
        
        curve_count = sum(1 for curve in bpy.data.curves if curve.users == 0)
        if curve_count > 0:
            orphan_details.append(f"Curves: {curve_count}")
        
        material_count = sum(1 for material in bpy.data.materials if material.users == 0)
        if material_count > 0:
            orphan_details.append(f"Materials: {material_count}")
        
        node_group_count = sum(1 for ng in bpy.data.node_groups if ng.users == 0)
        if node_group_count > 0:
            orphan_details.append(f"Node Groups: {node_group_count}")
        
        box = layout.box()
        box.alert = True
        box.label(text="⚠️ PERMANENT DELETION WARNING", icon='ERROR')
        
        row = box.row()
        row.scale_y = 0.8
        row.label(text="All orphan data will be PERMANENTLY deleted", icon='CANCEL')
        row = box.row()
        row.scale_y = 0.8
        row.label(text="This includes objects without collections!", icon='ERROR')
        row = box.row()
        row.scale_y = 0.8
        row.label(text="This cannot be undone!", icon='ERROR')
        
        if orphan_details:
            box = layout.box()
            box.label(text="Items to be removed:", icon='INFO')
            col = box.column(align=True)
            col.scale_y = 0.8
            for detail in orphan_details:
                col.label(text=f"• {detail}")
            
            total = sum(int(d.split(':')[1].strip()) for d in orphan_details)
            col.label(text=f"Total: {total} items")
        
        warning_box = layout.box()
        warning_box.alert = True
        warning_row = warning_box.row()
        warning_row.alignment = 'CENTER'
        warning_row.label(text="⚠️ Press ESC to cancel", icon='ERROR')
    
    def _safe_unlink_node_group(self, node_group):
        """Safely unlink node group before removal"""
        try:
            for material in bpy.data.materials:
                if material.use_nodes and material.node_tree:
                    for node in material.node_tree.nodes:
                        if hasattr(node, 'node_tree') and node.node_tree == node_group:
                            node.node_tree = None
            
            for ng in bpy.data.node_groups:
                if ng == node_group:
                    continue
                for node in ng.nodes:
                    if hasattr(node, 'node_tree') and node.node_tree == node_group:
                        node.node_tree = None
            
            for obj in bpy.data.objects:
                for modifier in obj.modifiers:
                    if modifier.type == 'NODES' and hasattr(modifier, 'node_group'):
                        if modifier.node_group == node_group:
                            modifier.node_group = None
        except:
            pass

class MATERIAL_OT_clean_empty_slots(bpy.types.Operator):
    """Clean empty material slots from all objects"""
    bl_idname = "material.clean_empty_slots"
    bl_label = "Clean Empty Slots"
    bl_description = "Remove empty material slots from all objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed_count = 0
        
        for obj in bpy.data.objects:
            if not hasattr(obj, 'material_slots') or not obj.material_slots:
                continue
                
            empty_indices = [i for i, slot in enumerate(obj.material_slots) if slot.material is None]
            
            if not empty_indices:
                continue
            
            was_hidden_viewport = obj.hide_viewport
            was_hidden_render = obj.hide_render
            was_selected = obj.select_get() if hasattr(obj, 'select_get') else False
            original_active = context.view_layer.objects.active
            
            if len(obj.users_collection) == 0:
                print(f"Skipping object '{obj.name}' - not in any collection")
                continue
            
            obj_in_view_layer = False
            for coll in obj.users_collection:
                if coll.name in context.view_layer.layer_collection.children:
                    obj_in_view_layer = True
                    break
            
            if not obj_in_view_layer:
                try:
                    context.collection.objects.link(obj)
                except:
                    print(f"Could not link object '{obj.name}' to view layer, skipping")
                    continue
            
            if was_hidden_viewport:
                obj.hide_viewport = False
            if was_hidden_render:
                obj.hide_render = False
            
            try:
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                try:
                    for i in reversed(empty_indices):
                        if i < len(obj.material_slots):
                            obj.active_material_index = i
                            
                            try:
                                with context.temp_override(
                                    object=obj,
                                    active_object=obj,
                                    selected_objects=[obj],
                                    selected_editable_objects=[obj]
                                ):
                                    bpy.ops.object.material_slot_remove()
                                removed_count += 1
                            except (RuntimeError, AttributeError):
                                pass
                finally:
                    obj.select_set(was_selected)
                    
            except RuntimeError as e:
                print(f"Error selecting object '{obj.name}': {e}")
                continue
            finally:
                obj.hide_viewport = was_hidden_viewport
                obj.hide_render = was_hidden_render
                
                try:
                    context.view_layer.objects.active = original_active
                except:
                    pass
        
        if removed_count > 0:
            DeletionHistoryManager.add_history_entry(
                context.scene,
                'EMPTY_SLOT',
                [f"{removed_count} empty slots cleaned"],
                removed_count
            )
        
        if removed_count > 0:
            self.report({'INFO'}, f"✓ Removed {removed_count} empty material slot(s)")
        else:
            self.report({'INFO'}, "✓ No empty material slots found")
        
        return {'FINISHED'}

class MATERIAL_OT_clean_orphan_fast(bpy.types.Operator):
    """Clean orphan data immediately (no confirmation dialog)"""
    bl_idname = "material.clean_orphan_fast"
    bl_label = "Clean Orphan (Fast)"
    bl_description = "Immediately remove orphan data blocks permanently"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed_counts = {
            'meshes': 0,
            'curves': 0,
            'materials': 0,
            'textures': 0,
            'images': 0,
            'lights': 0,
            'cameras': 0,
            'armatures': 0,
            'lattices': 0,
            'metaballs': 0,
            'grease_pencils': 0,
            'node_groups': 0,
            'collections': 0,
        }
        
        total_before = 0
        
        meshes_to_remove = [m for m in bpy.data.meshes if m.users == 0]
        for mesh in meshes_to_remove:
            try:
                bpy.data.meshes.remove(mesh)
                removed_counts['meshes'] += 1
            except:
                pass
        
        curves_to_remove = [c for c in bpy.data.curves if c.users == 0]
        for curve in curves_to_remove:
            try:
                bpy.data.curves.remove(curve)
                removed_counts['curves'] += 1
            except:
                pass
        
        materials_to_remove = [m for m in bpy.data.materials if m.users == 0]
        for material in materials_to_remove:
            try:
                bpy.data.materials.remove(material)
                removed_counts['materials'] += 1
            except:
                pass
        
        textures_to_remove = [t for t in bpy.data.textures if t.users == 0]
        for texture in textures_to_remove:
            try:
                bpy.data.textures.remove(texture)
                removed_counts['textures'] += 1
            except:
                pass
        
        images_to_remove = [i for i in bpy.data.images if i.users == 0]
        for image in images_to_remove:
            try:
                bpy.data.images.remove(image)
                removed_counts['images'] += 1
            except:
                pass
        
        lights_to_remove = [l for l in bpy.data.lights if l.users == 0]
        for light in lights_to_remove:
            try:
                bpy.data.lights.remove(light)
                removed_counts['lights'] += 1
            except:
                pass
        
        cameras_to_remove = [c for c in bpy.data.cameras if c.users == 0]
        for camera in cameras_to_remove:
            try:
                bpy.data.cameras.remove(camera)
                removed_counts['cameras'] += 1
            except:
                pass
        
        node_groups_to_remove = [ng for ng in bpy.data.node_groups if ng.users == 0]
        for node_group in node_groups_to_remove:
            try:
                for material in bpy.data.materials:
                    if material.use_nodes and material.node_tree:
                        for node in material.node_tree.nodes:
                            if hasattr(node, 'node_tree') and node.node_tree == node_group:
                                node.node_tree = None
                bpy.data.node_groups.remove(node_group, do_unlink=True)
                removed_counts['node_groups'] += 1
            except:
                pass
        
        total_removed = sum(removed_counts.values())
        
        if total_removed > 0:
            details = []
            for name, count in removed_counts.items():
                if count > 0:
                    name_trans = {
                        'meshes': 'mallas',
                        'curves': 'curvas',
                        'materials': 'materiales',
                        'textures': 'texturas',
                        'images': 'imágenes',
                        'lights': 'luces',
                        'cameras': 'cámaras',
                        'armatures': 'armaduras',
                        'lattices': 'lattices',
                        'metaballs': 'metaballs',
                        'grease_pencils': 'grease pencils',
                        'node_groups': 'grupos de nodos',
                        'collections': 'colecciones',
                    }
                    details.append(f"{count} {name_trans.get(name, name)}")
            
            details_text = ", ".join(details)
            self.report({'INFO'}, f"✓ Eliminated {total_removed} orphan: {details_text}")
        else:
            self.report({'INFO'}, "✓ There is no orphan data")
        
        return {'FINISHED'}

class MATERIAL_OT_remove_geometry_dialog(bpy.types.Operator):
    """Dialog to select and remove geometry"""
    bl_idname = "material.remove_geometry_dialog"
    bl_label = "Tavo Geometry Eliminator"
    bl_options = {'REGISTER', 'INTERNAL'}

    selected_objects: bpy.props.CollectionProperty(
        type=GeometrySelectionItem
    )
    
    search_filter: bpy.props.StringProperty(
        name="Search",
        description="Filter objects by name",
        default=""
    )
    
    object_types: bpy.props.EnumProperty(
        name="Object Types",
        description="Types of objects to show",
        items=[
            ('ALL', "All Types", "Show all object types"),
            ('MESH', "Meshes", "Show only mesh objects"),
            ('CURVE', "Curves", "Show only curve objects"),
            ('SURFACE', "Surfaces", "Show only surface objects"),
            ('META', "Metaballs", "Show only metaball objects"),
            ('FONT', "Text", "Show only text objects"),
            ('EMPTY', "Empties", "Show only empty objects"),
            ('LIGHT', "Lights", "Show only light objects"),
            ('CAMERA', "Cameras", "Show only camera objects"),
            ('ARMATURE', "Armatures", "Show only armature objects"),
            ('LATTICE', "Lattices", "Show only lattice objects"),
            ('SPEAKER', "Speakers", "Show only speaker objects"),
            ('LIGHT_PROBE', "Light Probes", "Show only light probe objects"),
        ],
        default='ALL'
    )
    
    show_hidden_viewport: bpy.props.BoolProperty(
        name="Show Hidden in Viewport",
        description="Show objects hidden in viewport",
        default=True
    )
    
    show_hidden_render: bpy.props.BoolProperty(
        name="Show Hidden in Render",
        description="Show objects hidden in render",
        default=True
    )
    
    show_visible_objects: bpy.props.BoolProperty(
        name="Show Visible Objects",
        description="Show objects that are visible in viewport and render",
        default=True
    )
    
    show_orphan_objects: bpy.props.BoolProperty(
        name="Show Orphan Objects",
        description="Show objects without any collection (orphan)",
        default=True
    )
    
    select_all_trigger: bpy.props.BoolProperty(
        name="Select All",
        description="Select all objects",
        default=False
    )
    
    select_all_processed: bpy.props.BoolProperty(
        default=False
    )

    def execute(self, context):
        removed_count = 0
        objects_to_remove = []
        
        for item in self.selected_objects:
            if item.selected and item.name in bpy.data.objects:
                obj = bpy.data.objects[item.name]
                
                if len(obj.users_collection) > 0:
                    objects_to_remove.append(item.name)
                else:
                    print(f"⚠️ Skipping orphan object: {item.name}")
        
        if not objects_to_remove:
            self.report({'WARNING'}, "No active objects selected.")
            return {'CANCELLED'}
        
        geometry_backup_json = DeletionHistoryManager.create_geometry_backup(objects_to_remove, context)
        
        materials_backup_json = DeletionHistoryManager.create_materials_backup_for_objects(objects_to_remove)
        
        combined_backup = {
            "geometry": json.loads(geometry_backup_json) if geometry_backup_json else {},
            "materials": json.loads(materials_backup_json) if materials_backup_json else {},
            "timestamp": time.time()
        }
        
        combined_json = json.dumps(combined_backup)
        
        for obj_name in objects_to_remove:
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                for coll in list(obj.users_collection):
                    coll.objects.unlink(obj)
                removed_count += 1
        
        if removed_count > 0:
            DeletionHistoryManager.add_history_entry(
                context.scene,
                'GEOMETRY',
                objects_to_remove,
                removed_count,
                combined_json  
            )
            self.report({'INFO'}, f"Removed {removed_count} active object(s) (added to Deletion History)")
        
        return {'FINISHED'}

    def invoke(self, context, event):
        self.selected_objects.clear()
        self.select_all_trigger = False
        self.select_all_processed = False
        
        for obj in bpy.data.objects:
            item = self.selected_objects.add()
            item.name = obj.name
            item.selected = False
            item.type = obj.type
            item.hide_viewport = obj.hide_viewport or obj.hide_get()
            item.hide_viewport_temp = obj.hide_get()  
            item.hide_render = obj.hide_render
            item.users = obj.users
            if len(obj.users_collection) == 0:
                item.hide_viewport_temp = True  
        
        return context.window_manager.invoke_props_dialog(self, width=800)

    def check_select_all(self):
        """Process select all trigger if needed"""
        if self.select_all_trigger and not self.select_all_processed:
            for item in self.selected_objects:
                if self._matches_filters(item):
                    item.selected = True
            self.select_all_processed = True
        elif not self.select_all_trigger and self.select_all_processed:
            for item in self.selected_objects:
                item.selected = False
            self.select_all_processed = False
    
    def _matches_filters(self, item):
        """Check if item matches current filters"""
        if self.search_filter and self.search_filter.lower() not in item.name.lower():
            return False
        
        if self.object_types != 'ALL' and item.type != self.object_types:
            return False
        
        obj = bpy.data.objects.get(item.name)
        is_orphan = obj and len(obj.users_collection) == 0
        
        if is_orphan:
            return self.show_orphan_objects
        
        is_visible = not item.hide_viewport and not item.hide_render
        is_hidden_viewport = item.hide_viewport or item.hide_viewport_temp
        is_hidden_render = item.hide_render
        
        if self.show_visible_objects and is_visible:
            return True
        if self.show_hidden_viewport and is_hidden_viewport:
            return True
        if self.show_hidden_render and is_hidden_render:
            return True
        
        return False

    def draw(self, context):
        layout = self.layout
        
        self.check_select_all()
        
        box = layout.box()
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text="Tavo Geometry Eliminator", icon_value=botton_geometry_icon_id)
        row = box.row()
        row.alignment = 'CENTER'
        row.scale_y = 0.8
        row.label(text="Manage all geometry objects in your scene")
        
        layout.separator()
        
        aux_box = layout.box()
        aux_box.label(text="Quick Actions", icon='PLAY')
        
        row = aux_box.row(align=True)
        row.scale_y = 1.2
        
        row.operator("material.remove_materials_dialog", 
                    text="Tavo Material Eliminator", 
                    icon_value=botton_materials_icon_id)
        
        row.operator("material.remove_node_groups_dialog", 
                    text="Tavo Node Groups Eliminator", 
                    icon_value=botton_node_groups_icon_id)
        
        row.operator("material.remove_collections_dialog", 
                    text="Tavo Collections Eliminator", 
                    icon_value=botton_collections_icon_id)
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Filters & Selection", icon='FILTER')
        
        row = box.row()
        row.prop(self, "search_filter", text="", icon='VIEWZOOM')
        row.prop(self, "select_all_trigger", text="Select All", toggle=True)
        
        col = box.column(align=True)
        
        row = col.row()
        row.label(text="Object Types:")
        row = col.row(align=True)
        row.prop(self, "object_types", text="")
        
        col.separator()
        
        row = col.row()
        row.label(text="Visibility Filters:")
        
        grid = col.grid_flow(row_major=True, columns=4, align=True)   
        grid.prop(self, "show_visible_objects", text="Visible", toggle=True, icon='HIDE_OFF')
        grid.prop(self, "show_hidden_viewport", text="Hidden Viewport", toggle=True, icon='RESTRICT_VIEW_ON')
        grid.prop(self, "show_hidden_render", text="Hidden Render", toggle=True, icon='RESTRICT_RENDER_ON')
        grid.prop(self, "show_orphan_objects", text="Orphan", toggle=True, icon='ORPHAN_DATA') 
        
        help_box = col.box()
        help_col = help_box.column(align=True)
        help_col.scale_y = 0.7
        help_col.label(text="Filter Help:", icon='QUESTION')
        help_col.label(text="• Visible: Objects visible in both viewport and render")
        help_col.label(text="• Hidden Viewport: Objects hidden in viewport (eye icon or H key)")
        help_col.label(text="• Hidden Render: Objects hidden in render (camera icon)")
        help_col.label(text="• Orphan: Objects without any collection", icon='ORPHAN_DATA')
        help_col.label(text="  - These are not visible in Outliner")
        help_col.label(text="  - Usually created when restoring from history")
        help_col.label(text="  - Can be cleaned with 'Clean Orphan' button")
        
        layout.separator()
        
        maintenance_box = layout.box()
        maintenance_box.label(text="Maintenance Tools", icon_value=botton_geometry_icon_id)
        
        row = maintenance_box.row(align=True)
        row.scale_y = 1.2
        
        orphan_objects_count = sum(1 for obj in bpy.data.objects if len(obj.users_collection) == 0)
        orphan_data_count = self.count_orphan_data()
        total_orphan = orphan_objects_count + orphan_data_count
        
        if total_orphan > 0:
            orphan_text = f"Clean Orphan Data ({total_orphan})"
        else:
            orphan_text = "Clean Orphan Data"
        
        row.operator("material.clean_orphan_data", 
                    text=orphan_text, 
                    icon_value=botton_orphan_data_icon_id)
        
        row.operator("material.clean_material_duplicates", 
                    text="Clean Material Duplicates", 
                    icon_value=botton_Clean_material_duplicates_icon_id)
        
        layout.separator()
       
        box = layout.box()
        row = box.row()
        row.label(text="All Scene Objects (including orphan objects)", icon='OUTLINER_OB_MESH')
        row = box.row()
        row.scale_y = 0.7
        row.label(text="Orphan objects have no collection and are not visible in Outliner", icon='INFO')
        
        row = box.row()
        row.scale_y = 0.8
        row.label(text="Select")
        row.label(text="Name")
        row.label(text="Type")
        row.label(text="Visibility")
        row.label(text="Users")
        
        box = layout.box()
        col = box.column(align=True)
        
        search_lower = self.search_filter.lower()
        visible_count = 0
        selected_count = 0
        
        for item in self.selected_objects:
            if not self._matches_filters(item):
                continue
                
            visible_count += 1
            if item.selected:
                selected_count += 1
                
            row = col.row(align=True)
            row.prop(item, "selected", text="")
            
            icon = self._get_object_icon(item.type)
            row.label(text=item.name, icon=icon)
            
            row.label(text=item.type.title())
            
            obj = bpy.data.objects.get(item.name)
            is_orphan = obj and len(obj.users_collection) == 0
            is_hidden_viewport = item.hide_viewport or (item.hide_viewport_temp and not is_orphan)
            
            if is_orphan:
                row.label(text="⚠️ Orphan (No Collection)", icon='ORPHAN_DATA')
            elif is_hidden_viewport and item.hide_render:
                if item.hide_viewport_temp:
                    row.label(text="Hidden Everywhere (Temp)", icon='RESTRICT_VIEW_OFF')
                else:
                    row.label(text="Hidden Everywhere", icon='RESTRICT_VIEW_OFF')
            elif is_hidden_viewport:
                if item.hide_viewport_temp:
                    row.label(text="Hidden in Viewport (H)", icon='RESTRICT_VIEW_ON')
                else:
                    row.label(text="Hidden in Viewport", icon='RESTRICT_VIEW_ON')
            elif item.hide_render:
                row.label(text="Hidden in Render", icon='RESTRICT_RENDER_ON')
            else:
                row.label(text="Visible", icon='HIDE_OFF')
            
            users_text = f"{item.users}"
            if item.users == 0:
                row.label(text=users_text, icon='ORPHAN_DATA')
            else:
                row.label(text=users_text, icon='LINKED')
        
        if len(self.selected_objects) == 0:
            col = box.column(align=True)
            col.alignment = 'CENTER'
            col.scale_y = 1.5
            col.label(text="No objects in scene", icon='INFO')
        elif visible_count == 0:
            col = box.column(align=True)
            col.alignment = 'CENTER'
            col.scale_y = 1.5
            col.label(text="No objects match current filters", icon='INFO')
            col.label(text="Try adjusting your search or filter settings")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Scene Statistics", icon='LINENUMBERS_ON')
        
        col = box.column(align=True)
        col.scale_y = 0.8
        
        total_objects = len(bpy.data.objects)
        hidden_viewport = sum(1 for obj in bpy.data.objects if obj.hide_viewport or obj.hide_get())
        hidden_render = sum(1 for obj in bpy.data.objects if obj.hide_render)
        hidden_both = sum(1 for obj in bpy.data.objects if (obj.hide_viewport or obj.hide_get()) and obj.hide_render)
        unused_objects = sum(1 for obj in bpy.data.objects if obj.users == 0)
        visible_objects = total_objects - hidden_viewport
        
        orphan_objects_count = sum(1 for obj in bpy.data.objects if len(obj.users_collection) == 0)
        orphan_data_count = self.count_orphan_data()
        
        orphan_node_groups = sum(1 for ng in bpy.data.node_groups if ng.users == 0)
        orphan_meshes = sum(1 for mesh in bpy.data.meshes if mesh.users == 0)

        col.label(text=f"Total Objects: {total_objects}")
        col.label(text=f"Visible Objects: {visible_objects}")
        col.label(text=f"Hidden in Viewport: {hidden_viewport}")
        col.label(text=f"Hidden in Render: {hidden_render}")
        col.label(text=f"Hidden Everywhere: {hidden_both}")
        col.label(text=f"Unused Objects: {unused_objects}")
        col.label(text=f"Orphan Objects (No Collection): {orphan_objects_count}") 
        col.label(text=f"Orphan Data Blocks: {orphan_data_count}")
        col.label(text=f"Orphan Node Groups: {orphan_node_groups}")
        col.label(text=f"Orphan Meshes: {orphan_meshes}")
        col.label(text=f"Selected for Removal: {selected_count}")
        
        type_counts = {}
        for obj in bpy.data.objects:
            type_counts[obj.type] = type_counts.get(obj.type, 0) + 1
        
        if type_counts:
            col.separator()
            col.label(text="Objects by Type:", icon='OUTLINER')
            for obj_type, count in sorted(type_counts.items()):
                icon = self._get_object_icon(obj_type)
                col.label(text=f"  • {obj_type.title()}: {count}", icon=icon)
        
        info_row = maintenance_box.row()
        info_row.scale_y = 0.7
        info_row.label(text="Use these tools to clean up after restoration", icon='INFO')
        
        if selected_count > 0:
            warning_box = layout.box()
            warning_box.alert = True
            row = warning_box.row()
            row.alignment = 'CENTER'
            row = warning_box.row()
            row.scale_y = 0.8
            row.alignment = 'CENTER'
            row.label(text=f"{selected_count} object(s) selected - Click OK to remove", icon='INFO')
        else:
            box = layout.box()
            col = box.column(align=True)
            col.alignment = 'CENTER'
            col.scale_y = 1.2
            col.label(text="Select objects above to remove them", icon='INFO')
        
        warning_box = layout.box()
        warning_box.alert = True
        warning_row = warning_box.row()
        warning_row.alignment = 'CENTER'
        warning_row.label(text="Press ESC to exit this panel", icon='ERROR')

    def _get_object_icon(self, obj_type):
        """Get appropriate icon for object type"""
        icons = {
            'MESH': 'MESH_DATA',
            'CURVE': 'CURVE_DATA',
            'SURFACE': 'SURFACE_DATA',
            'META': 'META_DATA',
            'FONT': 'FONT_DATA',
            'EMPTY': 'EMPTY_DATA',
            'LIGHT': 'LIGHT_DATA',
            'CAMERA': 'CAMERA_DATA',
            'ARMATURE': 'ARMATURE_DATA',
            'LATTICE': 'LATTICE_DATA',
            'SPEAKER': 'SPEAKER',
            'LIGHT_PROBE': 'LIGHT_PROBE',
        }
        return icons.get(obj_type, 'OBJECT_DATA')

    def count_empty_slots(self):
        """Count empty material slots in all objects"""
        empty_count = 0
        for obj in bpy.data.objects:
            if hasattr(obj, 'material_slots') and obj.material_slots:
                empty_count += sum(1 for slot in obj.material_slots if slot.material is None)
        return empty_count
    
    def count_orphan_data(self):
        """Count orphan data blocks"""
        orphan_count = 0
        orphan_count += sum(1 for mesh in bpy.data.meshes if mesh.users == 0)
        orphan_count += sum(1 for curve in bpy.data.curves if curve.users == 0)
        orphan_count += sum(1 for material in bpy.data.materials if material.users == 0)
        orphan_count += sum(1 for texture in bpy.data.textures if texture.users == 0)
        orphan_count += sum(1 for image in bpy.data.images if image.users == 0)
        orphan_count += sum(1 for node_group in bpy.data.node_groups if node_group.users == 0)
        return orphan_count
    
    @classmethod
    def poll(cls, context):
        """Allow dialog to open even when there are no objects"""
        return True

class MATERIAL_OT_remove_node_groups_dialog(bpy.types.Operator):
    """Dialog to select and remove node groups (Geometry Nodes, Shader Nodes, etc.)"""
    bl_idname = "material.remove_node_groups_dialog"
    bl_label = "Tavo Node Groups Eliminator"
    bl_options = {'REGISTER', 'INTERNAL'}

    selected_node_groups: bpy.props.CollectionProperty(
        type=NodeGroupSelectionItem
    )
    
    search_filter: bpy.props.StringProperty(
        name="Search",
        description="Filter node groups by name",
        default=""
    )
    
    node_group_types: bpy.props.EnumProperty(
        name="Node Group Types",
        description="Types of node groups to show",
        items=[
            ('ALL', "All Types", "Show all node group types"),
            ('GEOMETRY', "Geometry Nodes", "Show only Geometry Nodes"),
            ('SHADER', "Shader Nodes", "Show only Shader Nodes"),
            ('COMPOSITING', "Compositor Nodes", "Show only Compositor Nodes"),
            ('TEXTURE', "Texture Nodes", "Show only Texture Nodes"),
        ],
        default='ALL'
    )
    
    show_orphan_only: bpy.props.BoolProperty(
        name="Show Orphan Only",
        description="Show only node groups with no users",
        default=False
    )
    
    select_all_trigger: bpy.props.BoolProperty(
        name="Select All",
        description="Select all node groups",
        default=False
    )
    
    select_all_processed: bpy.props.BoolProperty(
        default=False
    )

    def execute(self, context):
        removed_count = 0
        failed_count = 0
        node_groups_to_remove = []
        
        for item in self.selected_node_groups:
            if item.selected and item.name in bpy.data.node_groups:
                node_groups_to_remove.append(item.name)
        
        if not node_groups_to_remove:
            self.report({'INFO'}, "No node groups selected for removal")
            return {'CANCELLED'}
        
        modifiers_to_remove = []
        for ng_name in node_groups_to_remove:
            ng = bpy.data.node_groups.get(ng_name)
            if not ng:
                continue
            for obj in bpy.data.objects:
                for mod in obj.modifiers:
                    if mod.type == 'NODES' and mod.node_group == ng:
                        modifiers_to_remove.append((obj, mod))
        
        for obj, mod in modifiers_to_remove:
            mod_name = mod.name
            obj_name = obj.name
            try:
                obj.modifiers.remove(mod)
                print(f"Removed modifier '{mod_name}' from object '{obj_name}'")
            except Exception as e:
                print(f"Error removing modifier {mod_name} from {obj_name}: {e}")
        
        for ng_name in node_groups_to_remove:
            if ng_name not in bpy.data.node_groups:
                continue
            try:
                node_group = bpy.data.node_groups[ng_name]
                bpy.data.node_groups.remove(node_group, do_unlink=True)
                removed_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Error removing node group {ng_name}: {e}")
        
        for area in context.screen.areas:
            area.tag_redraw()
        
        if removed_count > 0:

            self.report({'WARNING'}, f"⚠️ Permanently deleted {removed_count} node group(s) – NO history backup created!")
        else:
            if failed_count > 0:
                self.report({'WARNING'}, f"Failed to remove {failed_count} node group(s)")
        
        return {'FINISHED'}

    def invoke(self, context, event):
        self.selected_node_groups.clear()
        self.select_all_trigger = False
        self.select_all_processed = False
        
        for node_group in bpy.data.node_groups:
            item = self.selected_node_groups.add()
            item.name = node_group.name
            item.selected = False
            item.type = node_group.type
            item.users = node_group.users
        
        return context.window_manager.invoke_props_dialog(self, width=700)

    def count_empty_slots(self):
        """Count empty material slots in all objects"""
        empty_count = 0
        for obj in bpy.data.objects:
            if hasattr(obj, 'material_slots') and obj.material_slots:
                empty_count += sum(1 for slot in obj.material_slots if slot.material is None)
        return empty_count
    
    def check_select_all(self):
        """Process select all trigger if needed"""
        if self.select_all_trigger and not self.select_all_processed:
            for item in self.selected_node_groups:
                if self._matches_filters(item):
                    item.selected = True
            self.select_all_processed = True
        elif not self.select_all_trigger and self.select_all_processed:
            for item in self.selected_node_groups:
                item.selected = False
            self.select_all_processed = False
    
    def _matches_filters(self, item):
        """Check if item matches current filters"""
        if self.search_filter and self.search_filter.lower() not in item.name.lower():
            return False
        
        if self.node_group_types != 'ALL' and item.type != self.node_group_types:
            return False
        
        if self.show_orphan_only and item.users > 0:
            return False
        
        return True
    

    def draw(self, context):
        layout = self.layout
        
        self.check_select_all()
        
        box = layout.box()
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text="Tavo Node Groups Eliminator", icon_value=botton_node_groups_icon_id)
        row = box.row()
        row.alignment = 'CENTER'
        row.scale_y = 0.8
        row.label(text="Manage and remove Geometry Nodes, Shader Nodes, and other node groups")
        
        layout.separator()
        
        aux_box = layout.box()
        aux_box.label(text="Quick Actions", icon='PLAY')
        
        row = aux_box.row(align=True)
        row.scale_y = 1.2
        
        row.operator("material.remove_materials_dialog", 
                    text="Tavo Materials Eliminator", 
                    icon_value=botton_materials_icon_id)
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Filters & Selection", icon='FILTER')
        
        row = box.row()
        row.prop(self, "search_filter", text="", icon='VIEWZOOM')
        row.prop(self, "select_all_trigger", text="Select All", toggle=True)
        
        col = box.column(align=True)
        
        row = col.row()
        row.label(text="Node Group Types:")
        row = col.row(align=True)
        row.prop(self, "node_group_types", text="")
        
        col.separator()
        row = col.row()
        row.prop(self, "show_orphan_only", text="Show Orphan Only", toggle=True, icon='ORPHAN_DATA')
        
        layout.separator()
        
        box = layout.box()
        row = box.row()
        row.label(text="All Node Groups", icon_value=botton_node_groups_icon_id)
        
        row = box.row()
        row.scale_y = 0.8
        row.label(text="Select")
        row.label(text="Name")
        row.label(text="Type")
        row.label(text="Users")
        
        box = layout.box()
        col = box.column(align=True)
        
        search_lower = self.search_filter.lower()
        visible_count = 0
        selected_count = 0
        
        for item in self.selected_node_groups:
            if not self._matches_filters(item):
                continue
                
            visible_count += 1
            if item.selected:
                selected_count += 1
                
            row = col.row(align=True)
            row.prop(item, "selected", text="")
            
            icon = self._get_node_group_icon(item.type)
            row.label(text=item.name, icon=icon)
            
            row.label(text=item.type.title())
            
            users_text = f"{item.users}"
            if item.users == 0:
                row.label(text=users_text, icon='ORPHAN_DATA')
            else:
                row.label(text=users_text, icon='LINKED')
        
        if len(self.selected_node_groups) == 0:
            col = box.column(align=True)
            col.alignment = 'CENTER'
            col.scale_y = 1.5
            col.label(text="No node groups in file", icon='INFO')
        elif visible_count == 0:
            col = box.column(align=True)
            col.alignment = 'CENTER'
            col.scale_y = 1.5
            col.label(text="No node groups match current filters", icon='INFO')
            col.label(text="Try adjusting your search or filter settings")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Node Groups Statistics", icon='LINENUMBERS_ON')
        
        col = box.column(align=True)
        col.scale_y = 0.8
        
        total_node_groups = len(bpy.data.node_groups)
        geometry_nodes = sum(1 for ng in bpy.data.node_groups if ng.type == 'GEOMETRY')
        shader_nodes = sum(1 for ng in bpy.data.node_groups if ng.type == 'SHADER')
        compositor_nodes = sum(1 for ng in bpy.data.node_groups if ng.type == 'COMPOSITING')
        texture_nodes = sum(1 for ng in bpy.data.node_groups if ng.type == 'TEXTURE')
        orphan_node_groups = sum(1 for ng in bpy.data.node_groups if ng.users == 0)
        
        col.label(text=f"Total Node Groups: {total_node_groups}")
        col.label(text=f"Geometry Nodes: {geometry_nodes}", icon='GEOMETRY_NODES')
        col.label(text=f"Shader Nodes: {shader_nodes}", icon='SHADING_RENDERED')
        col.label(text=f"Compositor Nodes: {compositor_nodes}", icon='NODE_COMPOSITING')
        col.label(text=f"Texture Nodes: {texture_nodes}", icon='TEXTURE')
        col.label(text=f"Orphan Node Groups: {orphan_node_groups}", icon='ORPHAN_DATA')
        col.label(text=f"Selected for Removal: {selected_count}")
        
        if selected_count > 0:
            warning_box = layout.box()
            warning_box.alert = True
            row = warning_box.row()
            row.alignment = 'CENTER'
            row.label(text="This action cannot be undone!", icon='ERROR')
            row = warning_box.row()
            row.scale_y = 0.8
            row.alignment = 'CENTER'
            row.label(text=f"{selected_count} node group(s) selected - Click OK to remove", icon='INFO')
        else:
            box = layout.box()
            col = box.column(align=True)
            col.alignment = 'CENTER'
            col.scale_y = 1.2
            col.label(text="Select node groups above to remove them", icon='INFO')
        
        warning_box = layout.box()
        warning_box.alert = True
        warning_row = warning_box.row()
        warning_row.alignment = 'CENTER'
        warning_row.label(text="Press ESC to exit this panel", icon='ERROR')

    def _get_node_group_icon(self, ng_type):
        """Get appropriate icon for node group type"""
        icons = {
            'GEOMETRY': 'GEOMETRY_NODES',
            'SHADER': 'SHADING_RENDERED',
            'COMPOSITING': 'NODE_COMPOSITING',
            'TEXTURE': 'TEXTURE',
        }
        return icons.get(ng_type, 'NODETREE')
    
    def _unlink_node_group(self, node_group):
        """Unlink node group from all materials and node trees"""
        try:
            for material in bpy.data.materials:
                if material.use_nodes and material.node_tree:
                    try:
                        for node in material.node_tree.nodes:
                            if hasattr(node, 'node_tree') and node.node_tree == node_group:
                                node.node_tree = None
                    except (AttributeError, RuntimeError):
                        pass
            
            for ng in bpy.data.node_groups:
                if ng == node_group:
                    continue
                try:
                    for node in ng.nodes:
                        if hasattr(node, 'node_tree') and node.node_tree == node_group:
                            node.node_tree = None
                except (AttributeError, RuntimeError):
                    pass
            
            for obj in bpy.data.objects:
                try:
                    for modifier in obj.modifiers:
                        if modifier.type == 'NODES' and hasattr(modifier, 'node_group'):
                            if modifier.node_group == node_group:
                                modifier.node_group = None
                except (AttributeError, RuntimeError):
                    pass
        except Exception:
            pass
    
    @classmethod
    def poll(cls, context):
        """Allow dialog to open even when there are no node groups"""
        return True

    def _do_restore_geometry_with_modifiers(entry, context):
        """Restore geometry with its modifiers Geometry Nodes"""
        print(f"\n🔧 RESTORING GEOMETRY NODES WITH MODIFIERS")
        
        if not getattr(entry, 'data_backup', None):
            print("❌ No backup available")
            return False
        
        try:
            backup_data = json.loads(entry.data_backup)
            restored_count = 0
            modifiers_restored = 0
            
            for obj_data in backup_data.get("objects", []):
                obj_name = obj_data.get("name", "")
                if not obj_name:
                    continue
                
                if obj_name not in bpy.data.objects:
                    print(f"⚠️ Object {obj_name} It does not exist; modifiers cannot be restored")
                    continue
                
                obj = bpy.data.objects[obj_name]
                
                modifiers_data = obj_data.get("modifiers", [])
                for mod_data in modifiers_data:
                    mod_type = mod_data.get("type", "")
                    mod_name = mod_data.get("name", "")
                    
                    if mod_type == 'NODES':
                        existing_mod = obj.modifiers.get(mod_name)
                        
                        if existing_mod and existing_mod.type == 'NODES':
                            print(f"  ✅ Modifier {mod_name} already exists in {obj_name}")
                            continue
                        
                        try:
                            new_mod = obj.modifiers.new(name=mod_name, type='NODES')
                            
                            node_group_name = mod_data.get("node_group_name", "")
                            if node_group_name and node_group_name in bpy.data.node_groups:
                                new_mod.node_group = bpy.data.node_groups[node_group_name]
                                print(f"  ✅ Node group {node_group_name} assigned to {obj_name}")
                            
                            new_mod.show_viewport = mod_data.get("show_viewport", True)
                            new_mod.show_render = mod_data.get("show_render", True)
                            
                            inputs_data = mod_data.get("inputs", {})
                            if inputs_data and hasattr(new_mod, 'settings'):
                                for input_name, input_value in inputs_data.items():
                                    try:
                                        if input_name in new_mod.settings:
                                            try:
                                                setattr(new_mod.settings, input_name, input_value)
                                            except:
                                                try:
                                                    current_value = getattr(new_mod.settings, input_name)
                                                    if isinstance(current_value, float) and isinstance(input_value, (int, float)):
                                                        setattr(new_mod.settings, input_name, float(input_value))
                                                    elif isinstance(current_value, int) and isinstance(input_value, (int, float)):
                                                        setattr(new_mod.settings, input_name, int(input_value))
                                                    elif isinstance(current_value, bool) and isinstance(input_value, (bool, int)):
                                                        setattr(new_mod.settings, input_name, bool(input_value))
                                                except:
                                                    print(f"    ⚠️ Input could not be restored {input_name}")
                                    except:
                                        pass
                            
                            modifiers_restored += 1
                            print(f"  ✅ Geometry Nodes modifier restored: {mod_name}")
                            
                        except Exception as e:
                            print(f"  ❌ Error creating modifier {mod_name}: {e}")
                            import traceback
                            traceback.print_exc()
                
                restored_count += 1
            
            print(f"\n✅ Results:")
            print(f"  Processed objects: {restored_count}")
            print(f"  Modifiers restored: {modifiers_restored}")
            
            return restored_count > 0 or modifiers_restored > 0
            
        except Exception as e:
            print(f"❌ Error restoring Geometry Nodes: {e}")
            import traceback
            traceback.print_exc()
            return False

class MATERIAL_OT_remove_collections_dialog(bpy.types.Operator):
    """Dialog to select and remove collections"""
    bl_idname = "material.remove_collections_dialog"
    bl_label = "Tavo Collections Eliminator"
    bl_options = {'REGISTER', 'INTERNAL'}

    selected_collections: bpy.props.CollectionProperty(
        type=CollectionSelectionItem
    )
    
    search_filter: bpy.props.StringProperty(
        name="Search",
        description="Filter collections by name",
        default=""
    )
    
    show_empty_only: bpy.props.BoolProperty(
        name="Show Empty Only",
        description="Show only empty collections",
        default=False
    )
    
    select_all_trigger: bpy.props.BoolProperty(
        name="Select All",
        description="Select all collections",
        default=False
    )
    
    select_all_processed: bpy.props.BoolProperty(
        default=False
    )

    def execute(self, context):
        removed_count = 0
        collections_to_remove = []
        
        for item in self.selected_collections:
            if item.selected and item.name in bpy.data.collections:
                collections_to_remove.append(item.name)
        
        backup_data = DeletionHistoryManager.create_collection_backup(collections_to_remove, context)
        
        for coll_name in collections_to_remove:
            if coll_name in bpy.data.collections:
                try:
                    coll = bpy.data.collections[coll_name]
                    
                    for obj in list(coll.objects):
                        coll.objects.unlink(obj)
                    
                    bpy.data.collections.remove(coll)
                    removed_count += 1
                    
                except Exception as e:
                    print(f"Error removing collection {coll_name}: {e}")
        
        if removed_count > 0:
            DeletionHistoryManager.add_history_entry(
                context.scene,
                'COLLECTION',
                collections_to_remove,
                removed_count,
                backup_data
            )
            
            self.report({'INFO'}, f"✓ Removed {removed_count} collection(s) permanently")
        else:
            self.report({'INFO'}, "No collections selected for removal")
        
        return {'FINISHED'}

    def invoke(self, context, event):
        self.selected_collections.clear()
        self.select_all_trigger = False
        self.select_all_processed = False
        
        for collection in bpy.data.collections:
            if collection.name == context.scene.collection.name:
                continue
                
            item = self.selected_collections.add()
            item.name = collection.name
            item.selected = False
            item.type = 'COLLECTION'
            item.hide_viewport = collection.hide_viewport
            item.hide_render = collection.hide_render
            item.users = collection.users  
            item.object_count = len(collection.objects)
            item.child_count = len(collection.children)
            item.child_collection_count = sum(1 for child in collection.children if child.name in bpy.data.collections)
            item.is_linked = bool(collection.library)
            item.is_empty = (len(collection.objects) == 0 and len(collection.children) == 0)
        
        return context.window_manager.invoke_props_dialog(self, width=600)

    def check_select_all(self):
        """Process select all trigger if needed"""
        if self.select_all_trigger and not self.select_all_processed:
            for item in self.selected_collections:
                if self._matches_filters(item):
                    item.selected = True
            self.select_all_processed = True
        elif not self.select_all_trigger and self.select_all_processed:
            for item in self.selected_collections:
                item.selected = False
            self.select_all_processed = False
    
    def _matches_filters(self, item):
        """Check if item matches current filters"""
        if self.search_filter and self.search_filter.lower() not in item.name.lower():
            return False
        
        if self.show_empty_only and not item.is_empty:
            return False
        
        return True

    def draw(self, context):
        layout = self.layout
        
        self.check_select_all()
        
        box = layout.box()
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text=" Tavo Collections Eliminator", icon_value=botton_collections_icon_id)
        row = box.row()
        row.alignment = 'CENTER'
        row.scale_y = 0.8
        row.label(text="Manage and remove collections from your scene")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Filters & Selection", icon='FILTER')
        
        row = box.row()
        row.prop(self, "search_filter", text="", icon='VIEWZOOM')
        row.prop(self, "select_all_trigger", text="Select All", toggle=True)
        
        col = box.column(align=True)
        col.prop(self, "show_empty_only", text="Show Empty Only", toggle=True, icon='EMPTY_AXIS')
        
        layout.separator()
        
        box = layout.box()
        row = box.row()
        row.label(text="All Collections", icon_value=botton_collections_icon_id)
        
        row = box.row()
        row.scale_y = 0.8
        row.label(text="Select")
        row.label(text="Name")
        row.label(text="Objects")
        row.label(text="Children")
        row.label(text="Users")
        row.label(text="Status")
        
        box = layout.box()
        col = box.column(align=True)
        
        search_lower = self.search_filter.lower()
        visible_count = 0
        selected_count = 0
        
        for item in self.selected_collections:
            if not self._matches_filters(item):
                continue
                
            visible_count += 1
            if item.selected:
                selected_count += 1
                
            row = col.row(align=True)
            row.prop(item, "selected", text="")
            
            row.label(text=item.name, icon='OUTLINER_COLLECTION')
            
            row.label(text=f"Obj: {item.object_count}")
            
            row.label(text=f"Child: {item.child_collection_count}")

            users_text = f"Use: {item.users}"
            row.label(text=users_text)
            
            status_text = []
            if item.is_empty:
                status_text.append("Empty")
            if item.is_linked:
                status_text.append("Linked")
            if item.hide_viewport:
                status_text.append("Hidden")
            
            if status_text:
                row.label(text=", ".join(status_text), icon='INFO')
            else:
                row.label(text="Active")
        
        if visible_count == 0:
            col = box.column(align=True)
            col.alignment = 'CENTER'
            col.scale_y = 1.5
            col.label(text="No collections match current filters", icon='INFO')
            col.label(text="Try adjusting your search or filter settings")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Collections Statistics", icon='LINENUMBERS_ON')
        
        col = box.column(align=True)
        col.scale_y = 0.8
        
        total_collections = len(self.selected_collections)
        empty_collections = sum(1 for item in self.selected_collections if item.is_empty)
        linked_collections = sum(1 for item in self.selected_collections if item.is_linked)
        hidden_collections = sum(1 for item in self.selected_collections if item.hide_viewport)
        
        #slow more theme
        col.label(text=f"Total Collections: {total_collections}")
        col.label(text=f"Empty Collections: {empty_collections}", icon='EMPTY_AXIS')
        col.label(text=f"Linked Collections: {linked_collections}", icon='LIBRARY_DATA_DIRECT')
        col.label(text=f"Hidden Collections: {hidden_collections}", icon='HIDE_ON')
        col.label(text=f"Selected for Removal: {selected_count}")
        
        if selected_count > 0:
            warning_box = layout.box()
            warning_box.alert = True
            row = warning_box.row()
            row.alignment = 'CENTER'
            row.label(text="This action cannot be undone!", icon='ERROR')
            row = warning_box.row()
            row.scale_y = 0.8
            row.alignment = 'CENTER'
            row.label(text=f"{selected_count} collection(s) selected - Click OK to remove", icon='INFO')
        else:
            box = layout.box()
            col = box.column(align=True)
            col.alignment = 'CENTER'
            col.scale_y = 1.2
            col.label(text="Select collections above to remove them", icon='INFO')
        
        warning_box = layout.box()
        warning_box.alert = True
        warning_row = warning_box.row()
        warning_row.alignment = 'CENTER'
        warning_row.label(text="⚠️ Press ESC to cancel", icon='ERROR')
    
    @classmethod
    def poll(cls, context):
        """Allow dialog to open even when there are no collections"""
        return True

class MATERIAL_OT_remove_unused_materials_fast(bpy.types.Operator):
    """Remove unused materials immediately (no confirmation dialog)"""
    bl_idname = "material.remove_unused_materials_fast"
    bl_label = "Remove Unused Materials (Fast)"
    bl_description = "Immediately remove materials not used by any object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed_count = 0
        material_names = []
        
        for material in list(bpy.data.materials):
            if not material.users:
                material_names.append(material.name)
                bpy.data.materials.remove(material)
                removed_count += 1
        
        if removed_count > 0:
            self.report({'INFO'}, f"✓ Eliminated {removed_count} unused materials")
        else:
            self.report({'INFO'}, "✓ No unused materials to eliminate")
        
        return {'FINISHED'}


classes_property = [
    MaterialSelectionItem,
    GeometrySelectionItem,
    NodeGroupSelectionItem,
    CollectionSelectionItem,
    SeparationTempItem,
]

classes_ui = [
    SeparationItemList,
]

classes_operators = [

    MATERIAL_OT_clean_material_duplicates,
    MATERIAL_OT_view_deletion_history,
    MATERIAL_OT_simple_toggle,
    MATERIAL_OT_select_all_history,
    WM_OT_tooltip,
    MATERIAL_OT_restore_selected_history,
    
    MATERIAL_OT_fix_collection_hierarchy,
    
    MATERIAL_OT_restore_separation,
    MATERIAL_OT_separation_select_all,
    MATERIAL_OT_separation_toggle,
    MATERIAL_OT_scroll_separation,
    MATERIAL_OT_restore_separation_execute,
    MATERIAL_OT_restore_separation_confirm,
    
    MATERIAL_OT_clear_selected_history,
    MATERIAL_OT_clear_all_history,
    
    MATERIAL_OT_remove_materials_dialog,
    MATERIAL_OT_remove_all_materials,
    MATERIAL_OT_remove_unused_materials,
    
    MATERIAL_OT_clean_orphan_data,
    MATERIAL_OT_clean_empty_slots,
    MATERIAL_OT_clean_orphan_fast,
    
    MATERIAL_OT_remove_geometry_dialog,
    
    MATERIAL_OT_remove_node_groups_dialog,
    
    MATERIAL_OT_remove_collections_dialog,
]

classes = classes_property + classes_ui + classes_operators

def register():
    """Register all classes"""
    print("=== REGISTERING OPERATORS.PY ===")
    
    for cls in classes_property:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ Registered property class: {cls.__name__}")
        except Exception as e:
            print(f"❌ Error registering {cls.__name__}: {e}")
    
    for cls in classes_ui:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ Registered UI class: {cls.__name__}")
        except Exception as e:
            print(f"❌ Error registering UI class {cls.__name__}: {e}")
    
    for cls in classes_operators:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ Registered operator: {cls.__name__}")
        except Exception as e:
            print(f"❌ Error registering operator {cls.__name__}: {e}")
    
    print(f"✅ Total registered: {len(classes)} classes")
    print("================================")

def unregister():
    """Unregister all classes (in reverse order)"""
    print("=== UNREGISTERING OPERATORS.PY ===")
    
    for cls in reversed(classes_operators):
        try:
            bpy.utils.unregister_class(cls)
            print(f"✅ Unregistered operator: {cls.__name__}")
        except Exception as e:
            print(f"❌ Error unregistering {cls.__name__}: {e}")
    
    for cls in reversed(classes_ui):
        try:
            bpy.utils.unregister_class(cls)
            print(f"✅ Unregistered UI class: {cls.__name__}")
        except Exception as e:
            print(f"❌ Error unregistering UI class {cls.__name__}: {e}")
    
    for cls in reversed(classes_property):
        try:
            bpy.utils.unregister_class(cls)
            print(f"✅ Unregistered property class: {cls.__name__}")
        except Exception as e:
            print(f"❌ Error unregistering property class {cls.__name__}: {e}")
    
    print("===================================")

def diagnose_restoration_problem(entry):
    """Diagnosing problems with restoration"""
    print(f"\n🔍 COMPLETE DIAGNOSIS")
    print(f"{'='*60}")
    
    print(f"📄 Entry ID: {getattr(entry, 'deletion_id', 'N/A')}")
    print(f"📋 Entry Type: {getattr(entry, 'deletion_type', 'N/A')}")
    print(f"🔢 Count: {getattr(entry, 'count', 0)}")
    print(f"🏷️ Item Names: {getattr(entry, 'item_names', 'N/A')}")
    
    if entry.deletion_type == 'GEOMETRY':
        diagnose_geometry_nodes_problem(entry)
    elif entry.deletion_type == 'COLLECTION':
        diagnose_collections_problem(entry)  
    
    backup = getattr(entry, 'data_backup', '')
    if backup:
        try:
            data = json.loads(backup)
            print(f"📦 Backup Type: {data.get('type', 'Unknown')}")
            
            if data.get('type') == 'COLLECTIONS_WITH_HIERARCHY':
                print(f"🎯 Has complete hierarchy: {data.get('has_hierarchy', False)}")
                print(f"🎯 Has objects: {data.get('has_objects', False)}")
                
                collections = data.get("collections", [])
                hierarchy = data.get("hierarchy", [])
                print(f"📐 Collections in backup: {len(collections)}")
                print(f"📐 Hierarchical levels: {len(hierarchy)}")
                
                total_objects = sum(len(coll.get("objects", [])) for coll in collections)
                print(f"📍 Total objects in collections: {total_objects}")
            
            elif data.get('type') == 'GEOMETRY_WITH_EVERYTHING':
                print(f"🎯 Has modifier data: {data.get('has_modifier_data', False)}")
                
                objects = data.get("objects", [])
                print(f"📐 Objects in backup: {len(objects)}")
                
                geometry_nodes_count = 0
                for obj in objects:
                    for mod in obj.get("modifiers", []):
                        if mod.get("type") == 'NODES':
                            geometry_nodes_count += 1
                
                print(f"🔧 Geometry Nodes en backup: {geometry_nodes_count}")
        except Exception as e:
            print(f"❌ ERROR parsing backup: {e}")
    else:
        print("⚠️ No backup data available")
    
    print(f"{'='*60}\n")
