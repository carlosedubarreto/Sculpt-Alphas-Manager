# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENCE BLOCK #####

bl_info = {
    "name": "Textures Manager",
    "description": "Displays thumbnails of textures (by categories) for quicker assignment to brushes",
    "author": "Ryxx",
    "blender": (2, 81, 0),
    "version": (1, 0),
    "location": "(Sculpt, Vertex Paint, Texture Paint) Modes > Properties Editor > Active Tool tab > Texture Panel",
    "category": "Textures"
}

import bpy, os, sys, string, re
import bpy.utils.previews
from bpy.types import Operator, Menu, Panel, PropertyGroup, AddonPreferences, BlendData, Brush
from bpy.props import StringProperty, EnumProperty, BoolProperty, IntProperty
from bl_ui.properties_paint_common import brush_texture_settings
    
#--------------------------------------------------------------------------------------
# A D D O N   P R E F E R E N C E S
#--------------------------------------------------------------------------------------
    
class PreferencesTextureFilePaths(AddonPreferences):

    bl_idname = __name__

    sculpting_texture_directory: StringProperty(
        name="Sculpting Textures Directory",
        default="",        
        subtype='DIR_PATH',
        description='The default directory to search for sculpting textures'
    )
    
    vertex_paint_texture_directory: StringProperty(
        name="Vertex Paint Textures Directory",
        default="",        
        subtype='DIR_PATH',
        description='The default directory to search for vertex paint textures'
    )
    
    texture_paint_texture_directory: StringProperty(
        name="Texture Paint Textures Directory",
        default="",        
        subtype='DIR_PATH',
        description='The default directory to search for texture paint textures'
    )
        
    toggle_file_paths: BoolProperty(
        name="File Paths",
        default=False,        
        description='Set active section to File Paths'
    )
    
    show_labels: BoolProperty(
        name="Show Labels",
        default=True,        
        description='Show texture preview labels'
    )    
    
    preview_scale: IntProperty(
        name="Preview Scale",
        min=2,
        max=10,                
        default=8,        
        description='The scale of the texture UI preview'
    )                 
    
    def draw(self, context):
        layout = self.layout
        prefs = context.preferences

        row = layout.row(align=True)
        row.prop(self, "show_labels")         
        row.prop(self, "preview_scale")
                
        row = layout.row(align=True)                
        row.label(text="Set file paths in Preferences > File Paths > Data")
        row.prop(self, "toggle_file_paths", toggle=True)

        if self.toggle_file_paths:        
            context.preferences.active_section = 'FILE_PATHS'
            self.toggle_file_paths = False
                
#--------------------------------------------------------------------------------------
# G E N E R A L    F U N C T I O N A L I T I E S
#--------------------------------------------------------------------------------------

# TEXTURE FILE PATHS
def texture_file_paths(self, context):
    layout = self.layout
    
    preferences = context.preferences.addons[__name__].preferences

    col = self.layout.column()
    col.prop(preferences, "sculpting_texture_directory", text="Sculpting Textures")
    col.prop(preferences, "vertex_paint_texture_directory", text="Vertex Paint Textures")
    col.prop(preferences, "texture_paint_texture_directory", text="Texture Paint Textures")
    
# LIB PATH FUNCTION
def lib_path(self, context):
    mode = context.object.mode
    preferences = context.preferences.addons[__name__].preferences
            
    if mode == 'SCULPT':
        lib_path = preferences.sculpting_texture_directory
    elif mode == 'VERTEX_PAINT':
        lib_path = preferences.vertex_paint_texture_directory         
    elif mode == 'TEXTURE_PAINT':
        lib_path = preferences.texture_paint_texture_directory
                
    return lib_path

# LIB PATH FOLDER FUNCTION
def lib_path_folder(self, context):
    mode = context.object.mode
    
    if mode == 'SCULPT':
        lib_path_folder = 'sculpting_texture_directory'
    elif mode == 'VERTEX_PAINT':
        lib_path_folder = 'vertex_paint_texture_directory'         
    elif mode == 'TEXTURE_PAINT':
        lib_path_folder = 'texture_paint_texture_directory'
                
    return lib_path_folder

# BRUSH MODE FUNCTION
def brush_mode(self, context):
    mode = context.object.mode
    tool = context.tool_settings

    # Get brush by current mode            
    if mode == 'SCULPT':
        brush_mode = tool.sculpt.brush
    elif mode == 'VERTEX_PAINT':
        brush_mode = tool.vertex_paint.brush        
    elif mode == 'TEXTURE_PAINT':
        brush_mode = tool.image_paint.brush
                
    return brush_mode

# TEXTURE FOLDER CATEGORIES FUNCTION
def category_pointer(self, context):
    brush = brush_mode(self, context)
    
    category_pointer = brush.brush_texture.category
                        
    return category_pointer

# TEXTURE SUB FOLDER CATEGORIES FUNCTION
def sub_category_pointer(self, context):
    brush = brush_mode(self, context)
    
    sub_category_pointer = brush.brush_texture.sub_category
                        
    return sub_category_pointer

# TEXTURE SAME CATEGORY AND SUB FOLDER CATEGORY FUNCTION
def main_sub_category_pointer(self, context):
    brush = brush_mode(self, context)
    
    cat_subcat_same = False
    
    category_pointer = brush.brush_texture.category    
    sub_category_pointer = brush.brush_texture.sub_category

    # Check to see if the selected category and sub category is the same
    if sub_category_pointer == category_pointer:
        cat_subcat_same = True
    else:
        cat_subcat_same = False
                                                
    return cat_subcat_same

# SELECTED TEXTURE FUNCTION
def selected_texture(self, context):
    brush = brush_mode(self, context)
    
    selected_texture = brush.brush_texture.items_in_selected_category
               
    return selected_texture                       

# FIX LABELS FUNCTION
def fix_labels(self, context, current_labels):
    fix_labels = current_labels
   
    # Remove file extension
    remove_ext = fix_labels.split('.')[0]
    # Remove underscore
    under = remove_ext.replace("_", " ")
    # Separate capital words
    sep_by_upper = re.sub( r"([A-Z])", r" \1", under).split()
    join_sep_cap = " ".join(sep_by_upper)           
    # Capitalize all words
    cap_words = string.capwords(join_sep_cap)
    # Separate numbers from words
    sep_num = re.findall('\d+|\D+', cap_words)
    num_join = " ".join(sep_num).replace("  ", " ")
        
    fix_labels = num_join    
    
    
    return fix_labels

# SYNC PREVIEW WITH SELECTED IMAGE FUNCTION
def sync_image_preview(self, context):
    brush = brush_mode(self, context)   
    procedurals = preview_procedural_items(self, context)
    
    # TEXTURES
    # If using image_texture    
    if self.image_texture:
        selected_item_preview = brush.brush_texture.items_in_selected_category
        selected_item_image = brush.image_texture.image.name
        # Update the preview, if the selected image texture and preview is not the same                
        if selected_item_image != selected_item_preview:
            brush.brush_texture.items_in_selected_category = selected_item_image
                 
    # If using procedurals   
    if self.procedural_texture:
        selected_item_preview = brush.brush_texture.items_procedural_textures
        selected_item_image = brush.procedural_texture.name
        # Update the preview, if the selected procedural texture and preview is not the same                
        if selected_item_image != selected_item_preview and procedurals:
            brush.brush_texture.items_procedural_textures = selected_item_image     
            
#--------------------------------------------------------------------------------------
# F O L D E R    F U N C T I O N A L I T I E S
#--------------------------------------------------------------------------------------

# FOUND SUB CATEGORIES FUNCTION
def found_sub_categories(self, context):
    found_sub_categories = False
        
    # The selected category path                                
    path = (lib_path(self, context) + category_pointer(self, context) + "\\")              

    # See if selected category path is not empty
    if len(os.listdir(path)) != 0:
        for folder in os.listdir(path):
            # Check for folders in selected category
            if os.path.isdir(path + folder):                                    
                found_sub_categories = True
    else:        
        found_sub_categories = False
            
    return found_sub_categories
             
# TEXTURE CATEGORIES FOLDER ITEMS FUNCTION
def preview_folders_textures(self, context):
                
    list_of_category_folders = []
    categories = []       
    no_items_in_folder = [('NONE', 'None', 'None')]    
                    
    if not lib_path(self, context):
        return no_items_in_folder

    else:
        # Get items in the selected category               
        for folder in os.listdir(lib_path(self, context)):
            if os.path.isdir(lib_path(self, context) + folder):                
                list_of_category_folders.append(folder)

        # Append the categories and fix labels                              
        for name in list_of_category_folders:                                       
            cap_name = fix_labels(self, context, current_labels=name)
                                                
            categories.append((name.upper(), cap_name, ""))
                                             
    return categories


# TEXTURE CATEGORIES SUB FOLDER ITEMS FUNCTION
def preview_sub_folders_textures(self, context):
    category = category_pointer(self, context)                    
    
    folder_files = False
                       
    list_of_sub_category_folders = []
    sub_categories = []          
    no_items_in_folder = [('NONE', 'None', 'None')]    
                    
    if not lib_path(self, context):
        return no_items_in_folder
                  
    else:
        # The selected category path                                
        path = (lib_path(self, context) + category_pointer(self, context) + "\\")              

        # If selected category path is empty, return None 
        if len(os.listdir(path)) == 0:
            return no_items_in_folder
    
        for folder in os.listdir(path):
            # Check for no folders in selected category
            if not os.path.isdir(path + folder):                           
                folder_files = False
            # Check for both folders and files in selected category                
            elif os.path.isfile(path + folder) or os.path.isdir(path + folder):                           
                folder_files = True              
                
        # Add the selected category to sub categories and make it default, if both sub categories and files found or no folders found                            
        if not folder_files or folder_files:                  
            #list_of_sub_category_folders.append(category)                                
            list_of_sub_category_folders.append('None')
                        
        # Get folders in the selected category                                        
        for folder in os.listdir(path):
            if os.path.isdir(path + folder):                
                list_of_sub_category_folders.append(folder)

        # Append the sub categories and fix labels                                 
        for name in list_of_sub_category_folders:                
            cap_name = fix_labels(self, context, current_labels=name)
                                            
            sub_categories.append((name.upper(), cap_name, ""))        
            
                                             
    return sub_categories
                        
#--------------------------------------------------------------------------------------
# P R E V I E W    F U N C T I O N A L I T I E S
#--------------------------------------------------------------------------------------
            
# TEXTURE ITEMS PREVIEW FUNCTION
def preview_category_items(self, context):
    brush = brush_mode(self, context)        
    enum_items = []
    # Valid file extensions   
    extensions = ('.jpeg', '.jpg', '.png', '.tif', '.tiff', '.psd')
    
    if context is None:        
        return enum_items

    # Adds a NONE item
    enum_items.append(('NONE', 'None', 'None', 'TEXTURE', 0))
        
    is_sub_folders = preview_sub_folders_textures(self, context)
    same_categories = main_sub_category_pointer(self, context)
    sub_category = brush.brush_texture.sub_category
    
    # Path if there's sub categories and the selected category is not the same as the selected sub category    
    if is_sub_folders is not None and not same_categories and sub_category != 'NONE':        
        directory = os.path.join(lib_path(self, context), category_pointer(self, context), sub_category_pointer(self, context))                                  
    else:
        directory = os.path.join(lib_path(self, context), category_pointer(self, context))  

    if "textures" not in preview_collections_textures:
        pcoll = bpy.utils.previews.new()       
        pcoll.my_previews_dir = ""
        pcoll.my_previews = ()
        preview_collections_textures["textures"] = pcoll             
    else:             
        pcoll = preview_collections_textures["textures"]
        
    # New previews if path is different, needed for poll to show correct preview textures    
    if directory != pcoll.my_previews_dir:
        bpy.utils.previews.remove(pcoll)
        pcoll = bpy.utils.previews.new()       
        pcoll.my_previews_dir = ""
        pcoll.my_previews = ()
        preview_collections_textures["textures"] = pcoll
    # If nothing is changed, show current previews                
    else: 
        return pcoll.my_previews

    if directory == pcoll.my_previews_dir:
        return pcoll.my_previews
                        
    if directory and os.path.exists(directory):
        image_paths = []
                                
        for fn in os.listdir(directory):
            if fn.endswith(extensions):
                image_paths.append(fn)

        for i, name in enumerate(image_paths):
            filepath = os.path.join(directory, name)
         
            icon = pcoll.get(name)
                       
            if not icon:
                thumb = pcoll.load(name, filepath, 'IMAGE')                                                                                                                   
            else:
                thumb = pcoll[name]                
                                                                        
            cap_name = fix_labels(self, context, current_labels=name)
            
            # Since we added a NONE item, we have to add 1 to the identifier
            identifier = i + 1               
            enum_items.append((name, cap_name, name, thumb.icon_id, identifier))

                                                        
    pcoll.my_previews = enum_items
    pcoll.my_previews_dir = directory
    return pcoll.my_previews
    
# PREVIEW PROCEDURAL TEXTURE ITEMS FUNCTION
def preview_procedural_items(self, context):
    
    enum_items = []   

    if context is None:
        return enum_items

    # Adds a NONE item
    enum_items.append(('NONE', 'None', 'None', 'TEXTURE', 0))
    
    if "procedural" not in preview_collections_textures:
        ptcoll = bpy.utils.previews.new()        
        ptcoll.my_previews = ()
        preview_collections_textures["procedural"] = ptcoll
    else:    
        ptcoll = preview_collections_textures["procedural"]

    # Gets all textures that the type is not image
    tex_type = [t for t in bpy.data.textures if t.type != 'IMAGE' and t.type != 'NONE']
                                      
    for i, tex in enumerate(tex_type):
        
        # Since we added a NONE item, we have to add 1 to the identifier
        identifier = i + 1                                       
        enum_items.append((tex.name, tex.name, tex.name, tex.preview.icon_id, identifier))
                              
    ptcoll.my_previews = enum_items                     
    return ptcoll.my_previews

#--------------------------------------------------------------------------------------
# T E X T U R E    F U N C T I O N A L I T I E S
#--------------------------------------------------------------------------------------

# ASSIGN BRUSH TEXTURE
def assign_texture(self, context):
    brush = brush_mode(self, context)

    previousTexture = None
    textureImage = None
    
    selected_item = brush.brush_texture.items_in_selected_category

    selected_procedural = brush.brush_texture.items_procedural_textures
            
    is_sub_folders = preview_sub_folders_textures(self, context)
    is_folders = preview_folders_textures(self, context)
        
    category = brush.brush_texture.category
    sub_category = brush.brush_texture.sub_category
    
    previews = preview_category_items(self, context)

    #none_preview = previews[0][0]
    
    # Check for previews
    if previews:                              
        # Path if using sub categories
        if is_sub_folders and category != sub_category and sub_category != 'NONE':                
            selected_texture_path = os.path.join(lib_path(self, context), category_pointer(self, context), sub_category_pointer(self, context), selected_texture(self, context))                    
        # Path if using categories        
        else:
            selected_texture_path = os.path.join(lib_path(self, context), category_pointer(self, context), selected_texture(self, context))

       
        texname = os.path.splitext(selected_texture(self, context))[0]
        texname_no_extension = fix_labels(self, context, current_labels=texname)
                        
        use_procedural = brush.use_procedural_textures
        procedurals = preview_procedural_items(self, context)


        # If using image_texture                                                                                                 
        if not use_procedural:
            # Get previous texture
            previousTexture = brush.image_texture
                       
            if selected_item != 'NONE':                                                                
                # If the selected texture is not found and there's previews, create and assign new texture                       
                if texname_no_extension not in bpy.data.textures:        
                    bpy.data.images.load(selected_texture_path, check_existing=True)
                    image_to_texture = bpy.data.textures.new(texname_no_extension, 'IMAGE')
                    image_to_texture.image = bpy.data.images[selected_texture(self, context)]            
                    brush.texture = bpy.data.textures[texname_no_extension]
                    brush.image_texture = bpy.data.textures[texname_no_extension]
                # If the selected texture is already found            
                else:                                                                                                                                                                                          
                # If image_texture is not None, previews found and category != sub category, update texture and image_texture             
                    if brush.image_texture is not None:                    
                        brush.texture = bpy.data.textures[texname_no_extension]
                        brush.image_texture = bpy.data.textures[texname_no_extension]                                                             
                        
            # Remove texture, if None is selected                       
            else:
                brush.texture = None
                brush.image_texture = None
                                                                                               
        # If using procedurals                        
        else:
            if selected_procedural != 'NONE':
                #if brush.procedural_texture is not None and not procedurals:
                    #brush.texture = bpy.data.textures[brush.procedural_texture.name]        
                    #brush.procedural_texture = bpy.data.textures[brush.procedural_texture.name]                                       
                if brush.procedural_texture is not None and procedurals:                           
                    brush.texture = bpy.data.textures[selected_procedural]        
                    brush.procedural_texture = bpy.data.textures[selected_procedural]                    
                elif brush.procedural_texture is None and procedurals:                            
                    brush.texture = bpy.data.textures[selected_procedural]        
                    brush.procedural_texture = bpy.data.textures[selected_procedural]                        

            # Remove texture, if None is selected                       
            else:
                brush.texture = None
                brush.procedural_texture = None

    # Unlink texture and image
    if previousTexture:
        # Unlink previous texture, if no users        
        if brush.image_texture != previousTexture and previousTexture.users == 0:
            textureImage = bpy.data.textures[previousTexture.name].image
            bpy.data.textures.remove(bpy.data.textures[previousTexture.name], do_unlink=True, do_id_user=True, do_ui_user=True)
        # Unlink texture image, if no users        
        if textureImage is not None and textureImage.users == 0:
            bpy.data.images.remove(bpy.data.images[textureImage.name], do_unlink=True, do_id_user=True, do_ui_user=True)                

#--------------------------------------------------------------------------------------
# P R O P E R T Y    P O L L S
#--------------------------------------------------------------------------------------

# PROCEDURAL TEXTURE TYPE POLL
def procedural_items(self, object):                            
    return object.type != 'IMAGE' and object.type != 'NONE'

# ONLY PREVIEW TEXTURES POLL
def category_items(self, object):
                                    
    preview_textures = []
        
    preview_items = preview_collections_textures["textures"]
        
    for item in preview_items:
        preview_textures.append(item)       
                                                            
    return object.type == 'IMAGE' and object.users >= 1 and object.image.name in preview_textures
                                        
#--------------------------------------------------------------------------------------
# T E X T U R E   R E D R A W    R E G I S T E R
#--------------------------------------------------------------------------------------

# VARIABLES

#166 TEXTURE                                       
#763 IMAGE_RGB
#2 ERROR
#693 FILE_FOLDER    
showLabels = None
iconTemplateScale = None    
iconScale = None    
iconScaleLabel = None
iconTexture = 166
iconFolder = 693
alignLayout = True
iconLive = False
propToggle = True
                                                
# REDRAW NEW TEXTURE SETTINGS ON REGISTER           
def texture_register_draw(self, context):
    preferences = context.preferences.addons[__name__].preferences

    showLabels = preferences.show_labels
    iconTemplateScale = preferences.preview_scale 
    iconScale = (iconTemplateScale + 3)   
    iconScaleLabel = (iconScale - 4)
                                       
    settings = self.paint_settings(context)
    brush = settings.brush
    mode = context.object.mode
    tool = context.tool_settings          
    texture = brush.texture
    procedurals = preview_procedural_items(self, context)
    is_sub_folders = preview_sub_folders_textures(self, context)
    path_folder = lib_path_folder(self, context)
    items = preview_category_items(self, context)                
    path = lib_path(self, context)
                                   
    layout = self.layout                         

    brush = brush_mode(self, context)
    
    category_pointer = brush.brush_texture

    category = brush.brush_texture.category
    sub_category = brush.brush_texture.sub_category

    
    if is_sub_folders and sub_category != 'NONE': 
        texture_category = brush.brush_texture.sub_category                               
    else: 
        texture_category = brush.brush_texture.category  


    # Text and icon, if using / not using library preview
    if not brush.use_library_preview:
        previewText = 'Library Preview'
        previewIcon = 'ASSET_MANAGER'                
    else:
        previewText = 'Default Preview'
        previewIcon = 'PREFERENCES'

    # Text and icon, if using / not using procedural textures            
    if not brush.use_procedural_textures:
        proceduralText = 'Procedural'
        proceduralIcon = 'TEXTURE'
        
    else:
        proceduralText = 'Images'
        proceduralIcon = 'IMAGE_RGB'


    # Library preview setting       
    row = layout.row(align=alignLayout)
    row.alignment = 'RIGHT'

    row.label(text=previewText)    
    row.prop(brush, "use_library_preview", text='', icon=previewIcon, toggle=propToggle)

    # Settings if using library preview
    if brush.use_library_preview:
                      
        row = layout.row(align=alignLayout)
        row.alignment = 'RIGHT'

        # Procedural texture setting                        
        row.label(text=proceduralText)    
        row.prop(brush, "use_procedural_textures", text='', icon=proceduralIcon, toggle=propToggle)

        col = layout.column(align=False)            
        row = col.row(align=alignLayout)

        # Settings if not using procedural textures
        if not brush.use_procedural_textures:
            # Settings if path found                        
            if path:
                sub_cats_found = found_sub_categories(self, context)                
                                
                # Texture categories settings                
                row.label(text='Categories:')                                      
                row.prop(category_pointer, "category", text='')
                row.operator("texture_category.open", text='', icon='FILE_FOLDER')

                # If sub folders found and items found in selected category                           
                if is_sub_folders is not None and items and sub_cats_found:                        
                    # Texture sub categories settings                                                        
                    row = col.row(align=alignLayout)
                    row.label(text='Sub Categories:')                          
                    row.prop(category_pointer, "sub_category", text='')

                    # Check to see if open sub category folder operator setting can be enabled                    
                    row_enabled = row.row(align=alignLayout)                                         
                    if sub_category == 'NONE':
                        row_enabled.enabled = False
                    elif sub_category == category:
                        row_enabled.enabled = False
                    else:
                        row_enabled.enabled = True                                               
                                                                                                                                               
                    row_enabled.operator("texture_sub_category.open", text='', icon='FILE_FOLDER')
                    
            # Path setting, if path not found                                            
            else:
                row.prop(preferences, path_folder, text='')

            col = layout.column(align=alignLayout)

            # Preview setting, if items found in selected category                                                    
            if len(items) >= 2:                                       
                col.template_icon_view(category_pointer, "items_in_selected_category", show_labels=showLabels, scale=iconTemplateScale)                                                     
            else:
                # Preview setting, if only NONE item found                                                                
                if path and len(items) == 1:                     
                    col.template_icon_view(category_pointer, "items_in_selected_category", show_labels=showLabels, scale=iconTemplateScale)
                # Only a icon, if no path found                                                                         
                else:
                    row = col.row(align=alignLayout)                        
                    row.alignment = 'CENTER'             
                    row.label(text='No library folder selected !')
                    col.template_icon(icon_value=iconFolder, scale=iconScaleLabel)

            # Texture pointer property and brush settings, if assigned a texture           
            if texture:
                row = col.row(align=alignLayout)
                row.alignment = 'LEFT'                             
                row.label(text=brush.image_texture.name, icon='TEXTURE')                
                                                                                                                       
                col = layout.column()             
                brush_texture_settings(col, brush, context.sculpt_object)            

        # Settings if using procedural textures
        else:
            col = layout.column(align=alignLayout)
            # Icon and new precedural texture, if no procedural textures found                        
            if brush.use_procedural_textures and not procedurals: 
                col.template_icon(icon_value=iconTexture, scale=iconScaleLabel)
                col.template_ID(brush, "procedural_texture", new="procedural_texture.new", live_icon=iconLive)
                
            # Preview and procedural pointer property settings, if procedural textures found                                                    
            else:        
                col.template_icon_view(category_pointer, "items_procedural_textures", show_labels=showLabels, scale=iconTemplateScale)
                col.template_ID(brush, "procedural_texture", new="procedural_texture.new", live_icon=iconLive)

            # Brush settings                                
            col = layout.column()
            brush_texture_settings(col, brush, context.sculpt_object)        

    # Default settings, if not using library preview
    else:
        col = layout.column()

        col.template_ID_preview(brush, "texture", new="texture.new", rows=3, cols=8)

        brush_texture_settings(col, brush, context.sculpt_object)

#--------------------------------------------------------------------------------------
# T E X T U R E   R E D R A W    U N R E G I S T E R
#--------------------------------------------------------------------------------------

# REDRAW OLD TEXTURE SETTINGS ON UNREGISTER
def texture_unregister_draw(self, context):    
    layout = self.layout

    settings = self.paint_settings(context)
    brush = settings.brush

    col = layout.column()

    col.template_ID_preview(brush, "texture", new="texture.new", rows=3, cols=8)

    brush_texture_settings(col, brush, context.sculpt_object)
                        
#--------------------------------------------------------------------------------------
# O P E R A T O R S
#--------------------------------------------------------------------------------------

# PROCEDURAL TEXTURE
class ProceduralTexture(Operator):
    bl_idname = "procedural_texture.new"
    bl_label = "New Procedural Texture"
    bl_description = "Add a new procedural Texture"    
    bl_options = {'INTERNAL'}
    
    def execute(self, context):        
        brush = brush_mode(self, context)
                     
        tex = bpy.data.textures.new(name='Procedural Texture', type='BLEND')

        brush.texture = tex        
        brush.procedural_texture = tex 
        
        return {'FINISHED'}
    
# OPEN CATEGORY FOLDER
class OpenCategoryFolder(Operator):
    bl_idname = "texture_category.open"
    bl_label = "Open Category Folder"
    bl_description = "Open the selected category's folder"
    bl_options = {'REGISTER'}

    def execute(self, context):              
                   
        if sys.platform == "win32":
            os.startfile(os.path.join(lib_path(self, context), category_pointer(self, context)))
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, os.path.join(lib_path(self, context), category_pointer(self, context))])
                    
        return {'FINISHED'}

# OPEN SUB CATEGORY FOLDER
class OpenSubCategoryFolder(Operator):
    bl_idname = "texture_sub_category.open"
    bl_label = "Open Sub Category Folder"
    bl_description = "Open the selected sub category's folder"
    bl_options = {'REGISTER'}

    def execute(self, context):              
        
        brush = brush_mode(self, context)
        
        #category = brush.brush_texture.category
        sub_category = brush.brush_texture.sub_category
                                   
        if sys.platform == "win32":
            if sub_category == 'NONE':
                os.startfile(os.path.join(lib_path(self, context), category_pointer(self, context)))
            else:
                os.startfile(os.path.join(lib_path(self, context), category_pointer(self, context), sub_category_pointer(self, context)))
                                
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            if sub_category == 'NONE':            
                subprocess.call([opener, os.path.join(lib_path(self, context), category_pointer(self, context))])
            else:            
                subprocess.call([opener, os.path.join(lib_path(self, context), category_pointer(self, context), sub_category_pointer(self, context))])

                    
        return {'FINISHED'}
        
#--------------------------------------------------------------------------------------
# P R O P E R T Y    G R O U P    S E T T I N G S 
#--------------------------------------------------------------------------------------

# This fixes a issue, where the previous folder had more images than the current folder and preview is blank  
def update_single_item_preview(self, context):
    brush = brush_mode(self, context)
                    
    if self.sub_category:
        items = preview_category_items(self, context)
        # Checks for the NONE item and at least one other item                              
        if len(items) >= 2:
            # Assign the preview to the second item
            brush.brush_texture.items_in_selected_category = items[1][0]
        # Assign the preview to NONE, if only NONE found                       
        elif len(items) == 1:
            brush.brush_texture.items_in_selected_category = items[0][0]

    assign_texture(self, context)
    
def update_single_folder_preview(self, context):
    brush = brush_mode(self, context)         
                
    if self.category:
        sub_folders = preview_sub_folders_textures(self, context)
        # Checks for the NONE folder and at least one other folder       
        if len(sub_folders) >= 2:
            # Assign the sub folder to the second item                  
            brush.brush_texture.sub_category = sub_folders[1][0]        
        # Assign the sub folder to NONE, if only one sub folder found      
        elif len(sub_folders) == 1:                   
            brush.brush_texture.sub_category = sub_folders[0][0]
            
    assign_texture(self, context)
                
class BrushTexture(PropertyGroup):

    # TEXTURES AND MASK FOLDER CATEGORIES               
    category: EnumProperty(
                name='Categories', 
                items=preview_folders_textures,
                update=update_single_folder_preview,                                                               
                )                

    # TEXTURES AND MASK SUB FOLDER CATEGORIES               
    sub_category: EnumProperty(
                name='Sub Categories', 
                items=preview_sub_folders_textures,
                update=update_single_item_preview,                                                                           
                )                
                                
    # TEXTURES AND MASK    
    items_in_selected_category: EnumProperty(
                name='Items in the selected category', 
                items=preview_category_items,
                #items=[('BOB', 'BOB', 'BOB')],                  
                update=assign_texture,                             
                )                
                
    # PROCEDURAL TEXTURES AND MASK
    items_procedural_textures: EnumProperty(
                name='Procedural textures', 
                items=preview_procedural_items, 
                update=assign_texture,
                )                
                                                                                                                                                                                                     
#--------------------------------------------------------------------------------------
# R E G I S T R Y
#--------------------------------------------------------------------------------------
                
classes = (
    PreferencesTextureFilePaths,
    ProceduralTexture,    
    OpenCategoryFolder,
    OpenSubCategoryFolder,          
    BrushTexture,                   
)


preview_collections_textures = {}


def register():  
            
    bpy.types.USERPREF_PT_file_paths_data.append(texture_file_paths)       
    bpy.types.VIEW3D_PT_tools_brush_texture.draw = texture_register_draw
                    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)        

                        
    Brush.brush_texture = bpy.props.PointerProperty(
                            type=BrushTexture,
                            )
    Brush.image_texture = bpy.props.PointerProperty(
                            type=bpy.types.Texture,                             
                            poll=category_items, 
                            update=sync_image_preview,                            
                            )                           
    Brush.procedural_texture = bpy.props.PointerProperty(
                            type=bpy.types.Texture, 
                            poll=procedural_items, 
                            update=sync_image_preview,
                            )                        
    Brush.use_procedural_textures = bpy.props.BoolProperty(
                            name='', 
                            description='Toggle between using procedural or image textures', 
                            default=False,
                            #update=unlinkTextureData,
                            update=assign_texture,                                                                     
                            )                                                                   
    Brush.use_library_preview = bpy.props.BoolProperty(
                            name='', 
                            description='Toggle between library or default preview', 
                            default=True,                                                                                 
                            )
   
def unregister():
                
    bpy.types.USERPREF_PT_file_paths_data.remove(texture_file_paths)        
    bpy.types.VIEW3D_PT_tools_brush_texture.draw = texture_unregister_draw    
                              
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    
    del Brush.brush_texture    
    del Brush.image_texture        
    del Brush.procedural_texture              
    del Brush.use_procedural_textures    
    del Brush.use_library_preview               

                
    for pcoll in preview_collections_textures.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections_textures.clear()
    
        
if __name__ == "__main__":
    register()
  