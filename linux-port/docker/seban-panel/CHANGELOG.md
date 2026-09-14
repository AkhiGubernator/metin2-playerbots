# Zmiany
## 2026-09-15 00:11 CEST · 1.48.0

- Naprawiono "Internal Server Error" przez pierwsze ~5 minut po restarcie/aktualizacji: panel sam tworzy potrzebne tabele przy starcie zamiast czekać, aż kolektor je stworzy w swoim własnym cyklu; kolektor też ponawia szybko (10s) zamiast czekać pełne 5 minut, gdy pierwsza próba się nie uda (np. baza jeszcze się budzi). Zgłoszone przez graczy (sizowski, 23:16).
- `/manage`: docelowa liczba botów, respawn na mapach i wyłączanie skrzyni startowej — te trzy kontrolki wymagają naszych własnych skryptów questów, których świeży/publiczny install nie ma. Ukryte domyślnie, włączone na tym VPS-ie osobną flagą.
- Poprawiono błędne granice map Las, Czerwony Las i Wieża Demonów (błąd we wszystkich trzech współrzędnych bazowych i/lub rozmiarach) — zweryfikowane wprost z plików `Setting.txt` silnika.
- Zaktualizowano rdzeń Playerbots do wydania Tieru 2.0.48; przełączniki bez skrzyni ucznia i bez szkatułek blasku księżyca przetrwały. Liczba botów podniesiona do 1050 (+150).

## 2026-09-14 23:25 CEST · 1.47.0

- `/player/`: logi na żywo zaczynają się teraz same przy otwarciu strony (bez klikania), zbierają linie zamiast je zamieniać (nie "znikają" między odświeżeniami przy zatłoczonym logu) i kolorują wpisy jak w panelu Tieru.
- `/player/`: przycisk "Teleportuj moją postać do sklepu" przy Sklepie offline — przenosi na dokładne współrzędne straganu, nawet jeśli bot akurat nie odpowiada na status live.

## 2026-09-14 23:16 CEST · 1.46.0

- Naprawiono ranking "Skuteczność ulepszeń": silnik loguje porażkę jako `REMOVE (REFINE FAIL)`, a nie `REFINE FAIL` (który ma zero wpisów w bazie) — stąd wszyscy pokazywali 100%. Teraz zgadza się z wartością widoczną na `/player/`.
- `/player/`: nowa sekcja "Dziennik zdarzeń bota (logi na żywo)" — te same logi rdzenia gry co w panelu Tieru, z przyciskiem odświeżania na żądanie (co 4s) i kopiowania do schowka.

## 2026-09-14 23:05 CEST · 1.45.0

- Karuzela rankingów na dashboardzie sama się teraz przewija co 8s, z animacją wjazdu slajdu; kliknięcie strzałki/punktu resetuje timer.
- Puste rankingi (np. "Bossy" — na tym serwerze jeszcze nikt nie zabił bossa) pokazują teraz w karuzeli "Brak danych", zamiast całkowicie niewidocznego, pustego slajdu.
- Dodano ranking "Skuteczność ulepszeń" (% udanych ulepszeń, minimum 20 prób żeby jednorazowy szczęśliwy strzał nie lądował na #1) — w `/rankings/` i w karuzeli dashboardu.
- Naprawiono wiersze w `/rankings/`, które "rozjeżdżały się" wysokością, gdy niektóre boty nie mają danego przedmiotu (brak ikonki = niższy wiersz).

## 2026-09-14 22:42 CEST · 1.44.1

- Zakładki stron magazynu (Strona I/II/III) i obramówka siatki magazynu mają teraz kolor aktywnego motywu, zamiast sztywnego niebieskiego.

## 2026-09-14 22:26 CEST · 1.44.0

- Tooltipy ekwipunku pokazywały złe wartości bazowe: obrona/atak nie uwzględniały bonusu z ulepszenia, więc np. Różowa Szata+9 pokazywała 29 obrony zamiast rzeczywistych 83. Naprawione dla broni i zbroi (ciało, głowa, tarcza, buty).
- Wiele etykiet bonusów na przedmiotach było przesuniętych o jeden numer w tabeli tłumaczeń (np. "Silny przeciw mistykom" zamiast "Silny przeciw nieumarłym", "Odporność na dzwony" zamiast "na wachlarze") — cała tabela zweryfikowana krzyżowo z panelem Tieru i poprawiona. Znany, niepoprawiony wyjątek: jeden rzadki bonus (odbicie strzał) nadal pokazuje się jako "Odporność na sury" — ten sam brak jest też w źródle Tieru, wymaga dalszego śledztwa.

## 2026-09-14 22:04 CEST · 1.43.0

- `/player/`: magazyn ma teraz strony (I/II/III) jak w grze i uwzględnia rozmiar przedmiotu (2-3 sloty wysokości) — przedmioty nie nakładają się już na siebie.
- `/player/`: nagłówek postaci pokazuje teraz czas gry, ostatnie logowanie, Smocze Monety, małżeństwo i gildię jako osobne znaczniki; usunięto zbędną sekcję "Smocze Monety i VIP" (te wartości są teraz w nagłówku).
- `/player/`: naprawiono ikonki umiejętności — panel próbował je ładować z `127.0.0.1:7788`, adresu, który w przeglądarce operatora wskazuje na jego własny komputer, nie na serwer. Ikony są teraz hostowane lokalnie w naszym panelu.
- `/player/`: umiejętności wyświetlają się teraz jak przedmioty w ekwipunku — ranga nałożona na ikonę, pełna nazwa w tooltipie po najechaniu, bez osobnego tekstu obok. Dodano też listę umiejętności pasywnych bez ikon (Górnictwo, Kowalstwo, Polimorfia, Dowodzenie, Combo, języki, jazda konna).

## 2026-09-14 20:09 CEST · 1.42.0

- Zaktualizowano rdzeń Playerbots do wydania Tieru 2.0.46; przełączniki bez skrzyni ucznia i bez szkatułek blasku księżyca przetrwały bez ingerencji.
- Dashboard i `/economy/`: konta testowe instalatora (Admin, AdminNinja, AdminSura, AdminSzaman — 2 mld sztucznego yang) nie liczą się już do "yang w obiegu".
- Dashboard: liczba w segmencie "Boty na mapach" nie chowa się już za paskiem przewijania; segment rośnie i wypełnia cały wolny sidebar.
- `/player/`: nowa sekcja "Sklep offline" — co bot aktualnie sprzedaje, za ile i gdzie stoi stragan (nazwa, mapa, współrzędne), dociągane bezpośrednio z tabel IkarusShop.
- `/player/`: przycisk "Teleportuj moją postać w grze (1 klik)" — jak w panelu Tieru, przez tę samą kolejkę questa co nadania przedmiotów.
- `/player/`: "Historia ekwipunku" zamiast surowego logu — czytelne zdarzenia (Sprzedane handlarzowi, Założone, Ulepszenie udane, Spalone przy ulepszaniu itd.) z nazwą przedmiotu, jak w panelu Tieru.

## 2026-09-14 18:02 CEST · 1.41.0

- Sklepy offline: tooltip Księgi Umiejętności w profilu bota nie pokazuje już losowych bonusów innego przedmiotu.
- Sklepy offline: ranking najlepiej sprzedających się przedmiotów rozpoznaje teraz konkretną umiejętność Księgi (dociągana z socketu sprzedanego przedmiotu), zamiast jednej generycznej pozycji; dodano osobny panel z top księgami.
- Sklepy offline: nowy live-feed ostatnich sprzedaży ze straganów (ikona, sprzedawca, królestwo, mapa, cena) i wykres tempa sprzedaży z trendem ceny.
- Dashboard: kafelek "Boty według map" przełącza się automatycznie co 8s na wykres słupkowy "Sklepy według map" (jak w Sklepach offline, w mniejszej wersji).
- Dashboard: lista "Boty na mapach" w panelu bocznym jest teraz przewijana i nie wyjeżdża poza swój segment po dodaniu nowych map.
- Dodano trzy nowe mapy botów: Las, Czerwony Las i Wieża Demonów (heatmapa zdarzeń); Wieża Demonów nie pojawia się na mapie na żywo z kropkami botów, bo to prywatne instancje dungeonu.
- Naprawiono nakładające się linki w rozwijanym menu "Gospodarka" (bug Safari/WebKit z display:contents w grid).

## 2026-09-09 18:10 CEST · 1.40.0

- Dodano zwijany poradnik uruchomienia aktualizatora Tieru na VPS bezpośrednio w Zarządzaniu.
- Tabele, przyciski, linki, przedziałki i kafelki wskazanych widoków dziedziczą teraz aktywny motyw.
- Baza przedmiotów pokazuje ikonę rzeczywistego przedmiotu przy każdej kategorii.
- Konta i profil postaci pokazują flagę oraz nazwę królestwa.

## 2026-09-09 17:45 CEST · 1.39.1

- Karta Playerbots · świat na Dashboardzie dziedziczy pełną kolorystykę aktywnego motywu, także dla etykiet, rat i listy map.

## 2026-09-09 17:30 CEST · 1.39.0

- Kreator GM pozwala wybrać kobietę albo mężczyznę; zapisuje właściwy wariant modelu klienta, zachowując klasyczny wariant jako domyślny.
- Oryginalne portrety klas są widoczne w profilu postaci, liście graczy, rankingach, karuzeli Dashboardu i rankingu aktualnej mapy.
- Ranking botów otrzymał kolumnę klasy z portretem i nazwą.
- Mapa na żywo, filtry, paski aktywności oraz karuzela rankingów dziedziczą teraz pełną paletę motywu Ocean, Ember lub Forest.

## 2026-09-09 16:47 CEST · 1.38.6

- Kreator kont GM zapisuje teraz indeks wyboru postaci (`player.player_index`), więc utworzona postać jest widoczna od razu po zalogowaniu.
- Nieudana konfiguracja GM sprząta utworzone przez siebie rekordy, także na tabelach MyISAM bez transakcji.
- Nick GM przyjmuje pojedynczy prefiks w nawiasach, np. `[GM]Seban` lub `[GA]Seban`.
- Dodano osiem oryginalnych portretów klas z ekranu postaci klienta do `static/class-portraits/`.

## 2026-09-08 21:45 CEST · 1.38.5

- Wiadomości świata odzyskują polskie nazwy ulepszanych przedmiotów z VNUM; ulepszenia +8 i +9 są złote.
- Sezon liczy wyłącznie trzy indeksowane typy zdarzeń z ostatnich 7 dni, bez pełnych skanów całej historii logów.

## 2026-09-08 17:35 CEST · 1.38.4

- Sesja panelu ma własną nazwę ciasteczka i trwa 30 dni. Nie koliduje już z klasycznym panelem Tieru działającym na tym samym hoście pod innym portem.
- Dodano poprawkę rdzenia: po załadowaniu danych questa bot uruchamia własne timery. Dzięki temu odbiera także masowe nadania z kolejki panelu.
- Masowe nadania wybierają wyłącznie Playerboty; postacie zwykłych graczy i administracji nie trafią do listy odbiorców nawet wtedy, gdy spełniają warunki poziomu lub konia.

## 2026-09-08 17:15 CEST · 1.38.3

- Uporządkowano wykresy map: trwała paleta kolorów, wybór map przez tabelę i checkboxy oraz tooltip z godziną i liczbą postaci.
- Dashboard i `/manage` sprawdzają najnowsze wydanie Playerbots na GitHubie co 15 minut; lokalna wersja jest zielona, gdy aktualna, i pomarańczowa, gdy zaległa.
- Pasek wiadomości świata można ukryć; na telefonie zachowuje formę pojedynczego paska.
- Konto GM tworzy teraz od razu prawidłową postać wybranej klasy w wybranym królestwie; sama ranga GM nadal wymaga restartu usług gry.

## 2026-09-08 15:00 CEST · 1.38.2

- Dodano brakujące, śledzone tło ekwipunku `inventory-background.svg`; jest kopiowane do każdego obrazu i ZIP-a panelu.
- Helper ustawień serwera publikuje sygnał gotowości. `/manage` nie pozwala już utworzyć zlecenia restartu/respawnu, gdy integracja gry nie działa.
- Dodano bezpieczne usunięcie wyłącznie zaległego zlecenia po 10 minutach bez aktywnego helpera oraz wyjaśnienie instalacji integracji w README.

## 2026-09-08 14:35 CEST · 1.38.1

- Dodano `UPDATER_VPS.md`: komendy dla standardowych i niestandardowych instalacji Tieru na VPS, przygotowanie cache oraz diagnostykę aktualizatora.
- Rozszerzono README o wymagany wolumen `update-spool` i instrukcję włączenia aktualizacji z panelu.

## 2026-09-08 00:00 CEST · 1.38.0

- Dodano most do izolowanego aktualizatora Tieru w `/manage`: stan, postęp, log i przycisk zlecenia aktualizacji.
- Panel zapisuje wyłącznie identyfikator zlecenia do wspólnej kolejki; Docker socket pozostaje wyłącznie w kontenerze aktualizatora.
- Przycisk wymaga aktywnej ochrony hasłem oraz tokenu sesji; wdrożona aktualizacja automatycznie odświeża widoczną wersję Playerbots.

## 2026-09-07 22:55 CEST · 1.37.1

- Poprawiono źródło wersji Playerbots w Dashboardzie: jest ustawiane jawnie w `PLAYERBOTS_VERSION`, a przykładowa konfiguracja wskazuje 1.30.12.

## 2026-09-07 22:35 CEST · 1.37.0

- Zaktualizowano rdzeń Playerbots do wydania Tieru 1.30.12: obsługę szkatułek, wycenę bonusów w sklepach oraz diagnostykę Dockera.
- Dodano Loch Małp Normalny (108) i Loch Małp Trudny (109) do mapy na żywo, historii natężenia, heatmap, wykresów, list map i zarządzania respawnem.
- Z panelu można teraz sterować respawnem potworów we wszystkich trzech Lochach Małp; Metiny są ukryte, ponieważ te mapy nie mają pliku `stone.txt`.

## 2026-09-07 22:00 CEST · 1.36.2

- Dodano ranking zabitych bossów (`BOSS_KILL`) za ostatnie 7 dni do `/rankings` i karuzeli Dashboardu.
- Zweryfikowano produkcyjnie ustawienia respawnu: aktywne wartości są zapisywane do właściwych plików `regen.txt` przed restartem rdzeni.

## 2026-09-07 21:27 CEST · 1.36.1

- `/maps` pokazuje pełną listę obsługiwanych map, także gdy bieżące natężenie wynosi 0.
- Dodano warstwę cieplną zabitych bossów (`BOSS_KILL`) na dashboardzie i w aktywności map.
- Dodano publiczną w panelu sekcję Changelog; kolejne hotfixy będą dopisywane z czasem wdrożenia.
- Połączono kafelki postaci i kont, a wersję panelu przeniesiono do stopki dashboardu.

## 1.36.0

- Dodano Górę Sohan (ID 61) i Loch Pająków V1 (ID 104) do mapy live, historii natężenia, heatmap, wykresów, list botów oraz ustawień respawnu.
- Wsparto osobny respawn potworów dla obu map i Metinów dla Góry Sohan; Loch Pająków V1 nie zawiera pliku `stone.txt`, co panel oznacza wprost.
- Podkłady obu map są renderowane z tych samych danych terenu, z których korzysta nawigacja Playerbots.

## 1.35.0

- Synchronizacja nazw i numerów umiejętności z aktualnym Panelem Tieru: ikona i podpis używają tego samego VNUM; nieużywane pozycje nie są już wyświetlane.
- Zarządzanie zachowaniem obsługuje przełącznik szybkich ksiąg (`BOOKS`) oraz szanse szkatułek (`CHEST`, `CHEST_STONE`).
- Zapis wag zachowuje przyszłe klucze silnika, których panel jeszcze nie zna.

## Wcześniejsze funkcje (przed prowadzeniem changeloga)

- Prawdziwe podkłady map wyciągnięte z folderu `/pack/` klienta gry (nie zastępcze grafiki) wpięte do wszystkich widoków z mapą.
- Prawdziwe ikony przedmiotów z klienta gry w całym panelu: ekwipunek, ekonomia, baza przedmiotów, sklepy.
- Karta postaci: nadawanie VIP oraz Smoczych Monet bez wychodzenia z profilu bota.
- Karta postaci: możliwość usunięcia postaci.
- Karta postaci: zmiana nicku postaci.
- `/manage`: usunięto sekcje, które i tak nie działały.
- `/economy/`: kliknięcie w przedmiot otwiera wykres "Stan w gospodarce · ostatnie 14 dni".
- `/player/`: statystyki postaci — te same, które gracz widzi w grze pod klawiszem Y.
- Wiadomości ze świata poprawnie wyświetlają polskie znaki.

## 1.34.0

- Osobne czasy respawnu potworów i Metinów dla obsługiwanych map.
- Jawne ID map, Joan przypisane do Chunjo M1 (21); poprawiona ścieżka Doliny Orków (64).
- Wspólna kolejka mnożników i respawnu: jeden restart dla całego zestawu, walidacja i cofnięcie ustawień przy błędzie zapisu.
- Równe przyciski, postęp i historia restartu w jednej sekcji zarządzania.
- Data ukończonego restartu, źródło zlecenia oraz osobna informacja o automatycznym podniesieniu rdzenia.
- Przycisk samego restartu pomija niezapisane pola, również gdy zawierają nieprawidłowe wartości.
- Testy regresji formularza i integracji z kontenerem gry.
