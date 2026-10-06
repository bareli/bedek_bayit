/* Bedek Bayit sidebar panel: the card, full page, with a toolbar. */
// Same ?v= cache-buster as this module, so the card never loads stale.
await import(new URL(`./card.js${new URL(import.meta.url).search}`, import.meta.url).href);

class BedekBayitPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = `
      :host { display: block; min-height: 100vh; background: var(--primary-background-color); }
      .toolbar { display: flex; align-items: center; height: var(--header-height, 56px); padding: 0 12px; gap: 8px;
                 background: var(--app-header-background-color, var(--primary-color));
                 color: var(--app-header-text-color, var(--text-primary-color, #fff)); font-size: 20px; }
      .content { max-width: 760px; margin: 0 auto; padding: 16px; box-sizing: border-box; }
    `;
    this._menu = document.createElement("ha-menu-button");
    this._title = document.createElement("div");
    const toolbar = document.createElement("div");
    toolbar.className = "toolbar";
    toolbar.append(this._menu, this._title);
    this._card = document.createElement("bedek-bayit-card");
    this._card.setConfig({ show_add: true });
    const content = document.createElement("div");
    content.className = "content";
    content.append(this._card);
    this.shadowRoot.append(style, toolbar, content);
  }

  connectedCallback() {
    // Home Assistant may set these before this element upgrades (the card import above delays
    // define): own properties would shadow the setters, so re-apply them through the setters.
    for (const prop of ["hass", "narrow", "panel"]) {
      if (Object.prototype.hasOwnProperty.call(this, prop)) {
        const value = this[prop];
        delete this[prop];
        this[prop] = value;
      }
    }
  }

  set hass(hass) {
    this._hass = hass;
    this._menu.hass = hass;
    const he = (hass.language || "").startsWith("he");
    this._title.textContent = he ? "בדק בית" : "Bedek Bayit";
    this.shadowRoot.host.setAttribute("dir", he ? "rtl" : "ltr");
    this._card.hass = hass;
  }

  set narrow(narrow) { this._menu.narrow = narrow; }
  set panel(_panel) {}
}

if (!customElements.get("bedek-bayit-panel")) customElements.define("bedek-bayit-panel", BedekBayitPanel);
