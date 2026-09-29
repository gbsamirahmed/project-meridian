import {
  cpSync,
  createReadStream,
  existsSync,
  mkdirSync,
  readFileSync,
  realpathSync,
  statSync,
} from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { resolveMeridianDataPath } from "../meridian_paths.mjs";

export const GFS_BROWSER_PREFIX = "/weather/gfs";
const RUN_NAME = /^[0-9]{8}T(?:00|06|12|18)Z(?:-fields-[0-9a-f]{12})?$/;
const REQUIRED_FIELDS = new Set([
  "precipitation",
  "cloud_cover",
  "wind_10m",
  "temperature_2m",
  "pressure_msl",
  "gust_surface",
  "visibility_surface",
  "freezing_level",
  "highest_freezing_level",
  "cloud_ceiling",
]);

function isWithin(candidate, parent) {
  const relative = path.relative(parent, candidate);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== "..");
}

export function resolveGfsPublicationRoot(options = {}) {
  const dataRoot = resolveMeridianDataPath([], options);
  const publicationRoot = resolveMeridianDataPath(["derived", "weather", "gfs"], options);
  if (existsSync(publicationRoot)) {
    const realDataRoot = realpathSync(dataRoot);
    const realPublicationRoot = realpathSync(publicationRoot);
    if (!isWithin(realPublicationRoot, realDataRoot)) {
      throw new Error("Authoritative GFS publication escapes MERIDIAN_DATA_ROOT");
    }
    return realPublicationRoot;
  }
  return publicationRoot;
}

export function readGfsPublication(publicationRoot = resolveGfsPublicationRoot()) {
  const unresolvedRoot = path.resolve(publicationRoot);
  if (!existsSync(unresolvedRoot) || !statSync(unresolvedRoot).isDirectory()) {
    throw new Error(`Authoritative GFS publication root does not exist: ${unresolvedRoot}`);
  }
  const root = realpathSync(unresolvedRoot);
  if (!statSync(root).isDirectory()) {
    throw new Error(`Authoritative GFS publication root does not exist: ${root}`);
  }
  const latestPath = path.join(root, "latest.json");
  if (!existsSync(latestPath) || !statSync(latestPath).isFile()) {
    throw new Error(`Authoritative GFS catalogue is missing: ${latestPath}`);
  }
  const catalogue = JSON.parse(readFileSync(latestPath, "utf8"));
  const fields = catalogue.fields;
  if (!fields || typeof fields !== "object") {
    throw new Error("Authoritative GFS catalogue has no fields object");
  }
  const fieldNames = new Set(Object.keys(fields));
  if (fieldNames.size !== REQUIRED_FIELDS.size ||
      [...REQUIRED_FIELDS].some((field) => !fieldNames.has(field))) {
    throw new Error("Authoritative GFS catalogue is not the complete ten-field publication");
  }
  const runNames = new Set();
  for (const [field, entry] of Object.entries(fields)) {
    if (!entry || typeof entry !== "object" || entry.timestepCount !== 24 ||
        typeof entry.manifest !== "string") {
      throw new Error(`Invalid GFS catalogue entry for ${field}`);
    }
    const manifest = entry.manifest.replaceAll("\\", "/");
    const segments = manifest.split("/");
    const runName = segments[0];
    if (!RUN_NAME.test(runName) || segments.some((segment) => !segment || segment === "." || segment === "..")) {
      throw new Error(`Unsafe GFS manifest path for ${field}: ${entry.manifest}`);
    }
    const candidateManifestPath = path.resolve(root, ...segments);
    if (!isWithin(candidateManifestPath, root) || !existsSync(candidateManifestPath)) {
      throw new Error(`GFS manifest is unavailable for ${field}: ${entry.manifest}`);
    }
    const manifestPath = realpathSync(candidateManifestPath);
    if (!isWithin(manifestPath, root) || !statSync(manifestPath).isFile()) {
      throw new Error(`GFS manifest escapes the authoritative publication for ${field}`);
    }
    runNames.add(runName);
  }
  if (runNames.size !== 1) {
    throw new Error("Authoritative GFS catalogue must reference one immutable run");
  }
  return { root, latestPath, catalogue, runName: [...runNames][0] };
}

export function resolveGfsRequestPath(requestUrl, publicationRoot = resolveGfsPublicationRoot()) {
  const requestPath = requestUrl.split("?", 1)[0].split("#", 1)[0];
  if (requestPath !== GFS_BROWSER_PREFIX && !requestPath.startsWith(`${GFS_BROWSER_PREFIX}/`)) {
    return null;
  }
  const encoded = requestPath.slice(GFS_BROWSER_PREFIX.length).replace(/^\//, "");
  let decoded;
  try {
    decoded = decodeURIComponent(encoded);
  } catch {
    throw new Error("Malformed GFS publication URL");
  }
  if (!decoded || decoded.includes("\\")) {
    throw new Error("Invalid GFS publication path");
  }
  const segments = decoded.split("/");
  if (segments.some((segment) => !segment || segment === "." || segment === "..")) {
    throw new Error("Unsafe GFS publication path");
  }
  const publication = readGfsPublication(publicationRoot);
  if (decoded !== "latest.json" && segments[0] !== publication.runName) {
    throw new Error("Requested GFS asset is outside the catalogue-selected publication");
  }
  const candidate = path.resolve(publication.root, ...segments);
  if (!isWithin(candidate, publication.root)) {
    throw new Error("Requested GFS asset escapes the publication root");
  }
  if (!existsSync(candidate)) return candidate;
  const realCandidate = realpathSync(candidate);
  if (!isWithin(realCandidate, publication.root)) {
    throw new Error("Requested GFS asset resolves outside the publication root");
  }
  return realCandidate;
}

function contentType(target) {
  if (target.endsWith(".json")) return "application/json; charset=utf-8";
  if (target.endsWith(".png")) return "image/png";
  return "application/octet-stream";
}

export function createGfsPublicationMiddleware({ publicationRoot } = {}) {
  const root = publicationRoot || resolveGfsPublicationRoot();
  return (request, response, next) => {
    const requestPath = request.url?.split("?", 1)[0].split("#", 1)[0];
    if (requestPath !== GFS_BROWSER_PREFIX && !requestPath?.startsWith(`${GFS_BROWSER_PREFIX}/`)) {
      next();
      return;
    }
    try {
      const target = resolveGfsRequestPath(request.url, root);
      if (!target || !existsSync(target) || !statSync(target).isFile()) {
        response.statusCode = 404;
        response.end("GFS publication asset not found");
        return;
      }
      response.statusCode = 200;
      response.setHeader("Content-Type", contentType(target));
      response.setHeader(
        "Cache-Control",
        target.endsWith("latest.json") ? "no-cache" : "public, max-age=31536000, immutable",
      );
      createReadStream(target).on("error", next).pipe(response);
    } catch (error) {
      response.statusCode = 503;
      response.end(`GFS publication unavailable: ${error instanceof Error ? error.message : String(error)}`);
    }
  };
}

export function materializeGfsPublication(destination, { publicationRoot } = {}) {
  const publication = readGfsPublication(publicationRoot || resolveGfsPublicationRoot());
  const target = path.resolve(destination);
  if (existsSync(target)) {
    throw new Error(`Refusing to overwrite existing GFS publication view: ${target}`);
  }
  mkdirSync(target, { recursive: true });
  cpSync(publication.latestPath, path.join(target, "latest.json"));
  cpSync(
    path.join(publication.root, publication.runName),
    path.join(target, publication.runName),
    {
      recursive: true,
      filter: (source) => {
        const realSource = realpathSync(source);
        if (!isWithin(realSource, publication.root)) {
          throw new Error(`Refusing to publish asset outside the authoritative GFS root: ${source}`);
        }
        return true;
      },
    },
  );
  return { target, runName: publication.runName };
}

function main() {
  if (!process.argv.includes("--check")) {
    throw new Error("Use --check to validate the external GFS publication");
  }
  const publication = readGfsPublication();
  process.stdout.write(JSON.stringify({
    browserPrefix: GFS_BROWSER_PREFIX,
    runName: publication.runName,
    fieldCount: Object.keys(publication.catalogue.fields).length,
    timestepCount: 24,
  }, null, 2) + "\n");
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  try {
    main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
