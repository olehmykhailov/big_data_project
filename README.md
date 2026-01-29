# Dokumentacja Projektu: ETL NBP API & Analytics

**Wykonali:** 
* Oleh Mykhailov
* Katsiaryna Krupieńka
* Krzystof Bajda

**Cel projektu:** Pozyskiwanie danych o kursach walut oraz cenach złota z wykorzystaniem NBP API, ich składowanie oraz wizualizacja.

## 1. Ogólny pipeline i architektura

* **Baza danych:** Amazon RDS (PostgreSQL).
* **Pozyskiwanie metadanych:** Pobieranie listy walut ze strony Wikipedii (on-demand).
* **Orkiestracja:** Funkcja AWS Lambda + Amazon EventBridge Scheduler (CRON) do codziennego pobierania danych.
* **Wizualizacja:** Dashboard Power BI połączony bezpośrednio z bazą danych.

---

## 2. Baza danych

### 2.1 Struktura tabel

1. **`currencies`** – Słownik walut:
* `code`: Międzynarodowy kod waluty (np. USD).
* `name`: Nazwa waluty w języku polskim.
* `table_type`: Typ tabeli w NBP API (A, B lub C).


2. **`currencies_rates`** – Historyczne kursy walut względem PLN:
* `code`: Międzynarodowy kod waluty.
* `rate_date`: Data publikacji kursu.
* `rate`: Wartość kursu.


3. **`gold_prices`** – Ceny złota:
* `price_date`: Data publikacji ceny.
* `price_pln`: Cena za 1 gram złota w PLN.



### 2.2 Relacje (ORM)

* `currencies (code)` **1 -> *** `currencies_rates (code)`
* `Calendar` **1 -> *** `currencies_rates (rate_date)`
* `Calendar` **1 -> *** `gold_prices (price_date)`

### 2.3 Role i uprawnienia

* **`nbp_user`**: Wykorzystywany przez serwis ETL.
* Uprawnienia: `INSERT`, `UPDATE`, `DELETE`, `CONNECT`, `USAGE ON SCHEMA PUBLIC`.


* **`dashboard_user`**: Wykorzystywany przez Power BI.
* Uprawnienia: `SELECT`, `CONNECT`, `USAGE ON SCHEMA PUBLIC`.

---

## 3. Specyfikacja NBP API

Narodowy Bank Polski udostępnia dane poprzez REST API. Kluczowym elementem jest zrozumienie podziału na tabele, ponieważ każda z nich ma inną częstotliwość aktualizacji i zestaw walut.

### 3.1 Charakterystyka tabel kursów walut

API NBP dzieli kursy walut na trzy główne kategorie:

| Tabela | Opis | Częstotliwość aktualizacji |
| --- | --- | --- |
| **Tabela A** | Kursy średnie walut wymienialnych. | Każdy dzień roboczy (pon-pt), zazwyczaj między 11:45 a 12:15. |
| **Tabela B** | Kursy średnie walut niewymienialnych (rzadsze waluty). | Raz w tygodniu – w każdą środę (chyba że jest to dzień wolny). |
| **Tabela C** | Kursy kupna i sprzedaży walut wymienialnych. | Każdy dzień roboczy (pon-pt), zazwyczaj między 7:45 a 8:15. |

### 3.2 Szczegóły zawartości

1. **Tabela A**: Zawiera najpopularniejsze waluty świata (USD, EUR, GBP, CHF, JPY itd.). Jest to podstawowe źródło danych dla większości analiz finansowych.
2. **Tabela B**: Obejmuje waluty egzotyczne, które nie wykazują dużej zmienności płynności (np. afgani, birr etiopski). Ważne: przy pobieraniu danych historycznych należy pamiętać, że daty w tej tabeli są odstępach siedmiodniowych.
3. **Tabela C**: Jedyna tabela zawierająca spread (różnicę między kupnem a sprzedażą). W Twoim obecnym schemacie bazy danych (`currencies_rates`) przechowujesz jeden parametr `rate` – jeśli planujesz używać Tabeli C, warto rozważyć dodanie pól `bid` (kupno) i `ask` (sprzedaż).

### 3.3 Ceny złota

Dane o złocie są obsługiwane przez osobny punkt końcowy (endpoint). NBP publikuje cenę 1 grama złota o próbie 1000 w każdy dzień roboczy. Jest to cena wyliczana na podstawie notowań rynkowych i służy m.in. do celów statystycznych oraz podatkowych.

---

## 4. ETL-service

### 4.1 Tryby pracy

* **Daily (Codzienny)**: Pobieranie aktualnych danych (tryb domyślny, uruchamiany przez Amazon EventBridge).
* **Historical (Historyczny)**: Pobieranie danych wstecz (on-demand). Wymaga parametrów `start_date` oraz `end_date`.
> **Uwaga:** Należy uwzględnić, że różne tabele NBP mają różne daty początkowe publikacji danych.



### 4.2 Continuous Deployment (CD)

* Aplikacja jest konteneryzowana przy użyciu **Dockera**.
* Obrazy są przesyłane do **AWS Elastic Container Registry (ECR)** i wdrażane w środowisku AWS.

---

## 5. Dashboard (Power BI)

### 5.1 Strony raportu

* **Kursy walut (Currency Rates)**:
* Wykres liniowy w czasie.
* Filtry: waluta, rok.
* Karty (KPI) z podstawowymi metrykami statystycznymi (min, max, średnia).


* **Ceny złota (Gold Prices)**:
* Wykres liniowy trendu cen złota.
* Filtry: zakres dat, rok.
* Karty z aktualną ceną i zmianą procentową.

## 6. Analiza

### 6.1 Analiza cen złota i cen walut

* W 2022 ewidentnie widać spadek jednych z najpopularniejszych cen walut takich jak EURO czy Dolar Amerykański i jednoczesny dynamiczny wzrost cen złota. Taka reakcja rynku najprawdopodobniej jest spowodowana rosnącymi niepokojami wśród inwestorów związanych z konfliktami zbrojnymi na świecie i napiętą sytuacją geopolityczną. 
* Spadki Euro spowodowane są wojną w regionie, tuż za granią Unii Europejskiej a Stany Zjednoczone angażują się w konflikty zbrojne oraz prezydent podejmuje mało przewidywalne decyzje, które zachęcają prywatnych inwestorów do przeniesienia pieniędzy w aktywo nie powiązane ze Stanami Zjednoczonymi, podobną dynamikę możemy zauważyć w bankach centralnych, które skupują złoto jednocześnie powoli odchodząc od Dolara Amerykańskiego choć w dalszym ciągu Dolar Amerykański pozostaje bardzo ważną walutą rezerwową dla wielu państw.