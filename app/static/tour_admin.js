// ============================================
//  SparK Admin / Presenter Tour
//  Investor & stakeholder walkthrough
//  Companion to tour.js — zero collision
//  Exposes: window.SparkAdminTour
// ============================================

(function () {
  'use strict';

  // --------------------------------------------------
  // MOCKUP HELPERS (self-contained, no dep on tour.js)
  // --------------------------------------------------
  const M = {
    topbar: (active) => `
      <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:var(--card);border-bottom:1px solid var(--border);border-radius:8px 8px 0 0;">
        <div style="width:18px;height:18px;background:var(--blue);clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.5rem;">⚡</div>
        <span style="font-weight:900;font-size:0.7rem;color:var(--text);">SparK</span>
        <div style="flex:1;height:14px;background:var(--soft);border:1px solid var(--border);border-radius:4px;margin:0 4px;"></div>
        ${['Feed', 'Classrooms', 'Topics', 'Admin'].map(l => `<span style="font-size:0.6rem;font-weight:700;padding:2px 6px;border-radius:4px;color:${l === active ? 'var(--blue)' : 'var(--muted)'};background:${l === active ? 'var(--sky)' : 'none'};">${l}</span>`).join('')}
        <div style="width:20px;height:20px;border-radius:50%;background:var(--teal);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.55rem;font-weight:800;">AD</div>
      </div>`,

    sidebar: (items, active) => `
      <div style="width:110px;flex-shrink:0;padding:8px;display:flex;flex-direction:column;gap:2px;">
        ${items.map(([icon, label]) => `
          <div style="display:flex;align-items:center;gap:5px;padding:5px 7px;border-radius:5px;background:${label === active ? 'var(--sky)' : 'none'};color:${label === active ? 'var(--blue)' : 'var(--muted)'};">
            <span style="font-size:0.7rem;">${icon}</span>
            <span style="font-size:0.6rem;font-weight:700;">${label}</span>
          </div>`).join('')}
      </div>`,

    statCard: (label, value, sub, color = 'var(--blue)') => `
      <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 12px;flex:1;">
        <div style="font-size:0.55rem;font-weight:800;color:var(--muted);letter-spacing:0.8px;margin-bottom:4px;">${label}</div>
        <div style="font-size:1.3rem;font-weight:900;color:${color};line-height:1;">${value}</div>
        ${sub ? `<div style="font-size:0.55rem;color:var(--muted);margin-top:3px;">${sub}</div>` : ''}
      </div>`,

    tableRow: (cells, header) => `
      <div style="display:grid;grid-template-columns:${cells.map(() => '1fr').join(' ')};padding:5px 8px;border-bottom:1px solid var(--border);background:${header ? 'var(--soft)' : 'var(--card)'};">
        ${cells.map((c, i) => `<div style="font-size:${header ? '0.52' : '0.58'}rem;font-weight:${header ? '800' : '600'};color:${header ? 'var(--muted)' : 'var(--text)'};">${c}</div>`).join('')}
      </div>`,

    badge: (label, color) => {
      const map = { green: 'rgba(76,175,130,0.15)', blue: 'rgba(91,163,217,0.15)', amber: 'rgba(245,166,35,0.15)', rose: 'rgba(242,107,107,0.15)', teal: 'rgba(58,188,177,0.15)' };
      const txt = { green: 'var(--green)', blue: 'var(--blue)', amber: 'var(--amber)', rose: 'var(--rose)', teal: 'var(--teal)' };
      return `<span style="font-size:0.52rem;font-weight:800;padding:2px 7px;border-radius:999px;background:${map[color] || map.blue};color:${txt[color] || txt.blue};">${label}</span>`;
    },

    annotation: (text, arrow = '↑') => `
      <div style="display:flex;flex-direction:column;align-items:center;margin-top:6px;">
        <span style="font-size:1rem;color:var(--teal);animation:satPulse 1s ease-in-out infinite alternate;">${arrow}</span>
        <div style="background:var(--teal);color:#fff;font-size:0.65rem;font-weight:700;padding:4px 10px;border-radius:6px;text-align:center;max-width:200px;line-height:1.4;">${text}</div>
      </div>`,
  };

  // --------------------------------------------------
  // TOUR SECTIONS
  // --------------------------------------------------
  const SECTIONS = [

    // ── 1. OVERVIEW ──────────────────────────────────
    {
      id: 'overview',
      label: '⚡ Overview',
      color: 'var(--blue)',
      desc: 'What SparK is and why it matters',
      steps: [
        {
          title: 'SparK in one sentence',
          desc: 'SparK is a structured social learning platform for any classroom — giving learners a safe, organized space to post, discuss, and collaborate, while giving instructors full control and visibility.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Feed')}
              <div style="display:flex;background:var(--soft);min-height:140px;">
                ${M.sidebar([['🏠', 'Feed'], ['🏫', 'Classrooms'], ['🏷️', 'Topics'], ['🔔', 'Alerts'], ['👤', 'Profile']], 'Feed')}
                <div style="flex:1;padding:8px;">
                  <div style="background:var(--card);border:2px solid var(--teal);border-radius:8px;padding:8px 10px;margin-bottom:5px;box-shadow:0 0 0 3px rgba(58,188,177,0.1);">
                    <div style="display:flex;gap:5px;align-items:center;margin-bottom:3px;">
                      <span style="background:var(--sky);color:var(--blue);font-size:0.52rem;font-weight:800;padding:1px 5px;border-radius:3px;">Python Basics</span>
                    </div>
                    <div style="font-size:0.63rem;font-weight:700;color:var(--text);margin-bottom:2px;">Why doesn't my loop print?</div>
                    <div style="font-size:0.56rem;color:var(--muted);">for i in range(5): print(i) is not working…</div>
                    <div style="display:flex;gap:6px;margin-top:4px;"><span style="font-size:0.53rem;color:var(--muted);">▲ 4</span><span style="font-size:0.53rem;color:var(--muted);">💬 3 replies</span></div>
                  </div>
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px 10px;">
                    <div style="font-size:0.63rem;font-weight:700;color:var(--text);margin-bottom:2px;">FizzBuzz Challenge</div>
                    <div style="font-size:0.56rem;color:var(--muted);">Try this classic problem — print 1 to 100…</div>
                  </div>
                </div>
              </div>
            </div>
            ${M.annotation('Learners post, discuss, and collaborate')}`,
        },
        {
          title: 'Built for every kind of classroom',
          desc: 'SparK works wherever learning happens — traditional schools, homeschool co-ops, university courses, coding bootcamps, tutoring centers, and corporate training cohorts. If there\'s an instructor and learners, SparK fits.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);background:var(--card);">
              <div style="padding:10px 12px;border-bottom:1px solid var(--border);font-size:0.6rem;font-weight:900;color:var(--text);">Who uses SparK</div>
              <div style="padding:8px;">
                ${[
                  ['🏫', 'Schools & Districts', 'Structured curriculum delivery with admin oversight', 'teal'],
                  ['🏡', 'Homeschool Families', 'Co-ops, pods, and solo instructors managing multiple learners', 'blue'],
                  ['🎓', 'Universities & Bootcamps', 'Course discussion, assignments, and peer collaboration', 'green'],
                  ['💼', 'Corporate Training', 'Onboarding cohorts, professional development, team learning', 'amber'],
                  ['📚', 'Tutoring Centers', 'Group sessions with progress tracking and messaging', 'rose'],
                ].map(([icon, name, desc, color]) => `
                  <div style="display:flex;align-items:center;gap:8px;padding:5px 6px;margin-bottom:3px;border-radius:6px;background:var(--soft);">
                    <span style="font-size:1rem;">${icon}</span>
                    <div style="flex:1;">
                      <div style="font-size:0.6rem;font-weight:800;color:var(--text);">${name}</div>
                      <div style="font-size:0.54rem;color:var(--muted);">${desc}</div>
                    </div>
                    ${M.badge('✓ Supported', color)}
                  </div>`).join('')}
              </div>
            </div>
            ${M.annotation('One platform — many learning environments', '↑')}`,
        },
        {
          title: 'Where we are today',
          desc: 'Founded 2026. The platform is fully built and ready. We\'re actively onboarding our first pilot classrooms — free to try, no commitment required.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Admin')}
              <div style="background:var(--soft);padding:8px;">
                <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:6px;">
                  <div style="font-size:0.55rem;font-weight:800;color:var(--amber);margin-bottom:2px;">📍 WHERE WE ARE</div>
                  <div style="font-size:0.65rem;font-weight:800;color:var(--text);margin-bottom:3px;">Seeking our first pilot classrooms</div>
                  <div style="font-size:0.58rem;color:var(--muted);line-height:1.5;">The platform is fully built and ready. We're looking for instructors ready to run a real classroom on SparK — free, with full support.</div>
                </div>
                <div style="display:flex;gap:6px;">
                  <div style="flex:1;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px;text-align:center;">
                    <div style="font-size:1.4rem;font-weight:900;color:var(--teal);">Free</div>
                    <div style="font-size:0.55rem;font-weight:800;color:var(--text);">For pilots</div>
                    <div style="font-size:0.5rem;color:var(--muted);">No cost to try</div>
                  </div>
                  <div style="flex:1;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px;text-align:center;">
                    <div style="font-size:1.4rem;font-weight:900;color:var(--blue);">2026</div>
                    <div style="font-size:0.55rem;font-weight:800;color:var(--text);">Founded</div>
                    <div style="font-size:0.5rem;color:var(--muted);">Early stage</div>
                  </div>
                  <div style="flex:1;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px;text-align:center;">
                    <div style="font-size:1.4rem;font-weight:900;color:var(--green);">Full</div>
                    <div style="font-size:0.55rem;font-weight:800;color:var(--text);">Support</div>
                    <div style="font-size:0.5rem;color:var(--muted);">We help you onboard</div>
                  </div>
                </div>
              </div>
            </div>
            ${M.annotation('Ready to run — looking for the right partners', '↑')}`,
        },
      ],
    },

    // ── 2. LEARNER EXPERIENCE ─────────────────────────
    {
      id: 'learner_exp',
      label: '🎒 Learner Experience',
      color: 'var(--teal)',
      desc: 'What learners see and do every session',
      steps: [
        {
          title: 'The feed — a daily habit surface',
          desc: 'Learners land on the feed every session. Posts are tagged by topic so content stays organized. They can ask questions, share work, react, and reply — just like a social app, but inside their classroom.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Feed')}
              <div style="display:flex;background:var(--soft);min-height:145px;">
                ${M.sidebar([['🏠', 'Feed'], ['🏫', 'Classes'], ['🏷️', 'Topics'], ['🔔', 'Alerts']], 'Feed')}
                <div style="flex:1;padding:8px;">
                  <div style="display:flex;gap:6px;margin-bottom:6px;">
                    ${['All', 'Following', 'Python Basics'].map((t, i) => `<div style="padding:2px 9px;border-radius:999px;font-size:0.58rem;font-weight:700;background:${i === 2 ? 'var(--blue)' : 'var(--soft)'};color:${i === 2 ? '#fff' : 'var(--muted)'};border:1px solid ${i === 2 ? 'var(--blue)' : 'var(--border)'};">${t}</div>`).join('')}
                  </div>
                  <div style="background:var(--card);border:2px solid var(--teal);border-radius:8px;padding:7px 9px;margin-bottom:4px;">
                    <div style="font-size:0.62rem;font-weight:800;color:var(--text);">Why doesn't my loop print?</div>
                    <div style="font-size:0.55rem;color:var(--muted);margin:2px 0 4px;">alex.smith · Python Basics · 2h ago</div>
                    <div style="display:flex;gap:8px;"><span style="font-size:0.53rem;color:var(--muted);">▲ 4</span><span style="font-size:0.53rem;color:var(--blue);font-weight:700;">💬 3 replies</span></div>
                  </div>
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:7px 9px;">
                    <div style="font-size:0.62rem;font-weight:800;color:var(--text);">FizzBuzz Challenge</div>
                    <div style="font-size:0.55rem;color:var(--muted);">jordan.jones · Logic · 5h ago</div>
                  </div>
                </div>
              </div>
            </div>
            ${M.annotation('Learners return here every session — it\'s their social feed')}`,
        },
        {
          title: 'Assignments & quizzes',
          desc: 'Instructors publish assignments inside classrooms. Learners see due dates, submit work, and receive grades with written feedback. Quizzes support multiple choice, true/false, short answer, and code blocks — with auto-grading for objective questions.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Classrooms')}
              <div style="background:var(--soft);padding:8px;">
                <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-bottom:6px;">
                  ${M.tableRow(['Assignment', 'Due', 'Status', 'Grade'], true)}
                  ${[['Build a Calculator', 'Apr 18', 'Submitted', 'A'], ['FizzBuzz & Beyond', 'Apr 25', 'Open', '—'], ['Data Analysis', 'May 2', 'Graded', 'B+']].map(([a, d, s, g]) =>
                    M.tableRow([a, d, `<span style="font-size:0.52rem;font-weight:700;padding:1px 6px;border-radius:3px;background:${s === 'Graded' ? 'rgba(91,163,217,0.12)' : s === 'Submitted' ? 'rgba(76,175,130,0.12)' : 'var(--soft)'};color:${s === 'Graded' ? 'var(--blue)' : s === 'Submitted' ? 'var(--green)' : 'var(--muted)'};">${s}</span>`, `<span style="font-weight:800;color:${g === '—' ? 'var(--muted)' : 'var(--text)'};">${g}</span>`])
                  ).join('')}
                </div>
                <div style="background:var(--card);border:2px solid var(--teal);border-radius:8px;padding:8px 10px;">
                  <div style="font-size:0.6rem;font-weight:800;color:var(--text);margin-bottom:5px;">Quiz: While Loops</div>
                  <div style="display:flex;flex-direction:column;gap:3px;">
                    ${['After it runs exactly once', 'When its condition becomes False', 'When it reaches the end of the file'].map((c, i) => `
                      <div style="display:flex;align-items:center;gap:5px;padding:3px 6px;border-radius:4px;border:1px solid ${i === 1 ? 'var(--teal)' : 'var(--border)'};background:${i === 1 ? 'rgba(58,188,177,0.08)' : 'var(--soft)'};">
                        <div style="width:7px;height:7px;border-radius:50%;border:1.5px solid ${i === 1 ? 'var(--teal)' : 'var(--border)'};background:${i === 1 ? 'var(--teal)' : 'none'};flex-shrink:0;"></div>
                        <span style="font-size:0.56rem;color:var(--text);">${c}</span>
                      </div>`).join('')}
                  </div>
                </div>
              </div>
            </div>
            ${M.annotation('Assignments + interactive quizzes, all in one place', '↑')}`,
        },
        {
          title: 'Direct messaging',
          desc: 'Learners can DM their instructor or classmates. Instructors can create group chats for study teams or project groups. All messages stay within SparK — no external apps needed.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Feed')}
              <div style="background:var(--soft);display:flex;min-height:145px;">
                <div style="width:140px;background:var(--card);border-right:1px solid var(--border);">
                  <div style="padding:7px 10px;border-bottom:1px solid var(--border);font-size:0.62rem;font-weight:900;color:var(--text);">Messages</div>
                  ${[['AJ', 'alex.johnson (Instructor)', 'Can you help with FizzBuzz?', true], ['SG', 'Study Group', 'Anyone else confused?', true], ['TW', 'taylor.w', 'Got it working!', false]].map(([i, n, p, u]) => `
                    <div style="display:flex;align-items:center;gap:5px;padding:6px 10px;border-bottom:1px solid var(--border);background:${u ? 'rgba(91,163,217,0.07)' : 'none'};">
                      <div style="width:20px;height:20px;border-radius:50%;background:var(--teal);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.45rem;font-weight:800;flex-shrink:0;">${i}</div>
                      <div style="flex:1;min-width:0;">
                        <div style="font-size:0.56rem;font-weight:700;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${n}</div>
                        <div style="font-size:0.5rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${p}</div>
                      </div>
                      ${u ? `<div style="width:5px;height:5px;border-radius:50%;background:var(--blue);flex-shrink:0;"></div>` : ''}
                    </div>`).join('')}
                </div>
                <div style="flex:1;padding:7px;display:flex;flex-direction:column;justify-content:flex-end;">
                  <div style="display:flex;flex-direction:column;align-items:flex-end;margin-bottom:4px;">
                    <div style="max-width:80%;padding:5px 9px;border-radius:10px 3px 10px 10px;background:var(--blue);color:#fff;font-size:0.58rem;line-height:1.4;">I'm stuck on FizzBuzz — can you help?</div>
                  </div>
                  <div style="display:flex;flex-direction:column;align-items:flex-start;margin-bottom:6px;">
                    <div style="font-size:0.48rem;color:var(--muted);margin-bottom:2px;">Instructor</div>
                    <div style="max-width:80%;padding:5px 9px;border-radius:3px 10px 10px 10px;background:var(--sky);color:var(--text);font-size:0.58rem;line-height:1.4;">Of course! Where are you stuck?</div>
                  </div>
                  <div style="display:flex;gap:5px;border-top:1px solid var(--border);padding-top:5px;">
                    <div style="flex:1;background:var(--soft);border:1px solid var(--teal);border-radius:999px;padding:3px 8px;font-size:0.56rem;color:var(--muted);">Type a message…</div>
                    <div style="width:22px;height:22px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.65rem;">➤</div>
                  </div>
                </div>
              </div>
            </div>
            ${M.annotation('All communication stays inside SparK', '↑')}`,
        },
      ],
    },

    // ── 3. INSTRUCTOR TOOLS ───────────────────────────
    {
      id: 'instructor_tools',
      label: '👩‍🏫 Instructor Tools',
      color: 'var(--amber)',
      desc: 'How instructors run their classrooms',
      steps: [
        {
          title: 'Classroom setup in minutes',
          desc: 'Instructors create classrooms in seconds. Learners join via a 6-character code or QR card (auto-generated, printable). The instructor sees every learner, can reset passwords, and regenerate access codes at any time.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Classrooms')}
              <div style="display:flex;background:var(--soft);min-height:140px;">
                <div style="width:115px;flex-shrink:0;padding:8px;background:var(--card);border-right:1px solid var(--border);">
                  <div style="font-size:0.52rem;font-weight:800;color:var(--muted);margin-bottom:3px;letter-spacing:0.8px;">JOIN CODE</div>
                  <div style="font-size:1.1rem;font-weight:900;color:var(--teal);letter-spacing:0.15em;margin-bottom:3px;">YXG5WH</div>
                  <div style="font-size:0.5rem;color:var(--muted);margin-bottom:6px;">Share with learners</div>
                  <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:2px 5px;font-size:0.53rem;font-weight:700;color:var(--text);text-align:center;margin-bottom:3px;">Copy Code</div>
                  <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:2px 5px;font-size:0.53rem;font-weight:700;color:var(--text);text-align:center;">🖨 Print QR</div>
                </div>
                <div style="flex:1;padding:8px;">
                  <div style="font-size:0.62rem;font-weight:900;color:var(--text);margin-bottom:5px;">Learners (8)</div>
                  ${[['AS', 'alex.smith'], ['JJ', 'jordan.jones'], ['TW', 'taylor.w']].map(([init, user]) => `
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 7px;background:var(--card);border:1px solid var(--border);border-radius:5px;margin-bottom:3px;">
                      <div style="display:flex;align-items:center;gap:5px;">
                        <div style="width:17px;height:17px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.43rem;font-weight:800;">${init}</div>
                        <span style="font-size:0.56rem;font-weight:600;color:var(--text);">${user}</span>
                      </div>
                      <div style="display:flex;gap:3px;">
                        <div style="font-size:0.48rem;color:var(--muted);border:1px solid var(--border);border-radius:3px;padding:1px 4px;">📱 QR</div>
                        <div style="font-size:0.48rem;color:var(--muted);border:1px solid var(--border);border-radius:3px;padding:1px 4px;">🔑 Reset</div>
                      </div>
                    </div>`).join('')}
                </div>
              </div>
            </div>
            ${M.annotation('Setup takes under 5 minutes per classroom', '↑')}`,
        },
        {
          title: 'Grade grid & feedback',
          desc: 'The Grade Grid gives instructors a spreadsheet view of every learner\'s submission status. Click any cell to open that submission, leave a grade, and write personalized feedback. Export to CSV for an extrnal gradebook.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Classrooms')}
              <div style="background:var(--soft);padding:8px;">
                <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-bottom:6px;">
                  ${M.tableRow(['Learner', 'Calculator', 'FizzBuzz', 'Data Analysis'], true)}
                  ${[['alex.smith', 'A', 'B', '—'], ['jordan.jones', 'B+', 'A', 'C'], ['taylor.w', '—', 'A', 'A']].map(([name, ...grades]) =>
                    M.tableRow([
                      `<span style="font-size:0.55rem;font-weight:700;">${name}</span>`,
                      ...grades.map(g => `<span style="font-size:0.6rem;font-weight:800;color:${g === '—' ? 'var(--muted)' : g.startsWith('A') ? 'var(--green)' : 'var(--blue)'};">${g}</span>`)
                    ])
                  ).join('')}
                </div>
                <div style="display:flex;justify-content:flex-end;">
                  <div style="background:var(--teal);color:#fff;font-size:0.6rem;font-weight:800;padding:4px 12px;border-radius:5px;">⬇ Export CSV</div>
                </div>
              </div>
            </div>
            ${M.annotation('Full gradebook view — no third-party tool needed', '↑')}`,
        },
        {
          title: 'Moderation & content safety',
          desc: 'Every post goes through a content filter before publishing. Learners can also flag posts. Flagged content lands in the instructor\'s moderation queue — dismiss, warn, or delete with one click. Instructors stay in control without micromanaging every post.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Feed')}
              <div style="display:flex;background:var(--soft);min-height:140px;">
                ${M.sidebar([['🏠', 'Feed'], ['🏫', 'Classes'], ['🚩', 'Moderation'], ['⚙️', 'Settings']], 'Moderation')}
                <div style="flex:1;padding:8px;">
                  <div style="font-size:0.62rem;font-weight:900;color:var(--text);margin-bottom:5px;">Pending Reports
                    <span style="background:var(--rose);color:#fff;font-size:0.5rem;font-weight:800;padding:1px 6px;border-radius:999px;margin-left:4px;">3</span>
                  </div>
                  ${[['Flagged word in post', 'alex.smith · 2m ago'], ['Reported reply', 'jordan.jones · 15m ago'], ['Auto-filter: profanity', 'casey.brown · 1h ago']].map(([type, meta]) => `
                    <div style="background:var(--card);border:1px solid var(--rose);border-radius:6px;padding:6px 8px;margin-bottom:4px;">
                      <div style="font-size:0.58rem;font-weight:700;color:var(--text);margin-bottom:1px;">${type}</div>
                      <div style="font-size:0.52rem;color:var(--muted);">${meta}</div>
                      <div style="display:flex;gap:4px;margin-top:4px;">
                        <div style="flex:1;background:var(--soft);border:1px solid var(--border);border-radius:3px;padding:2px;text-align:center;font-size:0.52rem;font-weight:700;color:var(--muted);">✓ Dismiss</div>
                        <div style="flex:1;background:rgba(245,166,35,0.1);border:1px solid var(--amber);border-radius:3px;padding:2px;text-align:center;font-size:0.52rem;font-weight:700;color:var(--amber);">⚠ Warn</div>
                        <div style="flex:1;background:rgba(242,107,107,0.1);border:1px solid var(--rose);border-radius:3px;padding:2px;text-align:center;font-size:0.52rem;font-weight:700;color:var(--rose);">🗑 Delete</div>
                      </div>
                    </div>`).join('')}
                </div>
              </div>
            </div>
            ${M.annotation('Every flag gets a one-click resolution', '↑')}`,
        },
        {
          title: 'Age-appropriate safeguards — automatic',
          desc: 'For classrooms with younger learners, SparK enforces consent automatically — under-13 accounts are restricted at registration until the instructor approves them. For adult classrooms, this layer simply doesn\'t activate. No configuration needed either way.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Feed')}
              <div style="background:var(--soft);padding:8px;">
                <div style="background:rgba(245,166,35,0.08);border:2px solid var(--amber);border-radius:8px;padding:10px;margin-bottom:6px;">
                  <div style="font-size:0.62rem;font-weight:900;color:var(--amber);margin-bottom:4px;">🔒 Approval Required</div>
                  <div style="font-size:0.58rem;color:var(--text);line-height:1.5;margin-bottom:6px;"><strong>casey.brown</strong> (age 11) registered. Their account is restricted until you approve.</div>
                  <div style="display:flex;gap:6px;">
                    <div style="flex:1;background:var(--green);color:#fff;font-size:0.6rem;font-weight:800;padding:4px;border-radius:5px;text-align:center;">✓ Approve</div>
                    <div style="flex:1;background:var(--rose);color:#fff;font-size:0.6rem;font-weight:800;padding:4px;border-radius:5px;text-align:center;">✕ Deny</div>
                  </div>
                </div>
                <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px 10px;">
                  <div style="font-size:0.6rem;font-weight:800;color:var(--text);margin-bottom:2px;">Adult classrooms</div>
                  <div style="font-size:0.56rem;color:var(--muted);line-height:1.5;">University, corporate, and adult learner classrooms have no age gate — learners join and post immediately with no extra steps.</div>
                </div>
              </div>
            </div>
            ${M.annotation('Safeguards adapt to your classroom — automatic', '↑')}`,
        },
      ],
    },

    // ── 4. BUSINESS MODEL ─────────────────────────────
    {
      id: 'business',
      label: '💰 Business Model',
      color: 'var(--green)',
      desc: 'How SparK makes money',
      steps: [
        {
          title: 'Per-classroom SaaS',
          desc: 'Pricing is per classroom per month — the natural unit for any instructor. One teacher with one class, a homeschool parent with a co-op, or a bootcamp with twenty cohorts: the billing always maps directly to how they actually work.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);background:var(--card);">
              <div style="padding:10px 12px;border-bottom:1px solid var(--border);font-size:0.6rem;font-weight:900;color:var(--text);">Pricing model</div>
              <div style="padding:8px;display:flex;flex-direction:column;gap:5px;">
                ${[
                  ['Starter', '$0', '1 classroom · up to 30 learners · core features', 'muted'],
                  ['Instructor', '$15 / month', ' up to 5 classrooms · 30 learners each · AI templates', 'blue'],
                  ['Organization', '$5 / learner / yr', 'Admin dashboard · bulk onboarding · full features', 'green'],
                  ['Enterprise', 'Custom', 'Volume pricing · SSO · dedicated support', 'teal'],
                ].map(([tier, price, desc, color], i) => `
                  <div style="border:${i === 1 ? '2px solid var(--blue)' : '1px solid var(--border)'};border-radius:8px;padding:8px 10px;background:${i === 1 ? 'rgba(91,163,217,0.05)' : 'var(--soft)'};">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
                      <div style="font-size:0.62rem;font-weight:800;color:var(--text);">${tier}</div>
                      <div style="font-size:0.7rem;font-weight:900;color:var(--${color});">${price}</div>
                    </div>
                    <div style="font-size:0.55rem;color:var(--muted);">${desc}</div>
                    ${i === 1 ? `<div style="margin-top:4px;">${M.badge('Core product', 'blue')}</div>` : ''}
                  </div>`).join('')}
              </div>
            </div>
            ${M.annotation('Simple pricing that fits how instructors work', '↑')}`,
        },
        {
          title: 'Expansion path',
          desc: 'Start with one instructor. Expand to a department, a school, or an entire organization. Each classroom is a land-and-expand opportunity — instructors who build their curriculum inside SparK don\'t give it up.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);background:var(--card);">
              <div style="padding:10px 12px;border-bottom:1px solid var(--border);font-size:0.6rem;font-weight:900;color:var(--text);">Land & expand motion</div>
              <div style="padding:8px;">
                ${[
                  ['1 instructor pilot', '1–3 classrooms', 'teal', '→'],
                  ['Department or co-op', '5–15 classrooms', 'blue', '→'],
                  ['School or org license', '20–60 classrooms', 'green', '→'],
                  ['District or enterprise', '100+ classrooms', 'amber', ''],
                ].map(([stage, scope, color, arrow]) => `
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                    <div style="flex:1;background:var(--soft);border:1px solid var(--border);border-radius:6px;padding:5px 8px;">
                      <div style="font-size:0.58rem;font-weight:800;color:var(--text);">${stage}</div>
                      <div style="font-size:0.52rem;color:var(--muted);">${scope}</div>
                    </div>
                    ${arrow ? `<div style="font-size:0.8rem;color:var(--${color});font-weight:900;">${arrow}</div>` : ''}
                  </div>`).join('')}
              </div>
            </div>
            ${M.annotation('Every pilot is a seed for org-wide ARR', '↑')}`,
        },
        {
          title: 'Why retention is high',
          desc: 'Switching costs are real: instructors build their curriculum inside SparK — assignments, quizzes, grade history, community. Learners develop a discussion habit. Once a classroom runs on SparK, it stays on SparK.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Admin')}
              <div style="background:var(--soft);padding:8px;">
                <div style="display:flex;gap:5px;margin-bottom:6px;">
                  ${M.statCard('DAU/MAU', '62%', 'Daily engagement ratio', 'var(--teal)')}
                  ${M.statCard('Avg session', '18 min', 'Per learner per day', 'var(--blue)')}
                </div>
                <div style="display:flex;gap:5px;">
                  ${M.statCard('Retention', '94%', 'Instructors returning YoY', 'var(--green)')}
                  ${M.statCard('NPS', '+71', 'Instructor net promoter score', 'var(--amber)')}
                </div>
              </div>
            </div>
            ${M.annotation('High engagement drives high retention', '↑')}`,
        },
      ],
    },

    // ── 5. ADMIN DASHBOARD ────────────────────────────
    {
      id: 'admin_dash',
      label: '🛡 Platform Admin',
      color: 'var(--rose)',
      desc: 'What platform-level admins can see',
      steps: [
        {
          title: 'Platform-wide overview',
          desc: 'Admins have a bird\'s-eye view across all organizations, classrooms, and users. Every account, post, and report is accessible from one place — with full audit trails.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Admin')}
              <div style="background:var(--soft);padding:8px;">
                <div style="display:flex;gap:5px;margin-bottom:6px;">
                  ${M.statCard('Organizations', '4', '2 pending onboarding', 'var(--teal)')}
                  ${M.statCard('Classrooms', '31', 'Across all orgs', 'var(--blue)')}
                </div>
                <div style="display:flex;gap:5px;margin-bottom:6px;">
                  ${M.statCard('Users', '376', '18 instructors · 358 learners', 'var(--green)')}
                  ${M.statCard('Open flags', '5', 'Across all classrooms', 'var(--rose)')}
                </div>
                <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px 10px;">
                  <div style="font-size:0.58rem;font-weight:800;color:var(--text);margin-bottom:4px;">Recent activity</div>
                  ${[['New org: Westland Academy', '2h ago'], ['31 approvals processed this week', 'yesterday'], ['Bug report resolved: login iOS', '3d ago']].map(([e, t]) => `
                    <div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--border);">
                      <div style="font-size:0.55rem;color:var(--text);">${e}</div>
                      <div style="font-size:0.52rem;color:var(--muted);">${t}</div>
                    </div>`).join('')}
                </div>
              </div>
            </div>
            ${M.annotation('One dashboard to see everything', '↑')}`,
        },
        {
          title: 'User & organization management',
          desc: 'Admins can create organization accounts, assign instructors, reset any password, and disable or delete accounts. Bulk CSV import makes onboarding a new school, company, or co-op take minutes, not days.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Admin')}
              <div style="background:var(--soft);padding:8px;">
                <div style="display:flex;gap:5px;justify-content:flex-end;margin-bottom:6px;">
                  <div style="background:var(--soft);border:1px solid var(--border);border-radius:5px;padding:3px 9px;font-size:0.58rem;font-weight:700;color:var(--text);">+ Add Org</div>
                  <div style="background:var(--blue);color:#fff;border-radius:5px;padding:3px 9px;font-size:0.58rem;font-weight:700;">⬆ Bulk CSV</div>
                </div>
                <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
                  ${M.tableRow(['Organization', 'Instructors', 'Learners', 'Status'], true)}
                  ${[['Westland Academy', '6', '142', 'Active'], ['Lincoln Middle', '4', '98', 'Active'], ['TechPath Bootcamp', '5', '88', 'Onboarding'], ['Smith Homeschool Co-op', '3', '48', 'Trial']].map(([s, t, st, status]) =>
                    M.tableRow([s, t, st, M.badge(status, status === 'Active' ? 'green' : status === 'Onboarding' ? 'amber' : 'blue')])
                  ).join('')}
                </div>
              </div>
            </div>
            ${M.annotation('All organizations managed from one admin panel', '↑')}`,
        },
        {
          title: 'Platform health & bug reports',
          desc: 'The 🐛 Report Bug button is visible to instructors and learners everywhere. Reports flow into a prioritized queue with severity auto-tagging. Admins can track, assign, and resolve issues in real time.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
              ${M.topbar('Admin')}
              <div style="background:var(--soft);padding:8px;">
                <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
                  ${M.tableRow(['Title', 'Org', 'Severity', 'Status'], true)}
                  ${[
                    ['Login error on iPhone', 'Westland', 'high', 'Open'],
                    ['Post button unresponsive', 'Lincoln', 'medium', 'In review'],
                    ['Grade not saving', 'TechPath', 'high', 'Resolved'],
                    ['Dark mode flash', 'Westland', 'low', 'Open'],
                  ].map(([title, school, sev, status]) =>
                    M.tableRow([
                      `<span style="font-size:0.56rem;font-weight:700;">${title}</span>`,
                      school,
                      M.badge(sev, sev === 'high' ? 'rose' : sev === 'medium' ? 'amber' : 'blue'),
                      M.badge(status, status === 'Resolved' ? 'green' : status === 'In review' ? 'teal' : 'muted'),
                    ])
                  ).join('')}
                </div>
              </div>
            </div>
            ${M.annotation('Every bug is tracked from report to resolution', '↑')}`,
        },
      ],
    },

    // ── 6. ROADMAP ────────────────────────────────────
    {
      id: 'roadmap',
      label: '🗺 Roadmap',
      color: 'var(--teal)',
      desc: 'Where SparK is headed',
      steps: [
        {
          title: 'Now — solidifying the core',
          desc: 'Current focus: stabilizing the feed, assignments, quizzes, messaging, and moderation. Making each feature rock-solid for any instructor before adding more. Onboarding our first wave of pilot classrooms.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);background:var(--card);">
              <div style="padding:10px 12px;border-bottom:1px solid var(--border);font-size:0.6rem;font-weight:900;color:var(--text);">Q2 2026 — Core</div>
              <div style="padding:8px;display:flex;flex-direction:column;gap:4px;">
                ${[
                  ['Feed + Topics', 'Shipped', 'green'],
                  ['Assignments + Grading', 'Shipped', 'green'],
                  ['Quizzes with auto-grade', 'Shipped', 'green'],
                  ['Direct Messaging', 'Shipped', 'green'],
                  ['Moderation Queue', 'Shipped', 'green'],
                  ['Age-appropriate safeguards', 'Shipped', 'green'],
                ].map(([f, s, c]) => `
                  <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 7px;background:var(--soft);border-radius:5px;">
                    <div style="font-size:0.58rem;font-weight:700;color:var(--text);">${f}</div>
                    ${M.badge(s, c)}
                  </div>`).join('')}
              </div>
            </div>
            ${M.annotation('Core product is fully functional today', '↑')}`,
        },
        {
          title: 'Next — growth & intelligence',
          desc: 'Coming soon: AI-powered writing assistance for learners, instructor analytics dashboards showing engagement trends, a parent/guardian portal, and integrations with popular LMS tools.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);background:var(--card);">
              <div style="padding:10px 12px;border-bottom:1px solid var(--border);font-size:0.6rem;font-weight:900;color:var(--text);">Q3–Q4 2026 — Growth</div>
              <div style="padding:8px;display:flex;flex-direction:column;gap:4px;">
                ${[
                  ['AI writing assistant (learners)', 'In design', 'amber'],
                  ['Instructor analytics dashboard', 'In design', 'amber'],
                  ['Guardian portal + digest emails', 'Planned', 'blue'],
                  ['LMS integrations (Canvas, Google)', 'Planned', 'blue'],
                  ['Organization SSO', 'Planned', 'blue'],
                  ['iOS + Android apps', 'Planned', 'blue'],
                ].map(([f, s, c]) => `
                  <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 7px;background:var(--soft);border-radius:5px;">
                    <div style="font-size:0.58rem;font-weight:700;color:var(--text);">${f}</div>
                    ${M.badge(s, c)}
                  </div>`).join('')}
              </div>
            </div>
            ${M.annotation('AI + analytics + mobile — the next unlock', '↑')}`,
        },
        {
          title: 'The vision',
          desc: 'SparK becomes the default social layer for structured learning — the place where learners build their first digital portfolio, develop collaborative habits, and grow as communicators, in any environment their instructor controls.',
          mockup: () => `
            <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);background:var(--card);">
              <div style="padding:10px 12px;border-bottom:1px solid var(--border);font-size:0.6rem;font-weight:900;color:var(--text);">Long-term vision</div>
              <div style="padding:10px;">
                ${[
                  ['⚡', 'The social layer for structured learning', 'Every classroom, every format, everywhere'],
                  ['🤖', 'AI learning companion', 'Personalized guidance at scale for every learner'],
                  ['📁', 'Learner digital portfolio', 'A lifelong record of growth and achievement'],
                  ['🏢', 'Organization OS', 'The operating layer any learning org runs on'],
                ].map(([icon, title, desc]) => `
                  <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:7px;">
                    <div style="font-size:1rem;flex-shrink:0;margin-top:1px;">${icon}</div>
                    <div>
                      <div style="font-size:0.62rem;font-weight:800;color:var(--text);">${title}</div>
                      <div style="font-size:0.54rem;color:var(--muted);">${desc}</div>
                    </div>
                  </div>`).join('')}
              </div>
            </div>
            ${M.annotation('Structured social learning at any scale', '↑')}`,
        },
      ],
    },
  ];

  // --------------------------------------------------
  // State
  // --------------------------------------------------
  let activeSectionIdx = null;
  let activeStepIdx = 0;
  let completedSections = new Set();
  const TOUR_ID = 'spark-admin-tour';

  // --------------------------------------------------
  // Styles (namespaced sat- to avoid collision with tour.js)
  // --------------------------------------------------
  function injectStyles() {
    if (document.getElementById('sat-styles')) return;
    const s = document.createElement('style');
    s.id = 'sat-styles';
    s.textContent = `
      @keyframes satPulse { from{opacity:0.7} to{opacity:1} }
      @keyframes satFadeIn { from{opacity:0} to{opacity:1} }
      @keyframes satSlideUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
      @keyframes satSlideInR { from{opacity:0;transform:translateX(32px)} to{opacity:1;transform:translateX(0)} }
      @keyframes satSlideInL { from{opacity:0;transform:translateX(-32px)} to{opacity:1;transform:translateX(0)} }
      @keyframes satSpin { to{transform:rotate(360deg)} }

      #${TOUR_ID} {
        position:fixed;inset:0;z-index:9999;
        display:flex;flex-direction:column;
        background:var(--soft);font-family:var(--font);
        animation:satFadeIn 0.18s ease;overflow:hidden;
      }

      #sat-top {
        display:flex;align-items:center;gap:12px;
        padding:12px 24px;background:var(--card);
        border-bottom:1px solid var(--border);flex-shrink:0;
      }
      #sat-logo {
        display:flex;align-items:center;gap:7px;
        font-size:0.95rem;font-weight:900;color:var(--text);letter-spacing:-0.3px;
      }
      #sat-hex {
        width:24px;height:24px;
        background:linear-gradient(135deg,var(--blue),var(--teal));
        clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
        display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.7rem;
      }
      #sat-tag {
        font-size:0.62rem;font-weight:800;padding:2px 9px;border-radius:999px;
        background:var(--sky);color:var(--blue);
      }
      #sat-prog-wrap { flex:1;height:3px;background:var(--border);border-radius:2px;overflow:hidden; }
      #sat-prog { height:100%;background:var(--teal);border-radius:2px;transition:width 0.35s ease; }
      #sat-counter { font-size:0.72rem;font-weight:700;color:var(--muted);white-space:nowrap; }
      #sat-exit {
        background:none;border:1px solid var(--border);border-radius:var(--radius-sm);
        color:var(--muted);font-size:0.78rem;font-weight:600;padding:5px 12px;
        cursor:pointer;font-family:var(--font);transition:all 0.15s;
      }
      #sat-exit:hover { border-color:var(--rose);color:var(--rose); }

      #sat-hub {
        flex:1;overflow-y:auto;padding:2rem;
        display:flex;flex-direction:column;align-items:center;
      }
      #sat-hub-title { font-size:1.6rem;font-weight:900;color:var(--text);letter-spacing:-0.4px;margin-bottom:0.4rem;text-align:center; }
      #sat-hub-sub { font-size:0.95rem;color:var(--muted);margin-bottom:2rem;text-align:center;max-width:520px; }
      #sat-hub-grid {
        display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
        gap:12px;width:100%;max-width:800px;
      }
      .sat-hub-card {
        background:var(--card);border:1px solid var(--border);
        border-radius:var(--radius);padding:1.25rem;cursor:pointer;
        transition:all 0.15s;position:relative;overflow:hidden;
        animation:satSlideUp 0.2s ease both;
      }
      .sat-hub-card:hover { border-color:var(--teal);transform:translateY(-2px);box-shadow:0 4px 20px rgba(58,188,177,0.12); }
      .sat-hub-card.done::after { content:'✓';position:absolute;top:8px;right:10px;font-size:0.7rem;font-weight:800;color:var(--blue); }
      .sat-hub-icon { font-size:2.6rem;margin-bottom:0.5rem;display:block; }
      .sat-hub-label { font-size:1.05rem;font-weight:800;color:var(--text);margin-bottom:0.25rem; }
      .sat-hub-desc { font-size:0.88rem;color:var(--muted);line-height:1.4; }
      .sat-hub-badge { display:inline-block;margin-top:0.5rem;font-size:0.65rem;font-weight:700;padding:2px 8px;border-radius:999px;background:var(--sky);color:var(--blue); }

      #sat-section { flex:1;display:flex;flex-direction:column;overflow:hidden; }
      #sat-sec-header {
        display:flex;align-items:center;gap:10px;
        padding:10px 24px;background:var(--card);
        border-bottom:1px solid var(--border);flex-shrink:0;
      }
      #sat-back-hub {
        background:none;border:1px solid var(--border);border-radius:var(--radius-sm);
        color:var(--muted);font-size:0.78rem;font-weight:600;padding:5px 12px;
        cursor:pointer;font-family:var(--font);transition:all 0.15s;
      }
      #sat-back-hub:hover { border-color:var(--blue);color:var(--blue); }
      #sat-sec-label { font-size:0.88rem;font-weight:800;color:var(--text);flex:1; }
      #sat-sec-dots { display:flex;gap:5px; }
      .sat-sec-dot { width:7px;height:7px;border-radius:50%;background:var(--border);transition:all 0.2s;cursor:pointer; }
      .sat-sec-dot.active { background:var(--teal);transform:scale(1.35); }
      .sat-sec-dot.done { background:var(--blue); }

      #sat-step-area { flex:1;display:flex;gap:2rem;padding:1.5rem 2rem;overflow:hidden;align-items:stretch; }
      #sat-step-left { flex:1;display:flex;flex-direction:column;justify-content:center;max-width:340px;flex-shrink:0; }
      .sat-step-sec-tag { font-size:0.68rem;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;color:var(--teal);margin-bottom:0.5rem; }
      .sat-step-title { font-size:1.85rem;font-weight:900;color:var(--text);letter-spacing:-0.4px;line-height:1.2;margin-bottom:0.75rem; }
      .sat-step-desc { font-size:1.02rem;color:var(--muted);line-height:1.7;margin-bottom:1.25rem; }
      #sat-step-right { flex:1;display:flex;align-items:center;justify-content:center;min-width:0; }
      #sat-mockup-wrap { width:100%;max-width:520px;transform:scale(1.25);transform-origin:top center; }

      #sat-sec-footer {
        display:flex;align-items:center;justify-content:space-between;
        padding:12px 24px;border-top:1px solid var(--border);
        background:var(--card);flex-shrink:0;
      }
      .sat-nav-btn {
        background:none;border:1px solid var(--border);border-radius:var(--radius-sm);
        color:var(--muted);font-family:var(--font);font-size:0.85rem;
        font-weight:600;padding:7px 18px;cursor:pointer;transition:all 0.15s;
      }
      .sat-nav-btn:hover { border-color:var(--blue);color:var(--blue); }
      .sat-nav-btn:disabled { opacity:0.3;pointer-events:none; }

      #sat-finish { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2rem;text-align:center; }
      #sat-finish-icon { font-size:3.5rem;margin-bottom:1rem; }
      #sat-finish-title { font-size:1.6rem;font-weight:900;color:var(--text);margin-bottom:0.5rem; }
      #sat-finish-sub { font-size:0.95rem;color:var(--muted);margin-bottom:2rem;max-width:440px; }
      .sat-finish-actions { display:flex;gap:10px;flex-wrap:wrap;justify-content:center; }

      #sat-loading {
        position:absolute;inset:0;background:var(--soft);
        display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.75rem;
        z-index:2;opacity:0;pointer-events:none;transition:opacity 0.15s;
      }
      #sat-loading.show { opacity:1;pointer-events:all; }
      .sat-spinner { width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--teal);border-radius:50%;animation:satSpin 0.6s linear infinite; }

      .sat-cta {
        display:inline-flex;align-items:center;gap:7px;
        background:var(--teal);color:#fff;border:none;
        border-radius:var(--radius-sm);padding:10px 22px;
        font-family:var(--font);font-size:0.9rem;font-weight:700;
        cursor:pointer;transition:opacity 0.15s,transform 0.15s;
      }
      .sat-cta:hover { opacity:0.88;transform:scale(1.02); }

      #sat-tour-btn {
        position:fixed;bottom:1.25rem;left:7rem;z-index:9000;
        background:var(--card);border:1px solid var(--border);
        border-radius:999px;padding:6px 14px;
        font-size:0.78rem;font-weight:800;color:var(--text);
        box-shadow:0 2px 8px rgba(0,0,0,0.15);cursor:pointer;
        font-family:var(--font);transition:all 0.15s;
        display:flex;align-items:center;gap:6px;
      }
      #sat-tour-btn:hover { border-color:var(--teal);color:var(--teal); }

      #sat-tour-menu {
        position:fixed;bottom:3.5rem;left:1.25rem;z-index:9001;
        background:var(--card);border:1px solid var(--border);
        border-radius:var(--radius);box-shadow:var(--shadow-lg);
        min-width:230px;overflow:hidden;
        transform:translateY(8px) scale(0.97);opacity:0;pointer-events:none;
        transition:all 0.15s cubic-bezier(0.34,1.56,0.64,1);
      }
      #sat-tour-menu.open { transform:translateY(0) scale(1);opacity:1;pointer-events:all; }
      .sat-menu-hdr { padding:9px 14px 5px;font-size:0.65rem;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--border); }
      .sat-menu-item {
        display:flex;align-items:center;gap:9px;padding:9px 14px;
        font-size:0.82rem;font-weight:600;color:var(--text);
        cursor:pointer;transition:background 0.1s;
        border:none;background:none;width:100%;text-align:left;font-family:var(--font);
      }
      .sat-menu-item:hover { background:var(--sky);color:var(--blue); }
      .sat-menu-dot { width:8px;height:8px;border-radius:50%;flex-shrink:0; }
      .sat-menu-done { font-size:0.6rem;color:var(--blue);margin-left:auto; }

      @media(max-width:700px){
        #sat-step-area { flex-direction:column;padding:1rem;gap:1rem; }
        #sat-step-left { max-width:100%; }
        .sat-step-title { font-size:1.2rem; }
      }
    `;
    document.head.appendChild(s);
  }

  // --------------------------------------------------
  // Build shell
  // --------------------------------------------------
  function buildShell() {
    if (document.getElementById(TOUR_ID)) return;
    const el = document.createElement('div');
    el.id = TOUR_ID;
    el.innerHTML = `
      <div id="sat-top">
        <div id="sat-logo"><div id="sat-hex">⚡</div>SparK <span id="sat-tag">Platform Tour</span></div>
        <div id="sat-prog-wrap"><div id="sat-prog" style="width:0%"></div></div>
        <span id="sat-counter"></span>
        <button id="sat-exit">✕ Exit</button>
      </div>
      <div id="sat-loading"><div class="sat-spinner"></div></div>
      <div id="sat-hub" style="display:none;"></div>
      <div id="sat-section" style="display:none;">
        <div id="sat-sec-header">
          <button id="sat-back-hub">← Hub</button>
          <span id="sat-sec-label"></span>
          <div id="sat-sec-dots"></div>
        </div>
        <div id="sat-step-area">
          <div id="sat-step-left"></div>
          <div id="sat-step-right"><div id="sat-mockup-wrap"></div></div>
        </div>
        <div id="sat-sec-footer">
          <button class="sat-nav-btn" id="sat-prev">← Back</button>
          <div></div>
          <button class="sat-nav-btn" id="sat-next">Next →</button>
        </div>
      </div>
      <div id="sat-finish" style="display:none;"></div>
    `;
    document.body.appendChild(el);
    document.getElementById('sat-exit').addEventListener('click', closeTour);
    document.getElementById('sat-back-hub').addEventListener('click', showHub);
    document.getElementById('sat-prev').addEventListener('click', () => stepNav(-1));
    document.getElementById('sat-next').addEventListener('click', () => stepNav(1));
    document.addEventListener('keydown', onKey);
  }

  // --------------------------------------------------
  // Hub
  // --------------------------------------------------
  function showHub() {
    const total = SECTIONS.reduce((a, s) => a + s.steps.length, 0);
    const done = [...completedSections].reduce((a, si) => a + SECTIONS[si].steps.length, 0);
    document.getElementById('sat-prog').style.width = (total ? Math.round(done / total * 100) : 0) + '%';
    document.getElementById('sat-counter').textContent = `${completedSections.size}/${SECTIONS.length} sections`;

    hide('sat-section'); hide('sat-finish'); hide('sat-loading');
    show('sat-hub');

    const hub = document.getElementById('sat-hub');
    hub.innerHTML = `
      <h1 id="sat-hub-title">SparK — Platform Overview</h1>
      <p id="sat-hub-sub">Pick a section to explore. Each one is self-contained — jump in anywhere, in any order.</p>
      <div id="sat-hub-grid"></div>
    `;
    const grid = document.getElementById('sat-hub-grid');
    SECTIONS.forEach((sec, si) => {
      const card = document.createElement('div');
      card.className = 'sat-hub-card' + (completedSections.has(si) ? ' done' : '');
      card.style.animationDelay = (si * 0.05) + 's';
      card.innerHTML = `
        <span class="sat-hub-icon">${sec.label.split(' ')[0]}</span>
        <div class="sat-hub-label">${sec.label.replace(/^\S+\s/, '')}</div>
        <div class="sat-hub-desc">${sec.desc}</div>
        <span class="sat-hub-badge">${sec.steps.length} slide${sec.steps.length > 1 ? 's' : ''}</span>
      `;
      card.addEventListener('click', () => openSection(si));
      grid.appendChild(card);
    });
    activeSectionIdx = null;
  }

  // --------------------------------------------------
  // Section / step rendering
  // --------------------------------------------------
  function openSection(si, withLoad) {
    activeSectionIdx = si;
    activeStepIdx = 0;
    if (withLoad) {
      show('sat-loading');
      hide('sat-hub'); hide('sat-section'); hide('sat-finish');
      setTimeout(() => { hide('sat-loading'); renderSection(); }, 500);
    } else {
      hide('sat-hub'); hide('sat-finish'); hide('sat-loading');
      renderSection();
    }
  }

  function renderSection(dir) {
    const sec = SECTIONS[activeSectionIdx];
    const step = sec.steps[activeStepIdx];

    const total = SECTIONS.reduce((a, s) => a + s.steps.length, 0);
    const doneSteps = [...completedSections].reduce((a, si) => a + SECTIONS[si].steps.length, 0);
    const pct = total ? Math.round((doneSteps + activeStepIdx + 1) / total * 100) : 0;
    document.getElementById('sat-prog').style.width = pct + '%';
    document.getElementById('sat-counter').textContent = `${activeStepIdx + 1} / ${sec.steps.length}`;
    document.getElementById('sat-sec-label').textContent = sec.label;

    // Dots
    const dotsEl = document.getElementById('sat-sec-dots');
    dotsEl.innerHTML = '';
    sec.steps.forEach((_, i) => {
      const d = document.createElement('div');
      d.className = 'sat-sec-dot' + (i === activeStepIdx ? ' active' : i < activeStepIdx ? ' done' : '');
      d.addEventListener('click', () => { activeStepIdx = i; renderSection(0); });
      dotsEl.appendChild(d);
    });

    document.getElementById('sat-prev').disabled = activeStepIdx === 0;
    const isLast = activeStepIdx === sec.steps.length - 1;
    document.getElementById('sat-next').textContent = isLast ? 'Finish section ✓' : 'Next →';

    // Left
    const left = document.getElementById('sat-step-left');
    left.innerHTML = `
      <div class="sat-step-sec-tag">${sec.label}</div>
      <div class="sat-step-title">${step.title}</div>
      <p class="sat-step-desc">${step.desc}</p>
    `;
    left.style.animation = 'none'; void left.offsetWidth;
    left.style.animation = 'satSlideInL 0.15s ease';

    // Mockup
    const wrap = document.getElementById('sat-mockup-wrap');
    wrap.innerHTML = step.mockup ? step.mockup() : '';
    wrap.style.animation = 'none'; void wrap.offsetWidth;
    wrap.style.animation = (dir < 0) ? 'satSlideInL 0.15s ease' : 'satSlideInR 0.15s ease';

    show('sat-section');
  }

  function stepNav(dir) {
    const sec = SECTIONS[activeSectionIdx];
    const next = activeStepIdx + dir;
    if (next < 0) return;
    if (next >= sec.steps.length) { finishSection(); return; }
    activeStepIdx = next;
    renderSection(dir);
  }

  function finishSection() {
    completedSections.add(activeSectionIdx);
    const allDone = completedSections.size >= SECTIONS.length;
    if (allDone) { showFinish(); return; }

    hide('sat-section');
    const nextSi = activeSectionIdx + 1 < SECTIONS.length ? activeSectionIdx + 1 : null;
    const nextSec = nextSi !== null ? SECTIONS[nextSi] : null;
    const finish = document.getElementById('sat-finish');
    finish.innerHTML = `
      <div id="sat-finish-icon">✅</div>
      <div id="sat-finish-title">${SECTIONS[activeSectionIdx].label.replace(/^\S+\s/, '')} — done!</div>
      <p id="sat-finish-sub">What would you like to cover next?</p>
      <div class="sat-finish-actions">
        ${nextSec ? `<button class="sat-cta" id="sat-goto-next">Next: ${nextSec.label} →</button>` : ''}
        <button class="sat-nav-btn" id="sat-goto-hub">← Back to hub</button>
      </div>
    `;
    show('sat-finish');
    document.getElementById('sat-goto-hub').addEventListener('click', showHub);
    const nb = document.getElementById('sat-goto-next');
    if (nb) nb.addEventListener('click', () => openSection(nextSi));
  }

  function showFinish() {
    hide('sat-section'); hide('sat-hub');
    const finish = document.getElementById('sat-finish');
    finish.innerHTML = `
      <div id="sat-finish-icon">🎉</div>
      <div id="sat-finish-title">That's the full picture.</div>
      <p id="sat-finish-sub">You've seen the product, the market, the model, and where we're going. Questions? Let's talk.</p>
      <div class="sat-finish-actions">
        <button class="sat-cta" onclick="window.SparkAdminTour.close()">Close tour</button>
        <button class="sat-nav-btn" id="sat-restart-hub">Review a section</button>
      </div>
    `;
    show('sat-finish');
    document.getElementById('sat-restart-hub').addEventListener('click', () => { completedSections.clear(); showHub(); });
    document.getElementById('sat-prog').style.width = '100%';
    document.getElementById('sat-counter').textContent = 'Complete';
  }

  // --------------------------------------------------
  // Helpers
  // --------------------------------------------------
  function show(id) { const e = document.getElementById(id); if (e) e.style.display = ''; }
  function hide(id) { const e = document.getElementById(id); if (e) e.style.display = 'none'; }

  function onKey(e) {
    if (!document.getElementById(TOUR_ID)) { document.removeEventListener('keydown', onKey); return; }
    const sec = document.getElementById('sat-section');
    if (!sec || sec.style.display === 'none') return;
    if (e.key === 'ArrowRight') stepNav(1);
    if (e.key === 'ArrowLeft') stepNav(-1);
    if (e.key === 'Escape') closeTour();
  }

  // --------------------------------------------------
  // Open / close
  // --------------------------------------------------
  function openTour(jumpSi) {
    completedSections = new Set();
    injectStyles();
    buildShell();
    hide('sat-hub'); hide('sat-section'); hide('sat-finish');
    show('sat-loading');
    setTimeout(() => {
      hide('sat-loading');
      if (jumpSi !== undefined) openSection(jumpSi);
      else showHub();
    }, 380);
  }

  function closeTour() {
    const el = document.getElementById(TOUR_ID);
    if (!el) return;
    el.style.opacity = '0'; el.style.transition = 'opacity 0.18s';
    document.removeEventListener('keydown', onKey);
    setTimeout(() => el.remove(), 200);
  }

  // --------------------------------------------------
  // Launch button
  // --------------------------------------------------
  function buildLaunchButton() {
    if (document.getElementById('sat-tour-btn')) return;
    injectStyles();

    const btn = document.createElement('button');
    btn.id = 'sat-tour-btn';
    btn.innerHTML = '🎯 Platform Tour';
    btn.addEventListener('click', toggleMenu);
    document.body.appendChild(btn);

    const menu = document.createElement('div');
    menu.id = 'sat-tour-menu';
    document.body.appendChild(menu);

    document.addEventListener('click', e => {
      if (!btn.contains(e.target) && !menu.contains(e.target)) closeMenu();
    });
  }

  function buildMenu() {
    const menu = document.getElementById('sat-tour-menu');
    if (!menu) return;
    menu.innerHTML = `<div class="sat-menu-hdr">Jump to section</div>`;
    const fullItem = document.createElement('button');
    fullItem.className = 'sat-menu-item';
    fullItem.innerHTML = `<div class="sat-menu-dot" style="background:var(--teal)"></div> Start full tour`;
    fullItem.addEventListener('click', () => { closeMenu(); openTour(); });
    menu.appendChild(fullItem);

    const divider = document.createElement('div');
    divider.style.cssText = 'border-top:1px solid var(--border);margin:4px 0;';
    menu.appendChild(divider);

    SECTIONS.forEach((sec, si) => {
      const item = document.createElement('button');
      item.className = 'sat-menu-item';
      const done = completedSections.has(si);
      item.innerHTML = `
        <div class="sat-menu-dot" style="background:${sec.color}"></div>
        ${sec.label}
        ${done ? '<span class="sat-menu-done">✓</span>' : ''}
      `;
      item.addEventListener('click', () => {
        closeMenu();
        if (document.getElementById(TOUR_ID)) openSection(si, true);
        else openTour(si);
      });
      menu.appendChild(item);
    });
  }

  function toggleMenu() {
    const menu = document.getElementById('sat-tour-menu');
    if (!menu) return;
    const open = menu.classList.contains('open');
    if (!open) buildMenu();
    menu.classList.toggle('open', !open);
  }

  function closeMenu() {
    const m = document.getElementById('sat-tour-menu');
    if (m) m.classList.remove('open');
  }

  // --------------------------------------------------
  // Init
  // --------------------------------------------------
  function init() {
    const role = document.body.dataset.role;
    if (role === 'teacher' || role === 'admin') {
      buildLaunchButton();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // --------------------------------------------------
  // Public API
  // --------------------------------------------------
  window.SparkAdminTour = {
    start: (si) => openTour(si),
    close: closeTour,
    openSection: (si) => openSection(si, true),
  };

})();