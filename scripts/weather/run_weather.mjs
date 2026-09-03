import { spawn } from "node:child_process";

const configured = process.env.MERIDIAN_PYTHON?.trim();
const command = configured || (process.platform === "win32" ? "py" : "python3");
const prefix = configured || process.platform !== "win32" ? [] : ["-3.12"];
const child = spawn(
  command,
  [...prefix, "scripts/weather/build_gfs_weather.py", ...process.argv.slice(2)],
  { cwd: process.cwd(), stdio: "inherit" }
);
child.on("error", (error) => {
  console.error(`Could not start the weather updater with ${command}: ${error.message}`);
  process.exitCode = 1;
});
child.on("exit", (code, signal) => {
  if (signal) process.exitCode = 130;
  else process.exitCode = code ?? 1;
});
