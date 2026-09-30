function localFormatter(timeZone?: string): Intl.DateTimeFormat {
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short", hour: "2-digit", minute: "2-digit",
    timeZoneName: "short", ...(timeZone ? { timeZone } : {}),
  });
}

export function accumulationIntervalLabel(
  step: { accumulationStart?: string; accumulationEnd?: string },
  timeZone?: string
): string {
  if (!step.accumulationStart || !step.accumulationEnd) return "Interval unavailable";
  return `Interval ${localFormatter(timeZone).formatRange(
    new Date(step.accumulationStart), new Date(step.accumulationEnd)
  )}`;
}
