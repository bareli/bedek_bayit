/* Bedek Bayit card: household maintenance tasks, last done / next due, in Hebrew or English. */

const FSI = "\u2068"; // first-strong isolate
const PDI = "\u2069";
const iso = (text) => FSI + text + PDI;

const STATUS_ORDER = ["overdue", "due", "due_soon", "ok", "unknown", "paused"];
const STATUS_COLORS = {
  overdue: "var(--error-color, #db4437)",
  due: "var(--warning-color, #ffa600)",
  due_soon: "var(--warning-color, #ffa600)",
  ok: "var(--success-color, #43a047)",
  unknown: "var(--disabled-text-color, #9e9e9e)",
  paused: "var(--disabled-text-color, #9e9e9e)",
};
const CATEGORY_ICONS = {
  climate: "mdi:air-conditioner",
  water: "mdi:water",
  solar: "mdi:solar-panel",
  safety: "mdi:shield-check",
  gas: "mdi:gas-cylinder",
  kitchen: "mdi:silverware-fork-knife",
  structure: "mdi:home-roof",
  religious: "mdi:star-david",
  general: "mdi:wrench-outline",
};

// Hebrew counted nouns: [one, two, many].
const HE_UNITS = {
  days: ["יום", "יומיים", "ימים"],
  weeks: ["שבוע", "שבועיים", "שבועות"],
  months: ["חודש", "חודשיים", "חודשים"],
  years: ["שנה", "שנתיים", "שנים"],
};
const EN_UNITS = { days: ["day", "days"], weeks: ["week", "weeks"], months: ["month", "months"], years: ["year", "years"] };

function heCount(n, unit) {
  const [one, two, many] = HE_UNITS[unit];
  if (n === 1) return one;
  if (n === 2) return two;
  return `${iso(n)} ${many}`;
}
function enCount(n, unit) {
  const [one, many] = EN_UNITS[unit];
  return n === 1 ? `1 ${one}` : `${iso(n)} ${many}`;
}
// Days -> the most natural unit: 9 days, 3 weeks, 2 months, 1 year.
function span(days) {
  const d = Math.abs(days);
  if (d < 14) return [d, "days"];
  if (d < 60) return [Math.round(d / 7), "weeks"];
  if (d < 548) return [Math.round(d / 30.44), "months"];
  return [Math.round(d / 365.25), "years"];
}

const I18N = {
  en: {
    title: "Home maintenance",
    count: enCount,
    overdue_by: (t) => `Overdue by ${t}`,
    overdue_1: "Overdue since yesterday",
    due_today: "Due today",
    due_tomorrow: "Due tomorrow",
    due_in: (t) => `Due in ${t}`,
    unknown: "When was it last done?",
    paused: "Paused",
    no_data: "Waiting for the sensor",
    last_done: (t) => `Done ${t} ago`,
    last_done_today: "Done today",
    last_done_never: "Never recorded",
    snoozed: (d) => `snoozed to ${d}`,
    due_on: (d) => `due ${d}`,
    s_overdue: (n) => `${iso(n)} overdue`,
    s_due: (n) => `${iso(n)} today`,
    s_due_soon: (n) => `${iso(n)} soon`,
    all_good: "All up to date",
    done: "Done",
    done_today: "Done today",
    more: "More",
    add: "Add task",
    empty: "No tasks yet",
    loading: "Loading…",
    not_loaded: "Set up the Bedek Bayit integration first.",
    error: "Something went wrong",
    close: "Close",
    cancel: "Cancel",
    save: "Save",
    delete: "Delete task",
    confirm_delete: "Delete this task and its history?",
    confirm_yes: "Yes, delete",
    edit: "Edit",
    snooze: (n) => `Snooze ${enCount(n, "days")}`,
    record: "Record a completion",
    record_save: "Save completion",
    date: "Date",
    note: "Note",
    cost: "Cost (₪)",
    history: "History",
    no_history: "No completions recorded yet.",
    remove_entry: "Remove entry",
    by: (u) => `by ${u}`,
    new_task: "New task",
    edit_task: "Edit task",
    pick_template: "Pick a ready task, or start from scratch",
    custom: "Custom task",
    already: "added",
    f_name: "Name",
    f_icon: "Icon",
    f_category: "Category",
    f_schedule: "Repeats",
    f_every: "Every",
    f_unit: "Unit",
    f_holiday: "Holiday",
    f_days: "Days",
    f_when: "When",
    before: "before",
    after: "after",
    on_day: "on the day",
    f_day: "Day",
    f_month: "Month",
    f_entity: "Due-date sensor",
    f_entity_hint: "A date or timestamp sensor, for example the Tami4 'Filter upcoming replacement' sensor.",
    f_last_done: "Last done",
    f_remind_days: "Remind days before",
    f_remind_hint: (n) => `Empty = ${n} (integration setting)`,
    f_notes: "Notes",
    f_paused: "Paused (no reminders)",
    sched: {
      interval: "Every N days / weeks / months / years",
      holiday: "Yearly, around a Jewish holiday",
      yearly: "Yearly, on a date",
      entity: "From a sensor (for example Tami4)",
    },
    units: { days: "Days", weeks: "Weeks", months: "Months", years: "Years" },
    every: (n, unit) => (n === 1 ? `Every ${EN_UNITS[unit][0]}` : `Every ${iso(n)} ${EN_UNITS[unit][1]}`),
    around: (n, rel, h) => (n === 0 ? `On ${h}` : `${enCount(n, "days")} ${rel} ${h}`),
    yearly: (d) => `Every year on ${d}`,
    from_sensor: "From a sensor",
    holidays: { rosh_hashana: "Rosh Hashana", sukkot: "Sukkot", hanukkah: "Hanukkah", purim: "Purim", pesach: "Pesach", shavuot: "Shavuot" },
    categories: {
      climate: "Air conditioning", water: "Water", solar: "Solar water heater", safety: "Safety", gas: "Gas",
      kitchen: "Kitchen and laundry", structure: "House and roof", religious: "Judaica", general: "General",
    },
    errors: {
      required: "Required", too_long: "Too long", invalid: "Invalid value", future: "Can't be in the future",
      not_found: "Task not found", too_many: "Too many tasks",
    },
    e_title: "Title",
    e_attention_only: "Only tasks that need attention",
    e_limit: "Maximum tasks (0 = all)",
    e_categories: "Categories (empty = all)",
    e_show_add: "Show the Add button (admins)",
  },
  he: {
    title: "תחזוקת הבית",
    count: heCount,
    overdue_by: (t) => `באיחור של ${t}`,
    overdue_1: "באיחור מאתמול",
    due_today: "היום",
    due_tomorrow: "מחר",
    due_in: (t) => `בעוד ${t}`,
    unknown: "מתי בוצע לאחרונה?",
    paused: "מושהה",
    no_data: "ממתין לחיישן",
    last_done: (t) => `בוצע לפני ${t}`,
    last_done_today: "בוצע היום",
    last_done_never: "לא נרשם ביצוע",
    snoozed: (d) => `נדחה ל-${d}`,
    due_on: (d) => `מועד: ${d}`,
    s_overdue: (n) => `${iso(n)} באיחור`,
    s_due: (n) => `${iso(n)} להיום`,
    s_due_soon: (n) => `${iso(n)} בקרוב`,
    all_good: "הכול מעודכן",
    done: "בוצע",
    done_today: "בוצע היום",
    more: "עוד",
    add: "הוספת משימה",
    empty: "אין עדיין משימות",
    loading: "טוען…",
    not_loaded: "יש להגדיר קודם את האינטגרציה בדק בית.",
    error: "משהו השתבש",
    close: "סגירה",
    cancel: "ביטול",
    save: "שמירה",
    delete: "מחיקת משימה",
    confirm_delete: "למחוק את המשימה ואת ההיסטוריה שלה?",
    confirm_yes: "כן, למחוק",
    edit: "עריכה",
    snooze: (n) => (n === 1 ? "דחייה ביום" : n === 2 ? "דחייה ביומיים" : `דחייה ב-${iso(n)} ימים`),
    record: "רישום ביצוע",
    record_save: "שמירת ביצוע",
    date: "תאריך",
    note: "הערה",
    cost: "עלות (₪)",
    history: "היסטוריה",
    no_history: "עדיין לא נרשמו ביצועים.",
    remove_entry: "הסרת רשומה",
    by: (u) => `על ידי ${u}`,
    new_task: "משימה חדשה",
    edit_task: "עריכת משימה",
    pick_template: "בחרו משימה מוכנה, או התחילו מאפס",
    custom: "משימה מותאמת",
    already: "נוסף",
    f_name: "שם",
    f_icon: "סמל",
    f_category: "קטגוריה",
    f_schedule: "חוזר",
    f_every: "כל",
    f_unit: "יחידה",
    f_holiday: "חג",
    f_days: "ימים",
    f_when: "מתי",
    before: "לפני",
    after: "אחרי",
    on_day: "ביום עצמו",
    f_day: "יום",
    f_month: "חודש",
    f_entity: "חיישן מועד",
    f_entity_hint: "חיישן תאריך או זמן, למשל החיישן 'Filter upcoming replacement' של תמי4.",
    f_last_done: "בוצע לאחרונה",
    f_remind_days: "להזכיר ימים לפני",
    f_remind_hint: (n) => `ריק = ${iso(n)} (הגדרת האינטגרציה)`,
    f_notes: "הערות",
    f_paused: "מושהה (בלי תזכורות)",
    sched: {
      interval: "כל X ימים / שבועות / חודשים / שנים",
      holiday: "שנתי, סביב חג",
      yearly: "שנתי, בתאריך",
      entity: "לפי חיישן (למשל תמי4)",
    },
    units: { days: "ימים", weeks: "שבועות", months: "חודשים", years: "שנים" },
    every: (n, unit) => `כל ${heCount(n, unit)}`,
    around: (n, rel, h) => (n === 0 ? `ב${h}` : `${heCount(n, "days")} ${rel} ${h}`),
    yearly: (d) => `כל שנה ב-${d}`,
    from_sensor: "לפי חיישן",
    holidays: { rosh_hashana: "ראש השנה", sukkot: "סוכות", hanukkah: "חנוכה", purim: "פורים", pesach: "פסח", shavuot: "שבועות" },
    categories: {
      climate: "מיזוג אוויר", water: "מים", solar: "דוד שמש", safety: "בטיחות", gas: "גז",
      kitchen: "מטבח וכביסה", structure: "מבנה וגג", religious: "יהדות", general: "כללי",
    },
    errors: {
      required: "שדה חובה", too_long: "ארוך מדי", invalid: "ערך לא תקין", future: "לא יכול להיות בעתיד",
      not_found: "המשימה לא נמצאה", too_many: "יותר מדי משימות",
    },
    e_title: "כותרת",
    e_attention_only: "רק משימות שדורשות טיפול",
    e_limit: "מספר משימות מרבי (0 = הכול)",
    e_categories: "קטגוריות (ריק = הכול)",
    e_show_add: "להציג את כפתור ההוספה (למנהלים)",
  },
};

// "YYYY-MM-DD" -> local Date at noon (no timezone drift).
function parseDay(key) {
  return new Date(+key.slice(0, 4), +key.slice(5, 7) - 1, +key.slice(8, 10), 12);
}
function dayDiff(a, b) {
  return Math.round((parseDay(a) - parseDay(b)) / 86400000);
}

// Tiny DOM builder: el("div", {class: "x", onclick: fn}, child, "text").
function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value == null || value === false) continue;
    if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (key === "class") node.className = value;
    else if (key === "style") node.style.cssText = value;
    else if (key in node && typeof value !== "string") node[key] = value;
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) {
    if (child == null || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

const STYLE = `
  :host { display: block; }
  ha-card { overflow: hidden; }
  .header { display: flex; align-items: center; gap: 8px; padding: 12px 16px 4px; flex-wrap: wrap; }
  .title { font-size: 1.25em; font-weight: 500; flex: 1; min-width: 0; }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; padding: 0 16px 8px; }
  .chip { font-size: 0.8em; padding: 2px 8px; border-radius: 12px; background: var(--secondary-background-color); }
  .chip.overdue { color: var(--error-color, #db4437); font-weight: 500; }
  .chip.due, .chip.due_soon { color: var(--warning-color, #ffa600); font-weight: 500; }
  .chip.ok { color: var(--success-color, #43a047); }
  .list { padding: 0 8px 8px; }
  .row { display: flex; align-items: center; gap: 12px; padding: 8px; border-radius: 8px; }
  .row + .row { border-top: 1px solid var(--divider-color); border-radius: 0; }
  .icon { flex: none; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
          background: color-mix(in srgb, var(--c) 15%, transparent); color: var(--c); }
  .main { flex: 1; min-width: 0; }
  .name { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .when { font-size: 0.9em; color: var(--c); font-weight: 500; }
  .meta { font-size: 0.8em; color: var(--secondary-text-color); }
  .bar { height: 4px; border-radius: 2px; background: var(--divider-color); margin-top: 4px; overflow: hidden; }
  .bar > div { height: 100%; background: var(--c); }
  .actions { display: flex; gap: 4px; flex: none; align-items: center; }
  button { font: inherit; cursor: pointer; border-radius: 18px; border: 1px solid var(--divider-color);
           background: none; color: var(--primary-text-color); padding: 6px 12px; min-height: 36px; }
  button.primary { background: var(--primary-color); color: var(--text-primary-color, #fff); border-color: transparent; }
  button.danger { color: var(--error-color, #db4437); border-color: var(--error-color, #db4437); }
  button.icon-btn { border: none; padding: 6px; min-width: 36px; border-radius: 50%; }
  button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
    outline: 2px solid var(--primary-color); outline-offset: 2px; }
  button[disabled] { opacity: 0.5; cursor: default; }
  .empty, .status-msg { padding: 16px; color: var(--secondary-text-color); text-align: center; }
  .overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 10; display: flex;
             align-items: center; justify-content: center; padding: 16px; }
  .dialog { background: var(--card-background-color, var(--primary-background-color)); color: var(--primary-text-color);
            border-radius: 12px; width: min(560px, 100%); max-height: calc(100vh - 32px); overflow: auto; padding: 16px 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
  .dialog h2 { margin: 0 0 12px; font-size: 1.2em; font-weight: 500; display: flex; align-items: center; gap: 8px; }
  .dialog h3 { font-size: 1em; margin: 16px 0 8px; font-weight: 500; }
  .field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; flex: 1; min-width: 0; }
  .field label { font-size: 0.85em; color: var(--secondary-text-color); }
  .field.check { flex-direction: row; align-items: center; gap: 8px; }
  .inline { display: flex; gap: 8px; flex-wrap: wrap; }
  input, select, textarea { font: inherit; color: var(--primary-text-color); background: var(--secondary-background-color);
           border: 1px solid var(--divider-color); border-radius: 6px; padding: 8px; min-height: 20px; }
  input[type=checkbox] { min-height: auto; width: 18px; height: 18px; }
  textarea { min-height: 60px; resize: vertical; }
  input.bad, select.bad, textarea.bad { border-color: var(--error-color, #db4437); }
  .err { color: var(--error-color, #db4437); font-size: 0.8em; min-height: 0; }
  .hint { font-size: 0.8em; color: var(--secondary-text-color); }
  .buttons { display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap; margin-top: 16px; }
  .buttons .spacer { flex: 1; }
  .templates { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
  .tpl { display: flex; align-items: center; gap: 8px; text-align: start; border-radius: 8px; padding: 8px; }
  .tpl small { display: block; color: var(--secondary-text-color); }
  .cat { font-size: 0.8em; color: var(--secondary-text-color); margin: 12px 0 4px; grid-column: 1 / -1; }
  .hist { list-style: none; padding: 0; margin: 0; }
  .hist li { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-top: 1px solid var(--divider-color); font-size: 0.9em; }
  .hist li span { flex: 1; }
  .notes { white-space: pre-wrap; font-size: 0.9em; color: var(--secondary-text-color); margin: 0 0 8px; }
  @media (prefers-reduced-motion: no-preference) { .bar > div { transition: width 0.3s; } }
  @media (max-width: 420px) { .actions .label { display: none; } }
`;

class BedekBayitCard extends HTMLElement {
  static getConfigElement() { return document.createElement("bedek-bayit-card-editor"); }
  static getStubConfig() { return { attention_only: false }; }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._data = null;
    this._error = null;
    this._dialog = null; // {kind: "details"|"edit"|"pick"|"confirm", ...}
    this._busy = false;
  }

  setConfig(config) {
    this._config = Object.assign({ show_add: true, attention_only: false, limit: 0 }, config || {});
    this._render();
  }

  set hass(hass) {
    const first = !this._hass;
    const langChanged = this._hass && this._hass.language !== hass.language;
    this._hass = hass;
    if (first || langChanged) {
      this._render();
      this._subscribe();
    }
  }

  get lang() {
    const l = (this._data && this._data.language) || (this._hass && this._hass.language) || "en";
    return l.startsWith("he") ? "he" : "en";
  }
  t(key) { return I18N[this.lang][key]; }

  connectedCallback() { if (this._hass && !this._unsub) this._subscribe(); }
  disconnectedCallback() { this._unsubscribe(); }

  async _subscribe() {
    this._unsubscribe();
    if (!this._hass || !this.isConnected) return;
    try {
      this._unsub = await this._hass.connection.subscribeMessage(
        (payload) => { this._data = payload; this._error = null; this._render(); },
        { type: "bedek_bayit/subscribe", language: this._hass.language }
      );
    } catch (err) {
      this._error = err && err.code === "not_loaded" ? "not_loaded" : "error";
      this._render();
    }
  }
  _unsubscribe() {
    if (this._unsub) {
      const unsub = this._unsub;
      this._unsub = null;
      Promise.resolve(unsub()).catch(() => {});
    }
  }

  get isAdmin() { return !!(this._hass && this._hass.user && this._hass.user.is_admin); }

  _ws(msg) { return this._hass.callWS(msg); }

  getCardSize() { return 2 + Math.min(this._visible().length, 8); }

  _visible() {
    if (!this._data) return [];
    const cfg = this._config;
    let tasks = this._data.tasks;
    if (cfg.attention_only) tasks = tasks.filter((t) => ["overdue", "due", "due_soon"].includes(t.status));
    if (cfg.categories && cfg.categories.length) tasks = tasks.filter((t) => cfg.categories.includes(t.category));
    if (cfg.limit > 0) tasks = tasks.slice(0, cfg.limit);
    return tasks;
  }

  // ---- text helpers ----------------------------------------------------

  formatDate(key) {
    const locale = this.lang === "he" ? "he-IL" : (this._hass && this._hass.locale && this._hass.locale.language) || "en";
    const opts = this.lang === "he" ? { day: "numeric", month: "numeric", year: "numeric" } : { day: "numeric", month: "short", year: "numeric" };
    return iso(new Intl.DateTimeFormat(locale, opts).format(parseDay(key)));
  }

  whenText(task) {
    const t = I18N[this.lang];
    const d = task.days_left;
    if (task.status === "paused") return t.paused;
    if (task.status === "unknown") return task.schedule.type === "entity" ? t.no_data : t.unknown;
    if (d < -1) { const [n, u] = span(d); return t.overdue_by(t.count(n, u)); }
    if (d === -1) return t.overdue_1;
    if (d === 0) return t.due_today;
    if (d === 1) return t.due_tomorrow;
    const [n, u] = span(d);
    return t.due_in(t.count(n, u));
  }

  lastText(task) {
    const t = I18N[this.lang];
    if (!task.last_done) return t.last_done_never;
    const ago = dayDiff(this._data.today, task.last_done);
    if (ago <= 0) return t.last_done_today;
    const [n, u] = span(ago);
    return t.last_done(t.count(n, u));
  }

  scheduleText(s) {
    const t = I18N[this.lang];
    if (s.type === "interval") return t.every(s.every, s.unit);
    if (s.type === "holiday") {
      const off = s.offset_days || 0;
      return t.around(Math.abs(off), off < 0 ? t.before : t.after, t.holidays[s.holiday] || s.holiday);
    }
    if (s.type === "yearly") {
      const locale = this.lang === "he" ? "he-IL" : "en";
      const opts = this.lang === "he" ? { day: "numeric", month: "numeric" } : { day: "numeric", month: "long" };
      return t.yearly(iso(new Intl.DateTimeFormat(locale, opts).format(new Date(2028, s.month - 1, s.day, 12))));
    }
    return `${t.from_sensor}: ${s.entity_id}`;
  }

  // ---- rendering ---------------------------------------------------------

  _render() {
    if (!this._config) return;
    const active = this.shadowRoot.activeElement;
    const focusKey = active ? active.getAttribute("data-focus-key") : null;
    this._renderInner();
    if (focusKey) {
      const target = this.shadowRoot.querySelector(`[data-focus-key="${CSS.escape(focusKey)}"]`);
      if (target) target.focus();
    }
  }

  _renderInner() {
    const root = this.shadowRoot;
    root.replaceChildren();
    root.append(el("style", {}, STYLE));
    const t = I18N[this.lang];
    const card = el("ha-card", { dir: this.lang === "he" ? "rtl" : "ltr", lang: this.lang });
    root.append(card);

    const header = el("div", { class: "header" }, el("div", { class: "title" }, this._config.title || t.title));
    if (this._data && this.isAdmin && this._config.show_add) {
      header.append(
        el("button", { class: "primary", "data-focus-key": "add", onclick: () => this._openPicker() },
          el("ha-icon", { icon: "mdi:plus", style: "--mdc-icon-size:18px" }), " ", t.add)
      );
    }
    card.append(header);

    if (this._error) {
      card.append(el("div", { class: "status-msg", role: "alert" }, t[this._error] || t.error));
      return;
    }
    if (!this._data) {
      card.append(el("div", { class: "status-msg" }, t.loading));
      return;
    }

    const counts = { overdue: 0, due: 0, due_soon: 0 };
    this._data.tasks.forEach((task) => { if (task.status in counts) counts[task.status] += 1; });
    const chips = el("div", { class: "chips", role: "status" });
    ["overdue", "due", "due_soon"].forEach((s) => {
      if (counts[s]) chips.append(el("span", { class: `chip ${s}` }, t[`s_${s}`](counts[s])));
    });
    if (!chips.childNodes.length && this._data.tasks.length) chips.append(el("span", { class: "chip ok" }, t.all_good));
    card.append(chips);

    const tasks = this._visible();
    if (!this._data.tasks.length) {
      card.append(el("div", { class: "empty" }, t.empty));
    } else if (tasks.length) {
      const list = el("div", { class: "list", role: "list" });
      tasks.forEach((task) => list.append(this._row(task)));
      card.append(list);
    } else {
      card.append(el("div", { class: "empty" }, t.all_good));
    }

    if (this._dialog) root.append(this._renderDialog());
  }

  _row(task) {
    const t = I18N[this.lang];
    const color = STATUS_COLORS[task.status];
    const meta = [this.lastText(task)];
    if (task.due && task.status !== "paused") meta.push(t.due_on(this.formatDate(task.due)));
    if (task.snoozed_until && task.snoozed_until === task.due) meta.push(t.snoozed(this.formatDate(task.snoozed_until)));

    const main = el("div", { class: "main" },
      el("div", { class: "name" }, task.name),
      el("div", { class: "when" }, this.whenText(task)),
      el("div", { class: "meta" }, meta.join(" · ")),
    );
    if (task.progress != null && task.status !== "paused") {
      main.append(el("div", { class: "bar", "aria-hidden": "true" }, el("div", { style: `width:${Math.round(task.progress * 100)}%` })));
    }
    const doneLabel = task.status === "unknown" ? t.done_today : t.done;
    return el("div", { class: "row", role: "listitem", style: `--c:${color}` },
      el("div", { class: "icon", "aria-hidden": "true" }, el("ha-icon", { icon: task.icon || CATEGORY_ICONS[task.category] })),
      main,
      el("div", { class: "actions" },
        task.status !== "paused" && el("button", {
          class: ["overdue", "due", "due_soon", "unknown"].includes(task.status) ? "primary" : "",
          "data-focus-key": `done-${task.id}`,
          "aria-label": `${doneLabel}: ${task.name}`,
          disabled: this._busy,
          onclick: () => this._complete(task.id, {}),
        }, el("ha-icon", { icon: "mdi:check", style: "--mdc-icon-size:18px" }), el("span", { class: "label" }, " ", doneLabel)),
        el("button", {
          class: "icon-btn", "data-focus-key": `more-${task.id}`, "aria-label": `${t.more}: ${task.name}`,
          onclick: () => this._openDetails(task.id),
        }, el("ha-icon", { icon: "mdi:dots-vertical" })),
      ),
    );
  }

  // ---- actions -----------------------------------------------------------

  async _complete(taskId, data) {
    this._busy = true;
    this._render();
    try {
      const res = await this._ws(Object.assign({ type: "bedek_bayit/task/complete", task_id: taskId }, data));
      if (!res.ok) return res.errors;
      return null;
    } catch (err) {
      return { base: "invalid" };
    } finally {
      this._busy = false;
      this._render();
    }
  }

  _task(id) { return this._data && this._data.tasks.find((x) => x.id === id); }

  _openDetails(id) { this._dialog = { kind: "details", id, form: { date: this._data.today, note: "", cost: "" }, errors: {} }; this._render(); }
  _openPicker() { this._dialog = { kind: "pick" }; this._render(); }
  _openEdit(task, template) {
    const base = task
      ? JSON.parse(JSON.stringify(task))
      : template
        ? { name: template.name, template: template.key, category: template.category, icon: template.icon, schedule: Object.assign({}, template.schedule), notes: template.notes }
        : { name: "", category: "general", icon: "mdi:wrench-outline", schedule: { type: "interval", every: 1, unit: "months" }, notes: "" };
    this._dialog = { kind: "edit", task: base, errors: {}, returnTo: task ? task.id : null };
    this._render();
  }
  _close() {
    const prev = this._dialog;
    this._dialog = null;
    this._render();
    const key = prev && (prev.id || prev.returnTo) ? `more-${prev.id || prev.returnTo}` : "add";
    const target = this.shadowRoot.querySelector(`[data-focus-key="${key}"]`);
    if (target) target.focus();
  }

  _renderDialog() {
    const d = this._dialog;
    let body;
    if (d.kind === "details") body = this._detailsDialog(d);
    else if (d.kind === "pick") body = this._pickDialog();
    else if (d.kind === "edit") body = this._editDialog(d);
    else body = this._confirmDialog(d);
    const overlay = el("div", {
      class: "overlay",
      onclick: (ev) => { if (ev.target === overlay) this._close(); },
      onkeydown: (ev) => { if (ev.key === "Escape") { ev.stopPropagation(); this._close(); } },
    }, body);
    overlay.setAttribute("dir", this.lang === "he" ? "rtl" : "ltr");
    requestAnimationFrame(() => {
      if (!this.shadowRoot.activeElement || !overlay.contains(this.shadowRoot.activeElement)) {
        const first = overlay.querySelector("[autofocus], input, select, textarea, button");
        if (first) first.focus();
      }
    });
    return overlay;
  }

  _dialogShell(title, icon, ...content) {
    return el("div", { class: "dialog", role: "dialog", "aria-modal": "true", "aria-label": title },
      el("h2", {}, icon && el("ha-icon", { icon }), title), ...content);
  }

  _detailsDialog(d) {
    const t = I18N[this.lang];
    const task = this._task(d.id);
    if (!task) { this._dialog = null; return el("div"); }
    const f = d.form;
    const errs = d.errors || {};
    const field = (key, label, input) => el("div", { class: "field" },
      el("label", { for: `c-${key}` }, label), input, el("div", { class: "err", id: `c-${key}-err`, role: "alert" }, errs[key] ? t.errors[errs[key]] || errs[key] : ""));
    const input = (key, type, extra) => {
      const node = el("input", Object.assign({
        id: `c-${key}`, "data-focus-key": `c-${key}`, type, value: f[key] ?? "", class: errs[key] ? "bad" : "",
        "aria-invalid": errs[key] ? "true" : null, "aria-describedby": `c-${key}-err`,
        oninput: (ev) => { f[key] = ev.target.value; },
      }, extra));
      return node;
    };
    const snoozeN = this._data.snooze_days;
    const history = (task.history || []).map((h, i) => el("li", {},
      el("span", {}, [this.formatDate(h.date), h.note, h.cost != null ? `₪${iso(h.cost)}` : null, h.user ? t.by(h.user) : null].filter(Boolean).join(" · ")),
      this.isAdmin && el("button", {
        class: "icon-btn", "aria-label": `${t.remove_entry}: ${h.date}`, onclick: async () => {
          await this._ws({ type: "bedek_bayit/task/delete_history", task_id: task.id, index: i });
        },
      }, el("ha-icon", { icon: "mdi:delete-outline" })),
    ));
    return this._dialogShell(task.name, task.icon,
      el("div", { class: "when", style: `--c:${STATUS_COLORS[task.status]}` }, this.whenText(task)),
      el("div", { class: "meta" }, `${this.scheduleText(task.schedule)} · ${this.lastText(task)}`),
      task.notes ? el("p", { class: "notes" }, task.notes) : null,
      el("h3", {}, t.record),
      el("form", {
        novalidate: true,
        onsubmit: async (ev) => {
          ev.preventDefault();
          const errors = {};
          if (!f.date) errors.date = "required";
          else if (f.date > this._data.today) errors.date = "future";
          if (f.cost !== "" && (isNaN(+f.cost) || +f.cost < 0)) errors.cost = "invalid";
          if (f.note.length > 500) errors.note = "too_long";
          if (Object.keys(errors).length) { d.errors = errors; this._render(); return; }
          const payload = { date: f.date };
          if (f.note) payload.note = f.note;
          if (f.cost !== "") payload.cost = +f.cost;
          const res = await this._complete(task.id, payload);
          if (res) { d.errors = res; this._render(); } else this._close();
        },
      },
        el("div", { class: "inline" },
          field("date", t.date, input("date", "date", { max: this._data.today, required: true })),
          field("cost", t.cost, input("cost", "number", { min: "0", step: "0.01", inputmode: "decimal" })),
        ),
        field("note", t.note, input("note", "text", { maxlength: "500" })),
        el("div", { class: "buttons" },
          el("button", { type: "button", onclick: async () => {
            await this._ws({ type: "bedek_bayit/task/snooze", task_id: task.id });
            this._close();
          } }, t.snooze(snoozeN)),
          el("button", { type: "submit", class: "primary", disabled: this._busy }, t.record_save),
        ),
      ),
      el("h3", {}, t.history),
      history.length ? el("ul", { class: "hist" }, history) : el("div", { class: "hint" }, t.no_history),
      el("div", { class: "buttons" },
        this.isAdmin && el("button", { class: "danger", onclick: () => { this._dialog = { kind: "confirm", id: task.id }; this._render(); } }, t.delete),
        el("span", { class: "spacer" }),
        this.isAdmin && el("button", { onclick: () => this._openEdit(task) }, t.edit),
        el("button", { onclick: () => this._close() }, t.close),
      ),
    );
  }

  _confirmDialog(d) {
    const t = I18N[this.lang];
    const task = this._task(d.id);
    return this._dialogShell(t.delete, "mdi:delete-alert-outline",
      el("p", {}, task ? `${task.name}: ${t.confirm_delete}` : t.confirm_delete),
      el("div", { class: "buttons" },
        el("button", { onclick: () => this._openDetails(d.id) }, t.cancel),
        el("button", { class: "danger", onclick: async () => {
          await this._ws({ type: "bedek_bayit/task/delete", task_id: d.id });
          this._dialog = null;
          this._render();
        } }, t.confirm_yes),
      ),
    );
  }

  _pickDialog() {
    const t = I18N[this.lang];
    const used = new Set(this._data.tasks.map((x) => x.template).filter(Boolean));
    const grid = el("div", { class: "templates" });
    this._data.categories.forEach((cat) => {
      const items = this._data.templates.filter((x) => x.category === cat);
      if (!items.length) return;
      grid.append(el("div", { class: "cat" }, t.categories[cat]));
      items.forEach((tpl) => grid.append(el("button", { class: "tpl", onclick: () => this._openEdit(null, tpl) },
        el("ha-icon", { icon: tpl.icon }),
        el("span", {}, tpl.name, el("small", {}, this.scheduleText(tpl.schedule) + (used.has(tpl.key) ? ` · ${t.already}` : ""))),
      )));
    });
    return this._dialogShell(t.new_task, "mdi:plus",
      el("div", { class: "hint" }, t.pick_template),
      el("div", { class: "buttons", style: "justify-content:flex-start" },
        el("button", { class: "primary", onclick: () => this._openEdit(null, null) }, t.custom)),
      grid,
      el("div", { class: "buttons" }, el("button", { onclick: () => this._close() }, t.cancel)),
    );
  }

  _editDialog(d) {
    const t = I18N[this.lang];
    const task = d.task;
    const s = task.schedule;
    const errs = d.errors || {};
    const errText = (key) => (errs[key] ? t.errors[errs[key]] || errs[key] : "");
    const field = (key, label, control, hint) => el("div", { class: "field" },
      el("label", { for: `f-${key}` }, label), control,
      hint ? el("div", { class: "hint" }, hint) : null,
      el("div", { class: "err", id: `f-${key}-err`, role: "alert" }, errText(key)));
    const bind = (node, key, get, set) => {
      node.id = `f-${key}`;
      node.setAttribute("data-focus-key", `f-${key}`);
      node.setAttribute("aria-describedby", `f-${key}-err`);
      if (errs[key]) { node.classList.add("bad"); node.setAttribute("aria-invalid", "true"); }
      node.value = get() ?? "";
      node.addEventListener(node.tagName === "SELECT" ? "change" : "input", (ev) => set(ev.target.value));
      return node;
    };
    const select = (key, options, get, set, rerender) => bind(
      el("select", {}, options.map(([v, label]) => el("option", { value: String(v) }, label))),
      key, () => String(get() ?? ""), (v) => { set(v); if (rerender) this._render(); });
    const number = (key, get, set, min, max) => bind(el("input", { type: "number", min: String(min), max: String(max), step: "1", inputmode: "numeric" }), key, get, set);

    const schedFields = [];
    if (s.type === "interval") {
      schedFields.push(el("div", { class: "inline" },
        field("schedule.every", t.f_every, number("schedule.every", () => s.every, (v) => { s.every = v; }, 1, 3650)),
        field("schedule.unit", t.f_unit, select("schedule.unit", Object.entries(t.units), () => s.unit, (v) => { s.unit = v; })),
      ));
    } else if (s.type === "holiday") {
      const off = +(s.offset_days || 0);
      if (!d.rel) d.rel = off < 0 ? "before" : off > 0 ? "after" : "on";
      const signed = (n) => (d.rel === "before" ? -n : d.rel === "after" ? n : 0);
      schedFields.push(el("div", { class: "inline" },
        d.rel !== "on" && field("schedule.offset_days", t.f_days, number("schedule.offset_days", () => Math.abs(off), (v) => {
          s.offset_days = v === "" ? "" : signed(Math.abs(+v));
        }, 1, 180)),
        field("rel", t.f_when, select("rel", [["before", t.before], ["after", t.after], ["on", t.on_day]], () => d.rel, (v) => {
          d.rel = v;
          s.offset_days = signed(Math.abs(+(s.offset_days || 0)) || 7);
        }, true)),
        field("schedule.holiday", t.f_holiday, select("schedule.holiday", this._data.holidays.map((h) => [h, t.holidays[h]]), () => s.holiday, (v) => { s.holiday = v; })),
      ));
    } else if (s.type === "yearly") {
      const months = Array.from({ length: 12 }, (_, i) => [i + 1, new Intl.DateTimeFormat(this.lang === "he" ? "he-IL" : "en", { month: "long" }).format(new Date(2028, i, 1))]);
      schedFields.push(el("div", { class: "inline" },
        field("schedule.day", t.f_day, number("schedule.day", () => s.day, (v) => { s.day = v; }, 1, 31)),
        field("schedule.month", t.f_month, select("schedule.month", months, () => s.month, (v) => { s.month = +v; })),
      ));
    } else {
      const listId = "f-entities";
      const candidates = Object.values(this._hass.states)
        .filter((st) => ["date", "timestamp"].includes(st.attributes.device_class) || st.entity_id.startsWith("input_datetime."))
        .map((st) => st.entity_id).sort();
      schedFields.push(
        field("schedule.entity_id", t.f_entity,
          bind(el("input", { type: "text", list: listId, dir: "ltr", autocomplete: "off" }), "schedule.entity_id", () => s.entity_id, (v) => { s.entity_id = v.trim(); }),
          t.f_entity_hint),
        el("datalist", { id: listId }, candidates.map((id) => el("option", { value: id }))),
      );
    }

    const iconPicker = customElements.get("ha-icon-picker")
      ? (() => {
          const p = el("ha-icon-picker", { id: "f-icon" });
          p.hass = this._hass;
          p.value = task.icon;
          p.addEventListener("value-changed", (ev) => { task.icon = ev.detail.value; });
          return p;
        })()
      : bind(el("input", { type: "text", dir: "ltr", placeholder: "mdi:wrench" }), "icon", () => task.icon, (v) => { task.icon = v.trim(); });

    const paused = el("input", { type: "checkbox", id: "f-paused", checked: !!task.paused, onchange: (ev) => { task.paused = ev.target.checked; } });

    const form = el("form", {
      novalidate: true,
      onsubmit: async (ev) => {
        ev.preventDefault();
        const errors = this._validate(task);
        if (Object.keys(errors).length) { d.errors = errors; this._render(); return; }
        const payload = Object.assign({}, task);
        ["history", "due", "days_left", "status", "progress", "effective_remind_days", "created", "snoozed_until"].forEach((k) => delete payload[k]);
        payload.remind_days = task.remind_days === "" || task.remind_days == null ? null : +task.remind_days;
        payload.last_done = task.last_done || null;
        const sched = Object.assign({}, task.schedule);
        ["every", "day", "month", "offset_days"].forEach((k) => { if (k in sched && sched[k] !== "") sched[k] = +sched[k]; });
        payload.schedule = sched;
        try {
          const res = await this._ws({ type: "bedek_bayit/task/save", task: payload });
          if (!res.ok) { d.errors = res.errors; this._render(); return; }
          this._dialog = null;
          this._render();
        } catch (err) {
          d.errors = { base: "invalid" };
          this._render();
        }
      },
    },
      field("name", t.f_name, bind(el("input", { type: "text", maxlength: "60", required: true, autofocus: true }), "name", () => task.name, (v) => { task.name = v; })),
      el("div", { class: "inline" },
        field("category", t.f_category, select("category", this._data.categories.map((c) => [c, t.categories[c]]), () => task.category, (v) => { task.category = v; })),
        field("icon", t.f_icon, iconPicker),
      ),
      field("schedule.type", t.f_schedule, select("schedule.type", Object.entries(t.sched), () => s.type, (v) => {
        const defaults = {
          interval: { type: "interval", every: 1, unit: "months" },
          holiday: { type: "holiday", holiday: "pesach", offset_days: -7 },
          yearly: { type: "yearly", month: 4, day: 1, offset_days: 0 },
          entity: { type: "entity", entity_id: "" },
        };
        task.schedule = defaults[v];
        d.rel = null;
      }, true)),
      schedFields,
      el("div", { class: "inline" },
        field("last_done", t.f_last_done, bind(el("input", { type: "date", max: this._data.today }), "last_done", () => task.last_done, (v) => { task.last_done = v; })),
        field("remind_days", t.f_remind_days, number("remind_days", () => task.remind_days, (v) => { task.remind_days = v; }, 0, 365), t.f_remind_hint(this._data.remind_days)),
      ),
      field("notes", t.f_notes, bind(el("textarea", { maxlength: "500" }), "notes", () => task.notes, (v) => { task.notes = v; })),
      el("div", { class: "field check" }, paused, el("label", { for: "f-paused" }, t.f_paused)),
      errs.base ? el("div", { class: "err", role: "alert" }, errText("base")) : null,
      el("div", { class: "buttons" },
        el("button", { type: "button", onclick: () => (d.returnTo ? this._openDetails(d.returnTo) : this._close()) }, t.cancel),
        el("button", { type: "submit", class: "primary" }, t.save),
      ),
    );
    return this._dialogShell(d.returnTo ? t.edit_task : t.new_task, task.icon, form);
  }

  // Client-side checks mirror the server's (the server stays authoritative).
  _validate(task) {
    const e = {};
    const s = task.schedule;
    const int = (v, lo, hi) => v !== "" && v != null && Number.isInteger(+v) && +v >= lo && +v <= hi;
    if (!String(task.name || "").trim()) e.name = "required";
    else if (task.name.trim().length > 60) e.name = "too_long";
    if (s.type === "interval") {
      const max = { days: 3650, weeks: 520, months: 240, years: 20 }[s.unit];
      if (!int(s.every, 1, max)) e["schedule.every"] = "invalid";
    } else if (s.type === "holiday") {
      if (!int(s.offset_days, -180, 180)) e["schedule.offset_days"] = "invalid";
    } else if (s.type === "yearly") {
      const days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][(+s.month || 1) - 1];
      if (!int(s.day, 1, days)) e["schedule.day"] = "invalid";
    } else if (!/^(sensor|input_datetime|date|datetime)\.[a-z0-9_]+$/.test(s.entity_id || "")) {
      e["schedule.entity_id"] = "invalid";
    }
    if (task.last_done && task.last_done > this._data.today) e.last_done = "future";
    if (task.remind_days !== "" && task.remind_days != null && !int(task.remind_days, 0, 365)) e.remind_days = "invalid";
    if ((task.notes || "").length > 500) e.notes = "too_long";
    return e;
  }
}

class BedekBayitCardEditor extends HTMLElement {
  setConfig(config) { this._config = Object.assign({}, config); this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }

  _t(key) {
    const lang = this._hass && this._hass.language && this._hass.language.startsWith("he") ? "he" : "en";
    return I18N[lang][key];
  }

  _render() {
    if (!this._config || !this._hass) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (field) => this._t(`e_${field.name}`);
      this._form.addEventListener("value-changed", (ev) => {
        const value = Object.assign({}, ev.detail.value);
        Object.keys(value).forEach((k) => {
          if (value[k] === "" || value[k] == null || (Array.isArray(value[k]) && !value[k].length)) delete value[k];
        });
        this._config = value;
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: value }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    const cats = this._t("categories");
    this._form.hass = this._hass;
    this._form.schema = [
      { name: "title", selector: { text: {} } },
      { name: "attention_only", selector: { boolean: {} } },
      { name: "limit", selector: { number: { min: 0, max: 50, mode: "box" } } },
      { name: "categories", selector: { select: { multiple: true, options: Object.entries(cats).map(([value, label]) => ({ value, label })) } } },
      { name: "show_add", selector: { boolean: {} } },
    ];
    this._form.data = Object.assign({ attention_only: false, show_add: true, limit: 0 }, this._config);
  }
}

if (!customElements.get("bedek-bayit-card-editor")) {
  customElements.define("bedek-bayit-card-editor", BedekBayitCardEditor);
}
if (!customElements.get("bedek-bayit-card")) {
  customElements.define("bedek-bayit-card", BedekBayitCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "bedek-bayit-card",
    name: "Bedek Bayit",
    description: "Household maintenance: last done / next due, Israel flavor.",
    preview: false,
    documentationURL: "https://github.com/bareli/bedek_bayit",
  });
}
