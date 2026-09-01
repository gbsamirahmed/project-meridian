import type maplibregl from "maplibre-gl";
import type {
  CustomLayerInterface,
  CustomRenderMethodInput,
} from "maplibre-gl";

import { LAYER_VISUAL_STRENGTHS } from "../config/layerVisuals";

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
const DESKTOP_FRAME_INTERVAL_MS = 1000 / 30;
const MOBILE_FRAME_INTERVAL_MS = 1000 / 24;
const FIELD_TRANSITION_MS = 420;
const COVERAGE_FADE_MS = 180;
const MAX_FRAME_SECONDS = 0.06;
const PARTICLE_VIEWPORT_MARGIN = 90;

const DENSITY_ZOOM_STOPS = [
  [0, 0.82],
  [4, 0.9],
  [7, 1.02],
  [10, 1.16],
  [13, 1.28],
  [16, 1.34],
] as const;

const DESKTOP_TRAIL_ZOOM_STOPS = [
  [0, 16],
  [4, 18],
  [7, 22],
  [10, 27],
  [13, 31],
  [16, 33],
] as const;

const MOBILE_TRAIL_ZOOM_STOPS = [
  [0, 11],
  [4, 12],
  [7, 14],
  [10, 17],
  [13, 19],
  [16, 20],
] as const;

const REDUCED_MOTION_TRAIL_ZOOM_STOPS = [
  [0, 6],
  [4, 7],
  [7, 8],
  [10, 10],
  [13, 12],
  [16, 13],
] as const;

const WIDTH_ZOOM_STOPS = [
  [0, 0.82],
  [4, 0.9],
  [7, 1.05],
  [10, 1.28],
  [13, 1.5],
  [16, 1.62],
] as const;

const OPACITY_ZOOM_STOPS = [
  [0, 0.78],
  [4, 0.86],
  [7, 0.96],
  [10, 1.05],
  [13, 1.12],
  [16, 1.16],
] as const;

interface MutableCoordinate {
  longitude: number;
  latitude: number;
}

interface WindParticlePopulation {
  field: WindVectorField;
  particleCount: number;
  trailPointCount: number;
  longitudes: Float64Array;
  latitudes: Float64Array;
  ages: Float32Array;
  maximumAges: Float32Array;
  particleSpeeds: Float32Array;
  historyLongitudes: Float64Array;
  historyLatitudes: Float64Array;
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function smoothstep(edge0: number, edge1: number, value: number): number {
  const ratio = clamp((value - edge0) / (edge1 - edge0), 0, 1);

  return ratio * ratio * (3 - 2 * ratio);
}

function interpolateZoomStops(
  zoom: number,
  stops: ReadonlyArray<readonly [number, number]>
): number {
  if (zoom <= stops[0][0]) return stops[0][1];

  for (let index = 1; index < stops.length; index++) {
    const [nextZoom, nextValue] = stops[index];
    const [previousZoom, previousValue] = stops[index - 1];
    if (zoom <= nextZoom) {
      const amount = (zoom - previousZoom) / (nextZoom - previousZoom);
      return previousValue + (nextValue - previousValue) * amount;
    }
  }

  return stops[stops.length - 1][1];
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

function wrapLongitude(longitude: number): number {
  return ((longitude + 180) % 360 + 360) % 360 - 180;
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

interface WindProgram {
  program: WebGLProgram;
  positionAttribute: number;
  otherPositionAttribute: number;
  alphaAttribute: number;
  sideAttribute: number;
  speedAttribute: number;
  viewportUniform: WebGLUniformLocation | null;
  opacityUniform: WebGLUniformLocation | null;
  widthScaleUniform: WebGLUniformLocation | null;
  terrainMixUniform: WebGLUniformLocation | null;
  projectionMatrixUniform: WebGLUniformLocation | null;
  projectionFallbackMatrixUniform: WebGLUniformLocation | null;
  projectionTileMercatorUniform: WebGLUniformLocation | null;
  projectionClippingPlaneUniform: WebGLUniformLocation | null;
  projectionTransitionUniform: WebGLUniformLocation | null;
}

function createProgram(
  gl: WebGLRenderingContext | WebGL2RenderingContext,
  shaderData: CustomRenderMethodInput["shaderData"]
): WindProgram {
  const usesWebGl2 =
    typeof WebGL2RenderingContext !== "undefined" &&
    gl instanceof WebGL2RenderingContext;
  if (!usesWebGl2) {
    throw new Error("Projection-aware wind particles require WebGL 2");
  }
  const vertexSource = `#version 300 es
      ${shaderData.vertexShaderPrelude}
      ${shaderData.define}
      in vec2 a_position;
      in vec2 a_other_position;
      in float a_alpha;
      in float a_side;
      in float a_speed;
      uniform vec2 u_viewport;
      uniform float u_width_scale;
      out float v_alpha;
      out float v_speed;

      void main() {
        vec4 projected = projectTile(a_position);
        vec4 otherProjected = projectTile(a_other_position);
        vec2 screenDirection =
          (projected.xy / projected.w - otherProjected.xy / otherProjected.w) *
          u_viewport * 0.5;
        vec2 normal = normalize(vec2(-screenDirection.y, screenDirection.x));
        float halfWidth =
          mix(1.05, 1.5, clamp(a_speed / 55.0, 0.0, 1.0)) *
          u_width_scale;
        projected.xy += normal * (halfWidth * 2.0 / u_viewport) * a_side * projected.w;
        gl_Position = projected;
        v_alpha = a_alpha;
        v_speed = a_speed;
      }
    `;
  const fragmentSource = `#version 300 es
      precision mediump float;
      in float v_alpha;
      in float v_speed;
      uniform float u_opacity;
      uniform float u_terrain_mix;
      out vec4 fragmentColor;

      void main() {
        float speedMix = clamp(v_speed / 55.0, 0.0, 1.0);
        vec3 slowColor = mix(
          vec3(0.68, 0.92, 0.88),
          vec3(0.12, 0.48, 0.5),
          u_terrain_mix
        );
        vec3 fastColor = mix(
          vec3(1.0, 0.68, 0.22),
          vec3(0.9, 0.37, 0.12),
          u_terrain_mix
        );
        fragmentColor = vec4(
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

  return {
    program,
    positionAttribute: gl.getAttribLocation(program, "a_position"),
    otherPositionAttribute: gl.getAttribLocation(program, "a_other_position"),
    alphaAttribute: gl.getAttribLocation(program, "a_alpha"),
    sideAttribute: gl.getAttribLocation(program, "a_side"),
    speedAttribute: gl.getAttribLocation(program, "a_speed"),
    viewportUniform: gl.getUniformLocation(program, "u_viewport"),
    opacityUniform: gl.getUniformLocation(program, "u_opacity"),
    widthScaleUniform: gl.getUniformLocation(program, "u_width_scale"),
    terrainMixUniform: gl.getUniformLocation(program, "u_terrain_mix"),
    projectionMatrixUniform: gl.getUniformLocation(program, "u_projection_matrix"),
    projectionFallbackMatrixUniform: gl.getUniformLocation(
      program,
      "u_projection_fallback_matrix"
    ),
    projectionTileMercatorUniform: gl.getUniformLocation(
      program,
      "u_projection_tile_mercator_coords"
    ),
    projectionClippingPlaneUniform: gl.getUniformLocation(
      program,
      "u_projection_clipping_plane"
    ),
    projectionTransitionUniform: gl.getUniformLocation(
      program,
      "u_projection_transition"
    ),
  };
}

export class WindParticleLayer implements CustomLayerInterface {
  readonly id = WIND_PARTICLE_LAYER_ID;
  readonly type = "custom" as const;
  readonly renderingMode = "2d" as const;

  private map: maplibregl.Map | null = null;
  private readonly programs = new Map<string, WindProgram>();
  private vertexBuffer: WebGLBuffer | null = null;

  private field: WindVectorField | null = null;
  private previousPopulation: WindParticlePopulation | null = null;
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
    this.field?.scheduleCoverage?.(this.map!);
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
    if (this.reducedMotion) {
      this.previousPopulation?.field.dispose?.();
      this.previousPopulation = null;
    }
    this.viewportDirty = true;
    this.staticTrailsDirty = true;
    this.lastFrameAt = 0;
    this.requestRepaint(0);
  };

  setField(field: WindVectorField): void {
    if (this.field?.signature === field.signature) return;

    if (this.field && !this.reducedMotion && this.particleCount > 0) {
      this.previousPopulation?.field.dispose?.();
      this.previousPopulation = {
        field: this.field,
        particleCount: this.particleCount,
        trailPointCount: this.trailPointCount,
        longitudes: this.longitudes,
        latitudes: this.latitudes,
        ages: this.ages,
        maximumAges: this.maximumAges,
        particleSpeeds: this.particleSpeeds,
        historyLongitudes: this.historyLongitudes,
        historyLatitudes: this.historyLatitudes,
      };
      this.fieldTransitionStartedAt = performance.now();
      this.particleCount = 0;
      this.trailPointCount = 0;
      this.longitudes = new Float64Array(0);
      this.latitudes = new Float64Array(0);
      this.ages = new Float32Array(0);
      this.maximumAges = new Float32Array(0);
      this.particleSpeeds = new Float32Array(0);
      this.historyLongitudes = new Float64Array(0);
      this.historyLatitudes = new Float64Array(0);
    } else {
      this.field?.dispose?.();
      this.previousPopulation?.field.dispose?.();
      this.previousPopulation = null;
    }

    this.field = field;
    this.randomState = hashString(field.signature) || 0x6d2b79f5;
    this.viewportDirty = true;
    this.staticTrailsDirty = true;
    this.requestRepaint(0);
  }

  getFieldSignature(): string | null {
    return this.field?.signature ?? null;
  }

  scheduleCoverageRefresh(): void {
    if (this.map) this.field?.scheduleCoverage?.(this.map);
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
    this.vertexBuffer = gl.createBuffer();

    if (!this.vertexBuffer) {
      throw new Error("Could not create wind particle vertex buffer");
    }

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
    for (const windProgram of this.programs.values()) {
      gl.deleteProgram(windProgram.program);
    }
    this.programs.clear();
    this.field?.dispose?.();
    this.previousPopulation?.field.dispose?.();

    this.map = null;
    this.vertexBuffer = null;
  }

  render(
    gl: WebGLRenderingContext | WebGL2RenderingContext,
    options: CustomRenderMethodInput
  ): void {
    const map = this.map;
    const field = this.field;

    if (!map || !field || !this.enabled || this.isDocumentHidden) return;

    const now = performance.now();
    const elapsedMs = this.lastFrameAt
      ? Math.min(now - this.lastFrameAt, MAX_FRAME_SECONDS * 1000)
      : this.getFrameIntervalMs();

    this.updateCoverageAmount(elapsedMs);

    if (this.coverageAmount < 0.005 && this.coverageTarget === 0) return;

    if (!this.isMoving) {
      this.ensureParticleLayout();

      if (this.reducedMotion) {
        if (this.staticTrailsDirty) this.seedAllParticles();
      } else if (elapsedMs >= this.getFrameIntervalMs() * 0.85) {
        this.simulate(elapsedMs / 1000);
        this.simulatePreviousPopulation(elapsedMs / 1000);
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
    const zoom = map.getZoom();
    const densityFactor = interpolateZoomStops(zoom, DENSITY_ZOOM_STOPS);
    const minimum = mobile ? MOBILE_MIN_PARTICLES : DESKTOP_MIN_PARTICLES;
    const maximum = Math.round(
      (mobile ? MOBILE_MAX_PARTICLES : DESKTOP_MAX_PARTICLES) * densityFactor
    );
    const areaPerParticle = mobile
      ? MOBILE_AREA_PER_PARTICLE
      : DESKTOP_AREA_PER_PARTICLE;
    const reducedMotionFactor = this.reducedMotion ? 0.62 : 1;
    const baseParticleCount = clamp(
      (area / areaPerParticle) * densityFactor,
      minimum,
      maximum
    );
    const particleCount = Math.round(baseParticleCount * reducedMotionFactor);
    const trailPointCount = this.reducedMotion
      ? Math.round(
          interpolateZoomStops(zoom, REDUCED_MOTION_TRAIL_ZOOM_STOPS)
        )
      : mobile
        ? Math.round(interpolateZoomStops(zoom, MOBILE_TRAIL_ZOOM_STOPS))
        : Math.round(interpolateZoomStops(zoom, DESKTOP_TRAIL_ZOOM_STOPS));

    return { particleCount, trailPointCount };
  }

  private ensureParticleLayout(): void {
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
      this.seedAllParticles();
    } else if (this.reducedMotion) {
      this.seedAllParticles();
    }

    this.viewportDirty = false;
  }

  private seedAllParticles(): void {
    for (let index = 0; index < this.particleCount; index++) {
      this.respawnParticle(index);
    }

    this.staticTrailsDirty = false;
  }

  private respawnParticle(index: number): void {
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

    if (!found && !field.isGlobal) {
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

    if (!found && field.isGlobal) {
      this.longitudes[index] = Number.NaN;
      this.latitudes[index] = Number.NaN;
      this.ages[index] = 1;
      this.maximumAges[index] = 0;
      return;
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
          this.coordinateScratch
        )
      ) {
        historyLongitude = this.coordinateScratch.longitude;
        historyLatitude = this.coordinateScratch.latitude;
      }
    }

    if (this.sampleVector(latitude, longitude)) {
      this.particleSpeeds[index] = this.currentVector.speed;
    }
  }

  private simulate(elapsedSeconds: number): void {
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
          this.coordinateScratch
        )
      ) {
        this.respawnParticle(index);
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

  private simulatePreviousPopulation(elapsedSeconds: number): void {
    const map = this.map;
    const population = this.previousPopulation;

    if (!map || !population) return;

    const container = map.getContainer();
    for (let index = 0; index < population.particleCount; index++) {
      const longitude = population.longitudes[index];
      const latitude = population.latitudes[index];
      if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) continue;

      const projected = map.project([longitude, latitude]);
      const outsideViewport =
        projected.x < -PARTICLE_VIEWPORT_MARGIN ||
        projected.y < -PARTICLE_VIEWPORT_MARGIN ||
        projected.x > container.clientWidth + PARTICLE_VIEWPORT_MARGIN ||
        projected.y > container.clientHeight + PARTICLE_VIEWPORT_MARGIN;
      population.ages[index] += elapsedSeconds;

      if (
        population.ages[index] >= population.maximumAges[index] ||
        outsideViewport ||
        this.getCoverageFade(longitude, latitude, population.field) <= 0 ||
        !this.advectCoordinateWithField(
          population.field,
          longitude,
          latitude,
          elapsedSeconds,
          this.coordinateScratch,
          this.previousVector
        )
      ) {
        population.longitudes[index] = Number.NaN;
        population.latitudes[index] = Number.NaN;
        continue;
      }

      const historyOffset = index * population.trailPointCount;
      for (let point = population.trailPointCount - 1; point > 0; point--) {
        population.historyLongitudes[historyOffset + point] =
          population.historyLongitudes[historyOffset + point - 1];
        population.historyLatitudes[historyOffset + point] =
          population.historyLatitudes[historyOffset + point - 1];
      }

      population.longitudes[index] = this.coordinateScratch.longitude;
      population.latitudes[index] = this.coordinateScratch.latitude;
      population.historyLongitudes[historyOffset] =
        this.coordinateScratch.longitude;
      population.historyLatitudes[historyOffset] = this.coordinateScratch.latitude;
      population.particleSpeeds[index] = this.previousVector.speed;
    }
  }

  private advectCoordinate(
    longitude: number,
    latitude: number,
    elapsedSeconds: number,
    target: MutableCoordinate
  ): boolean {
    const field = this.field;

    if (!field) return false;
    return this.advectCoordinateWithField(
      field,
      longitude,
      latitude,
      elapsedSeconds,
      target,
      this.currentVector
    );
  }

  private advectCoordinateWithField(
    field: WindVectorField,
    longitude: number,
    latitude: number,
    elapsedSeconds: number,
    target: MutableCoordinate,
    vector: MutableWindVector
  ): boolean {
    const map = this.map;

    if (!map || !field.sample(latitude, longitude, vector)) return false;

    const speed = vector.speed;

    if (speed < 0.05) {
      target.longitude = longitude;
      target.latitude = latitude;
      return true;
    }

    const eastwardUnit = vector.eastwardFlow / speed;
    const northwardUnit = vector.northwardFlow / speed;
    const latitudeCosine = Math.max(
      0.12,
      Math.cos((latitude * Math.PI) / 180)
    );
    const pixelSpeed = clamp(speed * 1.02, 0.45, 44);
    if (map.getProjection()?.type === "globe") {
      const trialKilometers = 8;
      const center = map.getCenter();
      const centerLatitudeCosine = Math.max(
        0.12,
        Math.cos((center.lat * Math.PI) / 180)
      );
      const trialLatitude = clamp(
        center.lat + (northwardUnit * trialKilometers) / 111.32,
        -85.05112878,
        85.05112878
      );
      const trialLongitude =
        center.lng +
        (eastwardUnit * trialKilometers) /
          (111.32 * centerLatitudeCosine);
      const start = map.project(center);
      const trial = map.project([trialLongitude, trialLatitude]);
      const projectedDistance = Math.hypot(trial.x - start.x, trial.y - start.y);
      if (!Number.isFinite(projectedDistance) || projectedDistance < 0.01) {
        return false;
      }
      // A particle-local screen-distance denominator collapses through
      // foreshortening at the globe limb and creates a very large geographic
      // step. Calibrating at the visible globe centre keeps the stylistic
      // screen speed well-conditioned while natural perspective is allowed to
      // shorten trails toward the horizon.
      const travelKilometers =
        (pixelSpeed * elapsedSeconds * trialKilometers) / projectedDistance;
      target.latitude =
        latitude + (northwardUnit * travelKilometers) / 111.32;
      target.longitude = wrapLongitude(
        longitude +
          (eastwardUnit * travelKilometers) / (111.32 * latitudeCosine)
      );
    } else {
      const metersPerPixel =
        (156543.03392 * latitudeCosine) / 2 ** map.getZoom();
      const travelKilometers =
        (pixelSpeed * metersPerPixel * elapsedSeconds) / 1000;
      target.latitude =
        latitude + (northwardUnit * travelKilometers) / 111.32;
      target.longitude = wrapLongitude(
        longitude +
          (eastwardUnit * travelKilometers) / (111.32 * latitudeCosine)
      );
    }

    return (
      Number.isFinite(target.latitude) &&
      Number.isFinite(target.longitude) &&
      Math.abs(target.latitude) <= 85.05112878
    );
  }

  private sampleVector(latitude: number, longitude: number): boolean {
    const field = this.field;

    if (!field || !field.sample(latitude, longitude, this.currentVector)) {
      return false;
    }

    return true;
  }

  private getCoverageFade(
    longitude: number,
    latitude: number,
    field: WindVectorField
  ): number {
    if (field.isGlobal) {
      return Math.abs(latitude) <= 85.05112878 ? 1 : 0;
    }
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

    if (!field) return 0;

    const transition = this.previousPopulation
      ? smoothstep(
          0,
          1,
          (now - this.fieldTransitionStartedAt) / FIELD_TRANSITION_MS
        )
      : 1;
    const previous = this.previousPopulation;
    const currentCapacity =
      this.particleCount * Math.max(0, this.trailPointCount - 1) * 6 * 7;
    const previousCapacity = previous
      ? previous.particleCount *
        Math.max(0, previous.trailPointCount - 1) *
        6 *
        7
      : 0;
    const requiredCapacity = currentCapacity + previousCapacity;
    if (this.vertices.length < requiredCapacity) {
      this.vertices = new Float32Array(requiredCapacity);
    }

    let offset = this.appendPopulationVertices(
      {
        field,
        particleCount: this.particleCount,
        trailPointCount: this.trailPointCount,
        longitudes: this.longitudes,
        latitudes: this.latitudes,
        ages: this.ages,
        maximumAges: this.maximumAges,
        particleSpeeds: this.particleSpeeds,
        historyLongitudes: this.historyLongitudes,
        historyLatitudes: this.historyLatitudes,
      },
      transition,
      0
    );

    if (previous && transition < 1) {
      offset = this.appendPopulationVertices(previous, 1 - transition, offset);
    } else if (previous) {
      previous.field.dispose?.();
      this.previousPopulation = null;
    }

    return offset / 7;
  }

  private appendPopulationVertices(
    population: WindParticlePopulation,
    populationAlpha: number,
    initialOffset: number
  ): number {
    let offset = initialOffset;

    for (let particle = 0; particle < population.particleCount; particle++) {
      const lifeFade = Math.min(
        smoothstep(0, 0.4, population.ages[particle]),
        smoothstep(
          0,
          0.75,
          population.maximumAges[particle] - population.ages[particle]
        )
      );
      const historyOffset = particle * population.trailPointCount;
      const speed = population.particleSpeeds[particle];

      for (let point = 0; point < population.trailPointCount - 1; point++) {
        const startIndex = historyOffset + point;
        const endIndex = startIndex + 1;
        const startLongitude = population.historyLongitudes[startIndex];
        const startLatitude = population.historyLatitudes[startIndex];
        const endLongitude = population.historyLongitudes[endIndex];
        const endLatitude = population.historyLatitudes[endIndex];

        if (
          !Number.isFinite(startLongitude) ||
          !Number.isFinite(startLatitude) ||
          !Number.isFinite(endLongitude) ||
          !Number.isFinite(endLatitude)
        ) {
          continue;
        }

        let projectedEndLongitude = endLongitude;
        const longitudeDelta = projectedEndLongitude - startLongitude;
        if (longitudeDelta > 180) projectedEndLongitude -= 360;
        else if (longitudeDelta < -180) projectedEndLongitude += 360;

        const startTrailFade =
          (1 - point / population.trailPointCount) ** 1.35;
        const endTrailFade =
          (1 - (point + 1) / population.trailPointCount) ** 1.35;
        const startAlpha =
          populationAlpha *
          lifeFade *
          startTrailFade *
          this.getCoverageFade(
            startLongitude,
            startLatitude,
            population.field
          );
        const endAlpha =
          populationAlpha *
          lifeFade *
          endTrailFade *
          this.getCoverageFade(endLongitude, endLatitude, population.field);
        const startX = longitudeToMercatorX(startLongitude);
        const startY = latitudeToMercatorY(startLatitude);
        const endX = longitudeToMercatorX(projectedEndLongitude);
        const endY = latitudeToMercatorY(endLatitude);

        offset = this.writeTrailVertex(offset, startX, startY, endX, endY, startAlpha, -1, speed);
        offset = this.writeTrailVertex(offset, startX, startY, endX, endY, startAlpha, 1, speed);
        offset = this.writeTrailVertex(offset, endX, endY, startX, startY, endAlpha, -1, speed);
        offset = this.writeTrailVertex(offset, endX, endY, startX, startY, endAlpha, -1, speed);
        offset = this.writeTrailVertex(offset, startX, startY, endX, endY, startAlpha, 1, speed);
        offset = this.writeTrailVertex(offset, endX, endY, startX, startY, endAlpha, 1, speed);
      }
    }

    return offset;
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
    if (!this.vertexBuffer) return;

    let windProgram = this.programs.get(options.shaderData.variantName);
    if (!windProgram) {
      windProgram = createProgram(gl, options.shaderData);
      this.programs.set(options.shaderData.variantName, windProgram);
    }

    const basemapOpacity: Record<Basemap, number> = {
      terrain: 1.06,
      satellite: 0.98,
    };
    const zoom = this.map?.getZoom() ?? 0;
    const opacity =
      LAYER_VISUAL_STRENGTHS.windParticle *
      basemapOpacity[this.basemap] *
      interpolateZoomStops(zoom, OPACITY_ZOOM_STOPS) *
      this.coverageAmount;
    const depthTestWasEnabled = gl.isEnabled(gl.DEPTH_TEST);
    const cullFaceWasEnabled = gl.isEnabled(gl.CULL_FACE);

    gl.useProgram(windProgram.program);
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
    gl.enableVertexAttribArray(windProgram.positionAttribute);
    gl.enableVertexAttribArray(windProgram.otherPositionAttribute);
    gl.enableVertexAttribArray(windProgram.alphaAttribute);
    gl.enableVertexAttribArray(windProgram.sideAttribute);
    gl.enableVertexAttribArray(windProgram.speedAttribute);
    gl.vertexAttribPointer(
      windProgram.positionAttribute,
      2,
      gl.FLOAT,
      false,
      28,
      0
    );
    gl.vertexAttribPointer(
      windProgram.otherPositionAttribute,
      2,
      gl.FLOAT,
      false,
      28,
      8
    );
    gl.vertexAttribPointer(windProgram.alphaAttribute, 1, gl.FLOAT, false, 28, 16);
    gl.vertexAttribPointer(windProgram.sideAttribute, 1, gl.FLOAT, false, 28, 20);
    gl.vertexAttribPointer(windProgram.speedAttribute, 1, gl.FLOAT, false, 28, 24);
    gl.uniformMatrix4fv(
      windProgram.projectionMatrixUniform,
      false,
      options.defaultProjectionData.mainMatrix as Float32Array
    );
    gl.uniformMatrix4fv(
      windProgram.projectionFallbackMatrixUniform,
      false,
      options.defaultProjectionData.fallbackMatrix as Float32Array
    );
    gl.uniform4f(
      windProgram.projectionTileMercatorUniform,
      ...options.defaultProjectionData.tileMercatorCoords
    );
    gl.uniform4f(
      windProgram.projectionClippingPlaneUniform,
      ...options.defaultProjectionData.clippingPlane
    );
    gl.uniform1f(
      windProgram.projectionTransitionUniform,
      options.defaultProjectionData.projectionTransition
    );
    gl.uniform2f(
      windProgram.viewportUniform,
      gl.drawingBufferWidth,
      gl.drawingBufferHeight
    );
    gl.uniform1f(
      windProgram.widthScaleUniform,
      interpolateZoomStops(zoom, WIDTH_ZOOM_STOPS)
    );
    gl.uniform1f(
      windProgram.terrainMixUniform,
      this.basemap === "terrain" ? 1 : 0
    );
    gl.uniform1f(windProgram.opacityUniform, opacity);
    gl.drawArrays(gl.TRIANGLES, 0, vertexCount);
    gl.disableVertexAttribArray(windProgram.positionAttribute);
    gl.disableVertexAttribArray(windProgram.otherPositionAttribute);
    gl.disableVertexAttribArray(windProgram.alphaAttribute);
    gl.disableVertexAttribArray(windProgram.sideAttribute);
    gl.disableVertexAttribArray(windProgram.speedAttribute);
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
