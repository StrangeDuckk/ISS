# ISS
ISS - Inteligentne Systemy Sterowania, Arduino


ISS – Projekt 1: Interfejs komunikacyjny PC ↔ Arduino dla robota mobilnego
Cel:
 Zaprojektować i zaimplementować kompletny interfejs komunikacyjny pomiędzy aplikacją Python (PC) a oprogramowaniem C++ na Arduino, który umożliwi zarządzanie robotem mobilnym.
 Po stronie PC powstaje prosty interfejs terminalowy obsługujący komunikację, logowanie i testy.
 Po stronie Arduino powstaje warstwa komunikacyjna (parser ramek, walidacja, ACK/NACK) oraz warstwa sterowania robotem.
 Rozwiązanie ma być gotowe na rozwój w kolejnych projektach (PID, fuzzy, SLAM itp.).

1. Zakres i wymagania
PC:

wybór portu szeregowego i prędkości, watchdog połączenia,


wysyłanie komend,


wyświetlanie odpowiedzi (ACK/NACK, dane sensorów),


komendy pomocnicze: help, status, history, save-log, quit (opcjonalnie do wyboru).


Arduino (C++):

moduł protokołu (parser, walidacja, obsługa błędów),


warstwa sterująca (silniki, czujniki: sonar/IR lub emulacja).


Bezpieczeństwo i odporność:

każda ramka kończy się znacznikiem końca i zawiera liczbę kontrolną,


po stronie PC timeout i ponawianie z exponential backoff.


Język komend definiuje Student – należy dostarczyć specyfikację (tabela/diagramy).

2. Minimalny zestaw funkcji robota (wymagane)
M(cm) – ruch o zadaną odległość w cm (dodatnia – przód, ujemna – tył),


R(deg) – obrót o zadaną liczbe kroków (dodatni – prawo, ujemny – lewo),


V(v) – ustawienie prędkości liniowej,


S – natychmiastowe zatrzymanie,


B – odczyt sonaru w cm,


I – odczyt czujnika IR,


Możliwość ustawienia który silnik i cuzjnik jest który i w która strone ma przód. Początkowe ustawienia z poziomu komend umożliwiające łatwą zmiane robota bez zmian w kodzie.


(Nazwy i format ramek ustala Student.)


3. Dokumentacja protokołu 
Powinna zawierać:

Opis warstw (żądania/odpowiedzi, stany),


Format ramki, CMD, błędy, ograniczenia,


Tabele komend z przykładami,


Opis bezpieczeństwa,


Scenariusze testów.

