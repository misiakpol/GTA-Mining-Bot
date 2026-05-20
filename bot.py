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
# Wyłączenie skalowania Windows i opóźnień pydirectinput
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass
pydirectinput.PAUSE = 0

# Wczytanie koordynatów dywanu
sciezka_konfiguracji = os.path.join("User Settings", "region_dywanu.json")
if not os.path.exists(sciezka_konfiguracji):
    print("BŁĄD: Brak region_dywanu.json. Uruchom wybierak_obszaru.py")
    sys.exit()

with open(sciezka_konfiguracji, 'r') as plik:
    REGION_DYWANU = json.load(plik)

# Wczytanie wzorca karteczki z postępem z nowego folderu
sciezka_szablonu = os.path.join("Ressources", "szablon_postepu.png")
if not os.path.exists(sciezka_szablonu):
    print(f"BŁĄD: Brak pliku '{sciezka_szablonu}'. Zrób wycinek interfejsu i zapisz go w tym folderze!")
    sys.exit()

szablon = cv2.imread(sciezka_szablonu, cv2.IMREAD_COLOR)

# Załadowanie modelu AI
print("Ładowanie sztucznej inteligencji...")
model = YOLO('best.pt')
print("Mózg załadowany pomyślnie!\n")

sct = mss.mss()
monitor_glowny = sct.monitors[1]

# ==========================================
# 2. FUNKCJE POMOCNICZE (Oczy i Ręce)
# ==========================================
def czy_minigra_aktywna():
    """Robi zrzut całego ekranu i szuka na nim szablonu karteczki."""
    zrzut = np.array(sct.grab(monitor_glowny))
    ekran_bgr = cv2.cvtColor(zrzut, cv2.COLOR_BGRA2BGR)
    
    wynik = cv2.matchTemplate(ekran_bgr, szablon, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(wynik)
    
    # Próg tolerancji: 0.8 oznacza 80% pewności, że obrazek jest na ekranie
    if max_val > 0.8:
        return True
    return False

def szybkie_klikniecie(x, y):
    """Przesuwa kursor i klika z minimalnym opóźnieniem dla silnika gry."""
    pydirectinput.moveTo(x, y)
    time.sleep(0.05) # Krótka przerwa na zarejestrowanie ruchu
    pydirectinput.mouseDown()
    time.sleep(0.05) # Krótkie przytrzymanie dla pewności kliknięcia
    pydirectinput.mouseUp()
    time.sleep(0.02) # Przerwa przed kolejnym kliknięciem, by gra zdążyła zareagować

# ==========================================
# 3. GŁÓWNA PĘTLA BOTA (Maszyna Stanów)
# ==========================================
print("=====================================================")
print(" BOT GOTOWY DO PRACY!")
print(" -> Naciśnij 'E', aby uruchomić automatyczny cykl.")
print(" -> Naciśnij 'F9', aby zamknąć program.")
print("=====================================================")

dziala = True

while dziala:
    # --- STAN 1: CZUWANIE ---
    # Program czeka w tle, nie obciążając procesora
    
    if keyboard.is_pressed('f9'):
        print("Wyłączanie...")
        break

    # Przejście ze Stanu 1 do Stanu 2 następuje po wciśnięciu 'E'
    if keyboard.is_pressed('e'):
        print("\n[ROZPOCZYNAM CYKL] Spamuję LPM...")
        
        # --- STAN 2: KOPANIE ZŁOŻA ---
        # Dopóki karteczka się NIE pojawi, klikamy 'E'
        while not czy_minigra_aktywna():
            if keyboard.is_pressed('f9'):
                dziala = False
                break
                
            pydirectinput.mouseDown()
            time.sleep(0.05)  # Czas wciśnięcia przycisku
            pydirectinput.mouseUp()
            time.sleep(0.05)  # Przerwa między kliknięciami

        if not dziala: break
        
        print("\n[WYKRYTO MINIGRĘ!] Przerywam kopanie, ładuję snajpera.")
        time.sleep(0.15)  # Dajemy grze ułamek sekundy na wyrenderowanie kamieni
        
        # --- STAN 3: ZBIERANIE KAMIENI ---
        # Dopóki karteczka JEST widoczna, skanujemy dywan YOLO
        while czy_minigra_aktywna():
            if keyboard.is_pressed('f9'):
                dziala = False
                break
                
            # Analiza tylko małego obszaru dywanu
            screenshot = np.array(sct.grab(REGION_DYWANU))
            obraz_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
            wyniki = model.predict(source=obraz_bgr, conf=0.55, verbose=False)
            znalezione_kamienie = wyniki[0].boxes.xyxy.cpu().numpy()
            
            if len(znalezione_kamienie) > 0:
                print(f"YOLO namierzyło {len(znalezione_kamienie)} celów. Odklikuję...")
                for box in znalezione_kamienie:
                    x1, y1, x2, y2 = box
                    # Konwersja lokalnych koordynatów dywanu na globalne koordynaty ekranu
                    srodek_x = int((x1 + x2) / 2 + REGION_DYWANU["left"])
                    srodek_y = int((y1 + y2) / 2 + REGION_DYWANU["top"])
                    
                    szybkie_klikniecie(srodek_x, srodek_y)
            else:
                print("Czekam na nowe kamienie...")
                
            # Przerwa na to, by gra przemieliła kliknięcia i ewentualnie zamknęła okno
            time.sleep(0.3) 
            
        # Gdy pętla Stanu 3 się kończy (karteczka znika), wracamy na początek do Stanu 1
        print("[CYKL ZAKOŃCZONY] Minigra zniknęła. Czekam na ponowne wciśnięcie 'E'...")
        time.sleep(1) # Zabezpieczenie, żeby nie wyzwolić bota od razu, jeśli nadal trzymasz palec na E