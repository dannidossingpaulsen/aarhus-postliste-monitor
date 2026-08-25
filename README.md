# Aarhus postliste-monitor

Overvåger indgående post for:
- MBA- (Borgmesterens Afdeling)
- MTM- (Teknik og Miljø)

Ved hver kørsel hentes de seneste 10 kalenderdage, så forsinkede efterregistreringer fanges.

## Test nu
1. Opret et offentligt GitHub-repository, fx `aarhus-postliste-monitor`.
2. Upload alle filer fra denne pakke til repoets rod.
3. Gå til **Actions** → **Aarhus postliste monitor** → **Run workflow**.
4. Når kørslen er grøn, åbn `data/latest.json`.

Hvis `technical_status` er `ok`, kan GitHub nå kommunens API.

## Vigtige filer
- `data/latest.json`: seneste nye/ændrede poster + teknisk status.
- `data/all-current.json`: alle poster i det aktuelle 10-dages vindue.
- `data/seen.json`: kendte dokument-ID'er, så dubletter undgås.

Første kørsel vil markere alle poster i 10-dages-vinduet som nye. Derefter kun nye/ændrede.

Når repoet er offentligt, kan ChatGPT læse:
`https://raw.githubusercontent.com/DIT-BRUGERNAVN/aarhus-postliste-monitor/main/data/latest.json`
