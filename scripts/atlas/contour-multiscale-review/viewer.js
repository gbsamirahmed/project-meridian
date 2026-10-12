/* Offline multiscale display; retained LV95 contours and a separate visual hillshade. */
(() => {
  const policy = { boundariesMpp: [2, 0.75, 0.25], hysteresis: 0.12, settleMs: 180 };
  const bands = [
    { variant: 2, interval: 20, label: 'Overview' },
    { variant: 1, interval: 20, label: 'Intermediate' },
    { variant: 1, interval: 10, label: 'Close' },
    { variant: 0, interval: 10, label: 'Native detail' },
  ];
  const bandFor = (mpp, current = null) => {
    if (current === null) { const index = policy.boundariesMpp.findIndex(value => mpp >= value); return index < 0 ? 3 : index; }
    let next = current;
    while (next < 3 && mpp < policy.boundariesMpp[next] * (1 - policy.hysteresis)) next++;
    while (next > 0 && mpp >= policy.boundariesMpp[next - 1] * (1 + policy.hysteresis)) next--;
    return next;
  };
  const bounds = [2624000, 1091000, 2626000, 1093000];
  const worldToScreen = (point, view, width, height) => [width / 2 + (point[0] - view.x) * view.scale, height / 2 - (point[1] - view.y) * view.scale];
  const screenToWorld = (point, view, width, height) => [view.x + (point[0] - width / 2) / view.scale, view.y - (point[1] - height / 2) / view.scale];
  const fit = (width, height) => ({ x: 2625000, y: 1092000, scale: Math.max(0.01, Math.min(width, height) / 2200) });
  const zoom = (view, factor, anchor, width, height) => {
    const fixed = screenToWorld(anchor, view, width, height);
    const scale = Math.max(0.01, Math.min(15, view.scale * factor));
    return { x: fixed[0] - (anchor[0] - width / 2) / scale, y: fixed[1] + (anchor[1] - height / 2) / scale, scale };
  };
  const segmentDistance = (point, a, b) => {
    const dx = b[0] - a[0], dy = b[1] - a[1], denominator = dx * dx + dy * dy;
    const t = denominator ? Math.max(0, Math.min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / denominator)) : 0;
    return Math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy);
  };
  const accepts = (line, interval) => interval === 10 || line.twentyMetreSubset;
  globalThis.MeridianContourMath = { bounds, policy, bands, bandFor, worldToScreen, screenToWorld, fit, zoom, segmentDistance, accepts };
  if (typeof document === 'undefined') return; // Pure coordinate tests, without a browser.

  const canvas = document.getElementById('map'), context = canvas.getContext('2d');
  const variantSelect = document.getElementById('variant'), intervalSelect = document.getElementById('interval');
  const statistics = document.getElementById('statistics'), selection = document.getElementById('selection');
  let data, prepared = [], selected = null, view, width = 1, height = 1, frame = 0;
  try { data = JSON.parse(document.getElementById('contour-data').textContent); }
  catch { statistics.textContent = 'Local contour data could not be read.'; return; }
  const mode = document.getElementById('mode'), backgroundToggle = document.getElementById('background');
  const pointers = new Map();
  let interval = 20, activeBand = null, scaleTimer = 0, backgroundReady = false;
  const background = new Image();
  background.onload = () => {
    if (background.naturalWidth !== 4000 || background.naturalHeight !== 4000) {
      document.getElementById('background-state').textContent = 'Hillshade dimensions invalid; neutral background shown.'; return;
    }
    backgroundReady = true;
    document.getElementById('background-state').textContent = 'Swiss DTM hillshade · native 0.5 m · grid north up · opacity 50%';
    requestDraw();
  };
  background.onerror = () => { document.getElementById('background-state').textContent = 'Embedded hillshade could not be decoded; neutral background shown.'; };
  background.src = document.getElementById('hillshade-image').getAttribute('src');
  function settleScale() {
    if (mode.value !== 'auto' || pointers.size) return;
    const next = bandFor(1 / view.scale, activeBand);
    if (next !== activeBand) {
      activeBand = next;
      variantSelect.value = String(bands[next].variant);
      interval = bands[next].interval; intervalSelect.value = String(interval);
      chooseVariant();
    }
    updateStatistics();
  }
  const requestDraw = () => {
    if (!frame) frame = requestAnimationFrame(draw);
    clearTimeout(scaleTimer);
    if (view && mode.value === 'auto') scaleTimer = setTimeout(settleScale, policy.settleMs);
  };

  function chooseVariant() {
    const variant = data.variants[Number(variantSelect.value)];
    // Cache only the selected variant. Local metre offsets avoid sending large
    // LV95 coordinates through the path renderer. Source numbers remain intact.
    prepared = variant.lines.map(line => {
      const path = new Path2D();
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      line.coordinates.forEach((point, index) => {
        const x = point[0] - bounds[0], y = bounds[3] - point[1];
        if (index) path.lineTo(x, y); else path.moveTo(x, y);
        minX = Math.min(minX, point[0]); maxX = Math.max(maxX, point[0]);
        minY = Math.min(minY, point[1]); maxY = Math.max(maxY, point[1]);
      });
      return { line, path, box: [minX, minY, maxX, maxY] };
    });
    selected = null; updateStatistics(); requestDraw();
  }
  function updateStatistics() {
    const variant = data.variants[Number(variantSelect.value)], counts = variant.counts[String(interval)];
    statistics.textContent = `${mode.value === 'auto' ? bands[activeBand ?? 0].label : 'Manual'} · ${variant.label} · ${interval} m · ${(1 / view.scale).toFixed(2)} m/CSS px · ${counts.lines.toLocaleString('en-GB')} lines · ${counts.vertices.toLocaleString('en-GB')} unchanged vertices`;
    if (!selected) selection.textContent = 'Click a contour to inspect its elevation. No height is inferred between lines.';
  }
  function draw() {
    frame = 0;
    const ratio = Math.min(2, window.devicePixelRatio || 1);
    if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
      canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
    }
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.fillStyle = '#f4f1e8'; context.fillRect(0, 0, width, height);
    const origin = worldToScreen([bounds[0], bounds[3]], view, width, height);
    context.translate(origin[0], origin[1]); context.scale(view.scale, view.scale);
    if (backgroundReady && backgroundToggle.checked) {
      context.globalAlpha = 0.5; context.imageSmoothingEnabled = true;
      context.drawImage(background, 0, 0, 2000, 2000); context.globalAlpha = 1;
    }
    context.strokeStyle = '#dfded3'; context.lineWidth = 0.7 / view.scale;
    context.beginPath();
    for (let metre = 0; metre <= 2000; metre += 500) {
      context.moveTo(metre, 0); context.lineTo(metre, 2000);
      context.moveTo(0, metre); context.lineTo(2000, metre);
    }
    context.stroke(); context.strokeStyle = '#8f9990'; context.lineWidth = 1 / view.scale;
    context.strokeRect(0, 0, 2000, 2000);
    const lower = screenToWorld([0, height], view, width, height), upper = screenToWorld([width, 0], view, width, height);
    for (const feature of prepared) {
      const { line, path, box } = feature;
      if (!accepts(line, interval) || box[2] < lower[0] || box[0] > upper[0] || box[3] < lower[1] || box[1] > upper[1]) continue;
      context.strokeStyle = line.index ? '#68533b' : '#93795a';
      context.lineWidth = (line.index ? 1.3 : 0.6) / view.scale;
      context.stroke(path);
    }
    if (selected) { context.strokeStyle = '#bf3b20'; context.lineWidth = 2.4 / view.scale; context.stroke(selected.path); }
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.fillStyle = '#3c4942'; context.font = '12px system-ui'; context.fillText('N ↑', width - 40, 24);
    const desired = 100 / view.scale;
    const metres = [10, 20, 50, 100, 200, 500, 1000].reduce((chosen, value) => value <= desired ? value : chosen, 10);
    document.getElementById('scale-line').style.width = `${metres * view.scale}px`;
    document.getElementById('scale-label').textContent = `${metres} m · ${(1 / view.scale).toFixed(2)} m/CSS px`;
    updateStatistics();
  }
  function inspect(point) {
    const world = screenToWorld(point, view, width, height), tolerance = 7 / view.scale;
    let nearest = null, distance = tolerance;
    for (const feature of prepared) {
      const { line, box } = feature;
      if (!accepts(line, interval) || world[0] < box[0] - tolerance || world[0] > box[2] + tolerance || world[1] < box[1] - tolerance || world[1] > box[3] + tolerance) continue;
      for (let index = 1; index < line.coordinates.length; index++) {
        const candidate = segmentDistance(world, line.coordinates[index - 1], line.coordinates[index]);
        if (candidate < distance) { nearest = feature; distance = candidate; }
      }
    }
    selected = nearest;
    selection.textContent = nearest ? `${nearest.line.level} m LN02 · ${data.variants[Number(variantSelect.value)].label} · source line ${nearest.line.line}${nearest.line.index ? ' · index contour' : ''}` : 'No contour selected. No elevation is inferred from this position.';
    requestDraw();
  }
  function resize() {
    const box = canvas.getBoundingClientRect(); width = box.width; height = box.height;
    if (!view) view = fit(width, height); requestDraw();
  }
  new ResizeObserver(resize).observe(canvas);
  const setMode = () => {
    const automatic = mode.value === 'auto';
    variantSelect.disabled = automatic; intervalSelect.disabled = automatic;
    if (automatic) { activeBand = null; settleScale(); }
    updateStatistics(); requestDraw();
  };
  mode.addEventListener('change', setMode);
  backgroundToggle.addEventListener('change', requestDraw);
  variantSelect.addEventListener('change', chooseVariant);
  intervalSelect.addEventListener('change', () => { interval = Number(intervalSelect.value); selected = null; updateStatistics(); requestDraw(); });
  document.getElementById('fit').addEventListener('click', () => { view = fit(width, height); requestDraw(); });
  for (const [id, factor] of [['in', 1.5], ['out', 1 / 1.5]]) document.getElementById(id).addEventListener('click', () => { view = zoom(view, factor, [width / 2, height / 2], width, height); requestDraw(); });
  const position = event => { const box = canvas.getBoundingClientRect(); return [event.clientX - box.left, event.clientY - box.top]; };
  canvas.addEventListener('wheel', event => { event.preventDefault(); view = zoom(view, Math.exp(-Math.max(-100, Math.min(100, event.deltaY)) * 0.006), position(event), width, height); requestDraw(); }, { passive: false });
  canvas.addEventListener('keydown', event => {
    if (event.key === '+' || event.key === '=' || event.key === '-') view = zoom(view, event.key === '-' ? 1 / 1.5 : 1.5, [width / 2, height / 2], width, height);
    else if (event.key === 'ArrowLeft') view.x -= 70 / view.scale;
    else if (event.key === 'ArrowRight') view.x += 70 / view.scale;
    else if (event.key === 'ArrowUp') view.y += 70 / view.scale;
    else if (event.key === 'ArrowDown') view.y -= 70 / view.scale;
    else return;
    event.preventDefault(); requestDraw();
  });
  let previous = null, moved = false, down = null;
  const gesture = () => {
    const points = [...pointers.values()];
    return points.length === 1 ? { centre: points[0], distance: 0 } : {
      centre: [(points[0][0] + points[1][0]) / 2, (points[0][1] + points[1][1]) / 2],
      distance: Math.hypot(points[0][0] - points[1][0], points[0][1] - points[1][1]),
    };
  };
  canvas.addEventListener('pointerdown', event => {
    if (event.button !== 0 || pointers.size === 2) return;
    canvas.focus(); canvas.setPointerCapture(event.pointerId); pointers.set(event.pointerId, position(event));
    previous = gesture(); down = position(event); moved = pointers.size > 1;
  });
  canvas.addEventListener('pointermove', event => {
    if (!pointers.has(event.pointerId)) return;
    pointers.set(event.pointerId, position(event)); const next = gesture();
    if (previous.distance && next.distance) { view = zoom(view, next.distance / previous.distance, previous.centre, width, height); moved = true; }
    view.x -= (next.centre[0] - previous.centre[0]) / view.scale; view.y += (next.centre[1] - previous.centre[1]) / view.scale;
    if (Math.hypot(...position(event).map((value, index) => value - down[index])) > 4) moved = true;
    previous = next; requestDraw();
  });
  const endPointer = event => {
    if (!pointers.has(event.pointerId)) return;
    if (!moved && pointers.size === 1 && event.type === 'pointerup') inspect(position(event));
    pointers.delete(event.pointerId); previous = pointers.size ? gesture() : null;
    if (pointers.size) { down = [...pointers.values()][0]; moved = true; }
    requestDraw();
  };
  canvas.addEventListener('pointerup', endPointer); canvas.addEventListener('pointercancel', endPointer);
  resize(); chooseVariant(); setMode();
})();
