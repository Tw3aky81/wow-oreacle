# Oreacle — Design Document

> **Repository:** `wow-oreacle`  
> **Applicatie:** Oreacle  
> **Status:** Werkdocument — ontwerp vóór implementatie  
> **Laatste update:** 19 oktober 2026

## 1. Doel en uitgangspunten

Oreacle is een lokale **Python command-line application** voor het registreren en analyseren van activiteiten in **World of Warcraft**, met als uiteindelijke domein mining, prospecting en jewelcrafting.

Het project vervangt op termijn een bestaande spreadsheet, maar hoeft de spreadsheet niet letterlijk te kopiëren. De spreadsheet dient als **functionele referentie**, niet als verplicht datamodel.

### Primair doel: leren ontwerpen en bouwen

Oreacle is in de eerste plaats een **persoonlijk leerproject**, met een richtbudget van **20–40 uur** voor een afgeronde eerste versie. Het project moet helpen om zelfstandig van requirements naar een werkende applicatie te gaan, buiten de structuur van tutorials.

Bijzondere aandacht gaat naar:

- Softwarearchitectuur en het toewijzen van verantwoordelijkheden.
- Python-datastructuren, classes/dataclasses en domeinmodellering.
- Persistentie, validatie, foutafhandeling en testbaarheid.
- Kleine, bewuste ontwerpbeslissingen en onderhoudbare code.
- Leren refactoren om concrete redenen, zonder overengineering.

**Werkafspraak:** de ontwikkelaar ontwerpt en implementeert zelf. De mentor stelt vragen, geeft hints, bespreekt alternatieven en reviewt code; volledige oplossingen alleen op verzoek.

## 2. Huidige workflow en probleem

### Mining

1. Kies een zone en route uit de WoW **Routes**-addon.
2. Noteer de starttijd.
3. Mine één ronde of herhaal dezelfde route gedurende een periode.
4. Noteer de eindtijd.
5. Controleer de inventory en tel verzamelde materialen.
6. Registreer de run in de spreadsheet: datum, starttijd, zone, route (momenteel soms in notities), duur, ore per type en quality, lumber, concurrentie en eventuele notities.
7. Bekijk berekeningen zoals totaal ore, ore per uur en lumber per uur.

**Pijnpunt:** veel handmatig administratief werk, vooral tijdstippen, materiaalhoeveelheden en registratie. Oreacle moet de registratie vereenvoudigen en vergelijkingen tussen runs mogelijk maken.

### Andere spreadsheetworkflows

- **Prospecting:** gebruikte ores en hoeveelheden, output, kosten en rendement.
- **Jewelcrafting:** reagentkosten, geproduceerde items, verkoopprijzen, Auction House-cut, nettowinst en ROI.

Die workflows horen bij de langetermijnvisie, **niet** bij de eerste MVP.

Een handmatig onderhouden tab voor **Market Prices** is geen gewenst onderdeel van het ontwerp: de onderhoudslast weegt niet op tegen de meerwaarde. Eventuele AH-prijsintegratie moet later afzonderlijk worden beoordeeld.

Het spreadsheet-dashboard is een niet-functioneel concept en valt buiten scope.

## 3. Functionele doelstelling van v0.1

**Oreacle v0.1 is een mining-run tracker.** De applicatie moet mining sessies kunnen starten en stoppen, de opbrengst registreren, duurzaam bewaren en de efficiëntie inzichtelijk maken.

### MVP — beoogde functionaliteit

- Een mining sessie starten via de CLI, met keuze van **zone** en **route**.
- Een actieve sessie stoppen; start- en eindtijd worden door Oreacle vastgelegd.
- Verzamelde materialen na afloop invoeren.
- Een run lokaal en duurzaam bewaren in SQLite.
- Eerdere runs raadplegen.
- Totaal ore, ore per uur en eventueel lumber per uur berekenen.
- De opbrengst van runs en routes vergelijken; de exacte eerste rapportages moeten nog worden afgebakend.
- Ongeldige invoer en ongeldige toestandsovergangen afhandelen.
- De kernlogica met geautomatiseerde tests controleren.

### Buiten v0.1 / later onderzoeken

- Prospecting- en jewelcraftingfunctionaliteit.
- Auction House-prijzen of prijshistoriek.
- Dashboard of grafische interface.
- REST API.
- CSV-import/export.
- Uitgebreide rapportages over weekdagen en tijdsblokken.
- CLI-beheer van zones en routes.
- Automatische import uit de Routes-addon.
- Ondersteuning van materialen uit toekomstige WoW-expansions.

**Nog te beslissen voor v0.1:** of het achteraf bewerken/corrigeren van voltooide runs al tot de minimale release behoort. Het is wel een gewenste functie.

## 4. Gewenste analyses

De data moet op termijn antwoorden kunnen geven op:

1. Hoeveel ore (en lumber) leverde een run per uur op?
2. Wat is de gemiddelde opbrengst van een bepaalde route?
3. Welke route presteert het beste binnen een zone?
4. Welke zone heeft gemiddeld de hoogste opbrengst?
5. Welke dagen en tijdstippen leveren gemiddeld het beste resultaat op?

**Ontwerpprincipe:** bewaar de brongegevens (waaronder volledige start- en eindtijd) zodat analyses later kunnen worden toegevoegd, maar implementeer niet alle analyses in v0.1.

**Open statistische beslissing:** het rekenkundig gemiddelde van afzonderlijke `ore/hour`-waarden is niet hetzelfde als `som(ore) / som(duur)`; voor route- en zonevergelijkingen moet nog worden gekozen welke maatstaf wordt gebruikt, en waarom. Ook concurrentie kan de interpretatie beïnvloeden.

## 5. Eerste architectuur

De gekozen **richting** is een eenvoudige afhankelijkheidsketen:

```text
CLI  →  Mining (domeinlogica)  →  Persistence  →  SQLite
```

### CLI

- Ontleed commando's.
- Toont keuzemenu's, stelt vragen en verzamelt invoer.
- Zet terminalinvoer om naar bruikbare Python-waarden.
- Roept de mining-functionaliteit aan.
- Toont resultaten en begrijpelijke foutmeldingen.
- Bevat bij voorkeur **geen mining-businessregels**.

### Mining-module

- Modelleert `MiningRun` en bijbehorende regels.
- Controleert domeinvalidatie, bijvoorbeeld niet-negatieve hoeveelheden en geldige tijdsrelaties.
- Beheert de levenscyclus van een mining run.
- Bepaalt of een nieuwe run mag starten.
- Bevat berekeningen en uiteindelijk mining-analyses.
- Vraagt zo nodig informatie op via de persistencelaag, zonder zelf SQL te schrijven.
- Kent bij voorkeur geen `input()` of `print()`.

### Persistence-module

- Slaat runs op en haalt ze op via Python's ingebouwde `sqlite3`.
- Kan bijvoorbeeld de actieve run opzoeken.
- Handelt databaseoperaties en transacties af.
- Hoeft de reden achter een domeinregel niet te bepalen.

**Belangrijke grens:** CLI mag Mining aanroepen; Mining hoeft CLI niet aan te roepen. Vermijd wederzijdse imports en onnodige abstractielagen. De precieze bestandsstructuur, functies en eventuele serviceclasses liggen nog niet vast.

### Validatie

- **Invoervalidatie (CLI):** is tekst als integer of datum/tijd te interpreteren?
- **Domeinvalidatie (Mining):** mag een waarde of toestand binnen een mining run voorkomen?
- **Database-integriteit (Persistence/SQLite):** zorg waar nuttig dat opslag niet in een tegenstrijdige toestand terechtkomt.

Een actie kan een waarde of object teruggeven, of bij fouten een exception gebruiken. Dit is **nog niet beslist**; een eenvoudige succes-boolean is niet automatisch de beste API.

## 6. Domeinmodel: `MiningRun`

Een `MiningRun` stelt één concrete mining sessie voor, vergelijkbaar met één rij in de huidige mining-sheet, maar met eigen gedrag en regels.

### Voorlopige informatiecategorieën

| Categorie | Gegevens |
| --- | --- |
| Identiteit | Uniek ID (vorm nog te bepalen) |
| Context | Zone, route, concurrentie, optionele notitie |
| Tijd | Starttijd, eindtijd (aanvankelijk onbekend) |
| Miningopbrengst | Copper, Tin en Silver, elk in Q1/Q2/Q3 |
| Overige opbrengst | Lumber; eventuele andere huidige materialen nog te verifiëren |
| Levenscyclus | ACTIVE / INCOMPLETE / COMPLETED |

De exacte attributen, types, standaardwaarden, representatie van de negen ore-hoeveelheden en eventuele nullable velden moeten nog worden ontworpen.

Een Python **`@dataclass`** is voorlopig de voorkeursrichting, omdat het object vooral samenhangende gegevens representeert maar ook methods kan bevatten. Dit is nog geen uitgewerkte classdefinitie.

### Berekende gegevens

- `total_ore` wordt berekend uit de relevante ore-hoeveelheden.
- `ore_per_hour = total_ore / duration_in_hours`.
- `lumber_per_hour = lumber / duration_in_hours`.
- De duur volgt uit start- en eindtijd.

**Besluit:** sla in beginsel de oorspronkelijke gegevens op en **bereken afgeleide waarden wanneer nodig**. Dit voorkomt dat oude berekende waarden inconsistent worden wanneer rekenregels veranderen.

Berekeningen zijn alleen geldig als de benodigde gegevens bestaan en de duur positief is; gedrag bij een actieve/onvolledige run moet nog expliciet worden ontworpen.

### Correcties

Een gebruiker moet uiteindelijk invoerfouten in bestaande runs kunnen corrigeren (bijvoorbeeld een verkeerd getelde hoeveelheid). De precieze regels en de timing binnen de MVP zijn nog open.

## 7. Levenscyclus van een mining run

Het voorlopig overeengekomen toestandsmodel:

```text
ACTIVE  --stop + eindtijd bewaren-->  INCOMPLETE
INCOMPLETE  --materialen volledig en geldig-->  COMPLETED
```

| Status | Betekenis | Starttijd | Eindtijd | Materialen | In statistieken? |
| --- | --- | --- | --- | --- | --- |
| `ACTIVE` | Mining is bezig | Ja | Nee | Nog niet geregistreerd | Nee |
| `INCOMPLETE` | Gestopt, invoer moet nog worden afgerond | Ja | Ja | Ontbrekend of onvolledig | Nee |
| `COMPLETED` | Run is afgerond en valide | Ja | Ja | Volledig | Ja |

### Regels

- Er mag **maximaal één ACTIVE run** tegelijk bestaan.
- Meerdere INCOMPLETE runs zijn toegestaan en blokkeren een nieuwe run niet.
- Alleen COMPLETED runs tellen mee voor aggregaties en vergelijkingen.
- Een INCOMPLETE run kan later worden aangevuld, met behoud van de **oorspronkelijke eindtijd**.
- Een run is niet automatisch COMPLETED omdat de eindtijd bekend is.

Een expliciet persistent `status`-attribuut is gekozen om deze drie toestanden te representeren. **Consistentie tussen status en tijden** moet door de applicatie bewaakt worden.

### Start-workflow (conceptueel)

1. De CLI ontvangt `oreacle mining start`.
2. De gebruiker kiest zone en route.
3. Mining vraagt via Persistence of al een ACTIVE run bestaat.
4. Als er een actieve run is, wordt het starten geweigerd met een duidelijke melding.
5. Anders wordt de nieuwe ACTIVE run met starttijd opgeslagen.

### Stop-workflow (overeengekomen volgorde)

1. Controleer of er een ACTIVE run bestaat.
2. Registreer de **eindtijd** en zet de status op INCOMPLETE.
3. **Sla dit direct duurzaam op** voordat de gebruiker materiaalhoeveelheden gaat invoeren.
4. Vraag de verzamelde materialen aan de gebruiker.
5. Valideer de volledige invoer.
6. Werk de INCOMPLETE run bij en zet de status op COMPLETED.
7. Sla de gegevens en de statuswijziging samen betrouwbaar op.

De opslag van materialen + statuswijziging hoort logisch in één SQLite-transactie: bij een fout mag geen half bijgewerkte COMPLETED run achterblijven.

**Crashscenario:** valt het programma uit nadat de eindtijd is opgeslagen maar vóór volledige materiaalinvoer, dan blijft de run INCOMPLETE en kan deze later worden afgewerkt. Valt de pc uit vóór het uitvoeren van `stop`, dan is de echte eindtijd onbekend; een toekomstige mogelijkheid tot handmatige tijdcorrectie kan daarvoor nodig zijn.

## 8. Zones en routes

Een zone kan **meerdere routes** bevatten. De route hoort als zelfstandig gegeven in een run, niet uitsluitend in notities.

### Voor v0.1

- De gebruiker kiest zone en daarna route via **genummerde terminalmenu's**.
- De lijst met beschikbare zones en routes wordt in eerste instantie **handmatig bijgehouden in een JSON-bestand**.
- JSON dient als eenvoudige configuratie/keuzelijst; **SQLite** dient voor de historie van mining runs.
- De precieze JSON-structuur is nog niet definitief.

Voorbeeld van een mogelijke configuratie (niet bindend):

```json
{
  "Eversong Woods": ["Northern Loop", "Southern Loop"],
  "Zul'Aman": ["Eastern Route", "Western Route"]
}
```

### Later

- CLI-commando's voor beheer, bijvoorbeeld `oreacle zone add <naam>` en `oreacle route remove <naam>`; de commandosyntax is voorlopig illustratief.
- Mogelijk importeren of synchroniseren van routegegevens uit de WoW **Routes**-addon en de bijbehorende SavedVariables. De exacte bestandslocatie en het formaat moeten nog onderzocht worden.
- Historische runs moeten begrijpelijk blijven als een route later wordt hernoemd of uit de actuele keuzelijst verdwijnt.

## 9. Voorgestelde ontwikkeling in milestones

Dit is een **werkhypothese**, geen vaste architectuur of deadline.

| Milestone | Doel | Afbakening |
| --- | --- | --- |
| **1. Domeinmodel** | `MiningRun` ontwerpen en testen | Dataclass/attributen, toestanden, validatie, berekeningen; nog geen CLI/SQLite |
| **2. Persistentie** | Runs duurzaam opslaan en ophalen | SQLite, actieve run zoeken, transacties |
| **3. CLI & workflows** | Start/stop en materiaalinvoer bruikbaar maken | Commando's, numerieke zone-/routeselectie uit JSON, foutmeldingen |
| **4. Inzicht** | Historie en eerste routevergelijking | Lijst/overzicht, statistieken van COMPLETED runs |
| **5. Afronding** | V0.1 als zelfstandig project opleveren | Tests, README, refactoring, foutscenario's |

**Indicatief tijdsbudget (32 uur):** requirements/ontwerp 5u; CLI en domeinlogica 10u; persistentie 6u; analyse/rapportage 5u; tests/refactoring/documentatie 6u. Dit is geen toezegging dat elke functie binnen dit budget zal passen: beperk scope wanneer nodig.

### Directe volgende stap

Ontwerp eerst zelf een **schets van `MiningRun`**: classdefinitie, attributen, type hints en eventuele standaardwaarden; **nog geen methods, SQL of CLI**. Bespreek daarna de representatie van materialen en optionele velden vóór implementatie.

## 10. Open ontwerpvragen / decision log

Deze vragen blijven bewust open. Beslis ze op het moment dat ze relevant worden.

- [ ] Exacte attributen en type hints van `MiningRun`.
- [ ] Negen ore-hoeveelheden als losse attributen of gegroepeerde datastructuur?
- [ ] Hoe worden ontbrekende materiaalgegevens onderscheiden van een echte hoeveelheid `0`?
- [ ] Welke concurrentiewaarden en eventuele overige materialen zijn nodig?
- [ ] Hoe worden start-/eindtijden opgeslagen en vergeleken (tijdzone, datetime-formaat)?
- [ ] Hoe gedragen berekeningen zich voor ACTIVE en INCOMPLETE runs of een duur van nul?
- [ ] Hoe zien domeinfouten en returnwaarden er concreet uit?
- [ ] Wat is de minimale set commando's voor v0.1?
- [ ] Welke eerste vergelijkingsmaatstaf voor routes/zones: gemiddelde van run-rates of totale ore / totale duur?
- [ ] Welke mutaties aan COMPLETED runs zijn al in v0.1 toegestaan?
- [ ] Wat gebeurt er bij een fout na stoppen, en hoe rondt de gebruiker een oude INCOMPLETE run af?
- [ ] Welke persistentie-constraints bewaken geldige statussen en maximaal één ACTIVE run?
- [ ] Welke velden bewaart SQLite en hoe blijft historie stabiel bij routehernoeming?
- [ ] Definitieve JSON-structuur en locatie van de zone-/routeconfiguratie.

## 11. Ontwerpprincipes en toetsingsvragen

Gebruik dit document tijdens implementatie en code reviews. Vraag bij belangrijke beslissingen:

1. **Is dit noodzakelijk voor v0.1?** Zo niet, kan het wachten?
2. **Is de verantwoordelijkheid helder?** Hoort dit bij CLI, Mining of Persistence?
3. **Kan ik de mining-logica testen zonder terminal of database?**
4. **Bewaren we brongegevens in plaats van onnodig afgeleide waarden?**
5. **Wat gebeurt er bij ongeldige invoer, onderbroken processen en half voltooide operaties?**
6. **Hebben we deze abstractie nu echt nodig, of maken we het onnodig complex?**
7. **Kan ik uitleggen waarom ik deze oplossing koos en welk alternatief ik verwierp?**

> **Documentdiscipline:** wijzig dit ontwerp wanneer nieuwe inzichten een betere beslissing opleveren. Noteer bij materiële wijzigingen **wat** veranderd is en **waarom**. Het ontwerp is een hulpmiddel voor het denken, geen onveranderlijk contract.

## 12. Wijzigingslog

| Datum | Wijziging |
| --- | --- |
| 2026-10-19 | Eerste ontwerpdocument opgesteld op basis van het discovery- en architectuurgesprek. |
