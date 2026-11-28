# GUARDIAN — NEXO COMMAND CENTER
# DEEP-SPACE 3D DASHBOARD — AUTONOMOUS IMPLEMENTATION (for Codex)

You are working inside my existing Guardian project. You are NOT creating a new project.
You are continuing the existing Guardian HQ web app, which already has substantial work (auth, Supabase data, realtime, rooms, agents, tasks, approvals, devices, voice, a Canvas-2D 3D "Atlas" brain).

Your mission, executed autonomously with your own tools:
1. Read this whole prompt, then inspect the existing app.
2. Save the design vision as permanent project instructions.
3. Implement the complete visual and interaction direction below.
4. Verify it (tests, build, screen checks) and write a truthful report.

Do not describe what should be done. Do not write a tutorial. Do not stop after a plan.
Execute the work directly. User-visible text in the app stays in **simple Italian**.

---

## 00 — CONTEXT (CARRY FORWARD, ALREADY DECIDED)

- Working folder: the root of this repository (git worktree `C:\Users\casal\hq-codex`, local branch `codex-spazio`). App: `guardian-web/` (React 18 + Vite + TypeScript + Supabase JS). Deployed by Cloudflare Pages from branch `claude/gallant-sagan-fwncjr` — **you must NOT push**; Claude reviews your commits first.
- Run `npm ci` inside `guardian-web/` before anything else (node_modules is not present in this worktree).
- Local preview without secrets: `guardian-web/.env.local` already contains `VITE_DEMO=1` (git-ignored). `npx vite --port 5180`, log in with any email, e.g. `menotti`. Demo data lives in `src/data/demo.ts`.
- Key files:
  - `src/ui/Atlas.tsx` + `src/logic/atlas.ts`: current brain. Canvas 2D with hand-made perspective (`conProfondita`, `proietta`, `polvere`, `angoloAuto`, `filtraGrafo`, `vistaStanza`, `nodoInPunto`, `schedaNodo`), drag to rotate, wheel zoom, Esc reset, 30 fps cap, adaptive quality, pause on hidden tab, reduced-motion still frame. Its pure logic has tests in `src/logic/atlas.test.ts` — keep that logic and reuse it.
  - `src/ui/CommandCenter.tsx`: the Centro (`.hero` panel with a KPI drawer `numeriAperti`, `OrbitaStanze`, sections below).
  - `src/ui/Shell.tsx`: header, left rail, chat dock, command palette (Ctrl K), drawers/panels opened with `apri({ p: ... })`.
  - `src/ui/panels/`: existing panels (agents, tasks, approvals, statistics, devices "PC", etc.). Reuse them inside the new glass panels; do not rewrite their logic.
  - `src/state.tsx`: global state `useG()`, preferences in `localStorage['guardian.pref']` via `leggiPreferenze`/`salvaPreferenze`.
  - `src/styles/app.css`, `src/styles/volto.css` (`.con-volto` theme): styles.
  - `src/logic/dispositivi.ts` + devices panel: the real PC/machine data (registered PCs, online status from bridge heartbeats).
  - `src/volto/`, `src/voce/`: voice and face states (`pensa`, listening, speaking).
- Data rules: every number, status and machine shown must come from the real snapshot (`snap`: agents, tasks, approvals, stanze, dispositivi, events). Decorative particles/stars must be declared decorative in the accessible summary.
- Email: the web app has **no email integration yet**. Build the UI and a clean integration point, show "Email non collegata". Never fabricate inbox contents.
- The skill `web-design-guidelines` (Vercel) is installed for Claude; you must apply the official Vercel Web Interface Guidelines (https://vercel.com/design/guidelines) — if you have that skill or `ui-ux-pro-max`, `frontend-design`, `accessibility`, `core-web-vitals` in your own skills, load and use them.

---

## 01 — THE CORE VISION (the owner's words, all mandatory)

"When I enter the dashboard I must see **only an opaque black background, deep, like deep space**. Everything I see — the brain and the data — must look **almost like stars in space**, visible at first glance. The buttons I click must also have **that luminous whitish colour of stars, bright but not tiring for the eye**. Free up even more space."

And from the owner's reference brief: Guardian is my personal AI command center — like sitting at Tony Stark's private computer. At the center is the **Guardian Brain**, a genuinely three-dimensional living object suspended in space, connected to **three computers** (my three machines) through **flowing energy pathways**. Agents are visible when they work. Details open in **glass panels** over the living scene; the brain never disappears.

**One intelligence. Three machines. Multiple agents. One unified command center.**

The look is a premium scientific star-field visualization — cinematic, minimal, restrained. NOT a SaaS card grid, NOT a game, NOT cyberpunk neon, NOT matrix rain. Not every element glows: hierarchy, negative space, controlled light.

---

## 02 — DESIGN INSPIRATION (study, do not copy)

Look at these for ideas only; respect licenses; Guardian keeps its own identity:
- https://github.com/fls-dev/JARVIS_Admin_Dashboard — "Aurora" living canvas of task nodes, "Orbital" spatial navigation.
- https://github.com/BuiltByAdvait/JARVIS-AI — Three.js, GLSL plasma, particles, audio-reactive core.
- https://github.com/astroverse4223-lab/JarvisDashboard — dark cinematic glass panels around a central core.
- https://github.com/ChiranthaBimsara/jarvis-desktop — HUD, system health, command palette, live feedback.
- https://github.com/PRUTU29/jarvis — 3D interface + monitoring + voice + email aggregation.
If you cannot browse, proceed from this prompt; do not stall.

---

## 03 — PERMANENT PROJECT INSTRUCTIONS (do first, ~10 minutes)

1. Create `guardian-web/DESIGN-GUARDIAN.md` containing, in short Italian sections: the deep-space vision (§01), palette and button specs (§05), the 3D brain (§07), the three machines (§08), energy pathways (§09), agents in motion (§10), the glass-panel model (§12), email vision (§14), real-data rules, accessibility (§18), performance (§19), "preserve existing functionality", and "apply the Vercel Web Interface Guidelines / web-design-guidelines on every frontend change".
2. Append ONE line to the repository `AGENTS.md` under a new heading "Design di Guardian HQ": `Prima di toccare guardian-web/ leggi guardian-web/DESIGN-GUARDIAN.md.` Do not change any other line of AGENTS.md.
3. Commit: "Guardian: istruzioni di design permanenti (spazio profondo)".

---

## 04 — INSPECT BEFORE CHANGING

Read (with search, not whole-file dumps where avoidable) the files of §00. Write a short classification at the top of `guardian-web/RAPPORTO-CODEX.md`: Working / Partial / Broken / Missing for: brain, machines (devices), agents live, tasks, approvals, statistics, email, voice, command input, navigation, realtime. Do not start from scratch and do not create a disconnected demo.

---

## 05 — VISUAL LANGUAGE (measurable)

**Background**
- Solid `#000000` (up to `#02030a`). Remove grids, vignettes, blue radial glows (including the `createRadialGradient` glow in `Atlas.tsx disegna`), scanlines, the hero gradient. Optional far nebula alpha ≤ 0.03.
- A distant star field: 300–600 fixed points, 0.5–1.2 px, alpha 0.12–0.5, rotating ~5× slower than the brain, subtle twinkle (alpha ±15%, period 2–6 s, phase from a stable hash). Same render loop as the brain.

**Starlight palette**
- Star white `#F2F6FF` (core, primary text, primary buttons).
- Room tints, almost white: Sviluppo `#CDEFFF`, Vendite `#FFE7C2`, Amministrazione `#E4DCFF`.
- States, desaturated: working = brighter star white, waiting approval `#FFD9A0` (restrained amber), error `#FFB4A8`, offline = 35% alpha grey `#8A93A6`. Energy pathways: white-cyan `#DCEBFF` with a faint cyan `#9FE8F5` only at the moving particles.
- Never rely on colour alone: every state also has a word/icon/shape.

**Buttons and text ("star buttons")**
- Secondary: background `rgba(242,246,255,0.04)`, 1 px border `rgba(242,246,255,0.22)`, text `#F2F6FF` at 0.9, radius 999 px, glow `box-shadow: 0 0 14px rgba(220,232,255,0.14)`. Hover: glow 0.28, border 0.40, 150 ms on opacity/box-shadow only. Focus-visible: 2 px `#F2F6FF` outline, 2 px offset.
- Primary (Conversazione, Invia): background `rgba(242,246,255,0.92)`, text `#05070D`, same radius, soft glow.
- No saturated cyan fills, no coloured gradients on buttons.
- Text: minimum 12 px, body 14 px, WCAG AA contrast (4.5:1 under 18 px). Labels of stars: uppercase, letter-spaced, 11–13 px, alpha 0.6–0.85.

---

## 06 — THE GUARDIAN SCREEN (free up space)

At first load of the Centro the user sees ONLY:
1. deep black + distant stars;
2. the Guardian Brain at the center (35–45% of the central composition);
3. the three machines around it, connected by energy pathways;
4. at-a-glance data as **small labelled stars** (not cards);
5. a thin top status line (≤ 44 px, transparent) and a thin command bar at the bottom (≤ 52 px).

Concretely:
- Remove the big `.hero` panel. Guardian's status sentence ("Coordino 1 agente…") becomes one small line under the brain.
- The 4 KPIs (agenti al lavoro, task in esecuzione, approvazioni in attesa, completati oggi) become 4 "data stars" near the core: big number in star white (28–34 px, weight 300–400) + small label. They are real DOM `<button>`s over the canvas and open the same panels as today (`apri({ p: 'agenti' })`, `apri({ p: 'tasks', filtro: 'attivi' })`, `apri({ p: 'approvazioni' })`, `apri({ p: 'statistiche' })`).
- Add two more compact indicators in the status line: email (unread count or "non collegata") and machines online "PC 1/3".
- Header: logo "GUARDIAN" thin, bell, avatar; technical indicators (Database ms, Live/Dati locali, Cerca Ctrl K) collapse into a single status dot with tooltip/menu.
- Left rail: icons only at alpha 0.55, tooltips, expands on hover/click. Phone keeps the bottom bar with the same star style.
- Atlas filters (Tutti / rooms / Solo attivi): one star button "Filtri" that opens the group.
- Everything currently below the first screen (OrbitaStanze, Prossime azioni, Flotta agenti, Task attivi, …): inside a "Dettagli" glass panel, closed at start, state saved in `guardian.pref` (`dettagliAperti`, default false). No feature is lost; only its location changes.

---

## 07 — THE GUARDIAN BRAIN (true 3D)

- Must be genuinely 3D: real geometry, depth, perspective, lighting/additive glow, particles. Not CSS transforms, not a flat SVG.
- **Technology decision (owner-approved for this task):** you MAY add `three` (and `@types/three` as devDependency). Nothing else 3D (no React Three Fiber, no postprocessing libs). Load it **lazily** (`import('three')` inside the brain component) so the first paint is not delayed. Keep the existing Canvas-2D Atlas as the **fallback** when WebGL is unavailable or fails — never a blank screen.
- Look: a star-like neural core — luminous inner core (star white), a translucent shell of fine points (Points with a small round sprite/shader, additive blending), 2–3 slow rings of dots on different planes, fine neural filaments (LineSegments, alpha 0.04–0.12), subtle drifting particles. Not a cartoon brain, not a medical illustration, not a plain sphere.
- Motion layers: slow idle rotation (~90 s per turn), gentle breathing (scale/alpha ±3–5%), small internal pulses, particle drift, restrained camera parallax on pointer move (max ±3°, eased). Drag to orbit, wheel to zoom, Esc to reset (keep current behaviour).
- States from REAL app state (`statoNucleo`/`useG().pensa`, voice listening/speaking, approvals, errors, connection): idle (calm), listening (soft waveform ripple), thinking (more internal pulses), executing (energy flows toward the involved machine), waiting approval (restrained amber halo), completed (one short pulse), error (soft red-amber warning), offline (dimmed, label "Scollegato"). Never random.
- Keep `data-atlas`, `data-atlas-fps`, `data-atlas-nodi` attributes on the root element (used by tests/checks).

---

## 08 — THE THREE CONNECTED COMPUTERS

- Three machine nodes in the 3D scene around the brain (e.g. upper-left, upper-right, lower-center; adapt to viewport), balanced, smaller than the brain: compact holographic workstation silhouettes or star clusters with a small floating label. Not big desktop illustrations, not cards.
- Data source: the real registered PCs from `dispositivi` (devices panel). If fewer than 3 are registered, show the missing ones as faint outlined "slot" nodes labelled "PC non collegato — Registra un PC" (clicking opens the devices panel). Never show a machine as connected unless its heartbeat says so.
- Default label: name + status word (Collegato / In collegamento / Al lavoro / Inattivo / Scollegato / Errore) + agent count. Click → glass panel with: name, status, agents on it, current task, last activity, CPU/memory only if the data exists.
- Assign agents to machines using existing fields (agent ↔ device/pc relation if present; otherwise via the agent's user/room). Document the rule you used in the report.

---

## 09 — ENERGY PATHWAYS

- Brain ↔ each machine: curved 3D paths (CatmullRom/Quadratic Bézier tubes or line strips), luminous thin edges, faint glow, moving particles along the curve, connection points at both ends, depth-aware.
- Idle: dim path, particles slow and sparse. Active (agents working on that machine): brighter path, more frequent particles, machine node reacts, brain responds. Multiple active machines → simultaneous, individually readable activity. Direction: Guardian → machine for dispatch, machine → Guardian for results/approvals, when the data allows it.
- No fake traffic metrics.

---

## 10 — AGENTS VISIBLE IN MOTION

- Each active agent = a small luminous marker (star capsule / particle cluster) located at its machine, with name on hover/focus.
- When a real event says an agent started a task: animate the marker travelling along the pathway from the brain to the machine, then a working state (slow orbit around the machine). Completed → short pulse, result travels back. Waiting approval → stops, amber halo. Failed → error halo. Use the existing realtime/polling events (`snap.events`, agent `stato`, task `stato`), never random movement.
- Distinguish agents by name and shape/label, not only colour. Everything must also be reachable in the DOM (accessible list in the agents panel).

---

## 11 — LIVING BACKGROUND
Deep black + distant stars (§05). Alive but calm: slow star rotation, twinkle, very faint drifting dust. No grids, no scanlines, no flashing, no dense particles. Secondary to the brain.

---

## 12 — GLASS PANEL SYSTEM

- Details open in a glass panel over the scene, not a new page. Desktop width 30–36% of the viewport (min 360 px, max 560 px), from the right; the brain stays visible (shift the 3D camera/center slightly left when a panel is open).
- Glass: background `rgba(4,6,12,0.78)` + `backdrop-filter: blur(14px)` (only on the panel, not full screen), 1 px border `rgba(242,246,255,0.10)`, inner top highlight, soft shadow, radius 16–20 px, readable text (contrast AA).
- Open: slide/unfold 200–260 ms (transform + opacity); scene keeps animating. Close: retract, Esc closes, focus returns to the opener. Switching panels without closing animation jank. `role="dialog"`, `aria-modal` as appropriate, focus trap, labelled title. Reduced motion → no slide.
- Phone (< 600 px): bottom sheet up to 85vh.
- Reuse the existing panel contents from `src/ui/panels/` inside this shell.

---

## 13 — STATISTICS PANEL
Opens as a glass panel. Real data only: active agents, tasks open/running/completed/failed, approvals pending, machines online, recent activity, completed per day (14-day bars, hand-made SVG, no chart library). Missing data → explicit "non disponibile" state. Compare with previous week only if the data exists.

## 14 — EMAIL CENTER
- Compact indicator in the status line: "Email non collegata" (today). Click → glass panel with the future structure (inbox preview, unread, search, message detail, reply/forward, drafts) shown as an empty, clearly-labelled "Collega Gmail per vedere la posta" state.
- Create a typed integration point (e.g. `src/data/email.ts` with an interface and a `NonCollegata` implementation). No fake messages, no send button that pretends to work. Sending will always require approval: model the states Bozza / In attesa di approvazione / Invio / Inviata / Errore in the types.

## 15 — QUICK COMMAND BAR
Keep the existing chat/voice dock and its logic. Make it thin (≤ 52 px), star style, bottom-center, never covering the brain. Show received → processing → plan/assigned agent/machine → result, from real state; when a task is assigned to a machine, light that pathway. Command history with ↑/↓ if not present.

## 16 — AT-A-GLANCE
Without opening panels the user understands: Guardian status, machines connected (x/3), active agents, tasks waiting, approvals required, email status, important errors. Use the data stars and the status line, not big cards.

## 17 — NAVIGATION
Minimal icon rail (desktop) / bottom bar (phone) + Ctrl K palette. Access to: Guardian, Agenti, PC (machines), Aziende, Task, Approvazioni, Automazioni/Workflow, Email, Statistiche, Impostazioni. Opening a section opens its glass panel over the scene whenever the existing architecture allows; never lose the brain context.

## 18 — ACCESSIBILITY (Vercel guidelines)
Keyboard navigation, visible focus, labels, semantic HTML, proper dialogs and focus return, AA contrast, readable type, `aria-live` status, reduced-motion (static scene, no slides), targets ≥ 32 px desktop / 40 px touch. Everything shown in 3D (agents, machines, tasks, statuses) is also reachable via DOM controls. The `sr-only` Atlas summary stays and mentions that stars and dust are decorative.

## 19 — PERFORMANCE
- One render loop, cap 30–60 fps (30 on low-power), pause when `document.hidden`, DPR ≤ 1.5, adaptive quality (reduce particles if fps < 24 for 2 s).
- No full-screen blur; blur only on panels. No React re-render per frame (animation in refs/three objects). Dispose geometries/materials on unmount. No new polling loops.
- `three` loaded lazily; initial JS chunk must not grow by more than 15 KB gzip. Report the size of the new lazy chunk.

## 20 — RESPONSIVE
Targets 1920×1080, 1600×900, 1440×900, 1366×768, tablet, phone (390×844). Brain always visible on desktop; machines repositioned on narrow screens; no overlaps; no horizontal scroll; panels become bottom sheets on phone; reduce scene complexity on phone.

---

## 21 — CONSTRAINTS (non-negotiable)
- Allowed new dependencies: `three`, `@types/three` only. Anything else → stop and write it in the report.
- Do not touch `supabase/`, `bridge/`, `.env*` (except reading `.env.local`), Cloudflare/GitHub config, `registro/` files of other people, or anything outside this worktree.
- Do not change data-layer semantics in `src/data/` (you may ADD `email.ts`). Do not bypass auth or approvals. No secrets in code.
- Preserve existing features and tests; update tests only where a colour/text you changed is asserted; add tests for new pure logic (machine assignment, state → visual mapping, pathway curve helpers, star twinkle).
- Targeted edits; no wholesale rewrites of files that only need block changes.
- Never `git push`, never `git reset --hard`, never delete branches.

## 22 — WORKFLOW AND STOP CONDITIONS
Order: §03 → §04 → brain in three.js with Canvas-2D fallback (§07) → three machines (§08) → pathways (§09) → agents in motion (§10) → background (§11) → free space + data stars + star buttons (§05–06) → glass panels (§12) → statistics (§13) → email (§14) → command bar / navigation (§15–17) → polish.
- After EACH step: `npx vitest run` and `npm run build` in `guardian-web/` must pass, then commit with a clear Italian message. If a step cannot pass after 3 attempts, revert only that step's files (`git checkout -- <file>`), note it in the report, move on.
- Stop and report (do not improvise) if: a dependency other than `three` is needed; database/schema changes are needed; existing tests fail for reasons unrelated to your work; a requirement would break an existing feature with no safe alternative.

## 23 — VERIFICATION (before claiming anything)
1. `npx vitest run` → 0 failures. 2. `npm run build` → 0 TypeScript errors. 3. If you can drive a browser: demo mode (§00), check 1440×900 and 390×844: first screen = black + stars + brain + 3 machines + pathways + data stars + status line + command bar, no cards, no horizontal scroll, console without errors, `data-atlas-fps` ≥ 25, panels open/close with Esc and focus return. 4. Review against the Vercel Web Interface Guidelines and fix the relevant findings.

## 24 — FINAL REPORT
Complete `guardian-web/RAPPORTO-CODEX.md` (max 40 lines, Italian): classification from §04; what was implemented; files changed; features preserved; new dependency and lazy chunk size; machine-assignment rule; tests run/passed/failed; fps measured (or "non misurato" and why); what is NOT done and why. Do not exaggerate; do not say Guardian is finished if substantial work remains. Commit it as the last commit.

---

## FINAL DIRECTIVE
Save the design rules. Inspect the project. Build the deep-space scene: black, stars, a living 3D brain, three machines, energy pathways, agents moving only when they really work, star-white buttons, glass panels for statistics, email and details. Preserve every existing feature and the real data. Verify. Report truthfully. Do not stop at a plan or at a static mockup; work until done or until a genuine technical limit (§22) stops you.
