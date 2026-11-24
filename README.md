# Freies Zimmer

Zeigt mit einem Klick das nächste freie Zimmer, wenn ihr ausserhalb vom Schulzimmer arbeiten dürft.

- Schaut, wo die eigene Klasse gerade ist (Standard: G23v, unten änderbar)
- Empfiehlt zuerst ein freies Zimmer auf dem gleichen Stock (erste Ziffer = Stock), sonst ein Stock darüber oder darunter
- Keine Zimmer im Zirkusplatz (Z) oder Ergänzungsbau (E)
- Das Zimmer muss bis zum Ende der aktuellen Lektion frei sein

Grundlage: Zimmerplan 1. Semester, Stand 5.11.2026. Inoffiziell: Prüfungen, kurzfristige Reservationen und abgeschlossene Türen kennt die App nicht.

## Neuer Stundenplan (z.B. 2. Semester)

Mit den Untis-PDFs Klassenplan (KU), Zimmerplan-Übersicht (RU) und Zimmer-Einzelpläne (RE):

```bash
python3 tools/parse.py KU.pdf
python3 tools/parse_ru.py RU.pdf RE.pdf
python3 tools/build_simple.py
python3 tools/inject.py tools/template.html simple.json index.html
```
