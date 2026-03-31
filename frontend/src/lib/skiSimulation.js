/**
 * Avoriaz Ski Simulation Engine — JavaScript port of simulation.py
 * Pure math, no dependencies. Runs entirely in the browser.
 */

// ── Seeded PRNG (Mulberry32) ─────────────────────────────────────────────────
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

// Box-Muller normal sample using our seeded PRNG
function normalSample(rng, mean = 0, std = 1) {
  let u, v;
  do { u = rng(); } while (u === 0);
  do { v = rng(); } while (v === 0);
  return mean + std * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

function clip(x, min, max) { return Math.min(Math.max(x, min), max); }

// ── Enumerations ─────────────────────────────────────────────────────────────
export const Difficulty = { GREEN: 'green', BLUE: 'blue', RED: 'red', BLACK: 'black' };
export const Orientation = { N:'N', NE:'NE', E:'E', SE:'SE', S:'S', SW:'SW', W:'W', NW:'NW' };

// ── Avoriaz Run Database ─────────────────────────────────────────────────────
export const AVORIAZ_RUNS = [
  { name:'Combe de Chavannes', difficulty:'red',   altitude_m:2050, orientation:'N',  length_km:3.2, primary_lift:'Chavannes Express', popularity:0.65, flow_score:0.82, notes:'Classic summit red; N-facing wall holds powder long after snowfall' },
  { name:'Arare',              difficulty:'blue',  altitude_m:1900, orientation:'E',  length_km:2.1, primary_lift:'Arare Chairlift',   popularity:0.70, flow_score:0.68, notes:'Wide groomed blue; morning sun burns off ice without cooking the snow' },
  { name:'La Schuss',          difficulty:'black', altitude_m:2150, orientation:'N',  length_km:2.8, primary_lift:'Chavannes Express', popularity:0.35, flow_score:0.75, notes:'Sustained steep N-facing line; superb dry snow but demands advanced skill' },
  { name:'Lindarets Valley',   difficulty:'blue',  altitude_m:1700, orientation:'S',  length_km:2.5, primary_lift:'Lindarets Lift',    popularity:0.78, flow_score:0.60, notes:'Scenic low-altitude valley; S-facing = slushy by noon in late March' },
  { name:'Mossettes',          difficulty:'red',   altitude_m:2050, orientation:'W',  length_km:3.5, primary_lift:'Mossettes Lift',    popularity:0.55, flow_score:0.78, notes:'Long flowing red; excellent mornings, afternoon sun hits from 13:30' },
  { name:'Fornet',             difficulty:'red',   altitude_m:1950, orientation:'NE', length_km:2.2, primary_lift:'Fornet T-Bar',      popularity:0.28, flow_score:0.85, notes:'Hidden gem; NE orientation + low footfall = consistently excellent conditions' },
  { name:'Prolys',             difficulty:'blue',  altitude_m:1850, orientation:'N',  length_km:1.8, primary_lift:'Crêtes Chairlift',  popularity:0.82, flow_score:0.55, notes:'Most popular blue; high throughput near village creates congestion' },
  { name:'Crêtes',             difficulty:'blue',  altitude_m:2000, orientation:'E',  length_km:2.0, primary_lift:'Crêtes Chairlift',  popularity:0.60, flow_score:0.72, notes:'Ridgeline run with panoramic views; shares lift with Prolys but less traffic' },
  { name:'Chamois',            difficulty:'red',   altitude_m:2200, orientation:'N',  length_km:4.1, primary_lift:'Chavannes Express', popularity:0.40, flow_score:0.88, notes:"Highest-altitude red in sector; longest run, rarely crowded — hidden gem" },
  { name:'Stade Slalom',       difficulty:'black', altitude_m:2200, orientation:'N',  length_km:1.5, primary_lift:'Chavannes Express', popularity:0.30, flow_score:0.65, notes:'Race-course groomed pitch; technical but perfectly prepared' },
  { name:'Combe du Machon',    difficulty:'red',   altitude_m:1800, orientation:'S',  length_km:2.8, primary_lift:'Machon Lift',        popularity:0.50, flow_score:0.70, notes:'Mid-mountain red; S-facing means rapid snow deterioration after 11:30' },
  { name:'Super Morzine',      difficulty:'blue',  altitude_m:1650, orientation:'S',  length_km:3.0, primary_lift:'Super Morzine Gondola', popularity:0.68, flow_score:0.58, notes:'Low-altitude connector to Morzine; scenic but snow quality marginal by April' },
];

// ── Weather profile ──────────────────────────────────────────────────────────
const DAILY_WEATHER = {
  '2026-03-28': [-4.0,  8.0, 0.60],
  '2026-03-29': [-3.5,  2.0, 0.30],
  '2026-03-30': [-2.0,  0.0, 0.10],
  '2026-03-31': [-1.5,  0.0, 0.20],
  '2026-04-01': [-5.0, 15.0, 0.95],
  '2026-04-02': [-4.5,  5.0, 0.50],
  '2026-04-03': [-2.5,  0.0, 0.20],
  '2026-04-04': [-1.0,  0.0, 0.10],
};

export function getWeather(dt) {
  const key = dt.toISOString().slice(0, 10);
  return DAILY_WEATHER[key] || [-3.0, 0.0, 0.30];
}

// ── Sun exposure profiles ─────────────────────────────────────────────────────
const SUN_PROFILES = {
  N:  Array(24).fill(0.04),
  NE: [0,0,0,0,0,0,0, 0.30,0.65,0.90,0.85,0.55, 0.25,0.10, ...Array(10).fill(0.04)],
  E:  [0,0,0,0,0,0,0,0, 0.50,0.85,1.00,0.90, 0.60,0.25, ...Array(10).fill(0.05)],
  SE: [0,0,0,0,0,0,0,0,0, 0.55,0.85,1.00, 0.95,0.75,0.40,0.15, ...Array(8).fill(0.04)],
  S:  [0,0,0,0,0,0,0,0,0,0, 0.60,0.90, 1.00,1.00,0.85,0.55,0.20, ...Array(7).fill(0.04)],
  SW: [0,0,0,0,0,0,0,0,0,0,0,0, 0.30,0.65,0.90,1.00,0.85,0.40, ...Array(6).fill(0.04)],
  W:  [0,0,0,0,0,0,0,0,0,0,0,0,0, 0.35,0.70,0.95,1.00,0.70, ...Array(6).fill(0.10)],
  NW: [0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0.20,0.45,0.70,0.55,0.20, ...Array(5).fill(0.04)],
};

export function sunExposure(orientation, hour, cloudCover) {
  const profile = SUN_PROFILES[orientation] || SUN_PROFILES.N;
  const raw = profile[hour] ?? 0.04;
  return raw * (1.0 - cloudCover * 0.75);
}

export function altitudeFactor(altitude_m) {
  return 1.0 + (altitude_m - 1800) / 2200.0;
}

export function temperatureFactor(temp_c) {
  if (temp_c < -15) return 0.72;
  if (temp_c < -8)  return 0.85 + (temp_c + 15) * 0.022;
  if (temp_c < -2)  return 1.00;
  if (temp_c < 0)   return 1.00 - (temp_c + 2) * 0.07;
  if (temp_c < 3)   return 0.86 - temp_c * 0.09;
  return Math.max(0.38, 0.59 - temp_c * 0.05);
}

export function diurnalTemp(baseTemp, hour) {
  const phase = (hour - 7) / 24.0 * 2 * Math.PI;
  return baseTemp + 4.0 * Math.sin(phase);
}

export function snowSurfaceLabel(snowScore, hour, orientation, cloudCover) {
  const sun = sunExposure(orientation, hour, cloudCover);
  if (snowScore > 80 && sun < 0.15) return 'powder';
  if (snowScore > 65 && sun < 0.35) return 'groomed / firm';
  if (snowScore > 50 && sun < 0.60) return 'softening';
  if (sun >= 0.60) return 'slushy';
  if (snowScore < 38) return 'icy / wind-packed';
  return 'wind-packed';
}

// ── Snow quality ─────────────────────────────────────────────────────────────
export function computeSnowScore(run, dt, snowfall_cm, baseTemp, cloudCover, seed = 42) {
  const rng = mulberry32(seed ^ (dt.getTime() % 99991));
  const hour = dt.getHours();
  const tempNow = diurnalTemp(baseTemp, hour);
  const basePack = 67.0;
  const sfBonus = Math.min(25.0, snowfall_cm * 1.75);
  const altF = altitudeFactor(run.altitude_m);
  const tempF = temperatureFactor(tempNow);

  let sunDmg = 0;
  for (let h = 8; h <= Math.min(hour, 17); h++) {
    sunDmg += sunExposure(run.orientation, h, cloudCover) * 4.0;
  }

  const refDate = new Date('2026-03-28');
  const daysElapsed = Math.max(0, Math.floor((dt - refDate) / 86400000));
  const agePenalty = snowfall_cm > 3 ? 0 : daysElapsed * 2.2;

  const raw = (basePack + sfBonus) * altF * tempF - sunDmg - agePenalty;
  const noise = normalSample(rng, 0, 2.8);
  const score = clip(raw + noise, 0, 100);
  return [Math.round(score * 10) / 10, snowSurfaceLabel(score, hour, run.orientation, cloudCover)];
}

// ── Crowd model ──────────────────────────────────────────────────────────────
const LIFT_CONGESTION = {
  'Chavannes Express':    0.92,
  'Crêtes Chairlift':     0.76,
  'Arare Chairlift':      0.65,
  'Lindarets Lift':       0.70,
  'Mossettes Lift':       0.55,
  'Fornet T-Bar':         0.24,
  'Machon Lift':          0.44,
  'Super Morzine Gondola':0.60,
};
const SKILL_CLUSTER = {
  green: { beginner:0.60, intermediate:0.35, advanced:0.05 },
  blue:  { beginner:0.40, intermediate:0.45, advanced:0.15 },
  red:   { beginner:0.05, intermediate:0.55, advanced:0.40 },
  black: { beginner:0.00, intermediate:0.15, advanced:0.85 },
};
const HOUR_CROWD = { 8:0.25, 9:0.72, 10:0.95, 11:1.00, 12:0.62, 13:0.55, 14:0.90, 15:0.82, 16:0.50, 17:0.20 };
const DOW_FACTOR  = { 0:0.72, 1:0.68, 2:0.70, 3:0.68, 4:0.83, 5:1.00, 6:0.91 };

export function computeCrowdLevel(run, dt, touristMultiplier = 1.0, seed = 42) {
  const hour = dt.getHours();
  const timeM = HOUR_CROWD[hour] ?? 0;
  if (timeM === 0) return [0, 'Low'];

  const rng = mulberry32(seed ^ (dt.getTime() % 88887));
  const dowM  = DOW_FACTOR[dt.getDay()] ?? 0.72;
  const liftC = LIFT_CONGESTION[run.primary_lift] ?? 0.50;
  const skill = SKILL_CLUSTER[run.difficulty] ?? {};

  const base   = run.popularity * timeM * dowM * touristMultiplier;
  const liftP  = liftC * 0.18;
  const skillP = (skill.beginner ?? 0) * 0.14;

  const raw   = base + liftP + skillP;
  const noise = normalSample(rng, 0, 0.07);
  const crowd = clip(raw + noise, 0, 1);
  const label = crowd < 0.35 ? 'Low' : crowd < 0.62 ? 'Medium' : 'High';
  return [Math.round(crowd * 1000) / 1000, label];
}

// ── Enjoyment ────────────────────────────────────────────────────────────────
export function computeEnjoyment(run, snowScore, crowdLevel, prefs = {}) {
  let wSnow  = 0.35 + (prefs.prioritize_snow ?? 0) * 0.15;
  let wCrowd = 0.30 + (prefs.avoid_crowds    ?? 0) * 0.15;
  let wLen   = 0.15;
  let wFlow  = 0.20;
  const total = wSnow + wCrowd + wLen + wFlow;
  wSnow /= total; wCrowd /= total; wLen /= total; wFlow /= total;

  const cSnow  = snowScore;
  const cCrowd = (1.0 - crowdLevel) * 100.0;
  const cLen   = Math.min(100.0, run.length_km / 4.5 * 100.0);
  const cFlow  = run.flow_score * 100.0;

  const score = wSnow*cSnow + wCrowd*cCrowd + wLen*cLen + wFlow*cFlow;
  return Math.round(clip(score, 0, 100) * 10) / 10;
}

// ── Full condition snapshot ───────────────────────────────────────────────────
export function getRunConditions(run, dt, touristMultiplier = 1.0, prefs = {}, seed = 42) {
  const [baseTemp, snowfall, cloudCover] = getWeather(dt);
  const [snowScore, surface] = computeSnowScore(run, dt, snowfall, baseTemp, cloudCover, seed);
  const [crowdLevel, crowdLabel] = computeCrowdLevel(run, dt, touristMultiplier, seed);
  const enjoyment = computeEnjoyment(run, snowScore, crowdLevel, prefs);
  return {
    run,
    snow_score: snowScore,
    crowd_level: crowdLevel,
    crowd_label: crowdLabel,
    enjoyment_score: enjoyment,
    temperature_c: Math.round(diurnalTemp(baseTemp, dt.getHours()) * 10) / 10,
    snow_surface: surface,
    timestamp: dt.toISOString(),
    recommendation_reason: '',
  };
}

export function getAllConditions(dt, touristMultiplier = 1.0, prefs = {}, seed = 42) {
  return AVORIAZ_RUNS
    .map(run => getRunConditions(run, dt, touristMultiplier, prefs, seed))
    .sort((a, b) => b.enjoyment_score - a.enjoyment_score);
}
