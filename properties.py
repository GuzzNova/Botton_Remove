import bpy
from .icons import get_botton_icon_id, get_botton_history_icon_id, get_botton_node_groups_icon_id, get_botton_materials_icon_id
from bpy.props import CollectionProperty, IntProperty, EnumProperty, StringProperty, BoolProperty, FloatProperty, FloatVectorProperty

class DeletionHistoryItem(bpy.types.PropertyGroup):
    """Property group for tracking deletion history"""
    deletion_id: IntProperty(
        name="ID",
        description="Unique ID for this deletion",
        default=0
    )
    
    deletion_type: EnumProperty(
        name="Type",
        description="Type of deletion",
        items=[
            ('MATERIAL', "Material", "Material deletion"),
            ('GEOMETRY', "Geometry", "Geometry object deletion"),
            ('NODE_GROUP', "Node Group", "Node group deletion"),
            ('COLLECTION', "Collection", "Collection deletion"),
            ('EMPTY_SLOT', "Empty Slot", "Empty slot cleanup"),
            ('ORPHAN_DATA', "Orphan Data", "Orphan data cleanup"),
            ('ALL_MATERIALS', "All Materials", "All materials deletion"),
            ('UNUSED_MATERIALS', "Unused Materials", "Unused materials deletion"),
        ]
    )
    
    has_collection_hierarchy: BoolProperty(
        name="Has Collection Hierarchy",
        description="Whether this entry has collection hierarchy data",
        default=False
    )

    source: bpy.props.EnumProperty(
        name="Source",
        description="How this deletion was triggered",
        items=[
            ('DIALOG', "Dialog", "Deleted from the Tavo Eliminator dialog"),
            ('HOTKEY', "Hotkey (X)", "Deleted using the X key (Delete to History)"),
            ('OTHER', "Other", "Other method"),
        ],
        default='DIALOG'
    )
    
    collection_hierarchy_data: StringProperty(
        name="Collection Hierarchy Data",
        description="JSON data with complete collection hierarchy",
        default=""
    )
    
    item_names: StringProperty(
        name="Item Names",
        description="Comma-separated list of item names that were deleted",
        default=""
    )
    
    count: IntProperty(
        name="Count",
        description="Number of items deleted",
        default=1
    )
    
    timestamp: FloatProperty(
        name="Timestamp",
        description="Unix timestamp when deletion occurred",
        default=0.0
    )
    
    data_backup: StringProperty(
        name="Data Backup",
        description="JSON backup of deleted data",
        default=""
    )
    
    material_assignments: StringProperty(
        name="Material Assignments",
        description="JSON data with detailed material-to-object slot assignments",
        default=""
    )
    
    has_material_assignments: BoolProperty(
        name="Has Material Assignments",
        description="Whether this entry has detailed material assignment data",
        default=False
    )

    can_restore: BoolProperty(
        name="Can Restore",
        description="Whether this deletion can be restored",
        default=True
    )

    has_position_data: BoolProperty(
        name="Has Position Data",
        description="Whether this entry has position data for restoration",
        default=False
    )
    
    position_data: StringProperty(
        name="Position Data",
        description="JSON data with positions of deleted items",
        default=""
    )

class MaterialSelectionItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Material Name")
    selected: BoolProperty(name="Selected", default=False)
    users: IntProperty(name="Users", default=0)

class GeometrySelectionItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Object Name")
    selected: BoolProperty(name="Selected", default=False)
    type: StringProperty(name="Type", default="MESH")
    hide_viewport: BoolProperty(name="Hide Viewport", default=False)
    hide_viewport_temp: BoolProperty(name="Hide Viewport Temp", default=False)
    hide_render: BoolProperty(name="Hide Render", default=False)
    users: IntProperty(name="Users", default=0)

class NodeGroupSelectionItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Node Group Name")
    selected: BoolProperty(name="Selected", default=False)
    type: StringProperty(name="Type", default="SHADER")
    users: IntProperty(name="Users", default=0)

class CollectionSelectionItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Collection Name")
    selected: BoolProperty(name="Selected", default=False)
    object_count: IntProperty(name="Object Count", default=0)
    child_collection_count: IntProperty(name="Child Collections", default=0)
    is_linked: BoolProperty(name="Is Linked", default=False)
    users: IntProperty(name="Users", default=0)


class MATERIAL_PT_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    show_outliner_button: BoolProperty(
        name="Show Outliner Button",
        description="Show material remove button in outliner header (FORCED LEFT SIDE)",
        default=True
    )
    
    show_history_button: BoolProperty(
        name="Show History Button",
        description="Show history/undo button next to the trash button",
        default=False
    )
    
    show_3dview_menu: BoolProperty(
        name="Show 3D View Menu",
        description="Show Botton Remove menu in 3D View header",
        default=False
    )
    
    show_properties_panel: BoolProperty(
        name="Show Properties Panel",
        description="Show Botton Remove panel in multiple locations",
        default=False
    )
    
    hotkey_min_move_threshold: IntProperty(
        name="Min Mouse Move",
        description="Minimum mouse movement (pixels) to activate selection",
        default=20,
        min=5,
        max=100,
        step=1
    )
        
    tpanel_location: EnumProperty(
        name="T-Panel Location",
        description="Where to show Botton Remove in 3D View T-Panel",
        items=[
            ('ITEM', "Item Tab", "Show in Item tab of T-panel"),
            ('TOOLS', "Tools Tab", "Show in Tools tab of T-panel"),
            ('BOTH', "Both", "Show in both Item and Tools tabs"),
        ],
        default='BOTH'
    )

    show_node_editor_button: BoolProperty(
        name="Show Node Editor Button",
        description="Show Botton Remove button in Node Editor header",
        default=True
    )

    show_3dview_tpanel: BoolProperty(
        name="Show 3D View T-Panel",
        description="Show Botton Remove menu in 3D View T-Panel (press T)",
        default=False
    )
    
    panel_position: EnumProperty(
        name="Main Panel Location",
        description="Where to show the main Botton Remove panel",
        items=[
            ('SCENE', "Scene Properties", "Properties Editor → Scene tab"),
            ('TOOL', "Tool Properties", "Properties Editor → Tool tab"),
            ('OBJECT', "Object Properties", "Properties Editor → Object tab"),
            ('VIEW3D', "3D View Sidebar", "3D View → Sidebar → Tool tab"),
            ('MULTI', "Multiple Locations", "Show in all recommended locations"),
        ],
        default='MULTI'
    )

    enable_hotkey_x: BoolProperty(
        name="Enable Hotkey X",
        description="Enable circular menu when pressing X key",
        default=False
    )
    
    hotkey_menu_type: EnumProperty(
        name="Menu Type",
        description="Type of menu to show with hotkey",
        items=[
            ('CIRCULAR', "Circular Menu", "Show a circular menu with mouse selection"),
            ('PIE', "Pie Menu", "Show a pie menu (classic Blender pie menu)"),
        ],
        default='CIRCULAR'
    )
    
    hotkey_radius: FloatProperty(
        name="Menu Radius",
        description="Radius of the circular menu",
        default=120.0,
        min=100.0,
        max=300.0,
        step=10
    )
    
    hotkey_pie_position: EnumProperty(
        name="Pie Menu Position",
        description="Where to show the pie menu",
        items=[
            ('CURSOR', "At Cursor", "Show pie menu at cursor position"),
            ('CENTER', "Screen Center", "Show pie menu at screen center"),
        ],
        default='CURSOR'
    )
    
    hotkey_font_size: IntProperty(
        name="Font Size",
        description="Font size for the circular menu",
        default=12,
        min=8,
        max=24,
        step=1
    )
    
    hotkey_animation_speed: FloatProperty(
        name="Animation Speed",
        description="Animation speed of the circular menu",
        default=0.2,
        min=0.05,
        max=1.0,
        step=0.05
    )
    
    hotkey_opacity: FloatProperty(
        name="Menu Opacity",
        description="Opacity of the circular menu",
        default=0.95,
        min=0.5,
        max=1.0,
        step=0.05
    )
    
    confirm_before_remove: BoolProperty(
        name="Confirm Before Removal",
        description="Show confirmation dialog before removing materials",
        default=True
    )
    
    backup_before_remove: BoolProperty(
        name="Backup Before Removal",
        description="Save backup file before removing materials (recommended)",
        default=False
    )
    
    enable_deletion_history: BoolProperty(
        name="Enable Deletion History",
        description="Keep track of deleted items for recovery",
        default=True
    )
    
    max_history_actions: IntProperty(
        name="Max History Actions",
        description="Maximum number of deletion actions to remember",
        default=50,
        min=0,
        max=1000
    )
    
    auto_clear_history_on_exit: BoolProperty(
        name="Clear History on Exit",
        description="Automatically clear history when Blender is closed",
        default=False
    )
    
    auto_clear_history_minutes: IntProperty(
        name="Auto-clear History (minutes)",
        description="Automatically clear history after X minutes (0 = disabled)",
        default=0,
        min=0,
        max=1440
    )
    
    save_history_with_file: BoolProperty(
        name="Save History with File",
        description="Save deletion history when saving the .blend file",
        default=False
    )
    
    allow_unlimited_restore: BoolProperty(
        name="Allow Unlimited Restore",
        description="Allow restoring the same history entry multiple times (creates copies with _restoun suffix)",
        default=False
    )
    
    remove_entry_after_restore: BoolProperty(
        name="Remove Entry After Restore",
        description="Remove the history entry after a successful restore (disable for unlimited restores)",
        default=False
    )
    
    delete_to_history: BoolProperty(
        name="Delete to History",
        description="When enabled, deleting objects with X/Delete key sends them to Botton Remove history instead of permanent deletion. Works as a smart recycle bin",
        default=False
    )
    
    delete_to_history_types: EnumProperty(
        name="Capture Types",
        description="Which element types to capture when using Delete/X key",
        items=[
            ('OBJECTS', "Objects Only", "Only capture object deletions to history"),
            ('ALL', "All Types", "Capture objects, materials, collections, etc."),
        ],
        default='OBJECTS'
    )

    delete_history_method: EnumProperty(
        name="History Method for Geometry",
        description="How to handle geometry when using Delete-to-History",
        items=[
            ('HIDE', "Move to hidden collection (fast, exact restore)", "Objects are moved to a hidden collection – no backup needed, restore is instant"),
            ('BACKUP', "Backup full mesh (slow, heavy)", "Save full mesh data in history – allows restore even if objects are deleted, but can be slow and increase file size"),
        ],
        default='HIDE'
    )
    
    permanent_delete: BoolProperty(
        name="Permanent Delete Mode",
        description="When enabled, deletions bypass history completely - items are removed permanently without backup. Use with caution!",
        default=False
    )

    hotkey_color_materials: FloatVectorProperty(
        name="Materials Color",
        subtype='COLOR',
        default=(0.90, 0.30, 0.30),
        min=0.0, max=1.0,
        description="Color for Materials item"
    )

    hotkey_color_geometry: FloatVectorProperty(
        name="Geometry Color",
        subtype='COLOR',
        default=(0.25, 0.65, 0.88),
        min=0.0, max=1.0
    )

    hotkey_color_nodes: FloatVectorProperty(
        name="Nodes Color",
        subtype='COLOR',
        default=(0.40, 0.82, 0.35),
        min=0.0, max=1.0
    )

    hotkey_color_collections: FloatVectorProperty(
        name="Collections Color",
        subtype='COLOR',
        default=(0.95, 0.75, 0.15),
        min=0.0, max=1.0
    )

    hotkey_color_history: FloatVectorProperty(
        name="History Color",
        subtype='COLOR',
        default=(0.70, 0.40, 0.90),
        min=0.0, max=1.0
    )

    hotkey_color_cleanh: FloatVectorProperty(
        name="Clean History Color",
        subtype='COLOR',
        default=(0.55, 0.55, 0.60),
        min=0.0, max=1.0
    )

    hotkey_color_deltohist: FloatVectorProperty(
        name="Delete→History Color",
        subtype='COLOR',
        default=(0.20, 0.70, 0.30),
        min=0.0, max=1.0
    )

    hotkey_color_perm: FloatVectorProperty(
        name="Permanent Delete Color",
        subtype='COLOR',
        default=(1.00, 0.30, 0.30),
        min=0.0, max=1.0
    )

    hotkey_show_labels: BoolProperty(
        name="Show Labels",
        default=True
    )

    hotkey_show_keys: BoolProperty(
        name="Show Keys",
        default=True
    )

    hotkey_label_font_size: IntProperty(
        name="Label Font Size",
        default=12, min=6, max=30
    )

    hotkey_key_font_size: IntProperty(
        name="Key Font Size",
        default=16, min=8, max=40
    )

    hotkey_icon_size: FloatProperty(
        name="Icon Size",
        default=28.0, min=10.0, max=60.0
    )

    hotkey_label_distance: FloatProperty(
        name="Label Distance",
        default=28.0, min=10.0, max=100.0,
        description="Distance of labels from the center of each node"
    )

    hotkey_animation_curve: EnumProperty(
        name="Animation Curve",
        items=[
            ('LINEAR', "Linear", ""),
            ('EASE_OUT', "Ease Out", ""),
            ('EASE_IN_OUT', "Ease In Out", ""),
            ('BOUNCE', "Bounce", ""),
        ],
        default='EASE_OUT'
    )

    hotkey_enable_exit_animation: BoolProperty(
        name="Enable Exit Animation",
        description="Enable smooth exit animation when closing the menu. If you experience lag, disable this.",
        default=True
    )

    hotkey_exit_animation_speed: FloatProperty(
        name="Exit Animation Speed",
        description="Speed of the exit animation",
        default=0.15,
        min=0.05,
        max=1.0,
        step=0.05
    )

    hotkey_exit_animation_curve: EnumProperty(
        name="Exit Animation Curve",
        items=[
            ('LINEAR', "Linear", ""),
            ('EASE_OUT', "Ease Out", ""),
            ('EASE_IN_OUT', "Ease In Out", ""),
            ('BOUNCE', "Bounce", ""),
        ],
        default='EASE_OUT'
    )

    hotkey_selection_mode: EnumProperty(
        name="Selection Mode",
        items=[
            ('DISTANCE', "Mouse Distance", "Select by moving mouse towards item"),
            ('ANGLE', "Mouse Angle", "Select by pointing in direction (radial)"),
        ],
        default='DISTANCE'
    )

    hotkey_angle_tolerance: FloatProperty(
        name="Angle Tolerance",
        default=0.48, min=0.1, max=0.5,
        description="Fraction of slice width that triggers selection (0.5 = full slice)"
    )

    hotkey_min_select_distance: FloatProperty(
        name="Min Select Distance",
        default=30.0, min=10.0, max=200.0,
        description="Minimum distance from center to start selecting (DISTANCE mode)"
    )

    hotkey_max_select_distance: FloatProperty(
        name="Max Select Distance",
        default=80.0, min=30.0, max=300.0,
        description="Maximum distance from center to allow selection (DISTANCE mode)"
    )

    hotkey_background_opacity: FloatProperty(
        name="Background Opacity",
        default=0.75, min=0.0, max=1.0, step=0.05
    )

    hotkey_ring_thickness: FloatProperty(
        name="Ring Thickness",
        default=32.0, min=10.0, max=80.0
    )

    hotkey_center_size: FloatProperty(
        name="Center Size",
        default=14.0, min=5.0, max=40.0
    )

    hotkey_center_color: FloatVectorProperty(
        name="Center Color",
        subtype='COLOR',
        default=(0.18, 0.18, 0.22),
        min=0.0, max=1.0
    )

    hotkey_center_ring_color: FloatVectorProperty(
        name="Center Ring Color",
        subtype='COLOR',
        default=(0.45, 0.45, 0.50),
        min=0.0, max=1.0
    )

    hotkey_selection_highlight_color: FloatVectorProperty(
        name="Selection Highlight Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0, max=1.0
    )

    hotkey_selection_highlight_alpha: FloatProperty(
        name="Selection Highlight Alpha",
        default=0.18, min=0.0, max=1.0, step=0.05
    )

    hotkey_show_status_badges: BoolProperty(
        name="Show Status Badges",
        default=True
    )
    
    hotkey_status_badge_font_size: IntProperty(
        name="Badge Font Size",
        default=9, min=6, max=20
    )

    # ============================================================================
    # DRAW METHOD 
    # ============================================================================
    def draw(self, context):
        layout = self.layout
        
        # Info box
        box = layout.box()
        box.label(text="Botton Remove v1.0.0", icon_value=get_botton_icon_id()) 
        col = box.column(align=True)
        col.scale_y = 0.7
        col.label(text="Complete cleanup tool with deletion history")
        col.label(text="Now available in multiple locations for easy access")
        
        layout.separator()
        
        # ==================== UI SETTINGS ====================
        box = layout.box()
        box.label(text="UI Locations", icon='PREFERENCES')
        
        col = box.column(align=True)
        
        col.label(text="Header Buttons:", icon='WINDOW')
        col.prop(self, "show_outliner_button", text="Show Outliner Button", icon_value=get_botton_materials_icon_id())
        col.prop(self, "show_history_button", text="Show History Button", icon_value=get_botton_history_icon_id())
        
        col.separator()
        col.label(text="Other Headers:", icon='MENU_PANEL')
        col.prop(self, "show_node_editor_button", text="Show Node Editor Button", icon_value=get_botton_node_groups_icon_id())
        col.prop(self, "show_3dview_menu", text="Show 3D View Menu", icon_value=get_botton_icon_id()) 
        col.prop(self, "show_3dview_tpanel", text="Show 3D View T-Panel", icon_value=get_botton_icon_id()) 

        all_locations_box = box.box()
        all_locations_box.label(text="All Available UI Locations:", icon='VIEW3D')
        all_col = all_locations_box.column(align=True)
        all_col.scale_y = 0.7
        all_col.label(text="1. Outliner Header (left side)")
        all_col.label(text="2. 3D View Header menu (trash icon)")
        all_col.label(text="3. Properties Editor → Scene tab")
        all_col.label(text="4. Properties Editor → Tool tab")
        all_col.label(text="5. Properties Editor → Object tab")
        all_col.label(text="6. Node Editor Header")

        layout.separator()
        
        # ==================== HOTKEY SETTINGS ====================
        box = layout.box()
        box.label(text="Hotkey Settings", icon='KEY_HLT')

        col = box.column(align=True)
        col.prop(self, "enable_hotkey_x")

        if self.enable_hotkey_x:
            msg_box = col.box()
            msg_box.alert = True
            msg_col = msg_box.column(align=True)
            msg_col.scale_y = 0.7
            msg_col.label(text="This is the free version; it does not have access to keyboard shortcuts.", icon='INFO')
            msg_col.label(text="However, enjoy everything else and explore, and most importantly, have fun!", icon='INFO')

        layout.separator()
        
        box = layout.box()
        box.label(text="Safety Settings", icon='ERROR')

        col = box.column(align=True)
        col.prop(self, "confirm_before_remove")
        col.prop(self, "backup_before_remove")
        col.prop(self, "enable_deletion_history")
        
        if self.enable_deletion_history:
            sub_col = col.column(align=True)
            sub_col.prop(self, "max_history_actions")
            sub_col.prop(self, "auto_clear_history_on_exit")
            sub_col.prop(self, "auto_clear_history_minutes")
            sub_col.prop(self, "save_history_with_file")

        row = box.row()
        row.scale_y = 0.8
        row.label(text="Tip: Always save your file before removing data", icon='INFO')
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Restore Settings", icon='LOOP_BACK')
        
        col = box.column(align=True)
        col.prop(self, "allow_unlimited_restore", icon='FILE_REFRESH')
        
        if self.allow_unlimited_restore:
            info_box = col.box()
            info_col = info_box.column(align=True)
            info_col.scale_y = 0.7
            info_col.label(text="Unlimited restore allows you to restore the same", icon='INFO')
            info_col.label(text="entry multiple times. Duplicates get _restoun suffix.")
        
        col.prop(self, "remove_entry_after_restore", icon='CANCEL')
        
        if self.remove_entry_after_restore:
            warning_row = col.row()
            warning_row.alert = True
            warning_row.label(text="History entries will be removed after restore!", icon='ERROR')
        
        sub_box = col.box()
        sub_box.label(text="Delete to History (Smart Recycle Bin)", icon_value=get_botton_history_icon_id())
        
        col2 = sub_box.column(align=True)
        row = col2.row()
        row.prop(self, "delete_to_history", icon='IMPORT')
        
        if self.delete_to_history:
            sub_sub_box = col2.box()
            sub_sub_box.prop(self, "delete_to_history_types")
            
            info_col = sub_sub_box.column(align=True)
            info_col.scale_y = 0.7
            info_col.label(text="When active, pressing X/Delete on objects sends", icon='INFO')
            info_col.label(text="them to Botton Remove history for later recovery.")
            info_col.label(text="This overrides Blender's default delete behavior.")
            
            hotkey_info = sub_sub_box.column(align=True)
            hotkey_info.scale_y = 0.7
            hotkey_info.label(text="Hotkey preview: [X] / [Del] -> History", icon='KEY_HLT')
        
        sub_box = col.box()
        sub_box.label(text="Permanent Delete", icon='CANCEL')
        
        col2 = sub_box.column(align=True)
        row = col2.row()
        row.prop(self, "permanent_delete", icon='ERROR')
        
        if self.permanent_delete:
            warning_box = col2.box()
            warning_box.alert = True
            warning_col = warning_box.column(align=True)
            warning_col.scale_y = 0.7
            warning_col.label(text="WARNING: Permanent delete is active!", icon='ERROR')
            warning_col.label(text="Items will be deleted WITHOUT backup.")
            warning_col.label(text="No history entry will be created.")
            warning_col.label(text="This action CANNOT be undone!")
                        
            hotkey_info = col2.column(align=True)
            hotkey_info.scale_y = 0.7
            hotkey_info.separator() 
            hotkey_info.label(text="Hotkey preview: Shift+X shows [PERM] badge", icon='KEY_HLT')


def register():
    """Register all property groups and addon preferences"""
    bpy.utils.register_class(DeletionHistoryItem)
    bpy.utils.register_class(MaterialSelectionItem)
    bpy.utils.register_class(GeometrySelectionItem)
    bpy.utils.register_class(NodeGroupSelectionItem)
    bpy.utils.register_class(CollectionSelectionItem)
    
    bpy.utils.register_class(MATERIAL_PT_preferences)
    
    if not hasattr(bpy.types.Scene, 'deletion_history'):
        bpy.types.Scene.deletion_history = CollectionProperty(type=DeletionHistoryItem)
    if not hasattr(bpy.types.Scene, 'deletion_history_selection'):
        bpy.types.Scene.deletion_history_selection = StringProperty(
            name="Deletion History Selection",
            description="Comma-separated IDs of selected history entries for restore",
            default=""
        )
    if not hasattr(bpy.types.Scene, 'deletion_separation_entry_id'):
        bpy.types.Scene.deletion_separation_entry_id = IntProperty(
            name="Separation Entry ID",
            description="History entry ID for separation dialog",
            default=-1
        )
    if not hasattr(bpy.types.Scene, 'deletion_separation_selection'):
        bpy.types.Scene.deletion_separation_selection = StringProperty(
            name="Separation Selection",
            description="Comma-separated indices of items to restore in separation dialog",
            default=""
        )
    
    print("✓ Botton Remove properties registered")

def unregister():
    """Unregister all property groups and addon preferences"""
    if hasattr(bpy.types.Scene, 'deletion_separation_selection'):
        del bpy.types.Scene.deletion_separation_selection
    if hasattr(bpy.types.Scene, 'deletion_separation_entry_id'):
        del bpy.types.Scene.deletion_separation_entry_id
    if hasattr(bpy.types.Scene, 'deletion_history_selection'):
        del bpy.types.Scene.deletion_history_selection
    if hasattr(bpy.types.Scene, 'deletion_history'):
        del bpy.types.Scene.deletion_history
    
    bpy.utils.unregister_class(MATERIAL_PT_preferences)
    bpy.utils.unregister_class(CollectionSelectionItem)
    bpy.utils.unregister_class(NodeGroupSelectionItem)
    bpy.utils.unregister_class(GeometrySelectionItem)
    bpy.utils.unregister_class(MaterialSelectionItem)
    bpy.utils.unregister_class(DeletionHistoryItem)
    
    print("✓ Botton Remove properties unregistered")