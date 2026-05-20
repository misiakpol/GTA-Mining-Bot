import mss
import cv2
import numpy as np
import ctypes
import time

# 1. Wyłączamy oszukiwanie Pythona przez skalowanie ekranu w Windows (np. 125%)
# To najczęstsza przyczyna błędu rzędu 1000 pikseli!
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

# 2. TWOJE KOORDYNATY Z RADARU
REGION_DYWANU = {
    "top": 364,    # O ile pikseli dywan jest oddalony od górnej krawędzi ekranu
    "left": 1390,   # O ile pikseli dywan jest oddalony od lewej krawędzi ekranu
    "width": 794,  # Szerokość samego dywanu
    "height": 566  # Wysokość samego dywanu
}

print("Przygotuj grę! Zrzuty ekranu zrobią się za 3 sekundy...")
time.sleep(3) # Daje Ci 3 sekundy na kliknięcie w okno z grą, żeby była na wierzchu

with mss.mss() as sct:
    # ==========================================
    # ZDJĘCIE 1: PEŁNY EKRAN
    # ==========================================
    # sct.monitors[1] oznacza główny monitor
    monitor_glowny = sct.monitors[1]
    pelny_zrzut = np.array(sct.grab(monitor_glowny))
    pelny_bgr = cv2.cvtColor(pelny_zrzut[:, :, :3], cv2.COLOR_RGB2BGR)
    
    cv2.imwrite("01_pelny_ekran.png", pelny_bgr)
    print("[SUKCES] Zapisano cały ekran jako: 01_pelny_ekran.png")

    # ==========================================
    # ZDJĘCIE 2: TYLKO WYCINEK
    # ==========================================
    wycinek_zrzut = np.array(sct.grab(REGION_DYWANU))
    wycinek_bgr = cv2.cvtColor(wycinek_zrzut[:, :, :3], cv2.COLOR_RGB2BGR)
    
    cv2.imwrite("02_tylko_wycinek.png", wycinek_bgr)
    print("[SUKCES] Zapisano wycinek dywanu jako: 02_tylko_wycinek.png")

print("\nGotowe! Otwórz folder z projektem i sprawdź oba zdjęcia.")