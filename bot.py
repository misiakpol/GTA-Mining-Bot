import time
import keyboard
import pydirectinput
import mss
import numpy as np
import cv2
import json
import os
import sys
import winsound
import threading
from ultralytics import YOLO
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QFrame, QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor

# ==========================================
# 1. KONFIGURACJA I INICJALIZACJA
# ==========================================

os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
pydirectinput.PAUSE = 0

sciezka_konfiguracji = os.path.join("User Settings", "region_dywanu.json")
if not os.path.exists(sciezka_konfiguracji):
    print("BŁĄD: Brak region_dywanu.json. Uruchom wybierak_obszaru.py", flush=True)
    sys.exit()

with open(sciezka_konfiguracji, 'r') as plik:
    REGION_DYWANU = json.load(plik)

sciezka_szablonu_json = os.path.join("User Settings", "region_szablonu.json")
if not os.path.exists(sciezka_szablonu_json):
    print("BŁĄD: Brak region_szablonu.json. Uruchom wybierak_obszaru.py", flush=True)
    sys.exit()

with open(sciezka_szablonu_json, 'r') as plik:
    REGION_SZABLONU = json.load(plik)

sciezka_ustawien = os.path.join("User Settings", "settings.json")
if not os.path.exists(sciezka_ustawien):
    domyslne = {"klawisz_start": "e", "klawisz_pauza": "f8", "klawisz_stop": "f9", "monitor": 1}
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
MONITOR_INDEX = USTAWIENIA.get("monitor", 1)
ODTWARZAJ_DZWIEK = USTAWIENIA.get("odtwarzaj_dzwiek", False)
AUTO_CHODZENIE = USTAWIENIA.get("auto_chodzenie", False)

sciezka_szablonu = os.path.join("Ressources", "szablon_postepu.png")
sciezka_wydobycia = os.path.join("Ressources", "wydobycie.png")

if not os.path.exists(sciezka_szablonu) or not os.path.exists(sciezka_wydobycia):
    print("BŁĄD: Brak plików graficznych w folderze Ressources!", flush=True)
    sys.exit()

szablon = cv2.imread(sciezka_szablonu, cv2.IMREAD_COLOR)
szablon_wydobycia = cv2.imread(sciezka_wydobycia, cv2.IMREAD_COLOR)

REGION_WYDOBYCIE = {"top": 0, "left": 0, "width": 500, "height": 100}

print("Ładowanie sztucznej inteligencji...", flush=True)
model = YOLO('best.pt')
print("Mózg załadowany pomyślnie!\n", flush=True)

pydirectinput.FAILSAFE = False

sct = mss.MSS()
monitor_glowny = sct.monitors[MONITOR_INDEX]

# ==========================================
# 2. ZMIENNE GLOBALNE DLA GUI I STANU
# ==========================================
dziala = True
spauzowany = False

gui_tekst = "Szukam"
gui_kolor = "#00ff00"
zapisany_tekst = "Szukam"
zapisany_kolor = "#00ff00"

def ustaw_status(tekst, kolor="#00ff00"):
    global gui_tekst, gui_kolor, zapisany_tekst, zapisany_kolor
    # Zapamiętujemy, co bot robił przed wciśnięciem ewentualnej pauzy
    zapisany_tekst = tekst
    zapisany_kolor = kolor
    
    if spauzowany:
        gui_tekst = "Wstrzymane"
        gui_kolor = "orange"
    else:
        gui_tekst = tekst
        gui_kolor = kolor

def przelacz_pauze():
    global spauzowany
    spauzowany = not spauzowany
    # Przywracamy zapamiętany stan (np. "Szukam" na zielono)
    ustaw_status(zapisany_tekst, zapisany_kolor) 
    
    if spauzowany:
        print(f"\n[PAUZA] Wstrzymano. Naciśnij '{KLAWISZ_PAUZA}', aby wznowić.", flush=True)
    else:
        print(f"\n[WZNOWIONO] Kontynuacja pracy.", flush=True)

def zatrzymaj_bota():
    global dziala
    dziala = False
    print(f"\n[STOP] Otrzymano sygnał zatrzymania...", flush=True)

keyboard.on_press_key(KLAWISZ_PAUZA, lambda event: przelacz_pauze())
keyboard.on_press_key(KLAWISZ_STOP, lambda event: zatrzymaj_bota())

# ==========================================
# 3. FUNKCJE POMOCNICZE BOTA
# ==========================================
def bezpieczne_czekanie(czas_sekundy):
    start = time.time()
    while time.time() - start < czas_sekundy:
        if not dziala or spauzowany: return False
        time.sleep(0.01)
    return True

def czy_minigra_aktywna():
    zrzut = np.array(sct.grab(REGION_SZABLONU))
    ekran_bgr = cv2.cvtColor(zrzut, cv2.COLOR_BGRA2BGR)
    wynik = cv2.matchTemplate(ekran_bgr, szablon, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(wynik)
    return max_val > 0.8

def czy_widac_ikonke_wydobycia():
    zrzut = np.array(sct.grab(REGION_WYDOBYCIE))
    ekran_bgr = cv2.cvtColor(zrzut, cv2.COLOR_BGRA2BGR)
    wynik = cv2.matchTemplate(ekran_bgr, szablon_wydobycia, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(wynik)
    return max_val > 0.75

def szybkie_klikniecie(x, y):
    pydirectinput.moveTo(x, y)
    if not bezpieczne_czekanie(0.05): return
    pydirectinput.mouseDown()
    if not bezpieczne_czekanie(0.05): return
    pydirectinput.mouseUp()
    bezpieczne_czekanie(0.02)

# ==========================================
# 4. GŁÓWNY WĄTEK BOTA (Działa w tle)
# ==========================================
def petla_bota():
    global dziala
    print("Bot uruchomiony w tle.", flush=True)
    ustaw_status("Szukam")
    
    biegnie = False # Flaga Maszyny Stanów
    wymus_kopanie = False # Flaga ułatwiająca płynne przejście między biegiem a kopaniem
    
    while dziala:
        # --- BŁYSKAWICZNA OBSŁUGA PAUZY / STOPU ---
        if not dziala or spauzowany:
            if biegnie:
                # Puść klawisze ZAWSZE, gdy bot zostaje przerwany w trakcie biegu
                pydirectinput.keyUp('w')
                pydirectinput.keyUp('shift')
                biegnie = False
                print("[SYSTEM] Bieg przerwany (Pauza/Stop).", flush=True)
            
            if not dziala: break
            time.sleep(0.1)
            continue

        # --- STAN 1: BIEG W POSZUKIWANIU NOWEJ SKAŁY ---
        if biegnie:
            # Używamy spamu zamiast keyDown, żeby nie zablokować nasłuchu z keyboard.add_hotkey!
            # Dodatkowo, jeśli spauzujesz podczas biegu, pętla natychmiast puści klawisze wyżej.
            pydirectinput.keyDown('shift')
            pydirectinput.keyDown('w')
            
            if czy_widac_ikonke_wydobycia():
                print("[SYSTEM] Znalazłem nową skałę! Zatrzymuję bieg.", flush=True)
                pydirectinput.keyUp('w')
                pydirectinput.keyUp('shift')
                biegnie = False
                
                # Złapanie skały przez wciśnięcie 'E'
                pydirectinput.press('e')
                bezpieczne_czekanie(0.08) # Czas na wejście postaci w animację skały
                
                # [POPRAWKA] Od razu przekazujemy pętli informację, żeby w Stanie 2 zaczęła kopać,
                # zamiast liczyć na to, że ikonka wydobycia dalej tam jest.
                wymus_kopanie = True 
            else:
                bezpieczne_czekanie(0.05)
            continue

        # --- STAN 2: SZUKANIE / OCZEKIWANIE NA KOPANIE ---
        uruchomienie_reczne = keyboard.is_pressed(KLAWISZ_START)
        uruchomienie_auto = czy_widac_ikonke_wydobycia()

        # Jeśli zaczęliśmy z ręki, z automatu (obrazek), albo postać właśnie podbiegła do złoża
        if uruchomienie_reczne or uruchomienie_auto or wymus_kopanie:
            ustaw_status("Wydobywam")
            
            # Resetujemy wymuszenie po wejściu do kopania
            wymus_kopanie = False 
            
            # Wciskamy E tylko przy ręcznym/automatycznym rozpoznaniu, bez wymuszenia
            if uruchomienie_auto:
                pydirectinput.press('e')
                if not bezpieczne_czekanie(0.08): continue 

            # --- KOPANIE ZŁOŻA (Spam LPM) ---
            # Tutaj pętla bezpiecznie reaguje na Stop/Pauzę, bo używamy Twojego 'bezpieczne_czekanie'
            while True:
                if not dziala or spauzowany: break
                pydirectinput.mouseDown()
                if not bezpieczne_czekanie(0.05): break
                pydirectinput.mouseUp()
                if not bezpieczne_czekanie(0.02): break
                if czy_minigra_aktywna():
                    break

            # Jeśli zatrzymaliśmy na etapie kopania, przeskakujemy minigrę i wracamy na górę
            if not dziala or spauzowany: continue
            
            # --- STAN 3: ZBIERANIE KAMIENI (MINIGRA AI) ---
            if ODTWARZAJ_DZWIEK:
                winsound.Beep(400, 150)
            ustaw_status("Minigra")

            ostatnia_liczba_kamieni = -1

            while czy_minigra_aktywna():
                if not dziala or spauzowany: break
                    
                screenshot = np.array(sct.grab(REGION_DYWANU))
                obraz_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
                wyniki = model.predict(source=obraz_bgr, conf=0.70, verbose=False)
                znalezione_kamienie = wyniki[0].boxes.xyxy.cpu().numpy()
                
                aktualna_liczba = len(znalezione_kamienie)
        
                if aktualna_liczba > 0:
                    if aktualna_liczba != ostatnia_liczba_kamieni:
                        print(f"[AI] Pozostało kamieni do zebrania: {aktualna_liczba}", flush=True)
                        ostatnia_liczba_kamieni = aktualna_liczba
                        
                    for box in znalezione_kamienie:
                        if not dziala or spauzowany: break
                        if not czy_minigra_aktywna(): break
                        
                        x1, y1, x2, y2 = box
                        srodek_x = int((x1 + x2) / 2 + REGION_DYWANU["left"])
                        srodek_y = int((y1 + y2) / 2 + REGION_DYWANU["top"])
                        szybkie_klikniecie(srodek_x, srodek_y)
                
                if not bezpieczne_czekanie(0.3): break
                
            # --- KONIEC WYDOBYCIA - DECYZJA CO DALEJ ---
            if dziala and not spauzowany:
                ustaw_status("Szukam")
                
                if AUTO_CHODZENIE:
                    print("[SYSTEM] Złoże wyczerpane. Uruchamiam auto-walk (Shift+W)...", flush=True)
                    bezpieczne_czekanie(0.02) # Czekamy aż postać wyprostuje się po minigrze
                    
                    # Włączamy flagę bez wciskania na stałe - Stan 1 zajmie się mechaniką trzymania w następnym cyklu
                    biegnie = True 
                else:
                    bezpieczne_czekanie(0.02)
                
        # Zabezpieczenie przed przegrzaniem procesora w pętli czuwania
        time.sleep(0.05)

    print("\nBot zakończył pracę.", flush=True)

# Uruchamiamy logikę bota w osobnym wątku
watek_bota = threading.Thread(target=petla_bota, daemon=True)
watek_bota.start()

# ==========================================
# 5. WĄTEK GŁÓWNY - OKNO GUI (PyQt6)
# ==========================================
class StatusOverlay(QWidget):
    def __init__(self):
        super().__init__()
        # Konfiguracja okna bazowego (Niewidzialne, bez ramek, zawsze na wierzchu)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Większe okno i marginesy zapobiegają błędom wyświetlania rozmytego cienia
        self.resize(240, 90) 
        self.oldPos = self.pos()

        glowny_layout = QVBoxLayout(self)
        glowny_layout.setContentsMargins(30, 20, 30, 30)

        # Tworzymy widoczny pojemnik (nasz szary prostokąt)
        self.pojemnik = QFrame(self)
        self.pojemnik.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 12px;
                border: 1px solid #2e2e2e;
            }
        """)

        # Prawdziwy, miękki cień
        cien = QGraphicsDropShadowEffect(self)
        cien.setBlurRadius(25)
        cien.setColor(QColor(0, 0, 0, 180))
        cien.setOffset(0, 5)
        self.pojemnik.setGraphicsEffect(cien)

        # Układ elementów wewnątrz szarego prostokąta
        uklad_pojemnika = QHBoxLayout(self.pojemnik)
        uklad_pojemnika.setContentsMargins(20, 0, 15, 0)

        # Tekst (dosunięty do lewej)
        self.etykieta = QLabel(gui_tekst, self)
        self.etykieta.setStyleSheet("""
            QLabel {
                color: white; 
                font-family: 'Segoe UI'; 
                font-size: 11pt; 
                font-weight: bold; 
                border: none;
            }
        """)
        uklad_pojemnika.addWidget(self.etykieta)

        # Sprężyna (wypycha tekst na lewo, kółko na prawo)
        uklad_pojemnika.addStretch()

        # Kółko statusu (po prawej)
        self.kolko = QLabel(self)
        self.kolko.setFixedSize(12, 12)
        self.aktualizuj_kolko(gui_kolor)
        uklad_pojemnika.addWidget(self.kolko)

        glowny_layout.addWidget(self.pojemnik)

        # Timer odświeżający GUI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.odswiez)
        self.timer.start(100)

    def aktualizuj_kolko(self, kolor):
        self.kolko.setStyleSheet(f"""
            QLabel {{
                background-color: {kolor};
                border-radius: 6px;
                border: none;
            }}
        """)

    def odswiez(self):
        if not dziala:
            self.close()
            QApplication.quit()
            return
        self.etykieta.setText(gui_tekst)
        self.aktualizuj_kolko(gui_kolor)

    # Możliwość przeciągania okna
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if not self.oldPos: return
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

# ==========================================
# 6. START APLIKACJI
# ==========================================
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    okno = StatusOverlay()
    okno.show()
    sys.exit(app.exec())