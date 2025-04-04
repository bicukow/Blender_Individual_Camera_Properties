import bpy
from re import split
from bpy.props import (FloatProperty, IntProperty, BoolProperty, StringProperty, CollectionProperty, PointerProperty)
from bpy.types import (Operator, PropertyGroup, World)  
from bpy.app.handlers import persistent  

# ======================================================
#                       GLOBALS
# ======================================================

props_list = [
    ('render.resolution_x',          bpy.props.IntProperty(default=1024)),
    ('render.resolution_y',          bpy.props.IntProperty(default=1024)),
    ('render.resolution_percentage', bpy.props.IntProperty(default=100)),
    #
    ('render.use_border',            bpy.props.BoolProperty(default=0)),
    ('render.use_crop_to_border',    bpy.props.BoolProperty(default=0)),
    # 
    ('render.border_max_x',          bpy.props.FloatProperty(default=1.0)),
    ('render.border_max_y',          bpy.props.FloatProperty(default=1.0)),
    ('render.border_min_x',          bpy.props.FloatProperty(default=0.0)),
    ('render.border_min_y',          bpy.props.FloatProperty(default=0.0)),
    #
    ('view_settings.view_transform', bpy.props.StringProperty(default='Filmic')),
    ('view_settings.look',           bpy.props.StringProperty(default='None')),
    ('view_settings.exposure',       bpy.props.FloatProperty (default=0)),
    ('view_settings.gamma',          bpy.props.FloatProperty (default=1)),
    #
    ('cycles.use_adaptive_sampling', bpy.props.BoolProperty  (default=False)),
    ('cycles.samples',               bpy.props.IntProperty   (default=4096)),
    ('cycles.time_limit',            bpy.props.FloatProperty (default=60.0)),
    ('cycles.use_denoising',         bpy.props.BoolProperty  (default=False)),
    ('cycles.denoiser',              bpy.props.StringProperty(default='OPTIX')),
    ('cycles.denoising_input_passes',bpy.props.StringProperty(default='RGB_ALBEDO_NORMAL')),
    ]
    
stray_props_list = [('world',        bpy.props.PointerProperty(type = World, name = 'world')),
                    ]

props_list_new = [i[0].replace('.','__') for i in props_list]
props_attributes = [split(r'\.', i[0]) for i in props_list]
props_zip = list(zip([i[0] for i in props_list], props_list_new, props_attributes))
# ======================================================
#                      CLASSES
# ======================================================
    
class Cam_render_props_PG(PropertyGroup):
    __annotations__ = {i[0].replace('.','__'): i[1] for i in props_list + stray_props_list}
    
# ======================================================
#                       FUCNS
# ======================================================
def check_camera_type(func):
    '''decorator: pass function if active camera is object'''
    def wrapper(*args, **kwargs):
        if bpy.context.scene.camera.type == 'CAMERA': 
            return func(*args)
        else: 
            pass        
    return wrapper
# ======================================================
#              MSGBUS properties callback
# ======================================================

@check_camera_type
def store_props_in_camera(x,y, prnt): 
    '''lambda func for msgbus'''
    print(y, prnt)
    setattr(bpy.context.scene.camera.data.Cam_render_props, x, bpy.context.scene.path_resolve(y))
    return None

@persistent
def msgbus_subscribe_handler(scene, context):
    for i in props_zip:
        '''dynamically subscribe properties from the list using lambda func'''
        bpy.msgbus.subscribe_rna(
            key = bpy.context.scene.path_resolve(i[0], False),
            owner = bpy.types.Scene,
            args = (),
            notify = lambda x=i[1], y=i[0]: store_props_in_camera(x,y,'prop was updated'),
            )

    for i in stray_props_list:
        '''dynamically subscribe properties from the list using lambda func'''
        bpy.msgbus.subscribe_rna(
            key = (bpy.types.Scene, i[0]),
            owner = bpy.types.Scene,
            args = (),
            notify = lambda x=i[0], y=i[0]: store_props_in_camera(x,y,'prop was updated'),
            )
            
# ======================================================
#                Active Camera Handler
# ======================================================
@check_camera_type
def set_cam_render_props(props_zip):
    '''set render parameters from props stored in camera'''
    for i in props_zip:
        setattr(getattr(bpy.context.scene, i[2][0]),      i[2][1],    getattr(getattr(bpy.context.scene.camera.data, 'Cam_render_props'), i[1]))
#       setattr(getattr(bpy.context.scene, 'render'), 'resolution_x', getattr(getattr(bpy.context.scene.camera.data, 'Cam_render_props'), 'render__resolution_x'))
    for i in stray_props_list:
        setattr(bpy.context.scene, i[0], getattr(getattr(bpy.context.scene.camera.data, 'Cam_render_props'), i[0]))

@persistent
def Cam_change_handler(scene, context):            
    if not "cam" in scene.keys():
        #print('Active camera was NOT changed')
        pass
    elif scene["cam"] != scene.camera: 
        print('Active camera was changed:', scene.camera.name)   
        scene["cam"] = scene.camera  
        set_cam_render_props(props_zip)

@persistent
def intialize_handler(scene, context):
    bpy.context.scene['cam'] = bpy.context.scene.camera # variable to compare for camera change detection handler
    set_cam_render_props(props_zip)
     
# ======================================================
#                      REGISTER
# ======================================================
classes = [Cam_render_props_PG]

def register(): 
    # classes
    for cls in classes: bpy.utils.register_class(cls)
    # msgbus
    bpy.types.Camera.Cam_render_props = bpy.props.PointerProperty(type = Cam_render_props_PG, description = '')
    # handler
    bpy.app.handlers.load_post.append(msgbus_subscribe_handler)
    bpy.app.handlers.depsgraph_update_post.append(Cam_change_handler)
    bpy.app.handlers.load_post.append(intialize_handler)
    # set props on intializing addon
#    bpy.context.scene['cam'] = bpy.context.scene.camera # variable to compare for camera change detection handler
#    set_cam_render_props(props_zip)

def unregister(): 
    # classes
    for cls in classes: bpy.utils.unregister_class(cls)
    # handler
    bpy.app.handlers.load_post.remove(intialize_handler)
    bpy.app.handlers.depsgraph_update_post.remove(Cam_change_handler)
    bpy.app.handlers.load_post.remove(msgbus_subscribe_handler)
    # msgbus
    del bpy.types.Camera.Cam_render_props

if __name__ == "__main__": register()
