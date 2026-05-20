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

# --- Wczytanie i ewentualne generowanie ustawień klawiszy ---
sciezka_ustawien = os.path.join("User Settings", "settings.json")
if not os.path.exists(sciezka_ustawien):
    print("[INFO] Brak pliku settings.json. Generuję domyślne ustawienia...")
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

# --- Wczytanie wzorca karteczki ---
sciezka_szablonu = os.path.join("Ressources", "szablon_postepu.png")
if not os.path.exists(sciezka_szablonu):
    print(f"BŁĄD: Brak pliku '{sciezka_szablonu}'. Zrób wycinek interfejsu i zapisz go w tym folderze!")
    sys.exit()

szablon = cv2.imread(sciezka_szablonu, cv2.IMREAD_COLOR)

# --- Ładowanie AI ---
print("Ładowanie sztucznej inteligencji...")
model = YOLO('best.pt')
print("Mózg załadowany pomyślnie!\n")

sct = mss.mss()
monitor_glowny = sct.monitors[1]

# ==========================================
# 2. FLAGI STERUJĄCE I ZDARZENIA (Z TŁA)
# ==========================================
dziala = True
spauzowany = False

def przelacz_pauze():
    """Funkcja wywoływana natychmiast po wciśnięciu klawisza pauzy."""
    global spauzowany
    spauzowany = not spauzowany
    if spauzowany:
        print(f"\n[PAUZA] Skrypt wstrzymany. Naciśnij '{KLAWISZ_PAUZA}', aby wznowić.")
    else:
        print(f"\n[WZNOWIONO] Skrypt kontynuuje pracę.")

def zatrzymaj_bota():
    """Funkcja wywoływana natychmiast po wciśnięciu klawisza stopu."""
    global dziala
    dziala = False
    print(f"\n[STOP] Otrzymano sygnał zatrzymania...")

# Przypisanie klawiszy do funkcji działających w tle
keyboard.add_hotkey(KLAWISZ_PAUZA, przelacz_pauze)
keyboard.add_hotkey(KLAWISZ_STOP, zatrzymaj_bota)

# ==========================================
# 3. FUNKCJE POMOCNICZE
# ==========================================
def bezpieczne_czekanie(czas_sekundy):
    """Zastępuje time.sleep(). Pozwala na natychmiastowe przerwanie czekania przez pauzę/stop."""
    start = time.time()
    while time.time() - start < czas_sekundy:
        if not dziala or spauzowany:
            return False  # Zwraca False, jeśli w trakcie czekania wciśnięto pauzę/stop
        time.sleep(0.01)  # Mikrouśpienie, żeby nie palić procesora
    return True

def czy_minigra_aktywna():
    zrzut = np.array(sct.grab(monitor_glowny))
    ekran_bgr = cv2.cvtColor(zrzut, cv2.COLOR_BGRA2BGR)
    wynik = cv2.matchTemplate(ekran_bgr, szablon, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(wynik)
    return max_val > 0.8

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
print(" BOT GOTOWY DO PRACY!")
print(f" -> Start cyklu: '{KLAWISZ_START.upper()}'")
print(f" -> Pauza/Wznowienie: '{KLAWISZ_PAUZA.upper()}'")
print(f" -> Wyłączenie: '{KLAWISZ_STOP.upper()}'")
print("=====================================================")

while dziala:
    # --- STAN 0: PAUZA ---
    if spauzowany:
        time.sleep(0.1)
        continue

    # --- STAN 1: CZUWANIE ---
    if keyboard.is_pressed(KLAWISZ_START):
        print("\n[ROZPOCZYNAM CYKL] Spamuję LPM...")
        
        # --- STAN 2: KOPANIE ZŁOŻA ---
        while not czy_minigra_aktywna():
            if not dziala or spauzowany: break # Natychmiastowe wyrzucenie z pętli
                
            pydirectinput.mouseDown()
            if not bezpieczne_czekanie(0.05): break
            pydirectinput.mouseUp()
            if not bezpieczne_czekanie(0.05): break

        if not dziala or spauzowany: continue # Jeśli wyrzuciło nas przez pauzę, wracamy na początek
        
        print("\n[WYKRYTO MINIGRĘ!] Przerywam kopanie, ładuję snajpera.")
        if not bezpieczne_czekanie(0.15): continue
        
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
                    if not dziala or spauzowany: break # Przerywamy nawet w trakcie klikania serii
                    
                    x1, y1, x2, y2 = box
                    srodek_x = int((x1 + x2) / 2 + REGION_DYWANU["left"])
                    srodek_y = int((y1 + y2) / 2 + REGION_DYWANU["top"])
                    szybkie_klikniecie(srodek_x, srodek_y)
            else:
                print("Czekam na nowe kamienie...")
                
            if not bezpieczne_czekanie(0.3): break
            
        if dziala and not spauzowany:
            print("[CYKL ZAKOŃCZONY] Minigra zniknęła. Czekam na start...")
            bezpieczne_czekanie(1) # Zabezpieczenie przed trzymaniem klawisza

print("\nBot został całkowicie wyłączony. Do zobaczenia!")