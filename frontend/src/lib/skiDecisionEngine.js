/**
 * Avoriaz Ski Decision Engine — JavaScript port of decision_engine.py
 * Runs entirely in the browser, no backend needed.
 */

import {
  AVORIAZ_RUNS,
  getWeather,
  getAllConditions,
  getRunConditions,
  computeSnowScore,
  computeCrowdLevel,
  computeEnjoyment,
  diurnalTemp,
} from './skiSimulation.js';

// ── Difficulty filter ─────────────────────────────────────────────────────────
function difficultyFilter(level) {
  const map = {
    beginner:     ['green', 'blue'],
    intermediate: ['blue', 'red'],
    advanced:     ['red', 'black'],
    all:          ['green', 'blue', 'red', 'black'],
  };
  return map[level] || map.all;
}

// ── Recommendation reason ─────────────────────────────────────────────────────
function buildReason(rc) {
  const r = rc.run;
  const parts = [];
  if (rc.snow_surface === 'powder') parts.push('fresh powder');
  else if (rc.snow_surface === 'groomed / firm') parts.push('excellent groomed surface');
  else if (rc.snow_surface === 'softening') parts.push('pleasantly soft spring snow');

  if (rc.crowd_label === 'Low') parts.push('virtually empty piste');
  else if (rc.crowd_label === 'Medium') parts.push('manageable crowds');

  if ((r.orientation === 'N' || r.orientation === 'NE') && rc.snow_score > 72)
    parts.push('N-facing wall locks in cold dry snow');

  if (r.flow_score > 0.82) parts.push('superb rhythm & flow');
  if (r.altitude_m >= 2100) parts.push('high-altitude = coldest snow in sector');

  if (!parts.length)
    parts.push(`${rc.snow_surface} conditions with ${rc.crowd_label.toLowerCase()} crowds`);

  return parts.slice(0, 3).join('; ').replace(/^./, c => c.toUpperCase()) + '.';
}

function addDate(dt, days) {
  const d = new Date(dt);
  d.setDate(d.getDate() + days);
  return d;
}
function addMinutes(dt, mins) {
  return new Date(dt.getTime() + mins * 60000);
}

// ── get_top_3 ─────────────────────────────────────────────────────────────────
export function getTop3(dt, prefs = {}, tourists = 1.0, seed = 42) {
  const allowed = difficultyFilter(prefs.difficulty_level);
  const all = getAllConditions(dt, tourists, { prioritize_snow: prefs.prioritize_snow ?? 0.5, avoid_crowds: prefs.avoid_crowds ?? 0.5 }, seed);
  let filtered = all.filter(rc => allowed.includes(rc.run.difficulty));
  if (filtered.length < 3) filtered = all;
  return filtered.slice(0, 3).map(rc => ({ ...rc, recommendation_reason: buildReason(rc) }));
}

// ── get_time_strategy ─────────────────────────────────────────────────────────
export function getTimeStrategy(dt, prefs = {}, tourists = 1.0, seed = 42) {
  const allowed = difficultyFilter(prefs.difficulty_level);
  const prefsDict = { prioritize_snow: prefs.prioritize_snow ?? 0.5, avoid_crowds: prefs.avoid_crowds ?? 0.5 };
  const slots = [
    [9,  'Morning',   '09:00–11:30', 'First tracks: snow at its best, lifts filling up — move fast.'],
    [12, 'Midday',    '12:00–13:30', 'Lunch exodus empties the slopes — great window for power laps.'],
    [15, 'Afternoon', '14:00–16:30', 'Sun softens S/W faces; retreat to N-facing or high altitude.'],
  ];
  return slots.map(([hour, slot, timeRange, rationale]) => {
    const slotDt = new Date(dt);
    slotDt.setHours(hour, 0, 0, 0);
    const all = getAllConditions(slotDt, tourists, prefsDict, seed + hour);
    let filtered = all.filter(rc => allowed.includes(rc.run.difficulty));
    if (!filtered.length) filtered = all;
    const top = filtered.filter(rc => rc.crowd_label !== 'High').slice(0, 3)
      .map(rc => ({ ...rc, recommendation_reason: buildReason(rc) }));
    const avoid = filtered.filter(rc => rc.crowd_label === 'High' || ['slushy', 'icy / wind-packed'].includes(rc.snow_surface)).slice(0, 3);
    return { slot, time_range: timeRange, rationale, top_runs: top, avoid_runs: avoid };
  });
}

// ── generate_day_plan ─────────────────────────────────────────────────────────
function lapMinutes(run) {
  const descentMin = Math.round(run.length_km / 0.6 * 6);
  const liftMin = (run.primary_lift.includes('Express') || run.primary_lift.includes('Gondola')) ? 8 : 5;
  return descentMin + liftMin;
}

export function generateDayPlan(startDt, prefs = {}, tourists = 1.0, seed = 42) {
  const allowed = difficultyFilter(prefs.difficulty_level);
  const prefsDict = { prioritize_snow: prefs.prioritize_snow ?? 0.5, avoid_crowds: prefs.avoid_crowds ?? 0.5 };
  const endDay = new Date(startDt); endDay.setHours(16, 30, 0, 0);
  let current = new Date(startDt); current.setMinutes(0, 0, 0);

  const slots = [];
  let totalKm = 0, totalRuns = 0, prevRunName = '', lunchDone = false;

  while (current < endDay) {
    if (!lunchDone && current.getHours() >= 12) {
      const lunchEnd = addMinutes(current, 60);
      const placeholder = AVORIAZ_RUNS[0];
      slots.push({
        start_time: current.toISOString(),
        end_time: lunchEnd.toISOString(),
        run: placeholder,
        run_name: 'Lunch Break',
        run_difficulty: placeholder.difficulty,
        action: 'LUNCH BREAK',
        tip: 'Head to Alpage restaurant — mountain views, quick service.',
        conditions: getRunConditions(placeholder, current, tourists, prefsDict, seed),
        enjoyment_score: 0,
        snow_surface: '',
        crowd_label: '',
      });
      current = lunchEnd;
      lunchDone = true;
      continue;
    }

    const all = getAllConditions(current, tourists, prefsDict, seed + current.getHours());
    let filtered = all.filter(rc => allowed.includes(rc.run.difficulty));
    if (!filtered.length) filtered = all;
    let options = filtered.filter(rc => rc.run.name !== prevRunName);
    if (!options.length) options = filtered;
    const best = options[0];

    const lap = lapMinutes(best.run);
    const runEnd = addMinutes(current, lap);
    let tip = buildReason(best);
    if (current.getHours() < 10) tip = 'First tracks! ' + tip;

    slots.push({
      start_time: current.toISOString(),
      end_time: runEnd.toISOString(),
      run: best.run,
      run_name: best.run.name,
      run_difficulty: best.run.difficulty,
      action: 'SKI',
      tip,
      conditions: best,
      enjoyment_score: best.enjoyment_score,
      snow_surface: best.snow_surface,
      crowd_label: best.crowd_label,
    });

    totalKm += best.run.length_km;
    totalRuns++;
    prevRunName = best.run.name;
    current = runEnd;
    if (totalRuns > 14) break;
  }

  const skiSlots = slots.filter(s => s.action === 'SKI');
  const best = skiSlots.reduce((a, b) => a.enjoyment_score > b.enjoyment_score ? a : b, skiSlots[0] || slots[0]);
  return {
    date: startDt.toISOString(),
    slots,
    total_runs: totalRuns,
    total_km: Math.round(totalKm * 10) / 10,
    highlights: skiSlots.length
      ? `Start on ${skiSlots[0].run_name} for first tracks, target ${best.run_name} for peak enjoyment.`
      : '',
  };
}

// ── get_hidden_gems ───────────────────────────────────────────────────────────
export function getHiddenGems(dt, prefs = {}, tourists = 1.0, seed = 42, topN = 3) {
  const allowed = difficultyFilter(prefs.difficulty_level);
  const prefsDict = { prioritize_snow: prefs.prioritize_snow ?? 0.5, avoid_crowds: prefs.avoid_crowds ?? 0.5 };
  const all = getAllConditions(dt, tourists, prefsDict, seed);
  const gems = [];
  for (const rc of all) {
    if (!allowed.includes(rc.run.difficulty)) continue;
    if (rc.run.popularity >= 0.55) continue;
    if (rc.enjoyment_score < 63) continue;
    const alpha = rc.enjoyment_score / (rc.run.popularity * 100 + 1e-6);
    gems.push({
      run: rc.run,
      conditions: rc,
      why_hidden: `Popularity index ${Math.round(rc.run.popularity * 100)}% — far below resort average. Requires ${rc.run.primary_lift} (less-visited corridor).`,
      why_excellent: `Enjoyment ${rc.enjoyment_score.toFixed(0)}/100 driven by: ${rc.snow_surface} snow, ${rc.crowd_label.toLowerCase()} crowds, flow score ${Math.round(rc.run.flow_score * 100)}%.`,
      alpha_score: Math.round(alpha * 100) / 100,
    });
  }
  gems.sort((a, b) => b.alpha_score - a.alpha_score);
  return gems.slice(0, topN);
}

// ── sensitivity_analysis ─────────────────────────────────────────────────────
export function sensitivityAnalysis(dt, tourists = 1.0, seed = 42) {
  const [baseTemp, snowfall, cloudCover] = getWeather(dt);
  const baseScores = AVORIAZ_RUNS.map(run => {
    const [sn] = computeSnowScore(run, dt, snowfall, baseTemp, cloudCover, seed);
    const [cr] = computeCrowdLevel(run, dt, tourists, seed);
    return computeEnjoyment(run, sn, cr);
  });
  const baseAvg = baseScores.reduce((a, b) => a + b, 0) / baseScores.length;

  // 1. Temperature +5°C
  const tempScores = AVORIAZ_RUNS.map(run => {
    const [sn] = computeSnowScore(run, dt, snowfall, baseTemp + 5, cloudCover, seed);
    const [cr] = computeCrowdLevel(run, dt, tourists, seed);
    return computeEnjoyment(run, sn, cr);
  });
  const tempAvg = tempScores.reduce((a, b) => a + b, 0) / tempScores.length;

  // 2. Tourist ×1.5
  const crowdScores = AVORIAZ_RUNS.map(run => {
    const [sn] = computeSnowScore(run, dt, snowfall, baseTemp, cloudCover, seed);
    const [cr] = computeCrowdLevel(run, dt, tourists * 1.5, seed);
    return computeEnjoyment(run, sn, cr);
  });
  const crowdAvg = crowdScores.reduce((a, b) => a + b, 0) / crowdScores.length;

  // 3. 5-day-old snow
  const oldDt = addDate(dt, 5);
  const ageScores = AVORIAZ_RUNS.map(run => {
    const [sn] = computeSnowScore(run, oldDt, 0, baseTemp, cloudCover, seed);
    const [cr] = computeCrowdLevel(run, dt, tourists, seed);
    return computeEnjoyment(run, sn, cr);
  });
  const ageAvg = ageScores.reduce((a, b) => a + b, 0) / ageScores.length;

  const r = (v) => Math.round(v * 10) / 10;
  const results = [
    { variable: 'Temperature (+5 °C)', base_avg: r(baseAvg), shocked_avg: r(tempAvg), delta: r(tempAvg - baseAvg), pct_change: r((tempAvg - baseAvg) / baseAvg * 100), interpretation: 'A 5 °C warmer day softens/slushes S/SW-facing runs significantly. N-facing high-altitude runs buffered. Most damaging variable for snow quality.' },
    { variable: 'Tourist influx (×1.5)', base_avg: r(baseAvg), shocked_avg: r(crowdAvg), delta: r(crowdAvg - baseAvg), pct_change: r((crowdAvg - baseAvg) / baseAvg * 100), interpretation: '50% more visitors crushes popular runs. Chavannes Express queues cascade across the whole mountain. Remote runs (Fornet, Chamois) least affected.' },
    { variable: 'Snow age (5 days, no new snow)', base_avg: r(baseAvg), shocked_avg: r(ageAvg), delta: r(ageAvg - baseAvg), pct_change: r((ageAvg - baseAvg) / baseAvg * 100), interpretation: '5 stale days hit lower-altitude S-facing runs hardest (Lindarets, Super Morzine). High-altitude N-facing runs degrade slowest — best late-season insurance.' },
  ];
  results.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
  return results;
}

// ── stress_test ───────────────────────────────────────────────────────────────
function buildStressConditions(dt, touristMult, tempOffset, snowOverride, seedOffset, seed, prefs) {
  const [baseTemp, snowfall, cloudCover] = getWeather(dt);
  const prefsDict = { prioritize_snow: prefs.prioritize_snow ?? 0.5, avoid_crowds: prefs.avoid_crowds ?? 0.5 };
  const useDt = snowOverride !== null ? addDate(dt, 7) : dt;
  const useSnow = snowOverride !== null ? 0 : snowfall;
  return AVORIAZ_RUNS.map(run => {
    const [sn, surf] = computeSnowScore(run, useDt, useSnow, baseTemp + tempOffset, cloudCover, seed);
    const [cr, cl] = computeCrowdLevel(run, dt, touristMult, seed);
    const enj = computeEnjoyment(run, sn, cr, prefsDict);
    return { run, snow_score: sn, crowd_level: cr, crowd_label: cl, enjoyment_score: enj, temperature_c: Math.round(diurnalTemp(baseTemp + tempOffset, dt.getHours()) * 10) / 10, snow_surface: surf, timestamp: dt.toISOString(), recommendation_reason: '' };
  }).sort((a, b) => b.enjoyment_score - a.enjoyment_score);
}

export function stressTest(dt, prefs = {}, seed = 42) {
  const warm  = buildStressConditions(dt, 1.0, +6, null, 0, seed, prefs);
  const crowd = buildStressConditions(dt, 1.6,  0, null, 0, seed, prefs);
  const dry   = buildStressConditions(dt, 1.0,  0, 0,    0, seed, prefs);
  return [
    { name:'A — Warm Spell (+6 °C)', description:'Unseasonably warm day. S/W-facing runs become slushy by 11:00.', top_3:warm.slice(0,3), worst_3:warm.slice(-3), key_insight:'Migrate entirely to N-facing high-altitude runs (Chamois, La Schuss, Combe de Chavannes). Start by 08:30. Avoid Lindarets & Super Morzine all day.' },
    { name:'B — Peak Influx (×1.6 tourists)', description:'Sold-out changeover Saturday. Chavannes Express queue >30 min.', top_3:crowd.slice(0,3), worst_3:crowd.slice(-3), key_insight:'Fornet T-Bar and Machon Lift are capacity-limited on the demand side — they stay quiet even when the resort is full. Chamois and Fornet become sanctuary runs. Avoid Prolys, Arare, Lindarets.' },
    { name:'C — Snow Drought (7 days no new snow)', description:'Late-season icy conditions below 1900m. Top-up runs only.', top_3:dry.slice(0,3), worst_3:dry.slice(-3), key_insight:'Altitude becomes the dominant variable. Chamois (2200m N) retains the best pack. Stade Slalom race-course grooming compensates for natural snow loss. Super Morzine and Lindarets become unpleasant — icy ruts, no recovery.' },
  ];
}

// ── decision_rules ────────────────────────────────────────────────────────────
export function decisionRules(dt) {
  const [, snowfall] = getWeather(dt);
  const rules = [
    { condition:'Time > 12:00  AND  slope orientation = S or SW', action:'Avoid Lindarets Valley, Combe du Machon, Super Morzine', rationale:'S/SW faces accumulate >3.5 pts of sun damage per hour after noon. Snow transitions from softening → slushy → icy ruts within 90 min.' },
    { condition:'Crowd level = High  AND  primary lift = Chavannes Express', action:'Switch to Fornet T-Bar or Machon Lift corridor', rationale:'Chavannes Express is the mountain\'s single choke point. Fornet and Machon serve independent terrain with much lower capacity pressure.' },
    { condition:'Hour ∈ [09:00, 10:00]  AND  snowfall last 24 h > 5 cm', action:'Prioritise La Schuss or Chamois before grooming opens', rationale:'First 90 min after overnight dump = best powder window. N-facing steep terrain (La Schuss) holds untracked snow longest.' },
    { condition:'Temperature at 2000m > 0 °C  (spring warmth)', action:'Ski only N-facing runs above 2000m; finish by 13:00', rationale:'0 °C isotherm at altitude triggers rapid snow softening on any sun-exposed face. N-facing runs at 2100m+ stay below freezing 2–3 h longer.' },
    { condition:'Day = Saturday or Sunday  AND  hour ∈ [10:00, 11:30]', action:'Use Fornet T-Bar; avoid Crêtes Chairlift and Chavannes Express', rationale:'Weekend changeover floods Avoriaz lifts. Fornet T-Bar serves Fornet run (low popularity 0.28) and remains essentially queue-free even on peak days.' },
    { condition:'Enjoyment score drops below 60 on chosen run', action:'Switch to Chamois or Fornet — resort\'s most reliable performers', rationale:'Model shows Chamois and Fornet maintain >65 enjoyment across 87% of simulated conditions due to altitude, orientation, and low footfall.' },
    { condition:'Midday lull (12:00–13:30)', action:'Hit Mossettes or Crêtes — empty and still good snow', rationale:'Crowd model shows 35–40% drop in on-piste density during lunch hour. Mossettes (W-facing) not yet hit by afternoon sun; Crêtes maintains E-facing firmness.' },
  ];
  if (snowfall >= 10) {
    rules.unshift({ condition:`Snowfall last 24h ≥ ${Math.round(snowfall)} cm  (TODAY)`, action:'GO HIGH IMMEDIATELY — powder alarm active', rationale:`${Math.round(snowfall)} cm of fresh snow detected. First-tracks window on La Schuss, Chamois, Combe de Chavannes opens at 09:00. Move before 10:30.` });
  }
  return rules;
}
