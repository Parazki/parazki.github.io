// Stromfresser-Check – App-Logik. Läuft komplett im Browser und sendet nichts.
// Formeln identisch mit build.py (jahresverbrauch_kwh, bkw_rechnung).
(() => {
  "use strict";
  const SF = window.SF || { geraete: [], preis: 0.35, schnitt: {}, vorlage: [], solar: [] };
  const body = document.body;
  const ROOT = body.dataset.root || "./";
  const STANDARD_PREIS = parseFloat(body.dataset.preis) || SF.preis || 0.35;
  const STUNDEN_JAHR = 8760;
  const nachSlug = Object.fromEntries(SF.geraete.map((g) => [g.s, g]));
  const $ = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => Array.from(el.querySelectorAll(sel));

  // ------------------------------------------------ Speicher (nur lokal im Browser)
  const lies = (k, d) => { try { const v = localStorage.getItem("sf:" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } };
  const schreib = (k, v) => { try { localStorage.setItem("sf:" + k, JSON.stringify(v)); } catch (e) { /* privat/gesperrt */ } };
  const loesche = (k) => { try { localStorage.removeItem("sf:" + k); } catch (e) { /* egal */ } };

  // ------------------------------------------------ Formatierung & Formeln
  const zahl = (x, st = 0) => x.toLocaleString("de-DE", { minimumFractionDigits: st, maximumFractionDigits: st });
  const euro = (x) => (x < 100 ? zahl(x, 2) : zahl(x, 0)) + " €";
  const dauer = (h) => (h < 1 ? Math.round(h * 60) + " min" : zahl(h, h % 1 ? 1 : 0) + " h");
  const kwhJahr = (w, h, n, wj, sb) => {
    const nutz = Math.min(h * n * wj, STUNDEN_JAHR);
    return (w * nutz + sb * (STUNDEN_JAHR - nutz)) / 1000;
  };
  const standbyKwh = (h, n, wj, sb) => sb * (STUNDEN_JAHR - Math.min(h * n * wj, STUNDEN_JAHR)) / 1000;
  const geraetKwh = (g) => kwhJahr(g.w, g.h, g.nw, g.wj, g.sb);
  const preis = () => { const p = parseFloat(lies("preis", NaN)); return p > 0 && p < 5 ? p : STANDARD_PREIS; };
  const normal = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ß/g, "ss");
  const vibriere = (muster) => { try { if (navigator.vibrate) navigator.vibrate(muster); } catch (e) { /* egal */ } };
  // Besucherstatistik (Umami, ohne Cookies) – nur aktiv, wenn in config.json eine Website-ID steht
  const zaehle = (name, daten) => { try { if (window.umami && window.umami.track) window.umami.track(name, daten); } catch (e) { /* egal */ } };
  document.addEventListener("click", (ev) => {
    const link = ev.target.closest('a[href*="amazon.de"]');
    if (!link) return;
    const karte = link.closest(".produkt");
    zaehle("amazon-klick", { produkt: karte ? $("h3", karte).textContent : link.textContent, seite: location.pathname });
  });

  // Sanfter Zahlenwechsel für große Ergebniswerte
  function zeigeZahl(el, wert, format) {
    if (!el) return;
    const start = typeof el._wert === "number" ? el._wert : null;
    el._wert = wert;
    if (start === null || matchMedia("(prefers-reduced-motion: reduce)").matches || Math.abs(start - wert) < 0.005) {
      el.textContent = format(wert);
      return;
    }
    const t0 = performance.now();
    const schritt = (t) => {
      const p = Math.min(1, (t - t0) / 380);
      const k = 1 - Math.pow(1 - p, 3);
      if (el._wert !== wert) return;
      el.textContent = format(start + (wert - start) * k);
      if (p < 1) requestAnimationFrame(schritt);
    };
    requestAnimationFrame(schritt);
  }

  // ------------------------------------------------ Snackbar
  let snackTimer;
  function snackbar(text, aktion) {
    const el = $(".snackbar");
    if (!el) return;
    $(".snackbar-text", el).textContent = text;
    const a = $(".snackbar-aktion", el);
    a.hidden = !aktion;
    a.onclick = null;
    if (aktion) {
      a.textContent = aktion.text;
      a.href = aktion.href || "#";
      if (aktion.fn) a.onclick = (ev) => { ev.preventDefault(); aktion.fn(); el.classList.remove("sichtbar"); body.classList.remove("snack-offen"); };
    }
    el.classList.add("sichtbar");
    body.classList.add("snack-offen");
    clearTimeout(snackTimer);
    snackTimer = setTimeout(() => { el.classList.remove("sichtbar"); body.classList.remove("snack-offen"); }, 4500);
  }

  // ------------------------------------------------ Ripple & App-Leiste
  document.addEventListener("pointerdown", (ev) => {
    const ziel = ev.target.closest(".ripple");
    if (!ziel || ziel.disabled) return;
    const r = ziel.getBoundingClientRect();
    const d = Math.max(r.width, r.height) * 2.2;
    const w = document.createElement("span");
    w.className = "welle";
    w.style.cssText = `width:${d}px;height:${d}px;left:${ev.clientX - r.left - d / 2}px;top:${ev.clientY - r.top - d / 2}px`;
    ziel.appendChild(w);
    setTimeout(() => w.remove(), 600);
  });

  const appbar = $(".appbar");
  const fab = $(".fab");
  let letzteY = scrollY;
  addEventListener("scroll", () => {
    const y = scrollY;
    if (appbar) appbar.classList.toggle("gescrollt", y > 4);
    if (fab) fab.classList.toggle("versteckt", y > letzteY + 4 && y > 200);
    if (fab && y < letzteY - 4) fab.classList.remove("versteckt");
    letzteY = y;
  }, { passive: true });

  // ------------------------------------------------ Strompreis (global)
  function setzePreis(p) {
    if (p > 0 && p < 5) schreib("preis", p); else loesche("preis");
    aktualisiereAlles();
  }
  const dialog = $("#preis-dialog");
  $$("[data-preis-oeffnen]").forEach((b) => b.addEventListener("click", () => {
    if (!dialog || !dialog.showModal) { const p = prompt("Dein Strompreis in €/kWh", String(preis())); if (p) setzePreis(parseFloat(p.replace(",", "."))); return; }
    dialog.querySelector("input").value = preis();
    dialog.showModal();
  }));
  if (dialog) dialog.addEventListener("close", () => {
    if (dialog.returnValue === "ok") {
      setzePreis(parseFloat(String(dialog.querySelector("input").value).replace(",", ".")));
      zaehle("strompreis-geaendert");
      snackbar(`Strompreis: ${zahl(preis(), 2)} €/kWh – alle Kosten aktualisiert`);
    } else if (dialog.returnValue === "standard") {
      setzePreis(NaN);
      snackbar(`Standardpreis ${zahl(STANDARD_PREIS, 2)} €/kWh wiederhergestellt`);
    }
  });

  function aktualisiereAlles() {
    const p = preis();
    $$("[data-euro-kwh]").forEach((el) => { el.textContent = euro(parseFloat(el.dataset.euroKwh) * p / (parseFloat(el.dataset.teiler) || 1)); });
    $$("[data-preis-anzeige]").forEach((el) => { el.textContent = zahl(p, 2) + " €/kWh"; });
    $$('form[data-rechner] input[name="preis"]').forEach((el) => { if (document.activeElement !== el) el.value = p; });
    rechner.forEach((r) => r.rechne());
    if (haushalt) haushalt.render();
  }

  // ------------------------------------------------ Schieberegler <-> Zahlenfelder
  const anzeigeText = {
    stunden: (v) => dauer(v),
    nutzungen: (v) => (v === 7 ? "täglich" : v === 14 ? "2 × täglich" : zahl(v) + " × pro Woche"),
    wochen: (v) => (v >= 52 ? "ganzjährig" : zahl(v) + " Wochen"),
    modul: (v) => zahl(v) + " Wp",
    eigen: (v) => zahl(v) + " %",
    kosten: (v) => zahl(v) + " €",
  };
  function setzeSchieberFarbe(s) {
    const min = parseFloat(s.min) || 0, max = parseFloat(s.max) || 100;
    s.style.setProperty("--wert", ((parseFloat(s.value) - min) / (max - min || 1)) * 100 + "%");
  }
  function verbindeRegler(form, beiAenderung) {
    $$(".schieber[data-fuer]", form).forEach((s) => {
      const feld = form.elements[s.dataset.fuer];
      const anzeige = $(`[data-anzeige="${s.dataset.fuer}"]`, form);
      const zeige = () => { if (anzeige && anzeigeText[s.dataset.fuer]) anzeige.textContent = anzeigeText[s.dataset.fuer](parseFloat(feld.value) || 0); };
      s.addEventListener("input", () => { feld.value = s.value; setzeSchieberFarbe(s); zeige(); beiAenderung(); });
      feld.addEventListener("input", () => {
        const v = parseFloat(feld.value) || 0;
        if (v > parseFloat(s.max)) s.max = Math.ceil(v * 1.5);
        s.value = v; setzeSchieberFarbe(s); zeige();
      });
      s._sync = () => { s.value = feld.value; setzeSchieberFarbe(s); zeige(); };
      s._sync();
    });
  }
  const wert = (form, name) => {
    const el = form.elements[name];
    if (!el) return 0;
    const v = parseFloat(String(el.value).replace(",", "."));
    return isFinite(v) && v > 0 ? v : 0;
  };

  async function teilen(titel, text) {
    const url = location.href.split("#")[0];
    zaehle("teilen", { seite: location.pathname });
    try {
      if (navigator.share) { await navigator.share({ title: titel, text, url }); return; }
      await navigator.clipboard.writeText(text + " " + url);
      snackbar("Text und Link kopiert – jetzt einfügen und teilen");
    } catch (e) { /* abgebrochen */ }
  }

  // ------------------------------------------------ Geräte-Rechner
  const rechner = [];
  $$('form[data-rechner="geraet"]').forEach((form) => {
    const start = Object.fromEntries($$("input[name]", form).map((i) => [i.name, i.value]));
    const aus = (k) => $(`[data-aus="${k}"]`, form);
    const balken = $("[data-aus-balken]", form);
    const standbyChip = $("[data-standby-chip]", form);
    const g = nachSlug[form.dataset.slug];
    const werte = () => ({ w: wert(form, "leistung"), h: wert(form, "stunden"), n: wert(form, "nutzungen"), wj: wert(form, "wochen"), sb: wert(form, "standby") });
    const r = {
      rechne() {
        const v = werte();
        const kwh = kwhJahr(v.w, v.h, v.n, v.wj, v.sb);
        const sbKwh = standbyKwh(v.h, v.n, v.wj, v.sb);
        const p = preis();
        zeigeZahl(aus("euro_jahr"), kwh * p, euro);
        aus("euro_monat").textContent = euro(kwh * p / 12);
        aus("kwh_jahr").textContent = zahl(kwh) + " kWh";
        aus("euro_standby").textContent = euro(sbKwh * p);
        if (standbyChip) standbyChip.hidden = sbKwh <= 0;
        const anteil = Math.min(100, kwh / (SF.schnitt[2] || 2500) * 100);
        aus("anteil").textContent = zahl(anteil, 1) + " %";
        if (balken) balken.style.width = anteil + "%";
        r.kwh = kwh;
      },
      werte,
    };
    verbindeRegler(form, () => r.rechne());
    form.addEventListener("input", (ev) => {
      if (ev.target.name === "preis") { setzePreis(wert(form, "preis")); return; }
      r.rechne();
    });
    const reset = $("[data-zuruecksetzen]", form);
    if (reset) reset.addEventListener("click", () => {
      Object.entries(start).forEach(([k, v]) => { if (k !== "preis") form.elements[k].value = v; });
      $$(".schieber[data-fuer]", form).forEach((s) => s._sync());
      r.rechne();
    });
    const teil = $("[data-teilen]", form);
    if (teil) teil.addEventListener("click", () => {
      const name = g ? `${g.e} ${g.n}` : "⚡ Mein Gerät";
      teilen(document.title, `${name}: ${euro(r.kwh * preis())} Stromkosten im Jahr (${zahl(r.kwh)} kWh). Rechne selbst nach:`);
    });
    r.rechne();
    rechner.push(r);

    // „Zu meinem Haushalt“ übernimmt die aktuellen Werte dieses Rechners
    const fabKnopf = $(`[data-zum-haushalt="${form.dataset.slug}"]`);
    if (fabKnopf && g) fabKnopf.addEventListener("click", () => {
      const v = werte();
      const liste = lies("haushalt", []);
      const eintrag = liste.find((x) => x.s === g.s);
      if (eintrag) { Object.assign(eintrag, v); eintrag.m += 1; } else liste.push({ s: g.s, ...v, m: 1 });
      schreib("haushalt", liste);
      vibriere(20);
      zaehle("haushalt-hinzugefuegt", { geraet: g.s, quelle: "geraeteseite" });
      snackbar(`${g.n} zu deinem Haushalt hinzugefügt${eintrag ? ` (jetzt ${eintrag.m} ×)` : ""}`, { text: "Ansehen", href: ROOT + "haushalt/" });
    });
  });

  // ------------------------------------------------ Balkonkraftwerk
  $$('form[data-rechner="bkw"]').forEach((form) => {
    const aus = (k) => $(`[data-aus="${k}"]`, form);
    const monatsWerte = $$("[data-bkw-monat]");
    const r = {
      rechne() {
        const kwp = Math.min(wert(form, "modul"), wert(form, "wr") * 1.15) / 1000;
        const ertrag = kwp * wert(form, "region") * wert(form, "ausrichtung") * wert(form, "montage");
        const eigen = Math.min(wert(form, "eigen"), 100) / 100;
        const ersparnis = ertrag * eigen * preis();
        const kosten = wert(form, "kosten");
        zeigeZahl(aus("ersparnis"), ersparnis, euro);
        aus("ertrag").textContent = zahl(ertrag) + " kWh";
        aus("eigen_kwh").textContent = zahl(ertrag * eigen) + " kWh";
        aus("amort").textContent = ersparnis > 0 ? zahl(kosten / ersparnis, 1) + " Jahren" : "–";
        monatsWerte.forEach((el) => { el.textContent = zahl(ertrag * (SF.solar[+el.dataset.bkwMonat] || 0) / 100); });
        r.ersparnis = ersparnis; r.ertrag = ertrag;
      },
    };
    verbindeRegler(form, () => r.rechne());
    form.addEventListener("input", (ev) => {
      if (ev.target.name === "preis") { setzePreis(wert(form, "preis")); return; }
      r.rechne();
    });
    form.addEventListener("change", () => r.rechne());
    const teil = $("[data-teilen]", form);
    if (teil) teil.addEventListener("click", () =>
      teilen(document.title, `☀️ Mein Balkonkraftwerk erzeugt ca. ${zahl(r.ertrag)} kWh und spart rund ${euro(r.ersparnis)} im Jahr. Rechne selbst nach:`));
    r.rechne();
    rechner.push(r);
  });

  // ------------------------------------------------ Geräteübersicht: Suche, Filter, Sortierung
  const liste = $("[data-geraete-liste]");
  if (liste) {
    const karten = $$(".geraet-karte", liste);
    const suche = $("[data-geraete-suche]");
    const chips = $$("[data-kat-filter]");
    const treffer = $("[data-treffer]");
    const leer = $("[data-leer]");
    const params = new URLSearchParams(location.search);
    let kat = params.get("kat") || "";
    if (params.get("q")) suche.value = params.get("q");
    const filtere = () => {
      const q = normal(suche.value.trim());
      let n = 0;
      karten.forEach((k) => {
        const passt = (!kat || k.dataset.kat === kat) && (!q || normal(k.dataset.name).includes(q));
        k.hidden = !passt;
        if (passt) n++;
      });
      chips.forEach((c) => c.setAttribute("aria-pressed", String(c.dataset.katFilter === kat)));
      treffer.textContent = n === 1 ? "1 Gerät" : `${n} Geräte`;
      leer.hidden = n > 0;
      const u = new URL(location.href);
      if (kat) u.searchParams.set("kat", kat); else u.searchParams.delete("kat");
      if (q) u.searchParams.set("q", suche.value.trim()); else u.searchParams.delete("q");
      history.replaceState(null, "", u);
    };
    const sortiere = (art) => {
      const sortiert = karten.slice().sort((a, b) => (art === "name"
        ? a.dataset.name.localeCompare(b.dataset.name, "de")
        : parseFloat(b.dataset.kwh) - parseFloat(a.dataset.kwh)));
      sortiert.forEach((k) => liste.appendChild(k));
    };
    suche.addEventListener("input", filtere);
    chips.forEach((c) => c.addEventListener("click", () => { kat = c.dataset.katFilter; filtere(); }));
    $$('input[name="sortierung"]').forEach((r) => r.addEventListener("change", () => sortiere(r.value)));
    filtere();
    if (location.hash === "#suche") setTimeout(() => suche.focus(), 50);
  }

  // ------------------------------------------------ Mein Haushalt
  const FARBEN = ["var(--primary)", "var(--tertiary)", "#4F86C6", "#B4579B", "#7E6CD6", "var(--outline)"];
  const hhEl = $("[data-haushalt]");
  const haushalt = hhEl ? (() => {
    const hh = (k) => $(`[data-hh="${k}"]`, hhEl);
    const listeEl = $("[data-hh-liste]", hhEl);
    const suche = $("[data-hh-suche]", hhEl);
    const vorschlaege = $("[data-hh-vorschlaege]", hhEl);
    let personen = lies("personen", 2);
    const radio = $(`input[name="personen"][value="${personen}"]`, hhEl);
    if (radio) radio.checked = true;

    const laden = () => lies("haushalt", []).filter((x) => nachSlug[x.s]);
    const speichern = (l) => schreib("haushalt", l);
    const eintragKwh = (x) => kwhJahr(x.w, x.h, x.n, x.wj, x.sb) * (x.m || 1);
    const ausGeraet = (g) => ({ s: g.s, w: g.w, h: g.h, n: g.nw, wj: g.wj, sb: g.sb, m: 1 });

    function hinzufuegen(slug) {
      const l = laden();
      const vorhanden = l.find((x) => x.s === slug);
      if (vorhanden) vorhanden.m += 1; else l.push(ausGeraet(nachSlug[slug]));
      speichern(l);
      vibriere(15);
      zaehle("haushalt-hinzugefuegt", { geraet: slug, quelle: "haushalt" });
      suche.value = "";
      vorschlaege.innerHTML = "";
      render();
      snackbar(`${nachSlug[slug].n} hinzugefügt`);
    }

    function zeigeVorschlaege() {
      const q = normal(suche.value.trim());
      vorschlaege.innerHTML = "";
      if (!q) return;
      const p = preis();
      // Treffer am Namensanfang zuerst, dann im Namen, zuletzt nur über den Bereich
      const rang = (g) => { const n = normal(g.n); return n.startsWith(q) ? 0 : n.includes(q) ? 1 : normal(g.k).includes(q) ? 2 : 3; };
      SF.geraete.filter((g) => rang(g) < 3).sort((a, b) => rang(a) - rang(b)).slice(0, 6).forEach((g) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "vorschlag ripple";
        b.innerHTML = `<span class="emoji-kreis" aria-hidden="true">${g.e}</span><span>${g.n}</span><small>${euro(geraetKwh(g) * p)} / Jahr</small>`;
        b.addEventListener("click", () => hinzufuegen(g.s));
        vorschlaege.appendChild(b);
      });
      if (!vorschlaege.children.length) vorschlaege.innerHTML = '<p class="unterzeile">Nichts gefunden – probier einen anderen Begriff.</p>';
    }
    suche.addEventListener("input", zeigeVorschlaege);
    suche.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") { ev.preventDefault(); const erster = $(".vorschlag", vorschlaege); if (erster) erster.click(); }
    });

    $("[data-hh-vorlage]", hhEl).addEventListener("click", () => {
      const l = laden();
      let neu = 0;
      SF.vorlage.forEach(([slug, m]) => {
        if (nachSlug[slug] && !l.some((x) => x.s === slug)) { l.push({ ...ausGeraet(nachSlug[slug]), m }); neu++; }
      });
      speichern(l);
      render();
      zaehle("haushalt-vorlage");
      snackbar(neu ? `${neu} typische Geräte hinzugefügt – passe die Anzahl an` : "Die typischen Geräte sind schon in deiner Liste");
    });
    const leeren = $("[data-hh-leeren]", hhEl);
    leeren.addEventListener("click", () => {
      const sicherung = laden();
      speichern([]);
      render();
      snackbar("Liste geleert", { text: "Rückgängig", fn: () => { speichern(sicherung); render(); } });
    });
    $$('input[name="personen"]', hhEl).forEach((r) => r.addEventListener("change", () => { personen = +r.value; schreib("personen", personen); render(); }));

    function aendereMenge(slug, delta) {
      const l = laden();
      const i = l.findIndex((x) => x.s === slug);
      if (i < 0) return;
      const vorher = { ...l[i] };
      l[i].m += delta;
      if (l[i].m <= 0) {
        l.splice(i, 1);
        speichern(l);
        render();
        snackbar(`${nachSlug[slug].n} entfernt`, { text: "Rückgängig", fn: () => { const l2 = laden(); l2.splice(i, 0, vorher); speichern(l2); render(); } });
        return;
      }
      speichern(l);
      render();
    }

    function donut(teile, gesamt) {
      const svg = $("[data-hh-donut]", hhEl);
      const r = 52, u = 2 * Math.PI * r;
      let versatz = 0;
      svg.innerHTML = `<circle cx="60" cy="60" r="${r}" style="stroke:var(--surface-highest)"></circle>` + teile.map((t, i) => {
        const laenge = gesamt > 0 ? t.kwh / gesamt * u : 0;
        const kreis = `<circle cx="60" cy="60" r="${r}" style="stroke:${FARBEN[i]}" stroke-dasharray="${Math.max(0, laenge - 2)} ${u}" stroke-dashoffset="${-versatz}"></circle>`;
        versatz += laenge;
        return kreis;
      }).join("");
    }

    function render() {
      const l = laden();
      const p = preis();
      const gesamtKwh = l.reduce((s, x) => s + eintragKwh(x), 0);
      zeigeZahl(hh("euro_jahr"), gesamtKwh * p, euro);
      hh("euro_monat").textContent = euro(gesamtKwh * p / 12);
      hh("kwh_jahr").textContent = zahl(gesamtKwh) + " kWh";
      hh("anzahl").textContent = zahl(l.reduce((s, x) => s + x.m, 0));
      const schnitt = SF.schnitt[personen] || 2500;
      const anteil = gesamtKwh / schnitt * 100;
      $("[data-hh-balken]", hhEl).style.width = Math.min(100, anteil) + "%";
      hh("vergleich").textContent = l.length
        ? `Deine erfassten Geräte: ${zahl(anteil)} % des typischen Verbrauchs eines ${personen === 5 ? "5+" : personen}-Personen-Haushalts (ca. ${zahl(schnitt)} kWh im Jahr).`
        : "Füge Geräte hinzu, um dich mit einem Durchschnittshaushalt zu vergleichen.";

      const leerEl = $("[data-hh-leer]", hhEl);
      leerEl.hidden = l.length > 0;
      leeren.hidden = !l.length;
      ["[data-hh-diagramm]", "[data-hh-listen-abschnitt]", "[data-hh-tipps-abschnitt]"].forEach((s) => { $(s, hhEl).hidden = !l.length; });
      if (!l.length) { listeEl.innerHTML = ""; return; }

      const sortiert = l.map((x) => ({ x, g: nachSlug[x.s], kwh: eintragKwh(x) })).sort((a, b) => b.kwh - a.kwh);
      // Diagramm: Top 5 + Rest
      const teile = sortiert.slice(0, 5).map((t) => ({ name: t.g.n, emoji: t.g.e, kwh: t.kwh }));
      const rest = sortiert.slice(5).reduce((s, t) => s + t.kwh, 0);
      if (rest > 0) teile.push({ name: "Alle anderen", emoji: "➕", kwh: rest });
      donut(teile, gesamtKwh);
      $("[data-hh-legende]", hhEl).innerHTML = teile.map((t, i) =>
        `<li><i style="background:${FARBEN[i]}"></i><span>${t.emoji} ${t.name}</span><b>${zahl(gesamtKwh ? t.kwh / gesamtKwh * 100 : 0)} %</b></li>`).join("");

      listeEl.innerHTML = "";
      sortiert.forEach(({ x, g, kwh }) => {
        const li = document.createElement("li");
        li.className = "hh-eintrag";
        li.innerHTML = `<span class="emoji-kreis" aria-hidden="true">${g.e}</span>
          <span class="hh-name"><a href="${ROOT}geraet/${g.s}/">${g.n}</a><small>${zahl(kwh)} kWh · ${euro(kwh * p)} / Jahr</small></span>
          <span class="stepper"><button type="button" aria-label="Weniger" data-d="-1"><svg class="ic"><use href="#i-${x.m > 1 ? "minus" : "trash"}"/></svg></button>
          <output>${x.m}</output><button type="button" aria-label="Mehr" data-d="1"><svg class="ic"><use href="#i-plus"/></svg></button></span>`;
        $$("button[data-d]", li).forEach((b) => b.addEventListener("click", () => aendereMenge(g.s, +b.dataset.d)));
        listeEl.appendChild(li);
      });

      $("[data-hh-tipps]", hhEl).innerHTML = sortiert.slice(0, 3).map(({ g, kwh }) =>
        `<div class="tipp-karte"><h3>${g.e} ${g.n} · ${euro(kwh * p)} / Jahr</h3><p>${g.t}</p>
         <p><a href="${ROOT}geraet/${g.s}/">Zum Rechner und allen Tipps →</a></p></div>`).join("");
    }
    render();
    return { render };
  })() : null;

  // ------------------------------------------------ Quiz
  const quizEl = $("[data-quiz]");
  if (quizEl) {
    const RUNDEN = 10;
    const q = (k) => $(`[data-quiz="${k}"]`, quizEl);
    const optionen = $("[data-quiz-optionen]", quizEl);
    const aufloesung = $("[data-quiz-aufloesung]", quizEl);
    const ende = $("[data-quiz-ende]", quizEl);
    const spiel = $$(".quiz-kopf, .fortschritt, .quiz-frage, [data-quiz-optionen]", quizEl);
    let runde, punkte, paare;

    const mischen = (a) => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
    function erzeugePaare() {
      const ergebnis = [];
      const benutzt = new Set();
      let versuche = 0;
      while (ergebnis.length < RUNDEN && versuche++ < 2000) {
        const [a, b] = mischen(SF.geraete.slice()).slice(0, 2);
        const ka = geraetKwh(a), kb = geraetKwh(b);
        const faktor = Math.max(ka, kb) / Math.max(0.01, Math.min(ka, kb));
        if (faktor < 1.35 || benutzt.has(a.s) || benutzt.has(b.s)) continue;
        benutzt.add(a.s); benutzt.add(b.s);
        ergebnis.push([a, b]);
        if (benutzt.size > SF.geraete.length - 2) benutzt.clear();
      }
      return ergebnis;
    }
    function zeigeRunde() {
      const [a, b] = paare[runde];
      q("runde").textContent = `Runde ${runde + 1} von ${RUNDEN}`;
      q("punkte").textContent = punkte;
      $("[data-quiz-fortschritt]", quizEl).style.width = (runde / RUNDEN * 100) + "%";
      aufloesung.hidden = true;
      optionen.innerHTML = "";
      [a, b].forEach((g) => {
        const knopf = document.createElement("button");
        knopf.type = "button";
        knopf.className = "quiz-option ripple";
        knopf.innerHTML = `<span class="qo-emoji" aria-hidden="true">${g.e}</span><span class="qo-name">${g.n}</span><span class="qo-kosten">${euro(geraetKwh(g) * preis())}</span>`;
        knopf.addEventListener("click", () => antworte(g, a, b));
        optionen.appendChild(knopf);
      });
    }
    function antworte(wahl, a, b) {
      const [teuer, guenstig] = geraetKwh(a) >= geraetKwh(b) ? [a, b] : [b, a];
      const richtig = wahl === teuer;
      if (richtig) punkte++;
      vibriere(richtig ? 30 : [60, 40, 60]);
      $$(".quiz-option", optionen).forEach((k, i) => {
        const g = i === 0 ? a : b;
        k.disabled = true;
        k.classList.add("aufgedeckt");
        if (g === teuer) k.classList.add("richtig");
        if (g === wahl && !richtig) k.classList.add("falsch");
      });
      q("punkte").textContent = punkte;
      const p = preis();
      const faktor = geraetKwh(teuer) / Math.max(0.01, geraetKwh(guenstig));
      q("aufloesung").innerHTML = `<b>${richtig ? "Richtig! 🎉" : "Knapp daneben!"}</b> ${teuer.a === "eine" ? "Eine" : "Ein"} ${teuer.nm} kostet typischerweise rund <b>${euro(geraetKwh(teuer) * p)}</b> im Jahr, ` +
        `${guenstig.a} ${guenstig.nm} etwa <b>${euro(geraetKwh(guenstig) * p)}</b> – ${faktor >= 2 ? "rund " + zahl(faktor) + "-mal so viel" : "deutlich mehr"}.`;
      aufloesung.hidden = false;
      $("[data-quiz-weiter]", quizEl).textContent = runde + 1 < RUNDEN ? "Weiter" : "Ergebnis ansehen";
    }
    function zeigeEnde() {
      spiel.forEach((el) => { el.hidden = true; });
      aufloesung.hidden = true;
      ende.hidden = false;
      const rekord = Math.max(lies("quizrekord", 0), punkte);
      schreib("quizrekord", rekord);
      q("ergebnis").textContent = `${punkte} von ${RUNDEN}`;
      q("emoji").textContent = punkte >= 9 ? "🏆" : punkte >= 7 ? "🥇" : punkte >= 5 ? "👍" : "🔌";
      q("spruch").textContent = punkte >= 9 ? "Stromfresser-Profi! Dir macht keiner was vor."
        : punkte >= 7 ? "Sehr gut – du hast ein starkes Gefühl für Stromkosten."
        : punkte >= 5 ? "Nicht schlecht! Ein paar Überraschungen waren dabei."
        : "Stromkosten sind tückisch – genau deshalb lohnt sich der Check.";
      q("rekord").textContent = `Dein Rekord: ${rekord} von ${RUNDEN}`;
      zaehle("quiz-beendet", { punkte });
      vibriere([40, 60, 40]);
    }
    function neuesSpiel() {
      runde = 0; punkte = 0; paare = erzeugePaare();
      spiel.forEach((el) => { el.hidden = false; });
      ende.hidden = true;
      zeigeRunde();
    }
    $("[data-quiz-weiter]", quizEl).addEventListener("click", () => {
      runde++;
      if (runde < RUNDEN) zeigeRunde(); else zeigeEnde();
      quizEl.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    $("[data-quiz-neu]", quizEl).addEventListener("click", neuesSpiel);
    $("[data-quiz-teilen]", quizEl).addEventListener("click", () =>
      teilen("Stromfresser-Quiz", `⚡ Ich habe ${punkte} von ${RUNDEN} im Stromfresser-Quiz geschafft. Schaffst du mehr?`));
    neuesSpiel();
  }

  // ------------------------------------------------ Installierbare App (PWA)
  let installEvent = null;
  const installElemente = () => $$("[data-installieren], [data-install-karte]");
  addEventListener("beforeinstallprompt", (ev) => {
    ev.preventDefault();
    installEvent = ev;
    installElemente().forEach((el) => { el.hidden = false; });
  });
  $$("[data-installieren], [data-installieren-karte]").forEach((b) => b.addEventListener("click", async () => {
    if (!installEvent) return;
    installEvent.prompt();
    await installEvent.userChoice.catch(() => null);
    installEvent = null;
    installElemente().forEach((el) => { el.hidden = true; });
  }));
  addEventListener("appinstalled", () => {
    zaehle("app-installiert");
    installElemente().forEach((el) => { el.hidden = true; });
    snackbar("Installiert! Du findest den Stromfresser-Check jetzt auf deinem Startbildschirm.");
  });
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
    addEventListener("load", () => navigator.serviceWorker.register(ROOT + "sw.js").catch(() => null));
  }

  aktualisiereAlles();
})();
