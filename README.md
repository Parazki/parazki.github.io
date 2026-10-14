# Stromfresser-Check – automatische Nebeneinkommens-Website

Eine Website im **Android-/Material-You-Stil** mit **Stromkosten-Rechnern für 52 Haushaltsgeräte**, **„Mein Haushalt“-Check**, **Stromfresser-Quiz** und **Balkonkraftwerk-Rechner**.
Sie lässt sich auf dem Handy **als App installieren** und funktioniert offline (PWA).
Sie verdient Geld über **Amazon-Partnerlinks** (z. B. Strommessgerät, LED-Lampen, Sparduschkopf) und optional später über Werbung.

| Anforderung | Erfüllt? |
|---|---|
| Kostenlos | Ja: Hosting auf GitHub Pages (0 €), keine Domain nötig, keine Software-Kosten. Ausnahme: siehe „Recht & Steuern“. |
| Keine API | Ja: reine HTML-Seiten, alle Rechner laufen im Browser des Besuchers. |
| Online & automatisch | Ja: GitHub baut und veröffentlicht die Seite selbst und baut sie jeden Monat neu (Datum/Jahreszahl bleiben aktuell). Kein Server, keine Wartung. |
| Ohne dein Zutun | Nach ca. 1 Stunde einmaliger Einrichtung: ja. Amazon zahlt automatisch auf dein Konto. |
| **Garantiert 100 €/Monat** | **Nein. Das kann niemand ehrlich garantieren** (siehe unten). |

## Ehrliche Erwartung

Die Seite verdient nur, wenn Menschen sie über Google finden. Das dauert:

- **Monat 0–3:** Google lernt die Seite kennen. Fast keine Besucher, ≈ 0 €.
- **Monat 3–12:** Wenn Google die Seiten gut einstuft, kommen Besucher über Suchen wie „Wie viel Strom verbraucht ein Heizlüfter“.
- **Für ~100 €/Monat** braucht man grob **10.000–30.000 Seitenaufrufe pro Monat** (Partnerlinks + Werbung zusammen). Das ist erreichbar, aber nicht sicher – viele Nischenseiten schaffen es nie.

Was die Chancen erhöht (optional, nicht nötig für den Betrieb):
1. Einmalig den Link teilen (z. B. in einem Spar- oder Balkonkraftwerk-Forum, Reddit r/Finanzen, Freunde).
2. Mehr Geräte in `data/geraete.json` ergänzen – jede Zeile wird automatisch zu einer neuen Seite.
3. Nach 3–6 Monaten in der Google Search Console schauen, welche Seiten Besucher bekommen, und dort mehr Inhalte ergänzen.

## Einmalige Einrichtung (ca. 1 Stunde)

Diese Schritte kann Claude **nicht** für dich machen (Konten anlegen, persönliche Daten, Auszahlung):

1. **Impressum ausfüllen** – in `config.json` unter `impressum` Name, Anschrift und E-Mail eintragen.
   In Deutschland Pflicht für Websites mit Partnerlinks. Ohne Impressum verweigert der Bau die Veröffentlichung absichtlich.
2. **GitHub-Konto** anlegen (kostenlos): https://github.com/signup
3. Auf GitHub ein **neues, leeres, öffentliches Repository** `DEIN-GITHUB-NAME.github.io` anlegen (ohne README).
   Mit genau diesem Namen liegt die Seite an der Wurzel der Adresse – nur dann zeigt Google deinen Seitennamen und dein Logo
   statt einer grauen Weltkugel. (Ein anderer Name funktioniert auch, dann liegt die Seite unter `…github.io/NAME/`.)
4. In PowerShell in diesem Ordner ausführen (lädt alles hoch):
   ```
   powershell -ExecutionPolicy Bypass -File veroeffentlichen.ps1 -GitHubName DEIN-GITHUB-NAME
   ```
5. Auf GitHub im Repository: **Settings → Pages → Source: „GitHub Actions“**, dann **Actions → „Website bauen und veröffentlichen“ → Run workflow**.
   Nach ~2 Minuten ist die Seite online: `https://DEIN-GITHUB-NAME.github.io/`
   Bei jedem Veröffentlichen meldet der Workflow alle Seiten per IndexNow an Bing, Ecosia und DuckDuckGo.
6. **Amazon-Partnerprogramm** (kostenlos): https://partnernet.amazon.de – Website-URL aus Schritt 5 angeben.
   Den Partner-Tag (endet meist auf `-21`) in `config.json` bei `amazon_partner_tag` eintragen und hochladen
   (auf GitHub die Datei `config.json` öffnen → Stift-Symbol → eintragen → „Commit changes“). Die Seite baut sich automatisch neu.
   Hinweis: Amazon schließt Konten, die in den ersten 180 Tagen keine 3 Verkäufe erzielen – dann einfach später neu anmelden.
7. **Google Search Console** (kostenlos): https://search.google.com/search-console – Property „URL-Präfix“ mit deiner Seiten-URL,
   Bestätigung per „HTML-Tag“: nur den `content`-Wert in `config.json` bei `google_site_verification` eintragen und hochladen.
   Danach unter „Sitemaps“ `sitemap.xml` einreichen. Das sorgt dafür, dass Google die Seite schnell findet.
8. **Bing Webmaster Tools** (kostenlos): https://www.bing.com/webmasters – „Aus Google Search Console importieren“.
   Bing liefert auch die Ergebnisse von Ecosia, DuckDuckGo und Yahoo.

Optional später: **Google AdSense** (`adsense_client_id`), sobald die Seite Besucher hat. Dafür ist ein Cookie-Einwilligungsbanner nötig (bei AdSense kostenlos einschaltbar); die Datenschutzerklärung ergänzt sich automatisch um einen AdSense-Abschnitt.

## Recht & Steuern (kurz, keine Rechtsberatung)

- Partnerprovisionen sind in Deutschland in der Regel **gewerbliche Einnahmen** → **Gewerbeanmeldung** beim Gewerbeamt (einmalig ca. 15–60 €, je nach Stadt). Das ist der einzige Kostenpunkt.
- Einnahmen in der Steuererklärung angeben; für kleine Beträge gibt es die Kleinunternehmerregelung.
- Amazon PartnerNet setzt Volljährigkeit voraus.
- Impressum und Datenschutzerklärung sind Vorlagen – im Zweifel mit einem Generator (z. B. e-recht24) abgleichen.

## Technik

```
config.json          Name, Strompreis, Partner-Tag, Impressum
data/geraete.json    Gerätedaten – jede Zeile = eine Seite (mit Emoji)
build.py             erzeugt dist/ inkl. manifest.webmanifest, sw.js, assets/daten.js
test_build.py        Tests:  python test_build.py
assets/              Material-You-CSS, App-JavaScript, Icons
tools/icons.py       erzeugt die App-Icons (PNG) neu
.github/workflows/   automatischer Bau + Veröffentlichung + monatlicher Neubau
```

Lokale Vorschau: `python build.py` und dann `python -m http.server 8000 --directory dist` → http://localhost:8000
