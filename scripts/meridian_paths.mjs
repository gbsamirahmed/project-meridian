import { existsSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const DATA_ROOT_ENV = "MERIDIAN_DATA_ROOT";

export function defaultRepositoryRoot() {
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
}

function isWithin(candidate, parent) {
  const relative = path.relative(parent, candidate);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== "..");
}

export function resolveMeridianDataRoot({
  repositoryRoot = defaultRepositoryRoot(),
  environment = process.env,
  requireExists = true,
} = {}) {
  const repository = path.resolve(repositoryRoot);
  const configured = environment[DATA_ROOT_ENV]?.trim();
  if (configured && !path.isAbsolute(configured)) {
    throw new Error(`${DATA_ROOT_ENV} must be an absolute path, got: ${configured}`);
  }
  const dataRoot = path.resolve(configured || path.join(repository, "..", "meridian-data"));
  if (isWithin(dataRoot, repository)) {
    throw new Error(`Meridian data root must be outside the Git repository: ${dataRoot}`);
  }
  if (requireExists && (!existsSync(dataRoot) || !statSync(dataRoot).isDirectory())) {
    throw new Error(
      `Required Meridian data root does not exist: ${dataRoot}. ` +
      `Set ${DATA_ROOT_ENV} to an existing absolute directory.`,
    );
  }
  return dataRoot;
}

export function resolveMeridianDataPath(parts, options = {}) {
  const dataRoot = resolveMeridianDataRoot(options);
  const candidate = path.resolve(dataRoot, ...parts);
  if (!isWithin(candidate, dataRoot)) {
    throw new Error(`Meridian data path escapes its configured root: ${candidate}`);
  }
  return candidate;
}
