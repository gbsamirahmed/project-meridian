"""Illumination-only adapter in a physical copy of the frozen 012B scene."""
import json
import hashlib
import time
from pathlib import Path
import unreal
import lab012a_common as common

KEEP = []  # Keep transient depth targets/material instances alive through captures.


def config():
    project = Path(unreal.Paths.project_dir())
    if not (project/'RiffelhornLab012F.uproject').is_file(): raise RuntimeError('Refuse another project')
    root = Path(json.loads((project/'lab012f-source.json').read_text(encoding='utf-8'))['output_root'])
    return root, json.loads((root/'lab012f-inputs.json').read_text(encoding='utf-8'))


def actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def tiles():
    return sorted((a for a in actors().get_all_level_actors() if a.get_actor_label().startswith('Lab012B_tile_')),
                  key=lambda a: a.get_actor_label())


def camera():
    return next(a for a in actors().get_all_level_actors() if a.get_actor_label() == 'Lab012B_Camera')


def pose():
    a = camera(); p = a.get_actor_location(); r = a.get_actor_rotation()
    return [p.x, p.y, p.z, r.pitch, r.yaw, r.roll, a.camera_component.field_of_view]


def signature():
    answer = []
    for a in tiles():
        p = a.get_actor_location(); r = a.get_actor_rotation(); s = a.get_actor_scale3d()
        mesh = a.static_mesh_component.static_mesh
        answer.append([a.get_actor_label(), mesh.get_path_name(), p.x, p.y, p.z, r.pitch, r.yaw, r.roll,
                       s.x, s.y, s.z, mesh.get_num_triangles(0), mesh.get_num_vertices(0), mesh.get_num_lods()])
    return answer


def world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def view(name):
    _, m = config(); v = m['views'][name]; a = camera()
    p = unreal.Vector(*[x*100 for x in v['position_m']]); t = unreal.Vector(*[x*100 for x in v['target_m']])
    a.set_actor_location(p, False, True); a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(p, t), False)


def capture(folder, name):
    cam = camera(); a = actors().spawn_actor_from_class(unreal.SceneCapture2D, cam.get_actor_location(), cam.get_actor_rotation())
    rt = unreal.RenderingLibrary.create_render_target2d(world(), 1920, 1080,
        format=unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB, auto_generate_mip_maps=False)
    a.capture_component2d.set_editor_properties({'texture_target': rt, 'fov_angle': 50,
        'capture_source': unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,
        'capture_every_frame': False, 'capture_on_movement': False})
    unreal.AutomationLibrary.finish_loading_before_screenshot(); a.capture_component2d.capture_scene()
    unreal.RenderingLibrary.export_render_target(world(), rt, str(folder), name+'.png')
    a.destroy_actor()


def master(state, shadow):
    name = 'M_'+state+('_shadow' if shadow else '_directional')
    destination = '/Game/Lab012F/Materials'
    full = destination+'/'+name
    if unreal.EditorAssetLibrary.does_asset_exist(full): return unreal.EditorAssetLibrary.load_asset(full)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, destination, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_properties({'shading_model': unreal.MaterialShadingModel.MSM_UNLIT, 'two_sided': False})
    if state == 'rgb':
        texture = unreal.EditorAssetLibrary.load_asset('/Game/Lab012B/Textures/tile_0_0')
        colour = common.expression(m, unreal.MaterialExpressionTextureSampleParameter2D,
            parameter_name='ObservedRGB', texture=texture, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
        colour_output = 'RGB'
    else:
        colour = common.expression(m, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.5, .5, .5, 1))
        colour_output = ''
    normal = common.expression(m, unreal.MaterialExpressionVertexNormalWS)
    direction = common.expression(m, unreal.MaterialExpressionVectorParameter, parameter_name='Direction',
        default_value=unreal.LinearColor(.4, -.3, .8660254, 0))
    dot = common.expression(m, unreal.MaterialExpressionDotProduct)
    common.connect(normal, '', dot, 'A'); common.connect(direction, '', dot, 'B')
    positive = common.expression(m, unreal.MaterialExpressionMax, const_b=0); common.connect(dot, '', positive, 'A')
    light = positive
    if shadow:
        # Ordinary light-space depth comparison of the exact scene, not a new terrain/normal map.
        position = common.expression(m, unreal.MaterialExpressionWorldPosition)
        depth = common.expression(m, unreal.MaterialExpressionTextureObjectParameter, parameter_name='ShadowDepth',
                                  texture=unreal.EditorAssetLibrary.load_asset('/Engine/EngineResources/WhiteSquareTexture'))
        inputs = [('P', position, ''), ('D', depth, ''), ('NL', positive, '')]
        for key in ('Origin', 'Right', 'Up', 'Forward', 'Size'):
            node = common.expression(m, unreal.MaterialExpressionVectorParameter, parameter_name=key)
            inputs.append((key, node, ''))
        custom = common.expression(m, unreal.MaterialExpressionCustom, output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT1)
        custom_inputs = []
        for key, _, _ in inputs:
            item = unreal.CustomInput()
            item.set_editor_property('input_name', key)
            custom_inputs.append(item)
        custom.set_editor_property('inputs', custom_inputs)
        custom.set_editor_property('code', '''
float3 r=P-Origin.xyz;
float2 uv=float2(0.5+dot(r,Right.xyz)/Size.x,0.5-dot(r,Up.xyz)/Size.x);
float z=dot(r,Forward.xyz);
float bias=15.0+0.5*Size.z*(1.0-NL);
float v=0.0;
for(int j=-1;j<=1;j++) for(int i=-1;i<=1;i++) {
 float d=Texture2DSampleLevel(D,DSampler,uv+float2(i,j)/Size.y,0).r;
 v+=step(z-bias,d);
}
return v/9.0;
''')
        for key, node, output in inputs: common.connect(node, output, custom, key)
        light = common.expression(m, unreal.MaterialExpressionMultiply)
        common.connect(positive, '', light, 'A'); common.connect(custom, '', light, 'B')
    factor = common.expression(m, unreal.MaterialExpressionMultiply, const_b=.65); common.connect(light, '', factor, 'A')
    offset = common.expression(m, unreal.MaterialExpressionAdd, const_b=.35); common.connect(factor, '', offset, 'A')
    final = common.expression(m, unreal.MaterialExpressionMultiply)
    common.connect(colour, colour_output, final, 'A'); common.connect(offset, '', final, 'B')
    if not unreal.MaterialEditingLibrary.connect_material_property(final, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError('Lighting connection failed')
    unreal.MaterialEditingLibrary.recompile_material(m); unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def shadow_view(direction):
    _, m = config(); patches = m['geometry']['patches']
    lo = [min(p['bounds_local_m'][0][i] for p in patches) for i in (0, 2, 1)]
    hi = [max(p['bounds_local_m'][1][i] for p in patches) for i in (0, 2, 1)]
    centre = [(x+y)*50 for x, y in zip(lo, hi)]
    position = unreal.Vector(*[centre[i]+direction[i]*500000 for i in range(3)])
    target = unreal.Vector(*centre)
    a = actors().spawn_actor_from_class(unreal.SceneCapture2D, position, unreal.MathLibrary.find_look_at_rotation(position, target))
    vectors = {k: getattr(a, 'get_actor_'+method+'_vector')() for k, method in [('Right', 'right'), ('Up', 'up'), ('Forward', 'forward')]}
    span = []
    for v in (vectors['Right'], vectors['Up']):
        span.append(sum((hi[i]-lo[i])*100*abs([v.x, v.y, v.z][i]) for i in range(3)))
    width = max(span)+2000; size = 4096
    rt = unreal.RenderingLibrary.create_render_target2d(world(), size, size,
        format=unreal.TextureRenderTargetFormat.RTF_R32F, auto_generate_mip_maps=False)
    a.capture_component2d.set_editor_properties({'texture_target': rt, 'projection_type': unreal.CameraProjectionMode.ORTHOGRAPHIC,
        'ortho_width': width, 'auto_calculate_ortho_planes': False, 'update_ortho_planes': False,
        'max_view_distance_override': 1000000., 'capture_source': unreal.SceneCaptureSource.SCS_SCENE_DEPTH,
        'capture_every_frame': False, 'capture_on_movement': False})
    unreal.AutomationLibrary.finish_loading_before_screenshot(); a.capture_component2d.capture_scene()
    params = {'Origin': unreal.LinearColor(position.x, position.y, position.z, 0),
              'Size': unreal.LinearColor(width, size, width/size, 0)}
    for key, v in vectors.items(): params[key] = unreal.LinearColor(v.x, v.y, v.z, 0)
    record = {'position_cm': [position.x, position.y, position.z],
              'width_cm': width, 'pixels': size, 'texel_m': width/size/100,
              'basis': {k: [v.x, v.y, v.z] for k, v in vectors.items()}}
    KEEP.append(rt); a.destroy_actor()
    return rt, params, record


def variant(state, condition, shadow=None):
    _, m = config(); before = signature(); before_camera = pose()
    for a in tiles():
        name = a.get_actor_label().replace('Lab012B_', '')
        if condition == 'baseline':
            material = unreal.EditorAssetLibrary.load_asset('/Game/Lab012B/Materials/'+state+'/'+name)
        else:
            parent = master(state, condition.startswith('shadow'))
            material = unreal.MaterialLibrary.create_dynamic_material_instance(world(), parent); KEEP.append(material)
            if state == 'rgb':
                material.set_texture_parameter_value('ObservedRGB', unreal.EditorAssetLibrary.load_asset('/Game/Lab012B/Textures/'+name))
            direction = m['directions_unreal_east_south_up'][condition.split('_', 1)[1]]
            material.set_vector_parameter_value('Direction', unreal.LinearColor(*direction, 0))
            if condition.startswith('shadow'):
                rt, params, _ = shadow
                material.set_texture_parameter_value('ShadowDepth', rt)
                for key, value in params.items(): material.set_vector_parameter_value(key, value)
        a.static_mesh_component.set_material(0, material)
    if signature() != before or pose() != before_camera: raise RuntimeError('Lighting changed frozen geometry/camera')
    unreal.AutomationLibrary.finish_loading_before_screenshot()


def run(label):
    start = time.monotonic(); root, m = config()
    unreal.EditorLoadingAndSavingUtils.load_map('/Game/Lab012B/dsm')
    if len(tiles()) != 64: raise RuntimeError('Incomplete frozen surface')
    expected = m['geometry']; before = signature()
    if sum(s[-3] for s in before) != expected['triangles']: raise RuntimeError('Topology changed')
    for command in ('r.EyeAdaptationQuality 0', 'r.MotionBlurQuality 0', 'r.SetNearClipPlane 10'):
        unreal.SystemLibrary.execute_console_command(world(), command)
    # Capture depth with original opaque geometry before assigning depth-reading materials.
    shadows = {key: shadow_view(value) for key, value in m['directions_unreal_east_south_up'].items()}
    conditions = ['baseline', 'directional_northeast', 'shadow_northeast', 'directional_southwest', 'shadow_southwest']
    folder = root/'captures'/label; folder.mkdir(parents=True, exist_ok=True); records = []
    for condition in conditions:
        for state in ('neutral', 'rgb'):
            view('overview'); variant(state, condition, shadows.get(condition.split('_', 1)[-1]))
            for name in m['views']:
                view(name); filename = name+'-'+state+'-'+condition
                capture(folder, filename)
                records.append({'name': filename, 'view': name, 'state': state, 'condition': condition,
                                'run': label, 'pose': pose()})
                unreal.log('LAB012F_FRAME '+filename)
    if before != signature(): raise RuntimeError('Frozen scene changed')
    texture_checks = []
    for a in tiles():
        name = a.get_actor_label().replace('Lab012B_', '')
        t = unreal.EditorAssetLibrary.load_asset('/Game/Lab012B/Textures/'+name)
        s = t.blueprint_get_built_texture_size()
        if [round(s.x), round(s.y)] != [2510, 2510] or t.blueprint_get_memory_size() != common.mip_bytes(2510):
            raise RuntimeError('Frozen texture resource changed')
        texture_checks.append([name, round(s.x), round(s.y), t.blueprint_get_memory_size()])
    report = {'frames': records, 'invariance': {'signature': before, 'textures': texture_checks,
              'fov': 50, 'dimensions': [1920, 1080], 'exposure_adaptation': False,
              'atmosphere': 'none', 'normals': 'unchanged imported geometric normals'},
              'shadows': {k: v[2] for k, v in shadows.items()}, 'seconds': time.monotonic()-start,
              'adapter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (root/f'capture-{label}.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('LAB012F_COMPLETE '+label)
