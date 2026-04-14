// ============================================
//  SparK Tour v3
//  Hub screen → section tours → finish screen
//  Animated HTML/CSS mockups per step
// ============================================
(function () {
  'use strict';

  // --------------------------------------------------
  // MOCKUP HELPERS — reusable HTML snippets
  // --------------------------------------------------
  const M = {
    topbar: (active) => `
      <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:var(--card);border-bottom:1px solid var(--border);border-radius:8px 8px 0 0;">
        <div style="width:18px;height:18px;background:var(--blue);clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.5rem;">⚡</div>
        <span style="font-weight:900;font-size:0.7rem;color:var(--text);">SparK</span>
        <div style="flex:1;height:14px;background:var(--soft);border:1px solid var(--border);border-radius:4px;margin:0 4px;"></div>
        ${['Feed','Classrooms','Topics'].map(l=>`<span style="font-size:0.6rem;font-weight:700;padding:2px 6px;border-radius:4px;color:${l===active?'var(--blue)':'var(--muted)'};background:${l===active?'var(--sky)':'none'};">${l}</span>`).join('')}
        <div style="width:20px;height:20px;border-radius:50%;background:var(--teal);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.55rem;font-weight:800;">ME</div>
      </div>`,

    sidebar: (items, active) => `
      <div style="width:110px;flex-shrink:0;padding:8px;display:flex;flex-direction:column;gap:2px;">
        ${items.map(([icon,label])=>`
          <div style="display:flex;align-items:center;gap:5px;padding:5px 7px;border-radius:5px;background:${label===active?'var(--sky)':'none'};color:${label===active?'var(--blue)':'var(--muted)'};">
            <span style="font-size:0.7rem;">${icon}</span>
            <span style="font-size:0.6rem;font-weight:700;">${label}</span>
          </div>`).join('')}
      </div>`,

    postCard: (title, topic, preview, highlight) => `
      <div style="background:var(--card);border:${highlight?'2px solid var(--teal)':'1px solid var(--border)'};border-radius:8px;padding:8px 10px;margin-bottom:6px;${highlight?'box-shadow:0 0 0 3px rgba(58,188,177,0.15);':''}">
        <div style="display:flex;gap:6px;align-items:center;margin-bottom:4px;">
          <span style="background:var(--sky);color:var(--blue);font-size:0.55rem;font-weight:800;padding:1px 5px;border-radius:3px;">${topic}</span>
          <span style="font-size:0.55rem;color:var(--muted);">alex.smith · 2h ago</span>
        </div>
        <div style="font-size:0.65rem;font-weight:700;color:var(--text);margin-bottom:3px;">${title}</div>
        <div style="font-size:0.58rem;color:var(--muted);line-height:1.4;">${preview}</div>
        <div style="display:flex;gap:6px;margin-top:5px;">
          <span style="font-size:0.55rem;color:var(--muted);">▲ 4</span>
          <span style="font-size:0.55rem;color:var(--muted);">💬 3 replies</span>
        </div>
      </div>`,

    assignmentCard: (title, due, status, highlight) => `
      <div style="background:var(--card);border:${highlight?'2px solid var(--teal)':'1px solid var(--border)'};border-radius:8px;padding:8px 12px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;${highlight?'box-shadow:0 0 0 3px rgba(58,188,177,0.15);':''}">
        <div>
          <div style="font-size:0.65rem;font-weight:800;color:var(--text);">${title}</div>
          ${due?`<div style="font-size:0.55rem;color:var(--muted);margin-top:2px;">Due: ${due}</div>`:''}
        </div>
        <span style="font-size:0.55rem;font-weight:700;padding:2px 8px;border-radius:999px;background:${status==='Submitted'?'rgba(76,175,130,0.15)':status==='Graded'?'rgba(91,163,217,0.15)':'var(--sky)'};color:${status==='Submitted'?'var(--green)':status==='Graded'?'var(--blue)':'var(--muted)'};">${status}</span>
      </div>`,

    pill: (label, color='var(--teal)') => `<span style="font-size:0.6rem;font-weight:700;padding:2px 8px;border-radius:999px;background:${color};color:#fff;">${label}</span>`,

    bubble: (msg, mine, sender) => `
      <div style="display:flex;flex-direction:column;align-items:${mine?'flex-end':'flex-start'};margin-bottom:6px;">
        ${!mine?`<span style="font-size:0.5rem;color:var(--muted);margin-bottom:2px;">${sender}</span>`:''}
        <div style="max-width:75%;padding:6px 10px;border-radius:${mine?'10px 3px 10px 10px':'3px 10px 10px 10px'};background:${mine?'var(--blue)':'var(--sky)'};color:${mine?'#fff':'var(--text)'};font-size:0.6rem;line-height:1.5;">${msg}</div>
      </div>`,

    quizBlock: (type, question, choices, highlight) => `
      <div style="background:var(--card);border:${highlight?'2px solid var(--teal)':'1px solid var(--border)'};border-radius:8px;padding:8px 10px;margin-bottom:6px;">
        <div style="display:flex;gap:5px;align-items:center;margin-bottom:5px;">
          <span style="font-size:0.55rem;font-weight:800;padding:1px 6px;border-radius:3px;background:${type==='multiple_choice'?'#dbeafe':type==='true_false'?'#dcfce7':'#fef9c3'};color:${type==='multiple_choice'?'#1e40af':type==='true_false'?'#166534':'#854d0e'};">${type.replace('_',' ')}</span>
        </div>
        <div style="font-size:0.62rem;font-weight:700;color:var(--text);margin-bottom:5px;">${question}</div>
        ${choices?`<div style="display:flex;flex-direction:column;gap:3px;">${choices.map((c,i)=>`<div style="display:flex;align-items:center;gap:5px;padding:3px 6px;border-radius:4px;border:1px solid ${i===0?'var(--teal)':'var(--border)'};background:${i===0?'rgba(58,188,177,0.08)':'var(--soft)'}"><div style="width:8px;height:8px;border-radius:50%;border:1.5px solid ${i===0?'var(--teal)':'var(--border)'};background:${i===0?'var(--teal)':'none'};flex-shrink:0;"></div><span style="font-size:0.58rem;color:var(--text);">${c}</span></div>`).join('')}</div>`:''}
      </div>`,

    annotation: (text, arrow='↑') => `
      <div style="display:flex;flex-direction:column;align-items:center;margin-top:6px;">
        <span style="font-size:1rem;color:var(--teal);animation:stPulse 1s ease-in-out infinite alternate;">${arrow}</span>
        <div style="background:var(--teal);color:#fff;font-size:0.65rem;font-weight:700;padding:4px 10px;border-radius:6px;text-align:center;max-width:200px;line-height:1.4;">${text}</div>
      </div>`,
  };

  // --------------------------------------------------
  // SECTION DEFINITIONS
  // --------------------------------------------------

  const SECTIONS = {

    // ==================== STUDENT ====================
    student: [
      // ---- Feed ----
      {
        id: 'feed', label: '🏠 Feed', color: 'var(--blue)',
        desc: 'Your class discussion board',
        steps: [
          {
            title: 'The Feed is your home base',
            desc: 'Every question, tip, and project your class shares shows up here. You can post, reply, and react.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="display:flex;background:var(--soft);min-height:140px;">
                  ${M.sidebar([['🏠','Feed'],['🏫','Classrooms'],['🏷️','Topics'],['🔔','Alerts'],['👤','Profile']],'Feed')}
                  <div style="flex:1;padding:8px;">
                    ${M.postCard('Why doesn\'t my loop print?','Python Basics','for i in range(5): print(i) is not working?',true)}
                    ${M.postCard('Challenge: FizzBuzz','Logic','Try this classic problem: print 1 to 100...',false)}
                  </div>
                </div>
              </div>
              ${M.annotation('Posts from your class appear here')}`,
          },
          {
            title: 'Posts are organized by topic',
            desc: 'Click any topic pill on the left sidebar to filter the feed. Topics include Python Basics, Debugging Help, Project Showcase, and more.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="display:flex;background:var(--soft);min-height:140px;">
                  <div style="width:110px;flex-shrink:0;padding:8px;display:flex;flex-direction:column;gap:2px;">
                    ${[['🏠','Feed'],['🏫','Classrooms'],['🏷️','Topics']].map(([i,l])=>`<div style="display:flex;align-items:center;gap:5px;padding:5px 7px;border-radius:5px;color:var(--muted);"><span style="font-size:0.7rem;">${i}</span><span style="font-size:0.6rem;font-weight:700;">${l}</span></div>`).join('')}
                    <div style="height:1px;background:var(--border);margin:4px 0;"></div>
                    <div style="font-size:0.55rem;font-weight:800;color:var(--muted);padding:2px 7px;letter-spacing:0.8px;">TOPICS</div>
                    ${[['Python Basics',true],['Debugging Help',false],['Project Showcase',false],['Community Chat',false]].map(([l,a])=>`<div style="font-size:0.6rem;font-weight:700;padding:3px 7px;border-radius:4px;background:${a?'var(--blue)':'var(--sky)'};color:${a?'#fff':'var(--blue)'};cursor:pointer;">${l}</div>`).join('')}
                  </div>
                  <div style="flex:1;padding:8px;">
                    ${M.postCard('Why doesn\'t my loop print?','Python Basics','for i in range(5): print(i) is not working?',true)}
                    ${M.postCard('What does == mean?','Python Basics','Is == the same as =?',false)}
                  </div>
                </div>
              </div>
              ${M.annotation('Click a topic to filter posts', '↑')}`,
          },
          {
            title: 'React and reply to posts',
            desc: 'Click into any post to read replies and add your own. Use emoji reactions to show support without writing a full reply.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.7rem;font-weight:800;color:var(--text);margin-bottom:4px;">Why doesn't my loop print?</div>
                    <div style="font-size:0.6rem;color:var(--muted);margin-bottom:8px;">for i in range(5): print(i) is not working?</div>
                    <div style="display:flex;gap:6px;margin-bottom:8px;">
                      ${['❤️','💡','🤔','🎯'].map(e=>`<button style="background:var(--soft);border:1px solid var(--border);border-radius:5px;padding:2px 6px;font-size:0.8rem;cursor:pointer;">${e}</button>`).join('')}
                    </div>
                    <div style="border-top:1px solid var(--border);padding-top:6px;">
                      <div style="font-size:0.6rem;font-weight:700;color:var(--muted);margin-bottom:4px;">2 Replies</div>
                      <div style="background:var(--soft);border-radius:6px;padding:5px 8px;margin-bottom:4px;font-size:0.58rem;color:var(--muted);">Check your indentation!</div>
                      <div style="background:var(--sky);border:2px solid var(--teal);border-radius:6px;padding:5px 8px;font-size:0.58rem;color:var(--text);">Try putting print on a new line ↵</div>
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Click reactions or add a reply', '↑')}`,
          },
          {
            title: 'Create your own post',
            desc: 'Click + New Post to ask a question or share something you built. Pick a topic and add your content — you can even format code with [code] tags.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.7rem;font-weight:800;color:var(--text);margin-bottom:8px;">New Post</div>
                    <div style="margin-bottom:6px;">
                      <div style="font-size:0.55rem;font-weight:800;color:var(--muted);margin-bottom:2px;">TOPIC</div>
                      <div style="background:var(--soft);border:1px solid var(--teal);border-radius:4px;padding:4px 8px;font-size:0.6rem;color:var(--text);">Python Basics ▾</div>
                    </div>
                    <div style="margin-bottom:6px;">
                      <div style="font-size:0.55rem;font-weight:800;color:var(--muted);margin-bottom:2px;">TITLE</div>
                      <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:0.6rem;color:var(--text);">How do I use a for loop?</div>
                    </div>
                    <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:6px 8px;font-size:0.6rem;color:var(--muted);min-height:36px;">Write your post here…</div>
                    <div style="margin-top:6px;display:flex;justify-content:flex-end;">
                      <div style="background:var(--blue);color:#fff;font-size:0.6rem;font-weight:800;padding:4px 12px;border-radius:5px;">Post</div>
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Fill in title + topic and hit Post', '↑')}`,
          },
        ],
      },

      // ---- Assignments ----
      {
        id: 'assignments', label: '📋 Assignments', color: 'var(--amber)',
        desc: 'Submit and track your work',
        steps: [
          {
            title: 'Find your assignments',
            desc: 'Head to Classrooms and open your class. All assignments your teacher posted are listed here with their due dates.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="display:flex;background:var(--soft);min-height:140px;">
                  ${M.sidebar([['🏠','Overview'],['⬅','All Classes']],'Overview')}
                  <div style="flex:1;padding:8px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:6px;">CodeForward — Beginner Python</div>
                    ${M.assignmentCard('Build a Calculator','Apr 18','Open',true)}
                    ${M.assignmentCard('FizzBuzz & Beyond','Apr 25','Open',false)}
                    ${M.assignmentCard('Data Analysis','May 2','Submitted',false)}
                  </div>
                </div>
              </div>
              ${M.annotation('Your assignments are listed here', '↑')}`,
          },
          {
            title: 'Read the instructions',
            desc: 'Open an assignment to see the full instructions, point value, and due date. Read carefully before starting — your teacher explains exactly what\'s needed.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.7rem;font-weight:900;color:var(--text);margin-bottom:2px;">Build a Calculator</div>
                    <div style="font-size:0.55rem;color:var(--muted);margin-bottom:6px;">Due: April 18 · 100 pts</div>
                    <div style="background:var(--sky);border-left:3px solid var(--blue);border-radius:4px;padding:6px 8px;font-size:0.6rem;color:var(--text);line-height:1.5;margin-bottom:8px;">
                      Use functions for each operation (+, -, *, /). Your calculator should loop so the user can keep calculating without restarting. Handle division by zero gracefully.
                    </div>
                    <div style="background:var(--teal);color:#fff;font-size:0.6rem;font-weight:800;padding:4px 10px;border-radius:5px;display:inline-block;">Start Assignment →</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Read instructions then click Start', '↑')}`,
          },
          {
            title: 'Submit your work',
            desc: 'Type or paste your answer in the submission box and click Submit. You can resubmit before the due date if you want to improve your answer.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:6px;">Your Submission</div>
                    <div style="background:var(--soft);border:2px solid var(--teal);border-radius:6px;padding:6px 8px;font-size:0.58rem;color:var(--text);font-family:monospace;line-height:1.6;min-height:52px;margin-bottom:6px;">
                      def add(a, b):<br/>
                      &nbsp;&nbsp;&nbsp;&nbsp;return a + b<br/>
                      <br/>
                      def calculator():
                    </div>
                    <div style="display:flex;gap:6px;">
                      <div style="background:var(--blue);color:#fff;font-size:0.6rem;font-weight:800;padding:4px 12px;border-radius:5px;">Submit</div>
                      <div style="background:var(--soft);border:1px solid var(--border);color:var(--muted);font-size:0.6rem;font-weight:700;padding:4px 10px;border-radius:5px;">Save Draft</div>
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Type your answer and hit Submit', '↑')}`,
          },
          {
            title: 'View your grade & feedback',
            desc: 'Once your teacher grades your submission, you\'ll see your grade and written feedback right here. Use it to improve next time!',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                      <div style="font-size:0.65rem;font-weight:900;color:var(--text);">Build a Calculator</div>
                      <div style="background:rgba(76,175,130,0.15);color:var(--green);font-size:0.7rem;font-weight:900;padding:3px 10px;border-radius:999px;">A</div>
                    </div>
                    <div style="background:var(--sky);border-left:3px solid var(--teal);border-radius:4px;padding:6px 8px;font-size:0.6rem;color:var(--text);line-height:1.5;">
                      <div style="font-size:0.55rem;font-weight:800;color:var(--teal);margin-bottom:2px;">TEACHER FEEDBACK</div>
                      Great work! Clean code and good use of functions. Consider adding error handling for division by zero next time.
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Your grade and feedback appear here', '↑')}`,
          },
        ],
      },

      // ---- Quizzes ----
      {
        id: 'quizzes', label: '🧠 Quizzes', color: 'var(--rose)',
        desc: 'Interactive quiz assignments',
        steps: [
          {
            title: 'Quizzes have interactive blocks',
            desc: 'Some assignments are quizzes. Instead of a text box, you\'ll see a series of blocks — each one is a different type of question.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  ${M.quizBlock('multiple_choice','When does a while loop stop running?',['After it runs exactly once','When its condition becomes False','When it reaches the end of the file'],true)}
                  ${M.quizBlock('true_false','True or False: A while loop can run zero times.',null,false)}
                </div>
              </div>
              ${M.annotation('Each block is a different question type', '↑')}`,
          },
          {
            title: 'Multiple choice & true/false',
            desc: 'Click a bubble to select your answer. You can change your mind before submitting. The selected choice turns teal.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  ${M.quizBlock('multiple_choice','When does a while loop stop running?',['After it runs exactly once','When its condition becomes False','When it reaches the end of the file'],true)}
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px 10px;">
                    <div style="font-size:0.6rem;font-weight:700;color:var(--text);margin-bottom:5px;">True or False: A while loop can run zero times.</div>
                    <div style="display:flex;gap:6px;">
                      <div style="flex:1;padding:5px;border-radius:5px;border:2px solid var(--teal);background:rgba(58,188,177,0.1);text-align:center;font-size:0.62rem;font-weight:700;color:var(--teal);">✓ True</div>
                      <div style="flex:1;padding:5px;border-radius:5px;border:1px solid var(--border);background:var(--soft);text-align:center;font-size:0.62rem;font-weight:700;color:var(--muted);">False</div>
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Selected answer highlights in teal', '↑')}`,
          },
          {
            title: 'Code and short answer blocks',
            desc: 'For code prompts, type your Python directly in the block. For short answer, write a sentence or two. Both are graded by your teacher.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:2px solid var(--teal);border-radius:8px;padding:8px 10px;margin-bottom:6px;box-shadow:0 0 0 3px rgba(58,188,177,0.15);">
                    <div style="display:flex;gap:5px;margin-bottom:5px;"><span style="font-size:0.55rem;font-weight:800;padding:1px 6px;border-radius:3px;background:#f3e8ff;color:#6b21a8;">code</span></div>
                    <div style="font-size:0.62rem;font-weight:700;color:var(--text);margin-bottom:5px;">Write a while loop that counts down from 10 to 1.</div>
                    <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:5px 7px;font-family:monospace;font-size:0.6rem;color:var(--text);min-height:36px;line-height:1.6;">i = 10<br/>while i &gt;= 1:<br/>&nbsp;&nbsp;&nbsp;&nbsp;print(i)<br/>&nbsp;&nbsp;&nbsp;&nbsp;i -= 1</div>
                  </div>
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px 10px;">
                    <div style="display:flex;gap:5px;margin-bottom:5px;"><span style="font-size:0.55rem;font-weight:800;padding:1px 6px;border-radius:3px;background:#fef9c3;color:#854d0e;">short answer</span></div>
                    <div style="font-size:0.62rem;font-weight:700;color:var(--text);margin-bottom:5px;">What is an infinite loop?</div>
                    <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:5px 7px;font-size:0.6rem;color:var(--muted);min-height:28px;">A loop that never stops because…</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Type code or text directly in the block', '↑')}`,
          },
          {
            title: 'Submit when all blocks are done',
            desc: 'Once you\'ve answered every required block, the Submit button activates. Auto-graded questions (multiple choice, true/false) are scored instantly.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:6px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                      <div style="font-size:0.65rem;font-weight:900;color:var(--text);">Quiz: While Loops</div>
                      <div style="font-size:0.6rem;font-weight:700;color:var(--green);">4/4 complete</div>
                    </div>
                    <div style="display:flex;gap:3px;margin-bottom:8px;">
                      ${[1,2,3,4].map(()=>`<div style="flex:1;height:4px;border-radius:2px;background:var(--teal);"></div>`).join('')}
                    </div>
                    <div style="background:var(--teal);color:#fff;font-size:0.65rem;font-weight:800;padding:6px;border-radius:6px;text-align:center;">Submit Quiz →</div>
                  </div>
                  <div style="background:rgba(76,175,130,0.1);border:1px solid var(--green);border-radius:8px;padding:8px 10px;">
                    <div style="font-size:0.6rem;font-weight:800;color:var(--green);margin-bottom:2px;">✓ Auto-graded: 5/5 pts</div>
                    <div style="font-size:0.58rem;color:var(--muted);">Multiple choice and true/false scored instantly</div>
                  </div>
                </div>
              </div>
              ${M.annotation('All blocks done? Hit Submit!', '↑')}`,
          },
        ],
      },

      // ---- Messages ----
      {
        id: 'messages', label: '💬 Messages', color: 'var(--green)',
        desc: 'Chat with your teacher & classmates',
        steps: [
          {
            title: 'Open the chat widget',
            desc: 'See the blue bubble in the bottom right corner? Click it to open your messages. It shows a badge when you have unread messages.',
            mockup: () => `
              <div style="position:relative;border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);min-height:120px;padding:8px;">
                  ${M.postCard('Why doesn\'t my loop print?','Python Basics','for i in range(5): print(i)...',false)}
                </div>
                <div style="position:absolute;bottom:12px;right:12px;width:36px;height:36px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center;color:#fff;font-size:1rem;box-shadow:0 4px 12px rgba(0,0,0,0.3);animation:stPulse 1s ease-in-out infinite alternate;">💬</div>
                <div style="position:absolute;bottom:30px;right:10px;background:var(--rose);color:#fff;font-size:0.5rem;font-weight:800;width:14px;height:14px;border-radius:50%;display:flex;align-items:center;justify-content:center;">2</div>
              </div>
              ${M.annotation('Click the chat bubble to open messages', '↑')}`,
          },
          {
            title: 'Your conversations',
            desc: 'The inbox lists all your conversations — DMs with your teacher and group chats. Unread ones have a blue dot.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="display:flex;background:var(--soft);">
                  <div style="width:160px;background:var(--card);border-right:1px solid var(--border);">
                    <div style="padding:8px 10px;border-bottom:1px solid var(--border);">
                      <div style="font-size:0.65rem;font-weight:900;color:var(--text);">Messages</div>
                    </div>
                    ${[['AJ','alex.johnson (Teacher)','Can you help with FizzBuzz?',true],['SG','Study Group','Anyone else confused about Part 2?',true],['TW','taylor.williams','Got it working!',false]].map(([init,name,preview,unread])=>`
                      <div style="display:flex;align-items:center;gap:6px;padding:7px 10px;border-bottom:1px solid var(--border);background:${unread?'rgba(91,163,217,0.07)':'none'};">
                        <div style="width:22px;height:22px;border-radius:50%;background:var(--teal);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.5rem;font-weight:800;flex-shrink:0;">${init}</div>
                        <div style="flex:1;min-width:0;">
                          <div style="font-size:0.58rem;font-weight:700;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${name}</div>
                          <div style="font-size:0.52rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${preview}</div>
                        </div>
                        ${unread?`<div style="width:6px;height:6px;border-radius:50%;background:var(--blue);flex-shrink:0;"></div>`:''}
                      </div>`).join('')}
                  </div>
                  <div style="flex:1;padding:8px;display:flex;align-items:center;justify-content:center;">
                    <div style="font-size:0.65rem;color:var(--muted);">Select a conversation</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Blue dot = unread message', '↑')}`,
          },
          {
            title: 'Chat with your teacher',
            desc: 'Click a conversation to open it. Type in the box at the bottom and hit Send. Your teacher can reply anytime.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);">
                  <div style="padding:7px 10px;border-bottom:1px solid var(--border);background:var(--card);display:flex;align-items:center;gap:6px;">
                    <div style="width:22px;height:22px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.5rem;font-weight:800;">AJ</div>
                    <div style="font-size:0.62rem;font-weight:800;color:var(--text);">alex.johnson (Teacher)</div>
                  </div>
                  <div style="padding:8px;min-height:80px;">
                    ${M.bubble('Hey, I\'m stuck on FizzBuzz — can you help?',true,'')}
                    ${M.bubble('Of course! Where are you getting stuck?',false,'Teacher')}
                    ${M.bubble('I don\'t know how to check for both 3 and 5.',true,'')}
                  </div>
                  <div style="display:flex;gap:6px;padding:6px 8px;border-top:1px solid var(--border);background:var(--card);">
                    <div style="flex:1;background:var(--soft);border:1px solid var(--teal);border-radius:999px;padding:4px 10px;font-size:0.6rem;color:var(--muted);">Type a message…</div>
                    <div style="width:24px;height:24px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.7rem;">➤</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Type and send — your teacher will reply', '↑')}`,
          },
        ],
      },

      // ---- Profile ----
      {
        id: 'profile', label: '👤 Profile', color: 'var(--blue)',
        desc: 'Your profile and settings',
        steps: [
          {
            title: 'Visit your profile',
            desc: 'Click your avatar (circle with your initials) in the top right to open the menu, then click My Profile.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="position:relative;background:var(--soft);min-height:120px;padding:8px;">
                  <div style="position:absolute;top:8px;right:8px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px;min-width:120px;box-shadow:var(--shadow-lg);">
                    ${[['👤','My Profile'],['⚙️','Settings'],['🚪','Logout']].map(([i,l],idx)=>`<div style="display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:4px;background:${idx===0?'var(--sky)':'none'};"><span style="font-size:0.7rem;">${i}</span><span style="font-size:0.6rem;font-weight:${idx===0?'800':'600'};color:${idx===0?'var(--blue)':idx===2?'var(--rose)':'var(--text)'};">${l}</span></div>`).join('')}
                  </div>
                </div>
              </div>
              ${M.annotation('Click your avatar → My Profile', '↑')}`,
          },
          {
            title: 'Your profile page',
            desc: 'Your profile shows your display name, bio, posts, and follower count. Classmates can find you here and follow your posts.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
                    <div style="height:36px;background:var(--sky);"></div>
                    <div style="padding:0 12px 10px;margin-top:-18px;">
                      <div style="width:36px;height:36px;border-radius:50%;background:var(--blue);border:3px solid var(--card);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.65rem;font-weight:800;margin-bottom:4px;">ME</div>
                      <div style="font-size:0.7rem;font-weight:900;color:var(--text);">Alex Smith</div>
                      <div style="font-size:0.58rem;color:var(--muted);margin-bottom:6px;">Student in Python program</div>
                      <div style="display:flex;gap:12px;">
                        <div style="text-align:center;"><div style="font-size:0.7rem;font-weight:800;color:var(--text);">12</div><div style="font-size:0.52rem;color:var(--muted);">Posts</div></div>
                        <div style="text-align:center;"><div style="font-size:0.7rem;font-weight:800;color:var(--text);">5</div><div style="font-size:0.52rem;color:var(--muted);">Followers</div></div>
                        <div style="text-align:center;"><div style="font-size:0.7rem;font-weight:800;color:var(--text);">8</div><div style="font-size:0.52rem;color:var(--muted);">Following</div></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Your posts, followers, and bio live here', '↑')}`,
          },
          {
            title: 'Update your settings',
            desc: 'Go to Settings to change your password, update your bio, toggle dark/light mode, and manage notification preferences.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:8px;">Settings</div>
                    ${[['Display Name','Alex Smith'],['Bio','Student in Python program'],['Password','••••••••']].map(([l,v])=>`
                      <div style="margin-bottom:6px;">
                        <div style="font-size:0.52rem;font-weight:800;color:var(--muted);margin-bottom:2px;">${l.toUpperCase()}</div>
                        <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:0.6rem;color:var(--text);">${v}</div>
                      </div>`).join('')}
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;padding-top:6px;border-top:1px solid var(--border);">
                      <div style="font-size:0.6rem;font-weight:700;color:var(--text);">🌙 Dark Mode</div>
                      <div style="width:28px;height:14px;border-radius:999px;background:var(--teal);position:relative;"><div style="position:absolute;right:2px;top:2px;width:10px;height:10px;border-radius:50%;background:#fff;"></div></div>
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Update your info anytime in Settings', '↑')}`,
          },
        ],
      },

      // ---- Classrooms ----
      {
        id: 'classrooms', label: '🏫 Classrooms', color: 'var(--teal)',
        desc: 'Join and manage your classes',
        steps: [
          {
            title: 'Your classrooms dashboard',
            desc: 'The Classrooms page shows every class you\'re enrolled in. Click one to see its assignments, announcements, and members.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
                    ${[['CodeForward — Beginner Python','Intro to Python for students','👩‍🏫 alex.johnson',true],['Web Dev Basics','HTML, CSS, and JavaScript','👩‍🏫 morgan.brown',false]].map(([name,desc,teacher,hl])=>`
                      <div style="background:var(--card);border:${hl?'2px solid var(--teal)':'1px solid var(--border)'};border-radius:8px;padding:8px;">
                        <div style="font-size:0.62rem;font-weight:800;color:var(--text);margin-bottom:2px;">${name}</div>
                        <div style="font-size:0.55rem;color:var(--muted);margin-bottom:4px;">${desc}</div>
                        <div style="font-size:0.52rem;color:var(--teal);font-weight:700;">${teacher}</div>
                      </div>`).join('')}
                  </div>
                </div>
              </div>
              ${M.annotation('Click a classroom card to enter it', '↑')}`,
          },
          {
            title: 'Join a classroom with a code',
            desc: 'Your teacher gives you a 6-character join code. Type it in the Join a Classroom box and you\'ll be enrolled instantly.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:2px solid var(--teal);border-radius:8px;padding:10px;box-shadow:0 0 0 3px rgba(58,188,177,0.15);">
                    <div style="font-size:0.65rem;font-weight:800;color:var(--text);margin-bottom:6px;">Join a Classroom</div>
                    <div style="display:flex;gap:6px;align-items:center;">
                      <div style="flex:1;background:var(--soft);border:2px solid var(--teal);border-radius:5px;padding:5px 8px;font-size:0.75rem;font-weight:900;color:var(--text);letter-spacing:0.3em;text-align:center;">YXG5WH</div>
                      <div style="background:var(--blue);color:#fff;font-size:0.6rem;font-weight:800;padding:5px 12px;border-radius:5px;">Join</div>
                    </div>
                    <div style="font-size:0.55rem;color:var(--muted);margin-top:4px;">Ask your teacher for the 6-character join code</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Enter the join code your teacher gives you', '↑')}`,
          },
        ],
      },
    ],

    // ==================== TEACHER ====================
    teacher: [
      // ---- Feed ----
      {
        id: 'feed', label: '🏠 Feed', color: 'var(--blue)',
        desc: 'Your class discussion board',
        steps: [
          {
            title: 'The Feed — your class community',
            desc: 'Students post questions and projects here organized by topic. You can pin important posts, reply as a teacher, and react to encourage students.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="display:flex;background:var(--soft);min-height:140px;">
                  ${M.sidebar([['🏠','Feed'],['🏫','Classrooms'],['🏷️','Topics'],['🚩','Moderation'],['⚙️','Settings']],'Feed')}
                  <div style="flex:1;padding:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                      <div style="font-size:0.65rem;font-weight:900;color:var(--text);">Class Feed</div>
                      <div style="background:var(--blue);color:#fff;font-size:0.55rem;font-weight:800;padding:2px 8px;border-radius:4px;">+ New Post</div>
                    </div>
                    ${M.postCard('Why doesn\'t my loop print?','Python Basics','for i in range(5): print(i) is not working?',true)}
                    ${M.postCard('Challenge: FizzBuzz','Logic','Try this classic problem: print 1 to 100...',false)}
                  </div>
                </div>
              </div>
              ${M.annotation('Student posts appear here in real time', '↑')}`,
          },
          {
            title: 'Reply and guide students',
            desc: 'Click into any post to reply. Your replies are highlighted as Teacher so students know it\'s authoritative guidance.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.68rem;font-weight:800;color:var(--text);margin-bottom:4px;">Why doesn't my loop print?</div>
                    <div style="font-size:0.6rem;color:var(--muted);margin-bottom:8px;">for i in range(5): print(i) is not working?</div>
                    <div style="border-top:1px solid var(--border);padding-top:6px;">
                      <div style="background:var(--soft);border-radius:5px;padding:5px 8px;margin-bottom:4px;font-size:0.58rem;color:var(--muted);">Check your indentation! — alex.smith</div>
                      <div style="background:rgba(91,163,217,0.1);border:1px solid var(--blue);border-radius:5px;padding:5px 8px;margin-bottom:6px;">
                        <div style="font-size:0.5rem;font-weight:800;color:var(--blue);margin-bottom:1px;">👩‍🏫 TEACHER</div>
                        <div style="font-size:0.58rem;color:var(--text);">Try putting print on its own indented line.</div>
                      </div>
                      <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:0.58rem;color:var(--muted);">Add a reply…</div>
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Your replies are labeled as Teacher', '↑')}`,
          },
          {
            title: 'Post announcements',
            desc: 'Use the Announcements post type to pin important messages to the top of the feed — reminders, due dates, or session links.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:2px solid var(--amber);border-radius:8px;padding:8px 10px;margin-bottom:6px;">
                    <div style="display:flex;gap:5px;align-items:center;margin-bottom:3px;">
                      <span style="background:var(--amber);color:#fff;font-size:0.52rem;font-weight:800;padding:1px 6px;border-radius:3px;">📢 ANNOUNCEMENT</span>
                    </div>
                    <div style="font-size:0.65rem;font-weight:800;color:var(--text);margin-bottom:2px;">Assignment Reminder</div>
                    <div style="font-size:0.58rem;color:var(--muted);">Calculator assignment is due this Friday!</div>
                  </div>
                  ${M.postCard('Why doesn\'t my loop print?','Python Basics','for i in range(5)...',false)}
                </div>
              </div>
              ${M.annotation('Announcements pin to the top of the feed', '↑')}`,
          },
        ],
      },

      // ---- Classrooms ----
      {
        id: 'classrooms', label: '🏫 Classrooms', color: 'var(--teal)',
        desc: 'Create and manage classes',
        steps: [
          {
            title: 'Create a classroom',
            desc: 'Click + New Classroom and give it a name and description. A unique join code is generated automatically — share it with your students.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:8px;">New Classroom</div>
                    ${[['Name','CodeForward — Beginner Python'],['Description','Intro to Python for students']].map(([l,v])=>`
                      <div style="margin-bottom:6px;">
                        <div style="font-size:0.52rem;font-weight:800;color:var(--muted);margin-bottom:2px;">${l.toUpperCase()}</div>
                        <div style="background:var(--soft);border:1px solid var(--teal);border-radius:4px;padding:4px 8px;font-size:0.6rem;color:var(--text);">${v}</div>
                      </div>`).join('')}
                    <div style="background:var(--blue);color:#fff;font-size:0.6rem;font-weight:800;padding:5px;border-radius:5px;text-align:center;margin-top:4px;">Create Classroom</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Name your class and hit Create', '↑')}`,
          },
          {
            title: 'Share the join code',
            desc: 'After creating a class, the join code appears in the left sidebar. Share it verbally, write it on the board, or use Print All QR for younger students.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="display:flex;background:var(--soft);min-height:130px;">
                  <div style="width:120px;flex-shrink:0;padding:8px;background:var(--card);border-right:1px solid var(--border);">
                    <div style="font-size:0.55rem;font-weight:800;color:var(--muted);margin-bottom:4px;">JOIN CODE</div>
                    <div style="font-size:1.1rem;font-weight:900;color:var(--teal);letter-spacing:0.15em;margin-bottom:4px;">YXG5WH</div>
                    <div style="font-size:0.5rem;color:var(--muted);margin-bottom:6px;">Share with students</div>
                    <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:3px 6px;font-size:0.55rem;font-weight:700;color:var(--text);text-align:center;">Copy Code</div>
                    <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:3px 6px;font-size:0.55rem;font-weight:700;color:var(--text);text-align:center;margin-top:3px;">🖨 Print QR</div>
                  </div>
                  <div style="flex:1;padding:8px;">
                    ${M.assignmentCard('Build a Calculator','Apr 18','Open',false)}
                  </div>
                </div>
              </div>
              ${M.annotation('Copy the join code or print QR cards', '↑')}`,
          },
          {
            title: 'Manage students',
            desc: 'Expand the Students section to see everyone enrolled. From here you can reset passwords, regenerate QR codes, and unlock locked accounts.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                      <div style="font-size:0.65rem;font-weight:900;color:var(--text);">Students (8)</div>
                      <div style="font-size:0.6rem;color:var(--blue);font-weight:700;">▲ Collapse</div>
                    </div>
                    ${[['AS','alex.smith'],['JJ','jordan.jones'],['TW','taylor.williams']].map(([init,user])=>`
                      <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 8px;background:var(--soft);border-radius:5px;margin-bottom:3px;">
                        <div style="display:flex;align-items:center;gap:5px;">
                          <div style="width:18px;height:18px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.45rem;font-weight:800;">${init}</div>
                          <span style="font-size:0.58rem;font-weight:600;color:var(--text);">${user}</span>
                        </div>
                        <div style="display:flex;gap:3px;">
                          <div style="font-size:0.5rem;color:var(--muted);border:1px solid var(--border);border-radius:3px;padding:1px 4px;">📱 QR</div>
                          <div style="font-size:0.5rem;color:var(--muted);border:1px solid var(--border);border-radius:3px;padding:1px 4px;">🔑 Reset</div>
                        </div>
                      </div>`).join('')}
                  </div>
                </div>
              </div>
              ${M.annotation('Manage each student from here', '↑')}`,
          },
        ],
      },

      // ---- Assignments ----
      {
        id: 'assignments', label: '📋 Assignments', color: 'var(--amber)',
        desc: 'Create, grade, and track work',
        steps: [
          {
            title: 'Create a new assignment',
            desc: 'Inside a classroom, click + New Assignment. Add a title, instructions, optional due date, and point value. Students can start submitting immediately.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:8px;">New Assignment</div>
                    ${[['Title','Build a Calculator'],['Instructions','Use functions for each operation…'],['Due Date','2026-04-18']].map(([l,v],i)=>`
                      <div style="margin-bottom:5px;">
                        <div style="font-size:0.52rem;font-weight:800;color:var(--muted);margin-bottom:2px;">${l.toUpperCase()}</div>
                        <div style="background:var(--soft);border:1px solid ${i===0?'var(--teal)':'var(--border)'};border-radius:4px;padding:4px 8px;font-size:0.6rem;color:var(--text);">${v}</div>
                      </div>`).join('')}
                    <div style="background:var(--blue);color:#fff;font-size:0.6rem;font-weight:800;padding:5px;border-radius:5px;text-align:center;margin-top:4px;">Publish Assignment</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Fill in details and publish when ready', '↑')}`,
          },
          {
            title: 'The Grade Grid',
            desc: 'Click Grade next to any assignment to open the Grade Grid — a spreadsheet view of every student\'s submission status.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
                    <div style="display:grid;grid-template-columns:100px 1fr 1fr 1fr;font-size:0.52rem;font-weight:800;color:var(--muted);padding:5px 8px;border-bottom:1px solid var(--border);background:var(--soft);">
                      <div>Student</div><div>Calculator</div><div>FizzBuzz</div><div>Data Analysis</div>
                    </div>
                    ${[['alex.smith','A','B','—'],['jordan.jones','B+','A','C'],['taylor.w','—','A','A']].map(([name,...grades])=>`
                      <div style="display:grid;grid-template-columns:100px 1fr 1fr 1fr;padding:5px 8px;border-bottom:1px solid var(--border);align-items:center;">
                        <div style="font-size:0.55rem;font-weight:700;color:var(--text);">${name}</div>
                        ${grades.map(g=>`<div style="font-size:0.6rem;font-weight:800;color:${g==='—'?'var(--muted)':g.startsWith('A')?'var(--green)':'var(--blue)'};">${g}</div>`).join('')}
                      </div>`).join('')}
                  </div>
                </div>
              </div>
              ${M.annotation('Click any cell to open that submission', '↑')}`,
          },
          {
            title: 'Leave a grade and feedback',
            desc: 'Click a student\'s cell to open their submission. Read their work, assign a letter grade, and write personalized feedback.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.6rem;font-weight:900;color:var(--text);margin-bottom:2px;">alex.smith — Build a Calculator</div>
                    <div style="background:var(--soft);border-radius:4px;padding:5px 7px;font-family:monospace;font-size:0.55rem;color:var(--text);line-height:1.6;margin-bottom:6px;border:1px solid var(--border);">def add(a, b):<br/>&nbsp;&nbsp;return a + b</div>
                    <div style="display:flex;gap:6px;margin-bottom:6px;">
                      <div style="flex:1;">
                        <div style="font-size:0.52rem;font-weight:800;color:var(--muted);margin-bottom:2px;">GRADE</div>
                        <div style="display:flex;gap:3px;">
                          ${['A','B','C','D','F'].map((g,i)=>`<div style="flex:1;padding:3px;border-radius:3px;border:${i===0?'2px solid var(--teal)':'1px solid var(--border)'};background:${i===0?'rgba(58,188,177,0.1)':'var(--soft)'};text-align:center;font-size:0.6rem;font-weight:800;color:${i===0?'var(--teal)':'var(--muted)'};">${g}</div>`).join('')}
                        </div>
                      </div>
                    </div>
                    <div style="background:var(--soft);border:1px solid var(--teal);border-radius:4px;padding:5px 7px;font-size:0.58rem;color:var(--muted);min-height:28px;">Great work! Clean code and…</div>
                    <div style="background:var(--teal);color:#fff;font-size:0.6rem;font-weight:800;padding:4px;border-radius:4px;text-align:center;margin-top:6px;">Save Grade</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Pick a grade and write feedback, then save', '↑')}`,
          },
          {
            title: 'Export grades',
            desc: 'Click ⬇ Export Grades to download a CSV of all grades for the classroom. Great for importing into your school\'s gradebook.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="display:flex;gap:6px;justify-content:flex-end;margin-bottom:6px;">
                    <div style="background:var(--soft);border:1px solid var(--border);color:var(--muted);font-size:0.6rem;font-weight:700;padding:4px 10px;border-radius:5px;">+ Add Students</div>
                    <div style="background:var(--blue);color:#fff;font-size:0.6rem;font-weight:700;padding:4px 10px;border-radius:5px;">+ New Assignment</div>
                    <div style="background:var(--teal);color:#fff;font-size:0.6rem;font-weight:800;padding:4px 10px;border-radius:5px;box-shadow:0 0 0 2px rgba(58,188,177,0.3);">⬇ Export Grades</div>
                  </div>
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center;">
                    <div style="font-size:1.5rem;margin-bottom:4px;">📊</div>
                    <div style="font-size:0.62rem;font-weight:800;color:var(--text);margin-bottom:2px;">grades_codeforward.csv</div>
                    <div style="font-size:0.55rem;color:var(--muted);">All students · All assignments · Letter grades</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Export grades as CSV for your gradebook', '↑')}`,
          },
        ],
      },

      // ---- Quizzes ----
      {
        id: 'quizzes', label: '🧠 Quizzes', color: 'var(--rose)',
        desc: 'Build interactive quiz assignments',
        steps: [
          {
            title: 'Add quiz blocks to assignments',
            desc: 'When creating an assignment, toggle on Quiz Mode to add interactive blocks. Mix and match types — text, multiple choice, true/false, short answer, and code.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:6px;">Add Block</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;">
                      ${[['📝','Text/Reading'],['🔘','Multiple Choice'],['✅','True/False'],['✏️','Short Answer'],['💻','Code Prompt'],['📎','File Upload']].map(([i,l])=>`
                        <div style="display:flex;align-items:center;gap:5px;padding:5px 7px;border:1px solid var(--border);border-radius:5px;background:var(--soft);">
                          <span style="font-size:0.75rem;">${i}</span>
                          <span style="font-size:0.58rem;font-weight:700;color:var(--text);">${l}</span>
                        </div>`).join('')}
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Pick any block type to add it', '↑')}`,
          },
          {
            title: 'Configure each block',
            desc: 'Set the question text, point value, and whether the block is required. For multiple choice, add answer options and mark the correct one.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:2px solid var(--teal);border-radius:8px;padding:10px;box-shadow:0 0 0 3px rgba(58,188,177,0.1);">
                    <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                      <span style="font-size:0.55rem;font-weight:800;padding:1px 6px;border-radius:3px;background:#dbeafe;color:#1e40af;">multiple choice</span>
                      <span style="font-size:0.55rem;color:var(--muted);">2 pts · Required</span>
                    </div>
                    <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:4px 7px;font-size:0.6rem;color:var(--text);margin-bottom:5px;">When does a while loop stop running?</div>
                    <div style="display:flex;flex-direction:column;gap:3px;">
                      ${[['After it runs exactly once',false],['When its condition becomes False',true],['When it reaches the end of the file',false]].map(([c,correct])=>`
                        <div style="display:flex;align-items:center;gap:5px;padding:3px 6px;border-radius:4px;border:1px solid ${correct?'var(--green)':'var(--border)'};background:${correct?'rgba(76,175,130,0.08)':'var(--soft)'};">
                          <div style="width:8px;height:8px;border-radius:50%;border:1.5px solid ${correct?'var(--green)':'var(--border)'};background:${correct?'var(--green)':'none'};flex-shrink:0;"></div>
                          <span style="font-size:0.55rem;color:var(--text);flex:1;">${c}</span>
                          ${correct?`<span style="font-size:0.5rem;color:var(--green);font-weight:800;">✓ Correct</span>`:''}
                        </div>`).join('')}
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Mark the correct answer — it auto-grades', '↑')}`,
          },
          {
            title: 'Auto-grading',
            desc: 'Multiple choice and true/false blocks are graded automatically when a student submits. Code and short answer blocks go to your grading queue.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Classrooms')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:6px;">Quiz: While Loops — alex.smith</div>
                    ${[['Multiple Choice','2/2','auto',true],['True/False','1/1','auto',true],['Code Prompt','?/5','manual',false],['Short Answer','?/3','manual',false]].map(([type,score,how,done])=>`
                      <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 6px;border-radius:4px;background:var(--soft);margin-bottom:3px;">
                        <span style="font-size:0.58rem;color:var(--text);">${type}</span>
                        <div style="display:flex;align-items:center;gap:4px;">
                          <span style="font-size:0.58rem;font-weight:800;color:${done?'var(--green)':'var(--muted)'};">${score}</span>
                          <span style="font-size:0.5rem;padding:1px 5px;border-radius:3px;background:${done?'rgba(76,175,130,0.1)':'var(--sky)'};color:${done?'var(--green)':'var(--blue)'};">${how}</span>
                        </div>
                      </div>`).join('')}
                  </div>
                </div>
              </div>
              ${M.annotation('Auto-graded instantly, manual goes to queue', '↑')}`,
          },
        ],
      },

      // ---- Messages ----
      {
        id: 'messages', label: '💬 Messages', color: 'var(--green)',
        desc: 'DM students and create groups',
        steps: [
          {
            title: 'Message students directly',
            desc: 'Click the chat bubble (bottom right) to open your inbox. You can DM any student in your classroom for quick one-on-one check-ins.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;min-height:130px;position:relative;">
                  <div style="position:absolute;bottom:60px;right:8px;width:200px;background:var(--card);border:1px solid var(--border);border-radius:10px;box-shadow:var(--shadow-lg);">
                    <div style="padding:8px 10px;border-bottom:1px solid var(--border);font-size:0.62rem;font-weight:900;color:var(--text);">Messages</div>
                    ${[['AS','alex.smith','I\'m stuck on FizzBuzz',true],['JJ','jordan.jones','Thank you!',false]].map(([i,n,p,u])=>`
                      <div style="display:flex;align-items:center;gap:6px;padding:6px 10px;border-bottom:1px solid var(--border);background:${u?'rgba(91,163,217,0.07)':'none'};">
                        <div style="width:20px;height:20px;border-radius:50%;background:var(--teal);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.45rem;font-weight:800;">${i}</div>
                        <div style="flex:1;min-width:0;">
                          <div style="font-size:0.57rem;font-weight:700;color:var(--text);">${n}</div>
                          <div style="font-size:0.5rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${p}</div>
                        </div>
                        ${u?`<div style="width:5px;height:5px;border-radius:50%;background:var(--blue);"></div>`:''}
                      </div>`).join('')}
                  </div>
                  <div style="position:absolute;bottom:8px;right:8px;width:32px;height:32px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center;color:#fff;">💬</div>
                </div>
              </div>
              ${M.annotation('Click the bubble to open your inbox', '↑')}`,
          },
          {
            title: 'Create a group conversation',
            desc: 'Use the + icon in the inbox to start a group chat. Add multiple students for study groups, project teams, or small-group support.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:6px;">New Group Conversation</div>
                    <div style="font-size:0.52rem;font-weight:800;color:var(--muted);margin-bottom:3px;">GROUP NAME</div>
                    <div style="background:var(--soft);border:1px solid var(--teal);border-radius:4px;padding:4px 8px;font-size:0.6rem;color:var(--text);margin-bottom:6px;">FizzBuzz Study Group</div>
                    <div style="font-size:0.52rem;font-weight:800;color:var(--muted);margin-bottom:3px;">MEMBERS</div>
                    <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:6px;">
                      ${['alex.smith','jordan.jones','taylor.w'].map(n=>`<div style="display:flex;align-items:center;gap:3px;background:var(--sky);border-radius:999px;padding:2px 7px;"><span style="font-size:0.55rem;font-weight:700;color:var(--blue);">${n}</span><span style="font-size:0.55rem;color:var(--muted);">✕</span></div>`).join('')}
                    </div>
                    <div style="background:var(--teal);color:#fff;font-size:0.6rem;font-weight:800;padding:4px;border-radius:5px;text-align:center;">Start Conversation</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Name the group and add members', '↑')}`,
          },
        ],
      },

      // ---- Moderation ----
      {
        id: 'moderation', label: '🚩 Moderation', color: 'var(--rose)',
        desc: 'Keep your classroom safe',
        steps: [
          {
            title: 'The moderation queue',
            desc: 'When students flag a post or it triggers a filter, it appears here. The badge in the sidebar shows how many need attention.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="display:flex;background:var(--soft);min-height:130px;">
                  <div style="width:110px;flex-shrink:0;padding:8px;background:var(--card);border-right:1px solid var(--border);">
                    ${[['🏠','Feed'],['🏫','Classrooms']].map(([i,l])=>`<div style="display:flex;align-items:center;gap:5px;padding:5px 7px;color:var(--muted);"><span style="font-size:0.7rem;">${i}</span><span style="font-size:0.6rem;font-weight:700;">${l}</span></div>`).join('')}
                    <div style="display:flex;align-items:center;gap:5px;padding:5px 7px;border-radius:5px;background:var(--sky);">
                      <span style="font-size:0.7rem;">🚩</span>
                      <span style="font-size:0.6rem;font-weight:700;color:var(--blue);">Moderation</span>
                      <span style="background:var(--rose);color:#fff;font-size:0.5rem;font-weight:800;padding:1px 5px;border-radius:999px;margin-left:auto;">3</span>
                    </div>
                  </div>
                  <div style="flex:1;padding:8px;">
                    <div style="font-size:0.62rem;font-weight:900;color:var(--text);margin-bottom:5px;">Pending Reports (3)</div>
                    ${[['Flagged word in post','alex.smith · 2m ago'],['Reported reply','jordan.jones · 15m ago']].map(([type,meta])=>`
                      <div style="background:var(--card);border:1px solid var(--rose);border-radius:6px;padding:6px 8px;margin-bottom:4px;">
                        <div style="font-size:0.6rem;font-weight:700;color:var(--text);">${type}</div>
                        <div style="font-size:0.53rem;color:var(--muted);">${meta}</div>
                      </div>`).join('')}
                  </div>
                </div>
              </div>
              ${M.annotation('Badge shows pending items needing review', '↑')}`,
          },
          {
            title: 'Review and action reports',
            desc: 'Click a report to see the flagged content in context. You can dismiss it (false alarm), delete the post, or warn the student.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.62rem;font-weight:900;color:var(--text);margin-bottom:2px;">🚩 Flagged Post</div>
                    <div style="font-size:0.55rem;color:var(--muted);margin-bottom:6px;">Reported by 2 students · alex.smith · 5m ago</div>
                    <div style="background:rgba(242,107,107,0.07);border:1px solid var(--rose);border-radius:5px;padding:6px 8px;font-size:0.58rem;color:var(--text);margin-bottom:8px;line-height:1.5;">
                      This is a test post with flagged content…
                    </div>
                    <div style="display:flex;gap:5px;">
                      <div style="flex:1;background:var(--soft);border:1px solid var(--border);border-radius:5px;padding:4px;text-align:center;font-size:0.58rem;font-weight:700;color:var(--muted);">✓ Dismiss</div>
                      <div style="flex:1;background:rgba(245,166,35,0.1);border:1px solid var(--amber);border-radius:5px;padding:4px;text-align:center;font-size:0.58rem;font-weight:700;color:var(--amber);">⚠ Warn</div>
                      <div style="flex:1;background:rgba(242,107,107,0.1);border:1px solid var(--rose);border-radius:5px;padding:4px;text-align:center;font-size:0.58rem;font-weight:700;color:var(--rose);">🗑 Delete</div>
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Dismiss, warn, or delete the content', '↑')}`,
          },
        ],
      },

      // ---- COPPA ----
      {
        id: 'coppa', label: '🔒 COPPA', color: 'var(--amber)',
        desc: 'Approving students under 13',
        steps: [
          {
            title: 'What is COPPA approval?',
            desc: 'Federal law requires parental/teacher consent for students under 13. When one registers, their account is locked until you approve it.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:rgba(245,166,35,0.08);border:2px solid var(--amber);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--amber);margin-bottom:4px;">🔒 COPPA Notice</div>
                    <div style="font-size:0.6rem;color:var(--text);line-height:1.5;margin-bottom:6px;">
                      <strong>casey.brown</strong> registered but is under 13. Their account is restricted until you approve it.
                    </div>
                    <div style="display:flex;gap:6px;">
                      <div style="flex:1;background:var(--green);color:#fff;font-size:0.6rem;font-weight:800;padding:4px;border-radius:5px;text-align:center;">✓ Approve</div>
                      <div style="flex:1;background:var(--rose);color:#fff;font-size:0.6rem;font-weight:800;padding:4px;border-radius:5px;text-align:center;">✕ Deny</div>
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('You\'ll get notified when a student needs approval', '↑')}`,
          },
          {
            title: 'Review pending students',
            desc: 'Go to Pending COPPA in the nav to see all students awaiting approval. You can approve or deny each one. Denied accounts cannot log in.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:6px;">Pending COPPA Approval</div>
                    ${[['casey.brown','Age 11','2015-03-12'],['riley.garcia','Age 12','2014-08-20']].map(([name,age,dob])=>`
                      <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 8px;background:var(--soft);border-radius:5px;margin-bottom:4px;">
                        <div>
                          <div style="font-size:0.6rem;font-weight:700;color:var(--text);">${name}</div>
                          <div style="font-size:0.52rem;color:var(--muted);">${age} · DOB: ${dob}</div>
                        </div>
                        <div style="display:flex;gap:4px;">
                          <div style="background:var(--green);color:#fff;font-size:0.55rem;font-weight:800;padding:3px 8px;border-radius:4px;">Approve</div>
                          <div style="background:var(--rose);color:#fff;font-size:0.55rem;font-weight:800;padding:3px 8px;border-radius:4px;">Deny</div>
                        </div>
                      </div>`).join('')}
                  </div>
                </div>
              </div>
              ${M.annotation('Review and approve students under 13', '↑')}`,
          },
        ],
      },

      // ---- Bug Reports ----
      {
        id: 'bugs', label: '🐛 Bug Reports', color: 'var(--muted)',
        desc: 'Track and resolve issues',
        steps: [
          {
            title: 'Students can report bugs',
            desc: 'The 🐛 Report Bug button (bottom left) lets students and teachers flag issues they find. Severity is set automatically based on keywords.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);position:relative;">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);min-height:100px;padding:8px;">
                  ${M.postCard('Why doesn\'t my loop print?','Python Basics','for i in range(5)...',false)}
                </div>
                <div style="position:absolute;bottom:8px;left:8px;background:var(--card);border:1px solid var(--border);border-radius:999px;padding:4px 10px;font-size:0.6rem;font-weight:800;color:var(--text);box-shadow:0 2px 8px rgba(0,0,0,0.15);">🐛 Report Bug</div>
              </div>
              ${M.annotation('Always visible — bottom left of every page', '↑')}`,
          },
          {
            title: 'View submitted reports',
            desc: 'Find bug reports in your admin panel. Each report shows the title, description, severity, and who submitted it.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:6px;">Bug Reports</div>
                    ${[['Post button not working','Sometimes clicking post does nothing','medium','alex.smith'],['Login error on mobile','Can\'t log in on iPhone','high','jordan.jones']].map(([title,desc,sev,user])=>`
                      <div style="background:var(--soft);border:1px solid var(--border);border-radius:5px;padding:6px 8px;margin-bottom:4px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
                          <div style="font-size:0.6rem;font-weight:700;color:var(--text);">${title}</div>
                          <span style="font-size:0.5rem;font-weight:800;padding:1px 6px;border-radius:999px;background:${sev==='high'?'rgba(242,107,107,0.15)':'rgba(245,166,35,0.15)'};color:${sev==='high'?'var(--rose)':'var(--amber)'};">${sev}</span>
                        </div>
                        <div style="font-size:0.55rem;color:var(--muted);">${desc} · by ${user}</div>
                      </div>`).join('')}
                  </div>
                </div>
              </div>
              ${M.annotation('Review reports in the admin panel', '↑')}`,
          },
        ],
      },

      // ---- Settings ----
      {
        id: 'settings', label: '⚙️ Settings', color: 'var(--blue)',
        desc: 'Profile, password, and preferences',
        steps: [
          {
            title: 'Access your settings',
            desc: 'Click your avatar (top right) and select Settings. From here you can update your profile, change your password, and manage your account.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:8px;">Account Settings</div>
                    ${[['Display Name','Alex Johnson'],['Email','alex@example.com'],['Bio','Python teacher & CS enthusiast']].map(([l,v])=>`
                      <div style="margin-bottom:5px;">
                        <div style="font-size:0.52rem;font-weight:800;color:var(--muted);margin-bottom:2px;">${l.toUpperCase()}</div>
                        <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:0.6rem;color:var(--text);">${v}</div>
                      </div>`).join('')}
                    <div style="background:var(--teal);color:#fff;font-size:0.6rem;font-weight:800;padding:4px;border-radius:5px;text-align:center;margin-top:4px;">Save Changes</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Update your info and save', '↑')}`,
          },
          {
            title: 'Change your password',
            desc: 'In Settings, scroll to the Password section. Enter your current password, then your new one twice. Make it strong — at least 8 characters.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                ${M.topbar('Feed')}
                <div style="background:var(--soft);padding:8px;">
                  <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.65rem;font-weight:900;color:var(--text);margin-bottom:8px;">Change Password</div>
                    ${[['Current Password','••••••••'],['New Password','••••••••••••'],['Confirm Password','••••••••••••']].map(([l,v])=>`
                      <div style="margin-bottom:5px;">
                        <div style="font-size:0.52rem;font-weight:800;color:var(--muted);margin-bottom:2px;">${l.toUpperCase()}</div>
                        <div style="background:var(--soft);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:0.6rem;color:var(--text);">${v}</div>
                      </div>`).join('')}
                    <div style="display:flex;gap:4px;margin-top:4px;">
                      ${['strength: strong'].map(s=>`<div style="flex:1;height:3px;background:var(--green);border-radius:2px;"></div><div style="flex:1;height:3px;background:var(--green);border-radius:2px;"></div><div style="flex:1;height:3px;background:var(--green);border-radius:2px;"></div><div style="font-size:0.5rem;color:var(--green);font-weight:700;margin-left:4px;">${s}</div>`).join('')}
                    </div>
                  </div>
                </div>
              </div>
              ${M.annotation('Enter old then new password and save', '↑')}`,
          },
          {
            title: 'Toggle dark / light mode',
            desc: 'Click the 🌙 / ☀️ button in the top nav to switch themes. SparK remembers your preference across sessions.',
            mockup: () => `
              <div style="border-radius:10px;overflow:hidden;border:1px solid var(--border);">
                <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:var(--card);border-bottom:1px solid var(--border);">
                  <div style="width:18px;height:18px;background:var(--blue);clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.5rem;">⚡</div>
                  <span style="font-weight:900;font-size:0.7rem;color:var(--text);">SparK</span>
                  <div style="flex:1;"></div>
                  <div style="background:var(--sky);border:2px solid var(--teal);border-radius:6px;padding:3px 10px;font-size:0.62rem;font-weight:800;color:var(--teal);display:flex;align-items:center;gap:4px;">🌙 <span>Light</span></div>
                </div>
                <div style="background:var(--soft);padding:12px;display:flex;gap:8px;align-items:flex-start;">
                  <div style="flex:1;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;">
                    <div style="font-size:0.6rem;font-weight:800;color:var(--text);margin-bottom:4px;">Dark Mode Active</div>
                    <div style="font-size:0.55rem;color:var(--muted);">Easy on the eyes for late-night grading sessions.</div>
                  </div>
                </div>
              </div>
              ${M.annotation('Toggle theme anytime from the top nav', '↑')}`,
          },
        ],
      },
    ],
  };

  // --------------------------------------------------
  // State
  // --------------------------------------------------
  let currentRole = null;
  let currentSections = [];
  let activeSectionIdx = null;
  let activeStepIdx = 0;
  let completedSections = new Set();

  function getTourKey() {
    const u = window.SPARK_USER || {};
    if (u.role === 'teacher' || u.role === "admin") return 'teacher';
    if (u.role === 'student') return 'student';
    return null;
  }

  // --------------------------------------------------
  // Styles
  // --------------------------------------------------
  function injectStyles() {
    if (document.getElementById('spark-tour-styles')) return;
    const s = document.createElement('style');
    s.id = 'spark-tour-styles';
    s.textContent = `
      @keyframes stPulse { from{opacity:0.7} to{opacity:1} }
      @keyframes stFadeIn { from{opacity:0} to{opacity:1} }
      @keyframes stSlideUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
      @keyframes stSlideInR { from{opacity:0;transform:translateX(32px)} to{opacity:1;transform:translateX(0)} }
      @keyframes stSlideInL { from{opacity:0;transform:translateX(-32px)} to{opacity:1;transform:translateX(0)} }
      @keyframes stSpin { to{transform:rotate(360deg)} }

      #spark-tour {
        position:fixed;inset:0;z-index:9998;
        display:flex;flex-direction:column;
        background:var(--soft);font-family:var(--font);
        animation:stFadeIn 0.18s ease;overflow:hidden;
      }

      /* topbar */
      #st-top {
        display:flex;align-items:center;gap:12px;
        padding:12px 24px;background:var(--card);
        border-bottom:1px solid var(--border);flex-shrink:0;
      }
      #st-logo {
        display:flex;align-items:center;gap:7px;
        font-size:0.95rem;font-weight:900;color:var(--text);letter-spacing:-0.3px;
      }
      #st-hex {
        width:24px;height:24px;background:var(--blue);
        clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
        display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.7rem;
      }
      #st-prog-wrap { flex:1;height:3px;background:var(--border);border-radius:2px;overflow:hidden; }
      #st-prog { height:100%;background:var(--teal);border-radius:2px;transition:width 0.3s ease; }
      #st-counter { font-size:0.72rem;font-weight:700;color:var(--muted);white-space:nowrap; }
      #st-exit {
        background:none;border:1px solid var(--border);border-radius:var(--radius-sm);
        color:var(--muted);font-size:0.78rem;font-weight:600;padding:5px 12px;
        cursor:pointer;font-family:var(--font);transition:all 0.15s;
      }
      #st-exit:hover { border-color:var(--rose);color:var(--rose); }

      /* hub */
      #st-hub {
        flex:1;overflow-y:auto;padding:2rem;
        display:flex;flex-direction:column;align-items:center;
        animation:stFadeIn 0.18s ease;
      }
      #st-hub-title {
        font-size:1.6rem;font-weight:900;color:var(--text);
        letter-spacing:-0.4px;margin-bottom:0.5rem;text-align:center;
      }
      #st-hub-sub {
        font-size:0.95rem;color:var(--muted);margin-bottom:2rem;text-align:center;max-width:500px;
      }
      #st-hub-grid {
        display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
        gap:12px;width:100%;max-width:740px;
      }
      .st-hub-card {
        background:var(--card);border:1px solid var(--border);
        border-radius:var(--radius);padding:1.25rem;cursor:pointer;
        transition:all 0.15s;position:relative;overflow:hidden;
        animation:stSlideUp 0.2s ease both;
      }
      .st-hub-card:hover {
        border-color:var(--teal);box-shadow:0 4px 20px rgba(58,188,177,0.15);
        transform:translateY(-2px);
      }
      .st-hub-card.done { border-color:var(--blue); }
      .st-hub-card.done::after {
        content:'✓';position:absolute;top:8px;right:10px;
        font-size:0.7rem;font-weight:800;color:var(--blue);
      }
      .st-hub-icon { font-size:2.8rem;margin-bottom:0.5rem;display:block; }
      .st-hub-label { font-size:1.1rem;font-weight:800;color:var(--text);margin-bottom:0.25rem; }
      .st-hub-desc { font-size:0.9rem;color:var(--muted);line-height:1.45; }
      .st-hub-badge {
        display:inline-block;margin-top:0.5rem;font-size:0.65rem;
        font-weight:700;padding:2px 8px;border-radius:999px;
        background:var(--sky);color:var(--blue);
      }

      /* section view */
      #st-section {
        flex:1;display:flex;flex-direction:column;overflow:hidden;
        animation:stFadeIn 0.15s ease;
      }
      #st-sec-header {
        display:flex;align-items:center;gap:10px;
        padding:10px 24px;background:var(--card);
        border-bottom:1px solid var(--border);flex-shrink:0;
      }
      #st-back-hub {
        background:none;border:1px solid var(--border);border-radius:var(--radius-sm);
        color:var(--muted);font-size:0.78rem;font-weight:600;padding:5px 12px;
        cursor:pointer;font-family:var(--font);transition:all 0.15s;
      }
      #st-back-hub:hover { border-color:var(--blue);color:var(--blue); }
      #st-sec-label {
        font-size:0.88rem;font-weight:800;color:var(--text);flex:1;
      }
      #st-sec-dots { display:flex;gap:5px; }
      .st-sec-dot {
        width:7px;height:7px;border-radius:50%;
        background:var(--border);transition:all 0.2s;cursor:pointer;
      }
      .st-sec-dot.active { background:var(--teal);transform:scale(1.35); }
      .st-sec-dot.done { background:var(--blue); }

      /* step content */
      #st-step-area {
        flex:1;display:flex;gap:2rem;padding:1.5rem 2rem;
        overflow:hidden;align-items:stretch;
      }
      #st-step-left {
        flex:1;display:flex;flex-direction:column;justify-content:center;
        max-width:320px;flex-shrink:0;
      }
      .st-step-sec-tag {
        font-size:0.68rem;font-weight:800;letter-spacing:1.2px;
        text-transform:uppercase;color:var(--teal);margin-bottom:0.5rem;
      }
      .st-step-title {
        font-size:1.9rem;font-weight:900;color:var(--text);
        letter-spacing:-0.4px;line-height:1.2;margin-bottom:0.75rem;
      }
      .st-step-desc {
        font-size:1.05rem;color:var(--muted);line-height:1.7;margin-bottom:1.25rem;
      }
      .st-cta {
        display:inline-flex;align-items:center;gap:7px;
        background:var(--teal);color:#fff;border:none;
        border-radius:var(--radius-sm);padding:10px 22px;
        font-family:var(--font);font-size:0.9rem;font-weight:700;
        cursor:pointer;transition:opacity 0.15s,transform 0.15s;
        text-decoration:none;
      }
      .st-cta:hover { opacity:0.88;transform:scale(1.02);color:#fff; }

      #st-step-right {
        flex:1;display:flex;align-items:center;justify-content:center;
        min-width:0;
        font-size: 1.35rem;
      }
      #st-mockup-wrap {
        width:100%;max-width:520px;
        transform:scale(1.25);
        transform-origin: top center;
        animation:stSlideInR 0.15s ease;
      }
      #st-mockup-wrap.from-left { animation:stSlideInL 0.15s ease; }

      /* section footer */
      #st-sec-footer {
        display:flex;align-items:center;justify-content:space-between;
        padding:12px 24px;border-top:1px solid var(--border);
        background:var(--card);flex-shrink:0;
      }
      .st-nav-btn {
        background:none;border:1px solid var(--border);border-radius:var(--radius-sm);
        color:var(--muted);font-family:var(--font);font-size:0.85rem;
        font-weight:600;padding:7px 18px;cursor:pointer;transition:all 0.15s;
      }
      .st-nav-btn:hover { border-color:var(--blue);color:var(--blue); }
      .st-nav-btn:disabled { opacity:0.3;pointer-events:none; }

      /* finish screen */
      #st-finish {
        flex:1;display:flex;flex-direction:column;align-items:center;
        justify-content:center;padding:2rem;text-align:center;
        animation:stFadeIn 0.18s ease;
      }
      #st-finish-icon { font-size:3.5rem;margin-bottom:1rem; }
      #st-finish-title { font-size:1.6rem;font-weight:900;color:var(--text);margin-bottom:0.5rem; }
      #st-finish-sub { font-size:0.95rem;color:var(--muted);margin-bottom:2rem;max-width:420px; }
      .st-finish-actions { display:flex;gap:10px;flex-wrap:wrap;justify-content:center; }

      /* loading */
      #st-loading {
        position:absolute;inset:0;background:var(--soft);
        display:flex;flex-direction:column;align-items:center;
        justify-content:center;gap:0.75rem;z-index:2;
        opacity:0;pointer-events:none;transition:opacity 0.15s;
      }
      #st-loading.show { opacity:1;pointer-events:all; }
      .st-spinner {
        width:32px;height:32px;border:3px solid var(--border);
        border-top-color:var(--teal);border-radius:50%;
        animation:stSpin 0.6s linear infinite;
      }
      #st-load-label { font-size:0.82rem;font-weight:700;color:var(--muted); }

      /* replay pill */
      #spark-tour-btn {
        position:fixed;bottom:1rem;left:1.25rem;z-index:9000;
        background:var(--card);border:1px solid var(--border);
        border-radius:999px;padding:6px 14px;
        font-size:0.78rem;font-weight:800;color:var(--text);
        box-shadow:0 2px 8px rgba(0,0,0,0.15);cursor:pointer;
        font-family:var(--font);transition:all 0.15s;
        display:flex;align-items:center;gap:6px;
      }
      #spark-tour-btn:hover { border-color:var(--teal);color:var(--teal); }

      #spark-tour-menu {
        position:fixed;bottom:3.5rem;left:1.25rem;z-index:9001;
        background:var(--card);border:1px solid var(--border);
        border-radius:var(--radius);box-shadow:var(--shadow-lg);
        min-width:220px;overflow:hidden;
        transform:translateY(8px) scale(0.97);opacity:0;
        pointer-events:none;
        transition:all 0.15s cubic-bezier(0.34,1.56,0.64,1);
      }
      #spark-tour-menu.open { transform:translateY(0) scale(1);opacity:1;pointer-events:all; }
      .st-menu-hdr {
        padding:9px 14px 5px;font-size:0.65rem;font-weight:800;
        letter-spacing:1px;text-transform:uppercase;color:var(--muted);
        border-bottom:1px solid var(--border);
      }
      .st-menu-item {
        display:flex;align-items:center;gap:9px;padding:9px 14px;
        font-size:0.82rem;font-weight:600;color:var(--text);
        cursor:pointer;transition:background 0.1s;
        border:none;background:none;width:100%;text-align:left;
        font-family:var(--font);
      }
      .st-menu-item:hover { background:var(--sky);color:var(--blue); }
      .st-menu-dot { width:8px;height:8px;border-radius:50%;flex-shrink:0; }
      .st-menu-done { font-size:0.6rem;color:var(--blue);margin-left:auto; }

      @media(max-width:700px){
        #st-step-area { flex-direction:column;padding:1rem;gap:1rem; }
        #st-step-left { max-width:100%; }
        .st-step-title { font-size:1.2rem; }
        #st-top,#st-sec-footer,#st-sec-header { padding:10px 14px; }
        #st-hub { padding:1rem; }
        #st-hub-grid { grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); }
      }
    `;
    document.head.appendChild(s);
  }

  // --------------------------------------------------
  // Build shell
  // --------------------------------------------------
  function buildShell() {
    if (document.getElementById('spark-tour')) return;
    const el = document.createElement('div');
    el.id = 'spark-tour';
    el.innerHTML = `
      <div id="st-top">
        <div id="st-logo"><div id="st-hex">⚡</div>SparK Tour</div>
        <div id="st-prog-wrap"><div id="st-prog" style="width:0%"></div></div>
        <span id="st-counter"></span>
        <button id="st-exit">✕ Exit</button>
      </div>
      <div id="st-loading"><div class="st-spinner"></div><div id="st-load-label">Loading…</div></div>
      <div id="st-hub" style="display:none;"></div>
      <div id="st-section" style="display:none;">
        <div id="st-sec-header">
          <button id="st-back-hub">← Hub</button>
          <span id="st-sec-label"></span>
          <div id="st-sec-dots"></div>
        </div>
        <div id="st-step-area">
          <div id="st-step-left"></div>
          <div id="st-step-right"><div id="st-mockup-wrap"></div></div>
        </div>
        <div id="st-sec-footer">
          <button class="st-nav-btn" id="st-prev">← Back</button>
          <div></div>
          <button class="st-nav-btn" id="st-next">Next →</button>
        </div>
      </div>
      <div id="st-finish" style="display:none;"></div>
    `;
    document.body.appendChild(el);
    document.getElementById('st-exit').addEventListener('click', closeTour);
    document.getElementById('st-back-hub').addEventListener('click', showHub);
    document.getElementById('st-prev').addEventListener('click', () => stepNav(-1));
    document.getElementById('st-next').addEventListener('click', () => stepNav(1));
    document.addEventListener('keydown', onKey);
  }

  // --------------------------------------------------
  // Show hub
  // --------------------------------------------------
  function showHub() {
    const totalSteps = currentSections.reduce((a, s) => a + s.steps.length, 0);
    const doneSteps = [...completedSections].reduce((a, si) => a + currentSections[si].steps.length, 0);
    const pct = totalSteps ? Math.round(doneSteps / totalSteps * 100) : 0;

    document.getElementById('st-prog').style.width = pct + '%';
    document.getElementById('st-counter').textContent = `${completedSections.size}/${currentSections.length} sections`;

    hide('st-section'); hide('st-finish'); hide('st-loading');
    show('st-hub');

    const hub = document.getElementById('st-hub');
    hub.innerHTML = `
      <h1 id="st-hub-title">${currentRole === 'teacher' ? '👩‍🏫' : '⚡'} Where do you want to start?</h1>
      <p id="st-hub-sub">Pick any section. You can come back to others anytime using the ❓ button.</p>
      <div id="st-hub-grid"></div>
    `;

    const grid = document.getElementById('st-hub-grid');
    currentSections.forEach((sec, si) => {
      const card = document.createElement('div');
      card.className = 'st-hub-card' + (completedSections.has(si) ? ' done' : '');
      card.style.animationDelay = (si * 0.04) + 's';
      card.innerHTML = `
        <span class="st-hub-icon">${sec.label.split(' ')[0]}</span>
        <div class="st-hub-label">${sec.label.replace(/^\S+\s/,'')}</div>
        <div class="st-hub-desc">${sec.desc}</div>
        <span class="st-hub-badge">${sec.steps.length} step${sec.steps.length > 1 ? 's' : ''}</span>
      `;
      card.addEventListener('click', () => openSection(si));
      grid.appendChild(card);
    });

    activeSectionIdx = null;
  }

  // --------------------------------------------------
  // Open section
  // --------------------------------------------------
  function openSection(si, withLoad) {
    activeSectionIdx = si;
    activeStepIdx = 0;

    if (withLoad) {
      show('st-loading');
      document.getElementById('st-load-label').textContent = `Loading ${currentSections[si].label}…`;
      hide('st-hub'); hide('st-section'); hide('st-finish');
      setTimeout(() => { hide('st-loading'); renderSection(); }, 650);
    } else {
      hide('st-hub'); hide('st-finish'); hide('st-loading');
      renderSection();
    }
  }

  function renderSection(dir) {
    const sec = currentSections[activeSectionIdx];
    const step = sec.steps[activeStepIdx];
    const totalSteps = currentSections.reduce((a, s) => a + s.steps.length, 0);
    const doneSteps = [...completedSections].reduce((a, si) => a + currentSections[si].steps.length, 0);
    const pct = totalSteps ? Math.round((doneSteps + activeStepIdx + 1) / totalSteps * 100) : 0;

    document.getElementById('st-prog').style.width = pct + '%';
    document.getElementById('st-counter').textContent = `Step ${activeStepIdx + 1}/${sec.steps.length}`;
    document.getElementById('st-sec-label').textContent = sec.label;

    // Dots
    const dotsEl = document.getElementById('st-sec-dots');
    dotsEl.innerHTML = '';
    sec.steps.forEach((_, i) => {
      const d = document.createElement('div');
      d.className = 'st-sec-dot' + (i === activeStepIdx ? ' active' : i < activeStepIdx ? ' done' : '');
      d.addEventListener('click', () => { activeStepIdx = i; renderSection(0); });
      dotsEl.appendChild(d);
    });

    // Nav buttons
    document.getElementById('st-prev').disabled = activeStepIdx === 0;
    const isLast = activeStepIdx === sec.steps.length - 1;
    document.getElementById('st-next').textContent = isLast ? 'Finish section ✓' : 'Next →';

    // Left panel
    let ctaHtml = '';
    if (step.cta) {
      const { label, action, url } = step.cta;
      if (action === 'goto') {
        ctaHtml = `<a href="${url}" class="st-cta" target="_self">${label}</a>`;
      } else {
        ctaHtml = `<button class="st-cta" onclick="window.SparkTour._ctaNext()">${label}</button>`;
      }
    }

    const left = document.getElementById('st-step-left');
    left.innerHTML = `
      <div class="st-step-sec-tag">${sec.label}</div>
      <div class="st-step-title">${step.title}</div>
      <p class="st-step-desc">${step.desc}</p>
      ${ctaHtml}
    `;
    left.style.animation = 'none';
    void left.offsetWidth;
    left.style.animation = `stSlideInL 0.15s ease`;

    // Mockup
    const wrap = document.getElementById('st-mockup-wrap');
    wrap.className = dir < 0 ? 'from-left' : '';
    wrap.innerHTML = step.mockup ? step.mockup() : '';
    void wrap.offsetWidth;
    wrap.style.animation = 'none';
    void wrap.offsetWidth;
    wrap.style.animation = dir < 0 ? 'stSlideInL 0.15s ease' : 'stSlideInR 0.15s ease';

    show('st-section');
  }

  function stepNav(dir) {
    const sec = currentSections[activeSectionIdx];
    const next = activeStepIdx + dir;
    if (next < 0) return;
    if (next >= sec.steps.length) {
      finishSection();
      return;
    }
    activeStepIdx = next;
    renderSection(dir);
  }

  function finishSection() {
    completedSections.add(activeSectionIdx);
    const nextSi = activeSectionIdx + 1;
    const allDone = completedSections.size >= currentSections.length;

    if (allDone) {
      showFinish();
      return;
    }

    // Offer next section or hub
    hide('st-section');
    const sec = currentSections[activeSectionIdx];
    const nextSec = currentSections[nextSi];

    const finish = document.getElementById('st-finish');
    finish.innerHTML = `
      <div id="st-finish-icon">✅</div>
      <div id="st-finish-title">${sec.label.replace(/^\S+\s/,'')} complete!</div>
      <p id="st-finish-sub">Great job! What would you like to do next?</p>
      <div class="st-finish-actions">
        ${nextSec ? `<button class="st-cta" id="st-goto-next">Next: ${nextSec.label} →</button>` : ''}
        <button class="st-nav-btn" id="st-goto-hub">← Back to hub</button>
      </div>
    `;
    show('st-finish');

    document.getElementById('st-goto-hub').addEventListener('click', showHub);
    const nextBtn = document.getElementById('st-goto-next');
    if (nextBtn) nextBtn.addEventListener('click', () => openSection(nextSi));
  }

  function showFinish() {
    hide('st-section'); hide('st-hub');
    const finish = document.getElementById('st-finish');
    finish.innerHTML = `
      <div id="st-finish-icon">🎉</div>
      <div id="st-finish-title">Tour complete!</div>
      <p id="st-finish-sub">You've seen everything SparK has to offer. Use the ❓ button anytime to jump back to any section.</p>
      <div class="st-finish-actions">
        <button class="st-cta" onclick="window.SparkTour.close()">Start using SparK →</button>
        <button class="st-nav-btn" id="st-restart-hub">Review a section</button>
      </div>
    `;
    show('st-finish');
    document.getElementById('st-restart-hub').addEventListener('click', () => { completedSections.clear(); showHub(); });

    document.getElementById('st-prog').style.width = '100%';
    document.getElementById('st-counter').textContent = 'All done!';
  }

  // --------------------------------------------------
  // Helpers
  // --------------------------------------------------
  function show(id) { const e = document.getElementById(id); if(e) e.style.display = ''; }
  function hide(id) { const e = document.getElementById(id); if(e) e.style.display = 'none'; }

  function onKey(e) {
    if (!document.getElementById('spark-tour')) { document.removeEventListener('keydown', onKey); return; }
    if (document.getElementById('st-section').style.display === 'none') return;
    if (e.key === 'ArrowRight') stepNav(1);
    if (e.key === 'ArrowLeft') stepNav(-1);
    if (e.key === 'Escape') closeTour();
  }

  // --------------------------------------------------
  // Open / close
  // --------------------------------------------------
  function openTour(key, jumpSi) {
    currentRole = key || getTourKey();
    if (!currentRole || !SECTIONS[currentRole]) return;
    currentSections = SECTIONS[currentRole];
    completedSections = new Set();
    injectStyles();
    buildShell();
    hide('st-hub'); hide('st-section'); hide('st-finish');
    show('st-loading');
    setTimeout(() => {
      hide('st-loading');
      if (jumpSi !== undefined) openSection(jumpSi);
      else showHub();
    }, 400);
  }

  function closeTour() {
    const el = document.getElementById('spark-tour');
    if (!el) return;
    el.style.opacity = '0'; el.style.transition = 'opacity 0.18s';
    document.removeEventListener('keydown', onKey);
    setTimeout(() => el.remove(), 200);
    try { localStorage.setItem('spark_tour_seen_' + getTourKey(), '1'); } catch(e) {}
    const csrf = document.querySelector('meta[name="csrf-token"]');
    fetch('/tour/complete', { method:'POST', headers:{'X-CSRFToken': csrf ? csrf.content : ''} }).catch(()=>{});
  }

  // --------------------------------------------------
  // Replay button + menu
  // --------------------------------------------------
  function buildReplayButton() {
    if (document.getElementById('spark-tour-btn')) return;
    injectStyles();
    const btn = document.createElement('button');
    btn.id = 'spark-tour-btn';
    btn.innerHTML = '❓ Tour';
    btn.addEventListener('click', toggleMenu);
    document.body.appendChild(btn);
    const menu = document.createElement('div');
    menu.id = 'spark-tour-menu';
    document.body.appendChild(menu);
    document.addEventListener('click', e => {
      if (!btn.contains(e.target) && !menu.contains(e.target)) closeMenu();
    });
  }

  function buildMenu() {
    const key = getTourKey();
    if (!key || !SECTIONS[key]) return;
    const menu = document.getElementById('spark-tour-menu');
    if (!menu) return;
    menu.innerHTML = `<div class="st-menu-hdr">Jump to section</div>`;
    SECTIONS[key].forEach((sec, si) => {
      const item = document.createElement('button');
      item.className = 'st-menu-item';
      const done = completedSections && completedSections.has(si);
      item.innerHTML = `
        <div class="st-menu-dot" style="background:${sec.color}"></div>
        ${sec.label}
        ${done ? '<span class="st-menu-done">✓</span>' : ''}
      `;
      item.addEventListener('click', () => {
        closeMenu();
        if (document.getElementById('spark-tour')) {
          if (activeSectionIdx !== null) {
            show('st-loading');
            document.getElementById('st-load-label').textContent = `Loading ${sec.label}…`;
            hide('st-hub'); hide('st-section'); hide('st-finish');
            setTimeout(() => { hide('st-loading'); openSection(si); }, 650);
          } else {
            openSection(si, true);
          }
        } else {
          openTour(key, si);
        }
      });
      menu.appendChild(item);
    });
  }

  function toggleMenu() {
    const menu = document.getElementById('spark-tour-menu');
    if (!menu) return;
    const open = menu.classList.contains('open');
    if (!open) buildMenu();
    menu.classList.toggle('open', !open);
  }
  function closeMenu() {
    const m = document.getElementById('spark-tour-menu');
    if (m) m.classList.remove('open');
  }

  // --------------------------------------------------
  // Auto-launch
  // --------------------------------------------------
  function maybeAutoLaunch() {
    buildReplayButton();
    const u = window.SPARK_USER || {};
    const key = getTourKey();
    if (!key) return;
    try { if (localStorage.getItem('spark_tour_seen_' + key)) return; } catch(e) {}
    const tourSeen = document.body.dataset.tourSeen === 'true';
    if (!tourSeen) setTimeout(() => openTour(key), 600);
  }

  // --------------------------------------------------
  // Public API
  // --------------------------------------------------
  window.SparkTour = {
    start: (key) => openTour(key),
    close: closeTour,
    getTourKey,
    _ctaNext: () => stepNav(1),
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', maybeAutoLaunch);
  } else {
    maybeAutoLaunch();
  }


  function getTourKey() {
  const body = document.body;
  const role = body.dataset.role;
  if (role === 'teacher' || role === 'admin') return 'teacher';
  if (role === 'student') return 'student';
  return null;
}
})();