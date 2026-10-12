"""Static offline figures from the packaged lines; no raster/terrain derivation."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

def render(html,output):
    if output.exists():raise ValueError('Fresh figure directory required')
    text=html.read_text(encoding='utf-8')
    data=json.loads(text.split('<script type="application/json" id="contour-data">')[1].split('</script>')[0])
    del text
    output.mkdir()
    font_path=Path('C:/Windows/Fonts/arial.ttf')
    font=ImageFont.truetype(str(font_path),21) if font_path.exists() else ImageFont.load_default()
    small=ImageFont.truetype(str(font_path),16) if font_path.exists() else ImageFont.load_default()
    files=[]
    for name,bounds in (('whole-study',(2624000,1091000,2626000,1093000)),
                        ('centre-detail',(2624700,1091700,2625300,1092300))):
        image=Image.new('RGB',(1400,2300),'white');canvas=ImageDraw.Draw(image)
        canvas.text((28,18),'Riffelhorn: existing unsimplified LN02 DTM contours',fill='#262d2c',font=font)
        canvas.text((28,52),f'{name}: LV95 extent {bounds}; neutral background; same line weights in every panel',fill='#505854',font=small)
        for row,variant in enumerate(data['variants']):
            for col,interval in enumerate((10,20)):
                left=28+col*700;top=100+row*720
                canvas.text((left,top),f"{variant['label']} / {interval} m",fill='#262d2c',font=font)
                counts=variant['counts'][str(interval)]
                canvas.text((left,top+30),f"{counts['lines']:,} lines; {counts['vertices']:,} source vertices (whole study)",fill='#505854',font=small)
                # Draw in a separate tile so clipping never changes source lines.
                tile=Image.new('RGB',(640,640),'#f4f1e8');draw=ImageDraw.Draw(tile)
                scale=640/(bounds[2]-bounds[0])
                for line in variant['lines']:
                    if interval==20 and not line['twentyMetreSubset']:continue
                    points=[((p[0]-bounds[0])*scale,(bounds[3]-p[1])*scale) for p in line['coordinates']]
                    draw.line(points,fill='#68533b' if line['index'] else '#93795a',width=2 if line['index'] else 1)
                image.paste(tile,(left,top+64));canvas.rectangle((left,top+64,left+640,top+704),outline='#8f9990')
        canvas.text((28,2270),'©swisstopo / Swiss OGD · single-run evidence · no elevation transformation or simplification',fill='#505854',font=small)
        target=output/f'{name}.png';image.save(target)
        files.append({'name':target.name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    receipt={'sourceBundleSha256':hashlib.sha256(html.read_bytes()).hexdigest(),
             'operation':'affine contour display/rasterisation only; no shaded background or DEM read','files':files}
    (output/'figure-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();render(args.html,args.output)
