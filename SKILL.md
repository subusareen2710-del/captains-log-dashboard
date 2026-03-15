---
name: weekly-dashboard-update
description: Auto-detect new goals from brain dump, generate study plans, update training hub, deploy to Netlify
---

## Weekly Dashboard Auto-Update Pipeline

**Objective:** Read Subanshu's brain dump from Firestore, detect new learning goals, generate curated study plans with YouTube links, inject them into the Training Hub, run automated bug checks, commit to GitHub, and let Netlify auto-deploy.

---

### Firebase Config
- Project ID: `daily-planner-e61fc`
- API Key: `AIzaSyANpS7-0FwYHSZPapRy961cBgHLBd9hPu4`
- Firestore document: `dashboard/main`

### File paths
- Dashboard: `/sessions/zen-wizardly-brown/mnt/outputs/subanshu-dashboard.html`
- Training Hub: `/sessions/zen-wizardly-brown/mnt/outputs/training-hub.html`
- Git repo root: `/sessions/zen-wizardly-brown/mnt/outputs/`
- Archive log: `/sessions/zen-wizardly-brown/mnt/outputs/brain-dump-archive.txt`

---

### Step 1 — Read brain dump from Firestore

Fetch:
```
GET https://firestore.googleapis.com/v1/projects/daily-planner-e61fc/databases/(default)/documents/dashboard/main?key=AIzaSyANpS7-0FwYHSZPapRy961cBgHLBd9hPu4
```

Extract the `brainDump` field (`fields.brainDump.stringValue`) and the `buckets` map (`fields.buckets.mapValue`). Combine all text from brainDump + urgent/week/later bucket items into one string for scanning.

If everything is empty, log "No brain dump found this week" and stop — do not modify any files.

---

### Step 2 — Detect new learning goals

Scan combined text for certification/skill signals (case-insensitive):
PMP, PRINCE2, AZ-900, AZ-104, DP-900, PL-300, PL-100, DA-100, Six Sigma, Lean, Scrum, CAPM, MSP, ITIL, APM PMQ, AWS, Google Cloud, Tableau, dbt, SQL, Python, R, Power Automate, Copilot, Salesforce, Jira Advanced

Also catch phrases: "learn X", "study X", "get certified in X", "start X", "track X", "add X to tracker"

Read `training-hub.html` and extract existing tab labels (look for `class="tab-btn"` button text). Skip any goals already tracked.

Compile list of **new goals only**. If none, log it and skip to Step 5 (archive + clear).

---

### Step 3 — Research each new goal

Use web search to find 3–6 high-quality free YouTube videos per goal.

Preferred channels by topic:
- PMP/PRINCE2/project mgmt: ProjectManager.com, Prajeeth Sahasranam, Simplilearn, PrepCast
- Power BI/data: Guy in a Cube, SQLBI, Leila Gharani, Microsoft Learn
- Excel: Leila Gharani, Kevin Stratvert, ExcelIsFun
- Python/SQL: freeCodeCamp, Corey Schafer, Alex The Analyst
- Azure: John Savill's Technical Training, Adam Marczak, A Guide To Cloud
- Six Sigma/Lean: AIGPE, Advance Innovation Group

Search: `"[goal] tutorial YouTube [year] free beginner"`

Organise into 3–5 modules. Collect per video: title, YouTube URL, channel, duration (minutes).

---

### Step 4 — Inject new tabs into training-hub.html

Read the file. For each new goal, add:

**Tab button** inside `<div class="tab-bar">`:
```html
<button class="tab-btn" onclick="switchTab('TABID')" data-tab="TABID">ICON LABEL</button>
```

**Tab panel** following existing structure:
```html
<div id="tab-TABID" class="tab-panel" style="display:none">
  <details class="module" open>
    <summary>Module Title <span class="mod-count">N videos</span></summary>
    <table class="vid-table">
      <tr>
        <td><input type="checkbox" id="th_TABID_0" onchange="tick('th_TABID_0')"></td>
        <td><a href="URL" target="_blank" rel="noopener">Video Title</a></td>
        <td><span class="badge">Channel</span></td>
        <td class="dur">Xm</td>
      </tr>
    </table>
  </details>
</div>
```

Write updated file back.

---

### Step 5 — Automated bug check (REQUIRED before any commit)

Run the following checks on ALL modified files. If any check fails, fix the issue before proceeding — do not commit broken files:

**HTML files (subanshu-dashboard.html, training-hub.html):**
- `<script>` open/close tags balanced
- `<div>` open/close count within ±2 of each other
- Firebase API key present (`AIzaSy...`)
- `register('sw.js')` present in dashboard
- `manifest.json` link present in dashboard
- No placeholder text (`YOUR_`, `TODO`, `PLACEHOLDER`)
- All new checkbox IDs are unique (no `th_TABID_N` duplicates)
- All new YouTube URLs contain `youtube.com/watch?v=`
- `switchTab` function referenced for every new tab button
- New tab panel ID matches the `data-tab` attribute of its button

**sw.js:**
- CACHE version string is present
- ASSETS array contains `subanshu-dashboard.html` and `training-hub.html`

**manifest.json:**
- Valid JSON (parseable)
- `start_url` points to `subanshu-dashboard.html`

If any check fails: fix the specific issue, re-run checks, confirm clean before moving on.

---

### Step 6 — Archive brain dump + clear from Firestore

Append to `brain-dump-archive.txt`:
```
=== [YYYY-MM-DD] Weekly Update ===
Goals detected: [list or "none"]
New modules added: [count]
===================================
```

Clear the brainDump field in Firestore:
```
PATCH https://firestore.googleapis.com/v1/projects/daily-planner-e61fc/databases/(default)/documents/dashboard/main?updateMask.fieldPaths=brainDump&key=AIzaSyANpS7-0FwYHSZPapRy961cBgHLBd9hPu4
Body: {"fields": {"brainDump": {"stringValue": ""}}}
```

---

### Step 7 — Commit and push to GitHub (triggers Netlify auto-deploy)

```bash
cd /sessions/zen-wizardly-brown/mnt/outputs
git add subanshu-dashboard.html training-hub.html sw.js manifest.json
git commit -m "Weekly update [YYYY-MM-DD]: added [goal names]"
git push origin main
```

Netlify will detect the push and auto-deploy within ~30 seconds. No manual steps needed.

If `git push` fails (no remote set up yet), log: "GitHub remote not configured — skipping push. Run: git remote add origin <your-repo-url>" and stop gracefully.

---

### Step 8 — Save timestamped backup

Copy updated `training-hub.html` → `backups/training-hub-[YYYY-MM-DD].html`

---

### Constraints
- Never remove or modify existing tabs/modules — only add
- Only use verified YouTube URLs from actual search results
- Prefer free content; Subanshu is an Ops/PM professional in Oxford, UK
- Keep identical HTML structure and One Piece light theme
- NEVER commit if bug checks fail — fix first, then commit
- If no new goals found, still archive + clear the brain dump, but skip commit
