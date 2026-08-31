import type maplibregl from "maplibre-gl";
import type {
  CustomLayerInterface,
  CustomRenderMethodInput,
} from "maplibre-gl";

import { LAYER_VISUAL_STRENGTHS } from "../config/layerVisuals";
import { WEATHER_GRID_MIN_ZOOM } from "../config/gridConfig";

import type { Basemap } from "../types/layer";
import type { MutableWindVector } from "./weatherInterpolation";
import type { WindVectorField } from "./windField";

export const WIND_PARTICLE_LAYER_ID = "wind-particle-layer";

const DESKTOP_AREA_PER_PARTICLE = 5_400;
const MOBILE_AREA_PER_PARTICLE = 7_000;
const DESKTOP_MIN_PARTICLES = 80;
const DESKTOP_MAX_PARTICLES = 230;
const MOBILE_MIN_PARTICLES = 44;
const MOBILE_MAX_PARTICLES = 96;
const DESKTOP_TRAIL_POINTS = 20;
const MOBILE_TRAIL_POINTS = 13;
const REDUCED_MOTION_TRAIL_POINTS = 7;
const DESKTOP_FRAME_INTERVAL_MS = 1000 / 30;
const MOBILE_FRAME_INTERVAL_MS = 1000 / 24;
const FIELD_TRANSITION_MS = 420;
const COVERAGE_FADE_MS = 180;
const MAX_FRAME_SECONDS = 0.06;
const PARTICLE_VIEWPORT_MARGIN = 90;

interface MutableCoordinate {
  longitude: number;
  latitude: number;
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function smoothstep(edge0: number, edge1: number, value: number): number {
  const ratio = clamp((value - edge0) / (edge1 - edge0), 0, 1);

  return ratio * ratio * (3 - 2 * ratio);
}

function hashString(value: string): number {
  let hash = 2166136261;

  for (let index = 0; index < value.length; index++) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }

  return hash >>> 0;
}

function longitudeToMercatorX(longitude: number): number {
  return (longitude + 180) / 360;
}

function latitudeToMercatorY(latitude: number): number {
  const constrainedLatitude = clamp(latitude, -85.051129, 85.051129);
  const radians = (constrainedLatitude * Math.PI) / 180;

  return (
    (1 - Math.log(Math.tan(radians) + 1 / Math.cos(radians)) / Math.PI) /
    2
  );
}

function compileShader(
  gl: WebGLRenderingContext | WebGL2RenderingContext,
  type: number,
  source: string
): WebGLShader {
  const shader = gl.createShader(type);

  if (!shader) throw new Error("Could not create wind particle shader");

  gl.shaderSource(shader, source);
  gl.compileShader(shader);

  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const message = gl.getShaderInfoLog(shader) ?? "Unknown shader error";

    gl.deleteShader(shader);
    throw new Error(`Wind particle shader error: ${message}`);
  }

  return shader;
}

function createProgram(
  gl: WebGLRenderingContext | WebGL2RenderingContext
): WebGLProgram {
  const usesWebGl2 =
    typeof WebGL2RenderingContext !== "undefined" &&
    gl instanceof WebGL2RenderingContext;
  const vertexSource = usesWebGl2
    ? `#version 300 es
      in vec2 a_position;
      in vec2 a_other_position;
      in float a_alpha;
      in float a_side;
      in float a_speed;
      uniform mat4 u_matrix;
      uniform vec2 u_viewport;
      out float v_alpha;
      out float v_speed;

      void main() {
        vec4 projected = u_matrix * vec4(a_position, 0.0, 1.0);
        vec4 otherProjected = u_matrix * vec4(a_other_position, 0.0, 1.0);
        vec2 screenDirection =
          (projected.xy / projected.w - otherProjected.xy / otherProjected.w) *
          u_viewport * 0.5;
        vec2 normal = normalize(vec2(-screenDirection.y, screenDirection.x));
        float halfWidth = mix(1.05, 1.5, clamp(a_speed / 55.0, 0.0, 1.0));
        projected.xy += normal * (halfWidth * 2.0 / u_viewport) * a_side * projected.w;
        gl_Position = projected;
        v_alpha = a_alpha;
        v_speed = a_speed;
      }
    `
    : `
      attribute vec2 a_position;
      attribute vec2 a_other_position;
      attribute float a_alpha;
      attribute float a_side;
      attribute float a_speed;
      uniform mat4 u_matrix;
      uniform vec2 u_viewport;
      varying float v_alpha;
      varying float v_speed;

      void main() {
        vec4 projected = u_matrix * vec4(a_position, 0.0, 1.0);
        vec4 otherProjected = u_matrix * vec4(a_other_position, 0.0, 1.0);
        vec2 screenDirection =
          (projected.xy / projected.w - otherProjected.xy / otherProjected.w) *
          u_viewport * 0.5;
        vec2 normal = normalize(vec2(-screenDirection.y, screenDirection.x));
        float halfWidth = mix(1.05, 1.5, clamp(a_speed / 55.0, 0.0, 1.0));
        projected.xy += normal * (halfWidth * 2.0 / u_viewport) * a_side * projected.w;
        gl_Position = projected;
        v_alpha = a_alpha;
        v_speed = a_speed;
      }
    `;
  const fragmentSource = usesWebGl2
    ? `#version 300 es
      precision mediump float;
      in float v_alpha;
      in float v_speed;
      uniform float u_opacity;
      out vec4 fragmentColor;

      void main() {
        float speedMix = clamp(v_speed / 55.0, 0.0, 1.0);
        vec3 slowColor = vec3(0.68, 0.92, 0.88);
        vec3 fastColor = vec3(1.0, 0.68, 0.22);
        fragmentColor = vec4(
          mix(slowColor, fastColor, speedMix),
          mix(0.3, 1.0, pow(v_alpha, 0.68)) * u_opacity
        );
      }
    `
    : `
      precision mediump float;
      varying float v_alpha;
      varying float v_speed;
      uniform float u_opacity;

      void main() {
        float speedMix = clamp(v_speed / 55.0, 0.0, 1.0);
        vec3 slowColor = vec3(0.68, 0.92, 0.88);
        vec3 fastColor = vec3(1.0, 0.68, 0.22);
        gl_FragColor = vec4(
          mix(slowColor, fastColor, speedMix),
          mix(0.3, 1.0, pow(v_alpha, 0.68)) * u_opacity
        );
      }
    `;
  const vertexShader = compileShader(gl, gl.VERTEX_SHADER, vertexSource);
  const fragmentShader = compileShader(gl, gl.FRAGMENT_SHADER, fragmentSource);
  const program = gl.createProgram();

  if (!program) {
    gl.deleteShader(vertexShader);
    gl.deleteShader(fragmentShader);
    throw new Error("Could not create wind particle program");
  }

  gl.attachShader(program, vertexShader);
  gl.attachShader(program, fragmentShader);
  gl.linkProgram(program);
  gl.deleteShader(vertexShader);
  gl.deleteShader(fragmentShader);

  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    const message = gl.getProgramInfoLog(program) ?? "Unknown program error";

    gl.deleteProgram(program);
    throw new Error(`Wind particle program error: ${message}`);
  }

  return program;
}

export class WindParticleLayer implements CustomLayerInterface {
  readonly id = WIND_PARTICLE_LAYER_ID;
  readonly type = "custom" as const;
  readonly renderingMode = "2d" as const;

  private map: maplibregl.Map | null = null;
  private program: WebGLProgram | null = null;
  private vertexBuffer: WebGLBuffer | null = null;
  private positionAttribute = -1;
  private otherPositionAttribute = -1;
  private alphaAttribute = -1;
  private sideAttribute = -1;
  private speedAttribute = -1;
  private matrixUniform: WebGLUniformLocation | null = null;
  private viewportUniform: WebGLUniformLocation | null = null;
  private opacityUniform: WebGLUniformLocation | null = null;

  private field: WindVectorField | null = null;
  private previousField: WindVectorField | null = null;
  private fieldTransitionStartedAt = 0;
  private basemap: Basemap = "terrain";
  private coverageTarget = 1;
  private coverageAmount = 1;
  private enabled = true;
  private isMoving = false;
  private isDocumentHidden = document.visibilityState === "hidden";
  private reducedMotion = false;
  private reducedMotionQuery: MediaQueryList | null = null;
  private repaintTimer: number | null = null;
  private lastFrameAt = 0;
  private viewportDirty = true;
  private staticTrailsDirty = true;
  private randomState = 0x6d2b79f5;

  private particleCount = 0;
  private trailPointCount = 0;
  private longitudes = new Float64Array(0);
  private latitudes = new Float64Array(0);
  private ages = new Float32Array(0);
  private maximumAges = new Float32Array(0);
  private particleSpeeds = new Float32Array(0);
  private historyLongitudes = new Float64Array(0);
  private historyLatitudes = new Float64Array(0);
  private vertices = new Float32Array(0);

  private readonly currentVector: MutableWindVector = {
    eastwardFlow: 0,
    northwardFlow: 0,
    speed: 0,
    flowBearing: 0,
    fromDirection: 0,
  };
  private readonly previousVector: MutableWindVector = {
    eastwardFlow: 0,
    northwardFlow: 0,
    speed: 0,
    flowBearing: 0,
    fromDirection: 0,
  };
  private readonly coordinateScratch: MutableCoordinate = {
    longitude: 0,
    latitude: 0,
  };

  private readonly handleMoveStart = () => {
    this.isMoving = true;
    this.clearRepaintTimer();
  };

  private readonly handleMoveEnd = () => {
    this.isMoving = false;
    this.viewportDirty = true;
    this.staticTrailsDirty = true;
    this.lastFrameAt = 0;
    this.requestRepaint(0);
  };

  private readonly handleVisibilityChange = () => {
    this.isDocumentHidden = document.visibilityState === "hidden";

    if (this.isDocumentHidden) {
      this.clearRepaintTimer();
    } else {
      this.lastFrameAt = 0;
      this.requestRepaint(0);
    }
  };

  private readonly handleReducedMotionChange = (event: MediaQueryListEvent) => {
    this.reducedMotion = event.matches;
    if (this.reducedMotion) this.previousField = null;
    this.viewportDirty = true;
    this.staticTrailsDirty = true;
    this.lastFrameAt = 0;
    this.requestRepaint(0);
  };

  setField(field: WindVectorField): void {
    if (this.field?.signature === field.signature) return;

    if (this.field && !this.reducedMotion) {
      this.previousField = this.field;
      this.fieldTransitionStartedAt = performance.now();
    } else {
      this.randomState = hashString(field.signature) || 0x6d2b79f5;
    }

    this.field = field;
    this.viewportDirty = true;
    this.staticTrailsDirty = true;
    this.requestRepaint(0);
  }

  setBasemap(basemap: Basemap): void {
    if (this.basemap === basemap) return;

    this.basemap = basemap;
    this.requestRepaint(0);
  }

  setCoverageVisible(visible: boolean): void {
    const target = visible ? 1 : 0;

    if (this.coverageTarget === target) return;

    this.coverageTarget = target;
    this.requestRepaint(0);
  }

  setEnabled(enabled: boolean): void {
    if (this.enabled === enabled) return;

    this.enabled = enabled;

    if (enabled) {
      this.lastFrameAt = 0;
      this.requestRepaint(0);
    } else {
      this.clearRepaintTimer();
      this.map?.triggerRepaint();
    }
  }

  onAdd(
    map: maplibregl.Map,
    gl: WebGLRenderingContext | WebGL2RenderingContext
  ): void {
    this.map = map;
    this.program = createProgram(gl);
    this.vertexBuffer = gl.createBuffer();

    if (!this.vertexBuffer) {
      throw new Error("Could not create wind particle vertex buffer");
    }

    this.positionAttribute = gl.getAttribLocation(this.program, "a_position");
    this.otherPositionAttribute = gl.getAttribLocation(
      this.program,
      "a_other_position"
    );
    this.alphaAttribute = gl.getAttribLocation(this.program, "a_alpha");
    this.sideAttribute = gl.getAttribLocation(this.program, "a_side");
    this.speedAttribute = gl.getAttribLocation(this.program, "a_speed");
    this.matrixUniform = gl.getUniformLocation(this.program, "u_matrix");
    this.viewportUniform = gl.getUniformLocation(this.program, "u_viewport");
    this.opacityUniform = gl.getUniformLocation(this.program, "u_opacity");
    this.isMoving = map.isMoving();

    this.reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    this.reducedMotion = this.reducedMotionQuery.matches;
    this.reducedMotionQuery.addEventListener(
      "change",
      this.handleReducedMotionChange
    );
    document.addEventListener("visibilitychange", this.handleVisibilityChange);
    map.on("movestart", this.handleMoveStart);
    map.on("moveend", this.handleMoveEnd);
    map.on("resize", this.handleMoveEnd);
    this.requestRepaint(0);
  }

  onRemove(
    map: maplibregl.Map,
    gl: WebGLRenderingContext | WebGL2RenderingContext
  ): void {
    this.clearRepaintTimer();
    this.reducedMotionQuery?.removeEventListener(
      "change",
      this.handleReducedMotionChange
    );
    document.removeEventListener(
      "visibilitychange",
      this.handleVisibilityChange
    );
    map.off("movestart", this.handleMoveStart);
    map.off("moveend", this.handleMoveEnd);
    map.off("resize", this.handleMoveEnd);

    if (this.vertexBuffer) gl.deleteBuffer(this.vertexBuffer);
    if (this.program) gl.deleteProgram(this.program);

    this.map = null;
    this.program = null;
    this.vertexBuffer = null;
  }

  render(
    gl: WebGLRenderingContext | WebGL2RenderingContext,
    options: CustomRenderMethodInput
  ): void {
    const map = this.map;
    const field = this.field;

    if (!map || !field || !this.enabled || this.isDocumentHidden) return;

    const projectionType = map.getProjection()?.type ?? "mercator";

    if (
      projectionType !== "mercator" ||
      map.getZoom() < WEATHER_GRID_MIN_ZOOM
    ) {
      return;
    }

    const now = performance.now();
    const elapsedMs = this.lastFrameAt
      ? Math.min(now - this.lastFrameAt, MAX_FRAME_SECONDS * 1000)
      : this.getFrameIntervalMs();

    this.updateCoverageAmount(elapsedMs);

    if (this.coverageAmount < 0.005 && this.coverageTarget === 0) return;

    if (!this.isMoving) {
      this.ensureParticleLayout(now);

      if (this.reducedMotion) {
        if (this.staticTrailsDirty) this.seedAllParticles(now);
      } else if (elapsedMs >= this.getFrameIntervalMs() * 0.85) {
        this.simulate(elapsedMs / 1000, now);
        this.lastFrameAt = now;
      }
    }

    const vertexCount = this.buildVertices(now);

    if (vertexCount > 0) {
      this.draw(gl, options, vertexCount);
    }

    if (!this.reducedMotion && !this.isMoving) {
      this.requestRepaint(this.getFrameIntervalMs());
    } else if (Math.abs(this.coverageTarget - this.coverageAmount) > 0.005) {
      this.requestRepaint(this.getFrameIntervalMs());
    }
  }

  private getFrameIntervalMs(): number {
    const width = this.map?.getContainer().clientWidth ?? 0;

    return width <= 500
      ? MOBILE_FRAME_INTERVAL_MS
      : DESKTOP_FRAME_INTERVAL_MS;
  }

  private getParticleLayout(): {
    particleCount: number;
    trailPointCount: number;
  } {
    const map = this.map;

    if (!map) return { particleCount: 0, trailPointCount: 0 };

    const container = map.getContainer();
    const mobile = container.clientWidth <= 500;
    const area = container.clientWidth * container.clientHeight;
    const zoomFactor = clamp(1.15 - (map.getZoom() - 6) * 0.035, 0.72, 1.15);
    const minimum = mobile ? MOBILE_MIN_PARTICLES : DESKTOP_MIN_PARTICLES;
    const maximum = mobile ? MOBILE_MAX_PARTICLES : DESKTOP_MAX_PARTICLES;
    const areaPerParticle = mobile
      ? MOBILE_AREA_PER_PARTICLE
      : DESKTOP_AREA_PER_PARTICLE;
    const reducedMotionFactor = this.reducedMotion ? 0.62 : 1;
    const baseParticleCount = clamp(
      (area / areaPerParticle) * zoomFactor,
      minimum,
      maximum
    );
    const particleCount = Math.round(baseParticleCount * reducedMotionFactor);
    const trailPointCount = this.reducedMotion
      ? REDUCED_MOTION_TRAIL_POINTS
      : mobile
        ? MOBILE_TRAIL_POINTS
        : DESKTOP_TRAIL_POINTS;

    return { particleCount, trailPointCount };
  }

  private ensureParticleLayout(now: number): void {
    if (!this.viewportDirty && this.particleCount > 0) return;

    const { particleCount, trailPointCount } = this.getParticleLayout();
    const layoutChanged =
      particleCount !== this.particleCount ||
      trailPointCount !== this.trailPointCount;

    if (layoutChanged) {
      this.particleCount = particleCount;
      this.trailPointCount = trailPointCount;
      this.longitudes = new Float64Array(particleCount);
      this.latitudes = new Float64Array(particleCount);
      this.ages = new Float32Array(particleCount);
      this.maximumAges = new Float32Array(particleCount);
      this.particleSpeeds = new Float32Array(particleCount);
      this.historyLongitudes = new Float64Array(
        particleCount * trailPointCount
      );
      this.historyLatitudes = new Float64Array(
        particleCount * trailPointCount
      );
      this.vertices = new Float32Array(
        particleCount * Math.max(0, trailPointCount - 1) * 6 * 7
      );
      this.seedAllParticles(now);
    } else if (this.reducedMotion) {
      this.seedAllParticles(now);
    }

    this.viewportDirty = false;
  }

  private seedAllParticles(now: number): void {
    for (let index = 0; index < this.particleCount; index++) {
      this.respawnParticle(index, now);
    }

    this.staticTrailsDirty = false;
  }

  private respawnParticle(index: number, now: number): void {
    const map = this.map;
    const field = this.field;

    if (!map || !field) return;

    const container = map.getContainer();
    let longitude = 0;
    let latitude = 0;
    let found = false;

    for (let attempt = 0; attempt < 12; attempt++) {
      try {
        const location = map.unproject([
          this.random() * container.clientWidth,
          this.random() * container.clientHeight,
        ]);

        longitude = location.lng;
        latitude = location.lat;

        if (
          this.getCoverageFade(longitude, latitude, field) > 0.35 &&
          field.sample(latitude, longitude, this.currentVector)
        ) {
          found = true;
          break;
        }
      } catch {
        // Pitched/globe pixels above the horizon may not unproject to the map.
      }
    }

    if (!found) {
      const longitudeInset = (field.bounds.east - field.bounds.west) * 0.12;
      const latitudeInset = (field.bounds.north - field.bounds.south) * 0.12;

      longitude =
        field.bounds.west +
        longitudeInset +
        this.random() *
          (field.bounds.east - field.bounds.west - longitudeInset * 2);
      latitude =
        field.bounds.south +
        latitudeInset +
        this.random() *
          (field.bounds.north - field.bounds.south - latitudeInset * 2);
    }

    this.longitudes[index] = longitude;
    this.latitudes[index] = latitude;
    this.ages[index] = this.random() * 2.2;
    this.maximumAges[index] = 3 + this.random() * 3.8;

    const historyOffset = index * this.trailPointCount;
    let historyLongitude = longitude;
    let historyLatitude = latitude;
    const historyStep = -(this.getFrameIntervalMs() / 1000) * 1.35;

    for (let point = 0; point < this.trailPointCount; point++) {
      const historyIndex = historyOffset + point;

      this.historyLongitudes[historyIndex] = historyLongitude;
      this.historyLatitudes[historyIndex] = historyLatitude;

      if (
        this.advectCoordinate(
          historyLongitude,
          historyLatitude,
          historyStep,
          now,
          this.coordinateScratch
        )
      ) {
        historyLongitude = this.coordinateScratch.longitude;
        historyLatitude = this.coordinateScratch.latitude;
      }
    }

    if (this.sampleVector(latitude, longitude, now)) {
      this.particleSpeeds[index] = this.currentVector.speed;
    }
  }

  private simulate(elapsedSeconds: number, now: number): void {
    const map = this.map;
    const field = this.field;

    if (!map || !field) return;

    const container = map.getContainer();

    for (let index = 0; index < this.particleCount; index++) {
      const longitude = this.longitudes[index];
      const latitude = this.latitudes[index];
      const projected = map.project([longitude, latitude]);
      const outsideViewport =
        projected.x < -PARTICLE_VIEWPORT_MARGIN ||
        projected.y < -PARTICLE_VIEWPORT_MARGIN ||
        projected.x > container.clientWidth + PARTICLE_VIEWPORT_MARGIN ||
        projected.y > container.clientHeight + PARTICLE_VIEWPORT_MARGIN;

      this.ages[index] += elapsedSeconds;

      if (
        this.ages[index] >= this.maximumAges[index] ||
        outsideViewport ||
        this.getCoverageFade(longitude, latitude, field) <= 0 ||
        !this.advectCoordinate(
          longitude,
          latitude,
          elapsedSeconds,
          now,
          this.coordinateScratch
        )
      ) {
        this.respawnParticle(index, now);
        continue;
      }

      const historyOffset = index * this.trailPointCount;

      for (let point = this.trailPointCount - 1; point > 0; point--) {
        this.historyLongitudes[historyOffset + point] =
          this.historyLongitudes[historyOffset + point - 1];
        this.historyLatitudes[historyOffset + point] =
          this.historyLatitudes[historyOffset + point - 1];
      }

      this.longitudes[index] = this.coordinateScratch.longitude;
      this.latitudes[index] = this.coordinateScratch.latitude;
      this.historyLongitudes[historyOffset] = this.coordinateScratch.longitude;
      this.historyLatitudes[historyOffset] = this.coordinateScratch.latitude;
      this.particleSpeeds[index] = this.currentVector.speed;
    }
  }

  private advectCoordinate(
    longitude: number,
    latitude: number,
    elapsedSeconds: number,
    now: number,
    target: MutableCoordinate
  ): boolean {
    const map = this.map;

    if (!map || !this.sampleVector(latitude, longitude, now)) return false;

    const speed = this.currentVector.speed;

    if (speed < 0.05) {
      target.longitude = longitude;
      target.latitude = latitude;
      return true;
    }

    const eastwardUnit = this.currentVector.eastwardFlow / speed;
    const northwardUnit = this.currentVector.northwardFlow / speed;
    const latitudeCosine = Math.max(
      0.12,
      Math.cos((latitude * Math.PI) / 180)
    );
    const metersPerPixel =
      (156543.03392 * latitudeCosine) / 2 ** map.getZoom();
    const pixelSpeed = clamp(speed * 1.02, 0.45, 44);
    const travelKilometers =
      (pixelSpeed * metersPerPixel * elapsedSeconds) / 1000;

    target.latitude =
      latitude + (northwardUnit * travelKilometers) / 111.32;
    target.longitude =
      longitude +
      (eastwardUnit * travelKilometers) / (111.32 * latitudeCosine);

    return Number.isFinite(target.latitude) && Number.isFinite(target.longitude);
  }

  private sampleVector(
    latitude: number,
    longitude: number,
    now: number
  ): boolean {
    const field = this.field;

    if (!field || !field.sample(latitude, longitude, this.currentVector)) {
      return false;
    }

    const previousField = this.previousField;

    if (!previousField) return true;

    const transition = clamp(
      (now - this.fieldTransitionStartedAt) / FIELD_TRANSITION_MS,
      0,
      1
    );

    if (transition >= 1) {
      this.previousField = null;
      return true;
    }

    if (previousField.sample(latitude, longitude, this.previousVector)) {
      const currentWeight = smoothstep(0, 1, transition);
      const previousWeight = 1 - currentWeight;

      this.currentVector.eastwardFlow =
        this.previousVector.eastwardFlow * previousWeight +
        this.currentVector.eastwardFlow * currentWeight;
      this.currentVector.northwardFlow =
        this.previousVector.northwardFlow * previousWeight +
        this.currentVector.northwardFlow * currentWeight;
      this.currentVector.speed = Math.hypot(
        this.currentVector.eastwardFlow,
        this.currentVector.northwardFlow
      );
    }

    return true;
  }

  private getCoverageFade(
    longitude: number,
    latitude: number,
    field: WindVectorField
  ): number {
    const longitudeSpan = field.bounds.east - field.bounds.west;
    const latitudeSpan = field.bounds.north - field.bounds.south;

    if (longitudeSpan <= 0 || latitudeSpan <= 0) return 0;

    const edgeDistance = Math.min(
      (longitude - field.bounds.west) / longitudeSpan,
      (field.bounds.east - longitude) / longitudeSpan,
      (latitude - field.bounds.south) / latitudeSpan,
      (field.bounds.north - latitude) / latitudeSpan
    );

    return smoothstep(0.025, 0.13, edgeDistance);
  }

  private buildVertices(now: number): number {
    const field = this.field;

    if (!field || this.vertices.length === 0) return 0;

    let offset = 0;

    for (let particle = 0; particle < this.particleCount; particle++) {
      const lifeFade = Math.min(
        smoothstep(0, 0.4, this.ages[particle]),
        smoothstep(0, 0.75, this.maximumAges[particle] - this.ages[particle])
      );
      const historyOffset = particle * this.trailPointCount;
      const speed = this.particleSpeeds[particle];

      for (let point = 0; point < this.trailPointCount - 1; point++) {
        const startIndex = historyOffset + point;
        const endIndex = startIndex + 1;
        const startLongitude = this.historyLongitudes[startIndex];
        const startLatitude = this.historyLatitudes[startIndex];
        const endLongitude = this.historyLongitudes[endIndex];
        const endLatitude = this.historyLatitudes[endIndex];

        if (
          !Number.isFinite(startLongitude) ||
          !Number.isFinite(startLatitude) ||
          !Number.isFinite(endLongitude) ||
          !Number.isFinite(endLatitude)
        ) {
          continue;
        }

        const startTrailFade = (1 - point / this.trailPointCount) ** 1.35;
        const endTrailFade =
          (1 - (point + 1) / this.trailPointCount) ** 1.35;
        const startAlpha =
          lifeFade *
          startTrailFade *
          this.getCoverageFade(startLongitude, startLatitude, field);
        const endAlpha =
          lifeFade *
          endTrailFade *
          this.getCoverageFade(endLongitude, endLatitude, field);

        const startX = longitudeToMercatorX(startLongitude);
        const startY = latitudeToMercatorY(startLatitude);
        const endX = longitudeToMercatorX(endLongitude);
        const endY = latitudeToMercatorY(endLatitude);

        offset = this.writeTrailVertex(
          offset,
          startX,
          startY,
          endX,
          endY,
          startAlpha,
          -1,
          speed
        );
        offset = this.writeTrailVertex(
          offset,
          startX,
          startY,
          endX,
          endY,
          startAlpha,
          1,
          speed
        );
        offset = this.writeTrailVertex(
          offset,
          endX,
          endY,
          startX,
          startY,
          endAlpha,
          -1,
          speed
        );
        offset = this.writeTrailVertex(
          offset,
          endX,
          endY,
          startX,
          startY,
          endAlpha,
          -1,
          speed
        );
        offset = this.writeTrailVertex(
          offset,
          startX,
          startY,
          endX,
          endY,
          startAlpha,
          1,
          speed
        );
        offset = this.writeTrailVertex(
          offset,
          endX,
          endY,
          startX,
          startY,
          endAlpha,
          1,
          speed
        );
      }
    }

    if (this.previousField && now - this.fieldTransitionStartedAt > FIELD_TRANSITION_MS) {
      this.previousField = null;
    }

    return offset / 7;
  }

  private writeTrailVertex(
    offset: number,
    x: number,
    y: number,
    otherX: number,
    otherY: number,
    alpha: number,
    side: number,
    speed: number
  ): number {
    this.vertices[offset++] = x;
    this.vertices[offset++] = y;
    this.vertices[offset++] = otherX;
    this.vertices[offset++] = otherY;
    this.vertices[offset++] = alpha;
    this.vertices[offset++] = side;
    this.vertices[offset++] = speed;

    return offset;
  }

  private draw(
    gl: WebGLRenderingContext | WebGL2RenderingContext,
    options: CustomRenderMethodInput,
    vertexCount: number
  ): void {
    if (!this.program || !this.vertexBuffer) return;

    const basemapOpacity: Record<Basemap, number> = {
      terrain: 0.9,
      satellite: 1,
    };
    const opacity =
      LAYER_VISUAL_STRENGTHS.windParticle *
      basemapOpacity[this.basemap] *
      this.coverageAmount;
    const depthTestWasEnabled = gl.isEnabled(gl.DEPTH_TEST);
    const cullFaceWasEnabled = gl.isEnabled(gl.CULL_FACE);

    gl.useProgram(this.program);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, this.vertices, gl.DYNAMIC_DRAW);
    gl.enable(gl.BLEND);
    gl.blendFuncSeparate(
      gl.SRC_ALPHA,
      gl.ONE_MINUS_SRC_ALPHA,
      gl.ONE,
      gl.ONE_MINUS_SRC_ALPHA
    );
    // Wind is an atmospheric overlay. Terrain depth must not occlude the
    // traces, but the previous GL state is restored for subsequent map layers.
    gl.disable(gl.DEPTH_TEST);
    gl.disable(gl.CULL_FACE);
    gl.enableVertexAttribArray(this.positionAttribute);
    gl.enableVertexAttribArray(this.otherPositionAttribute);
    gl.enableVertexAttribArray(this.alphaAttribute);
    gl.enableVertexAttribArray(this.sideAttribute);
    gl.enableVertexAttribArray(this.speedAttribute);
    gl.vertexAttribPointer(
      this.positionAttribute,
      2,
      gl.FLOAT,
      false,
      28,
      0
    );
    gl.vertexAttribPointer(
      this.otherPositionAttribute,
      2,
      gl.FLOAT,
      false,
      28,
      8
    );
    gl.vertexAttribPointer(this.alphaAttribute, 1, gl.FLOAT, false, 28, 16);
    gl.vertexAttribPointer(this.sideAttribute, 1, gl.FLOAT, false, 28, 20);
    gl.vertexAttribPointer(this.speedAttribute, 1, gl.FLOAT, false, 28, 24);
    gl.uniformMatrix4fv(
      this.matrixUniform,
      false,
      // MapLibre 5's custom-layer matrix accepts whole-world Mercator
      // coordinates in the 0..1 range used by this particle buffer.
      options.defaultProjectionData.mainMatrix as Float32Array
    );
    gl.uniform2f(
      this.viewportUniform,
      gl.drawingBufferWidth,
      gl.drawingBufferHeight
    );
    gl.uniform1f(this.opacityUniform, opacity);
    gl.drawArrays(gl.TRIANGLES, 0, vertexCount);
    gl.disableVertexAttribArray(this.positionAttribute);
    gl.disableVertexAttribArray(this.otherPositionAttribute);
    gl.disableVertexAttribArray(this.alphaAttribute);
    gl.disableVertexAttribArray(this.sideAttribute);
    gl.disableVertexAttribArray(this.speedAttribute);
    gl.bindBuffer(gl.ARRAY_BUFFER, null);
    gl.useProgram(null);

    if (depthTestWasEnabled) gl.enable(gl.DEPTH_TEST);
    if (cullFaceWasEnabled) gl.enable(gl.CULL_FACE);
  }

  private updateCoverageAmount(elapsedMs: number): void {
    if (this.coverageAmount === this.coverageTarget) return;

    const difference = this.coverageTarget - this.coverageAmount;
    const step = Math.min(1, elapsedMs / COVERAGE_FADE_MS);

    this.coverageAmount += difference * step;

    if (Math.abs(this.coverageTarget - this.coverageAmount) < 0.005) {
      this.coverageAmount = this.coverageTarget;
    }
  }

  private requestRepaint(delayMs: number): void {
    if (
      !this.map ||
      !this.enabled ||
      this.isDocumentHidden ||
      this.repaintTimer !== null
    ) {
      return;
    }

    this.repaintTimer = window.setTimeout(() => {
      this.repaintTimer = null;
      this.map?.triggerRepaint();
    }, Math.max(0, delayMs));
  }

  private clearRepaintTimer(): void {
    if (this.repaintTimer === null) return;

    window.clearTimeout(this.repaintTimer);
    this.repaintTimer = null;
  }

  private random(): number {
    this.randomState =
      (Math.imul(this.randomState, 1664525) + 1013904223) >>> 0;

    return this.randomState / 4294967296;
  }
}
