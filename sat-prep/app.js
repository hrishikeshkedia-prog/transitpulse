// ============================================================
// SAT Quest — RPG-Style SAT Preparation App
// app.js — Complete Application Logic
// ============================================================

'use strict';

// ============================================================
// CONSTANTS & DATA
// ============================================================

const LEVEL_THRESHOLDS = [0, 500, 1200, 2100, 3200, 4500, 6000, 7800, 9800, 12000];
const LEVEL_TITLES = [
  "Novice", "Apprentice", "Scholar", "Adept", "Sage",
  "Master", "Champion", "Legend", "Grandmaster", "SAT Conqueror"
];

const SAT_DATE = new Date('2026-08-15T00:00:00');

const DUNGEON_WEEKS = [
  { week: 1, start: "2026-06-01", end: "2026-06-07", name: "Tutorial Ruins", emoji: "🏚️",
    topics: ["linear_equations", "central_ideas", "grammar"],
    description: "Master the fundamentals" },
  { week: 2, start: "2026-06-08", end: "2026-06-14", name: "Algebra Caverns", emoji: "⚗️",
    topics: ["systems_of_equations", "inequalities", "command_of_evidence", "punctuation"],
    description: "Conquer algebraic systems" },
  { week: 3, start: "2026-06-15", end: "2026-06-21", name: "Polynomial Peaks", emoji: "⛰️",
    topics: ["quadratics", "polynomials", "inferences", "sentence_structure"],
    description: "Scale advanced math heights" },
  { week: 4, start: "2026-06-22", end: "2026-06-28", name: "Function Forest", emoji: "🌲",
    topics: ["exponential", "radical_equations", "vocabulary_in_context", "text_structure"],
    description: "Navigate functional complexity" },
  { week: 5, start: "2026-06-29", end: "2026-07-05", name: "Data Analytics Den", emoji: "📊",
    topics: ["ratios", "percentages", "statistics", "probability"],
    description: "Analyze data like a wizard" },
  { week: 6, start: "2026-07-06", end: "2026-07-12", name: "Geometry Gauntlet", emoji: "📐",
    topics: ["area_volume", "circles", "cross_text_connections", "rhetorical_synthesis"],
    description: "Shape your spatial skills" },
  { week: 7, start: "2026-07-13", end: "2026-07-19", name: "Trigonometry Tower", emoji: "🗼",
    topics: ["right_triangles", "trig", "transitions", "expression"],
    description: "Reach new angular heights" },
  { week: 8, start: "2026-07-20", end: "2026-07-26", name: "Mixed Battle Arena", emoji: "⚔️",
    topics: ["all_math_review", "all_rw_review"],
    description: "All-domain combat training" },
  { week: 9, start: "2026-07-27", end: "2026-08-02", name: "Score Rush Dungeon", emoji: "🚀",
    topics: ["weak_area_focus", "speed_drills"],
    description: "Maximum intensity sprint" },
  { week: 10, start: "2026-08-03", end: "2026-08-09", name: "Final Approach", emoji: "🏰",
    topics: ["full_review", "strategy_refinement"],
    description: "Polish every skill for the final fight" },
  { week: 11, start: "2026-08-10", end: "2026-08-15", name: "⚡ FINAL BOSS ⚡", emoji: "👑",
    topics: [],
    description: "August 15, 2026 — The Real SAT", isFinalBoss: true }
];

const DEFAULT_STATE = {
  character: {
    name: "SAT Challenger",
    level: 1,
    totalXP: 0,
    mathXP: 0,
    rwXP: 0,
    streak: 0,
    lastStudyDate: null,
    totalStudyMinutes: 0,
    initialized: false
  },
  skills: {
    math: {
      algebra: {
        linear_equations: { name: "Linear Equations", status: "unlocked", sessions: 0, totalQ: 0, wrongQ: 0 },
        systems_of_equations: { name: "Systems of Equations", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        inequalities: { name: "Inequalities", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 }
      },
      advanced_math: {
        quadratics: { name: "Quadratics", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        polynomials: { name: "Polynomials", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        exponential: { name: "Exponential Functions", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        radical_equations: { name: "Radical Equations", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 }
      },
      psda: {
        ratios: { name: "Ratios & Proportions", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        percentages: { name: "Percentages", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        statistics: { name: "Statistics", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        probability: { name: "Probability", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 }
      },
      geometry: {
        area_volume: { name: "Area & Volume", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        circles: { name: "Circles", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        right_triangles: { name: "Right Triangles", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        trig: { name: "Basic Trigonometry", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 }
      }
    },
    rw: {
      info_ideas: {
        central_ideas: { name: "Central Ideas", status: "unlocked", sessions: 0, totalQ: 0, wrongQ: 0 },
        command_of_evidence: { name: "Command of Evidence", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        inferences: { name: "Inferences", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 }
      },
      craft_structure: {
        vocabulary_in_context: { name: "Vocabulary in Context", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        text_structure: { name: "Text Structure & Purpose", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        cross_text_connections: { name: "Cross-Text Connections", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 }
      },
      expression: {
        rhetorical_synthesis: { name: "Rhetorical Synthesis", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        transitions: { name: "Transitions", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 }
      },
      sec: {
        grammar: { name: "Grammar", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        punctuation: { name: "Punctuation", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 },
        sentence_structure: { name: "Sentence Structure", status: "locked", sessions: 0, totalQ: 0, wrongQ: 0 }
      }
    }
  },
  papers: [],
  sessions: [],
  achievements: {},
  settings: { notifications: false, name: "SAT Challenger" },
  weeklyQuestsCompleted: 0,
  lastQuestReset: null,
  dailyQuests: []
};

// ============================================================
// ACHIEVEMENT HELPER FUNCTIONS
// ============================================================

function checkPerfectWeek(s) {
  if (!s.sessions || !s.sessions.length) return false;
  const now = new Date();
  const weekStart = new Date(now);
  weekStart.setDate(now.getDate() - now.getDay());
  weekStart.setHours(0, 0, 0, 0);
  const days = new Set();
  s.sessions.forEach(sess => {
    const d = new Date(sess.date);
    if (d >= weekStart) {
      days.add(d.toDateString());
    }
  });
  return days.size >= 7;
}

function hasStrongTopic(s) {
  return getAllTopicsFromState(s).some(t => t.data.status === 'strong');
}

function getAllTopicsFromState(s) {
  const topics = [];
  const skills = s.skills;
  function traverse(branch, category) {
    for (const key in branch) {
      const node = branch[key];
      if (node && typeof node === 'object' && 'sessions' in node) {
        topics.push({ key, name: node.name, data: node, category });
      } else if (typeof node === 'object') {
        traverse(node, category);
      }
    }
  }
  traverse(skills.math, 'math');
  traverse(skills.rw, 'rw');
  return topics;
}

function checkScoreImprovement(s, threshold) {
  if (!s.papers || s.papers.length < 2) return false;
  const sorted = [...s.papers].sort((a, b) => new Date(a.date) - new Date(b.date));
  const first = sorted[0];
  const last = sorted[sorted.length - 1];
  return (last.mathScore + last.rwScore) - (first.mathScore + first.rwScore) >= threshold;
}

const ACHIEVEMENTS = {
  first_steps: {
    name: "First Steps", icon: "👣",
    desc: "Complete your first study session",
    condition: s => s.sessions && s.sessions.length >= 1
  },
  week_warrior: {
    name: "Week Warrior", icon: "🔥",
    desc: "Maintain a 7-day study streak",
    condition: s => s.character.streak >= 7
  },
  paper_slayer: {
    name: "Paper Slayer", icon: "📜",
    desc: "Complete your first practice paper",
    condition: s => s.papers && s.papers.length >= 1
  },
  boss_slayer: {
    name: "Boss Slayer", icon: "⚔️",
    desc: "Complete your first mock test",
    condition: s => s.papers && s.papers.some(p => p.type === 'mock')
  },
  perfect_week: {
    name: "Perfect Week", icon: "💎",
    desc: "Study all 7 days in a week",
    condition: s => checkPerfectWeek(s)
  },
  month_master: {
    name: "Month Master", icon: "🌙",
    desc: "30-day study streak",
    condition: s => s.character.streak >= 30
  },
  math_600: {
    name: "600 Barrier Broken", icon: "🎯",
    desc: "Score 600+ on Math section",
    condition: s => s.papers && s.papers.some(p => p.mathScore >= 600)
  },
  math_700: {
    name: "700 Territory", icon: "⚡",
    desc: "Score 700+ on Math section",
    condition: s => s.papers && s.papers.some(p => p.mathScore >= 700)
  },
  math_750: {
    name: "Math Target Hit!", icon: "🏆",
    desc: "Score 750+ on Math — TARGET ACHIEVED!",
    condition: s => s.papers && s.papers.some(p => p.mathScore >= 750)
  },
  rw_600: {
    name: "RW Breakthrough", icon: "📖",
    desc: "Score 600+ on Reading & Writing",
    condition: s => s.papers && s.papers.some(p => p.rwScore >= 600)
  },
  rw_650: {
    name: "RW Target Hit!", icon: "✨",
    desc: "Score 650+ on RW — TARGET ACHIEVED!",
    condition: s => s.papers && s.papers.some(p => p.rwScore >= 650)
  },
  total_1400: {
    name: "1400 Club", icon: "🌟",
    desc: "Score 1400+ total — SO CLOSE!",
    condition: s => s.papers && s.papers.some(p => p.mathScore + p.rwScore >= 1400)
  },
  final_boss: {
    name: "FINAL BOSS DEFEATED", icon: "👑",
    desc: "Score 1500+ total — ULTIMATE GOAL ACHIEVED!",
    condition: s => s.papers && s.papers.some(p => p.mathScore + p.rwScore >= 1500)
  },
  topic_master: {
    name: "Topic Master", icon: "🎓",
    desc: "Get any topic to Strong status",
    condition: s => hasStrongTopic(s)
  },
  early_bird: {
    name: "Early Bird", icon: "🌅",
    desc: "Log a morning study session (before 7am)",
    condition: s => s.sessions && s.sessions.some(sess => {
      const h = new Date(sess.date).getHours();
      return h >= 5 && h < 7;
    })
  },
  score_improver: {
    name: "On The Rise", icon: "📈",
    desc: "Improve total score by 50+ points",
    condition: s => checkScoreImprovement(s, 50)
  },
  big_improver: {
    name: "Power Surge", icon: "⚡",
    desc: "Improve total score by 100+ points",
    condition: s => checkScoreImprovement(s, 100)
  }
};

// ============================================================
// STATE MANAGEMENT
// ============================================================

let state = null;
let scoreChart = null;
let topicChart = null;

function deepMerge(target, source) {
  const result = Object.assign({}, target);
  for (const key in source) {
    if (!(key in result)) {
      result[key] = source[key];
    } else if (
      source[key] !== null &&
      typeof source[key] === 'object' &&
      !Array.isArray(source[key]) &&
      result[key] !== null &&
      typeof result[key] === 'object' &&
      !Array.isArray(result[key])
    ) {
      result[key] = deepMerge(result[key], source[key]);
    }
  }
  return result;
}

function loadState() {
  try {
    const raw = localStorage.getItem('satquest_state');
    if (raw) {
      const parsed = JSON.parse(raw);
      state = deepMerge(parsed, DEFAULT_STATE);
      if (!Array.isArray(state.papers)) state.papers = [];
      if (!Array.isArray(state.sessions)) state.sessions = [];
      if (!Array.isArray(state.dailyQuests)) state.dailyQuests = [];
      if (!state.achievements || typeof state.achievements !== 'object') state.achievements = {};
    } else {
      state = JSON.parse(JSON.stringify(DEFAULT_STATE));
    }
  } catch (e) {
    console.error('Failed to load state:', e);
    state = JSON.parse(JSON.stringify(DEFAULT_STATE));
  }
}

function saveState() {
  try {
    localStorage.setItem('satquest_state', JSON.stringify(state));
  } catch (e) {
    console.error('Failed to save state:', e);
    showToast('Warning: Could not save progress (storage full?)', 'error');
  }
}

// ============================================================
// HELPER FUNCTIONS
// ============================================================

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return 'Invalid Date';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch (e) {
    return 'N/A';
  }
}

function todayString() {
  return new Date().toISOString().split('T')[0];
}

function getDaysUntilSAT() {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const sat = new Date('2026-08-15');
  sat.setHours(0, 0, 0, 0);
  const diff = Math.ceil((sat - now) / (1000 * 60 * 60 * 24));
  return Math.max(0, diff);
}

function getLevelFromXP(xp) {
  let level = 1;
  for (let i = LEVEL_THRESHOLDS.length - 1; i >= 0; i--) {
    if (xp >= LEVEL_THRESHOLDS[i]) {
      level = i + 1;
      break;
    }
  }
  return Math.min(level, 10);
}

function getLevelTitle(level) {
  return LEVEL_TITLES[Math.min(level - 1, LEVEL_TITLES.length - 1)];
}

function getXPBar(xp) {
  const level = getLevelFromXP(xp);
  if (level >= 10) {
    return { current: LEVEL_THRESHOLDS[9], start: LEVEL_THRESHOLDS[9], end: LEVEL_THRESHOLDS[9], pct: 100 };
  }
  const start = LEVEL_THRESHOLDS[level - 1];
  const end = LEVEL_THRESHOLDS[level];
  const pct = Math.min(100, Math.max(0, ((xp - start) / (end - start)) * 100));
  return { current: xp - start, start, end, pct };
}

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
}

// ============================================================
// TOPIC UTILITIES
// ============================================================

function getAllTopics(s) {
  return getAllTopicsFromState(s || state);
}

function getTopicData(topicKey) {
  const skills = state.skills;
  for (const cat of ['math', 'rw']) {
    for (const domain in skills[cat]) {
      if (skills[cat][domain] && skills[cat][domain][topicKey]) {
        return { data: skills[cat][domain][topicKey], category: cat, domain };
      }
    }
  }
  return null;
}

function getTopicCategory(topicKey) {
  const result = getTopicData(topicKey);
  return result ? result.category : null;
}

function computeTopicStatus(data) {
  if (data.sessions === 0) {
    return data.status === 'unlocked' ? 'unlocked' : 'locked';
  }
  const accuracy = data.totalQ >= 5
    ? ((data.totalQ - data.wrongQ) / data.totalQ) * 100
    : null;

  if (accuracy !== null) {
    if (accuracy >= 80) return 'strong';
    if (accuracy >= 60) return 'steady';
    return 'weak';
  }
  // Less than 5 questions answered — go by sessions count and raw accuracy
  if (data.totalQ > 0) {
    const rawAcc = ((data.totalQ - data.wrongQ) / data.totalQ) * 100;
    if (rawAcc < 50) return 'weak';
  }
  return 'in_progress';
}

function recalculateTopicStatuses() {
  const skills = state.skills;
  function traverse(branch) {
    for (const key in branch) {
      const node = branch[key];
      if (node && typeof node === 'object' && 'sessions' in node) {
        node.status = computeTopicStatus(node);
      } else if (node && typeof node === 'object') {
        traverse(node);
      }
    }
  }
  traverse(skills.math);
  traverse(skills.rw);
}

function getTopicDisplayName(topicKey) {
  if (!topicKey) return 'Unknown';
  const t = getTopicData(topicKey);
  if (t) return t.data.name;
  // Fallback for special keys like all_math_review, weak_area_focus etc.
  return topicKey.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function getAllTopicOptions() {
  const options = [];
  const skills = state.skills;
  for (const cat of ['math', 'rw']) {
    for (const domain in skills[cat]) {
      for (const topicKey in skills[cat][domain]) {
        const data = skills[cat][domain][topicKey];
        if (data && typeof data === 'object' && 'sessions' in data) {
          options.push({
            key: topicKey,
            label: `[${cat.toUpperCase()}] ${data.name}`,
            category: cat,
            domain
          });
        }
      }
    }
  }
  return options;
}

// ============================================================
// STREAK LOGIC
// ============================================================

function updateStreak() {
  const today = todayString();
  const last = state.character.lastStudyDate;
  if (!last) {
    state.character.streak = 1;
    state.character.lastStudyDate = today;
    return;
  }
  if (last === today) return; // already studied today

  const lastDate = new Date(last);
  const todayDate = new Date(today);
  const diffDays = Math.round((todayDate - lastDate) / (1000 * 60 * 60 * 24));
  if (diffDays === 1) {
    state.character.streak += 1;
  } else if (diffDays > 1) {
    state.character.streak = 1;
  }
  state.character.lastStudyDate = today;
}

function checkStreakMilestones(oldStreak, newStreak) {
  const milestones = [7, 14, 30];
  let bonusXP = 0;
  for (const m of milestones) {
    if (oldStreak < m && newStreak >= m) {
      bonusXP += 500;
      setTimeout(() => showToast(`🔥 ${m}-Day Streak! +500 XP Bonus!`, 'success'), 100);
    }
  }
  return bonusXP;
}

// ============================================================
// XP SYSTEM
// ============================================================

function addXP(amount, category) {
  if (!amount || amount <= 0) return;
  const oldLevel = getLevelFromXP(state.character.totalXP);
  state.character.totalXP += amount;
  if (category === 'math') state.character.mathXP += amount;
  else if (category === 'rw') state.character.rwXP += amount;
  const newLevel = getLevelFromXP(state.character.totalXP);
  state.character.level = newLevel;
  if (newLevel > oldLevel) {
    setTimeout(() => showLevelUpModal(newLevel), 200);
  }
}

function calcSessionXP(session) {
  let xp = 100;
  const streakBonus = Math.min((state.character.streak || 0) * 10, 100);
  xp += streakBonus;
  // Morning bonus: 5am-7am
  const h = new Date(session.date).getHours();
  if (h >= 5 && h < 7) xp += 50;
  return xp;
}

function addSession(sessionData) {
  const oldStreak = state.character.streak || 0;
  updateStreak();
  const newStreak = state.character.streak;

  // Check prev status before updating
  const topicInfo = getTopicData(sessionData.topicKey);
  const prevStatus = topicInfo ? topicInfo.data.status : null;

  const xp = calcSessionXP(sessionData);
  sessionData.xpGained = xp;
  sessionData._prevStatus = prevStatus;

  state.sessions.push(sessionData);
  state.character.totalStudyMinutes = (state.character.totalStudyMinutes || 0) + (sessionData.minutes || 0);

  // Update topic session count
  if (topicInfo) {
    const t = topicInfo.data;
    t.sessions += 1;
    if (t.status === 'locked') t.status = 'in_progress';
    else if (t.status === 'unlocked') t.status = 'in_progress';
  }

  recalculateTopicStatuses();

  // Check for status upgrade bonuses
  let bonusXP = 0;
  if (topicInfo) {
    const newStatus = topicInfo.data.status;
    if (prevStatus !== 'steady' && prevStatus !== 'strong' && newStatus === 'steady') bonusXP += 150;
    if (prevStatus !== 'strong' && newStatus === 'strong') bonusXP += 250;
    if (bonusXP > 0) {
      setTimeout(() => showToast(`📈 Topic upgraded to ${newStatus}! +${bonusXP} XP Bonus!`, 'success'), 300);
    }
  }

  const streakBonus = checkStreakMilestones(oldStreak, newStreak);
  bonusXP += streakBonus;

  const cat = getTopicCategory(sessionData.topicKey);
  addXP(xp + bonusXP, cat);

  checkAllAchievements();
  saveState();
}

function addPaper(paperData) {
  state.papers.push(paperData);

  let xp = paperData.type === 'mock' ? 500 : 300;
  const mathXPShare = Math.round(xp * 0.5);
  const rwXPShare = xp - mathXPShare;
  addXP(mathXPShare, 'math');
  addXP(rwXPShare, 'rw');

  // Update topic wrong answer data from paper entries
  if (paperData.wrongAnswers && Array.isArray(paperData.wrongAnswers)) {
    paperData.wrongAnswers.forEach(wa => {
      if (!wa.topicKey) return;
      const topicInfo = getTopicData(wa.topicKey);
      if (topicInfo) {
        const count = parseInt(wa.count) || 1;
        topicInfo.data.totalQ += count;
        topicInfo.data.wrongQ += count;
      }
    });
  }

  recalculateTopicStatuses();
  checkAllAchievements();
  saveState();
}

// ============================================================
// SCORE PREDICTION
// ============================================================

function predictScore() {
  const papers = state.papers.slice().sort((a, b) => new Date(a.date) - new Date(b.date));
  if (!papers.length) {
    return { math: 550, rw: 500, total: 1050, confidence: 'low', onTrack: false };
  }
  if (papers.length === 1) {
    const p = papers[0];
    const total = p.mathScore + p.rwScore;
    return { math: p.mathScore, rw: p.rwScore, total, confidence: 'low', onTrack: total >= 1350 };
  }

  const recent = papers.slice(-3).reverse();
  const weights = [0.5, 0.3, 0.2];
  let mathPred = 0, rwPred = 0, totalWeight = 0;
  recent.forEach((p, i) => {
    const w = weights[i] !== undefined ? weights[i] : 0;
    mathPred += p.mathScore * w;
    rwPred += p.rwScore * w;
    totalWeight += w;
  });
  if (totalWeight > 0) {
    mathPred = Math.round(mathPred / totalWeight);
    rwPred = Math.round(rwPred / totalWeight);
  }

  return {
    math: mathPred,
    rw: rwPred,
    total: mathPred + rwPred,
    confidence: papers.length >= 3 ? 'high' : 'medium',
    onTrack: (mathPred >= 700 && rwPred >= 600) || (mathPred + rwPred) >= 1350
  };
}

// ============================================================
// ACHIEVEMENT SYSTEM
// ============================================================

function checkAllAchievements() {
  if (!state.achievements) state.achievements = {};
  for (const key in ACHIEVEMENTS) {
    if (state.achievements[key] && state.achievements[key].unlocked) continue;
    try {
      if (ACHIEVEMENTS[key].condition(state)) {
        state.achievements[key] = { unlocked: true, date: new Date().toISOString() };
        const def = ACHIEVEMENTS[key];
        setTimeout(() => showToast(`${def.icon} Achievement Unlocked: ${def.name}!`, 'achievement'), 150);
      }
    } catch (e) {
      // Silently ignore condition errors
    }
  }
}

// ============================================================
// QUEST GENERATION
// ============================================================

function getCurrentDungeonWeek() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  for (const w of DUNGEON_WEEKS) {
    const start = new Date(w.start);
    const end = new Date(w.end);
    end.setHours(23, 59, 59, 999);
    if (today >= start && today <= end) return w;
  }
  return null;
}

function getWeakestTopics(count) {
  const all = getAllTopics();
  const studied = all.filter(t => t.data.sessions > 0);
  if (!studied.length) {
    return all.filter(t => t.data.status === 'unlocked').slice(0, count);
  }
  const sorted = studied.sort((a, b) => {
    const accA = a.data.totalQ > 0 ? (a.data.totalQ - a.data.wrongQ) / a.data.totalQ : 0.5;
    const accB = b.data.totalQ > 0 ? (b.data.totalQ - b.data.wrongQ) / b.data.totalQ : 0.5;
    if (Math.abs(accA - accB) < 0.01) return a.data.sessions - b.data.sessions;
    return accA - accB;
  });
  return sorted.slice(0, count);
}

function hasCompletedPaperThisWeek() {
  const now = new Date();
  const weekStart = new Date(now);
  weekStart.setDate(now.getDate() - now.getDay());
  weekStart.setHours(0, 0, 0, 0);
  return state.papers.some(p => new Date(p.date) >= weekStart);
}

function generateDailyQuests() {
  const today = todayString();
  if (state.lastQuestReset === today && state.dailyQuests && state.dailyQuests.length > 0) {
    return state.dailyQuests;
  }

  const quests = [];
  const weak = getWeakestTopics(2);

  weak.forEach(t => {
    quests.push({
      id: generateId(),
      topic: t.data.name,
      topicKey: t.key,
      type: t.data.sessions === 0 ? 'new_concept' : 'review',
      description: t.data.sessions === 0
        ? `Begin studying ${t.data.name} — unlock this skill!`
        : `Review ${t.data.name} — accuracy needs improvement`,
      xp: t.data.sessions === 0 ? 120 : 100,
      completed: false,
      category: t.category
    });
  });

  // Dungeon week topic
  const currentWeek = getCurrentDungeonWeek();
  if (currentWeek && currentWeek.topics.length > 0) {
    const topicKey = currentWeek.topics[Math.floor(Math.random() * currentWeek.topics.length)];
    const topicInfo = getTopicData(topicKey);
    if (topicInfo && !quests.find(q => q.topicKey === topicKey)) {
      quests.push({
        id: generateId(),
        topic: topicInfo.data.name,
        topicKey,
        type: 'problem_set',
        description: `${currentWeek.emoji} ${currentWeek.name}: Practice ${topicInfo.data.name}`,
        xp: 130,
        completed: false,
        category: topicInfo.category
      });
    }
  }

  // Timed practice if no paper this week
  if (!hasCompletedPaperThisWeek()) {
    quests.push({
      id: generateId(),
      topic: 'Full Practice',
      topicKey: null,
      type: 'timed_practice',
      description: 'Complete 30 minutes of timed practice today',
      xp: 150,
      completed: false,
      category: 'both'
    });
  }

  // Boss battle suggestion on weekends
  const dayOfWeek = new Date().getDay();
  if (dayOfWeek === 0 || dayOfWeek === 6) {
    quests.push({
      id: generateId(),
      topic: 'Mock Test',
      topicKey: null,
      type: 'boss_battle',
      description: '⚔️ Boss Battle: Complete a full mock SAT test!',
      xp: 500,
      completed: false,
      category: 'both'
    });
  }

  state.dailyQuests = quests.slice(0, 5);
  state.lastQuestReset = today;
  saveState();
  return state.dailyQuests;
}

function completeQuest(questId) {
  if (!state.dailyQuests) return;
  const quest = state.dailyQuests.find(q => q.id === questId);
  if (!quest || quest.completed) return;
  quest.completed = true;
  state.weeklyQuestsCompleted = (state.weeklyQuestsCompleted || 0) + 1;
  const cat = quest.category === 'math' ? 'math' : quest.category === 'rw' ? 'rw' : null;
  addXP(quest.xp, cat);
  showToast(`Quest Complete! +${quest.xp} XP`, 'success');
  saveState();
  updateQuests();
  renderDashboard();
  renderHeader();
}

// ============================================================
// ERROR PATTERN ANALYSIS
// ============================================================

function analyzeErrorPatterns(papers) {
  const counts = { conceptGap: 0, careless: 0, timePressure: 0 };
  (papers || []).forEach(p => {
    if (p.wrongAnswers) {
      p.wrongAnswers.forEach(wa => {
        if (wa.errorType && Object.prototype.hasOwnProperty.call(counts, wa.errorType)) {
          counts[wa.errorType] += (parseInt(wa.count) || 1);
        }
      });
    }
  });

  const total = counts.conceptGap + counts.careless + counts.timePressure;
  if (total === 0) {
    return { message: "No error data yet — add papers with wrong answer details.", counts, total: 0 };
  }

  let message;
  if (counts.conceptGap > counts.careless && counts.conceptGap > counts.timePressure) {
    message = "Primary issue: Concept Gaps — focus on learning, not speed";
  } else if (counts.careless > counts.conceptGap && counts.careless > counts.timePressure) {
    message = "Primary issue: Careless Mistakes — slow down and double-check";
  } else if (counts.timePressure > counts.conceptGap && counts.timePressure > counts.careless) {
    message = "Primary issue: Time Pressure — practice timed sections";
  } else {
    message = "Mixed error pattern — general practice recommended";
  }

  return { message, counts, total };
}

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================

function showToast(message, type) {
  type = type || 'info';
  let container = document.getElementById('toast-container');
  if (!container) container = createToastContainer();
  const toast = document.createElement('div');
  toast.className = 'satquest-toast satquest-toast-' + type;
  toast.textContent = message;
  container.appendChild(toast);
  // Force reflow for animation
  void toast.offsetWidth;
  toast.classList.add('satquest-toast-show');
  setTimeout(() => {
    toast.classList.remove('satquest-toast-show');
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 400);
  }, 3500);
}

function createToastContainer() {
  const el = document.createElement('div');
  el.id = 'toast-container';
  el.style.cssText = [
    'position:fixed', 'bottom:20px', 'right:20px', 'z-index:9999',
    'display:flex', 'flex-direction:column', 'gap:8px', 'pointer-events:none'
  ].join(';');
  document.body.appendChild(el);
  return el;
}

// ============================================================
// LEVEL UP MODAL
// ============================================================

function showLevelUpModal(level) {
  const title = getLevelTitle(level);
  // Remove existing if any
  const existing = document.getElementById('levelup-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'levelup-modal';
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.85);display:flex;align-items:center;justify-content:center;z-index:10000;';
  modal.innerHTML = `
    <div style="background:linear-gradient(135deg,#1e1b4b,#312e81);border:2px solid #7c3aed;border-radius:16px;padding:40px 48px;text-align:center;max-width:420px;width:90%;animation:satquest-pop 0.4s ease;">
      <div style="font-size:4rem;margin-bottom:12px;">⚡</div>
      <h2 style="color:#c4b5fd;font-size:1.4rem;margin:0 0 8px;font-weight:900;letter-spacing:2px;">LEVEL UP!</h2>
      <div style="font-size:3.5rem;font-weight:900;color:#a78bfa;margin:8px 0;">${level}</div>
      <div style="color:#e2e8f0;font-size:1.3rem;margin-bottom:8px;">${title}</div>
      <div style="color:#94a3b8;font-size:0.9rem;margin-bottom:28px;">Total XP: ${state.character.totalXP.toLocaleString()}</div>
      <button onclick="document.getElementById('levelup-modal').remove()"
        style="background:linear-gradient(135deg,#7c3aed,#4c1d95);color:#fff;border:none;border-radius:10px;padding:12px 32px;font-size:1rem;cursor:pointer;font-weight:700;">
        Continue Quest ⚡
      </button>
    </div>
  `;
  document.body.appendChild(modal);
  // Close on overlay click
  modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
}

// ============================================================
// WELCOME MODAL
// ============================================================

function showWelcomeModal() {
  const existing = document.getElementById('welcome-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'welcome-modal';
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.97);display:flex;align-items:center;justify-content:center;z-index:10001;';
  modal.innerHTML = `
    <div style="background:linear-gradient(135deg,#0f172a,#1e1b4b);border:2px solid #7c3aed;border-radius:20px;padding:48px;text-align:center;max-width:480px;width:90%;box-shadow:0 0 60px rgba(124,58,237,0.4);">
      <div style="font-size:4rem;margin-bottom:16px;">⚔️</div>
      <h1 style="color:#c4b5fd;font-size:2rem;margin:0 0 8px;font-weight:900;">Welcome to SAT Quest</h1>
      <p style="color:#94a3b8;margin:0 0 8px;line-height:1.6;font-size:0.95rem;">Your RPG journey to <strong style="color:#a78bfa;">1500+</strong> begins now.</p>
      <p style="color:#64748b;margin:0 0 32px;font-size:0.85rem;">🏰 Final Boss: August 15, 2026 — The Real SAT</p>
      <div style="margin-bottom:24px;text-align:left;">
        <label style="display:block;color:#a78bfa;margin-bottom:8px;font-size:0.9rem;font-weight:600;">Your Hero Name</label>
        <input id="welcome-name-input" type="text" placeholder="Enter your name..." value="SAT Challenger"
          style="width:100%;padding:14px;border-radius:10px;border:1px solid #4c1d95;background:#0f172a;color:#e2e8f0;font-size:1rem;box-sizing:border-box;outline:none;"
          maxlength="30">
      </div>
      <button id="welcome-start-btn"
        style="background:linear-gradient(135deg,#7c3aed,#4c1d95);color:#fff;border:none;border-radius:12px;padding:16px 40px;font-size:1.1rem;cursor:pointer;width:100%;font-weight:900;letter-spacing:1px;transition:transform 0.15s;">
        Start Your Journey ⚡
      </button>
      <p style="color:#475569;font-size:0.75rem;margin-top:16px;">Math target: 750 | R&W target: 650 | Total: 1500+</p>
    </div>
  `;
  document.body.appendChild(modal);

  const startBtn = modal.querySelector('#welcome-start-btn');
  const nameInput = modal.querySelector('#welcome-name-input');

  startBtn.addEventListener('mouseenter', () => { startBtn.style.transform = 'scale(1.02)'; });
  startBtn.addEventListener('mouseleave', () => { startBtn.style.transform = 'scale(1)'; });

  startBtn.addEventListener('click', () => {
    const name = (nameInput.value || 'SAT Challenger').trim() || 'SAT Challenger';
    state.character.name = name;
    state.character.initialized = true;
    state.settings.name = name;
    saveState();
    modal.remove();
    renderAll();
    showToast(`Welcome, ${name}! Your quest begins! ⚔️`, 'success');
  });

  nameInput.addEventListener('keydown', e => { if (e.key === 'Enter') startBtn.click(); });
}

// ============================================================
// NAVIGATION
// ============================================================

let activeTab = 'dashboard';

function switchTab(tabName) {
  activeTab = tabName;

  // Update nav items — HTML uses data-panel, support both
  document.querySelectorAll('[data-tab],[data-panel]').forEach(el => {
    const key = el.dataset.tab || el.dataset.panel;
    el.classList.toggle('active', key === tabName);
  });

  // Show/hide sections using CSS class (styles.css: .tab-panel.active { display: block })
  document.querySelectorAll('.tab-panel').forEach(el => {
    el.classList.toggle('active', el.id === tabName);
  });

  // Re-render current tab
  switch (tabName) {
    case 'dashboard':     renderDashboard(); break;
    case 'skill-tree':   renderSkillTree('math'); break;
    case 'papers':       renderPapers(); break;
    case 'progress':     renderProgress(); break;
    case 'achievements': renderAchievements(); break;
  }
}

// ============================================================
// RENDER: HEADER
// ============================================================

function renderHeader() {
  const level = getLevelFromXP(state.character.totalXP);
  const title = getLevelTitle(level);
  const xpBar = getXPBar(state.character.totalXP);
  const daysLeft = getDaysUntilSAT();

  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  const style = (id, prop, val) => { const el = document.getElementById(id); if (el) el.style[prop] = val; };

  set('char-name', state.character.name);
  set('char-level', `Level ${level}`);
  set('char-title', title);
  set('char-streak', `🔥 ${state.character.streak}`);
  set('header-level', `Lv.${level}`);
  set('header-streak', `🔥 ${state.character.streak}`);
  set('header-title', title);
  set('days-until-sat', daysLeft);
  set('days-counter', `${daysLeft} days`);
  set('xp-text', `${state.character.totalXP.toLocaleString()} XP`);
  set('xp-label', `${Math.round(xpBar.current)} / ${xpBar.end - xpBar.start} XP to Level ${level + 1}`);
  set('total-xp-display', `Total XP: ${state.character.totalXP.toLocaleString()}`);
  style('xp-bar-fill', 'width', `${xpBar.pct.toFixed(1)}%`);
}

// ============================================================
// RENDER: DASHBOARD
// ============================================================

function renderDashboard() {
  renderHeader();
  generateDailyQuests();
  updateQuests();

  const pred = predictScore();
  const daysLeft = getDaysUntilSAT();

  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  const style = (id, prop, val) => { const el = document.getElementById(id); if (el) el.style[prop] = val; };
  const setHTML = (id, val) => { const el = document.getElementById(id); if (el) el.innerHTML = val; };

  set('pred-math', pred.math);
  set('pred-rw', pred.rw);
  set('pred-total', pred.total);
  set('pred-confidence', pred.confidence.toUpperCase());

  const mathPct  = Math.min(100, (pred.math  / 750) * 100);
  const rwPct    = Math.min(100, (pred.rw    / 650) * 100);
  const totalPct = Math.min(100, (pred.total / 1500) * 100);
  style('math-target-bar',  'width', `${mathPct.toFixed(1)}%`);
  style('rw-target-bar',    'width', `${rwPct.toFixed(1)}%`);
  style('total-target-bar', 'width', `${totalPct.toFixed(1)}%`);

  set('stat-sessions', state.sessions.length);
  set('stat-papers',   state.papers.length);
  set('stat-minutes',  state.character.totalStudyMinutes);
  set('stat-streak',   state.character.streak);
  set('stat-days',     daysLeft);

  const onTrackEl = document.getElementById('on-track-indicator');
  if (onTrackEl) {
    onTrackEl.textContent = pred.onTrack ? '✅ On Track for 1500+' : '⚠️ Need to Push Harder';
    onTrackEl.className = pred.onTrack ? 'on-track yes' : 'on-track no';
  }

  // Current dungeon week
  const currentWeek = getCurrentDungeonWeek();
  const weekEl = document.getElementById('current-week');
  if (weekEl) {
    if (currentWeek) {
      setHTML('current-week', `
        <span class="week-emoji">${currentWeek.emoji}</span>
        <strong>${currentWeek.name}</strong>
        <span style="color:#94a3b8;font-size:0.85rem;display:block;margin-top:2px;">${currentWeek.description}</span>
      `);
    } else {
      weekEl.textContent = 'Pre-study phase — June campaigns begin soon!';
    }
  }

  // Error analysis summary
  const errorAnalysis = analyzeErrorPatterns(state.papers);
  set('error-pattern', errorAnalysis.message);

  // Category XP bars
  const mathXPPct = Math.min(100, (state.character.mathXP / 2000) * 100);
  const rwXPPct   = Math.min(100, (state.character.rwXP   / 2000) * 100);
  style('math-xp-bar', 'width', `${mathXPPct.toFixed(1)}%`);
  style('rw-xp-bar',   'width', `${rwXPPct.toFixed(1)}%`);
  set('math-xp-val', `${state.character.mathXP.toLocaleString()} XP`);
  set('rw-xp-val',   `${state.character.rwXP.toLocaleString()} XP`);

  // Recent sessions
  renderRecentSessions();
}

function renderRecentSessions() {
  const el = document.getElementById('recent-sessions');
  if (!el) return;
  const recent = state.sessions.slice().reverse().slice(0, 5);
  if (!recent.length) {
    el.innerHTML = '<p class="satquest-empty">No sessions yet. Log your first study session!</p>';
    return;
  }
  el.innerHTML = recent.map(s => `
    <div class="satquest-session-item">
      <div class="satquest-session-topic">${getTopicDisplayName(s.topicKey)}</div>
      <div class="satquest-session-meta">
        ${formatDate(s.date)} &bull; ${s.minutes} min &bull; <span style="color:#7c3aed;">+${s.xpGained} XP</span>
      </div>
    </div>
  `).join('');
}

// ============================================================
// RENDER: SKILL TREE
// ============================================================

function renderSkillTree(category) {
  category = category || 'math';

  document.querySelectorAll('.skill-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.cat === category);
  });

  const container = document.getElementById('skill-tree-content');
  if (!container) return;

  const skills = state.skills[category];
  if (!skills) { container.innerHTML = '<p class="satquest-empty">No skill data available.</p>'; return; }

  const domainNames = {
    algebra: '⚗️ Algebra',
    advanced_math: '📐 Advanced Math',
    psda: '📊 Problem Solving & Data',
    geometry: '🔺 Geometry',
    info_ideas: '💡 Information & Ideas',
    craft_structure: '🔬 Craft & Structure',
    expression: '✍️ Expression of Ideas',
    sec: '📖 Standard English Conventions'
  };

  const statusIcons = {
    locked: '🔒', unlocked: '🔓', in_progress: '⚡', weak: '⚠️', steady: '📈', strong: '✅'
  };
  const statusColors = {
    locked: '#475569', unlocked: '#64748b', in_progress: '#7c3aed',
    weak: '#dc2626', steady: '#d97706', strong: '#16a34a'
  };
  const statusLabels = {
    locked: 'Locked', unlocked: 'Available', in_progress: 'In Progress',
    weak: 'Weak', steady: 'Steady', strong: 'Strong'
  };

  let html = '';
  for (const domain in skills) {
    const domainSkills = skills[domain];
    html += `<div class="satquest-skill-domain">`;
    html += `<h3 class="satquest-domain-title">${domainNames[domain] || domain}</h3>`;
    html += `<div class="satquest-skill-nodes">`;
    for (const topicKey in domainSkills) {
      const t = domainSkills[topicKey];
      if (!t || typeof t !== 'object' || !('sessions' in t)) continue;
      const status = t.status || 'locked';
      const accuracy = t.totalQ >= 5
        ? Math.round(((t.totalQ - t.wrongQ) / t.totalQ) * 100)
        : (t.totalQ > 0 ? Math.round(((t.totalQ - t.wrongQ) / t.totalQ) * 100) : null);
      const color = statusColors[status] || '#475569';
      html += `
        <div class="satquest-skill-node satquest-status-${status}" data-topic="${topicKey}"
          style="border-color:${color};" title="Click to log a session on this topic">
          <div class="satquest-node-icon">${statusIcons[status] || '?'}</div>
          <div class="satquest-node-name">${t.name}</div>
          <div class="satquest-node-sessions">${t.sessions} session${t.sessions !== 1 ? 's' : ''}</div>
          ${accuracy !== null ? `<div class="satquest-node-acc" style="color:${color};">${accuracy}% acc</div>` : ''}
          <div class="satquest-node-status" style="color:${color};">${statusLabels[status] || status}</div>
        </div>
      `;
    }
    html += `</div></div>`;
  }

  container.innerHTML = html || '<p class="satquest-empty">No topics found.</p>';

  container.querySelectorAll('.satquest-skill-node').forEach(node => {
    node.addEventListener('click', () => {
      const topicKey = node.dataset.topic;
      if (topicKey) openLogSessionModal(topicKey);
    });
  });
}

// ============================================================
// RENDER: PAPERS
// ============================================================

function renderPapers() {
  const container = document.getElementById('papers-list') || document.getElementById('paper-list');
  if (!container) return;

  if (!state.papers.length) {
    container.innerHTML = '<p class="satquest-empty">No papers logged yet. Add your first practice paper!</p>';
    return;
  }

  const sorted = state.papers.slice().sort((a, b) => new Date(b.date) - new Date(a.date));
  container.innerHTML = sorted.map(p => {
    const total = (p.mathScore || 0) + (p.rwScore || 0);
    const typeMap = { mock: '⚔️ Mock Test', diagnostic: '🔍 Diagnostic', practice: '📝 Practice', section: '📋 Section' };
    const typeLabel = typeMap[p.type] || '📝 Practice';
    const mathDiff = p.mathScore >= 750 ? '🎯' : p.mathScore >= 700 ? '⚡' : '';
    const rwDiff   = p.rwScore  >= 650 ? '🎯' : p.rwScore  >= 600 ? '⚡' : '';

    const wrongRows = p.wrongAnswers && p.wrongAnswers.length
      ? `<div class="satquest-paper-errors">
          <span style="color:#94a3b8;font-size:0.75rem;margin-right:6px;">Errors:</span>
          ${p.wrongAnswers.map(wa => `
            <span class="satquest-error-tag">${getTopicDisplayName(wa.topicKey)} (${wa.errorType}, ×${wa.count})</span>
          `).join('')}
        </div>`
      : '';

    return `
      <div class="satquest-paper-card">
        <div class="satquest-paper-header">
          <span class="satquest-paper-type">${typeLabel}</span>
          <span class="satquest-paper-date">${formatDate(p.date)}</span>
        </div>
        <div class="satquest-paper-scores">
          <div class="satquest-score-box satquest-math">
            <div class="satquest-score-label">Math ${mathDiff}</div>
            <div class="satquest-score-val">${p.mathScore}</div>
            <div class="satquest-score-sub">target: 750</div>
          </div>
          <div class="satquest-score-box satquest-rw">
            <div class="satquest-score-label">R&W ${rwDiff}</div>
            <div class="satquest-score-val">${p.rwScore}</div>
            <div class="satquest-score-sub">target: 650</div>
          </div>
          <div class="satquest-score-box satquest-total" style="${total >= 1500 ? 'border-color:#f59e0b;' : total >= 1400 ? 'border-color:#7c3aed;' : ''}">
            <div class="satquest-score-label">Total ${total >= 1500 ? '👑' : total >= 1400 ? '🌟' : ''}</div>
            <div class="satquest-score-val">${total}</div>
            <div class="satquest-score-sub">target: 1500</div>
          </div>
        </div>
        ${wrongRows}
        ${p.notes ? `<div class="satquest-paper-notes">"${p.notes}"</div>` : ''}
      </div>
    `;
  }).join('');
}

// ============================================================
// RENDER: PROGRESS
// ============================================================

function renderProgress() {
  renderDungeonMap();
  renderScoreChart();
  renderTopicChart();
  renderErrorAnalysis();
}

function renderDungeonMap() {
  const container = document.getElementById('dungeon-map');
  if (!container) return;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  container.innerHTML = DUNGEON_WEEKS.map(w => {
    const start = new Date(w.start);
    const end = new Date(w.end);
    end.setHours(23, 59, 59, 999);
    const isCurrent = today >= start && today <= end;
    const isPast    = today > end;

    let cls = 'satquest-dungeon-week';
    if (isCurrent) cls += ' satquest-dungeon-current';
    else if (isPast) cls += ' satquest-dungeon-past';
    if (w.isFinalBoss) cls += ' satquest-dungeon-boss';

    const topicTags = w.topics.filter(t => getTopicData(t)).map(t =>
      `<span class="satquest-dungeon-topic">${getTopicDisplayName(t)}</span>`
    ).join('');
    const specialTags = w.topics.filter(t => !getTopicData(t)).map(t =>
      `<span class="satquest-dungeon-topic special">${t.replace(/_/g, ' ')}</span>`
    ).join('');

    return `
      <div class="${cls}">
        <div class="satquest-dungeon-header">
          <span class="satquest-dungeon-emoji">${w.emoji}</span>
          <span class="satquest-dungeon-num">Week ${w.week}</span>
          ${isCurrent ? '<span class="satquest-dungeon-badge">⚡ CURRENT</span>' : ''}
          ${isPast ? '<span class="satquest-dungeon-badge satquest-past">✅ CLEARED</span>' : ''}
        </div>
        <div class="satquest-dungeon-name">${w.name}</div>
        <div class="satquest-dungeon-desc">${w.description}</div>
        <div class="satquest-dungeon-dates">${formatDate(w.start)} – ${formatDate(w.end)}</div>
        ${topicTags || specialTags
          ? `<div class="satquest-dungeon-topics">${topicTags}${specialTags}</div>`
          : ''}
      </div>
    `;
  }).join('');
}

function renderScoreChart() {
  // HTML canvas uses id="scoreChart"; dynamic modal fallback uses "score-chart"
  const canvas = document.getElementById('scoreChart') || document.getElementById('score-chart');
  if (!canvas) return;
  if (typeof Chart === 'undefined') return;

  if (scoreChart) { scoreChart.destroy(); scoreChart = null; }

  const papers = state.papers.slice().sort((a, b) => new Date(a.date) - new Date(b.date));

  if (!papers.length) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '16px system-ui,sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('No papers logged yet', canvas.width / 2, canvas.height / 2);
    return;
  }

  const labels = papers.map(p => formatDate(p.date));
  const mathScores = papers.map(p => p.mathScore);
  const rwScores   = papers.map(p => p.rwScore);

  const ctx = canvas.getContext('2d');
  scoreChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Math Score',
          data: mathScores,
          borderColor: '#7c3aed',
          backgroundColor: 'rgba(124,58,237,0.08)',
          tension: 0.3,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: '#7c3aed',
          fill: false
        },
        {
          label: 'R&W Score',
          data: rwScores,
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245,158,11,0.08)',
          tension: 0.3,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: '#f59e0b',
          fill: false
        },
        {
          label: 'Math Target (750)',
          data: labels.map(() => 750),
          borderColor: 'rgba(124,58,237,0.4)',
          borderDash: [6, 3],
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false
        },
        {
          label: 'R&W Target (650)',
          data: labels.map(() => 650),
          borderColor: 'rgba(245,158,11,0.4)',
          borderDash: [6, 3],
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: {
          min: 200, max: 800,
          grid: { color: 'rgba(255,255,255,0.07)' },
          ticks: { color: '#94a3b8', font: { size: 12 } }
        },
        x: {
          grid: { color: 'rgba(255,255,255,0.07)' },
          ticks: { color: '#94a3b8', font: { size: 12 } }
        }
      },
      plugins: {
        legend: { labels: { color: '#e2e8f0', font: { size: 12 } } },
        tooltip: {
          backgroundColor: 'rgba(15,23,42,0.95)',
          borderColor: '#7c3aed',
          borderWidth: 1,
          titleColor: '#c4b5fd',
          bodyColor: '#e2e8f0'
        }
      }
    }
  });
}

function renderTopicChart() {
  const canvas = document.getElementById('topic-chart');
  if (!canvas) return;
  if (typeof Chart === 'undefined') return;

  if (topicChart) { topicChart.destroy(); topicChart = null; }

  const studied = getAllTopics().filter(t => t.data.totalQ > 0);

  if (!studied.length) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '14px system-ui,sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('No accuracy data yet — attempt some questions!', canvas.width / 2, canvas.height / 2);
    return;
  }

  const sorted = studied.sort((a, b) => {
    const accA = (a.data.totalQ - a.data.wrongQ) / a.data.totalQ;
    const accB = (b.data.totalQ - b.data.wrongQ) / b.data.totalQ;
    return accA - accB; // ascending: worst first
  });

  const labels = sorted.map(t => t.data.name);
  const data   = sorted.map(t => Math.round(((t.data.totalQ - t.data.wrongQ) / t.data.totalQ) * 100));
  const colors = data.map(acc => acc >= 80 ? '#16a34a' : acc >= 60 ? '#d97706' : '#dc2626');

  const ctx = canvas.getContext('2d');
  topicChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Accuracy %',
        data,
        backgroundColor: colors,
        borderColor: colors.map(c => c + 'cc'),
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          min: 0, max: 100,
          grid: { color: 'rgba(255,255,255,0.07)' },
          ticks: { color: '#94a3b8', font: { size: 11 }, callback: v => v + '%' }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#94a3b8', font: { size: 11 } }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15,23,42,0.95)',
          borderColor: '#7c3aed',
          borderWidth: 1,
          callbacks: { label: ctx => `Accuracy: ${ctx.parsed.x}%` }
        }
      }
    }
  });
}

function renderErrorAnalysis() {
  const el = document.getElementById('error-analysis-detail');
  if (!el) return;

  const analysis = analyzeErrorPatterns(state.papers);
  if (!analysis.total) {
    el.innerHTML = '<p class="satquest-empty">Log papers with wrong answer details to see error analysis.</p>';
    return;
  }

  const { counts, total } = analysis;
  const pct = n => total > 0 ? Math.round((n / total) * 100) : 0;

  el.innerHTML = `
    <p style="color:#e2e8f0;font-weight:600;margin-bottom:16px;">${analysis.message}</p>
    <div style="display:flex;flex-direction:column;gap:12px;">
      ${[
        { label: 'Concept Gaps', key: 'conceptGap', color: '#dc2626' },
        { label: 'Careless Mistakes', key: 'careless', color: '#d97706' },
        { label: 'Time Pressure', key: 'timePressure', color: '#7c3aed' }
      ].map(item => `
        <div style="display:flex;align-items:center;gap:10px;font-size:0.85rem;">
          <span style="width:140px;color:#94a3b8;flex-shrink:0;">${item.label}</span>
          <div style="flex:1;height:10px;background:rgba(255,255,255,0.08);border-radius:5px;overflow:hidden;">
            <div style="width:${pct(counts[item.key])}%;height:100%;background:${item.color};border-radius:5px;transition:width 0.5s ease;"></div>
          </div>
          <span style="color:${item.color};font-weight:700;width:60px;text-align:right;">${counts[item.key]} (${pct(counts[item.key])}%)</span>
        </div>
      `).join('')}
    </div>
  `;
}

// ============================================================
// RENDER: ACHIEVEMENTS
// ============================================================

function renderAchievements() {
  const container = document.getElementById('achievements-grid');
  if (!container) return;

  const unlocked = Object.values(state.achievements).filter(a => a && a.unlocked).length;
  const total    = Object.keys(ACHIEVEMENTS).length;

  const progEl = document.getElementById('achievement-progress');
  if (progEl) progEl.textContent = `${unlocked} / ${total} Unlocked`;

  container.innerHTML = Object.entries(ACHIEVEMENTS).map(([key, def]) => {
    const ach = state.achievements[key];
    const isUnlocked = ach && ach.unlocked;
    return `
      <div class="satquest-achievement-card ${isUnlocked ? 'satquest-ach-unlocked' : 'satquest-ach-locked'}">
        <div class="satquest-ach-icon">${isUnlocked ? def.icon : '🔒'}</div>
        <div class="satquest-ach-name">${def.name}</div>
        <div class="satquest-ach-desc">${def.desc}</div>
        ${isUnlocked && ach.date ? `<div class="satquest-ach-date">${formatDate(ach.date)}</div>` : ''}
      </div>
    `;
  }).join('');
}

// ============================================================
// RENDER: QUESTS
// ============================================================

function updateQuests() {
  const container = document.getElementById('daily-quests');
  if (!container) return;

  const quests = state.dailyQuests || [];
  if (!quests.length) {
    container.innerHTML = '<p class="satquest-empty">Generating today\'s quests...</p>';
    return;
  }

  const questIcons = {
    new_concept: '📚', timed_practice: '⏱️', review: '🔄',
    problem_set: '📝', boss_battle: '⚔️'
  };

  container.innerHTML = quests.map(q => `
    <div class="satquest-quest-item ${q.completed ? 'satquest-quest-done' : ''}">
      <span class="satquest-quest-icon">${questIcons[q.type] || '🎯'}</span>
      <div class="satquest-quest-body">
        <div class="satquest-quest-desc">${q.description}</div>
        <div class="satquest-quest-xp">+${q.xp} XP</div>
      </div>
      <button class="satquest-quest-btn" onclick="completeQuest('${q.id}')" ${q.completed ? 'disabled' : ''}>
        ${q.completed ? '✅' : 'Complete'}
      </button>
    </div>
  `).join('');
}

// ============================================================
// MODAL: ADD PAPER
// ============================================================

function openAddPaperModal() {
  const modal = document.getElementById('add-paper-modal');
  if (!modal) { buildAddPaperModal(); return openAddPaperModal(); }
  const dateInput = document.getElementById('paper-date');
  if (dateInput) dateInput.value = todayString();
  const waContainer = document.getElementById('wrong-answers-container') || document.getElementById('wrong-answers-list');
  if (waContainer) waContainer.innerHTML = '';
  // Support both CSS-class modals (.open) and inline-style modals
  if (modal.classList.contains('modal-overlay')) modal.classList.add('open');
  else modal.style.display = 'flex';
}

function closeAddPaperModal() {
  const modal = document.getElementById('add-paper-modal');
  if (!modal) return;
  if (modal.classList.contains('modal-overlay')) modal.classList.remove('open');
  else modal.style.display = 'none';
}

function populateTopicSelect(sel) {
  if (!sel) return;
  const options = getAllTopicOptions();
  sel.innerHTML = '<option value="">Select Topic</option>' +
    options.map(o => `<option value="${o.key}">${o.label}</option>`).join('');
}

function addWrongAnswerRow() {
  const container = document.getElementById('wrong-answers-container');
  if (!container) return;
  const row = document.createElement('div');
  row.className = 'satquest-wa-row';
  row.style.cssText = 'display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap;';
  row.innerHTML = `
    <select class="wa-topic-select" style="${INPUT_STYLE_INLINE}flex:2;min-width:160px;"></select>
    <select class="wa-error-type" style="${INPUT_STYLE_INLINE}flex:1;min-width:120px;">
      <option value="conceptGap">Concept Gap</option>
      <option value="careless">Careless</option>
      <option value="timePressure">Time Pressure</option>
    </select>
    <input type="number" class="wa-count" min="1" max="50" value="1"
      style="${INPUT_STYLE_INLINE}width:64px;" placeholder="#">
    <button type="button" onclick="this.closest('.satquest-wa-row').remove()"
      style="background:#7f1d1d;color:#fca5a5;border:none;border-radius:6px;padding:6px 10px;cursor:pointer;flex-shrink:0;">✕</button>
  `;
  populateTopicSelect(row.querySelector('.wa-topic-select'));
  container.appendChild(row);
}

// Map human-readable topic names to state keys
function topicNameToKey(name) {
  const map = {
    'linear equations': 'linear_equations', 'systems of equations': 'systems_of_equations',
    'inequalities': 'inequalities', 'quadratics': 'quadratics', 'polynomials': 'polynomials',
    'exponential': 'exponential', 'exponential functions': 'exponential',
    'radical equations': 'radical_equations', 'ratios': 'ratios',
    'ratios & proportions': 'ratios', 'ratios and proportions': 'ratios',
    'percentages': 'percentages', 'statistics': 'statistics', 'probability': 'probability',
    'area & volume': 'area_volume', 'area and volume': 'area_volume', 'circles': 'circles',
    'right triangles': 'right_triangles', 'trigonometry': 'trig', 'basic trigonometry': 'trig',
    'central ideas': 'central_ideas', 'command of evidence': 'command_of_evidence',
    'inferences': 'inferences', 'vocabulary in context': 'vocabulary_in_context',
    'text structure': 'text_structure', 'text structure & purpose': 'text_structure',
    'cross-text connections': 'cross_text_connections', 'rhetorical synthesis': 'rhetorical_synthesis',
    'transitions': 'transitions', 'grammar': 'grammar', 'punctuation': 'punctuation',
    'sentence structure': 'sentence_structure'
  };
  return map[(name || '').toLowerCase().trim()] || name;
}

function submitPaperForm() {
  const dateInput  = document.getElementById('paper-date');
  // Support both paper-math-score (dynamic modal) and math-score (HTML modal)
  const mathInput  = document.getElementById('paper-math-score') || document.getElementById('math-score');
  const rwInput    = document.getElementById('paper-rw-score')   || document.getElementById('rw-score');
  const notesInput = document.getElementById('paper-notes');

  // Paper type: prefer select, fall back to active type-btn
  let paperType = 'practice';
  const typeSelect = document.getElementById('paper-type');
  if (typeSelect) {
    paperType = typeSelect.value;
  } else {
    const activeBtn = document.querySelector('#add-paper-modal .type-btn.active[data-type]');
    if (activeBtn) paperType = activeBtn.dataset.type;
  }

  if (!dateInput || !dateInput.value) { showToast('Please enter a date', 'error'); return; }
  if (!mathInput || !rwInput) { showToast('Score inputs missing', 'error'); return; }

  const mathScore = parseInt(mathInput.value);
  const rwScore   = parseInt(rwInput.value);
  if (isNaN(mathScore) || isNaN(rwScore)) { showToast('Please enter valid scores', 'error'); return; }
  if (mathScore < 200 || mathScore > 800)  { showToast('Math score must be 200–800', 'error'); return; }
  if (rwScore   < 200 || rwScore   > 800)  { showToast('R&W score must be 200–800', 'error'); return; }

  const wrongAnswers = [];
  // Collect from dynamically-added rows (app.js modal) AND HTML static rows
  const rowSelectors = '.satquest-wa-row, .wrong-answer-entry';
  document.querySelectorAll(rowSelectors).forEach(row => {
    const topicSel  = row.querySelector('.wa-topic-select');
    const errorSel  = row.querySelector('.wa-error-type, .wa-error-select');
    const countSel  = row.querySelector('.wa-count, .wa-count-input');
    const rawTopic  = topicSel ? topicSel.value : '';
    if (!rawTopic) return;
    const topicKey  = topicNameToKey(rawTopic);
    const errorType = errorSel ? (errorSel.value || 'conceptGap') : 'conceptGap';
    const count     = parseInt(countSel ? countSel.value : '1') || 1;
    wrongAnswers.push({ topicKey, errorType, count, category: getTopicCategory(topicKey) });
  });

  const paper = {
    id: generateId(),
    date: dateInput.value,
    type: typeSelect ? typeSelect.value : 'practice',
    mathScore,
    rwScore,
    wrongAnswers,
    notes: notesInput ? notesInput.value.trim() : '',
    analyzed: wrongAnswers.length > 0
  };

  addPaper(paper);
  const xpEarned = paper.type === 'mock' ? 500 : 300;
  showToast(`Paper logged! Total: ${mathScore + rwScore} | +${xpEarned} XP`, 'success');
  closeAddPaperModal();
  renderPapers();
  renderDashboard();
  renderHeader();
}

// ============================================================
// MODAL: LOG SESSION
// ============================================================

let activeLogTopicKey = null;

function openLogSessionModal(prefilledTopicKey) {
  let modal = document.getElementById('log-session-modal');
  if (!modal) { buildLogSessionModal(); modal = document.getElementById('log-session-modal'); }
  if (!modal) return;

  activeLogTopicKey = prefilledTopicKey || null;

  const topicSelect = document.getElementById('session-topic');
  if (topicSelect) {
    const options = getAllTopicOptions();
    topicSelect.innerHTML = '<option value="">Select Topic</option>' +
      options.map(o => `<option value="${o.key}" ${o.key === activeLogTopicKey ? 'selected' : ''}>${o.label}</option>`).join('');
  }

  const dateInput = document.getElementById('session-date');
  if (dateInput) {
    const now = new Date();
    dateInput.value = now.toISOString().slice(0, 16);
  }

  const slider = document.getElementById('session-minutes');
  if (slider) { slider.value = 30; updateDurationDisplay(); }

  // Clear question inputs
  const totalQ = document.getElementById('session-total-q');
  const wrongQ = document.getElementById('session-wrong-q');
  if (totalQ) totalQ.value = '';
  if (wrongQ) wrongQ.value = '';

  if (modal.classList.contains('modal-overlay')) modal.classList.add('open');
  else modal.style.display = 'flex';
}

function closeLogSessionModal() {
  const modal = document.getElementById('log-session-modal');
  if (modal) {
    if (modal.classList.contains('modal-overlay')) modal.classList.remove('open');
    else modal.style.display = 'none';
  }
  activeLogTopicKey = null;
}

function submitSessionForm() {
  const topicSelect  = document.getElementById('session-topic');
  const dateInput    = document.getElementById('session-date');
  // HTML modal uses session-duration; dynamic modal uses session-minutes
  const minutesInput = document.getElementById('session-minutes') || document.getElementById('session-duration');
  const typeSelect   = document.getElementById('session-type');
  const notesInput   = document.getElementById('session-notes');
  const totalQInput  = document.getElementById('session-total-q');
  const wrongQInput  = document.getElementById('session-wrong-q');

  if (!topicSelect || !topicSelect.value) { showToast('Please select a topic', 'error'); return; }

  // Resolve topic key — handle both raw keys and human-readable names
  const rawTopic = topicSelect.value;
  const topicKey = topicNameToKey(rawTopic);
  const minutes  = parseInt(minutesInput ? minutesInput.value : '30') || 30;
  const dateVal  = dateInput ? dateInput.value : new Date().toISOString();
  const totalQ   = parseInt(totalQInput ? totalQInput.value : '0') || 0;
  const wrongQ   = Math.min(parseInt(wrongQInput ? wrongQInput.value : '0') || 0, totalQ);

  // Update question counts on topic
  const topicInfo = getTopicData(topicKey);
  if (topicInfo && totalQ > 0) {
    topicInfo.data.totalQ += totalQ;
    topicInfo.data.wrongQ += wrongQ;
  }

  const session = {
    id: generateId(),
    date: dateVal || new Date().toISOString(),
    topicKey,
    category: getTopicCategory(topicKey),
    minutes,
    type: typeSelect ? typeSelect.value : 'practice',
    xpGained: 0,
    notes: notesInput ? notesInput.value.trim() : ''
  };

  addSession(session);
  showToast(`Session logged! +${session.xpGained} XP`, 'success');
  closeLogSessionModal();
  renderDashboard();
  renderHeader();
  if (activeTab === 'skill-tree') renderSkillTree('math');
}

// ============================================================
// DURATION SLIDER
// ============================================================

function updateDurationDisplay() {
  const slider  = document.getElementById('session-minutes');
  const display = document.getElementById('duration-display');
  if (!slider || !display) return;
  const val = parseInt(slider.value);
  if (val >= 60) {
    const h = Math.floor(val / 60);
    const m = val % 60;
    display.textContent = m > 0 ? `${h}h ${m}m` : `${h}h`;
  } else {
    display.textContent = `${val} min`;
  }
}

// ============================================================
// SETTINGS
// ============================================================

function saveSettings() {
  const nameInput   = document.getElementById('settings-name');
  const notifToggle = document.getElementById('settings-notifications');

  if (nameInput && nameInput.value.trim()) {
    state.character.name = nameInput.value.trim();
    state.settings.name  = state.character.name;
  }
  if (notifToggle) {
    state.settings.notifications = notifToggle.checked;
    if (notifToggle.checked) requestNotificationPermission();
  }
  saveState();
  renderHeader();
  showToast('Settings saved!', 'success');
}

function loadSettingsUI() {
  const nameInput   = document.getElementById('settings-name');
  const notifToggle = document.getElementById('settings-notifications');
  if (nameInput)   nameInput.value = state.character.name || 'SAT Challenger';
  if (notifToggle) notifToggle.checked = !!(state.settings && state.settings.notifications);
}

// ============================================================
// SERVICE WORKER & NOTIFICATIONS
// ============================================================

async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  try {
    await navigator.serviceWorker.register('/sat-prep/sw.js');
  } catch (e) {
    console.warn('Service worker registration failed:', e);
  }
}

async function requestNotificationPermission() {
  if (!('Notification' in window)) {
    showToast('Notifications not supported in this browser', 'info');
    return;
  }
  try {
    const permission = await Notification.requestPermission();
    if (permission === 'granted') {
      showToast('Notifications enabled!', 'success');
      scheduleNotifications();
    } else {
      showToast('Notification permission denied', 'error');
      state.settings.notifications = false;
      const toggle = document.getElementById('settings-notifications');
      if (toggle) toggle.checked = false;
      saveState();
    }
  } catch (e) {
    console.warn('Notification request failed:', e);
  }
}

function scheduleNotifications() {
  if (navigator.serviceWorker && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({
      type: 'SCHEDULE_NOTIFICATIONS',
      schedule: [
        { hour: 5, minute: 45, message: 'Morning Quest begins! 🌅 Start your SAT study block' },
        { hour: 18, minute: 30, message: 'Evening Study Block! ⚔️ Time to level up' },
        { dayOfWeek: 0, hour: 8, minute: 0, message: 'Full Paper Day! 📜 Boss Battle awaits' }
      ]
    });
  }
}

// ============================================================
// DATA RESET
// ============================================================

function resetAllData() {
  if (!confirm('⚠️ Reset ALL data? This cannot be undone!\n\nAll sessions, papers, XP, and achievements will be deleted.')) return;
  if (scoreChart) { scoreChart.destroy(); scoreChart = null; }
  if (topicChart) { topicChart.destroy(); topicChart = null; }
  localStorage.removeItem('satquest_state');
  location.reload();
}

// ============================================================
// FULL RENDER
// ============================================================

function renderAll() {
  renderHeader();
  renderDashboard();
}

// ============================================================
// INLINE STYLE CONSTANT
// ============================================================

const INPUT_STYLE_INLINE = 'padding:10px;border-radius:8px;border:1px solid #4c1d95;background:#0f172a;color:#e2e8f0;font-size:0.9rem;box-sizing:border-box;';

// ============================================================
// MODAL BUILDERS (programmatic — used if HTML doesn't include them)
// ============================================================

function buildAddPaperModal() {
  if (document.getElementById('add-paper-modal')) return;
  const modal = document.createElement('div');
  modal.id = 'add-paper-modal';
  modal.className = 'satquest-modal';
  modal.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,0.82);align-items:center;justify-content:center;z-index:1000;';
  modal.innerHTML = `
    <div style="background:#1e1b4b;border:1px solid #7c3aed;border-radius:16px;padding:32px;max-width:620px;width:92%;max-height:88vh;overflow-y:auto;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
        <h2 style="color:#c4b5fd;margin:0;font-size:1.25rem;">📜 Add Practice Paper</h2>
        <button id="close-paper-modal" style="background:none;border:none;color:#94a3b8;font-size:1.5rem;cursor:pointer;line-height:1;">✕</button>
      </div>
      <form id="add-paper-form">
        <div class="satquest-form-row">
          <label>Date</label>
          <input type="date" id="paper-date" required style="${INPUT_STYLE_INLINE}width:100%;">
        </div>
        <div class="satquest-form-row">
          <label>Paper Type</label>
          <select id="paper-type" style="${INPUT_STYLE_INLINE}width:100%;">
            <option value="practice">Practice Paper</option>
            <option value="mock">Mock Test (Full — 500 XP)</option>
            <option value="diagnostic">Diagnostic</option>
            <option value="section">Section Practice</option>
          </select>
        </div>
        <div class="satquest-form-row">
          <label>Math Score (200–800)</label>
          <input type="number" id="paper-math-score" min="200" max="800" step="10" placeholder="e.g. 580" required style="${INPUT_STYLE_INLINE}width:100%;">
        </div>
        <div class="satquest-form-row">
          <label>Reading & Writing Score (200–800)</label>
          <input type="number" id="paper-rw-score" min="200" max="800" step="10" placeholder="e.g. 540" required style="${INPUT_STYLE_INLINE}width:100%;">
        </div>
        <div class="satquest-form-row">
          <label>Notes (optional)</label>
          <textarea id="paper-notes" rows="2" placeholder="Any observations or focus areas..." style="${INPUT_STYLE_INLINE}width:100%;resize:vertical;"></textarea>
        </div>
        <div style="margin-top:16px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <label style="color:#a78bfa;font-weight:600;">Wrong Answer Analysis (optional)</label>
            <button type="button" id="add-wrong-answer-btn"
              style="background:#4c1d95;color:#c4b5fd;border:none;border-radius:8px;padding:6px 14px;cursor:pointer;font-size:0.85rem;">
              + Add Row
            </button>
          </div>
          <div id="wrong-answers-container"></div>
        </div>
        <button type="button" id="submit-paper-btn"
          style="margin-top:24px;width:100%;background:linear-gradient(135deg,#7c3aed,#4c1d95);color:#fff;border:none;border-radius:10px;padding:14px;font-size:1rem;cursor:pointer;font-weight:700;">
          Log Paper ⚡
        </button>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', e => { if (e.target === modal) closeAddPaperModal(); });
  document.getElementById('close-paper-modal').addEventListener('click', closeAddPaperModal);
  document.getElementById('add-wrong-answer-btn').addEventListener('click', addWrongAnswerRow);
  document.getElementById('submit-paper-btn').addEventListener('click', submitPaperForm);
}

function buildLogSessionModal() {
  if (document.getElementById('log-session-modal')) return;
  const modal = document.createElement('div');
  modal.id = 'log-session-modal';
  modal.className = 'satquest-modal';
  modal.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,0.82);align-items:center;justify-content:center;z-index:1000;';
  modal.innerHTML = `
    <div style="background:#1e1b4b;border:1px solid #7c3aed;border-radius:16px;padding:32px;max-width:500px;width:92%;max-height:88vh;overflow-y:auto;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
        <h2 style="color:#c4b5fd;margin:0;font-size:1.25rem;">⚡ Log Study Session</h2>
        <button id="close-session-modal" style="background:none;border:none;color:#94a3b8;font-size:1.5rem;cursor:pointer;line-height:1;">✕</button>
      </div>
      <form id="log-session-form">
        <div class="satquest-form-row">
          <label>Topic</label>
          <select id="session-topic" required style="${INPUT_STYLE_INLINE}width:100%;">
            <option value="">Select Topic</option>
          </select>
        </div>
        <div class="satquest-form-row">
          <label>Date & Time</label>
          <input type="datetime-local" id="session-date" style="${INPUT_STYLE_INLINE}width:100%;">
        </div>
        <div class="satquest-form-row">
          <label>Duration: <strong id="duration-display" style="color:#a78bfa;">30 min</strong></label>
          <input type="range" id="session-minutes" min="10" max="180" value="30" step="5" style="width:100%;margin-top:8px;accent-color:#7c3aed;">
        </div>
        <div class="satquest-form-row">
          <label>Session Type</label>
          <select id="session-type" style="${INPUT_STYLE_INLINE}width:100%;">
            <option value="practice">Practice Problems</option>
            <option value="concept">Concept Learning</option>
            <option value="review">Review / Revision</option>
            <option value="timed">Timed Drill</option>
          </select>
        </div>
        <div class="satquest-form-row">
          <label>Questions Attempted (optional)</label>
          <input type="number" id="session-total-q" min="0" max="500" placeholder="Total questions" style="${INPUT_STYLE_INLINE}width:100%;">
        </div>
        <div class="satquest-form-row">
          <label>Questions Wrong (optional)</label>
          <input type="number" id="session-wrong-q" min="0" max="500" placeholder="Wrong answers" style="${INPUT_STYLE_INLINE}width:100%;">
        </div>
        <div class="satquest-form-row">
          <label>Notes (optional)</label>
          <textarea id="session-notes" rows="2" placeholder="What did you focus on? Key takeaways?" style="${INPUT_STYLE_INLINE}width:100%;resize:vertical;"></textarea>
        </div>
        <button type="button" id="submit-session-btn"
          style="margin-top:24px;width:100%;background:linear-gradient(135deg,#7c3aed,#4c1d95);color:#fff;border:none;border-radius:10px;padding:14px;font-size:1rem;cursor:pointer;font-weight:700;">
          Log Session ⚡
        </button>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', e => { if (e.target === modal) closeLogSessionModal(); });
  document.getElementById('close-session-modal').addEventListener('click', closeLogSessionModal);
  document.getElementById('submit-session-btn').addEventListener('click', submitSessionForm);
  const slider = modal.querySelector('#session-minutes');
  if (slider) slider.addEventListener('input', updateDurationDisplay);
}

// ============================================================
// FALLBACK CSS INJECTION
// ============================================================

function injectStyles() {
  if (document.getElementById('satquest-app-styles')) return;
  const style = document.createElement('style');
  style.id = 'satquest-app-styles';
  style.textContent = `
    /* ---- Animations ---- */
    @keyframes satquest-pop {
      from { transform: scale(0.85); opacity: 0; }
      to   { transform: scale(1);    opacity: 1; }
    }

    /* ---- Toast ---- */
    .satquest-toast {
      background: #1e1b4b;
      border: 1px solid #7c3aed;
      color: #e2e8f0;
      padding: 12px 20px;
      border-radius: 10px;
      font-size: 0.88rem;
      line-height: 1.4;
      opacity: 0;
      transform: translateX(50px);
      transition: all 0.35s cubic-bezier(0.34,1.56,0.64,1);
      max-width: 340px;
      pointer-events: auto;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .satquest-toast-show { opacity: 1; transform: translateX(0); }
    .satquest-toast-success { border-color: #16a34a; }
    .satquest-toast-error   { border-color: #dc2626; }
    .satquest-toast-achievement { border-color: #f59e0b; background: #1c1410; }

    /* ---- Skill Tree ---- */
    .satquest-skill-domain  { margin-bottom: 28px; }
    .satquest-domain-title  { color: #a78bfa; font-size: 0.95rem; font-weight: 700; margin-bottom: 12px; letter-spacing: 0.5px; }
    .satquest-skill-nodes   { display: flex; flex-wrap: wrap; gap: 12px; }
    .satquest-skill-node    {
      border: 2px solid #475569; border-radius: 10px; padding: 14px 12px;
      min-width: 130px; max-width: 160px; cursor: pointer;
      transition: transform 0.15s, box-shadow 0.15s;
      background: rgba(15,23,42,0.75); text-align: center;
    }
    .satquest-skill-node:hover {
      transform: translateY(-3px);
      box-shadow: 0 6px 24px rgba(124,58,237,0.25);
    }
    .satquest-node-icon     { font-size: 1.4rem; margin-bottom: 6px; }
    .satquest-node-name     { color: #e2e8f0; font-size: 0.82rem; font-weight: 600; margin-bottom: 4px; line-height: 1.3; }
    .satquest-node-sessions { color: #64748b; font-size: 0.72rem; }
    .satquest-node-acc      { font-size: 0.78rem; font-weight: 700; margin-top: 4px; }
    .satquest-node-status   { font-size: 0.7rem; margin-top: 3px; text-transform: capitalize; }

    /* ---- Papers ---- */
    .satquest-paper-card    { background: rgba(30,27,75,0.7); border: 1px solid #312e81; border-radius: 12px; padding: 20px; margin-bottom: 16px; transition: border-color 0.2s; }
    .satquest-paper-card:hover { border-color: #7c3aed; }
    .satquest-paper-header  { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .satquest-paper-type    { color: #a78bfa; font-weight: 700; font-size: 0.88rem; }
    .satquest-paper-date    { color: #64748b; font-size: 0.82rem; }
    .satquest-paper-scores  { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
    .satquest-score-box     { flex: 1; min-width: 90px; background: rgba(15,23,42,0.8); border-radius: 8px; padding: 12px; text-align: center; border: 1px solid #1e2d4a; }
    .satquest-math          { border-color: rgba(124,58,237,0.5) !important; }
    .satquest-rw            { border-color: rgba(245,158,11,0.5) !important; }
    .satquest-total         { border-color: rgba(22,163,74,0.5) !important; }
    .satquest-score-label   { color: #94a3b8; font-size: 0.72rem; margin-bottom: 4px; }
    .satquest-score-val     { font-size: 1.7rem; font-weight: 900; color: #e2e8f0; line-height: 1; }
    .satquest-score-sub     { color: #475569; font-size: 0.68rem; margin-top: 3px; }
    .satquest-paper-errors  { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; align-items: center; }
    .satquest-error-tag     { background: rgba(220,38,38,0.15); border: 1px solid rgba(220,38,38,0.35); border-radius: 6px; padding: 3px 8px; font-size: 0.72rem; color: #fca5a5; }
    .satquest-paper-notes   { color: #94a3b8; font-size: 0.82rem; font-style: italic; border-top: 1px solid #1e2d4a; padding-top: 10px; margin-top: 8px; }

    /* ---- Achievements ---- */
    .satquest-achievement-card  {
      background: rgba(15,23,42,0.8); border: 1px solid #1e2d4a; border-radius: 10px;
      padding: 16px 12px; text-align: center; transition: all 0.2s;
    }
    .satquest-ach-unlocked { border-color: #7c3aed !important; background: rgba(124,58,237,0.1) !important; }
    .satquest-ach-locked   { opacity: 0.45; filter: grayscale(0.8); }
    .satquest-ach-icon     { font-size: 2rem; margin-bottom: 8px; }
    .satquest-ach-name     { color: #e2e8f0; font-weight: 700; font-size: 0.85rem; margin-bottom: 4px; }
    .satquest-ach-desc     { color: #94a3b8; font-size: 0.76rem; line-height: 1.4; }
    .satquest-ach-date     { color: #7c3aed; font-size: 0.7rem; margin-top: 6px; }

    /* ---- Quests ---- */
    .satquest-quest-item {
      display: flex; align-items: center; gap: 12px;
      background: rgba(15,23,42,0.7); border: 1px solid #1e2d4a; border-radius: 10px;
      padding: 12px 14px; margin-bottom: 10px; transition: border-color 0.2s;
    }
    .satquest-quest-item:hover { border-color: #4c1d95; }
    .satquest-quest-done { opacity: 0.45; }
    .satquest-quest-icon { font-size: 1.35rem; flex-shrink: 0; }
    .satquest-quest-body { flex: 1; min-width: 0; }
    .satquest-quest-desc { color: #e2e8f0; font-size: 0.86rem; line-height: 1.4; }
    .satquest-quest-xp   { color: #7c3aed; font-size: 0.78rem; font-weight: 700; margin-top: 3px; }
    .satquest-quest-btn  {
      background: #7c3aed; color: #fff; border: none; border-radius: 7px;
      padding: 7px 14px; font-size: 0.8rem; cursor: pointer; flex-shrink: 0;
      transition: background 0.15s;
    }
    .satquest-quest-btn:hover:not(:disabled) { background: #6d28d9; }
    .satquest-quest-btn:disabled { background: #334155; cursor: default; }

    /* ---- Sessions ---- */
    .satquest-session-item   { border-bottom: 1px solid #1e2d4a; padding: 10px 0; }
    .satquest-session-item:last-child { border-bottom: none; }
    .satquest-session-topic  { color: #c4b5fd; font-weight: 600; font-size: 0.88rem; }
    .satquest-session-meta   { color: #64748b; font-size: 0.78rem; margin-top: 2px; }

    /* ---- Dungeon Map ---- */
    .satquest-dungeon-week    { background: rgba(15,23,42,0.7); border: 1px solid #1e2d4a; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
    .satquest-dungeon-current { border-color: #7c3aed !important; background: rgba(124,58,237,0.08) !important; }
    .satquest-dungeon-past    { opacity: 0.55; }
    .satquest-dungeon-boss    { border-color: #f59e0b !important; background: rgba(245,158,11,0.06) !important; }
    .satquest-dungeon-header  { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
    .satquest-dungeon-emoji   { font-size: 1.3rem; }
    .satquest-dungeon-num     { color: #64748b; font-size: 0.78rem; }
    .satquest-dungeon-badge   { background: #7c3aed; color: #fff; border-radius: 6px; padding: 2px 8px; font-size: 0.68rem; font-weight: 700; }
    .satquest-past            { background: #16a34a !important; }
    .satquest-dungeon-name    { color: #e2e8f0; font-weight: 700; font-size: 0.95rem; margin-bottom: 3px; }
    .satquest-dungeon-desc    { color: #94a3b8; font-size: 0.82rem; margin-bottom: 4px; }
    .satquest-dungeon-dates   { color: #475569; font-size: 0.73rem; margin-bottom: 8px; }
    .satquest-dungeon-topics  { display: flex; flex-wrap: wrap; gap: 6px; }
    .satquest-dungeon-topic   { background: rgba(124,58,237,0.15); border: 1px solid rgba(124,58,237,0.25); border-radius: 6px; padding: 2px 8px; font-size: 0.72rem; color: #a78bfa; }
    .satquest-dungeon-topic.special { background: rgba(100,116,139,0.15); border-color: rgba(100,116,139,0.25); color: #94a3b8; }

    /* ---- Forms ---- */
    .satquest-form-row        { margin-bottom: 16px; }
    .satquest-form-row label  { display: block; color: #a78bfa; margin-bottom: 6px; font-size: 0.88rem; font-weight: 600; }

    /* ---- Empty State ---- */
    .satquest-empty { color: #475569; font-style: italic; text-align: center; padding: 24px 16px; }

    /* ---- Skill tab ---- */
    .skill-tab {
      background: rgba(30,27,75,0.7); color: #94a3b8;
      border: 1px solid #4c1d95; border-radius: 8px;
      padding: 8px 20px; cursor: pointer; transition: all 0.2s; font-size: 0.9rem;
    }
    .skill-tab.active      { background: #7c3aed; color: #fff; border-color: #7c3aed; }
    .skill-tab:hover:not(.active) { border-color: #7c3aed; color: #c4b5fd; }
  `;
  document.head.appendChild(style);
}

// ============================================================
// EVENT BINDING
// ============================================================

function bindEvents() {
  // Nav tabs
  document.querySelectorAll('[data-tab]').forEach(el => {
    el.addEventListener('click', () => switchTab(el.dataset.tab));
  });

  // Skill tree tabs
  document.querySelectorAll('.skill-tab').forEach(btn => {
    btn.addEventListener('click', () => renderSkillTree(btn.dataset.cat));
  });

  // Add Paper button (may be in HTML)
  const addPaperBtn = document.getElementById('add-paper-btn');
  if (addPaperBtn) addPaperBtn.addEventListener('click', openAddPaperModal);

  // Log Session button (may be in HTML)
  const logSessionBtn = document.getElementById('log-session-btn');
  if (logSessionBtn) logSessionBtn.addEventListener('click', () => openLogSessionModal(null));

  // Settings save (may be in HTML)
  const settingsSaveBtn = document.getElementById('settings-save-btn');
  if (settingsSaveBtn) settingsSaveBtn.addEventListener('click', saveSettings);

  // Reset data (may be in HTML)
  const resetBtn = document.getElementById('reset-data-btn');
  if (resetBtn) resetBtn.addEventListener('click', resetAllData);

  // Escape key closes modals
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeAddPaperModal();
      closeLogSessionModal();
    }
  });

  // Close modals when clicking overlay (for any existing HTML modals)
  document.querySelectorAll('.modal, .satquest-modal').forEach(modal => {
    modal.addEventListener('click', e => {
      if (e.target === modal) modal.style.display = 'none';
    });
  });
}

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  loadState();
  injectStyles();
  createToastContainer();
  buildAddPaperModal();
  buildLogSessionModal();
  bindEvents();
  generateDailyQuests();
  recalculateTopicStatuses();
  checkAllAchievements();
  loadSettingsUI();
  registerServiceWorker();

  if (!state.character.initialized) {
    showWelcomeModal();
  } else {
    switchTab('dashboard');
  }
});

// ============================================================
// GLOBAL EXPORTS — for HTML onclick="" attributes
// ============================================================

window.switchTab           = switchTab;
window.openAddPaperModal   = openAddPaperModal;
window.closeAddPaperModal  = closeAddPaperModal;
window.openLogSessionModal = openLogSessionModal;
window.openSessionModal    = openLogSessionModal;  // alias for HTML skill-node onclicks
window.closeLogSessionModal= closeLogSessionModal;
window.addWrongAnswerRow   = addWrongAnswerRow;
window.submitPaperForm     = submitPaperForm;
window.submitSessionForm   = submitSessionForm;
window.completeQuest       = completeQuest;
window.renderSkillTree     = renderSkillTree;
window.saveSettings        = saveSettings;
window.resetAllData        = resetAllData;
window.updateDurationDisplay = updateDurationDisplay;
