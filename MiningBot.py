import json
import os
import sys
import time
import keyboard
import pydirectinput
import mss
import numpy as np
import cv2
from ultralytics import YOLO
import pydirectinput

# WYŁĄCZAMY UKRYTY HAMULEC BEZPIECZEŃSTWA (domyślnie 0.1s)
pydirectinput.PAUSE = 0

# 1. Konfiguracja Dywanu
print("Wczytywanie ustawień użytkownika...")
sciezka_konfiguracji = os.path.join("User Settings", "region_dywanu.json")
# Sprawdzamy, czy plik istnieje (czy użytkownik użył kreatora)
if not os.path.exists(sciezka_konfiguracji):
    print("BŁĄD: Nie znaleziono konfiguracji dywanu!")
    print("Uruchom najpierw skrypt 'wybierak_obszaru.py', aby zaznaczyć minigrę na ekranie.")
    sys.exit() # Zatrzymuje bota

# Odczytujemy zapisane koordynaty
with open(sciezka_konfiguracji, 'r') as plik:
    REGION_DYWANU = json.load(plik)

print("Ładowanie sztucznej inteligencji...")
model = YOLO('best.pt')
print("Mózg załadowany pomyślnie!\n")
print("=====================================================")
print(" BOT GOTOWY DO PRACY!")
print(" -> Naciśnij 'F9', aby zamknąć bota całkowicie.")
print("=====================================================")

sct = mss.mss()

def kliknij_w_gre(x, y):
    """Funkcja do fizycznego przesunięcia myszki i kliknięcia w GTA V"""
    pydirectinput.moveTo(x, y)
    time.sleep(0.05) # Dajemy grze ułamek sekundy na zarejestrowanie ruchu myszki
    # Symulacja ludzkiego kliknięcia (wciśnięcie i puszczenie)
    pydirectinput.mouseDown()
    time.sleep(0.05) 
    pydirectinput.mouseUp()
    time.sleep(0.02) # Krótka przerwa przed podróżą do kolejnego kamienia

# Główna pętla programu
while True:
    # Wyłącznik bezpieczeństwa
    if keyboard.is_pressed('f8'):
        print("Wyłączanie bota...")
        break

    # Ręczny wyzwalacz skanowania
    if keyboard.is_pressed('f9'):
        print("\n=== ROZPOCZYNAM SKANOWANIE ===")
        
        # 1. Błyskawiczny zrzut ekranu (tylko mały wycinek)
        screenshot = np.array(sct.grab(REGION_DYWANU))
        obraz_do_analizy = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

        cv2.imwrite("debug_wycinek.png", obraz_do_analizy)
        print("[DEBUG] Zapisałem aktualny wycinek ekranu jako 'debug_wycinek.png'!")
        
        # 2. Wysyłamy zdjęcie do AI
        wyniki = model.predict(source=obraz_do_analizy, conf=0.6, verbose=False)
        znalezione_kamienie = wyniki[0].boxes.xyxy.cpu().numpy()
        
        if len(znalezione_kamienie) == 0:
            print("YOLO mówi: Dywan jest czysty (nic nie znalazłem).")
        else:
            print(f"YOLO mówi: Znalazłem {len(znalezione_kamienie)} kamieni! Wykonuję kliknięcia...")
            
            for box in znalezione_kamienie:
                x1, y1, x2, y2 = box
                srodek_x = (x1 + x2) / 2
                srodek_y = (y1 + y2) / 2
                
                prawdziwy_x = int(REGION_DYWANU["left"] + srodek_x)
                prawdziwy_y = int(REGION_DYWANU["top"] + srodek_y)
                
                kliknij_w_gre(prawdziwy_x, prawdziwy_y)
        
        print("================================\n")
        time.sleep(0.5)  # Zabezpieczenie przed podwójnym kliknięciem F8