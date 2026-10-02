"""Generated, isolated UE Lab 012B. Never opens Tryfan or the Lab 012A project."""
import json
from pathlib import Path
import unreal
import lab012a_common as common

ASSETS = '/Game/Lab012B'


def config():
    project = Path(unreal.Paths.project_dir())
    if not (project/'RiffelhornLab012B.uproject').exists():
        raise RuntimeError('Refuse another renderer project')
    root = Path(json.loads((project/'lab012b-source.json').read_text())['output_root'])
    return root, json.loads((root/'lab012b-manifest.json').read_text())


def texture(name):
    root,manifest=config()
    result=common.asset(root/'textures'/(name+'.png'),name,ASSETS+'/Textures')
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    if result.blueprint_get_memory_size()==0:
        result=common.asset(root/'textures'/(name+'.png'),name,ASSETS+'/Textures',reimport=True)
    settings={'srgb':True,'compression_settings':unreal.TextureCompressionSettings.TC_EDITOR_ICON,
        'filter':unreal.TextureFilter.TF_TRILINEAR,'address_x':unreal.TextureAddress.TA_CLAMP,'address_y':unreal.TextureAddress.TA_CLAMP,
        'mip_gen_settings':unreal.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE,'lod_bias':0,'max_texture_size':0,'never_stream':True}
    if any(result.get_editor_property(k)!=v for k,v in settings.items()):result.set_editor_properties(settings)
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    size=result.blueprint_get_built_texture_size()
    if (round(size.x),round(size.y))!=tuple(manifest['textures']['dimensions']) or result.blueprint_get_memory_size()!=common.mip_bytes(2510):
        raise RuntimeError('Native decoded texture/mips not fully built: '+name)
    unreal.EditorAssetLibrary.save_loaded_asset(result)
    return result


def material(name,state):
    path=ASSETS+'/Materials/'+state+'/'+name
    rgb=texture(name) if state=='rgb' else None
    if unreal.EditorAssetLibrary.does_asset_exist(path):return unreal.EditorAssetLibrary.load_asset(path)
    result=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,ASSETS+'/Materials/'+state,unreal.Material,unreal.MaterialFactoryNew())
    result.set_editor_properties({'shading_model':unreal.MaterialShadingModel.MSM_UNLIT,'two_sided':False})
    if state=='rgb':
        colour=common.expression(result,unreal.MaterialExpressionTextureSampleParameter2D,parameter_name='ObservedRGB',texture=rgb,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR);output='RGB'
    else:
        colour=common.expression(result,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.5,.5,.5,1));output=''
    normal=common.expression(result,unreal.MaterialExpressionVertexNormalWS)
    direction=common.expression(result,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.4,-.3,.8660254,0))
    dot=common.expression(result,unreal.MaterialExpressionDotProduct);common.connect(normal,'',dot,'A');common.connect(direction,'',dot,'B')
    positive=common.expression(result,unreal.MaterialExpressionMax,const_b=0);common.connect(dot,'',positive,'A')
    factor=common.expression(result,unreal.MaterialExpressionMultiply,const_b=.35);common.connect(positive,'',factor,'A')
    offset=common.expression(result,unreal.MaterialExpressionAdd,const_b=.65);common.connect(factor,'',offset,'A')
    final=common.expression(result,unreal.MaterialExpressionMultiply);common.connect(colour,output,final,'A');common.connect(offset,'',final,'B')
    if not unreal.MaterialEditingLibrary.connect_material_property(final,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR):raise RuntimeError('Material connection failed')
    unreal.MaterialEditingLibrary.recompile_material(result);unreal.EditorAssetLibrary.save_loaded_asset(result)
    return result


def setup(kind):
    if kind not in ('dtm','dsm'):raise ValueError('Choose dtm or dsm')
    root,manifest=config()
    map_path=ASSETS+'/'+kind
    if unreal.EditorAssetLibrary.does_asset_exist(map_path):unreal.EditorLoadingAndSavingUtils.load_map(map_path)
    else:unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing={a.get_actor_label():a for a in actors.get_all_level_actors()}
    checks=[]
    for patch in manifest['geometry'][kind]['patches']:
        name=patch['name'];mesh=common.asset(root/'meshes'/kind/(name+'.glb'),name,ASSETS+'/Meshes/'+kind)
        if mesh.get_num_lods()!=1 or mesh.get_num_triangles(0)!=patch['triangles']:raise RuntimeError('Native topology changed')
        bounds=mesh.get_bounding_box();actual=[bounds.min.x,bounds.min.y,bounds.min.z,bounds.max.x,bounds.max.y,bounds.max.z]
        expected=[x[i]*100 for x in patch['bounds_local_m'] for i in (0,2,1)]
        if any(abs(a-b)>.1 for a,b in zip(actual,expected)):raise RuntimeError('Local axis/scale/height mismatch')
        nanite=mesh.get_editor_property('nanite_settings');nanite.set_editor_property('enabled',False);mesh.set_editor_property('nanite_settings',nanite)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        label='Lab012B_'+name;actor=existing.get(label) or actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector())
        actor.set_actor_label(label);actor.static_mesh_component.set_static_mesh(mesh);actor.static_mesh_component.set_material(0,material(name,'neutral'))
        checks.append({'name':name,'bounds_cm':actual,'triangles':mesh.get_num_triangles(0),'vertices':mesh.get_num_vertices(0),'lods':mesh.get_num_lods()})
    cam=existing.get('Lab012B_Camera') or actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector())
    cam.set_actor_label('Lab012B_Camera');cam.camera_component.set_editor_properties({'field_of_view':50,'aspect_ratio':1920/1080,'constrain_aspect_ratio':True})
    for command in ('r.EyeAdaptationQuality 0','r.MotionBlurQuality 0','r.SetNearClipPlane 10'):
        unreal.SystemLibrary.execute_console_command(world,command)
    view('overview')
    unreal.EditorLoadingAndSavingUtils.save_map(world,map_path)
    (root/f'unreal-setup-{kind}.json').write_text(json.dumps({'result':'PASS','kind':kind,'checks':checks,'attribution':'©swisstopo'},indent=2))
    return checks


def camera():
    return next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='Lab012B_Camera')


def view(name):
    _,manifest=config();v=manifest['views'][name];cam=camera()
    position=unreal.Vector(*[x*100 for x in v['position_m']]);target=unreal.Vector(*[x*100 for x in v['target_m']])
    cam.set_actor_location(position,False,True);cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position,target),False)
    return name


def camera_pose():
    cam=camera();p=cam.get_actor_location();r=cam.get_actor_rotation()
    return [p.x,p.y,p.z,r.pitch,r.yaw,r.roll,cam.camera_component.field_of_view]


def geometry_signature():
    result=[]
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label().startswith('Lab012B_tile_'):
            p=actor.get_actor_location();r=actor.get_actor_rotation();s=actor.get_actor_scale3d()
            result.append([actor.get_actor_label(),actor.static_mesh_component.static_mesh.get_path_name(),p.x,p.y,p.z,r.pitch,r.yaw,r.roll,s.x,s.y,s.z])
    return sorted(result)


def variant(state):
    if state not in ('neutral','rgb'):raise ValueError('Choose neutral or rgb')
    before=camera_pose();geometry=geometry_signature()
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label().startswith('Lab012B_tile_'):
            actor.static_mesh_component.set_material(0,material(actor.get_actor_label().replace('Lab012B_',''),state))
    if before!=camera_pose() or geometry!=geometry_signature():raise RuntimeError('Material state changed camera/geometry')
    unreal.AutomationLibrary.finish_loading_before_screenshot()


def capture(name):
    root,_=config();world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();cam=camera()
    actor=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.SceneCapture2D,cam.get_actor_location(),cam.get_actor_rotation())
    target=unreal.RenderingLibrary.create_render_target2d(world,1920,1080,format=unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB,auto_generate_mip_maps=False)
    actor.capture_component2d.set_editor_properties({'texture_target':target,'fov_angle':50,'capture_source':unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,'capture_every_frame':False,'capture_on_movement':False})
    unreal.AutomationLibrary.finish_loading_before_screenshot();actor.capture_component2d.capture_scene()
    folder=root/'captures/raw';folder.mkdir(parents=True,exist_ok=True)
    unreal.RenderingLibrary.export_render_target(world,target,str(folder),name+'.png');actor.destroy_actor()


def comparisons(kind,state):
    root,manifest=config();variant(state);records=[]
    for name in manifest['views']:
        view(name);capture(name+'-'+kind+'-'+state)
        records.append({'view':name,'kind':kind,'state':state,'camera_pose_cm_degrees':camera_pose(),'file':name+'-'+kind+'-'+state+'.png','attribution':'©swisstopo'})
    textures=[]
    if state=='rgb':
        for patch in manifest['geometry'][kind]['patches']:
            tex=unreal.EditorAssetLibrary.load_asset(ASSETS+'/Textures/'+patch['name']);size=tex.blueprint_get_built_texture_size()
            if (round(size.x),round(size.y))!=(2510,2510) or tex.blueprint_get_memory_size()!=common.mip_bytes(2510):raise RuntimeError('Incomplete native GPU image resource')
            textures.append({'tile':patch['name'],'dimensions':[round(size.x),round(size.y)],'gpu_bytes':tex.blueprint_get_memory_size(),'never_stream':tex.never_stream})
    (root/f'captures-{kind}-{state}.json').write_text(json.dumps({'captures':records,'textures':textures,'geometry_signature':geometry_signature(),'attribution':'©swisstopo'},indent=2))
    return records
