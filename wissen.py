"""Ratgeber-Artikel für den Bereich „Wissen“.

Platzhalter (werden von build.py gefüllt): {root} relativer Pfad zur Website-Wurzel,
{preis} Strompreis „0,35“, {euro_1w} Kosten von 1 W Dauerbetrieb pro Jahr,
{euro_kwh} Kosten von 1 kWh. Sonst keine geschweiften Klammern im Text verwenden.
"""

ARTIKEL = [
    {
        "slug": "watt-und-kwh",
        "emoji": "⚡",
        "titel": "Watt und kWh einfach erklärt",
        "kurz": "Was der Unterschied zwischen Leistung und Energie ist – und wie du daraus deine Stromkosten berechnest.",
        "beschreibung": "Watt, Kilowattstunde, Strompreis: Einfach erklärt mit Beispielen, Formel und dem Übersetzer „Was ist eigentlich 1 kWh?“.",
        "abschnitte": [
            ("Watt: wie stark ein Gerät gerade zieht",
             "<p>Watt (W) ist die <strong>Leistung</strong> – also wie viel Strom ein Gerät in genau diesem Moment braucht. "
             "Ein Wasserkocher zieht etwa 2.000 W, eine LED-Lampe nur rund 8 W. Die Wattzahl steht meist auf dem Typenschild "
             "oder in der Anleitung.</p>"
             "<p>Die Leistung allein sagt aber noch nichts über die Kosten. Entscheidend ist, <strong>wie lange</strong> ein Gerät läuft.</p>"),
            ("Kilowattstunde: was am Ende auf der Rechnung steht",
             "<p>Die Kilowattstunde (kWh) ist die <strong>Energie</strong>, also Leistung mal Zeit. 1 kWh bedeutet: "
             "1.000 Watt eine Stunde lang – oder 100 Watt zehn Stunden lang.</p>"
             '<div class="formel"><span>Watt</span><b>×</b><span>Stunden</span><b>÷</b><span>1.000</span><b>=</b><span class="formel-ziel">kWh</span></div>'
             "<p>Dein Stromanbieter rechnet in Cent pro kWh ab. Bei {preis} €/kWh kostet jede Kilowattstunde also rund {euro_kwh}.</p>"),
            ("Drei Beispiele zum Mitrechnen",
             "<ul class=\"beispiel-liste\">"
             "<li><span>🫖</span><div><strong>Wasserkocher</strong> 2.000 W × 0,1 h (6 Minuten) = 0,2 kWh</div></li>"
             "<li><span>📺</span><div><strong>Fernseher</strong> 90 W × 4 h = 0,36 kWh pro Tag – im Jahr rund 131 kWh</div></li>"
             "<li><span>🔆</span><div><strong>LED-Lampe</strong> 8 W × 125 h = 1 kWh</div></li>"
             "</ul>"
             "<p>Du willst es nicht selbst rechnen? Der <a href=\"{root}#rechner\">freie Stromkosten-Rechner</a> erledigt das für jedes Gerät.</p>"),
            ("Was ist eigentlich 1 kWh?",
             "<p>Eine Kilowattstunde klingt abstrakt. So viel kannst du ungefähr damit machen:</p>"
             '<div class="kwh-raster">'
             '<div><span>🔆</span><b>125 h</b><small>LED-Licht</small></div>'
             '<div><span>🫖</span><b>ca. 9 Liter</b><small>Wasser kochen</small></div>'
             '<div><span>📱</span><b>ca. 50×</b><small>Handy laden</small></div>'
             '<div><span>🚗</span><b>ca. 6 km</b><small>E-Auto fahren</small></div>'
             '<div><span>💻</span><b>ca. 25 h</b><small>Laptop</small></div>'
             '<div><span>🌀</span><b>ca. ⅔</b><small>Trockner-Ladung (Wärmepumpe)</small></div>'
             "</div>"
             "<p class=\"klein\">Grobe Richtwerte – je nach Gerät und Nutzung weicht der echte Wert ab.</p>"),
        ],
        "fragen": [
            ("Wie rechne ich Watt in kWh um?", "Watt × Betriebsstunden ÷ 1.000 = kWh. Beispiel: 500 W × 2 Stunden ÷ 1.000 = 1 kWh."),
            ("Was ist der Unterschied zwischen kW und kWh?", "kW (Kilowatt) ist die Leistung in einem Moment, kWh (Kilowattstunde) die verbrauchte Energie über eine Zeit. Abgerechnet werden kWh."),
            ("Wie viel kostet eine Kilowattstunde?", "Das hängt von deinem Tarif ab. Der Arbeitspreis steht auf deiner Stromrechnung in Cent pro kWh. Diese Seite rechnet standardmäßig mit {preis} €/kWh – du kannst oben rechts deinen eigenen Preis einstellen."),
        ],
        "werkzeug": ("Stromkosten jedes Geräts berechnen", "geraete/"),
    },
    {
        "slug": "standby",
        "emoji": "🔌",
        "titel": "Standby: der unsichtbare Stromfresser",
        "kurz": "Warum Geräte im Bereitschaftsmodus Geld kosten, wie viel das im Jahr ausmacht – und wie du es abstellst.",
        "beschreibung": "Was kostet Standby im Jahr? Typische Werte, Rechenbeispiele und die besten Tipps gegen Standby-Verbrauch.",
        "abschnitte": [
            ("Was ist Standby?",
             "<p>Viele Geräte sind nie ganz aus: Fernseher warten auf die Fernbedienung, Konsolen laden Updates, Ladegeräte "
             "hängen in der Steckdose. Dieser Bereitschaftsmodus braucht wenig Leistung – aber eben <strong>rund um die Uhr</strong>.</p>"),
            ("Warum wenige Watt viel ausmachen",
             '<div class="formel"><span>1 Watt</span><b>×</b><span>8.760 h</span><b>=</b><span class="formel-ziel">8,76 kWh</span></div>'
             "<p>Ein Jahr hat 8.760 Stunden. Jedes Watt, das dauerhaft läuft, kostet bei {preis} €/kWh rund <strong>{euro_1w} pro Jahr</strong>. "
             "Kommen in einem Haushalt 20 bis 30 Watt Dauerverbrauch zusammen, sind das bei 0,35 €/kWh schon rund 60 bis 90 € im Jahr.</p>"),
            ("Typische Standby-Werte",
             "<p>Neue Geräte dürfen im reinen Bereitschaftsmodus laut EU-Vorgaben meist nur noch sehr wenig verbrauchen, oft "
             "höchstens 0,5 Watt. Vernetzte Geräte mit WLAN, Sprachsteuerung oder Schnellstart liegen aber oft deutlich höher. "
             "Ältere Receiver, Drucker oder Boiler ziehen teils mehrere Watt.</p>"
             "<p>Wie viel es bei dir ist, zeigt der <a href=\"{root}werkzeuge/standby/\">Standby-Rechner</a>.</p>"),
            ("So stellst du Standby ab",
             "<ul class=\"haken-liste\">"
             "<li><strong>Schaltbare Steckdosenleiste:</strong> Fernseher, Receiver, Soundbar und Konsole mit einem Klick komplett aus.</li>"
             "<li><strong>Master-Slave-Leiste:</strong> Schaltet Monitor und Lautsprecher automatisch mit dem PC ab.</li>"
             "<li><strong>Zeitschaltuhr:</strong> Router-WLAN, Boiler oder Kaffeemaschine nachts abschalten.</li>"
             "<li><strong>Schnellstart ausschalten:</strong> In Fernseher und Konsole den „Instant-On“- bzw. Ruhemodus deaktivieren.</li>"
             "<li><strong>Nachmessen:</strong> Ein Strommessgerät zeigt den echten Standby-Wert deiner Geräte.</li>"
             "</ul>"),
        ],
        "fragen": [
            ("Wie viel kostet Standby im Jahr?", "Jedes Watt Dauerverbrauch sind 8,76 kWh im Jahr, bei {preis} €/kWh also rund {euro_1w}. Zehn Geräte mit je 2 Watt kosten so über 60 €."),
            ("Ist Standby schädlich für Geräte?", "Nein. Komplett ausschalten schadet modernen Geräten nicht. Ausnahme: Manche Geräte wie Router oder Drucker brauchen nach dem Einschalten etwas Zeit zum Starten."),
            ("Welche Geräte haben den höchsten Standby-Verbrauch?", "Häufig ältere Receiver und Set-Top-Boxen, Drucker, Soundbars, Spielkonsolen im Ruhemodus und Warmwassergeräte, die ständig nachheizen."),
        ],
        "werkzeug": ("Standby-Kosten berechnen", "werkzeuge/standby/"),
    },
    {
        "slug": "stromzaehler-ablesen",
        "emoji": "🔢",
        "titel": "Stromzähler ablesen und Verbrauch berechnen",
        "kurz": "Welche Zahl auf dem Zähler zählt, wie du deinen Verbrauch hochrechnest und eine Nachzahlung früh erkennst.",
        "beschreibung": "Stromzähler richtig ablesen: Drehstromzähler, digitaler Zähler und Smart Meter erklärt – mit Rechner für Verbrauch und Nachzahlung.",
        "abschnitte": [
            ("Welche Zähler gibt es?",
             "<ul class=\"beispiel-liste\">"
             "<li><span>⚙️</span><div><strong>Ferraris-Zähler</strong> – der klassische Zähler mit Drehscheibe und Zahlenrollen.</div></li>"
             "<li><span>🔢</span><div><strong>Digitaler Zähler</strong> (moderne Messeinrichtung) – mit Display, ohne Datenverbindung.</div></li>"
             "<li><span>📡</span><div><strong>Smart Meter</strong> (intelligentes Messsystem) – digitaler Zähler mit Kommunikationsmodul.</div></li>"
             "</ul>"),
            ("Die richtige Zahl ablesen",
             "<p>Beim Ferraris-Zähler liest du die Ziffern von links nach rechts ab; die Stelle nach dem Komma (oft rot umrandet) "
             "kannst du weglassen. Beim digitalen Zähler wechselt die Anzeige oft automatisch. Wichtig ist der Wert mit der Kennung "
             "<strong>1.8.0</strong> – das ist der Strom, den du aus dem Netz beziehst. <strong>2.8.0</strong> zeigt eingespeisten Strom, "
             "zum Beispiel von einem Balkonkraftwerk.</p>"),
            ("Verbrauch berechnen",
             '<div class="formel"><span>Neuer Stand</span><b>−</b><span>alter Stand</span><b>=</b><span class="formel-ziel">Verbrauch</span></div>'
             "<p>Teile den Verbrauch durch die Anzahl der Tage dazwischen und nimm ihn mal 365 – schon hast du eine Hochrechnung "
             "für das ganze Jahr. Der <a href=\"{root}werkzeuge/zaehlerstand/\">Zählerstand-Rechner</a> macht das automatisch und vergleicht "
             "das Ergebnis mit deinem monatlichen Abschlag.</p>"),
            ("Tipp: einmal im Monat notieren",
             "<p>Lies den Zähler immer am gleichen Tag ab, zum Beispiel am Monatsersten. So erkennst du Ausreißer sofort – etwa ein "
             "Gerät, das plötzlich mehr verbraucht – und wirst bei der Jahresabrechnung nicht überrascht. Im Winter liegt der Verbrauch "
             "wegen Licht und längerer Abende meist etwas höher als im Sommer.</p>"),
        ],
        "fragen": [
            ("Welche Zahl muss ich am Stromzähler ablesen?", "Beim digitalen Zähler den Wert 1.8.0 (Strombezug), beim Ferraris-Zähler die Zahl vor dem Komma."),
            ("Wie berechne ich meinen Jahresverbrauch?", "Verbrauch zwischen zwei Ablesungen ÷ Anzahl der Tage × 365. Je länger der Zeitraum, desto genauer die Hochrechnung."),
            ("Was bedeutet 2.8.0 auf dem Stromzähler?", "2.8.0 zeigt die Energie, die ins Netz eingespeist wurde – zum Beispiel von einer Solaranlage oder einem Balkonkraftwerk."),
        ],
        "werkzeug": ("Verbrauch und Nachzahlung berechnen", "werkzeuge/zaehlerstand/"),
    },
    {
        "slug": "energielabel",
        "emoji": "🏷️",
        "titel": "Das EU-Energielabel verstehen",
        "kurz": "Was die Buchstaben A bis G bedeuten, welche Zahl wirklich wichtig ist und wozu der QR-Code da ist.",
        "beschreibung": "EU-Energielabel A bis G erklärt: Effizienzklassen, Jahresverbrauch, QR-Code und worauf du beim Gerätekauf achten solltest.",
        "abschnitte": [
            ("Die neue Skala von A bis G",
             "<p>Seit März 2021 gilt für viele Geräte eine neue Skala von <strong>A (sehr sparsam) bis G</strong> – die Plus-Klassen wie "
             "A+++ gibt es dort nicht mehr. Betroffen sind unter anderem Kühl- und Gefriergeräte, Waschmaschinen, Waschtrockner, "
             "Geschirrspüler, Fernseher und Monitore; seit September 2021 auch Lampen.</p>"
             '<div class="label-skala"><span style="--f:#00A651">A</span><span style="--f:#50B848">B</span><span style="--f:#BFD730">C</span>'
             '<span style="--f:#FFF200">D</span><span style="--f:#FDB913">E</span><span style="--f:#F37021">F</span><span style="--f:#ED1C24">G</span></div>'
             "<p>Weil die Skala strenger geworden ist, landen viele Geräte, die früher A+++ hatten, heute nur in einer mittleren Klasse. "
             "Das Gerät ist dadurch nicht schlechter geworden – nur die Messlatte höher.</p>"),
            ("Die wichtigste Zahl: der Verbrauch",
             "<p>Schau nicht nur auf den Buchstaben, sondern auf die <strong>Verbrauchsangabe</strong>. Sie steht direkt auf dem Label:</p>"
             "<ul class=\"beispiel-liste\">"
             "<li><span>🧊</span><div><strong>Kühl- und Gefriergeräte:</strong> kWh pro Jahr</div></li>"
             "<li><span>🫧</span><div><strong>Waschmaschinen und Geschirrspüler:</strong> kWh pro 100 Durchgänge im Eco-Programm</div></li>"
             "<li><span>📺</span><div><strong>Fernseher und Monitore:</strong> kWh pro 1.000 Stunden</div></li>"
             "</ul>"
             "<p>Ein größeres Gerät kann trotz guter Klasse mehr verbrauchen als ein kleines mit schlechterer Klasse. "
             "Vergleiche deshalb immer die kWh.</p>"),
            ("Wozu ist der QR-Code?",
             "<p>Der QR-Code oben rechts führt zur EU-Produktdatenbank (EPREL). Dort findest du das offizielle Datenblatt mit allen "
             "Angaben zum Gerät – praktisch, um Modelle im Laden schnell zu vergleichen.</p>"),
            ("Lohnt sich ein sparsameres Gerät?",
             "<p>Ein teureres, sparsames Gerät rechnet sich vor allem bei Geräten, die viel laufen: Kühl- und Gefrierschrank, Trockner, "
             "Waschmaschine. Wie schnell, zeigt der <a href=\"{root}werkzeuge/austausch/\">Austausch-Rechner</a>.</p>"),
        ],
        "fragen": [
            ("Was bedeutet Energieeffizienzklasse A?", "A ist auf der neuen Skala die sparsamste Klasse. Viele Gerätegruppen haben anfangs kaum Modelle in Klasse A, damit Platz für künftige, noch sparsamere Geräte bleibt."),
            ("Gibt es noch A+++?", "Für Kühlgeräte, Waschmaschinen, Geschirrspüler, Fernseher und Lampen nicht mehr – dort gilt seit 2021 die Skala A bis G."),
            ("Worauf soll ich beim Kauf achten?", "Auf den Verbrauch in kWh auf dem Label, nicht nur auf den Buchstaben. Und auf die Größe: Ein passend großes Gerät spart mehr als ein zu großes mit guter Klasse."),
        ],
        "werkzeug": ("Austausch eines alten Geräts berechnen", "werkzeuge/austausch/"),
    },
    {
        "slug": "strom-sparen",
        "emoji": "💡",
        "titel": "30 Tipps zum Strom sparen",
        "kurz": "Die wirksamsten Spartipps für Küche, Wäsche, Technik, Licht und Heizen – sortiert nach Bereichen.",
        "beschreibung": "30 einfache Tipps zum Strom sparen im Haushalt: Küche, Waschen, Technik, Licht und Heizen – sofort umsetzbar.",
        "abschnitte": [
            ("🍳 Küche",
             "<ol class=\"tipp-liste\">"
             "<li>Kühlschrank auf 7 °C, Gefrierschrank auf −18 °C einstellen.</li>"
             "<li>Kühlgeräte nicht neben Herd oder Heizung stellen, Lüftungsgitter frei halten.</li>"
             "<li>Gefrierschrank regelmäßig abtauen.</li>"
             "<li>Beim Kochen immer einen Deckel benutzen.</li>"
             "<li>Wasser im Wasserkocher erhitzen statt auf dem Herd – und nur so viel wie nötig.</li>"
             "<li>Beim Backofen Umluft nutzen und aufs Vorheizen meist verzichten.</li>"
             "<li>Kleine Portionen in Heißluftfritteuse oder Mikrowelle statt im großen Ofen.</li>"
             "<li>Spülmaschine voll beladen und das Eco-Programm wählen.</li>"
             "</ol>"),
            ("🫧 Waschen und Trocknen",
             "<ol class=\"tipp-liste\" start=\"9\">"
             "<li>Mit 30 °C statt 60 °C waschen – das spart mehr als die Hälfte der Energie.</li>"
             "<li>Eco-Programme nutzen: Sie dauern länger, brauchen aber weniger Strom.</li>"
             "<li>Die Maschine voll beladen.</li>"
             "<li>Wäsche mit hoher Drehzahl schleudern, bevor sie in den Trockner kommt.</li>"
             "<li>Wann immer möglich an der Leine oder auf dem Wäscheständer trocknen.</li>"
             "<li>Flusensieb des Trockners nach jedem Durchgang reinigen.</li>"
             "</ol>"),
            ("📺 Technik und Standby",
             "<ol class=\"tipp-liste\" start=\"15\">"
             "<li>Fernseher, Receiver und Konsole über eine schaltbare Steckdosenleiste ganz ausschalten.</li>"
             "<li>Energiesparmodus und geringere Helligkeit am Fernseher aktivieren.</li>"
             "<li>Den Ruhemodus von Spielkonsolen deaktivieren, wenn du ihn nicht brauchst.</li>"
             "<li>Laptop statt Desktop-PC für Büroarbeit nutzen.</li>"
             "<li>Router-WLAN nachts per Zeitschaltung abschalten.</li>"
             "<li>Ladegeräte ausstecken, wenn nichts geladen wird.</li>"
             "</ol>"),
            ("💡 Licht",
             "<ol class=\"tipp-liste\" start=\"21\">"
             "<li>Alle Glühbirnen und Halogenlampen durch LEDs ersetzen.</li>"
             "<li>Licht ausschalten, wenn du den Raum verlässt – bei LEDs lohnt sich das immer.</li>"
             "<li>Bei smarten Lampen auf den Standby-Verbrauch achten.</li>"
             "</ol>"),
            ("🌡️ Heizen, Kühlen und Warmwasser",
             "<ol class=\"tipp-liste\" start=\"24\">"
             "<li>Heizlüfter nur kurz und für kleine Räume einsetzen.</li>"
             "<li>Statt den Raum zu heizen: Heizdecke für Sofa oder Schreibtisch.</li>"
             "<li>Sparduschkopf beim Durchlauferhitzer – halbiert die Wassermenge.</li>"
             "<li>Warmwassergeräte auf 40–45 °C stellen und nachts abschalten.</li>"
             "<li>Im Sommer tagsüber verschatten und nachts lüften statt Klimagerät.</li>"
             "</ol>"),
            ("🧠 Allgemein",
             "<ol class=\"tipp-liste\" start=\"29\">"
             "<li>Einmal den eigenen Haushalt durchrechnen – im <a href=\"{root}haushalt/\">Haushalts-Check</a> siehst du sofort die größten Posten.</li>"
             "<li>Große Verbraucher mit einem Strommessgerät nachmessen statt schätzen.</li>"
             "</ol>"),
        ],
        "fragen": [
            ("Wo kann man am meisten Strom sparen?", "Meist bei Geräten, die viel Wärme erzeugen oder ständig laufen: Warmwasser, Heizlüfter, Trockner, Kühl- und Gefriergeräte sowie Standby vieler Kleingeräte."),
            ("Lohnt sich Ausschalten statt Standby?", "Ja. Jedes Watt Dauerverbrauch kostet bei {preis} €/kWh rund {euro_1w} im Jahr."),
            ("Spart Waschen mit niedriger Temperatur wirklich?", "Ja. Den Großteil der Energie braucht das Aufheizen des Wassers. 30 °C statt 60 °C spart deshalb mehr als die Hälfte."),
        ],
        "werkzeug": ("Den eigenen Haushalt durchrechnen", "haushalt/"),
    },
    {
        "slug": "stromverbrauch-haushalt",
        "emoji": "🏠",
        "titel": "Wie viel Strom ist normal?",
        "kurz": "Typischer Jahresverbrauch nach Haushaltsgröße – und was deinen Verbrauch nach oben treibt.",
        "beschreibung": "Durchschnittlicher Stromverbrauch nach Personen im Haushalt: Richtwerte, Einflussfaktoren und wie du deinen Verbrauch einordnest.",
        "abschnitte": [
            ("Richtwerte nach Haushaltsgröße",
             "<p>Als grobe Orientierung für Haushalte <strong>ohne</strong> Warmwasserbereitung über Strom:</p>"
             '<div class="balken-tabelle">'
             '<div><span>1 Person</span><i style="--w:33%"></i><b>ca. 1.500 kWh</b></div>'
             '<div><span>2 Personen</span><i style="--w:56%"></i><b>ca. 2.500 kWh</b></div>'
             '<div><span>3 Personen</span><i style="--w:71%"></i><b>ca. 3.200 kWh</b></div>'
             '<div><span>4 Personen</span><i style="--w:84%"></i><b>ca. 3.800 kWh</b></div>'
             '<div><span>5 Personen</span><i style="--w:100%"></i><b>ca. 4.500 kWh</b></div>'
             "</div>"
             "<p class=\"klein\">Grobe Richtwerte. Der tatsächliche Verbrauch schwankt je nach Wohnung, Geräten und Gewohnheiten stark.</p>"),
            ("Was den Verbrauch nach oben treibt",
             "<ul class=\"haken-liste\">"
             "<li><strong>Warmwasser über Strom</strong> (Durchlauferhitzer, Boiler) – oft der größte Einzelposten.</li>"
             "<li><strong>Elektrisches Heizen</strong> mit Heizlüfter, Radiator oder Infrarotheizung.</li>"
             "<li><strong>Wäschetrockner</strong>, besonders ältere Kondenstrockner.</li>"
             "<li><strong>Alte Kühl- und Gefriergeräte</strong> und ein zusätzlicher Kühlschrank im Keller.</li>"
             "<li><strong>Homeoffice, Gaming-PC, Aquarium oder E-Auto</strong>.</li>"
             "</ul>"),
            ("So ordnest du deinen Verbrauch ein",
             "<p>Deinen Jahresverbrauch findest du auf der letzten Stromrechnung oder durch zwei Zählerablesungen im "
             "<a href=\"{root}werkzeuge/zaehlerstand/\">Zählerstand-Rechner</a>. Liegst du deutlich über dem Richtwert, lohnt sich ein Blick auf die "
             "großen Verbraucher – im <a href=\"{root}haushalt/\">Haushalts-Check</a> siehst du, welche Geräte den größten Anteil haben.</p>"),
        ],
        "fragen": [
            ("Wie viel Strom verbraucht ein 2-Personen-Haushalt?", "Als grober Richtwert etwa 2.500 kWh im Jahr, wenn das Warmwasser nicht über Strom erzeugt wird."),
            ("Wie viel Strom verbraucht ein Single-Haushalt?", "Grob etwa 1.500 kWh im Jahr. Mit Durchlauferhitzer kann es deutlich mehr sein."),
            ("Ist mein Stromverbrauch zu hoch?", "Vergleiche ihn mit den Richtwerten für deine Haushaltsgröße. Liegt er deutlich darüber, prüfe die großen Verbraucher wie Warmwasser, Trockner, Heizgeräte und alte Kühlgeräte."),
        ],
        "werkzeug": ("Haushalt durchrechnen", "haushalt/"),
    },
]


ARTIKEL += [
    {
        "slug": "stromanbieter-wechseln",
        "emoji": "🔄",
        "titel": "Stromanbieter wechseln: so einfach geht's",
        "kurz": "Worauf es beim Tarifvergleich ankommt, wie der Wechsel abläuft – und warum dir dabei nie der Strom ausgeht.",
        "beschreibung": "Stromanbieter wechseln Schritt für Schritt: Tarife richtig vergleichen, Bonus, Preisgarantie, Kündigung und Sonderkündigungsrecht einfach erklärt.",
        "abschnitte": [
            ("Warum sich ein Vergleich lohnt",
             "<p>Wer seit Jahren im selben Tarif oder in der <strong>Grundversorgung</strong> ist, zahlt oft mehr als nötig. "
             "Ein Wechsel dauert meist nur wenige Minuten online – und der Strom kommt danach aus derselben Steckdose wie vorher.</p>"),
            ("Das brauchst du für den Wechsel",
             "<ul class=\"haken-liste\">"
             "<li><strong>Zählernummer</strong> – steht auf dem Zähler und auf deiner Stromrechnung.</li>"
             "<li><strong>Jahresverbrauch</strong> in kWh – aus der letzten Abrechnung oder dem <a href=\"{root}werkzeuge/zaehlerstand/\">Zählerstand-Rechner</a>.</li>"
             "<li><strong>Deinen aktuellen Anbieter</strong> und die Kundennummer.</li>"
             "</ul>"),
            ("Tarife richtig vergleichen",
             "<p>Entscheidend ist der <strong>Gesamtpreis</strong> für deinen Verbrauch: Arbeitspreis × kWh + 12 × Grundpreis. Achte außerdem auf:</p>"
             "<ul class=\"beispiel-liste\">"
             "<li><span>🎁</span><div><strong>Bonus:</strong> gilt meist nur im ersten Jahr. Rechne auch das zweite Jahr ohne Bonus.</div></li>"
             "<li><span>🔒</span><div><strong>Preisgarantie:</strong> schützt eine Zeit lang vor Erhöhungen – lies, welche Bestandteile sie umfasst.</div></li>"
             "<li><span>📅</span><div><strong>Laufzeit und Kündigungsfrist:</strong> kurze Bindungen lassen dir die Freiheit, wieder zu wechseln.</div></li>"
             "<li><span>💳</span><div><strong>Vorkasse oder Pakettarife:</strong> lieber meiden, sie sind selten ein guter Deal.</div></li>"
             "</ul>"
             "<p>Der <a href=\"{root}werkzeuge/tarifvergleich/\">Tarif-Vergleich</a> rechnet dir aus, was ein neuer Tarif im ersten und im zweiten Jahr wirklich kostet.</p>"),
            ("So läuft der Wechsel ab",
             "<ol class=\"tipp-liste\">"
             "<li>Neuen Tarif online abschließen.</li>"
             "<li>Der neue Anbieter kündigt in der Regel für dich beim alten.</li>"
             "<li>Am Wechseltag den Zählerstand notieren und beiden Anbietern mitteilen.</li>"
             "<li>Fertig – Schlussrechnung vom alten, Begrüßung vom neuen Anbieter.</li>"
             "</ol>"
             "<p><strong>Keine Sorge:</strong> Der Strom wird beim Wechsel nicht unterbrochen. Sollte etwas schiefgehen, versorgt dich automatisch der örtliche Grundversorger weiter.</p>"),
            ("Sonderkündigungsrecht bei Preiserhöhung",
             "<p>Erhöht dein Anbieter die Preise, muss er dich vorher informieren. Du kannst dann in der Regel außerordentlich kündigen – "
             "auch wenn deine Vertragslaufzeit noch nicht vorbei ist. Ein guter Anlass, die Preise neu zu vergleichen.</p>"),
        ],
        "fragen": [
            ("Wird mir beim Wechsel der Strom abgestellt?", "Nein. Die Versorgung läuft ohne Unterbrechung weiter. Notfalls übernimmt der örtliche Grundversorger."),
            ("Muss ich meinen alten Vertrag selbst kündigen?", "Meist nicht – das übernimmt in der Regel der neue Anbieter für dich. Prüfe das beim Abschluss."),
            ("Lohnt sich ein Neukundenbonus?", "Oft ja, aber rechne immer auch das zweite Jahr ohne Bonus. Ein günstiger Arbeitspreis spart dauerhaft, ein Bonus nur einmal."),
        ],
        "werkzeug": ("Tarife vergleichen", "werkzeuge/tarifvergleich/"),
    },
    {
        "slug": "grundlast",
        "emoji": "🌙",
        "titel": "Grundlast: der Strom, der nie schläft",
        "kurz": "Wie du herausfindest, was dein Zuhause rund um die Uhr verbraucht – und warum hier oft das größte Sparpotenzial steckt.",
        "beschreibung": "Grundlast im Haushalt messen und senken: Was sie ist, wie du sie mit dem Stromzähler ermittelst und was jedes Watt im Jahr kostet.",
        "abschnitte": [
            ("Was ist die Grundlast?",
             "<p>Die Grundlast ist die Leistung, die in deinem Zuhause <strong>rund um die Uhr</strong> läuft – auch nachts, wenn niemand etwas "
             "benutzt: Kühlschrank, Router, Standby-Geräte, Umwälzpumpen, Smart-Home-Geräte.</p>"),
            ("Warum sie so teuer werden kann",
             '<div class="formel"><span>10 Watt</span><b>×</b><span>8.760 h</span><b>=</b><span class="formel-ziel">87,6 kWh</span></div>'
             "<p>Jedes Watt Grundlast kostet bei {preis} €/kWh rund {euro_1w} im Jahr. Wer seine Grundlast um 30 Watt senkt, spart "
             "dauerhaft jedes Jahr – ohne auf irgendetwas zu verzichten.</p>"),
            ("So misst du deine Grundlast",
             "<ol class=\"tipp-liste\">"
             "<li>Abends, wenn alles Übliche aus ist, den Zählerstand notieren (bei digitalen Zählern möglichst mit Nachkommastellen).</li>"
             "<li>Genau eine Stunde später erneut ablesen – in dieser Zeit nichts einschalten.</li>"
             "<li>Die Differenz in kWh × 1.000 ergibt deine Grundlast in Watt.</li>"
             "</ol>"
             "<p>Moderne digitale Zähler zeigen die aktuelle Leistung oft direkt an – dann reicht ein Blick nachts auf das Display.</p>"),
            ("Grundlast senken",
             "<ul class=\"haken-liste\">"
             "<li>Standby-Geräte mit schaltbaren Steckdosenleisten komplett trennen.</li>"
             "<li>Zweit-Kühlschrank oder alte Gefriertruhe im Keller prüfen – oft die größten Dauerverbraucher.</li>"
             "<li>Router-WLAN nachts per Zeitschaltung abschalten.</li>"
             "<li>Warmwasser-Kleinspeicher nur bei Bedarf heizen lassen.</li>"
             "<li>Einzelne Geräte mit einem Strommessgerät durchmessen.</li>"
             "</ul>"
             "<p>Welche Geräte im Standby hängen, zeigt der <a href=\"{root}werkzeuge/standby/\">Standby-Rechner</a>.</p>"),
        ],
        "fragen": [
            ("Was ist eine normale Grundlast?", "Das hängt stark von Haushalt und Geräten ab. Viele Haushalte liegen grob zwischen 50 und 150 Watt – darüber lohnt sich meist eine genauere Suche."),
            ("Wie messe ich die Grundlast ohne Messgerät?", "Über den Stromzähler: nachts eine Stunde lang nichts einschalten und den Verbrauch in dieser Stunde ablesen. kWh × 1.000 = Watt."),
            ("Was kostet die Grundlast im Jahr?", "Jedes Watt Dauerverbrauch sind 8,76 kWh im Jahr, bei {preis} €/kWh also rund {euro_1w}. 100 Watt Grundlast kosten damit rund 300 € im Jahr."),
        ],
        "werkzeug": ("Standby-Kosten berechnen", "werkzeuge/standby/"),
    },
    {
        "slug": "e-auto-laden",
        "emoji": "🚗",
        "titel": "E-Auto zu Hause laden: Kosten und Tipps",
        "kurz": "Was eine Akkuladung kostet, wann sich eine Wallbox lohnt und wie du am günstigsten lädst.",
        "beschreibung": "E-Auto zu Hause laden: Kosten pro 100 km, Wallbox oder Steckdose, Ladeverluste und Vergleich mit öffentlichen Ladesäulen.",
        "abschnitte": [
            ("Was kosten 100 Kilometer?",
             '<div class="formel"><span>kWh / 100 km</span><b>×</b><span>Strompreis</span><b>=</b><span class="formel-ziel">€ / 100 km</span></div>'
             "<p>Ein typisches E-Auto braucht etwa 15 bis 20 kWh auf 100 km. Dazu kommen Ladeverluste von grob 10 %. "
             "Bei {preis} €/kWh zu Hause sind das grob 6 bis 8 € pro 100 km. An öffentlichen Ladesäulen ist der Strom meist teurer.</p>"
             "<p>Den genauen Vergleich – auch gegen einen Verbrenner – macht der <a href=\"{root}werkzeuge/e-auto/\">E-Auto-Rechner</a>.</p>"),
            ("Steckdose oder Wallbox?",
             "<ul class=\"beispiel-liste\">"
             "<li><span>🔌</span><div><strong>Haushaltssteckdose:</strong> geht für gelegentliches Laden, ist aber langsam und belastet die Leitung lange. Lass die Installation vorher von einer Elektrofachkraft prüfen.</div></li>"
             "<li><span>⚡</span><div><strong>Wallbox (meist 11 kW):</strong> lädt schneller, sicherer und mit geringeren Verlusten. Sie wird von einer Elektrofachkraft installiert und muss beim Netzbetreiber angemeldet werden.</div></li>"
             "</ul>"),
            ("So lädst du günstiger",
             "<ul class=\"haken-liste\">"
             "<li>Möglichst zu Hause laden statt an teuren Schnellladern.</li>"
             "<li>Mit einer eigenen Solaranlage tagsüber Sonnenstrom laden.</li>"
             "<li>Stromtarife vergleichen – manche Anbieter haben spezielle Autostrom- oder dynamische Tarife.</li>"
             "<li>Den Akku im Alltag meist nur bis etwa 80 % laden – das schont ihn.</li>"
             "</ul>"),
        ],
        "fragen": [
            ("Was kostet eine Akkuladung zu Hause?", "Akkugröße in kWh × Strompreis, plus etwa 10 % Ladeverluste. Ein 60-kWh-Akku kostet bei {preis} €/kWh von leer auf voll grob 23 €."),
            ("Muss ich eine Wallbox anmelden?", "Ja, Wallboxen müssen beim Netzbetreiber angemeldet werden; sehr leistungsstarke Modelle brauchen sogar eine Genehmigung. Das übernimmt meist die Elektrofachkraft."),
            ("Ist Laden zu Hause günstiger als an der Ladesäule?", "Meistens ja. Öffentliche Ladesäulen und besonders Schnelllader verlangen in der Regel einen höheren Preis pro kWh als ein Haushaltstarif."),
        ],
        "werkzeug": ("E-Auto-Ladekosten berechnen", "werkzeuge/e-auto/"),
    },
]

# Strom-Lexikon: (Begriff, Erklärung). Erklärungen ohne geschweifte Klammern.
LEXIKON = [
    ("Abschlag", "Monatliche Vorauszahlung an den Stromanbieter. Mit der Jahresabrechnung wird verrechnet, ob du zu viel (Guthaben) oder zu wenig (Nachzahlung) gezahlt hast."),
    ("Arbeitspreis", "Preis für jede verbrauchte Kilowattstunde, meist in Cent pro kWh angegeben. Er macht den größten Teil der Stromrechnung aus."),
    ("Balkonkraftwerk", "Kleine Solaranlage mit ein bis zwei Modulen und Wechselrichter, die über eine Steckdose ins Hausnetz einspeist. In Deutschland ist eine Wechselrichterleistung bis 800 W vorgesehen."),
    ("Dynamischer Stromtarif", "Tarif, dessen Preis sich – oft stündlich – am Börsenstrompreis orientiert. Wer flexibel ist, kann günstige Zeiten nutzen. Voraussetzung ist ein Smart Meter."),
    ("Durchlauferhitzer", "Gerät, das Wasser beim Durchfließen elektrisch erhitzt. Sehr hohe Leistung (oft 18–24 kW) und häufig der größte Stromverbraucher im Haushalt."),
    ("Eigenverbrauch", "Anteil des selbst erzeugten Solarstroms, den du direkt im Haushalt nutzt. Je höher der Eigenverbrauch, desto mehr sparst du."),
    ("Einspeisung", "Strom, der von einer Solaranlage ins öffentliche Netz fließt, weil im Haus gerade nicht genug verbraucht wird. Bei Balkonkraftwerken meist ohne Vergütung."),
    ("Energielabel", "EU-weit einheitliches Etikett mit Effizienzklasse (A bis G) und Verbrauchsangabe. Über den QR-Code gelangst du zur Produktdatenbank EPREL."),
    ("EPREL", "Europäische Produktdatenbank für Energielabels. Dort findest du die offiziellen Datenblätter gelabelter Geräte."),
    ("Ferraris-Zähler", "Klassischer mechanischer Stromzähler mit drehender Scheibe und Zahlenrollen. Er wird nach und nach durch digitale Zähler ersetzt."),
    ("Grundlast", "Leistung, die im Haushalt rund um die Uhr läuft – etwa Kühlschrank, Router und Standby. Jedes Watt Grundlast sind 8,76 kWh im Jahr."),
    ("Grundpreis", "Fester Betrag pro Monat oder Jahr, den du unabhängig vom Verbrauch zahlst. Er deckt unter anderem Zähler und Abrechnung."),
    ("Grundversorgung", "Tarif des örtlichen Grundversorgers, der automatisch gilt, wenn du keinen anderen Vertrag hast. Oft teurer als Sondertarife, dafür kurzfristig kündbar."),
    ("Jahresabrechnung", "Abrechnung über deinen tatsächlichen Verbrauch eines Jahres. Sie verrechnet die gezahlten Abschläge und legt die neuen fest."),
    ("Kilowatt (kW)", "1.000 Watt. Einheit für Leistung – also wie viel Strom ein Gerät in einem Moment braucht."),
    ("Kilowattpeak (kWp)", "Nennleistung von Solarmodulen unter genormten Testbedingungen. Ein Balkonkraftwerk hat meist 0,8 bis 2 kWp Modulleistung."),
    ("Kilowattstunde (kWh)", "Einheit für Energie: 1.000 Watt eine Stunde lang. Danach wird Strom abgerechnet."),
    ("Ladeverluste", "Energie, die beim Laden eines Akkus als Wärme verloren geht – beim E-Auto grob 10 %. Sie wird mitbezahlt, landet aber nicht im Akku."),
    ("Leistungsaufnahme", "Die Leistung in Watt, die ein Gerät aus dem Netz zieht. Sie steht auf dem Typenschild meist als Höchstwert."),
    ("Marktstammdatenregister", "Offizielles Register der Bundesnetzagentur, in dem Stromerzeugungsanlagen – auch Balkonkraftwerke – angemeldet werden."),
    ("Moderne Messeinrichtung", "Digitaler Stromzähler mit Display, aber ohne Kommunikationsmodul. Er zeigt Zählerstände und oft historische Werte an."),
    ("Nachzahlung", "Betrag, den du nach der Jahresabrechnung zahlen musst, wenn deine Abschläge niedriger waren als die tatsächlichen Kosten."),
    ("Netzentgelt", "Teil des Strompreises, mit dem Bau, Betrieb und Wartung der Stromnetze bezahlt werden. Er unterscheidet sich je nach Region."),
    ("OBIS-Kennzahl", "Code auf digitalen Zählern, der angibt, welcher Wert angezeigt wird: 1.8.0 ist der Bezug aus dem Netz, 2.8.0 die Einspeisung."),
    ("Smart Meter", "Intelligentes Messsystem: digitaler Zähler mit Kommunikationsmodul, der Verbrauchsdaten sicher übertragen kann. Voraussetzung für dynamische Tarife."),
    ("Sonderkündigungsrecht", "Recht, einen Stromvertrag außerordentlich zu kündigen – etwa wenn der Anbieter die Preise erhöht."),
    ("Standby", "Bereitschaftsmodus, in dem ein Gerät nicht ganz ausgeschaltet ist und weiter Strom zieht – oft rund um die Uhr."),
    ("Volt, Ampere, Watt", "Leistung (Watt) = Spannung (Volt) × Stromstärke (Ampere). Das Haushaltsnetz in Deutschland hat 230 Volt."),
    ("Wallbox", "Fest installierte Ladestation für E-Autos, meist mit 11 kW. Sie muss beim Netzbetreiber angemeldet werden."),
    ("Wärmepumpe", "Heizung, die Wärme aus Luft, Erde oder Wasser nutzt. Aus einer Kilowattstunde Strom macht sie mehrere Kilowattstunden Wärme."),
    ("Wechselrichter", "Gerät, das den Gleichstrom aus Solarmodulen in haushaltsüblichen Wechselstrom umwandelt."),
    ("Wirkungsgrad", "Verhältnis von nutzbarer zu eingesetzter Energie. Je höher, desto weniger geht als Wärme oder Verlust verloren."),
]
