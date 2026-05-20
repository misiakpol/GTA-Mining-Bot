import cv2
import mss
import numpy as np
import ctypes
import time
import json
import os

# Wyłączamy skalowanie Windowsa, żeby koordynaty były idealne na każdym komputerze
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

sciezka_ustawien = os.path.join("User Settings", "settings.json")
if not os.path.exists(sciezka_ustawien):
    domyslne = {
        "klawisz_start": "e", 
        "klawisz_pauza": "f8", 
        "klawisz_stop": "f9",
        "monitor": 1
    }
    os.makedirs("User Settings", exist_ok=True)
    with open(sciezka_ustawien, 'w') as plik:
        json.dump(domyslne, plik, indent=4)
    USTAWIENIA = domyslne
else:
    with open(sciezka_ustawien, 'r') as plik:
        USTAWIENIA = json.load(plik)

# Używamy .get(), co zabezpiecza bota w przypadku starszych wersji pliku settings.json
KLAWISZ_START = USTAWIENIA.get("klawisz_start", "e")
KLAWISZ_PAUZA = USTAWIENIA.get("klawisz_pauza", "f8")
KLAWISZ_STOP = USTAWIENIA.get("klawisz_stop", "f9")
MONITOR_INDEX = USTAWIENIA.get("monitor", 1)

# Zmienne globalne do rysowania
rysuje = False
ix, iy = -1, -1
obraz = None
obraz_kopia = None
wybrany_obszar = None

# Zmienne do obsługi dwóch etapów
etap = 1
obszar_dywanu = None
obszar_szablonu = None

def wyswietl_instrukcje():
    """Rysuje czarny pasek z instrukcją na górze ekranu."""
    if etap == 1:
        tekst = "KROK 1: Zaznacz obszar DYWANU i wcisnij ENTER"
        kolor = (0, 255, 0) # Zielony
    else:
        tekst = "KROK 2: Zaznacz OBSZAR WYSZUKIWANIA karteczki i wcisnij ENTER"
        kolor = (0, 255, 255) # Żółty
        
    cv2.rectangle(obraz_kopia, (0, 0), (1200, 70), (0, 0, 0), -1)
    cv2.putText(obraz_kopia, tekst, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, kolor, 2)

def rysuj_prostokat(event, x, y, flags, param):
    global ix, iy, rysuje, obraz, obraz_kopia, wybrany_obszar

    # Kiedy klikniesz lewy przycisk: zacznij rysować
    if event == cv2.EVENT_LBUTTONDOWN:
        rysuje = True
        ix, iy = x, y

    # Kiedy ruszasz myszką z wciśniętym przyciskiem: aktualizuj zieloną ramkę
    elif event == cv2.EVENT_MOUSEMOVE:
        if rysuje:
            obraz_kopia = obraz.copy()
            wyswietl_instrukcje()
            cv2.rectangle(obraz_kopia, (ix, iy), (x, y), (0, 255, 0), 2)

    # Kiedy puścisz przycisk: zapisz współrzędne
    elif event == cv2.EVENT_LBUTTONUP:
        rysuje = False
        obraz_kopia = obraz.copy()
        wyswietl_instrukcje()
        cv2.rectangle(obraz_kopia, (ix, iy), (x, y), (0, 255, 0), 2)
        
        # Obliczamy top, left, width, height niezależnie od tego w którą stronę ciągnąłeś myszkę
        left = min(ix, x)
        top = min(iy, y)
        width = abs(x - ix)
        height = abs(y - iy)
        
        wybrany_obszar = {
            "top": top,
            "left": left,
            "width": width,
            "height": height
        }
        print("\n[ZAPISANO OBSZAR!] Wciśnij ENTER aby przejść dalej, lub ESC aby anulować.")

print("Przygotuj grę! Za 3 sekundy ekran zostanie zamrożony...")
time.sleep(3)

# 1. Robimy zrzut całego ekranu
with mss.mss() as sct:
    try:
        monitor = sct.monitors[MONITOR_INDEX]
    except IndexError:
        monitor = sct.monitors[1]
        
    zrzut = np.array(sct.grab(monitor))
    obraz = cv2.cvtColor(zrzut, cv2.COLOR_BGRA2BGR)
    obraz_kopia = obraz.copy()

# 2. Tworzymy pełnoekranowe okno do rysowania
nazwa_okna = "Kreator Bota (Wcisnij ESC aby wyjsc)"
cv2.namedWindow(nazwa_okna, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(nazwa_okna, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setWindowProperty(nazwa_okna, cv2.WND_PROP_TOPMOST, 1)
cv2.setMouseCallback(nazwa_okna, rysuj_prostokat)

wyswietl_instrukcje()

print("Zaznacz myszką obszar na ekranie zgodnie z poleceniem.")

# 3. Pętla wyświetlająca okno i obsługująca etapy
while True:
    cv2.imshow(nazwa_okna, obraz_kopia)
    klawisz = cv2.waitKey(1) & 0xFF
    
    # Przerwij jeśli wciśnięto ESC (27)
    if klawisz == 27: 
        break
        
    # Jeśli wciśnięto ENTER (13) przechodzimy do kolejnego etapu
    elif klawisz == 13: 
        if etap == 1:
            if wybrany_obszar and wybrany_obszar["width"] > 0:
                obszar_dywanu = wybrany_obszar
                wybrany_obszar = None
                etap = 2
                obraz_kopia = obraz.copy() # Resetujemy obraz dla kroku 2
                wyswietl_instrukcje()
                print("[INFO] Zapisano dywan. Zaznacz teraz obszar wyszukiwania karteczki!")
            else:
                print("Najpierw zaznacz obszar dywanu myszką!")
                
        elif etap == 2:
            if wybrany_obszar and wybrany_obszar["width"] > 0:
                obszar_szablonu = wybrany_obszar
                break
            else:
                print("Najpierw zaznacz obszar wyszukiwania karteczki myszką!")

cv2.destroyAllWindows()

# 4. Zapisanie wyników do dwóch oddzielnych plików w podfolderze
print("\n==============================================")
folder_ustawien = "User Settings"
os.makedirs(folder_ustawien, exist_ok=True)

if obszar_dywanu:
    sciezka_dywan = os.path.join(folder_ustawien, "region_dywanu.json")
    with open(sciezka_dywan, 'w') as plik:
        json.dump(obszar_dywanu, plik, indent=4)
    print(f"[OK] Dywan zapisany w: {sciezka_dywan}")

if obszar_szablonu:
    sciezka_szablon = os.path.join(folder_ustawien, "region_szablonu.json")
    with open(sciezka_szablon, 'w') as plik:
        json.dump(obszar_szablonu, plik, indent=4)
    print(f"[OK] Obszar wyszukiwania zapisany w: {sciezka_szablon}")

print("==============================================\n")