// Motor del juego en JavaScript para la versión de un solo archivo (sin servidor).
//
// Es un port fiel de bones_bullets/{dice,hands,revolver,game,duel,ai}.py y de
// serialize()/apply_action() de server.py: devuelve exactamente los mismos
// objetos de estado, así que la interfaz de web/index.html no cambia nada.
// Si tocas las reglas en Python, hay que tocarlas aquí igual.
(function (global) {
  "use strict";

  // --- azar reproducible (no coincide con el random de Python, pero una semilla
  //     siempre da la misma partida dentro de esta versión) -------------------
  function RNG(seed) {
    this.s = (seed >>> 0) || 1;
  }
  RNG.prototype.next = function () {
    this.s = (this.s + 0x6D2B79F5) >>> 0;
    let t = this.s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  RNG.prototype.randrange = function (n) { return Math.floor(this.next() * n); };
  RNG.prototype.choice = function (list) { return list[this.randrange(list.length)]; };
  RNG.prototype.shuffle = function (list) {
    for (let i = list.length - 1; i > 0; i--) { const j = this.randrange(i + 1); [list[i], list[j]] = [list[j], list[i]]; }
  };
  RNG.prototype.sample = function (list, k) { const c = list.slice(); this.shuffle(c); return c.slice(0, k); };

  // --- constantes de balance (game.py) --------------------------------------
  const FACES = [1, 2, 3, 4, 5, 6];
  const MAX_LEVEL = 8, HANDS_PER_LEVEL = 3, MAX_WOUNDS = 3;
  const CYLINDER_SIZE = 6, LIVE_ROUNDS = 1, SILVER_MULT = 3.0;
  const UPGRADE_CHOICES = 3, STREAK_BONUS = 0.5;
  const LOADED_FACES = [3, 4, 5, 6, 6, 6];
  const levelTarget = n => 40 + 25 * n + 4 * n * n;

  const HIGH = "carta alta", PAIR = "pareja", TWO_PAIR = "dobles parejas", THREE = "trío",
        STRAIGHT = "escalera", FULL = "full", FOUR = "póker", FIVE = "repóker";
  const BASE_MULT = { [HIGH]: 1, [PAIR]: 1.5, [TWO_PAIR]: 2, [THREE]: 3, [STRAIGHT]: 5, [FULL]: 6, [FOUR]: 8, [FIVE]: 12 };

  // Python redondea al par en los empates (round(16.5) == 16) y JS no: sin esto
  // las manos con .5 puntúan uno de más respecto a la versión de Python.
  function pyRound(x) {
    const piso = Math.floor(x), resto = x - piso;
    if (Math.abs(resto - 0.5) > 1e-9) return Math.round(x);
    return piso % 2 === 0 ? piso : piso + 1;
  }

  function evaluate(values) {
    const v = values.slice().sort((a, b) => a - b);
    const c = {};
    v.forEach(x => { c[x] = (c[x] || 0) + 1; });
    const counts = Object.values(c).sort((a, b) => b - a);
    if (counts[0] === 5) return FIVE;
    if (counts[0] === 4) return FOUR;
    if (counts[0] === 3 && counts[1] === 2) return FULL;
    if (v.length === 5 && counts.length === 5 && v[4] - v[0] === 4) return STRAIGHT;
    if (counts[0] === 3) return THREE;
    if (counts[0] === 2 && counts[1] === 2) return TWO_PAIR;
    if (counts[0] === 2) return PAIR;
    return HIGH;
  }
  function scoreOf(values, mults) {
    const hand = evaluate(values);
    const total = values.reduce((a, b) => a + b, 0);
    const mult = (mults || BASE_MULT)[hand];
    return { hand, total, mult, points: pyRound(total * mult) };
  }
  // la mano que se muestra: multiplicador con racha y plata aplicadas
  function handWith(values, mults, streak, silver) {
    const s = scoreOf(values, mults);
    let mult = s.mult + streak * STREAK_BONUS;
    if (silver) mult *= SILVER_MULT;
    return { hand: s.hand, total: s.total, mult, points: pyRound(s.total * mult) };
  }

  // --- dados ----------------------------------------------------------------
  const newDie = () => ({ value: 1, locked: false, faces: FACES.slice() });
  function newHand(rng) { return Array.from({ length: 5 }, () => { const d = newDie(); d.value = rng.choice(d.faces); return d; }); }
  function rollAll(dice, rng) { dice.forEach(d => { if (!d.locked) d.value = rng.choice(d.faces); }); }
  const unlockAll = dice => dice.forEach(d => { d.locked = false; });
  const isLoaded = d => d.faces.join() === LOADED_FACES.join();

  // --- revólver (revolver.py) ----------------------------------------------
  function Cylinder(size, live) {
    this.size = size; this.live = live; this.blanks = 0; this.silver = 0; this.bounce = 0; this.chambers = [];
  }
  Cylinder.prototype.reload = function (rng) {
    const c = [];
    for (let i = 0; i < this.live; i++) c.push("LIVE");
    for (let i = 0; i < this.blanks; i++) c.push("BLANK");
    for (let i = 0; i < this.silver; i++) c.push("SILVER");
    for (let i = 0; i < this.bounce; i++) c.push("BOUNCE");
    while (c.length < this.size) c.push("EMPTY");
    rng.shuffle(c); this.chambers = c;
  };
  Cylinder.prototype.pullTrigger = function (rng) {
    if (!this.chambers.length) this.reload(rng);
    const chamber = this.chambers.splice(rng.randrange(this.chambers.length), 1)[0];
    if (chamber === "LIVE" || !this.chambers.length) this.reload(rng);
    return chamber;
  };
  Cylinder.prototype.known = function () {
    const n = k => this.chambers.filter(c => c === k).length;
    return { remaining: this.chambers.length, live: n("LIVE"), blank: n("BLANK"), silver: n("SILVER"), bounce: n("BOUNCE") };
  };
  Cylinder.prototype.risk = function () { return this.chambers.length ? this.chambers.filter(c => c === "LIVE").length / this.chambers.length : 0; };

  // --- mejoras (game.py) ----------------------------------------------------
  const UPGRADES = {
    MULT_PAIR: "+1 mult. pareja", MULT_TWO_PAIR: "+1 mult. dobles parejas", MULT_THREE: "+1 mult. trío",
    MULT_STRAIGHT: "+1 mult. escalera", MULT_FULL: "+1 mult. full",
    ADD_BLANK: "Fogueo: +1 recámara inofensiva en el tambor",
    ADD_SILVER: "Plata: +1 recámara que triplica la mano",
    ADD_BOUNCE: "Rebote: +1 recámara que relanza dos veces y se queda con lo mejor",
    LOADED_DIE: "Dado cargado: un dado pasa a tener caras 3-4-5-6-6-6",
    SHIELD: "Chaleco: la primera bala de cada nivel no hiere",
    EXTRA_HAND: "Mano extra: +1 mano por nivel",
    HEAL: "Curar 1 herida",
  };
  const MULT_UPGRADES = { MULT_PAIR: PAIR, MULT_TWO_PAIR: TWO_PAIR, MULT_THREE: THREE, MULT_STRAIGHT: STRAIGHT, MULT_FULL: FULL };
  const UPGRADE_DESC = {
    ADD_BLANK: "Una recámara más en el tambor que nunca hiere.",
    ADD_SILVER: "Una recámara que triplica la mano en la que sale.",
    ADD_BOUNCE: "Una recámara que relanza dos veces y se queda con lo mejor.",
    LOADED_DIE: "Un dado pasa a tener caras 3-4-5-6-6-6.",
    SHIELD: "La primera bala de cada nivel no hiere.",
    EXTRA_HAND: "Una mano más en cada nivel.",
    HEAL: "Recuperas un corazón.",
  };
  function upgradeInfo(id) {
    const name = UPGRADES[id].split(":")[0];
    return { id, name, desc: UPGRADE_DESC[id] || `El multiplicador de ${name.slice(8)} sube en 1.` };
  }

  const fmt = x => (Number.isInteger(x) ? String(x) : String(Math.round(x * 1000) / 1000));

  // --- partida en solitario (game.py) --------------------------------------
  function Game(rng) {
    this.rng = rng; this.level = 1; this.score = 0;
    this.maxHands = HANDS_PER_LEVEL; this.handsLeft = HANDS_PER_LEVEL; this.wounds = 0;
    this.dice = newHand(rng);
    this.cylinder = new Cylinder(CYLINDER_SIZE, LIVE_ROUNDS); this.cylinder.reload(rng);
    this.mults = Object.assign({}, BASE_MULT);
    this.silver = false; this.streak = 0; this.shieldMax = 0; this.shield = 0;
    this.pulled = false; this.pending = []; this.message = "";
  }
  Game.prototype.target = function () { return levelTarget(this.level); };
  Game.prototype.cleared = function () { return this.score >= this.target(); };
  Game.prototype.gameOver = function () { return this.wounds >= MAX_WOUNDS || (this.handsLeft <= 0 && this.score < this.target()); };
  Game.prototype.hand = function () { return handWith(this.dice.map(d => d.value), this.mults, this.streak, this.silver); };
  Game.prototype.toggleLock = function (i) { this.dice[i].locked = !this.dice[i].locked; return this.dice[i].locked; };
  Game.prototype.resetHand = function () { this.silver = false; this.streak = 0; unlockAll(this.dice); rollAll(this.dice, this.rng); };
  Game.prototype.pullTrigger = function () {
    this.pulled = true;
    const chamber = this.cylinder.pullTrigger(this.rng);
    if (chamber === "LIVE") {
      if (this.shield > 0) {
        this.shield -= 1; rollAll(this.dice, this.rng);
        this.message = "¡BANG! ...el chaleco aguanta. Sin herida. Relanzas los dados libres.";
        return { chamber, wounded: false, shielded: true };
      }
      this.wounds += 1; this.handsLeft -= 1; this.resetHand();
      this.message = "¡BANG! Herida. La mano se pierde y el tambor se recarga.";
      return { chamber, wounded: true, shielded: false };
    }
    this.streak += 1;
    if (chamber === "SILVER") this.silver = true;
    if (chamber === "BOUNCE") {
      rollAll(this.dice, this.rng);
      const first = this.hand().points;
      const snapshot = this.dice.map(d => d.value);
      rollAll(this.dice, this.rng);
      if (this.hand().points < first) this.dice.forEach((d, i) => { d.value = snapshot[i]; });
    } else rollAll(this.dice, this.rng);
    const texts = {
      EMPTY: "Click. Relanzas los dados libres.",
      BLANK: "Fogueo. Relanzas los dados libres.",
      SILVER: `¡Plata! Esta mano vale x${fmt(SILVER_MULT)}. Relanzas los dados libres.`,
      BOUNCE: "¡Rebote! Dos tiradas y te quedas con la mejor.",
    };
    this.message = texts[chamber] + ` Racha ${this.streak}: +${fmt(this.streak * STREAK_BONUS)} al multiplicador.`;
    return { chamber, wounded: false, shielded: false };
  };
  Game.prototype.playHand = function () {
    const r = this.hand();
    this.score += r.points; this.handsLeft -= 1; this.resetHand();
    this.message = `${r.hand}: ${r.total} × ${fmt(r.mult)} = ${r.points}`;
    if (this.cleared()) {
      if (!this.pulled && this.wounds > 0) { this.wounds -= 1; this.message += " Sangre fría: curas 1 herida."; }
      this.offerUpgrades();
    }
    return r;
  };
  Game.prototype.offerUpgrades = function () {
    let pool = Object.keys(UPGRADES);
    if (this.wounds === 0) pool = pool.filter(u => u !== "HEAL");
    if (this.shieldMax > 0) pool = pool.filter(u => u !== "SHIELD");
    if (this.dice.every(isLoaded)) pool = pool.filter(u => u !== "LOADED_DIE");
    this.pending = this.rng.sample(pool, Math.min(UPGRADE_CHOICES, pool.length));
    return this.pending;
  };
  Game.prototype.applyUpgrade = function (u) {
    if (MULT_UPGRADES[u]) this.mults[MULT_UPGRADES[u]] += 1;
    else if (u === "ADD_BLANK") this.cylinder.blanks += 1;
    else if (u === "ADD_SILVER") this.cylinder.silver += 1;
    else if (u === "ADD_BOUNCE") this.cylinder.bounce += 1;
    else if (u === "LOADED_DIE") { const d = this.dice.find(x => !isLoaded(x)); if (d) d.faces = LOADED_FACES.slice(); }
    else if (u === "SHIELD") this.shieldMax += 1;
    else if (u === "EXTRA_HAND") this.maxHands += 1;
    else if (u === "HEAL") this.wounds = Math.max(0, this.wounds - 1);
    this.pending = [];
  };
  Game.prototype.nextLevel = function () {
    this.level += 1; this.score = 0; this.handsLeft = this.maxHands; this.shield = this.shieldMax;
    this.pulled = false; this.pending = [];
    this.cylinder.reload(this.rng); this.resetHand();
  };

  // --- duelo (duel.py) ------------------------------------------------------
  function Player(name, isAI, maxWounds) {
    this.name = name; this.isAI = !!isAI; this.wounds = 0; this.maxWounds = maxWounds || MAX_WOUNDS;
    this.dice = []; this.streak = 0; this.silver = false; this.played = null; this.banged = false; this.roundsWon = 0;
  }
  Player.prototype.alive = function () { return this.wounds < this.maxWounds; };
  const who = (p, third, second) => (p.name === "Tú" ? second.charAt(0).toUpperCase() + second.slice(1) : `${p.name} ${third}`);

  function Duel(rng, players, cylinder) {
    this.rng = rng; this.players = players; this.cylinder = cylinder;
    this.mults = Object.assign({}, BASE_MULT);
    this.round = 1; this.turn = 0; this.message = ""; this.lastRound = null;
    this.players.forEach(p => { if (!p.dice.length) p.dice = newHand(rng); });
    if (!this.cylinder.chambers.length) this.cylinder.reload(rng);
  }
  Duel.prototype.current = function () { return this.players[this.turn]; };
  Duel.prototype.other = function (p) { return this.players.find(q => q !== p); };
  Duel.prototype.winner = function () { const a = this.players.filter(p => p.alive()); return a.length === 1 ? a[0] : null; };
  Duel.prototype.gameOver = function () { return this.winner() !== null; };
  Duel.prototype.handOf = function (p) { return handWith(p.dice.map(d => d.value), this.mults, p.streak, p.silver); };
  Duel.prototype.toggleLock = function (i) { const d = this.current().dice; d[i].locked = !d[i].locked; return d[i].locked; };

  Duel.prototype.pullTrigger = function (target) {
    const p = this.current();
    if (target === "rival") return this.shootRival();
    const chamber = this.cylinder.pullTrigger(this.rng);
    if (chamber === "LIVE") {
      p.wounds += 1; p.banged = true;
      p.played = { hand: HIGH, total: 0, mult: 0, points: 0 };
      const verb = p.name === "Tú" ? "pierdes" : "pierde";
      this.message = `¡BANG! ${who(p, "recibe", "recibes")} una herida y ${verb} la mano.`;
      this.endTurn();
      return { chamber, wounded: true };
    }
    p.streak += 1;
    if (chamber === "SILVER") p.silver = true;
    rollAll(p.dice, this.rng);
    this.message = `${p.name === "Tú" ? "Click" : p.name + ": click"}. Racha ${p.streak}.`;
    return { chamber, wounded: false };
  };
  Duel.prototype.shootRival = function () {
    const p = this.current(), other = this.other(p);
    const chamber = this.cylinder.pullTrigger(this.rng);
    if (chamber === "LIVE") {
      other.wounds += 1;
      this.message = `¡BANG! ${who(other, "recibe", "recibes")} la bala: una herida.`;
      if (!other.alive()) this.message += ` ${who(p, "gana", "ganas")} el duelo.`;
      return { chamber, wounded: true };
    }
    const head = p.name === "Tú" ? "Click" : p.name + ": click";
    this.message = `${head}. El disparo falla: ${p.name === "Tú" ? "tu" : "su"} mano vale cero esta ronda.`;
    p.played = { hand: HIGH, total: 0, mult: 0, points: 0 };
    this.endTurn();
    return { chamber, wounded: false };
  };
  Duel.prototype.playHand = function () {
    const p = this.current(), r = this.handOf(p);
    p.played = r;
    this.message = `${who(p, "juega", "juegas")} ${r.hand}: ${r.total} × ${fmt(r.mult)} = ${r.points}.`;
    this.endTurn();
    return r;
  };
  Duel.prototype.endTurn = function () {
    const p = this.current();
    p.streak = 0; p.silver = false; unlockAll(p.dice);
    if (this.players.every(q => q.played)) this.resolveRound();
    else this.turn = (this.turn + 1) % this.players.length;
  };
  Duel.prototype.resolveRound = function () {
    const [a, b] = this.players, pa = a.played.points, pb = b.played.points;
    let loser = null, summary;
    if (pa === pb) summary = `Ronda ${this.round}: empate a ${pa}. Nadie sangra.`;
    else {
      const winner = pa > pb ? a : b; loser = pa > pb ? b : a;
      winner.roundsWon += 1;
      summary = `Ronda ${this.round}: ${who(winner, "gana", "ganas")} ${Math.max(pa, pb)} a ${Math.min(pa, pb)}.`;
      if (loser.banged) summary += ` ${who(loser, "ya sangró", "ya sangraste")} por la bala.`;
      else { loser.wounds += 1; summary += ` ${who(loser, "recibe", "recibes")} una herida.`; }
    }
    this.lastRound = {
      round: this.round, points: [pa, pb], loser: loser ? loser.name : null,
      hands: this.players.map(p => ({ hand: p.played.hand, total: p.played.total, mult: p.played.mult,
                                      points: p.played.points, dice: p.dice.map(d => d.value), banged: p.banged })),
    };
    this.message += " " + summary;
    if (this.gameOver()) { this.message += ` ${who(this.winner(), "gana", "ganas")} el duelo.`; return; }
    this.round += 1;
    this.turn = loser ? this.players.indexOf(loser) : (this.turn + 1) % 2;
    this.players.forEach(p => { p.played = null; p.banged = false; rollAll(p.dice, this.rng); });
  };

  // --- rivales (ai.py) ------------------------------------------------------
  const SAMPLES = 32;
  const PERSONALITIES = {
    cauto: { key: "cauto", name: "El Cauto", maxRisk: 0.20, greed: 0.9, taunt: "Prefiero llegar vivo a casa.", lives: 3, liveRounds: 1, smart: false },
    tahur: { key: "tahur", name: "El Tahúr", maxRisk: 0.34, greed: 1.1, taunt: "Las cartas no mienten. Los dados tampoco.", lives: 3, liveRounds: 1, smart: false },
    loco: { key: "loco", name: "El Loco", maxRisk: 0.50, greed: 1.4, taunt: "¿Solo una bala? Qué aburrido.", lives: 3, liveRounds: 1, smart: false },
    sheriff: { key: "sheriff", name: "El Sheriff", maxRisk: 0.67, greed: 1.0, taunt: "Tres balas. Una por cada vez que me mentiste.", lives: 4, liveRounds: 3, smart: true },
  };
  const DEFAULT_RIVAL = "sheriff";

  const pointsOf = (values, mults, streak, silver) => {
    const s = scoreOf(values, mults);
    let mult = s.mult + streak * STREAK_BONUS;
    if (silver) mult *= SILVER_MULT;
    return s.total * mult;
  };
  const winProb = (points, opp) => {
    if (opp !== null && opp !== undefined) return points > opp ? 1 : points === opp ? 0.5 : 0;
    return 1 / (1 + Math.exp(-(points - 52) / 14));
  };
  function expectedWin(values, keep, faces, mults, streak, silver, opp, rng) {
    const free = keep.map((k, i) => (k ? -1 : i)).filter(i => i >= 0);
    let total = 0;
    for (let s = 0; s < SAMPLES; s++) {
      const vals = values.slice();
      free.forEach(i => { vals[i] = rng.choice(faces[i]); });
      total += winProb(pointsOf(vals, mults, streak, silver), opp);
    }
    return total / SAMPLES;
  }
  function planSmart(duel, me, rng) {
    const other = duel.other(me);
    const opp = other.played ? other.played.points : null;
    const values = me.dice.map(d => d.value), faces = me.dice.map(d => d.faces);
    const wNow = winProb(pointsOf(values, duel.mults, me.streak, me.silver), opp);
    let bestKeep = [true, true, true, true, true], bestW = -1;
    for (let mask = 0; mask < 31; mask++) { // 31: todas menos "guardar los cinco"
      const keep = [0, 1, 2, 3, 4].map(i => !!(mask & (1 << i)));
      const w = expectedWin(values, keep, faces, duel.mults, me.streak + 1, me.silver, opp, rng);
      if (w > bestW) { bestKeep = keep; bestW = w; }
    }
    return { keep: bestKeep, wNow, wFire: bestW };
  }
  function chooseAction(duel, me, pers, wNow, wFire) {
    const risk = duel.cylinder.risk(), other = duel.other(me);
    const livesLeft = me.maxWounds - me.wounds;
    const bulletCost = 1 + (livesLeft <= 1 ? 0.6 : 0);
    const stand = 1 - wNow;
    const options = { stand };
    if (risk <= pers.maxRisk) options.self = risk * bulletCost + (1 - risk) * (1 - wFire);
    if (other.alive() && risk > 0) {
      const killBonus = other.maxWounds - other.wounds <= 1 ? 0.5 : 0;
      const afterHit = Math.min.apply(null, Object.values(options));
      const loseIfMiss = other.played && other.played.points === 0 ? 0.5 : 1;
      options.rival = (risk * afterHit + (1 - risk) * loseIfMiss) - risk * (1 + killBonus);
    }
    let best = "stand";
    Object.keys(options).forEach(k => { if (options[k] < options[best]) best = k; });
    if (best !== "stand" && options[best] + 0.02 >= stand) return "stand";
    return best;
  }
  function lockBest(p) {
    const c = {};
    p.dice.forEach(d => { c[d.value] = (c[d.value] || 0) + 1; });
    let best = 1;
    Object.keys(c).forEach(v => { const n = +v; if (c[n] > c[best] || (c[n] === c[best] && n > best)) best = n; });
    p.dice.forEach(d => { d.locked = d.value === best; });
  }
  function takeTurn(duel, pers) {
    const me = duel.current(), startRound = duel.round, events = [];
    const aiRng = new RNG(duel.rng.randrange(1 << 30));
    while (duel.current() === me && !duel.gameOver() && duel.round === startRound) {
      let action;
      if (pers.smart) {
        const plan = planSmart(duel, me, aiRng);
        me.dice.forEach((d, i) => { d.locked = plan.keep[i]; });
        action = chooseAction(duel, me, pers, plan.wNow, plan.wFire);
      } else {
        lockBest(me);
        const other = duel.other(me);
        const need = (other.played ? other.played.points + 1 : 45) * pers.greed;
        action = duel.handOf(me).points < need && duel.cylinder.risk() <= pers.maxRisk ? "self" : "stand";
      }
      const locked = me.dice.map(d => d.locked);
      if (action === "self" || action === "rival") {
        const r = duel.pullTrigger(action);
        events.push({ type: "fire", target: action, chamber: r.chamber, wounded: r.wounded,
                      dice: me.dice.map(d => d.value), locked, message: duel.message });
        continue;
      }
      const r2 = duel.playHand();
      events.push({ type: "play", hand: r2.hand, points: r2.points, total: r2.total, mult: r2.mult,
                    dice: me.dice.map(d => d.value), locked, message: duel.message });
    }
    return events;
  }

  // --- estado para la interfaz (serialize de server.py) ----------------------
  function serialize(g, seed) {
    const h = g.hand(), k = g.cylinder.known();
    return Object.assign({
      mode: "solo", seed,
      level: g.level, max_level: MAX_LEVEL, score: g.score, target: g.target(),
      hands_left: g.handsLeft, wounds: g.wounds, max_wounds: MAX_WOUNDS,
      dice: g.dice.map(d => ({ value: d.value, locked: d.locked, loaded: isLoaded(d) })),
      hand: h,
      mults: Object.assign({}, g.mults),
      cylinder: Object.assign(k, { risk: g.cylinder.risk() }),
      streak: g.streak, streak_bonus: STREAK_BONUS, silver: g.silver, shield: g.shield,
      message: g.message,
      pending_upgrades: g.pending.map(upgradeInfo),
      cleared: g.cleared(), game_over: g.gameOver(),
      victory: g.level >= MAX_LEVEL && g.cleared(),
    });
  }
  function serializeDuel(d, seed, rivalKey) {
    const [me, rival] = d.players, k = d.cylinder.known(), h = d.handOf(me), w = d.winner();
    return {
      mode: "duel", seed, rival: rivalKey, rival_name: rival.name,
      round: d.round, my_turn: d.current() === me && !d.gameOver(),
      max_wounds: MAX_WOUNDS,
      me: { wounds: me.wounds, max_wounds: me.maxWounds, streak: me.streak, silver: me.silver, rounds_won: me.roundsWon,
            dice: me.dice.map(x => ({ value: x.value, locked: x.locked, loaded: false })), played: me.played },
      opponent: { wounds: rival.wounds, max_wounds: rival.maxWounds, rounds_won: rival.roundsWon,
                  dice: rival.dice.map(x => x.value), played: rival.played },
      hand: h,
      mults: Object.assign({}, d.mults),
      cylinder: Object.assign(k, { risk: d.cylinder.risk() }),
      streak_bonus: STREAK_BONUS,
      message: d.message, last_round: d.lastRound,
      game_over: d.gameOver(), victory: w === me,
    };
  }

  // --- misma forma que la API JSON del servidor ------------------------------
  let sess = null;

  function newGame(body) {
    const seed = body && body.seed !== undefined && body.seed !== null && body.seed !== ""
      ? Number(body.seed) >>> 0 : Math.floor(Math.random() * 1e9);
    const rng = new RNG(seed);
    if (body && body.mode === "duel") {
      const key = PERSONALITIES[body.rival] ? body.rival : DEFAULT_RIVAL;
      const p = PERSONALITIES[key];
      const duel = new Duel(rng, [new Player("Tú"), new Player(p.name, true, p.lives)], new Cylinder(CYLINDER_SIZE, p.liveRounds));
      sess = { mode: "duel", seed, rival: key, duel };
    } else {
      sess = { mode: "solo", seed, game: new Game(rng) };
    }
    return state();
  }
  const state = () => (sess.mode === "duel" ? serializeDuel(sess.duel, sess.seed, sess.rival) : serialize(sess.game, sess.seed));

  function duelAction(action, body) {
    const d = sess.duel, pers = PERSONALITIES[sess.rival];
    if (d.gameOver()) return { error: "El duelo ha terminado. Empieza otro." };
    if (d.current().isAI) return { error: "No es tu turno." };
    if (action === "lock") {
      const i = Number(body.index);
      if (!(i >= 0 && i < 5)) return { error: "Índice de dado inválido." };
      return { locked: d.toggleLock(i) };
    }
    let event;
    if (action === "fire") {
      const target = body.target === "rival" ? "rival" : "self";
      const r = d.pullTrigger(target);
      event = { target, chamber: r.chamber, wounded: r.wounded, shielded: false, message: d.message };
    } else if (action === "play") {
      const r = d.playHand();
      event = { played: r, message: d.message };
    } else return { error: "Acción desconocida." };
    if (!d.gameOver() && d.current().isAI) {
      event.ai_events = takeTurn(d, pers);
      event.ai_taunt = pers.taunt;
    }
    return event;
  }

  function soloAction(action, body) {
    const g = sess.game;
    if (g.gameOver()) return { error: "La partida ha terminado. Empieza una nueva." };
    if (g.cleared() && action !== "upgrade") return { error: "Nivel superado: elige una mejora primero." };
    if (action === "lock") {
      const i = Number(body.index);
      if (!(i >= 0 && i < g.dice.length)) return { error: "Índice de dado inválido." };
      return { locked: g.toggleLock(i) };
    }
    if (action === "fire") { const r = g.pullTrigger(); return { chamber: r.chamber, wounded: r.wounded, shielded: r.shielded }; }
    if (action === "play") { return { played: g.playHand() }; }
    if (action === "upgrade") {
      if (!g.pending.length) return { error: "No hay mejoras pendientes." };
      if (g.level >= MAX_LEVEL) return { error: "La partida ya está ganada." };
      const id = body.id;
      if (!UPGRADES[id]) return { error: "Mejora desconocida." };
      if (g.pending.indexOf(id) < 0) return { error: "Esa mejora no está entre las ofrecidas." };
      g.applyUpgrade(id); g.nextLevel();
      return { next_level: g.level };
    }
    return { error: "Acción desconocida." };
  }

  // Mismo contrato que fetch("/api/…"): {token, state, event} o lanza el error.
  global.LocalGame = {
    // expuesto solo para poder contrastar la puntuación con la de Python
    _score: (values, mults) => scoreOf(values, mults),
    api(path, body) {
      body = body || {};
      if (path === "new") return { token: "local", state: newGame(body) };
      if (!sess) throw new Error("No hay partida. Empieza una nueva.");
      if (path === "state") return { state: state() };
      const event = sess.mode === "duel" ? duelAction(path, body) : soloAction(path, body);
      if (event.error) { const e = new Error(event.error); e.state = state(); throw e; }
      return { event, state: state() };
    },
  };
})(window);
