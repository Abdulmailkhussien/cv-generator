/* ============================================================
   CV generator - client
   ============================================================
   Lifted out of the page. It was forty-five kilobytes inlined in
   index.html, which meant the browser re-downloaded every line of
   behaviour on each visit and nothing was cacheable.

   Four ideas run through the whole file:

   1. collectData() and fillForm() are inverses, and they are the only
      two functions that know the shape of the form. The draft, the
      preview, the job match and all three import doors go through them.

   2. Every import door - voice, document, pasted text - ends in
      fillForm(). The browser never learns which door was used.

   3. The preview is the real renderer on the server, not an HTML
      imitation. An imitation drifts, and "the download does not match
      what I saw" is a worse complaint than having no preview.

   4. Nothing is written into a CV that its owner did not say. That rule
      lives mostly in the prompts on the server, and here it shows up as
      the one place with no "apply" button: genuinely missing skills.
   ============================================================ */

const TEMPLATE_DATA = {
    classic: { ar: 'كلاسيكي', en: 'Classic', color: '#000000' },
    modern: { ar: 'عصري', en: 'Modern', color: '#2563eb' },
    minimal: { ar: 'بسيط', en: 'Minimal', color: '#059669' },
    executive: { ar: 'تنفيذي', en: 'Executive', color: '#7c3aed' },
    compact: { ar: 'مضغوط', en: 'Compact', color: '#ea580c' },
    professional: { ar: 'احترافي', en: 'Professional', color: '#1e3a5f' },
    creative: { ar: 'إبداعي', en: 'Creative', color: '#0d9488' },
    diamond: { ar: 'الماسي', en: 'Diamond', color: '#d4a843' },
    tech: { ar: 'تقني', en: 'Tech', color: '#06b6d4' },
};

const LABELS = {
    ar: {
        title: 'المسمى الوظيفي', company: 'الشركة', start: 'من', end: 'إلى', description: 'ماذا أنجزت',
        degree: 'الدرجة العلمية', school: 'الجامعة / المدرسة', field: 'التخصص', year: 'السنة',
        certName: 'اسم الشهادة', certIssuer: 'الجهة المانحة',
        langName: 'اللغة', langLevel: 'المستوى',
        projName: 'اسم المشروع', projDesc: 'الوصف', projLink: 'الرابط (اختياري)',
        phTitle: 'مطوّر أول', phCompany: 'شركة التقنية', phStart: '2020', phEnd: 'الآن',
        phDesc: 'سطر إلى ثلاثة، كل سطر يبدأ بفعل: قُدت... طوّرت... خفّضت...',
        phDegree: 'بكالوريوس', phSchool: 'الجامعة الأردنية', phField: 'علوم الحاسب',
        phCertName: 'شهادة AWS', phCertIssuer: 'أمازون', phYear: '2023',
        phLangName: 'العربية', phLangLevel: 'اللغة الأم',
        phProjName: 'منصة تجارة إلكترونية', phProjDesc: 'بناء منصة متكاملة...', phProjLink: 'https://github.com/...',
        navBasics: 'الأساسية', navExp: 'الخبرات', navEdu: 'التعليم', navSkills: 'المهارات',
        navCerts: 'الشهادات', navLangs: 'اللغات', navProj: 'المشاريع',
    },
    en: {
        title: 'Job title', company: 'Company', start: 'From', end: 'To', description: 'What you achieved',
        degree: 'Degree', school: 'School / university', field: 'Field of study', year: 'Year',
        certName: 'Certification', certIssuer: 'Issued by',
        langName: 'Language', langLevel: 'Level',
        projName: 'Project', projDesc: 'Description', projLink: 'Link (optional)',
        phTitle: 'Senior Developer', phCompany: 'Google Inc.', phStart: '2020', phEnd: 'Present',
        phDesc: 'One to three lines, each starting with a verb: Led... Built... Cut...',
        phDegree: 'BSc Computer Science', phSchool: 'MIT', phField: 'Computer Science',
        phCertName: 'AWS Certified', phCertIssuer: 'Amazon', phYear: '2023',
        phLangName: 'English', phLangLevel: 'Native',
        phProjName: 'E-commerce platform', phProjDesc: 'Built a full-stack...', phProjLink: 'https://github.com/...',
        navBasics: 'Basics', navExp: 'Experience', navEdu: 'Education', navSkills: 'Skills',
        navCerts: 'Certifications', navLangs: 'Languages', navProj: 'Projects',
    }
};

const SHEETS = [
    { key: 'basics', icon: '👤', label: 'navBasics' },
    { key: 'exp', icon: '💼', label: 'navExp' },
    { key: 'edu', icon: '🎓', label: 'navEdu' },
    { key: 'skills', icon: '⚡', label: 'navSkills' },
    { key: 'certs', icon: '🏆', label: 'navCerts' },
    { key: 'langs', icon: '🌍', label: 'navLangs' },
    { key: 'proj', icon: '🚀', label: 'navProj' },
];

let currentLang = 'ar';
let currentStep = 1;
let currentSheet = 'basics';

/* ============ SMALL HELPERS ============ */

const $ = id => document.getElementById(id);

function esc(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

let toastTimer = null;
function toast(msg) {
    const el = $('toast');
    el.textContent = msg;
    el.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('on'), 3800);
}

function busy(on, text) {
    if (text) $('overlayText').textContent = text;
    $('overlay').classList.toggle('on', on);
}

const T = (ar, en) => (currentLang === 'ar' ? ar : en);

/* ============ LANGUAGE & THEME ============ */

function setLang(lang) {
    currentLang = lang;
    $('language').value = lang;

    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.body.classList.toggle('ltr', lang === 'en');

    $('segAr').classList.toggle('on', lang === 'ar');
    $('segEn').classList.toggle('on', lang === 'en');

    document.querySelectorAll('[data-' + lang + ']').forEach(el => {
        el.textContent = el.getAttribute('data-' + lang);
    });
    document.querySelectorAll('[data-ph-' + lang + ']').forEach(el => {
        el.placeholder = el.getAttribute('data-ph-' + lang);
    });

    buildNav();
    buildTemplates();
    relabelItems();

    if (currentStep === 3) schedulePreview();
}

function toggleTheme() {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    const next = dark ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', next);
    $('themeBtn').textContent = next === 'dark' ? '☀️' : '🌙';

    try { localStorage.setItem('cv_theme', next); } catch (e) { }
}

/* ============ STEPS ============ */

function goStep(step) {
    currentStep = step;

    document.querySelectorAll('.step').forEach(s => s.classList.remove('on'));
    $(step === 'tailor' ? 'stepTailor' : 'step' + step).classList.add('on');

    [1, 2, 3].forEach(n => {
        const rail = $('rail' + n);
        rail.classList.toggle('on', n === step);
        rail.classList.toggle('done', n < (step === 'tailor' ? 4 : step));
    });

    if (step === 'tailor') showTailorState();

    window.scrollTo({ top: 0, behavior: 'smooth' });

    // The preview costs a render on the server, so it only runs on the
    // step that shows it.
    if (step === 3) schedulePreview();
}

/* ============ STEP 2 NAVIGATION ============ */

function buildNav() {
    const lb = LABELS[currentLang];

    $('navList').innerHTML = SHEETS.map(s =>
        `<button onclick="openSheet('${s.key}')" data-nav="${s.key}"
                 class="${s.key === currentSheet ? 'on' : ''}">
            <span class="tick">✓</span>
            <span>${s.icon} ${lb[s.label]}</span>
         </button>`).join('');

    markProgress();
}

function openSheet(key) {
    currentSheet = key;

    document.querySelectorAll('.sheet').forEach(s =>
        s.classList.toggle('on', s.dataset.sheet === key));
    document.querySelectorAll('[data-nav]').forEach(b =>
        b.classList.toggle('on', b.dataset.nav === key));
}

// A tick per finished section. Twenty-seven empty boxes give no sense of
// how much is left; seven sections with four ticks do.
function markProgress() {
    const d = collectData();

    const filled = {
        basics: !!(d.full_name && d.job_title),
        exp: d.experiences.some(x => x.title || x.company),
        edu: d.education.some(x => x.degree || x.school),
        skills: !!d.skills.trim(),
        certs: d.certifications.some(x => x.name),
        langs: d.languages.some(x => x.language),
        proj: d.projects.some(x => x.name),
    };

    document.querySelectorAll('[data-nav]').forEach(b => {
        b.classList.toggle('filled', !!filled[b.dataset.nav]);
    });
}

/* ============ REPEATABLE ITEMS ============ */

function itemShell(inner) {
    return `<div class="item">
        <button class="kill" onclick="this.parentElement.remove(); afterEdit()"
                aria-label="${T('حذف', 'Remove')}">×</button>
        ${inner}</div>`;
}

function fieldHTML(cls, labelKey, phKey, tag) {
    const lb = LABELS[currentLang];
    const control = tag === 'textarea'
        ? `<textarea class="${cls}" rows="3" data-lbl="${phKey}" placeholder="${esc(lb[phKey])}"></textarea>`
        : `<input class="${cls}" data-lbl="${phKey}" placeholder="${esc(lb[phKey])}">`;

    return `<div class="field"><label data-lbl="${labelKey}">${esc(lb[labelKey])}</label>${control}</div>`;
}

function addExp() {
    $('experiences').insertAdjacentHTML('beforeend', itemShell(
        `<div class="row2">${fieldHTML('exp-title', 'title', 'phTitle')}${fieldHTML('exp-company', 'company', 'phCompany')}</div>
         <div class="row2">${fieldHTML('exp-start', 'start', 'phStart')}${fieldHTML('exp-end', 'end', 'phEnd')}</div>
         ${fieldHTML('exp-desc', 'description', 'phDesc', 'textarea')}`));
}

function addEdu() {
    $('education').insertAdjacentHTML('beforeend', itemShell(
        `<div class="row2">${fieldHTML('edu-degree', 'degree', 'phDegree')}${fieldHTML('edu-field', 'field', 'phField')}</div>
         <div class="row2">${fieldHTML('edu-school', 'school', 'phSchool')}${fieldHTML('edu-year', 'year', 'phYear')}</div>`));
}

function addCert() {
    $('certifications').insertAdjacentHTML('beforeend', itemShell(
        `<div class="row2">${fieldHTML('cert-name', 'certName', 'phCertName')}${fieldHTML('cert-issuer', 'certIssuer', 'phCertIssuer')}</div>
         ${fieldHTML('cert-year', 'year', 'phYear')}`));
}

function addLang() {
    $('languages').insertAdjacentHTML('beforeend', itemShell(
        `<div class="row2">${fieldHTML('lng-name', 'langName', 'phLangName')}${fieldHTML('lng-level', 'langLevel', 'phLangLevel')}</div>`));
}

function addProject() {
    $('projects').insertAdjacentHTML('beforeend', itemShell(
        `${fieldHTML('proj-name', 'projName', 'phProjName')}
         ${fieldHTML('proj-desc', 'projDesc', 'phProjDesc', 'textarea')}
         ${fieldHTML('proj-link', 'projLink', 'phProjLink')}`));
}

// Items are built from the label table at the time they are added, so a
// language switch has to walk the ones already on screen.
function relabelItems() {
    const lb = LABELS[currentLang];

    document.querySelectorAll('[data-lbl]').forEach(el => {
        const key = el.dataset.lbl;
        if (!lb[key]) return;

        if (el.tagName === 'LABEL') el.textContent = lb[key];
        else el.placeholder = lb[key];
    });
}

/* ============ THE FORM, BOTH WAYS ============ */

function readItems(containerId, map) {
    return Array.from(document.querySelectorAll('#' + containerId + ' .item')).map(card => {
        const out = {};
        for (const key in map) {
            const el = card.querySelector('.' + map[key]);
            out[key] = el ? el.value : '';
        }
        return out;
    });
}

function collectData() {
    return {
        language: $('language').value,
        template: $('template').value,
        full_name: $('fullName').value,
        job_title: $('jobTitle').value,
        email: $('email').value,
        phone: $('phone').value,
        location: $('location').value,
        linkedin: $('linkedin').value,
        summary: $('summary').value,
        skills: $('skills').value,
        experiences: readItems('experiences', {
            title: 'exp-title', company: 'exp-company',
            start_date: 'exp-start', end_date: 'exp-end', description: 'exp-desc'
        }),
        education: readItems('education', {
            degree: 'edu-degree', school: 'edu-school', field: 'edu-field', year: 'edu-year'
        }),
        certifications: readItems('certifications', {
            name: 'cert-name', issuer: 'cert-issuer', year: 'cert-year'
        }),
        languages: readItems('languages', { language: 'lng-name', level: 'lng-level' }),
        projects: readItems('projects', { name: 'proj-name', description: 'proj-desc', link: 'proj-link' }),
    };
}

function setVal(id, v) { if (v) $(id).value = v; }

function fillItems(containerId, rows, adder, map) {
    const box = $(containerId);
    box.innerHTML = '';

    (rows || []).forEach(row => {
        adder();
        const card = box.lastElementChild;
        for (const key in map) {
            const el = card.querySelector('.' + map[key]);
            if (el) el.value = row[key] || '';
        }
    });
}

function fillForm(cv) {
    if (!cv) return;

    setVal('fullName', cv.full_name); setVal('jobTitle', cv.job_title);
    setVal('email', cv.email); setVal('phone', cv.phone);
    setVal('location', cv.location); setVal('linkedin', cv.linkedin);
    setVal('summary', cv.summary); setVal('skills', cv.skills);

    fillItems('experiences', cv.experiences, addExp, {
        title: 'exp-title', company: 'exp-company',
        start_date: 'exp-start', end_date: 'exp-end', description: 'exp-desc'
    });
    fillItems('education', cv.education, addEdu, {
        degree: 'edu-degree', school: 'edu-school', field: 'edu-field', year: 'edu-year'
    });
    fillItems('certifications', cv.certifications, addCert, {
        name: 'cert-name', issuer: 'cert-issuer', year: 'cert-year'
    });
    fillItems('languages', cv.languages, addLang, { language: 'lng-name', level: 'lng-level' });
    fillItems('projects', cv.projects, addProject, {
        name: 'proj-name', description: 'proj-desc', link: 'proj-link'
    });

    if (cv.template) selectTemplate(cv.template);

    afterEdit();
}

// One hook for everything that must react to the form changing.
function afterEdit() {
    markProgress();
    saveDraft();
    if (currentStep === 3) schedulePreview();
}

/* ============ TEMPLATES ============ */

function buildTemplates() {
    const chosen = $('template').value;

    $('tplGrid').innerHTML = Object.keys(TEMPLATE_DATA).map(key => {
        const t = TEMPLATE_DATA[key];
        return `<div class="tpl ${key === chosen ? 'on' : ''}" onclick="selectTemplate('${key}')">
            <div class="tpl-mini">
                <div class="bar" style="background:${t.color};width:60%"></div>
                <div class="line" style="width:85%"></div>
                <div class="line" style="width:70%"></div>
                <div class="bar" style="background:${t.color};width:35%;opacity:.5"></div>
                <div class="line" style="width:80%"></div>
            </div>
            <div class="tpl-name">${esc(t[currentLang])}</div>
        </div>`;
    }).join('');
}

function selectTemplate(key) {
    if (!TEMPLATE_DATA[key]) return;

    $('template').value = key;
    buildTemplates();

    if (currentStep === 3) schedulePreview();
    saveDraft();
}

/* ============ LIVE PREVIEW ============ */

let previewTimer = null;
let previewUrl = null;
let previewSeq = 0;

function schedulePreview() {
    clearTimeout(previewTimer);
    previewTimer = setTimeout(renderPreview, 800);
}

async function renderPreview() {
    const data = collectData();

    if (!data.full_name && !data.experiences.some(x => x.title)) {
        $('previewBox').innerHTML = $('previewEmpty') ? $('previewBox').innerHTML : '';
        return;
    }

    // Renders can overlap: a slow one started earlier must never paint over
    // a newer one that already finished.
    const seq = ++previewSeq;

    try {
        const res = await fetch('/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!res.ok || seq !== previewSeq) return;

        const blob = await res.blob();
        if (seq !== previewSeq) return;

        // Blob URLs are held by the document until revoked; without this a
        // long editing session leaks a PDF per keystroke pause.
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        previewUrl = URL.createObjectURL(blob);

        $('previewBox').innerHTML =
            `<iframe src="${previewUrl}#toolbar=0&navpanes=0" title="${T('معاينة السيرة', 'CV preview')}"></iframe>`;

    } catch (e) {
        /* A failed preview is not worth interrupting anyone over. */
    }
}

/* ============ ERRORS FROM THE SERVER ============ */

const ERRORS = {
    ar: {
        missing_key: 'خدمة الذكاء الاصطناعي غير مفعّلة بعد. يمكنك ملء النموذج يدوياً.',
        bad_key: 'مفتاح الخدمة غير صالح. تم إبلاغ المسؤول.',
        bad_model: 'إعداد الخدمة غير صحيح. تم إبلاغ المسؤول.',
        quota: 'تجاوزنا الحصة المسموحة اليوم. جرّب لاحقاً أو أكمل يدوياً.',
        busy: 'خوادم الذكاء الاصطناعي مزدحمة الآن. حاولنا ثلاث مرات — جرّب بعد دقيقة.',
        bad_request: 'تعذّرت قراءة هذا الملف. جرّب ملفاً آخر أو الصق النص.',
        too_large: 'الملف كبير. الحد 10 ميجابايت، والتسجيل 3 دقائق.',
        too_short: 'النص قصير جداً. الصق سيرتك كاملة.',
        job_too_short: 'نص الإعلان قصير. الصقه كاملاً.',
        cv_empty: 'املأ سيرتك أولاً ثم افحصها على الإعلان.',
        bad_type: 'نوع الملف غير مدعوم. استخدم PDF أو Word.',
        no_file: 'لم يُختر ملف.',
        empty: 'لم نتمكّن من قراءة المحتوى. جرّب مرة أخرى أو أكمل يدوياً.',
        upstream: 'تعذّر الوصول للخدمة. جرّب بعد قليل.',
        mic: 'لم نستطع الوصول إلى الميكروفون. اسمح به في إعدادات المتصفح.',
        short_rec: 'التسجيل قصير جداً.',
    },
    en: {
        missing_key: 'AI is not enabled yet. You can fill the form manually.',
        bad_key: 'Service key is invalid. The owner has been notified.',
        bad_model: 'Service is misconfigured. The owner has been notified.',
        quota: 'Daily quota reached. Try later, or continue manually.',
        busy: 'The AI servers are busy. We tried three times — give it a minute.',
        bad_request: 'We could not read that file. Try another, or paste the text.',
        too_large: 'File too large. Max 10MB, recordings max 3 minutes.',
        too_short: 'That text is too short. Paste the full CV.',
        job_too_short: 'The advert text is too short. Paste all of it.',
        cv_empty: 'Fill in your CV first, then check it against the advert.',
        bad_type: 'Unsupported file type. Use PDF or Word.',
        no_file: 'No file selected.',
        empty: 'We could not read that. Try again or continue manually.',
        upstream: 'Service unreachable. Try again shortly.',
        mic: 'Could not reach the microphone. Allow it in your browser settings.',
        short_rec: 'That recording is too short.',
    }
};

function failed(code) {
    const table = ERRORS[currentLang] || ERRORS.ar;
    toast(table[code] || table.upstream);
}

async function postJSON(url, payload) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    return res.json();
}

function imported() {
    goStep(2);
    toast(T('تم — راجع كل حقل قبل التحميل', 'Done — check every field before downloading'));
}

/* ============ DOOR 1: PASTED TEXT ============ */

let openPanel = null;

function openDoor(which) {
    const same = openPanel === which;

    ['voice', 'file', 'text'].forEach(k => {
        const cap = k[0].toUpperCase() + k.slice(1);
        $('panel' + cap).classList.remove('on');
        $('door' + cap).classList.remove('on');
    });

    if (same) { openPanel = null; return; }

    const cap = which[0].toUpperCase() + which.slice(1);
    $('panel' + cap).classList.add('on');
    $('door' + cap).classList.add('on');
    openPanel = which;
}

async function importText() {
    const text = $('pasteBox').value.trim();
    if (text.length < 40) { failed('too_short'); return; }

    busy(true, T('نقرأ النص ونرتّبه...', 'Reading your text...'));

    try {
        const out = await postJSON('/api/import/text', { text, language: currentLang });
        if (out.ok) { fillForm(out.cv); imported(); } else { failed(out.error); }
    } catch (e) { failed('upstream'); }
    finally { busy(false); }
}

/* ============ DOOR 2: AN EXISTING CV ============ */

async function uploadCV(file, from) {
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { failed('too_large'); return; }

    const form = new FormData();
    form.append('file', file);
    form.append('language', currentLang);

    busy(true, T('نقرأ سيرتك...', 'Reading your CV...'));

    try {
        const res = await fetch('/api/import/file', { method: 'POST', body: form });
        const out = await res.json();

        if (!out.ok) { failed(out.error); return; }

        fillForm(out.cv);

        // Someone who uploaded from the tailoring screen came to compare
        // against an advert, not to edit a form. Leave them where they were.
        if (from === 'tailor') {
            showTailorState();
            toast(T('قرأنا سيرتك — الصق الإعلان الآن', 'CV read — now paste the advert'));
        } else {
            imported();
        }
    } catch (e) { failed('upstream'); }
    finally { busy(false); }
}

/* ============ DOOR 3: VOICE ============
   The recording is uploaded as audio. Transcribing in the browser first
   would hand the model a guess at a Jordanian or Gulf accent instead of
   the accent itself, and that guess is where company names and
   qualifications get mangled. */

let recorder = null, chunks = [], recStart = 0, recTimer = null;
const MAX_SECONDS = 180;

function fmt(s) { return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); }

async function toggleRec() {
    if (recorder && recorder.state === 'recording') { recorder.stop(); return; }

    let stream;
    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) { failed('mic'); return; }

    chunks = [];
    recorder = new MediaRecorder(stream);
    recorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };

    recorder.onstop = async () => {
        clearInterval(recTimer);
        stream.getTracks().forEach(t => t.stop());

        $('recBtn').classList.remove('live');
        $('recBtn').textContent = '🎙️';
        $('recState').textContent = T('اضغط وابدأ الكلام', 'Tap and start talking');

        const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });

        // Two seconds of silence is a misclick, not a CV.
        if (blob.size < 8000) { failed('short_rec'); return; }

        const form = new FormData();
        form.append('audio', blob, 'voice.webm');
        form.append('language', currentLang);

        busy(true, T('نستمع ونكتب سيرتك...', 'Listening and writing...'));

        try {
            const res = await fetch('/api/import/audio', { method: 'POST', body: form });
            const out = await res.json();
            if (out.ok) { fillForm(out.cv); imported(); } else { failed(out.error); }
        } catch (e) { failed('upstream'); }
        finally { busy(false); }
    };

    recorder.start();
    recStart = Date.now();

    $('recBtn').classList.add('live');
    $('recBtn').textContent = '⏹';
    $('recState').textContent = T('يسجّل... اضغط لإنهاء', 'Recording... tap to finish');

    recTimer = setInterval(() => {
        const secs = Math.floor((Date.now() - recStart) / 1000);
        $('recTime').textContent = fmt(secs);

        // A hard stop rather than a warning: one long upload left running
        // would spend a day's quota on a single CV.
        if (secs >= MAX_SECONDS && recorder.state === 'recording') recorder.stop();
    }, 500);
}

/* ============ THE DRAFT ============
   Twenty-seven fields and no persistence: one refresh, one closed tab,
   one phone call, and everything typed was gone. */

const DRAFT_KEY = 'cv_draft_v2';
let draftTimer = null;

function saveDraft() {
    clearTimeout(draftTimer);
    draftTimer = setTimeout(() => {
        try {
            localStorage.setItem(DRAFT_KEY, JSON.stringify({ at: Date.now(), cv: collectData() }));
        } catch (e) { /* private window, or storage full - not fatal */ }
    }, 700);
}

function readDraft() {
    try {
        const raw = localStorage.getItem(DRAFT_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
}

function restoreDraft() {
    const d = readDraft();
    if (d && d.cv) { fillForm(d.cv); goStep(2); }
    $('restore').classList.remove('on');
}

function discardDraft() {
    try { localStorage.removeItem(DRAFT_KEY); } catch (e) { }
    $('restore').classList.remove('on');
}

/* ============ TAILORING TO ONE ADVERT ============ */

let lastMatch = null;

async function matchJob() {
    const jobText = $('jobText').value.trim();
    if (jobText.length < 60) { failed('job_too_short'); return; }

    const cv = collectData();
    if (!cv.full_name && !cv.experiences.some(x => x.title)) { failed('cv_empty'); return; }

    busy(true, T('نقارن سيرتك بالإعلان...', 'Comparing...'));

    try {
        const out = await postJSON('/api/match-job', { cv, job_text: jobText, language: currentLang });
        if (out.ok) { lastMatch = out.result; renderMatch(out.result); } else { failed(out.error); }
    } catch (e) { failed('upstream'); }
    finally { busy(false); }
}

function scoreColour(pct) {
    if (pct >= 75) return 'var(--ok)';
    if (pct >= 50) return 'var(--gold)';
    return 'var(--danger)';
}

function renderMatch(r) {
    const c = scoreColour(r.match_percent);
    let h = '';

    // The number sits beside the evidence it came from. A score with
    // nothing behind it is what every other site shows, and it is why
    // nobody believes those scores.
    h += `<div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap;margin-bottom:18px">
        <div class="score" style="color:${c};border:3px solid ${c}">${r.match_percent}%</div>
        <div>
            <div style="font-weight:800;margin-bottom:3px">${esc(r.job_title)}</div>
            <div style="font-size:.9rem;color:var(--ink-soft)">${esc(r.verdict)}</div>
            <div style="font-size:.82rem;color:var(--ink-faint);margin-top:6px">
                ${T(`${r.found_count} من ${r.total_count} من متطلبات الإعلان ظاهرة في سيرتك`,
                    `${r.found_count} of ${r.total_count} requirements visible in your CV`)}
            </div>
        </div></div>`;

    h += '<div style="margin-bottom:18px">';
    (r.terms || []).forEach(t => {
        h += `<span class="chip ${t.found ? 'yes' : 'no'}${t.importance === 'essential' ? ' key' : ''}"
                    title="${esc(t.evidence || '')}">${t.found ? '✓' : '✗'} ${esc(t.term)}</span>`;
    });
    h += '</div>';

    if (r.tailored_summary) {
        h += `<div class="fix">
            <div class="fix-where">${T('ملخص مهني موجّه لهذه الوظيفة', 'Summary aimed at this job')}</div>
            <div class="fix-new">${esc(r.tailored_summary)}</div>
            <button class="btn sm" style="margin-top:10px" onclick="applySummary()">${T('استخدمه', 'Use it')}</button>
        </div>`;
    }

    if ((r.rewrites || []).length) {
        h += `<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:22px 0 10px">
            <div style="font-weight:800">
                ${T('عندك هذا فعلاً — لكن بكلمات أخرى', 'You already have these, worded differently')}</div>
            <button class="btn sm" onclick="applyAllFixes()">
                ${T('طبّق الكل', 'Apply all')}</button>
        </div>`;

        r.rewrites.forEach((w, i) => {
            h += `<div class="fix">
                <div class="fix-where">${esc(w.where_label || '')}</div>
                ${w.current ? `<div class="fix-old">${esc(w.current)}</div>` : ''}
                <div class="fix-new">${esc(w.suggested)}</div>
                ${(w.covers || []).length ? `<div style="font-size:.76rem;color:var(--ink-faint);margin-top:6px">
                    ${T('يُظهر: ', 'surfaces: ')}${esc(w.covers.join('، '))}</div>` : ''}
                <button class="btn sm" data-fix="${i}" style="margin-top:10px" onclick="applyFix(${i})">${T('طبّق', 'Apply')}</button>
            </div>`;
        });
    }

    // Last, separate, and with no button. Telling someone to write in a
    // skill they do not have wins the filter and loses the interview.
    if ((r.genuinely_missing || []).length) {
        h += `<div class="gaps">
            <div style="font-weight:800;margin-bottom:8px">
                ${T('ناقص فعلاً — لا تضفه لسيرتك', 'Genuinely missing — do not add it')}</div>`;

        r.genuinely_missing.forEach(g => {
            h += `<div style="font-size:.88rem;margin:7px 0"><b>${esc(g.term)}</b> — ${esc(g.note)}</div>`;
        });

        h += `<div style="font-size:.79rem;color:var(--ink-soft);margin-top:10px">
            ${T('كتابة مهارة لا تملكها تمرّ من الفلتر وتسقط في المقابلة. الأفضل أن تتعلّمها أو تتقدّم كما أنت.',
                'A skill you do not have passes the filter and fails the interview.')}</div></div>`;
    }

    // The point of the whole screen: leaving with a different file for
    // this advert. Without this the person is handed a report and left to
    // find the download button on another screen.
    h += `<div style="margin-top:22px;padding-top:18px;border-top:1px solid var(--line);
                      display:flex;gap:10px;flex-wrap:wrap;align-items:center">
        <button class="btn" onclick="downloadTailored()">
            ${T('حمّل السيرة المفصّلة لهذه الوظيفة', 'Download the CV tailored to this job')}</button>
        <button class="btn ghost" onclick="goStep(2)">
            ${T('راجع المحتوى أولاً', 'Review the content first')}</button>
    </div>`;

    $('matchOut').innerHTML = h;
}

function applySummary() {
    if (!lastMatch || !lastMatch.tailored_summary) return;
    $('summary').value = lastMatch.tailored_summary;
    afterEdit();
    toast(T('تم تحديث الملخص', 'Summary updated'));
}

function copyFix(i) {
    const w = (lastMatch && lastMatch.rewrites || [])[i];
    if (!w) return;
    navigator.clipboard.writeText(w.suggested)
        .then(() => toast(T('نُسخ — الصقه في مكانه', 'Copied')));
}

/* ============ APPLYING WHAT THE CHECK FOUND ============
   The first version printed its suggestions and left the person to copy
   them across by hand - which is the same failure the whole project
   started with: we did the analysis and handed them the work.

   A rewrite now points at a field (section, index, field) so it can be
   written straight into the form. `current` is checked first: the CV may
   have been edited between running the check and pressing apply, and
   silently overwriting newer text would be worse than refusing. */

function rewriteTarget(w) {
    const idx = w.where_index || 0;

    if (w.where_section === 'summary') return $('summary');
    if (w.where_section === 'skills') return $('skills');

    const box = w.where_section === 'project' ? 'projects' : 'experiences';
    const cards = document.querySelectorAll('#' + box + ' .item');
    const card = cards[idx];

    if (!card) return null;

    const cls = w.where_section === 'project'
        ? (w.where_field === 'title' ? 'proj-name' : 'proj-desc')
        : (w.where_field === 'title' ? 'exp-title' : 'exp-desc');

    return card.querySelector('.' + cls);
}

function applyFix(i, quiet) {
    const w = (lastMatch && lastMatch.rewrites || [])[i];
    if (!w) return false;

    const el = rewriteTarget(w);

    if (!el) {
        if (!quiet) toast(T('لم نجد هذا الحقل — ربما حذفته', 'That field is gone — it may have been removed'));
        return false;
    }

    // Edited since the check ran: refuse rather than discard the new text.
    const now = (el.value || '').trim();
    const was = (w.current || '').trim();

    if (was && now && now !== was) {
        if (!quiet) toast(T('تغيّر النص بعد الفحص — راجعه يدوياً', 'This text changed after the check — review it by hand'));
        return false;
    }

    el.value = w.suggested;

    const btn = document.querySelector('[data-fix="' + i + '"]');
    if (btn) { btn.textContent = T('✓ طُبّق', '✓ Applied'); btn.disabled = true; }

    afterEdit();
    return true;
}

function applyAllFixes() {
    const list = (lastMatch && lastMatch.rewrites) || [];
    let done = 0;

    list.forEach((w, i) => { if (applyFix(i, true)) done++; });

    if (lastMatch && lastMatch.tailored_summary && !list.some(w => w.where_section === 'summary')) {
        $('summary').value = lastMatch.tailored_summary;
        done++;
    }

    afterEdit();

    toast(done
        ? T(`طُبّق ${done} تعديلاً — راجعها قبل التحميل`, `${done} changes applied — review before downloading`)
        : T('لا شيء للتطبيق', 'Nothing to apply'));
}

// Downloading from the tailoring screen, named after the job, because the
// whole point is ending up with a different file per advert.
async function downloadTailored() {
    const data = collectData();

    if (!data.full_name) { toast(T('اكتب اسمك أولاً', 'Enter your name first')); return; }

    const job = (lastMatch && lastMatch.job_title ? lastMatch.job_title : '')
        .replace(/[\\/:*?"<>|]/g, '').replace(/\s+/g, '_').slice(0, 40);

    busy(true, T('جارٍ إنشاء السيرة المفصّلة...', 'Building the tailored CV...'));

    try {
        const blob = await pdfBlob(data);
        const base = data.full_name.replace(/\s+/g, '_') || 'cv';
        saveBlob(blob, base + (job ? '_' + job : '_tailored') + '.pdf');
        toast(T('تم التحميل ✨', 'Downloaded ✨'));
    } catch (e) {
        toast(T('تعذّر الإنشاء. جرّب مرة أخرى.', 'Could not generate. Try again.'));
    } finally { busy(false); }
}

// The tailoring screen is reachable from the top bar at any moment, so it
// has to cope with arriving before there is any CV to compare.
function showTailorState() {
    const d = collectData();
    const hasCv = !!(d.full_name || d.experiences.some(x => x.title || x.company));

    $('tailorNoCv').style.display = hasCv ? 'none' : 'block';
    $('tailorReady').style.display = hasCv ? 'block' : 'none';
}

/* ============ DOWNLOAD ============ */

async function generate() {
    const data = collectData();

    if (!data.full_name) {
        toast(T('اكتب اسمك أولاً', 'Enter your name first'));
        goStep(2); openSheet('basics');
        return;
    }

    busy(true, T('جارٍ إنشاء السيرة...', 'Generating your CV...'));

    try {
        const res = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!res.ok) { toast(T('تعذّر الإنشاء. جرّب مرة أخرى.', 'Could not generate. Try again.')); return; }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');

        a.href = url;
        a.download = (data.full_name.replace(/\s+/g, '_') || 'cv') + '.pdf';
        a.click();
        URL.revokeObjectURL(url);

        toast(T('تم التحميل ✨', 'Downloaded ✨'));

    } catch (e) {
        toast(T('حدث خطأ. جرّب مرة أخرى.', 'Something went wrong. Try again.'));
    } finally { busy(false); }
}

/* ============ BOTH LANGUAGES, ONE INPUT ============
   The thing a chat model cannot finish. It translates the words and
   leaves you fighting a word processor for an Arabic PDF a filter can
   read; here one recording produces both files.

   In Jordan and the Gulf most applicants genuinely need the pair, so this
   is the feature worth being known for rather than "CV builder". */

async function pdfBlob(data) {
    const res = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (!res.ok) throw new Error('generate failed');
    return res.blob();
}

function saveBlob(blob, name) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
}

async function downloadBoth() {
    const data = collectData();

    if (!data.full_name) {
        toast(T('اكتب اسمك أولاً', 'Enter your name first'));
        goStep(2); openSheet('basics');
        return;
    }

    const here = data.language;
    const there = here === 'ar' ? 'en' : 'ar';
    const base = data.full_name.replace(/\s+/g, '_') || 'cv';

    busy(true, T('نترجم ونُخرج الملفين...', 'Translating and building both files...'));

    try {
        // The language the person is already in goes out first, so a
        // failure in the translation still leaves them holding the file
        // they came for.
        saveBlob(await pdfBlob(data), base + '_' + here + '.pdf');

        const out = await postJSON('/api/translate', { cv: data, target: there });

        if (!out.ok) { failed(out.error); return; }

        const other = Object.assign({}, out.cv, {
            language: there,
            template: data.template
        });

        saveBlob(await pdfBlob(other), base + '_' + there + '.pdf');

        toast(T('تم تحميل النسختين ✨', 'Both versions downloaded ✨'));

    } catch (e) {
        toast(T('تعذّر الإنشاء. جرّب مرة أخرى.', 'Could not generate. Try again.'));
    } finally { busy(false); }
}

/* ============ START ============ */

document.addEventListener('input', e => {
    if (e.target.closest('.card')) afterEdit();
});

(function init() {
    try {
        const saved = localStorage.getItem('cv_theme');
        if (saved === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            $('themeBtn').textContent = '☀️';
        }
    } catch (e) { }

    buildNav();
    buildTemplates();
    addExp();
    addEdu();
    setLang('ar');

    const d = readDraft();
    if (d && d.cv && (d.cv.full_name || d.cv.summary ||
        (d.cv.experiences || []).some(x => x.title || x.company))) {
        $('restore').classList.add('on');
    }
})();
