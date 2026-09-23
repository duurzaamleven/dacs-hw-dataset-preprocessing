# Gebruiksvoorwaarden van de DACS-HW-dataset

Deze repository verwerkt de openbare meetdata van **DACS-HW** (Digitale Aggregatie en Collectieve
Sturing van Hybride Warmtepompen), een MOOI-project (Missiegedreven Onderzoek, Ontwikkeling en
Innovatie, regeling Gebouwde Omgeving 2022), referentienummer **MOOI322001**, uitgevoerd door een
consortium van zeven partijen: Inversable, Voorstroom, Samen Energie Neutraal, Enexis, Enablemi,
Intergas en de TU/e. Het project is in december 2025 afgerond. De ruwe dataset staat **niet** in
deze git-repo (`data/` is gitignored) en wordt niet door of via deze repo verspreid.

Deze paragraaf was op 17-09-2026, bij het ophalen van de dataset, nog niet nagelopen (zie
`literatuur/MANIFEST.md` van de afnemende repo). Dat is hieronder alsnog gedaan.

## De twee datasets, en twee verschillende regimes

DACS-HW publiceert via **KITE** (Kennis- en Dataplatform Individuele Technieken, RVO) twee losse
downloads, elk met een eigen data-eigenaar en een eigen voorwaarde. Bron van de citaten hieronder:
de KITE-projectpagina *DACS-HW · Kennis- en Dataplatform Individuele Technieken (KITE) · Kennisdelen
RVO*, opgehaald 17-09-2026 (in de afnemende repo bewaard als
`literatuur/dacs-hw/DACS-HW · Kennis- en Dataplatform Individuele Technieken (KITE) · Kennisdelen
RVO.mhtml`), sectie "Dataset toelichting", versie **"1 sept 2026"** zoals de pagina zelf vermeldt.

### 1. Woningdata (`dataset-dacs-hw.zip`: warmtepompen en slimme meters)

> *"Dataset Auteur: Projectgroep DACS-HW. Dataeigenaar: Projectgroep DACS-HW, aanspreekpunt
> Inversable B.V."*
>
> *"Licentie en gebruik: De dataset die aan de basis ligt van DACS-HW is beschikbaar voor onderzoek
> en analyses met een maatschappelijk doel. Gebruik van de data moet gemeld worden bij
> data@inversable.com en de uitkomsten, resultaten en/of analyses moeten onder dezelfde
> gebruiksvoorwaarden gedeeld met de KITE community."*

Geen licentienaam (geen CC BY, CC0, ODbL). "Beschikbaar voor onderzoek en analyses met een
maatschappelijk doel" is een **doelbeperking**, geen vrijgave voor herverspreiding.

### 2. Enexis-onderstationdata (`wijktrafo_15min.zip`: stroom, spanning, vermogen van de wijktrafo)

> *"Dataset Auteur: Projectgroep DACS-HW. Dataeigenaar: Enexis (contact via kite@rvo.nl)."*
>
> *"Licentie en gebruik: De dataset is beschikbaar voor onderzoek en analyse met een maatschappelijk
> doel. Voor het downloaden van de data vraagt Enexis: Het doel of de onderzoeksvraag van de
> gebruiker. Het verkregen inzicht uit de dataset. Naam en e-mailadres wordt gevraagd voor contact
> over de data. (contact verloopt via KITE, naam en email worden niet met Enexis gedeeld)."*

Andere data-eigenaar dan de woningdata (**Enexis**, niet de DACS-HW-projectgroep/Inversable), en een
eigen toegangsprocedure: een downloadformulier waarin doel en verkregen inzicht worden opgegeven,
niet een vrije download-URL. Ook hier geen licentienaam.

## Wat dit betekent voor deze repo

1. **Melden vóór gebruik.** Voor de woningdata: <data@inversable.com>. Voor de Enexis-trafodata loopt
   contact via <kite@rvo.nl>; bij het downloaden is bovendien al het doel en het beoogde inzicht
   opgegeven, wat zelf al een vorm van vooraf melden is. Beide vóórdat er iets naar buiten gaat. Of
   de meldplicht ook geldt voor intern gebruik zonder publicatie is niet vastgesteld; de formulering
   suggereert van wel.
2. **Analyseresultaten delen met de KITE-community**, onder dezelfde voorwaarden (letterlijk alleen
   zo geformuleerd voor de woningdata; voor de Enexis-data staat het niet met zoveel woorden, maar
   dezelfde maatschappelijk-doel-beperking geldt). Deze repo doet zelf geen analyse, maar wie de
   uitvoer gebruikt, valt onder deze voorwaarde.
3. **Maatschappelijk doel.** Beide datasets zijn beperkt tot onderzoek en analyse met een
   maatschappelijk doel; wat daar precies wel en niet onder valt, is op de KITE-pagina niet verder
   gedefinieerd. **Niet vastgesteld.**
4. **De ruwe data blijft buiten versiebeheer**, net als alles wat eruit volgt. Geen van beide
   voorwaarden geeft een recht de dataset zelf te herpubliceren.
5. **Het eindrapport en de twee TU/e-papers vallen hier niet onder.** Voor het eindrapport
   (*Digitale Aggregatie en Collectieve Sturing van Hybride Warmtepompen, Openbare versie*, 23
   januari 2026) is in de tekst zelf geen expliciete copyrightvermelding of licentie aangetroffen
   (gecontroleerd op de woorden "copyright", "rechten voorbehouden" en "©"); **niet vastgesteld** of
   er een specifieke licentie op rust. Bij afwezigheid van een aangetroffen licentie wordt hier het
   voorzichtige uitgangspunt gehanteerd dat ook rapporten van een projectconsortium doorgaans
   strenger zijn dan de dataset zelf (zelfde lijn als bij vergelijkbare MOOI-/KITE-rapporten):
   citeren met bronvermelding kan, meesturen of overnemen niet. De twee papers zijn gepubliceerd bij
   IEEE (ISGT Europe 2024, EEEIC/I&CPS Europe 2025) en dragen een eigen IEEE-copyright; ook die
   worden hier alleen geciteerd, niet overgenomen. Geen van de drie staat daarom in deze repo; ze
   staan (met sha256) vermeld in `literatuur/MANIFEST.md` van de afnemende repo.

## Privacy

`household_monthly.csv` bevat gepseudonimiseerde huishoudrijen (`custom_id`), stabiel binnen deze
dataset maar expliciet **niet** te koppelen aan de kwartierbestanden (`README_dataset.md`, sectie
"Privacy": *"This `id` is stable across months within this dataset. It can not directly be compared
with the 15min data."*). Deze repo voegt geen andere bron toe die heridentificatie mogelijk zou
maken. Of er een DPIA, een privacyverklaring of een ethische toetsing is uitgevoerd, is met de
middelen van deze repo **niet vastgesteld**; de KITE-pagina en het archief zelf vermelden dit niet
expliciet.

## Hoe je de datasets zelf verkrijgt

### Woningdata

- <https://data.inversable.cloud/dacs-hw/dataset-dacs-hw.zip> (rechtstreekse downloadlink, van de
  KITE-pagina), 2.140.045 bytes, sha256
  `f251e66129f3eae25490d799f2e0cf7dae2290adcd7527476c05fb28aefc2bcf`, opgehaald 17-09-2026. Bevat
  zes bestanden: `heatpump_15m.csv`, `heatpump_steering_15m.csv`, `smartmeters_gas_hourly.csv`,
  `household_monthly.csv`, `metadata.csv` en `README_dataset.md`.

### Enexis-onderstationdata

Geen vrije downloadlink: de KITE-pagina verwijst naar een **downloadformulier** waarin je doel en
onderzoeksvraag en het beoogde inzicht opgeeft (zie het citaat hierboven); Enexis krijgt zelf geen
naam of e-mailadres, dat blijft bij KITE. Deze repo bevat daarom geen herhaalbare URL voor dit
archief. Het exemplaar waarmee deze repo gebouwd is: `wijktrafo_15min.zip`, 1.991.982 bytes, sha256
`23b1d080d57f5fbb950f82885a8455826a1e5a134989dae4a32184785ef87c93`, opgehaald 17-09-2026. Bevat drie
bestanden: `wijktrafo_15min.csv`, `Toelichting DACS-HW Enexis Dataset.txt` en een voorbeeldfiguur van
de herbemonstering.

Zet beide archieven ongewijzigd in `data/raw/`. **Pak ze niet uit**: de pijplijn leest streamend uit
de zips (de set is klein, samen 17 MB uitgepakt, dus dit is voor de snelheid geen vereiste zoals bij
grotere datasets, maar wel de consistente werkwijze).

De KITE-pagina noemt voor beide datasets **"Versie 1 sept 2026"**; de sha256 hierboven is het
sluitende bewijs van welk exemplaar precies is verwerkt, niet de versietekst op de pagina.
