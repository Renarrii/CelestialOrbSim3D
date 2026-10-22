# 🪐 CelestialOrbSim3D

**Precyzyjny symulator grawitacyjny N-ciał z analizatorem trajektorii kosmicznych**

## 📖 O projekcie

**CelestialOrbSim3D** to autorski symulator grawitacyjny stworzony w języku Python, służący do modelowania i wizualizacji trajektorii obiektów w Układzie Słonecznym. Projekt w sposób szczególny uwzględnia analizę lotu komety **3I/ATLAS**. Dzięki zastosowaniu numerycznej metody całkowania **Rungego-Kutty 4. rzędu (RK4)**, symulator rozwiązuje problem N-ciał, minimalizując błędy numeryczne podczas bliskich przelotów (np. w układzie Ziemia-Księżyc). 

Projekt integruje się z systemem **NASA JPL Horizons**, pobierając rzeczywiste efemerydy obiektów w celu inicjalizacji stanu początkowego oraz późniejszej weryfikacji precyzji obliczeń.

## 🏗️ Architektura Systemu

Poniższy schemat przedstawia przepływ danych i architekturę modułową aplikacji:

```mermaid
graph TD
    subgraph API ["Zewnętrzne API"]
        JPL[NASA JPL Horizons API]
    end

    subgraph Symulator ["Symulator (src/main.py)"]
        INIT[Inicjalizacja Stanu<br/>Pozycje i Prędkości]
        RK4[Silnik Fizyczny RK4<br/>Całkowanie Numeryczne]
        3D[VPython 3D Engine<br/>Wizualizacja na żywo]
    end

    subgraph Analiza ["Analiza i Raportowanie (src/compare_orbit.py)"]
        CSV[(Wyniki Symulacji<br/>atlas_simulated_trajectory_rk4.csv)]
        ERR[Obliczanie błędu euklidesowego]
        PLT[Wizualizacja Błędów<br/>Matplotlib]
    end

    JPL -- "Astroquery (Początkowe wektory)" --> INIT
    INIT --> RK4
    RK4 -- "Aktualizacja klatek" --> 3D
    RK4 -- "Eksport co N kroków" --> CSV
    
    CSV --> ERR
    JPL -- "Astroquery (Referencyjne efemerydy)" --> ERR
    ERR --> PLT
'''
## 🛠️ Użyte Technologie

Projekt został zbudowany z wykorzystaniem nowoczesnego stosu technologicznego w ekosystemie Pythona, podzielonego na logiczne warstwy:

*   **Fizyka i Silnik Obliczeniowy:**
    *   `Python 3` z silnym typowaniem statycznym (`typing`).
    *   Algorytm **Rungego-Kutty 4. rzędu (RK4)** do precyzyjnego wyliczania przyspieszeń i wektorów ruchu.
*   **Zarządzanie Danymi i API:**
    *   `astroquery` (moduł `jplhorizons`) – bezpośrednia integracja z bazami NASA, pobieranie wektorów stanu (pozycja, prędkość) w jednostkach astronomicznych (AU).
    *   `pandas` & `numpy` – wysokowydajne przetwarzanie szeregów czasowych, mapowanie dat i szybkie wektorowe obliczenia dystansu euklidesowego.
*   **Wizualizacja (Frontend):**
    *   `vpython` – renderowanie trójwymiarowej sceny Układu Słonecznego w czasie rzeczywistym, śledzenie trajektorii obiektów.
    *   `matplotlib` – generowanie analitycznych wykresów 2D (kumulacja błędu w kilometrach) oraz statycznych zestawień 3D (symulacja vs rzeczywistość).
*   **Zapewnienie Jakości (QA):**
    *   `unittest` – wbudowany framework do testów jednostkowych, izolujący i weryfikujący logikę matematyczną oraz fizyczną (kierunki wektorów sił).

## 📂 Struktura Katalogów

Projekt zachowuje czysty podział na kod źródłowy i testy:

```text
📦 CelestialOrbSim3D
 ┣ 📂 src
 ┃ ┣ 📜 main.py                  # Główna pętla symulacji, silnik 3D (vpython) i implementacja RK4
 ┃ ┗ 📜 compare_orbit.py         # Narzędzie weryfikacji precyzji: Porównanie CSV z danymi z JPL
 ┣ 📂 tests
 ┃ ┣ 📜 test_simulation.py       # Testy jednostkowe logiki fizycznej i wyszukiwania obiektów
 ┃ ┗ 📜 test_compare.py          # Weryfikacja matematyczna modułu analizy błędów trajektorii
 ┣ 📜 atlas_simulated_trajectory_rk4.csv # (Generowany automatycznie) Logi z przebiegu symulacji
 ┗ 📜 README.md
```

## 🚀 Uruchomienie Projektu

### 1. Instalacja zależności

```bash
pip install -r requirements.txt
```

### 2. Uruchomienie Symulacji 3D
Uruchom główny skrypt, aby rozpocząć całkowanie i wyrenderować wizualizację. Proces będzie zapisywał pozycje komety do pliku CSV co 100 kroków symulacji.

```bash
python src/main.py
```
*Uwaga: Symulację można przerwać w dowolnym momencie za pomocą `Ctrl+C`, co spowoduje bezpieczne zapisanie i zamknięcie pliku CSV.*

### 3. Analiza Błędów
Po wygenerowaniu pliku `atlas_simulated_trajectory_rk4.csv`, uruchom skrypt analityczny. Pobierze on rzeczywiste dane z JPL dla odpowiadających ram czasowych i wygeneruje wykresy błędów:

```bash
python src/compare_orbit.py
```

### 4. Testy Jednostkowe
Aby upewnić się, że cała logika matematyczna działa poprawnie, uruchom pakiet testów:

```bash
python -m unittest discover -s tests
```
