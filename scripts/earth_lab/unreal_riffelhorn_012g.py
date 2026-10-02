"""Frozen 012B geometry/012F lighting; only the experimental appearance varies."""
import hashlib
import json
import time
from pathlib import Path
import unreal
import lab012a_common as common
import lab012f as frozen

KEEP = []


def config():
    project = Path(unreal.Paths.project_dir())
    if not (project/'RiffelhornLab012G.uproject').is_file(): raise RuntimeError('Refuse another project')
    root = Path(json.loads((project/'lab012g-source.json').read_text(encoding='utf-8'))['output_root'])
    return root, json.loads((root/'lab012g-inputs.json').read_text(encoding='utf-8'))


def view(name):
    _, m = config(); v = m['views'][name]; a = frozen.camera()
    p = unreal.Vector(*[x*100 for x in v['position_m']]); t = unreal.Vector(*[x*100 for x in v['target_m']])
    a.set_actor_location(p, False, True); a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(p, t), False)


def texture(name):
    root, _ = config()
    result = common.asset(root/'textures'/(name+'.png'), name, '/Game/Lab012G/Textures')
    settings = {'srgb': True, 'compression_settings': unreal.TextureCompressionSettings.TC_EDITOR_ICON,
        'filter': unreal.TextureFilter.TF_TRILINEAR, 'address_x': unreal.TextureAddress.TA_CLAMP,
        'address_y': unreal.TextureAddress.TA_CLAMP, 'mip_gen_settings': unreal.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE,
        'lod_bias': 0, 'max_texture_size': 0, 'never_stream': True}
    if any(result.get_editor_property(k) != v for k, v in settings.items()): result.set_editor_properties(settings)
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    s = result.blueprint_get_built_texture_size()
    if [round(s.x), round(s.y)] != [2510, 2510] or result.blueprint_get_memory_size() != common.mip_bytes(2510):
        raise RuntimeError('Corrected texture sampling changed')
    unreal.EditorAssetLibrary.save_loaded_asset(result)
    return result


def diagnostic_master(density=False):
    name = 'M_density' if density else 'M_original_unlit'; path = '/Game/Lab012G/Materials'
    full = path+'/'+name
    if unreal.EditorAssetLibrary.does_asset_exist(full): return unreal.EditorAssetLibrary.load_asset(full)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, path, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_properties({'shading_model': unreal.MaterialShadingModel.MSM_UNLIT, 'two_sided': False})
    if density:
        # Actual fragment triangle area orientation; diagnostic only, never a shading normal replacement.
        position = common.expression(m, unreal.MaterialExpressionWorldPosition)
        node = common.expression(m, unreal.MaterialExpressionCustom, output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        item = unreal.CustomInput(); item.set_editor_property('input_name', 'P'); node.set_editor_property('inputs', [item])
        node.set_editor_property('code', 'float c=abs(normalize(cross(ddx(P),ddy(P))).z); return float3(1-c,c,0.2);')
        common.connect(position, '', node, 'P'); output = ''
    else:
        node = common.expression(m, unreal.MaterialExpressionTextureSampleParameter2D, parameter_name='ObservedRGB',
            texture=unreal.EditorAssetLibrary.load_asset('/Game/Lab012B/Textures/tile_0_0'),
            sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR); output = 'RGB'
    if not unreal.MaterialEditingLibrary.connect_material_property(node, output, unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError('Diagnostic connection failed')
    unreal.MaterialEditingLibrary.recompile_material(m); unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def variant(state):
    if state not in config()[1]['states']: raise ValueError(state)
    before, camera = frozen.signature(), frozen.pose()
    for a in frozen.tiles():
        name = a.get_actor_label().replace('Lab012B_', '')
        if state == 'density': parent = diagnostic_master(True)
        elif state == 'original_unlit': parent = diagnostic_master()
        else: parent = unreal.EditorAssetLibrary.load_asset('/Game/Lab012F/Materials/M_rgb_directional')
        material = unreal.MaterialLibrary.create_dynamic_material_instance(frozen.world(), parent); KEEP.append(material)
        if state != 'density':
            t = texture(name) if state == 'normalised_lit' else unreal.EditorAssetLibrary.load_asset('/Game/Lab012B/Textures/'+name)
            material.set_texture_parameter_value('ObservedRGB', t)
        if state.endswith('_lit'):
            material.set_vector_parameter_value('Direction', unreal.LinearColor(.4, -.3, .8660254, 0))
        a.static_mesh_component.set_material(0, material)
    if frozen.signature() != before or frozen.pose() != camera: raise RuntimeError('Appearance changed geometry/camera')
    unreal.AutomationLibrary.finish_loading_before_screenshot()


def run(label):
    start = time.monotonic(); root, m = config()
    unreal.EditorLoadingAndSavingUtils.load_map('/Game/Lab012B/dsm')
    before = frozen.signature()
    if len(before) != 64 or sum(s[-3] for s in before) != 31984002: raise RuntimeError('Frozen topology differs')
    for command in ('r.EyeAdaptationQuality 0', 'r.MotionBlurQuality 0', 'r.SetNearClipPlane 10'):
        unreal.SystemLibrary.execute_console_command(frozen.world(), command)
    folder = root/'captures'/label; folder.mkdir(parents=True, exist_ok=True); records = []
    for state in m['states']:
        view('overview'); variant(state)
        for name in m['views']:
            view(name); filename = name+'-'+state
            frozen.capture(folder, filename)
            records.append({'name': filename, 'view': name, 'state': state, 'pose': frozen.pose()})
            unreal.log('LAB012G_FRAME '+filename)
    if frozen.signature() != before: raise RuntimeError('Frozen surface changed')
    resources = []
    for a in frozen.tiles():
        name = a.get_actor_label().replace('Lab012B_', '')
        for namespace in ('Lab012B', 'Lab012G'):
            t = unreal.EditorAssetLibrary.load_asset('/Game/'+namespace+'/Textures/'+name)
            s = t.blueprint_get_built_texture_size(); size = t.blueprint_get_memory_size()
            if [round(s.x), round(s.y)] != [2510, 2510] or size != common.mip_bytes(2510): raise RuntimeError('Texture resized')
            resources.append([namespace, name, round(s.x), round(s.y), size])
    report = {'frames': records, 'invariance': {'signature': before, 'textures': resources, 'fov': 50,
        'dimensions': [1920, 1080], 'atmosphere': 'none', 'exposure_adaptation': False,
        'lighting': m['lighting'], 'normals': 'unchanged imported geometric normals'},
        'seconds': time.monotonic()-start, 'adapter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (root/f'capture-{label}.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('LAB012G_COMPLETE '+label)
