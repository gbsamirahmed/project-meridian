"""Isolated local evaluation renderer; never opens the Tryfan project/map."""
import json
from pathlib import Path
import unreal

ASSETS='/Game/Lab012A'
VARIANTS=('neutral','rgb25','rgb125','rgb5')


def config():
    root=Path(json.loads((Path(unreal.Paths.project_dir())/'lab012a-source.json').read_text())['output_root'])
    return root,json.loads((root/'lab012a-manifest.json').read_text())


def asset(path,name,destination,reimport=False):
    full=destination+'/'+name
    if unreal.EditorAssetLibrary.does_asset_exist(full) and not reimport:
        existing=unreal.EditorAssetLibrary.load_asset(full)
        if Path(path).suffix!='.glb' or unreal.EditorAssetLibrary.get_metadata_tag(existing,'Lab012A.ImportPolicy')=='native-full-uv-v1': return existing
        reimport=True
    task=unreal.AssetImportTask();task.set_editor_properties({'filename':str(path),'destination_path':destination,
        'destination_name':name,'automated':True,'replace_existing':reimport,'save':True})
    if Path(path).suffix=='.glb':
        pipeline=unreal.InterchangeGenericAssetsPipeline()
        pipeline.mesh_pipeline.set_editor_properties({'build_nanite':False,'collision':False,'generate_lightmap_u_vs':False})
        pipeline.common_meshes_properties.set_editor_properties({'recompute_normals':False,'recompute_tangents':False,'use_full_precision_u_vs':True})
        override=unreal.InterchangePipelineStackOverride();override.add_pipeline(pipeline)
        task.set_editor_property('options',override)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    result=unreal.EditorAssetLibrary.load_asset(full)
    if result is None:
        candidates=[unreal.EditorAssetLibrary.load_asset(p) for p in task.imported_object_paths]
        result=next((x for x in candidates if isinstance(x,(unreal.StaticMesh,unreal.Texture2D))),None)
    if result is None: raise RuntimeError('Import failed: '+str(path))
    if Path(path).suffix=='.glb': unreal.EditorAssetLibrary.set_metadata_tag(result,'Lab012A.ImportPolicy','native-full-uv-v1')
    return result


def expression(material,kind,**properties):
    node=unreal.MaterialEditingLibrary.create_material_expression(material,kind)
    node.set_editor_properties(properties);return node


def connect(source,output,target,input_name):
    if not unreal.MaterialEditingLibrary.connect_material_expressions(source,output,target,input_name): raise RuntimeError('Material connection failed')


def mip_bytes(size):
    total=0
    while size:
        total+=size*size*4;size//=2
    return total


def native_texture(name,variant):
    root,_=config();source=root/'textures'/variant/(name+'.png');destination=ASSETS+'/Textures/'+variant
    texture=asset(source,name,destination)
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    if texture.blueprint_get_memory_size()==0:
        texture=asset(source,name,destination,reimport=True)
    properties={'srgb':True,'compression_settings':unreal.TextureCompressionSettings.TC_EDITOR_ICON,
        'filter':unreal.TextureFilter.TF_TRILINEAR,'address_x':unreal.TextureAddress.TA_CLAMP,'address_y':unreal.TextureAddress.TA_CLAMP,
        'mip_gen_settings':unreal.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE,'lod_bias':0,'max_texture_size':0,'never_stream':True}
    if any(texture.get_editor_property(k)!=value for k,value in properties.items()): texture.set_editor_properties(properties)
    # Platform data is rebuilt asynchronously after property edits.
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    size={'rgb25':502,'rgb125':1004,'rgb5':2510}[variant]
    built=texture.blueprint_get_built_texture_size()
    if (round(built.x),round(built.y))!=(size,size) or texture.blueprint_get_memory_size()!=mip_bytes(size):
        raise RuntimeError('Incomplete native BGRA texture/mip chain: '+name)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    return texture


def material(name,variant):
    root,_=config();destination=ASSETS+'/Materials/'+variant;path=destination+'/'+name
    texture=native_texture(name,variant) if variant!='neutral' else None
    if unreal.EditorAssetLibrary.does_asset_exist(path): return unreal.EditorAssetLibrary.load_asset(path)
    m=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,destination,unreal.Material,unreal.MaterialFactoryNew())
    m.set_editor_properties({'shading_model':unreal.MaterialShadingModel.MSM_UNLIT,'two_sided':False})
    if variant=='neutral':
        colour=expression(m,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.5,.5,.5,1)); output=''
    else:
        colour=expression(m,unreal.MaterialExpressionTextureSampleParameter2D,parameter_name='NativeRGB',texture=texture,
                          sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR);output='RGB'
    normal=expression(m,unreal.MaterialExpressionVertexNormalWS)
    direction=expression(m,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.4,-.3,.8660254,0))
    dot=expression(m,unreal.MaterialExpressionDotProduct);connect(normal,'',dot,'A');connect(direction,'',dot,'B')
    clamp=expression(m,unreal.MaterialExpressionMax,const_b=0);connect(dot,'',clamp,'A')
    multiplier=expression(m,unreal.MaterialExpressionMultiply,const_b=.35);connect(clamp,'',multiplier,'A')
    addition=expression(m,unreal.MaterialExpressionAdd,const_b=.65);connect(multiplier,'',addition,'A')
    final=expression(m,unreal.MaterialExpressionMultiply);connect(colour,output,final,'A');connect(addition,'',final,'B')
    if not unreal.MaterialEditingLibrary.connect_material_property(final,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR): raise RuntimeError('Emissive connection failed')
    unreal.MaterialEditingLibrary.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def setup(limit=None,reimport_meshes=False):
    root,manifest=config()
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    # This is a generated empty Lab project; refuse to populate another world.
    if 'Tryfan' in world.get_path_name(): raise RuntimeError('Lab 012A must not modify Tryfan')
    if unreal.EditorAssetLibrary.does_asset_exist(ASSETS+'/Lab012A'):
        unreal.EditorLoadingAndSavingUtils.load_map(ASSETS+'/Lab012A')
    else:
        unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing={a.get_actor_label():a for a in actors.get_all_level_actors()}
    subsystem=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    patches=manifest['geometry']['patches'][:limit] if limit else manifest['geometry']['patches']
    observations=[]
    for p in patches:
        mesh=asset(root/'meshes'/(p['name']+'.glb'),p['name'],ASSETS+'/Meshes',reimport=reimport_meshes)
        if not isinstance(mesh,unreal.StaticMesh): raise RuntimeError('Expected static DSM mesh')
        if subsystem is not None:  # Static mesh editor subsystem is absent in commandlets.
            settings=subsystem.get_lod_build_settings(mesh,0)
            settings.set_editor_properties({'recompute_normals':False,'recompute_tangents':False,'generate_lightmap_u_vs':False,'use_full_precision_u_vs':True})
            subsystem.set_lod_build_settings(mesh,0,settings)
        if mesh.get_num_lods()!=1: raise RuntimeError('Unexpected geometry LOD simplification')
        if mesh.get_num_triangles(0)!=p['triangles']: raise RuntimeError('Imported triangle count differs from native DSM')
        nanite=mesh.get_editor_property('nanite_settings');nanite.set_editor_property('enabled',False);mesh.set_editor_property('nanite_settings',nanite)
        box=mesh.get_bounding_box()
        expected_min=[p['bounds_local_m'][0][i]*100 for i in (0,2,1)]
        expected_max=[p['bounds_local_m'][1][i]*100 for i in (0,2,1)]
        actual_min=[box.min.x,box.min.y,box.min.z];actual_max=[box.max.x,box.max.y,box.max.z]
        if any(abs(a-b)>.1 for a,b in zip(actual_min+actual_max,expected_min+expected_max)): raise RuntimeError('glTF axes/scale changed')
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        label='Lab012A_'+p['name']
        actor=existing.get(label) or actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector())
        actor.set_actor_label(label);actor.static_mesh_component.set_static_mesh(mesh)
        actor.static_mesh_component.set_material(0,material(p['name'],'neutral'))
        observations.append({'name':p['name'],'bounds_cm':[actual_min,actual_max],'triangles':mesh.get_num_triangles(0),
                             'vertices':mesh.get_num_vertices(0),'lods':mesh.get_num_lods()})
    camera=existing.get('Lab012A_Camera') or actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector())
    camera.set_actor_label('Lab012A_Camera');camera.camera_component.set_editor_properties({'field_of_view':50,'aspect_ratio':1920/1080,'constrain_aspect_ratio':True})
    unreal.SystemLibrary.execute_console_command(world,'r.EyeAdaptationQuality 0')
    unreal.SystemLibrary.execute_console_command(world,'r.Streaming.PoolSize 512')
    unreal.SystemLibrary.execute_console_command(world,'r.MotionBlurQuality 0')
    report={'result':'PASS','patches_imported':len(observations),'mesh_observations':observations,'geometry_modified_by_variant':False}
    (root/'unreal-setup-validation.json').write_text(json.dumps(report,indent=2))
    view('overview')
    # Only this newly generated Lab map is saved; no preserved map is touched.
    unreal.EditorLoadingAndSavingUtils.save_map(world,ASSETS+'/Lab012A')
    return report


def camera():
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    return next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='Lab012A_Camera')


def view(name):
    _,manifest=config();v=manifest['views'][name];actor=camera()
    position=unreal.Vector(*[x*100 for x in v['position_m']]);target=unreal.Vector(*[x*100 for x in v['target_m']])
    actor.set_actor_location(position,False,True)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position,target),False)
    return name


def camera_pose():
    actor=camera();p=actor.get_actor_location();r=actor.get_actor_rotation();s=actor.get_actor_scale3d()
    return (p.x,p.y,p.z,r.pitch,r.yaw,r.roll,s.x,s.y,s.z,actor.camera_component.field_of_view)


def geometry_signature():
    result=[]
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label().startswith('Lab012A_tile_'):
            p=actor.get_actor_location();r=actor.get_actor_rotation();s=actor.get_actor_scale3d()
            result.append((actor.get_actor_label(),actor.static_mesh_component.static_mesh.get_path_name(),
                           p.x,p.y,p.z,r.pitch,r.yaw,r.roll,s.x,s.y,s.z))
    return sorted(result)


def variant(name):
    if name not in VARIANTS: raise ValueError('Choose neutral, rgb25, rgb125 or rgb5')
    before=camera_pose()
    geometry_before=geometry_signature()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith('Lab012A_tile_'):
            tile=actor.get_actor_label().replace('Lab012A_','')
            actor.static_mesh_component.set_material(0,material(tile,name))
    if camera_pose()!=before: raise RuntimeError('Variant changed camera coordinates')
    if geometry_signature()!=geometry_before: raise RuntimeError('Variant changed DSM meshes/transforms')
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    return name


def capture(name):
    root,_=config();world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();cam=camera()
    actor=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.SceneCapture2D,cam.get_actor_location(),cam.get_actor_rotation())
    target=unreal.RenderingLibrary.create_render_target2d(world,1920,1080,format=unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB,auto_generate_mip_maps=False)
    actor.capture_component2d.set_editor_properties({'texture_target':target,'fov_angle':50,'capture_source':unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,
                                                   'capture_every_frame':False,'capture_on_movement':False})
    unreal.AutomationLibrary.finish_loading_before_screenshot();actor.capture_component2d.capture_scene()
    folder=root/'captures';folder.mkdir(exist_ok=True)
    unreal.RenderingLibrary.export_render_target(world,target,str(folder),name+'.png')
    actor.destroy_actor()


def comparisons(states=VARIANTS,output_file='comparison-captures.json'):
    root,manifest=config();records=[]
    for v in manifest['views']:
        view(v)
        for state in states:
            variant(state);capture(v+'-'+state);records.append({'view':v,'variant':state,'output':v+'-'+state+'.png','camera_pose_cm_degrees':camera_pose()})
    textures=[]
    for state in (s for s in states if s!='neutral'):
        for patch in manifest['geometry']['patches']:
            texture=unreal.EditorAssetLibrary.load_asset(ASSETS+'/Textures/'+state+'/'+patch['name'])
            size=texture.blueprint_get_built_texture_size()
            expected=manifest['textures']['dimensions_with_apron'][state]
            if (round(size.x),round(size.y))!=tuple(expected): raise RuntimeError('Built GPU texture lost native resolution')
            if texture.blueprint_get_memory_size()!=mip_bytes(expected[0]): raise RuntimeError('Missing native mip resource')
            textures.append({'variant':state,'tile':patch['name'],'built_dimensions':[round(size.x),round(size.y)],
                             'gpu_bytes':texture.blueprint_get_memory_size(),'never_stream':texture.never_stream})
    (root/output_file).write_text(json.dumps({'captures':records,'textures':textures,'geometry_signature':geometry_signature()},indent=2))
    return records
