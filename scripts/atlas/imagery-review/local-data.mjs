import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
export const PINS = {
  imageryManifest: '3c8b50fb9d7721b678abc46b9450495b417ccafff15d4ee8a67d9d6a3fee4934',
  contourProduct: '7b5b39baf93abbb7934f1a19c586f28997d5381a9399eae07498459566dc1ad8',
  contourReceipt: 'f9f47535d4edb2bbc1198e703920d50aa12452fd76744d451bdbe752c44b8d7f',
};
export async function openData(dataRoot) {
  const imageryRoot = join(dataRoot, 'derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1');
  const contourRoot = join(dataRoot, 'experiments/atlas/contour-vector-tiles-v1');
  async function record(root, file, expected) {
    const bytes = await readFile(join(root, file));
    if (hash(bytes) !== expected) throw Error(`Retained evidence changed: ${file}`);
    return JSON.parse(bytes);
  }
  const imagery = await record(imageryRoot, 'manifest.json', PINS.imageryManifest);
  const product = await record(contourRoot, 'product.json', PINS.contourProduct);
  const contours = await record(contourRoot, 'tile-receipt.json', PINS.contourReceipt);
  const files = new Map();
  for (const item of imagery.files.filter(f => f.path.startsWith('tiles/') && f.path.endsWith('.png'))) {
    files.set('/imagery/' + item.path.slice(6), { ...item, root: imageryRoot, type: 'image/png' });
  }
  for (const item of contours.inventory) {
    const path = `tiles/${item.product}/${item.z}/${item.x}/${item.y}.pbf`;
    files.set('/contours/' + path.slice(6), { ...item, path, root: contourRoot, type: 'application/vnd.mapbox-vector-tile' });
  }
  files.set('/hillshade.png', { root: contourRoot, path: 'hillshade-mercator.png', sha256: product.background.outputSha256, bytes: 9942966, type: 'image/png' });
  const metadata = { centre: product.centre, bounds: product.boundsLonLat, hillshadeCoordinates: product.background.imageCoordinates,
    imageryIdentity: imagery.identity, imageryYear: imagery.acquisition.mosaicYear,
    nominalInformationMetres: imagery.nominalSourceInformationMetres, distributedGridMetres: imagery.distributedGridMetres,
    imageryDelivery: imagery.delivery, contourVerticalReference: 'LN02 / EPSG:5728, metres', attribution: '©swisstopo / Swiss OGD' };
  return { metadata, async load(url) {
    const file = files.get(url);
    if (!file) return undefined;
    const data = await readFile(join(file.root, file.path));
    if (data.length !== file.bytes || hash(data) !== file.sha256) throw Error('Retained visual product changed');
    return { data, type: file.type };
  } };
}
