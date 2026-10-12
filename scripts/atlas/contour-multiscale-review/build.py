"""Package unchanged contour masters and the verified local hillshade, without a server."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import time

SOURCE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('retained_bundle', SOURCE.parent/'contour-visual-review/build.py')
retained = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retained)


def build(data_root, background_root, output):
    started = time.monotonic()
    if output.exists():
        raise ValueError('Fresh viewer directory required')
    history = data_root/'experiments/atlas/source-aware-contours-v1'
    seal = json.loads((SOURCE.parent/'contour-pilot/genuine-rerun-receipt.json').read_text())
    retained.verify_history(history, seal)
    background = json.loads((background_root/'background-receipt.json').read_text())
    image = background_root/'hillshade.png'
    if (background['bounds'] != list(retained.BOUNDS) or background['shape'] != [4000, 4000]
            or background['horizontalReference'] != 'EPSG:2056'
            or background['verticalReference'] != 'LN02 / EPSG:5728'
            or retained.digest(image) != background['outputSha256']):
        raise ValueError('Hillshade alignment or payload seal invalid')
    output.mkdir(parents=True)
    code = (SOURCE/'viewer.js').read_bytes()
    template = (SOURCE/'viewer.html').read_text(encoding='utf-8')
    template = template.replace('CODE_HASH', base64.b64encode(hashlib.sha256(code).digest()).decode())
    template = template.replace('HILLSHADE_DATA', 'data:image/png;base64,'+base64.b64encode(image.read_bytes()).decode())
    prefix, suffix = template.split('DATA_PAYLOAD')
    target = output/'contours-hillshade.html'
    partial = output/'contours-hillshade.partial'
    with partial.open('xb') as raw:
        stream = retained.BoundedWriter(raw, limit=64_000_000)
        stream.write(prefix.encode())
        products = retained.package_products(stream, history/'execution-3/processing/run-1')
        stream.write(suffix.replace('VIEWER_CODE', code.decode()).encode())
    retained.verify_history(history, seal)
    partial.rename(target)
    receipt = {'scope': 'self-contained multiscale contour display over local Swiss visual hillshade',
               'requests': 0, 'newContours': 0, 'products': products,
               'backgroundSha256': retained.digest(image), 'outputSha256': retained.digest(target),
               'outputBytes': target.stat().st_size, 'elapsedSeconds': time.monotonic()-started,
               'display': 'uniform LV95 translation/scale/Y inversion only; LN02 elevations unchanged',
               'implementationSha256': {name: retained.digest(SOURCE/name)
                                        for name in ('build.py', 'viewer.js', 'viewer.html')},
               'browserReview': 'owner-operated Chrome file opening required; no automated browser pass claimed'}
    (output/'bundle-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--background', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({key: value for key, value in build(args.data_root, args.background, args.output).items()
                      if key != 'products'}, indent=2))
