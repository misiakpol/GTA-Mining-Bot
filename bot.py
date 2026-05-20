import time
import keyboard
import pydirectinput
import mss
import numpy as np
import cv2
import json
import os
import sys
import ctypes
from ultralytics import YOLO

# ==========================================
# 1. KONFIGURACJA I INICJALIZACJA
# ==========================================
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass
pydirectinput.PAUSE = 0

# --- Wczytanie koordynatów dywanu ---
sciezka_konfiguracji = os.path.join("User Settings", "region_dywanu.json")
if not os.path.exists(sciezka_konfiguracji):
    print("BŁĄD: Brak region_dywanu.json. Uruchom wybierak_obszaru.py")
    sys.exit()

with open(sciezka_konfiguracji, 'r') as plik:
    REGION_DYWANU = json.load(plik)

# --- Ustawienia klawiszy ---
sciezka_ustawien = os.path.join("User Settings", "settings.json")
if not os.path.exists(sciezka_ustawien):
    domyslne = {"klawisz_start": "e", "klawisz_pauza": "f8", "klawisz_stop": "f9"}
    os.makedirs("User Settings", exist_ok=True)
    with open(sciezka_ustawien, 'w') as plik:
        json.dump(domyslne, plik, indent=4)
    USTAWIENIA = domyslne
else:
    with open(sciezka_ustawien, 'r') as plik:
        USTAWIENIA = json.load(plik)

KLAWISZ_START = USTAWIENIA["klawisz_start"]
KLAWISZ_PAUZA = USTAWIENIA["klawisz_pauza"]
KLAWISZ_STOP = USTAWIENIA["klawisz_stop"]

# --- Wczytanie wzorców obrazków (Szablon minigry i Ikona wydobycia) ---
sciezka_szablonu = os.path.join("Ressources", "szablon_postepu.png")
sciezka_wydobycia = os.path.join("Ressources", "wydobycie.png")

if not os.path.exists(sciezka_szablonu):
    print(f"BŁĄD: Brak pliku '{sciezka_szablonu}'!")
    sys.exit()
if not os.path.exists(sciezka_wydobycia):
    print(f"BŁĄD: Brak pliku '{sciezka_wydobycia}'!")
    sys.exit()

szablon = cv2.imread(sciezka_szablonu, cv2.IMREAD_COLOR)
szablon_wydobycia = cv2.imread(sciezka_wydobycia, cv2.IMREAD_COLOR)

# --- Konfiguracja rejonu nasłuchu "Wydobycia" (Lewy górny róg) ---
REGION_WYDOBYCIE = {
    "top": 0,
    "left": 0,
    "width": 500,
    "height": 100
}

# --- Ładowanie AI ---
print("Ładowanie sztucznej inteligencji...")
model = YOLO('best.pt')
print("Mózg załadowany pomyślnie!\n")

sct = mss.mss()
monitor_glowny = sct.monitors[1]

# ==========================================
# 2. FLAGI STERUJĄCE I ZDARZENIA
# ==========================================
dziala = True
spauzowany = False

def przelacz_pauze():
    global spauzowany
    spauzowany = not spauzowany
    if spauzowany:
        print(f"\n[PAUZA] Skrypt wstrzymany. Naciśnij '{KLAWISZ_PAUZA}', aby wznowić.")
    else:
        print(f"\n[WZNOWIONO] Skrypt kontynuuje pracę.")

def zatrzymaj_bota():
    global dziala
    dziala = False
    print(f"\n[STOP] Otrzymano sygnał zatrzymania...")

keyboard.add_hotkey(KLAWISZ_PAUZA, przelacz_pauze)
keyboard.add_hotkey(KLAWISZ_STOP, zatrzymaj_bota)

# ==========================================
# 3. FUNKCJE POMOCNICZE
# ==========================================
def bezpieczne_czekanie(czas_sekundy):
    start = time.time()
    while time.time() - start < czas_sekundy:
        if not dziala or spauzowany:
            return False
        time.sleep(0.01)
    return True

def czy_minigra_aktywna():
    zrzut = np.array(sct.grab(monitor_glowny))
    ekran_bgr = cv2.cvtColor(zrzut, cv2.COLOR_BGRA2BGR)
    wynik = cv2.matchTemplate(ekran_bgr, szablon, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(wynik)
    return max_val > 0.8

def czy_widac_ikonke_wydobycia():
    zrzut = np.array(sct.grab(REGION_WYDOBYCIE))
    ekran_bgr = cv2.cvtColor(zrzut, cv2.COLOR_BGRA2BGR)
    wynik = cv2.matchTemplate(ekran_bgr, szablon_wydobycia, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(wynik)
    return max_val > 0.75  # Tolerancja ustawiona na 75%

def szybkie_klikniecie(x, y):
    pydirectinput.moveTo(x, y)
    if not bezpieczne_czekanie(0.05): return
    pydirectinput.mouseDown()
    if not bezpieczne_czekanie(0.05): return
    pydirectinput.mouseUp()
    bezpieczne_czekanie(0.02)

# ==========================================
# 4. GŁÓWNA PĘTLA BOTA (Maszyna Stanów)
# ==========================================
print("=====================================================")
print(" BOT GOTOWY DO PRACY! WŁĄCZONY TRYB AUTO-WYDOBYCIA.")
print(f" -> Bot sam rozpocznie pracę, gdy wykryje obrazek w lewym górnym rogu.")
print(f" -> Możesz też wystartować ręcznie klawiszem: '{KLAWISZ_START.upper()}'")
print(f" -> Pauza/Wznowienie: '{KLAWISZ_PAUZA.upper()}'")
print(f" -> Wyłączenie: '{KLAWISZ_STOP.upper()}'")
print("=====================================================")

while dziala:
    # --- STAN 0: PAUZA ---
    if spauzowany:
        time.sleep(0.1)
        continue

    # --- STAN 1: CZUWANIE ---
    # Skanujemy w tle, dopóki gracz nie wciśnie startu LUB dopóki nie wykryjemy ikonki
    uruchomienie_reczne = keyboard.is_pressed(KLAWISZ_START)
    uruchomienie_auto = czy_widac_ikonke_wydobycia()

    if uruchomienie_reczne or uruchomienie_auto:
        
        if uruchomienie_auto:
            print("\n[AUTO-WYKRYCIE] Znalazłem ikonę wydobycia! Wciskam 'E'...")
            pydirectinput.press('e')
            # Krótka pauza, aby gra zdążyła schować ikonę i rozpocząć animację postaci
            if not bezpieczne_czekanie(0.01): continue 
        else:
            print("\n[START RĘCZNY] Wciśnięto klawisz. Zaczynam pracę...")

        print("[ROZPOCZYNAM CYKL] Spamuję LPM, czekam na dywan...")
        
        # --- STAN 2: KOPANIE ZŁOŻA ---
        while not czy_minigra_aktywna():
            if not dziala or spauzowany: break
                
            pydirectinput.mouseDown()
            if not bezpieczne_czekanie(0.05): break
            pydirectinput.mouseUp()
            if not bezpieczne_czekanie(0.02): break

        if not dziala or spauzowany: continue
        
        print("\n[WYKRYTO MINIGRĘ!] Przerywam kopanie, ładuję snajpera.")
        if not bezpieczne_czekanie(0.01): continue
        
        # --- STAN 3: ZBIERANIE KAMIENI ---
        while czy_minigra_aktywna():
            if not dziala or spauzowany: break
                
            screenshot = np.array(sct.grab(REGION_DYWANU))
            obraz_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
            wyniki = model.predict(source=obraz_bgr, conf=0.55, verbose=False)
            znalezione_kamienie = wyniki[0].boxes.xyxy.cpu().numpy()
            
            if len(znalezione_kamienie) > 0:
                print(f"YOLO namierzyło {len(znalezione_kamienie)} celów. Odklikuję...")
                for box in znalezione_kamienie:
                    if not dziala or spauzowany: break
                    
                    x1, y1, x2, y2 = box
                    srodek_x = int((x1 + x2) / 2 + REGION_DYWANU["left"])
                    srodek_y = int((y1 + y2) / 2 + REGION_DYWANU["top"])
                    szybkie_klikniecie(srodek_x, srodek_y)
            else:
                print("Czekam na nowe kamienie...")
                
            if not bezpieczne_czekanie(0.3): break
            
        if dziala and not spauzowany:
            print("[CYKL ZAKOŃCZONY] Minigra zniknęła. Wracam do czuwania...")
            bezpieczne_czekanie(1.5) # Zabezpieczenie przed podwójnym odpaleniem na tym samym zwoju

print("\nBot został całkowicie wyłączony. Do zobaczenia!")