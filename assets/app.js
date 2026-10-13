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
  const BEWEGUNG_AUS = matchMedia("(prefers-reduced-motion: reduce)").matches;
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
  const vibriere = (muster) => {
    try { if (navigator.vibrate && (!navigator.userActivation || navigator.userActivation.hasBeenActive)) navigator.vibrate(muster); } catch (e) { /* egal */ }
  };
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
    const erstes = typeof el._wert !== "number";
    const start = erstes ? 0 : el._wert;
    el._wert = wert;
    if (BEWEGUNG_AUS || Math.abs(start - wert) < 0.005) {
      el.textContent = format(wert);
      return;
    }
    const dauerMs = erstes ? 1000 : 380;
    const t0 = performance.now();
    const schritt = (t) => {
      const p = Math.min(1, (t - t0) / dauerMs);
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
  // ------------------------------------------------ Mein Profil (bleibt nur auf diesem Gerät)
  const profil = () => lies("profil", {}) || {};
  const profilPersonen = () => parseInt(profil().personen, 10) || 0;
  const dialog = $("#profil-dialog");
  const profilForm = dialog ? $("[data-profil-form]", dialog) : null;
  function profilOeffnen() {
    if (!dialog || !dialog.showModal) { const p = prompt("Dein Strompreis in €/kWh", String(preis())); if (p) setzePreis(parseFloat(p.replace(",", "."))); return; }
    const pr = profil();
    profilForm.elements.name.value = pr.name || "";
    profilForm.elements.preis.value = preis();
    ["personen", "wasser", "wohnen"].forEach((k) => {
      $$(`input[name="${k}"]`, profilForm).forEach((r) => { r.checked = String(pr[k] || (k === "personen" ? lies("personen", "") : "")) === r.value; });
    });
    profilForm.elements.balkon.checked = !!pr.balkon;
    profilForm.elements.eauto.checked = !!pr.eauto;
    $("[data-profil-avatar]", dialog).textContent = pr.name ? pr.name.trim()[0].toUpperCase() : "👤";
    dialog.showModal();
  }
  $$("[data-profil-oeffnen]").forEach((b) => b.addEventListener("click", profilOeffnen));
  if (dialog) dialog.addEventListener("close", () => {
    if (dialog.returnValue === "ok") {
      const f = profilForm.elements;
      const wert = (k) => { const r = $(`input[name="${k}"]:checked`, profilForm); return r ? r.value : undefined; };
      const neu = { name: f.name.value.trim().slice(0, 24), personen: wert("personen"), wasser: wert("wasser"), wohnen: wert("wohnen"), balkon: f.balkon.checked, eauto: f.eauto.checked };
      Object.keys(neu).forEach((k) => { if (neu[k] === undefined || neu[k] === "") delete neu[k]; });
      schreib("profil", neu);
      if (neu.personen) schreib("personen", +neu.personen);
      const sc = lies("sparcheck", {}) || {};
      if (neu.personen) sc.personen = neu.personen;
      if (neu.wasser) sc.wasser = neu.wasser;
      if (Object.keys(sc).length) schreib("sparcheck", sc);
      setzePreis(parseFloat(String(f.preis.value).replace(",", ".")));
      zaehle("profil-gespeichert", { personen: neu.personen || "?" });
      persoenlichAnwenden(true);
      setTimeout(abzeichenPruefen, 3500);
      snackbar(neu.name ? `Danke, ${neu.name}! Die Seite passt sich jetzt an deinen Haushalt an.` : "Profil gespeichert – die Seite passt sich jetzt an deinen Haushalt an.");
    } else if (dialog.returnValue === "loeschen") {
      const sicherung = {};
      try { Object.keys(localStorage).filter((k) => k.startsWith("sf:")).forEach((k) => { sicherung[k] = localStorage.getItem(k); localStorage.removeItem(k); }); } catch (e) { /* egal */ }
      aktualisiereAlles();
      persoenlichAnwenden(true);
      snackbar("Alle deine Daten auf diesem Gerät wurden gelöscht", { text: "Rückgängig", fn: () => {
        try { Object.entries(sicherung).forEach(([k, v]) => localStorage.setItem(k, v)); } catch (e) { /* egal */ }
        aktualisiereAlles(); persoenlichAnwenden(true);
      } });
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
    "tarif:verbrauch": (v) => zahl(v) + " kWh",
    "eauto:verbrauch": (v) => zahl(v, v % 1 ? 1 : 0) + " kWh/100 km",
    "eauto:km": (v) => zahl(v) + " km",
    "eauto:anteil": (v) => zahl(v) + " %",
  };
  function setzeSchieberFarbe(s) {
    const min = parseFloat(s.min) || 0, max = parseFloat(s.max) || 100;
    s.style.setProperty("--wert", ((parseFloat(s.value) - min) / (max - min || 1)) * 100 + "%");
  }
  function verbindeRegler(form, beiAenderung) {
    $$(".schieber[data-fuer]", form).forEach((s) => {
      const feld = form.elements[s.dataset.fuer];
      const anzeige = $(`[data-anzeige="${s.dataset.fuer}"]`, form);
      const fn = anzeigeText[(form.dataset.rechner || "") + ":" + s.dataset.fuer] || anzeigeText[s.dataset.fuer];
      const zeige = () => { if (anzeige && fn) anzeige.textContent = fn(parseFloat(feld.value) || 0); };
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

  // ------------------------------------------------ Standby-Rechner
  $$('form[data-rechner="standby"]').forEach((form) => {
    const aus = (k) => $(`[data-aus="${k}"]`, form);
    const felder = $$('input[type="hidden"][data-watt]', form);
    const r = {
      rechne() {
        const watt = felder.reduce((s, f) => s + (parseFloat(f.value) || 0) * parseFloat(f.dataset.watt), 0);
        const kwh = watt * wert(form, "stunden") * 365 / 1000;
        const p = preis();
        zeigeZahl(aus("euro_jahr"), kwh * p, euro);
        aus("watt").textContent = zahl(watt, 1) + " W";
        aus("kwh_jahr").textContent = zahl(kwh) + " kWh";
        aus("euro_10").textContent = euro(kwh * p * 10);
      },
    };
    felder.forEach((f) => {
      const zeile = f.closest(".standby-zeile");
      const ausgabe = $("output", zeile);
      const zeige = () => { ausgabe.textContent = f.value; zeile.classList.toggle("an", +f.value > 0); };
      $$("button[data-schritt]", zeile).forEach((b) => b.addEventListener("click", () => {
        f.value = Math.max(0, Math.min(20, (+f.value || 0) + +b.dataset.schritt));
        zeige(); vibriere(8); r.rechne();
      }));
      zeige();
    });
    verbindeRegler(form, () => r.rechne());
    form.addEventListener("input", () => r.rechne());
    r.rechne();
    rechner.push(r);
  });

  // ------------------------------------------------ Austausch-Rechner mit 10-Jahres-Bilanz
  $$('form[data-rechner="austausch"]').forEach((form) => {
    const aus = (k) => $(`[data-aus="${k}"]`, form);
    const bilanz = $("[data-bilanz]");
    const r = {
      rechne() {
        const ersparnis = Math.max(0, wert(form, "alt") - wert(form, "neu")) * preis();
        const kosten = wert(form, "kosten");
        zeigeZahl(aus("ersparnis"), ersparnis, euro);
        aus("amort").textContent = ersparnis > 0 ? zahl(kosten / ersparnis, 1) + " Jahren" : "–";
        const zehn = ersparnis * 10 - kosten;
        aus("bilanz").textContent = (zehn < 0 ? "−" : "+") + euro(Math.abs(zehn));
        if (!bilanz) return;
        const werte = Array.from({ length: 10 }, (_, i) => ersparnis * (i + 1) - kosten);
        const hoch = Math.max(0, ...werte), tief = Math.min(0, ...werte);
        const spanne = (hoch - tief) || 1;
        const null_ = hoch / spanne * 100;
        if (!bilanz.children.length) {
          bilanz.innerHTML = werte.map((_, i) => `<div class="bilanz-spalte"><span class="bilanz-balken"></span><span class="bilanz-jahr">${i + 1}</span></div>`).join("")
            + '<span class="bilanz-null"></span>';
        }
        $$(".bilanz-spalte", bilanz).forEach((sp, i) => {
          const v = werte[i];
          const b = $(".bilanz-balken", sp);
          b.className = "bilanz-balken " + (v >= 0 ? "positiv" : "negativ");
          b.style.top = (v >= 0 ? (hoch - v) / spanne * 100 : null_) + "%";
          b.style.height = Math.max(0.6, Math.abs(v) / spanne * 100) + "%";
          sp.title = `Jahr ${i + 1}: ${v < 0 ? "−" : "+"}${euro(Math.abs(v))}`;
        });
        $(".bilanz-null", bilanz).style.top = `calc(16px + (100% - 50px) * ${null_ / 100})`;
      },
    };
    $$('input[name="vorlage"]', form).forEach((radio) => radio.addEventListener("change", () => {
      form.elements.alt.value = radio.dataset.alt;
      form.elements.neu.value = radio.dataset.neu;
      form.elements.kosten.value = radio.dataset.kosten;
      $$(".schieber[data-fuer]", form).forEach((s) => s._sync());
      vibriere(8);
      r.rechne();
    }));
    verbindeRegler(form, () => r.rechne());
    form.addEventListener("input", (ev) => {
      if (ev.target.name === "preis") { setzePreis(wert(form, "preis")); return; }
      r.rechne();
    });
    r.rechne();
    rechner.push(r);
  });

  // ------------------------------------------------ Zählerstand-Rechner
  $$('form[data-rechner="zaehler"]').forEach((form) => {
    const aus = (k) => $(`[data-aus="${k}"]`, form);
    const held = $("[data-zaehler-ergebnis]", form);
    const meldung = aus("meldung");
    const r = {
      rechne() {
        const t1 = new Date(form.elements.datum_alt.value), t2 = new Date(form.elements.datum_neu.value);
        const tage = Math.round((t2 - t1) / 86400000);
        const verbrauch = wert(form, "neu") - wert(form, "alt");
        const fehler = !(tage > 0) ? "Das zweite Datum muss nach dem ersten liegen."
          : !(verbrauch > 0) ? "Der aktuelle Zählerstand muss größer sein als der erste." : "";
        meldung.hidden = !fehler;
        meldung.textContent = fehler;
        if (fehler) { held.classList.remove("nachzahlung", "guthaben"); return; }
        const proTag = verbrauch / tage, jahr = proTag * 365;
        const kosten = jahr * preis() + wert(form, "grund") * 12;
        const diff = kosten - wert(form, "abschlag") * 12;
        held.classList.toggle("nachzahlung", diff > 0);
        held.classList.toggle("guthaben", diff <= 0);
        aus("label").textContent = diff > 0 ? "Voraussichtliche Nachzahlung" : "Voraussichtliches Guthaben";
        zeigeZahl(aus("differenz"), Math.abs(diff), euro);
        aus("verbrauch").textContent = zahl(verbrauch) + " kWh";
        aus("tage").textContent = zahl(tage);
        aus("pro_tag").textContent = zahl(proTag, 1) + " kWh";
        aus("jahr").textContent = zahl(jahr) + " kWh";
        aus("kosten").textContent = euro(kosten);
      },
    };
    form.addEventListener("input", (ev) => {
      if (ev.target.name === "preis") { setzePreis(wert(form, "preis")); return; }
      r.rechne();
    });
    form.addEventListener("change", () => r.rechne());
    r.rechne();
    rechner.push(r);
  });

  // ------------------------------------------------ Scroll-Geschichten (Apple-Stil) & Lesefortschritt
  const geschichten = $$("[data-story]");
  const lesebalken = $("[data-lesefortschritt]");
  if (geschichten.length && !BEWEGUNG_AUS) {
    geschichten.forEach((st) => {
      st.classList.add("lebendig");
      $$("[data-story-zahl]", st).forEach((z) => { z._endtext = z.textContent; z.textContent = "0"; });
    });
  }
  let scrollGeplant = false;
  function scrollBild() {
    scrollGeplant = false;
    const vh = innerHeight;
    geschichten.forEach((st) => {
      if (!st.classList.contains("lebendig")) return;
      const box = st.getBoundingClientRect();
      if (box.bottom < -vh || box.top > vh * 2) return;
      const p = Math.min(1, Math.max(0, -box.top / Math.max(1, box.height - vh)));
      const schritte = $$(".story-schritt", st);
      const n = schritte.length;
      const i = Math.min(n - 1, Math.floor(p * n * 0.999));
      st.style.setProperty("--p", p.toFixed(4));
      if (st.dataset.aktiv !== String(i)) {
        st.dataset.aktiv = String(i);
        schritte.forEach((s, k) => s.classList.toggle("aktiv", k === i));
        $$(".story-punkte i", st).forEach((d, k) => d.classList.toggle("aktiv", k === i));
        $$("[data-story-zahl]", st).forEach((z) => {
          const ziel = parseFloat(z.dataset.storyZahl);
          const kwh = z._endtext && z._endtext.includes("kWh") ? " kWh" : "";
          if (i === n - 1) zeigeZahl(z, ziel, (x) => zahl(Math.round(x)) + kwh);
          else { z._wert = undefined; z.textContent = "0" + kwh; }
        });
      }
    });
    if (lesebalken) {
      const h = document.documentElement.scrollHeight - innerHeight;
      const anteil = h > 0 ? Math.min(100, scrollY / h * 100) : 0;
      lesebalken.style.width = anteil + "%";
      const slug = lesebalken.dataset.artikelSlug;
      if (slug && anteil >= 85) {
        const gelesen = lies("gelesen", []) || [];
        if (!gelesen.includes(slug)) {
          schreib("gelesen", gelesen.concat(slug));
          snackbar("📚 Ratgeber als gelesen markiert");
          setTimeout(abzeichenPruefen, 0); // erst nach dem vollständigen Start aufrufen
        }
      }
    }
  }
  if (geschichten.length || lesebalken) {
    const anstossen = () => { if (!scrollGeplant) { scrollGeplant = true; requestAnimationFrame(scrollBild); } };
    addEventListener("scroll", anstossen, { passive: true });
    addEventListener("resize", anstossen);
    scrollBild();
  }

  // ------------------------------------------------ Gemeinsame Helfer: Kosten-Balken & Amazon-Links
  function zeichneBalken(name, zeilen) {
    const el = $(`[data-balken="${name}"]`);
    if (!el) return;
    const max = Math.max(1, ...zeilen.map((z) => z.wert));
    if (el.children.length !== zeilen.length) {
      el.innerHTML = zeilen.map(() => '<div class="kb-zeile"><span></span><span class="kb-spur"><i></i></span><b></b></div>').join("");
    }
    zeilen.forEach((z, i) => {
      const zeile = el.children[i];
      zeile.className = "kb-zeile " + (z.klasse || "");
      zeile.children[0].textContent = z.name;
      $("i", zeile).style.width = Math.max(1, z.wert / max * 100) + "%";
      zeile.children[2].textContent = euro(z.wert);
    });
  }
  const amazonLink = (q) => "https://www.amazon.de/s?k=" + encodeURIComponent(q).replace(/%20/g, "+") + (SF.tag ? "&tag=" + encodeURIComponent(SF.tag) : "");
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // ------------------------------------------------ Tarif-Vergleich
  $$('form[data-rechner="tarif"]').forEach((form) => {
    const aus = (k) => $(`[data-aus="${k}"]`, form);
    const held = $("[data-tarif-ergebnis]", form);
    const r = {
      rechne() {
        const v = wert(form, "verbrauch");
        const alt = v * wert(form, "alt_ap") / 100 + 12 * wert(form, "alt_gp");
        const neu2 = v * wert(form, "neu_ap") / 100 + 12 * wert(form, "neu_gp");
        const neu1 = Math.max(0, neu2 - wert(form, "bonus"));
        const e1 = alt - neu1, e2 = alt - neu2;
        held.classList.toggle("guthaben", e1 >= 0);
        held.classList.toggle("nachzahlung", e1 < 0);
        aus("label").textContent = e1 >= 0 ? "Ersparnis im ersten Jahr" : "Mehrkosten im ersten Jahr";
        zeigeZahl(aus("ersparnis"), Math.abs(e1), euro);
        aus("ersparnis2").textContent = (e2 < 0 ? "−" : "") + euro(Math.abs(e2));
        aus("alt").textContent = euro(alt);
        zeichneBalken("tarif", [
          { name: "Bisher", wert: alt, klasse: "warm" },
          { name: "Neu, 1. Jahr", wert: neu1 },
          { name: "Neu, ab Jahr 2", wert: neu2, klasse: "gold" },
        ]);
      },
    };
    const hhKnopf = $("[data-aus-haushalt]", form);
    const hh = lies("haushalt", []).filter((x) => nachSlug[x.s]);
    if (hhKnopf && hh.length) {
      hhKnopf.hidden = false;
      hhKnopf.addEventListener("click", () => {
        const kwh = hh.reduce((s, x) => s + kwhJahr(x.w, x.h, x.n, x.wj, x.sb) * (x.m || 1), 0);
        form.elements.verbrauch.value = Math.max(500, Math.round(kwh / 50) * 50);
        $$(".schieber[data-fuer]", form).forEach((s) => s._sync());
        r.rechne();
        snackbar(`${zahl(kwh)} kWh aus „Mein Haushalt“ übernommen`);
      });
    }
    verbindeRegler(form, () => r.rechne());
    form.addEventListener("input", () => r.rechne());
    r.rechne();
    rechner.push(r);
  });

  // ------------------------------------------------ E-Auto-Ladekosten
  $$('form[data-rechner="eauto"]').forEach((form) => {
    const aus = (k) => $(`[data-aus="${k}"]`, form);
    const anteil = () => { const v = parseFloat(form.elements.anteil.value); return isFinite(v) ? Math.min(100, Math.max(0, v)) / 100 : 0.8; };
    const r = {
      rechne() {
        const km = wert(form, "km");
        const kwh = km / 100 * wert(form, "verbrauch") * 1.1;
        const a = anteil();
        const kostenE = kwh * (a * preis() + (1 - a) * wert(form, "saeule"));
        const kostenV = km / 100 * wert(form, "liter") * wert(form, "sprit");
        const diff = kostenV - kostenE;
        aus("label").textContent = diff >= 0 ? "Ersparnis gegenüber Verbrenner" : "Mehrkosten gegenüber Verbrenner";
        zeigeZahl(aus("ersparnis"), Math.abs(diff), euro);
        aus("e_jahr").textContent = euro(kostenE);
        aus("e_100").textContent = euro(km > 0 ? kostenE / km * 100 : 0);
        aus("kwh").textContent = zahl(kwh) + " kWh";
        zeichneBalken("eauto", [{ name: "E-Auto", wert: kostenE }, { name: "Verbrenner", wert: kostenV, klasse: "warm" }]);
      },
    };
    verbindeRegler(form, () => r.rechne());
    form.addEventListener("input", (ev) => {
      if (ev.target.name === "preis") { setzePreis(wert(form, "preis")); return; }
      r.rechne();
    });
    r.rechne();
    rechner.push(r);
  });

  // ------------------------------------------------ Geräte-Vergleich
  const vgForm = $("[data-vergleich]");
  if (vgForm) {
    const params = new URLSearchParams(location.search);
    ["a", "b"].forEach((k) => { if (nachSlug[params.get(k)]) vgForm.elements[k].value = params.get(k); });
    const r = {
      rechne() {
        const p = preis();
        const g = { a: nachSlug[vgForm.elements.a.value], b: nachSlug[vgForm.elements.b.value] };
        const kwh = { a: geraetKwh(g.a), b: geraetKwh(g.b) };
        ["a", "b"].forEach((k) => {
          const sp = $(`[data-vg="${k}"]`, vgForm);
          const em = $("[data-vg-emoji]", sp);
          if (em.textContent !== g[k].e) { em.textContent = g[k].e; em.style.animation = "none"; void em.offsetWidth; em.style.animation = ""; }
          $("[data-vg-name]", sp).textContent = g[k].n;
          zeigeZahl($("[data-vg-euro]", sp), kwh[k] * p, euro);
          $("[data-vg-monat]", sp).textContent = euro(kwh[k] * p / 12);
          $("[data-vg-tag]", sp).textContent = zahl(kwh[k] * p / 365 * 100, 1) + " ct";
          $("[data-vg-kwh]", sp).textContent = zahl(kwh[k]) + " kWh";
          $("[data-vg-link]", sp).href = `${ROOT}geraet/${g[k].s}/`;
          sp.classList.toggle("gewinner", kwh[k] > kwh[k === "a" ? "b" : "a"]);
        });
        const [teuer, guenstig] = kwh.a >= kwh.b ? ["a", "b"] : ["b", "a"];
        const faktor = kwh[teuer] / Math.max(0.01, kwh[guenstig]);
        const artikel = (x) => (x.a === "eine" ? "eine" : "ein");
        $("[data-vg-fazit]", vgForm).innerHTML = g.a === g.b ? "Wähle zwei verschiedene Geräte."
          : `${artikel(g[teuer]).replace(/^./, (c) => c.toUpperCase())} ${esc(g[teuer].nm)} kostet im Jahr <b>${faktor >= 1.95 ? "rund " + zahl(faktor, faktor < 10 ? 1 : 0) + "-mal so viel" : "rund " + euro((kwh[teuer] - kwh[guenstig]) * p) + " mehr"}</b> ${faktor >= 1.95 ? "wie" : "als"} ${artikel(g[guenstig])} ${esc(g[guenstig].nm)}.`;
        const u = new URL(location.href);
        u.searchParams.set("a", g.a.s); u.searchParams.set("b", g.b.s);
        history.replaceState(null, "", u);
      },
    };
    vgForm.addEventListener("change", () => r.rechne());
    r.rechne();
    rechner.push(r);
  }

  // ------------------------------------------------ Lexikon-Filter
  const lexSuche = $("[data-lex-suche]");
  if (lexSuche) {
    lexSuche.addEventListener("input", () => {
      const q = normal(lexSuche.value.trim());
      let n = 0;
      $$(".lex-gruppe").forEach((gr) => {
        let sichtbarIn = 0;
        $$(".lex-eintrag", gr).forEach((ein) => {
          const passt = !q || normal(ein.dataset.lex).includes(q);
          ein.hidden = !passt;
          if (passt) { sichtbarIn++; ein.classList.add("sichtbar"); }
        });
        gr.hidden = sichtbarIn === 0;
        n += sichtbarIn;
      });
      $("[data-lex-leer]").hidden = n > 0;
    });
  }

  // ------------------------------------------------ Spar-Check
  const pers = (a) => parseInt(a.personen, 10) || 2;
  const MASSNAHMEN = [
    { id: "dusche", e: "🚿", t: "Sparduschkopf montieren", text: "Halbiert die Wassermenge beim Duschen – und damit den Strom für den Durchlauferhitzer.",
      wenn: (a) => a.wasser === "strom", kwh: (a) => 200 * pers(a), q: "Sparduschkopf", link: "geraet/durchlauferhitzer/", lt: "Durchlauferhitzer" },
    { id: "heizdecke", e: "🛋️", t: "Heizdecke statt Heizlüfter", text: "Wärmt dich mit rund 60 statt 2.000 Watt – direkt am Sofa oder Schreibtisch.",
      wenn: (a) => a.heizen !== "nie", kwh: (a) => (a.heizen === "oft" ? 530 : 260), q: "Heizdecke Abschaltautomatik", link: "geraet/heizluefter/", lt: "Heizlüfter-Rechner" },
    { id: "led", e: "💡", t: "Auf LED umstellen", text: "Eine LED braucht rund 85 % weniger Strom als eine Glühbirne und hält viel länger.",
      wenn: (a) => a.licht !== "led", kwh: (a) => (a.licht === "alt" ? 450 : 200), q: "LED Lampe E27 warmweiß 806 lm", link: "geraet/gluehbirne/", lt: "Glühbirne vs. LED" },
    { id: "trockner", e: "🌀", t: "Wärmepumpentrockner statt Kondenstrockner", text: "Braucht für die gleiche Wäsche nur einen Bruchteil des Stroms.",
      wenn: (a) => a.trockner === "kondens", kwh: (a) => (pers(a) <= 2 ? 250 : 380), q: "Wärmepumpentrockner", link: "werkzeuge/austausch/", lt: "Austausch-Rechner" },
    { id: "standby", e: "🔌", t: "Standby konsequent abschalten", text: "Schaltbare Steckdosenleisten trennen Fernseher, Konsole und Co. komplett vom Netz.",
      wenn: (a) => a.standby !== "wenig", kwh: (a) => (a.standby === "viel" ? 280 : 140), q: "Steckdosenleiste schaltbar", link: "werkzeuge/standby/", lt: "Standby-Rechner" },
    { id: "kuehlschrank", e: "🧊", t: "Alten Kühlschrank ersetzen", text: "Geräte über 15 Jahre verbrauchen oft doppelt so viel wie moderne.",
      wenn: (a) => a.kuehl === "alt", kwh: () => 150, q: "Kühlschrank Energieeffizienzklasse A", link: "werkzeuge/austausch/", lt: "Lohnt sich das?" },
    { id: "leine", e: "🧺", t: "Öfter an der Leine trocknen", text: "Jeder Trockengang an der Luft kostet 0 Cent.",
      wenn: (a) => a.trockner !== "nein", kwh: (a) => (a.trockner === "kondens" ? 120 : 50) * (pers(a) <= 2 ? 1 : 1.5), q: "Wäscheständer platzsparend", link: "geraet/waermepumpentrockner/", lt: "Trockner-Rechner" },
    { id: "waschen", e: "🫧", t: "Mit 30 °C waschen", text: "Das Aufheizen macht den Großteil aus – 30 statt 60 °C spart mehr als die Hälfte pro Waschgang.",
      wenn: (a) => a.waschen !== "30", kwh: (a) => (a.waschen === "60" ? 50 : 15) * pers(a), q: "", link: "geraet/waschmaschine/", lt: "Waschmaschinen-Rechner" },
    { id: "kuehltemp", e: "🌡️", t: "Kühlschrank auf 7 °C stellen", text: "Jedes Grad kälter kostet rund 6 % mehr Strom.",
      wenn: (a) => a.kuehl !== "alt", kwh: () => 20, q: "Kühlschrank Thermometer", link: "geraet/kuehlschrank/", lt: "Kühlschrank-Rechner" },
    { id: "wlan", e: "📶", t: "WLAN nachts abschalten", text: "Die meisten Router haben eine Nachtschaltung – einmal einstellen, für immer sparen.",
      wenn: () => true, kwh: () => 25, q: "", link: "geraet/wlan-router/", lt: "Router-Rechner" },
  ];

  // Persönlicher Sparplan aus den Spar-Check-Antworten
  const sparPlan = (a) => MASSNAHMEN.filter((m) => m.wenn(a)).map((m) => ({ ...m, wert: m.kwh(a) })).sort((x, y) => y.wert - x.wert);
  const sparCheckFertig = (a) => ["personen", "wasser", "kuehl", "trockner", "licht", "standby", "heizen", "waschen"].every((k) => a && a[k]);
  const scEl = $("[data-spar-check]");
  if (scEl) {
    const fragen = $$(".sc-frage", scEl);
    const anzahl = fragen.length;
    const spiel = $(".sc-spiel", scEl), ergebnis = $("[data-sc-ergebnis]", scEl);
    let antworten = lies("sparcheck", {}) || {};
    // Vorbelegung aus dem Profil
    if (!antworten.personen && profil().personen) antworten.personen = String(profil().personen);
    if (!antworten.wasser && profil().wasser) antworten.wasser = profil().wasser;
    let index = 0, summe = 0;

    function zeigeFrage(i) {
      index = i;
      fragen.forEach((f, k) => { f.hidden = k !== i; });
      $("[data-sc-schritt]", scEl).textContent = `Frage ${i + 1} von ${anzahl}`;
      $("[data-sc-fortschritt]", scEl).style.width = (i / anzahl * 100) + "%";
      $("[data-sc-zurueck]", scEl).hidden = i === 0;
      const key = fragen[i].dataset.frage;
      $$(".sc-option", fragen[i]).forEach((o) => o.classList.toggle("gewaehlt", antworten[key] === o.dataset.wert));
    }
    function zeigeErgebnis() {
      spiel.hidden = true;
      ergebnis.hidden = false;
      const p = preis();
      const liste = sparPlan(antworten);
      const erledigt = lies("erledigt", []) || [];
      const kwh = liste.reduce((s, m) => s + m.wert, 0);
      summe = kwh * p;
      zeigeZahl($("[data-sc-summe]", scEl), summe, (x) => "bis zu " + euro(x));
      $("[data-sc-kwh]", scEl).textContent = zahl(kwh) + " kWh";
      $("[data-sc-anzahl]", scEl).textContent = liste.length;
      $("[data-sc-zehn]", scEl).textContent = euro(summe * 10);
      const gespart = liste.filter((m) => erledigt.includes(m.id)).reduce((s, m) => s + m.wert, 0) * p;
      let chip = $("[data-sc-gespart]", scEl);
      if (!chip) { chip = document.createElement("span"); chip.className = "eh-chip"; chip.dataset.scGespart = ""; $("[data-sc-zehn]", scEl).parentElement.after(chip); }
      chip.innerHTML = `✅ schon umgesetzt: <b>${euro(gespart)}</b> / Jahr`;
      const max = Math.max(1, ...liste.map((m) => m.wert));
      const stern = SF.tag ? "*" : "";
      $("[data-sc-massnahmen]", scEl).innerHTML = liste.map((m, i) => `<div class="massnahme${erledigt.includes(m.id) ? " erledigt" : ""}" style="animation-delay:${i * 70}ms">
        <span class="massnahme-emoji" aria-hidden="true">${m.e}</span><strong>${esc(m.t)}</strong>
        <span class="massnahme-wert">${euro(m.wert * p)}<small>pro Jahr</small></span><p>${esc(m.text)}</p>
        <span class="massnahme-balken"><i style="width:${m.wert / max * 100}%;animation-delay:${i * 70 + 200}ms"></i></span>
        <span class="massnahme-aktionen"><button type="button" class="knopf erledigt-knopf ripple" data-erledigt="${m.id}" aria-pressed="${erledigt.includes(m.id)}">${erledigt.includes(m.id) ? "✓ Erledigt" : "Als erledigt markieren"}</button>
        <a class="knopf knopf-tonal ripple" href="${ROOT}${m.link}">${esc(m.lt)}</a>
        ${m.q ? `<a class="knopf knopf-text ripple" href="${esc(amazonLink(m.q))}" rel="${SF.tag ? "sponsored " : ""}nofollow noopener" target="_blank">Passendes Produkt${stern}</a>` : ""}</span></div>`).join("");
      zaehle("spar-check-beendet", { summe: Math.round(summe) });
      $$("[data-erledigt]", scEl).forEach((b) => b.addEventListener("click", () => {
        const liste2 = lies("erledigt", []) || [];
        const id = b.dataset.erledigt;
        const an = !liste2.includes(id);
        schreib("erledigt", an ? liste2.concat(id) : liste2.filter((x) => x !== id));
        vibriere(an ? [20, 30, 20] : 10);
        if (an) zaehle("massnahme-erledigt", { id });
        zeigeErgebnis();
        abzeichenPruefen();
      }));
    }
    fragen.forEach((f, i) => $$(".sc-option", f).forEach((o) => o.addEventListener("click", () => {
      antworten[f.dataset.frage] = o.dataset.wert;
      schreib("sparcheck", antworten);
      if (f.dataset.frage === "personen" || f.dataset.frage === "wasser") schreib("profil", { ...profil(), [f.dataset.frage]: o.dataset.wert });
      $$(".sc-option", f).forEach((x) => x.classList.toggle("gewaehlt", x === o));
      vibriere(12);
      setTimeout(() => {
        if (i + 1 < anzahl) zeigeFrage(i + 1);
        else { zeigeErgebnis(); vibriere([30, 40, 30]); scEl.scrollIntoView({ behavior: "smooth", block: "start" }); }
      }, 240);
    })));
    $("[data-sc-zurueck]", scEl).addEventListener("click", () => { if (index > 0) zeigeFrage(index - 1); });
    $("[data-sc-neu]", scEl).addEventListener("click", () => {
      antworten = {}; loesche("sparcheck");
      ergebnis.hidden = true; spiel.hidden = false;
      zeigeFrage(0);
      scEl.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    $("[data-sc-teilen]", scEl).addEventListener("click", () =>
      teilen("Spar-Check", `🎯 Mein Strom-Spar-Check: bis zu ${euro(summe)} Sparpotenzial pro Jahr. Mach deinen eigenen:`));
    const fertig = fragen.every((f) => antworten[f.dataset.frage]);
    if (fertig) zeigeErgebnis(); else zeigeFrage(0);
    rechner.push({ rechne() { if (!ergebnis.hidden) zeigeErgebnis(); } });
  }

  // ------------------------------------------------ Spotlight-Suche
  const spot = $("[data-spotlight]");
  if (spot) {
    const eingabe = $("[data-spotlight-eingabe]", spot);
    const liste = $("[data-spotlight-ergebnisse]", spot);
    const REIHENFOLGE = ["Werkzeug", "Gerät", "Ratgeber", "Lexikon", "Seite"];
    let treffer = [], aktiv = 0;
    const alle = () => SF.geraete.map((g) => ({ t: g.n, u: `geraet/${g.s}/`, e: g.e, k: "Gerät", d: `${g.k} · ${euro(geraetKwh(g) * preis())} / Jahr` }))
      .concat(SF.seiten || []);
    function suche(q) {
      const nq = normal(q.trim());
      if (!nq) {
        const beliebt = ["Spar-Check", "Zählerstand-Rechner", "Tarif-Vergleich", "Mein Haushalt"];
        return beliebt.map((t) => (SF.seiten || []).find((x) => x.t === t)).filter(Boolean)
          .concat(SF.geraete.filter((g) => ["kuehlschrank", "heizluefter", "spielkonsole"].includes(g.s))
            .map((g) => ({ t: g.n, u: `geraet/${g.s}/`, e: g.e, k: "Gerät", d: g.k })));
      }
      return alle().map((x) => {
        const t = normal(x.t);
        const rang = t.startsWith(nq) ? 0 : t.split(/[\s(/-]+/).some((w) => w.startsWith(nq)) ? 1 : t.includes(nq) ? 2
          : (x.d && normal(x.d).includes(nq) && x.k !== "Gerät") ? 3 : 9;
        return { ...x, rang };
      }).filter((x) => x.rang < 9).sort((a, b) => a.rang - b.rang || REIHENFOLGE.indexOf(a.k) - REIHENFOLGE.indexOf(b.k)).slice(0, 14)
        // Top-Treffer zuerst, danach sauber nach Art gruppiert
        .map((x, i, alle) => (i === 0 ? { ...x, top: true } : x))
        .sort((a, b) => (b.top ? 1 : 0) - (a.top ? 1 : 0) || REIHENFOLGE.indexOf(a.k) - REIHENFOLGE.indexOf(b.k) || a.rang - b.rang);
    }
    function zeichne() {
      treffer = suche(eingabe.value);
      aktiv = 0;
      if (!treffer.length) { liste.innerHTML = '<p class="spot-gruppe">Nichts gefunden – versuch ein anderes Wort.</p>'; return; }
      let html = "", gruppe = "";
      const titel = eingabe.value.trim() ? null : "Beliebt";
      if (titel) html += `<p class="spot-gruppe">${titel}</p>`;
      treffer.forEach((x, i) => {
        if (!titel && x.top) { gruppe = "top"; html += '<p class="spot-gruppe">Top-Treffer</p>'; }
        else if (!titel && x.k !== gruppe) { gruppe = x.k; html += `<p class="spot-gruppe">${({ Werkzeug: "Werkzeuge", "Gerät": "Geräte", Ratgeber: "Ratgeber", Lexikon: "Lexikon", Seite: "Seiten" })[gruppe] || esc(gruppe)}</p>`; }
        html += `<a class="spot-treffer" role="option" href="${ROOT}${x.u}" data-i="${i}" aria-selected="${i === 0}">
          <span class="emoji-kreis" aria-hidden="true">${x.e}</span><span><b>${esc(x.t)}</b>${x.d ? `<small>${esc(x.d)}</small>` : ""}</span><em>${esc(x.k)}</em></a>`;
      });
      liste.innerHTML = html;
    }
    const markiere = (i) => {
      const el = $$(".spot-treffer", liste);
      if (!el.length) return;
      aktiv = (i + el.length) % el.length;
      el.forEach((x, k) => x.setAttribute("aria-selected", String(k === aktiv)));
      el[aktiv].scrollIntoView({ block: "nearest" });
    };
    const oeffnen = () => {
      spot.hidden = false; body.style.overflow = "hidden";
      eingabe.value = ""; zeichne();
      setTimeout(() => eingabe.focus(), 30);
    };
    const schliessen = () => { spot.hidden = true; body.style.overflow = ""; };
    $$("[data-spotlight-oeffnen]").forEach((a) => a.addEventListener("click", (ev) => { ev.preventDefault(); oeffnen(); }));
    $("[data-spotlight-zu]", spot).addEventListener("click", schliessen);
    spot.addEventListener("click", (ev) => { if (ev.target === spot) schliessen(); });
    eingabe.addEventListener("input", zeichne);
    eingabe.addEventListener("keydown", (ev) => {
      if (ev.key === "ArrowDown") { ev.preventDefault(); markiere(aktiv + 1); }
      else if (ev.key === "ArrowUp") { ev.preventDefault(); markiere(aktiv - 1); }
      else if (ev.key === "Enter") { const el = $$(".spot-treffer", liste)[aktiv]; if (el) { ev.preventDefault(); location.href = el.href; } }
    });
    document.addEventListener("keydown", (ev) => {
      const tippt = /INPUT|TEXTAREA|SELECT/.test((document.activeElement || {}).tagName || "");
      if ((ev.key === "k" && (ev.ctrlKey || ev.metaKey)) || (ev.key === "/" && !tippt)) { ev.preventDefault(); oeffnen(); }
      else if (ev.key === "Escape" && !spot.hidden) schliessen();
    });
  }

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
    let personen = parseInt(profil().personen, 10) || lies("personen", 2);
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
    $$('input[name="personen"]', hhEl).forEach((r) => r.addEventListener("change", () => { personen = +r.value; schreib("personen", personen); schreib("profil", { ...profil(), personen: String(personen) }); render(); }));

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
        ? `Deine erfassten Geräte: ${zahl(anteil)} % des typischen Verbrauchs ${personen === 5 ? "eines Haushalts mit 5 oder mehr Personen" : "eines " + personen + "-Personen-Haushalts"} (ca. ${zahl(schnitt)} kWh im Jahr).`
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
      if (punkte >= 7) setTimeout(konfetti, 250);
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

  // ------------------------------------------------ Einblenden beim Scrollen (gestaffelt)
  const EINBLENDEN = ".seitenkopf, .werkzeug-karte, .kennzahlen, .rechner, .produkt, .hinweis-karte, .tipp-karte, .fakt-karte, "
    + ".kategorie-karte, .faq-eintrag, .geraet-karte, .rangliste, .quiz, .text-karte, .monate, .diagramm-karte, "
    + ".abschnitt > h2, .abschnitt > .overline, .abschnitt-kopf, .abschnitt > .unterzeile, "
    + ".statement-zeile, .statement-unter, .artikel-karte, .artikel-abschnitt, .cta-karte, .kwh-raster > div, .label-skala, "
    + ".sparcheck-promo, .lex-eintrag, .kosten-balken, .vg-raster";
  const ziele = $$(EINBLENDEN).filter((el) => !el.closest(".held, .story"));
  if ("IntersectionObserver" in window && !BEWEGUNG_AUS) {
    let gemeldet = false;
    const beobachter = new IntersectionObserver((eintraege) => {
      gemeldet = true;
      eintraege.forEach((e) => {
        if (!e.isIntersecting) return;
        e.target.classList.add("sichtbar");
        beobachter.unobserve(e.target);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.08 });
    ziele.forEach((el) => {
      const geschwister = Array.from(el.parentElement.children).filter((k) => k.matches(EINBLENDEN));
      el.style.setProperty("--verz", Math.min(geschwister.indexOf(el), 6) * 60 + "ms");
      el.classList.add("einblenden");
      beobachter.observe(el);
    });
    // Sicherheitsnetz: Inhalte dürfen nie unsichtbar bleiben
    setTimeout(() => { if (!gemeldet) ziele.forEach((el) => el.classList.add("sichtbar")); }, 2500);
  } else {
    ziele.forEach((el) => el.classList.add("sichtbar"));
  }

  // ------------------------------------------------ Kennzahlen zählen hoch
  $$("[data-hochzaehlen]").forEach((el) => {
    const ziel = parseFloat(el.dataset.hochzaehlen);
    if (BEWEGUNG_AUS || !("IntersectionObserver" in window)) return;
    el.textContent = "0";
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      io.disconnect();
      zeigeZahl(el, ziel, (x) => zahl(Math.round(x)));
    });
    io.observe(el);
  });

  // ------------------------------------------------ Live-Ticker im Kopfbereich
  const ticker = $("[data-ticker]");
  if (ticker && SF.geraete.length && !BEWEGUNG_AUS) {
    const reihe = SF.geraete.slice().sort(() => Math.random() - 0.5);
    let i = 0;
    setInterval(() => {
      if (document.hidden) return;
      const g = reihe[i++ % reihe.length];
      ticker.classList.remove("rein");
      ticker.classList.add("raus");
      setTimeout(() => {
        ticker.textContent = `${g.e} ${g.n} · ${euro(geraetKwh(g) * preis())} im Jahr`;
        ticker.classList.remove("raus");
        ticker.classList.add("rein");
      }, 280);
    }, 2800);
  }

  // ------------------------------------------------ Konfetti (Quiz-Belohnung)
  function konfetti() {
    if (BEWEGUNG_AUS) return;
    const c = document.createElement("canvas");
    c.className = "konfetti";
    const dpr = window.devicePixelRatio || 1;
    c.width = innerWidth * dpr; c.height = innerHeight * dpr;
    body.appendChild(c);
    const ctx = c.getContext("2d");
    ctx.scale(dpr, dpr);
    const farben = ["#006C4C", "#6CDBAC", "#FFC94A", "#F7BD48", "#4F86C6", "#B4579B"];
    const teile = Array.from({ length: 140 }, () => ({
      x: innerWidth / 2 + (Math.random() - 0.5) * 80, y: innerHeight * 0.35,
      vx: (Math.random() - 0.5) * 14, vy: -Math.random() * 14 - 4,
      w: 6 + Math.random() * 6, h: 8 + Math.random() * 8, r: Math.random() * Math.PI, vr: (Math.random() - 0.5) * 0.4,
      f: farben[Math.floor(Math.random() * farben.length)],
    }));
    const t0 = performance.now();
    const bild = (t) => {
      const alter = t - t0;
      ctx.clearRect(0, 0, innerWidth, innerHeight);
      teile.forEach((s) => {
        s.vy += 0.35; s.vx *= 0.99; s.x += s.vx; s.y += s.vy; s.r += s.vr;
        ctx.save(); ctx.translate(s.x, s.y); ctx.rotate(s.r);
        ctx.globalAlpha = Math.max(0, 1 - alter / 2400);
        ctx.fillStyle = s.f; ctx.fillRect(-s.w / 2, -s.h / 2, s.w, s.h * Math.abs(Math.cos(s.r * 2)));
        ctx.restore();
      });
      if (alter < 2400) requestAnimationFrame(bild); else c.remove();
    };
    requestAnimationFrame(bild);
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

  // ------------------------------------------------ Persönliche Ebene
  const SKALIERUNG = {
    waschmaschine: { feld: "nutzungen", wert: (p) => Math.min(14, p * 2), text: (v) => `${v} Waschgänge pro Woche` },
    geschirrspueler: { feld: "nutzungen", wert: (p) => Math.min(14, Math.max(2, Math.round(p * 1.75))), text: (v) => `${v} Spülgänge pro Woche` },
    waermepumpentrockner: { feld: "nutzungen", wert: (p) => Math.min(14, Math.round(p * 1.5)), text: (v) => `${v} Trockengänge pro Woche` },
    kondenstrockner: { feld: "nutzungen", wert: (p) => Math.min(14, Math.round(p * 1.5)), text: (v) => `${v} Trockengänge pro Woche` },
    durchlauferhitzer: { feld: "stunden", wert: (p) => Math.round(p * 0.15 * 100) / 100, text: (v) => `${Math.round(v * 60)} Minuten warmes Wasser pro Tag` },
  };
  const ARTIKEL = (SF.seiten || []).filter((x) => x.k === "Ratgeber").map((x) => ({ ...x, slug: x.u.split("/")[1] }));

  function fortschritt() {
    const pr = profil();
    const hh = (lies("haushalt", []) || []).filter((x) => nachSlug[x.s]);
    const sc = lies("sparcheck", {}) || {};
    const fertig = sparCheckFertig(sc);
    const plan = fertig ? sparPlan(sc) : [];
    const erledigt = lies("erledigt", []) || [];
    const umgesetzt = plan.filter((m) => erledigt.includes(m.id));
    const gelesen = (lies("gelesen", []) || []).filter((s) => ARTIKEL.some((a) => a.slug === s));
    return {
      pr, hh, fertig, plan, umgesetzt, gelesen, quiz: lies("quizrekord", 0) || 0,
      hhKwh: hh.reduce((s, x) => s + kwhJahr(x.w, x.h, x.n, x.wj, x.sb) * (x.m || 1), 0),
      potenzial: plan.reduce((s, m) => s + m.wert, 0), gespart: umgesetzt.reduce((s, m) => s + m.wert, 0),
    };
  }

  const ABZEICHEN = [
    { id: "profil", e: "👤", t: "Ganz meins", d: "Profil angelegt", ok: (f) => !!f.pr.personen },
    { id: "haushalt", e: "🏠", t: "Haushalts-Held", d: "8 Geräte erfasst", ok: (f) => f.hh.length >= 8 },
    { id: "sparfuchs", e: "🦊", t: "Sparfuchs", d: "Spar-Check gemacht", ok: (f) => f.fertig },
    { id: "macher", e: "✅", t: "Macher", d: "3 Maßnahmen umgesetzt", ok: (f) => f.umgesetzt.length >= 3 },
    { id: "quiz", e: "🧠", t: "Quiz-Profi", d: "8 von 10 im Quiz", ok: (f) => f.quiz >= 8 },
    { id: "wissen", e: "📚", t: "Wissensdurst", d: "5 Ratgeber gelesen", ok: (f) => f.gelesen.length >= 5 },
  ];
  function abzeichenPruefen() {
    const f = fortschritt();
    const bekannt = lies("abzeichen", []) || [];
    const neu = ABZEICHEN.filter((a) => a.ok(f) && !bekannt.includes(a.id));
    if (!neu.length) return;
    schreib("abzeichen", bekannt.concat(neu.map((a) => a.id)));
    const text = neu.length === 1 ? `🏅 Neues Abzeichen: ${neu[0].e} ${neu[0].t}` : `🏅 ${neu.length} neue Abzeichen: ${neu.map((a) => a.e + " " + a.t).join(", ")}`;
    setTimeout(() => { snackbar(text); vibriere([30, 50, 30, 50, 60]); neu.forEach((a) => zaehle("abzeichen", { id: a.id })); }, 900);
    dashboard();
  }

  function ringe(svg, werte) {
    const farben = ["var(--primary)", "#FFB300", "#4F86C6"];
    svg.innerHTML = werte.map((w, i) => {
      const r = 50 - i * 13, u = 2 * Math.PI * r, l = Math.max(0.001, Math.min(1, w)) * u;
      return `<circle cx="60" cy="60" r="${r}" class="ring-spur" style="stroke:${farben[i]}"></circle>
        <circle cx="60" cy="60" r="${r}" class="ring-wert" style="stroke:${farben[i]};--l:${l};--u:${u};animation-delay:${i * 120}ms" stroke-dasharray="${l} ${u}"></circle>`;
    }).join("");
  }

  function dashboard() {
    const mb = $("[data-mein-bereich]");
    if (!mb) return;
    const f = fortschritt();
    const p = preis();
    const hatDaten = !!(f.pr.personen || f.pr.name || f.hh.length || f.fertig);
    const einladung = $("[data-personalisieren]");
    if (einladung) einladung.hidden = hatDaten;
    mb.hidden = !hatDaten;
    if (!hatDaten) return;
    const std = new Date().getHours();
    $("[data-mb-zeit]", mb).textContent = std < 5 ? "Gute Nacht" : std < 11 ? "Guten Morgen" : std < 17 ? "Guten Tag" : std < 22 ? "Guten Abend" : "Gute Nacht";
    $("[data-mb-gruss]", mb).textContent = f.pr.name ? `Hallo ${f.pr.name} 👋` : "Dein Strom-Überblick";
    const nArtikel = ARTIKEL.length || 1;
    ringe($("[data-ringe]", mb), [f.hh.length / 8, f.plan.length ? f.umgesetzt.length / f.plan.length : 0, f.gelesen.length / nArtikel]);
    $("[data-ringe-legende]", mb).innerHTML = [
      ["var(--primary)", "Haushalt", `${Math.min(f.hh.length, 8)}/8 Geräte`],
      ["#FFB300", "Sparplan", f.plan.length ? `${f.umgesetzt.length}/${f.plan.length} umgesetzt` : "noch offen"],
      ["#4F86C6", "Wissen", `${f.gelesen.length}/${nArtikel} gelesen`],
    ].map(([c, t, w]) => `<li><i style="background:${c}"></i><span>${t}</span><b>${w}</b></li>`).join("");
    const kachel = (href, e, label, wert, sub) => `<a class="mb-kachel ripple" href="${ROOT}${href}"><span class="mbk-emoji" aria-hidden="true">${e}</span><small>${label}</small><b>${wert}</b><em>${sub}</em></a>`;
    $("[data-mb-kacheln]", mb).innerHTML = [
      f.hh.length ? kachel("haushalt/", "🏠", "Dein Haushalt", euro(f.hhKwh * p), `${zahl(f.hhKwh)} kWh pro Jahr`) : kachel("haushalt/", "🏠", "Dein Haushalt", "Erfassen", "Geräte zusammenstellen"),
      f.fertig ? kachel("werkzeuge/spar-check/", "🎯", "Sparpotenzial", "bis " + euro(f.potenzial * p), `${f.plan.length} Maßnahmen`) : kachel("werkzeuge/spar-check/", "🎯", "Sparpotenzial", "Ermitteln", "Spar-Check in 60 Sek."),
      kachel("werkzeuge/spar-check/", "✅", "Schon gespart", euro(f.gespart * p), "pro Jahr, umgesetzt"),
      `<button type="button" class="mb-kachel ripple" data-profil-oeffnen-kachel><span class="mbk-emoji" aria-hidden="true">⚡</span><small>Dein Strompreis</small><b>${zahl(p, 2)} €</b><em>pro kWh · ändern</em></button>`,
    ].join("");
    $("[data-profil-oeffnen-kachel]", mb).addEventListener("click", profilOeffnen);
    const ideen = [];
    if (!f.hh.length) ideen.push(["🏠", "Haushalt erfassen", "Sieh, was dein Zuhause im Jahr kostet", "haushalt/"]);
    if (!f.fertig) ideen.push(["🎯", "Spar-Check machen", "8 Fragen bis zu deinem Sparplan", "werkzeuge/spar-check/"]);
    if (f.pr.wasser === "strom") ideen.push(["🚿", "Durchlauferhitzer checken", "Weil dein Warmwasser mit Strom läuft", "geraet/durchlauferhitzer/"]);
    if (f.pr.balkon) ideen.push(["☀️", "Balkonkraftwerk rechnen", "Weil du Balkon oder Garten mit Sonne hast", "balkonkraftwerk/"]);
    if (f.pr.eauto) ideen.push(["🚗", "E-Auto-Ladekosten", "Weil du ein E-Auto fährst", "werkzeuge/e-auto/"]);
    if (f.pr.wohnen === "haus") ideen.push(["🌙", "Grundlast finden", "In Häusern laufen oft mehr Geräte dauerhaft", "wissen/grundlast/"]);
    if (f.plan.length && f.umgesetzt.length < f.plan.length) { const m = f.plan.find((x) => !f.umgesetzt.includes(x)); ideen.push([m.e, m.t, `Dein größter offener Hebel: ${euro(m.wert * p)} / Jahr`, "werkzeuge/spar-check/"]); }
    ideen.push(["🔄", "Tarif prüfen", "Oft die schnellste Ersparnis", "werkzeuge/tarifvergleich/"]);
    const naechster = ARTIKEL.find((a) => !f.gelesen.includes(a.slug));
    if (naechster) ideen.push([naechster.e, naechster.t, "Dein nächster Ratgeber", naechster.u]);
    if (!f.quiz) ideen.push(["🧠", "Stromfresser-Quiz", "Teste dein Gefühl für Stromkosten", "quiz/"]);
    $("[data-mb-empfehlungen]", mb).innerHTML = ideen.slice(0, 6).map(([e, t, g, u]) =>
      `<a class="empfehlung ripple" href="${ROOT}${u}"><span class="ak-emoji" aria-hidden="true">${e}</span><strong>${esc(t)}</strong><small>${esc(g)}</small></a>`).join("");
    $("[data-abzeichen]", mb).innerHTML = ABZEICHEN.map((a) => {
      const ok = a.ok(f);
      return `<div class="abzeichen${ok ? " verdient" : ""}" title="${esc(a.d)}"><span aria-hidden="true">${ok ? a.e : "🔒"}</span><b>${esc(a.t)}</b><small>${esc(a.d)}</small></div>`;
    }).join("");
  }

  function geraetPersoenlich(neuBerechnen) {
    const box = $("[data-persoenlich]");
    const form = $('form[data-rechner="geraet"][data-slug]');
    if (!box || !form) return;
    const slug = form.dataset.slug, g = nachSlug[slug];
    const teile = [];
    const regel = SKALIERUNG[slug], pers = profilPersonen();
    if (regel && pers && (neuBerechnen || !form._angepasst)) {
      const v = regel.wert(pers);
      form.elements[regel.feld].value = v;
      $$(".schieber[data-fuer]", form).forEach((s) => s._sync());
      form._angepasst = true;
      form.dispatchEvent(new Event("input", { bubbles: true }));
      teile.push(`<p>👤 <b>Angepasst an deinen Haushalt mit ${pers} ${pers === 1 ? "Person" : "Personen"}:</b> ${regel.text(v)}. <button type="button" class="link-knopf" data-typisch>Typische Werte</button></p>`);
    }
    const hh = (lies("haushalt", []) || []).filter((x) => nachSlug[x.s]);
    const eintrag = hh.find((x) => x.s === slug);
    if (eintrag) {
      const ges = hh.reduce((s, x) => s + kwhJahr(x.w, x.h, x.n, x.wj, x.sb) * (x.m || 1), 0);
      const k = kwhJahr(eintrag.w, eintrag.h, eintrag.n, eintrag.wj, eintrag.sb) * (eintrag.m || 1);
      teile.push(`<p>🏠 <b>In deinem Haushalt:</b> ${eintrag.m > 1 ? eintrag.m + " × " : ""}${esc(g.n)} kostet ${euro(k * preis())} im Jahr – ${zahl(ges ? k / ges * 100 : 0)} % deiner erfassten Stromkosten. <a href="${ROOT}haushalt/">Zum Haushalt</a></p>`);
    }
    box.innerHTML = teile.join("");
    box.hidden = !teile.length;
    const typ = $("[data-typisch]", box);
    if (typ) typ.addEventListener("click", () => {
      const r = $("[data-zuruecksetzen]", form);
      if (r) r.click();
      typ.closest("p").remove();
      box.hidden = !box.children.length;
    });
  }

  function persoenlichAnwenden(neu) {
    const pr = profil();
    $$("[data-avatar]").forEach((a) => {
      a.hidden = !pr.name;
      a.textContent = pr.name ? pr.name.trim()[0].toUpperCase() : "";
      a.closest(".profil-knopf").classList.toggle("hat-avatar", !!pr.name);
    });
    $$(".artikel-karte[data-artikel]").forEach((k) => k.classList.toggle("gelesen", (lies("gelesen", []) || []).includes(k.dataset.artikel)));
    dashboard();
    geraetPersoenlich(neu);
    if (haushalt && neu) haushalt.render();
  }

  aktualisiereAlles();
  persoenlichAnwenden(false);
  abzeichenPruefen();
  document.documentElement.dataset.appBereit = "1"; // Gesundheits-Marker: Skript komplett durchgelaufen
})();
