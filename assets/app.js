// Rechner für Stromfresser-Check. Läuft komplett im Browser, sendet nichts.
// Formeln identisch mit build.py (jahresverbrauch_kwh, balkonkraftwerk_seite).
(function () {
  "use strict";
  var STUNDEN_JAHR = 8760;

  function zahl(x, stellen) {
    return x.toLocaleString("de-DE", { minimumFractionDigits: stellen || 0, maximumFractionDigits: stellen || 0 });
  }
  function euro(x) {
    return (x < 100 ? zahl(x, 2) : zahl(x, 0)) + " €";
  }
  function wert(form, name) {
    var el = form.elements[name];
    if (!el) return 0;
    var v = parseFloat(String(el.value).replace(",", "."));
    return isFinite(v) && v > 0 ? v : 0;
  }
  function zeige(form, key, text) {
    var el = form.querySelector('[data-aus="' + key + '"]');
    if (el) el.textContent = text;
  }

  function rechneGeraet(form) {
    var h = Math.min(wert(form, "stunden") * wert(form, "nutzungen") * wert(form, "wochen"), STUNDEN_JAHR);
    var standby = wert(form, "standby");
    var sbKwh = standby * (STUNDEN_JAHR - h) / 1000;
    var kwh = wert(form, "leistung") * h / 1000 + sbKwh;
    var preis = wert(form, "preis");
    zeige(form, "euro_jahr", euro(kwh * preis));
    zeige(form, "kwh_jahr", zahl(kwh) + " kWh");
    zeige(form, "euro_monat", euro(kwh * preis / 12));
    zeige(form, "kwh_monat", zahl(kwh / 12, 1) + " kWh");
    zeige(form, "euro_standby", euro(sbKwh * preis));
    zeige(form, "kwh_standby", zahl(sbKwh, 1) + " kWh");
  }

  function rechneBkw(form) {
    // Modulleistung über ~115 % des Wechselrichters bringt kaum Mehrertrag (Begrenzung).
    var kwp = Math.min(wert(form, "modul"), wert(form, "wr") * 1.15) / 1000;
    var ertrag = kwp * wert(form, "region") * wert(form, "ausrichtung") * wert(form, "montage");
    var eigen = Math.min(wert(form, "eigen"), 100) / 100;
    var ersparnis = ertrag * eigen * wert(form, "preis");
    var kosten = wert(form, "kosten");
    zeige(form, "ertrag", zahl(ertrag) + " kWh");
    zeige(form, "ersparnis", euro(ersparnis));
    zeige(form, "eigen_kwh", zahl(ertrag * eigen) + " kWh selbst genutzt");
    zeige(form, "amort", ersparnis > 0 ? zahl(kosten / ersparnis, 1) + " Jahre" : "–");
  }

  var rechner = { geraet: rechneGeraet, bkw: rechneBkw };
  var formulare = document.querySelectorAll("form[data-rechner]");
  for (var i = 0; i < formulare.length; i++) {
    (function (form) {
      var fn = rechner[form.getAttribute("data-rechner")];
      if (!fn) return;
      form.addEventListener("input", function () { fn(form); });
      form.addEventListener("change", function () { fn(form); });
      fn(form);
    })(formulare[i]);
  }
})();
