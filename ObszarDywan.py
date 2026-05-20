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

# Zmienne globalne do rysowania
rysuje = False
ix, iy = -1, -1
obraz = None
obraz_kopia = None
wybrany_obszar = None

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
            cv2.rectangle(obraz_kopia, (ix, iy), (x, y), (0, 255, 0), 2)

    # Kiedy puścisz przycisk: zapisz współrzędne
    elif event == cv2.EVENT_LBUTTONUP:
        rysuje = False
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
        print("\n[ZAPISANO OBSZAR!] Wciśnij ENTER lub ESC, aby zamknąć okno.")

print("Przygotuj grę! Za 3 sekundy ekran zostanie zamrożony...")
time.sleep(3)

# 1. Robimy zrzut całego ekranu
with mss.mss() as sct:
    monitor = sct.monitors[1]
    zrzut = np.array(sct.grab(monitor))
    obraz = cv2.cvtColor(zrzut, cv2.COLOR_BGRA2BGR)
    obraz_kopia = obraz.copy()

# 2. Tworzymy pełnoekranowe okno do rysowania
nazwa_okna = "Zaznacz dywan (Wcisnij ENTER aby wyjsc)"
cv2.namedWindow(nazwa_okna, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(nazwa_okna, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setWindowProperty(nazwa_okna, cv2.WND_PROP_TOPMOST, 1)
cv2.setMouseCallback(nazwa_okna, rysuj_prostokat)

print("Zaznacz myszką obszar dywanu na ekranie.")

# 3. Pętla wyświetlająca okno
while True:
    cv2.imshow(nazwa_okna, obraz_kopia)
    klawisz = cv2.waitKey(1) & 0xFF
    
    # Przerwij jeśli wciśnięto ESC (27) lub ENTER (13)
    if klawisz == 27 or klawisz == 13: 
        break

cv2.destroyAllWindows()

# 4. Zapisanie wyników do pliku w podfolderze
if wybrany_obszar and wybrany_obszar["width"] > 0 and wybrany_obszar["height"] > 0:
    
    # Tworzymy folder, jeśli jeszcze nie istnieje
    folder_ustawien = "User Settings"
    os.makedirs(folder_ustawien, exist_ok=True)
    
    # Ścieżka do naszego pliku konfiguracyjnego
    sciezka_pliku = os.path.join(folder_ustawien, "region_dywanu.json")
    
    # Zapisujemy dane do pliku JSON w czytelnym formacie
    with open(sciezka_pliku, 'w') as plik:
        json.dump(wybrany_obszar, plik, indent=4)
        
    print("\n==============================================")
    print(f"GOTOWE! Pomyślnie zapisano ustawienia w:")
    print(f" -> {sciezka_pliku}")
    print("Twój bot odczyta te dane automatycznie przy starcie.")
    print("==============================================\n")
else:
    print("\nNie zaznaczono żadnego poprawnego obszaru.")