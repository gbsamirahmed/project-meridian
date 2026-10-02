"""Read-only pre-display scalar audit; no new benchmark material or image state."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unreal

sys.path.insert(0, unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()+'Python'))
import lab012g as lab
import lab012f as frozen

root, manifest = lab.config()
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Lab012B/dsm')
before = frozen.signature()
for command in ('r.EyeAdaptationQuality 0', 'r.MotionBlurQuality 0', 'r.SetNearClipPlane 10'):
    unreal.SystemLibrary.execute_console_command(frozen.world(), command)
points = {'riffelhorn_oblique': [[x, y] for y in (816, 920, 1008) for x in (1182, 1254, 1342, 1454)],
          'alpine_path': [[520, 400], [600, 504], [800, 552], [960, 600]]}
records = []
for state in ('original_unlit', 'original_lit', 'normalised_lit'):
    lab.view('overview'); lab.variant(state)
    for view, pixels in points.items():
        lab.view(view); camera = frozen.camera()
        actor = frozen.actors().spawn_actor_from_class(unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation())
        target = unreal.RenderingLibrary.create_render_target2d(frozen.world(), 1920, 1080,
            format=unreal.TextureRenderTargetFormat.RTF_RGBA32F, auto_generate_mip_maps=False)
        actor.capture_component2d.set_editor_properties({'texture_target': target, 'fov_angle': 50,
            'capture_source': unreal.SceneCaptureSource.SCS_SCENE_COLOR_HDR,
            'capture_every_frame': False, 'capture_on_movement': False})
        unreal.AutomationLibrary.finish_loading_before_screenshot(); actor.capture_component2d.capture_scene()
        values = []
        for x, y in pixels:
            value = unreal.RenderingLibrary.read_render_target_raw_pixel(frozen.world(), target, x, y, normalize=False)
            values.append([value.r, value.g, value.b])
        records.append({'view': view, 'state': state, 'pixels': pixels, 'hdr_rgb': values, 'pose': frozen.pose()})
        actor.destroy_actor()
assert frozen.signature() == before
report = {'records': records, 'geometry_unchanged': True, 'input_identity': manifest['identity'],
          'interpretation': 'scene colour before final LDR display conversion; common exposure/pre-exposure remains fixed',
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'attribution': '\u00a9 swisstopo'}
label = os.environ.get('MERIDIAN_012G_PROBE_RUN', 'first')
if label not in ('first', 'repeat'): raise ValueError(label)
(root/f'pre-tone-probe-{label}.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
unreal.log('LAB012G_PRE_TONE_PROBE_PASS')
