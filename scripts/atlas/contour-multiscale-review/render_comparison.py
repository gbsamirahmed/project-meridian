"""Offline static cartographic comparisons from retained lines and the local PNG."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from background import digest


def render(html, background, output):
    if output.exists():
        raise ValueError('Fresh figure directory required')
    text = html.read_text(encoding='utf-8')
    data = json.loads(text.split('<script type="application/json" id="contour-data">')[1].split('</script>')[0])
    del text
    shade = Image.open(background).convert('RGBA')
    shade.putalpha(shade.getchannel('A').point(lambda value: round(value*0.5)))
    output.mkdir()
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
    files = []
    views = [('overview', (2624000, 1091000, 2626000, 1093000)),
             ('ridge-detail', (2624700, 1091700, 2625300, 1092300)),
             ('native-close', (2624950, 1091950, 2625050, 1092050))]
    for name, bounds in views:
        image = Image.new('RGB', (1840, 1410), 'white')
        canvas = ImageDraw.Draw(image)
        canvas.text((20, 12), f'Riffelhorn / {name}: same 50% native-grid hillshade and unsimplified source contours', fill='#262d2c', font=font)
        canvas.text((20, 42), f'LV95 footprint {bounds}; LN02 heights unchanged. Static raster comparison, not a browser screenshot.', fill='#505854', font=small)
        crop_box = ((bounds[0]-2624000)*2, (1093000-bounds[3])*2,
                    (bounds[2]-2624000)*2, (1093000-bounds[1])*2)
        backdrop = shade.crop(crop_box).resize((580, 580), Image.Resampling.LANCZOS)
        for column, variant in enumerate(data['variants']):
            for row, interval in enumerate((20, 10)):
                left, top = 20+column*610, 80+row*650
                canvas.text((left, top), f"{variant['label']} / {interval} m", fill='#262d2c', font=font)
                canvas.text((left, top+28), f'{(bounds[2]-bounds[0])/580:.2f} metres/display pixel; 100 m indices darker', fill='#505854', font=small)
                # Supersampling approximates the viewer's 0.6/1.3 px line hierarchy.
                tile = Image.new('RGBA', (1160, 1160), '#f4f1e8')
                tile.alpha_composite(backdrop.resize((1160, 1160)))
                draw = ImageDraw.Draw(tile)
                scale = 1160/(bounds[2]-bounds[0])
                for line in variant['lines']:
                    if interval == 20 and not line['twentyMetreSubset']:
                        continue
                    points = [((point[0]-bounds[0])*scale, (bounds[3]-point[1])*scale)
                              for point in line['coordinates']]
                    draw.line(points, fill='#68533b' if line['index'] else '#93795a', width=3 if line['index'] else 1)
                image.paste(tile.resize((580, 580), Image.Resampling.LANCZOS).convert('RGB'), (left, top+54))
        canvas.text((20, 1380), '©swisstopo / Swiss OGD · native visual gradients · no new contours or datum transformation · subset boundary only', fill='#505854', font=small)
        target = output/f'{name}.png'; image.save(target)
        files.append({'name': target.name, 'bytes': target.stat().st_size, 'sha256': digest(target)})
    receipt = {'sourceBundleSha256': digest(html), 'backgroundSha256': digest(background),
               'operation': 'affine display/cropping only; no DEM reads or new contours', 'files': files}
    (output/'figure-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--background', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); render(args.html, args.background, args.output)
