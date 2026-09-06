import type { JourneyPlan, JourneyProfile } from "../types/route";
import { isoFromLocal, localInputValue } from "../services/journeyPresentation";

interface JourneySettingsProps {
  profile: JourneyProfile;
  plan: JourneyPlan;
  onProfileChange: (profile: JourneyProfile) => void;
  onPlanChange: (plan: JourneyPlan) => void;
  onBack: () => void;
}

export default function JourneySettings({ profile, plan, onProfileChange, onPlanChange, onBack }: JourneySettingsProps) {
  return <section className="journey-settings-view" aria-labelledby="journey-settings-title">
    <div className="journey-subview-heading">
      <button type="button" className="journey-back-button" onClick={onBack}>← Journey</button>
      <div><p className="section-kicker">Journey estimate</p><h2 id="journey-settings-title">Journey settings</h2></div>
    </div>
    <div className="route-form-grid journey-settings-grid">
      <label><span>Activity</span><strong>Hiking / walking</strong></label>
      <label><span>Pace</span><select value={profile.pace} onChange={(event) => onProfileChange({ ...profile, pace: event.target.value as JourneyProfile["pace"] })}><option value="relaxed">Relaxed</option><option value="normal">Normal</option><option value="fast">Fast</option></select></label>
      <label><span>Party</span><select value={profile.party} onChange={(event) => onProfileChange({ ...profile, party: event.target.value as JourneyProfile["party"] })}><option value="solo">Solo</option><option value="group">Group</option></select></label>
      <label><span>Load</span><select value={profile.load} onChange={(event) => onProfileChange({ ...profile, load: event.target.value as JourneyProfile["load"] })}><option value="light">Light / day pack</option><option value="heavy">Heavy / overnight</option></select></label>
      <label><span>Planned breaks</span><select value={profile.plannedBreakMinutes} onChange={(event) => onProfileChange({ ...profile, plannedBreakMinutes: Number(event.target.value) })}><option value={0}>Minimal / none</option><option value={30}>Normal · 30 min</option><option value={60}>Generous · 60 min</option></select></label>
      <label><span>Plan from</span><select value={plan.mode} onChange={(event) => onPlanChange({ ...plan, mode: event.target.value as JourneyPlan["mode"] })}><option value="profile">Selected profile</option><option value="target-duration">Target duration</option><option value="target-finish">Target finish</option></select></label>
      <label className="route-form-wide"><span>Departure</span><input type="datetime-local" value={localInputValue(plan.departureTime)} onChange={(event) => onPlanChange({ ...plan, departureTime: isoFromLocal(event.target.value, plan.departureTime) })} /></label>
      {plan.mode === "target-duration" && <label className="route-form-wide"><span>Target total hours</span><input type="number" min="0.5" max="48" step="0.25" value={(plan.targetDurationMinutes / 60).toFixed(2)} onChange={(event) => onPlanChange({ ...plan, targetDurationMinutes: Number(event.target.value) * 60 })} /></label>}
      {plan.mode === "target-finish" && <label className="route-form-wide"><span>Target finish</span><input type="datetime-local" value={localInputValue(plan.targetFinishTime)} onChange={(event) => onPlanChange({ ...plan, targetFinishTime: isoFromLocal(event.target.value, plan.targetFinishTime) })} /></label>}
    </div>
  </section>;
}