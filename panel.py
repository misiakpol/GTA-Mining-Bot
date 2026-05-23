import sys
import os
import json
import subprocess
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, 
                             QLineEdit, QPlainTextEdit, QHBoxLayout, 
                             QVBoxLayout, QGroupBox, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, QProcess, QObject, pyqtSignal, QProcessEnvironment
from PyQt6.QtGui import QIcon

# Ścieżka do ustawień
SCIEZKA_USTAWIEN = os.path.join("User Settings", "settings.json")

class PrzekierowanieLogow(QObject):
    """Klasa przechwytująca wyjście procesów i zamieniająca je na sygnały Qt"""
    nowy_log = pyqtSignal(str)

    def write(self, tekst):
        if tekst.strip():
            self.nowy_log.emit(tekst.strip())
            
    def flush(self):
        pass

class PanelSterowania(QWidget):
    def __init__(self):
        super().__init__()
        self.proces_bota = None
        self.proces_kreatora = None
        self.init_ui()
        self.wczytaj_ustawienia()

    def init_ui(self):
        # 1. Główne okno panelu
        self.setWindowTitle("GTA V Bot - Panel Sterowania")
        self.setWindowIcon(QIcon("ikona.ico"))
        self.resize(850, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial;
                font-size: 10pt;
            }
            QGroupBox {
                border: 1px solid #2d2d2d;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #ff0073;
                border: 1px solid #8f0047;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff69b4;
                border: 1px solid #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #111111;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 4px;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #00ff00;
            }
        """)

        # Układ główny - poziomy (Lewa strona | Prawa strona)
        uklad_glowny = QHBoxLayout(self)

        # ==========================================
        # LEWA STRONA: PRZYCISKI I USTAWIENIA
        # ==========================================
        lewa_strona = QVBoxLayout()

        # Grupa: Akcje bota
        grupa_akcji = QGroupBox("Zarządzanie Botem")
        uklad_akcji = QVBoxLayout(grupa_akcji)

        self.btn_bot = QPushButton("URUCHOM BOTA")
        self.btn_bot.setStyleSheet("font-size: 11pt; color: #ffffff;")
        self.btn_bot.clicked.connect(self.zarzadzaj_botem)
        uklad_akcji.addWidget(self.btn_bot)

        self.btn_kreator = QPushButton("Uruchom Kreator Obszarów")
        self.btn_kreator.clicked.connect(self.uruchom_kreator)
        uklad_akcji.addWidget(self.btn_kreator)
        lewa_strona.addWidget(grupa_akcji)

        # Grupa: Edycja ustawień (settings.json)
        grupa_ustawien = QGroupBox("Ustawienia (settings.json)")
        uklad_ustawien = QVBoxLayout(grupa_ustawien)

        # Pola tekstowe dla klawiszy
        self.input_start = self.stworz_pole_ustawienia(uklad_ustawien, "Klawisz Start:")
        self.input_pauza = self.stworz_pole_ustawienia(uklad_ustawien, "Klawisz Pauzy:")
        self.input_stop = self.stworz_pole_ustawienia(uklad_ustawien, "Klawisz Stop:")
        self.input_monitor = self.stworz_pole_ustawienia(uklad_ustawien, "Indeks Monitora:")
        self.chk_dzwiek = QCheckBox("Odtwórz dźwięk po wydobyciu kamienia")
        self.chk_dzwiek.setStyleSheet("margin-top: 5px; margin-bottom: 5px;")
        uklad_ustawien.addWidget(self.chk_dzwiek)
        self.chk_chodzenie = QCheckBox("Auto-Walk")
        self.chk_chodzenie.setStyleSheet("margin-top: 5px; margin-bottom: 5px;")
        uklad_ustawien.addWidget(self.chk_chodzenie)

        # Przycisk zapisu
        self.btn_zapisz = QPushButton("Zapisz Ustawienia")
        self.btn_zapisz.setStyleSheet("background-color: #52263c; border-color: #78003c;")
        self.btn_zapisz.clicked.connect(self.zapisz_ustawienia)
        uklad_ustawien.addWidget(self.btn_zapisz)

        lewa_strona.addWidget(grupa_ustawien)
        lewa_strona.addStretch() # Pcha wszystko do góry
        uklad_glowny.addLayout(lewa_strona, stretch=2)

        # ==========================================
        # PRAWA STRONA: ELEGANCKI TERMINAL
        # ==========================================
        prawa_strona = QVBoxLayout()
        label_terminal = QLabel("Konsola systemowa (Logi bota):")
        label_terminal.setStyleSheet("font-weight: bold; color: #888888;")
        prawa_strona.addWidget(label_terminal)

        self.terminal = QPlainTextEdit(self)
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0a0a0a;
                border: 1px solid #222222;
                border-radius: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9.5pt;
                color: #a3a3a3;
            }
        """)
        prawa_strona.addWidget(self.terminal)
        uklad_glowny.addLayout(prawa_strona, stretch=3)

    def stworz_pole_ustawienia(self, uklad, tekst_labela):
        """Pomocnicza funkcja generująca parę Opis + Pole tekstowe"""
        uklad_h = QHBoxLayout()
        lbl = QLabel(tekst_labela)
        lbl.setFixedWidth(110)
        inp = QLineEdit()
        uklad_h.addWidget(lbl)
        uklad_h.addWidget(inp)
        uklad.addLayout(uklad_h)
        return inp

    # ==========================================
    # LOGIKA I OBSŁUGA PLIKÓW / PROCESÓW
    # ==========================================
    def wczytaj_ustawienia(self):
        #Jeśli plik nie istnieje (pierwsze uruchomienie), stwórz go z domyślnymi wartościami
        if not os.path.exists(SCIEZKA_USTAWIEN):
            domyslne = {
                "klawisz_start": "e",
                "klawisz_pauza": "f8",
                "klawisz_stop": "f9",
                "monitor": 1,
                "odtwarzaj_dzwiek": False,
                "auto_chodzenie": False
            }
            os.makedirs("User Settings", exist_ok=True)
            with open(SCIEZKA_USTAWIEN, 'w') as plik:
                json.dump(domyslne, plik, indent=4)
                
        # Jeżeli istnieje; odczytujemy go do panelu:
        with open(SCIEZKA_USTAWIEN, 'r') as plik:
            dane = json.load(plik)
            self.input_start.setText(str(dane.get("klawisz_start", "e")))
            self.input_pauza.setText(str(dane.get("klawisz_pauza", "f8")))
            self.input_stop.setText(str(dane.get("klawisz_stop", "f9")))
            self.input_monitor.setText(str(dane.get("monitor", 1)))
            self.chk_dzwiek.setChecked(dane.get("odtwarzaj_dzwiek", False))
            self.chk_chodzenie.setChecked(dane.get("auto_chodzenie", False))

    def zapisz_ustawienia(self):
        nowe_ustawienia = {
            "klawisz_start": self.input_start.text().strip(),
            "klawisz_pauza": self.input_pauza.text().strip(),
            "klawisz_stop": self.input_stop.text().strip(),
            "monitor": int(self.input_monitor.text().strip() if self.input_monitor.text().isdigit() else 1),
            "odtwarzaj_dzwiek": self.chk_dzwiek.isChecked(),
            "auto_chodzenie": self.chk_chodzenie.isChecked()
        }
        os.makedirs("User Settings", exist_ok=True)
        with open(SCIEZKA_USTAWIEN, 'w') as plik:
            json.dump(nowe_ustawienia, plik, indent=4)
        
        self.loguj("[SYSTEM] Pomyślnie zapisano nowe ustawienia do settings.json")
        QMessageBox.information(self, "Sukces", "Ustawienia zostały zapisane!")

    def loguj(self, tekst):
        """Dodaje tekst do naszego wbudowanego terminala"""
        self.terminal.appendPlainText(tekst)
        # Automatyczne przewijanie konsoli na sam dół
        self.terminal.ensureCursorVisible()

    def zarzadzaj_botem(self):
        """Uruchamia lub zatrzymuje bota jako niezależny proces sub-skryptu"""
        if self.proces_bota is None:
            self.loguj("[SYSTEM] Uruchamianie bota w tle...")
            self.proces_bota = QProcess()
            srodowisko = QProcessEnvironment.systemEnvironment()
            srodowisko.insert("PYTHONUNBUFFERED", "1")
            self.proces_bota.setProcessEnvironment(srodowisko)
            self.proces_bota.readyReadStandardOutput.connect(self.obsluga_outputu_bota)
            self.proces_bota.readyReadStandardError.connect(self.obsluga_bledow_bota)
            self.proces_bota.finished.connect(self.bot_zakonczyl)
            
            # Inteligentne wykrywanie środowiska (Skrypt vs Gotowy EXE)
            if getattr(sys, 'frozen', False):
                # Tryb produkcyjny (EXE): uruchamiamy bot.exe z tego samego folderu
                folder_aplikacji = os.path.dirname(sys.executable)
                sciezka_bota = os.path.join(folder_aplikacji, "bot.exe")
                self.proces_bota.start(sciezka_bota)
            else:
                # Tryb deweloperski (Python): uruchamiamy bot.py przez interpreter
                self.proces_bota.start(sys.executable, ["-u", "bot.py"])
            
            self.btn_bot.setText("ZATRZYMAJ BOTA")
            self.btn_bot.setStyleSheet("font-size: 11pt; color: #ffffff;")
            self.btn_zapisz.setEnabled(False) # Blokujemy edycję podczas pracy bota
        else:
            self.loguj("[SYSTEM] Wysyłanie żądania zatrzymania bota...")
            # Ponieważ bot słucha hotkeya F9 (KLAWISZ_STOP), QProcess zamknie go bezpiecznie killując proces
            self.proces_bota.kill()

    def bot_zakonczyl(self):
        self.proces_bota = None
        self.btn_bot.setText("URUCHOM BOTA")
        self.btn_bot.setStyleSheet("font-size: 11pt; color: #ffffff;")
        self.btn_zapisz.setEnabled(True)
        self.loguj("[SYSTEM] Bot został całkowicie wyłączony.")

    def obsluga_outputu_bota(self):
        dane = self.proces_bota.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.loguj(dane.strip())

    def obsluga_bledow_bota(self):
        dane = self.proces_bota.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.loguj(f"[BŁĄD BOTA] {dane.strip()}")

    def uruchom_kreator(self):
        """Uruchamia kreator obszarów jako osobny proces zewnętrzny"""
        if self.proces_bota is not None:
            QMessageBox.warning(self, "Błąd", "Nie możesz uruchomić kreatora, kiedy bot pracuje!")
            return
            
        self.loguj("[SYSTEM] Uruchamianie Kreatora Obszarów... Przygotuj ekran gry!")

        # Inteligentne wykrywanie środowiska dla kreatora
        if getattr(sys, 'frozen', False):
            # Tryb produkcyjny (jako skompilowany plik .exe)
            folder_aplikacji = os.path.dirname(sys.executable)
            sciezka_kreatora = os.path.join(folder_aplikacji, "wybierak_obszaru.exe")
            subprocess.Popen([sciezka_kreatora])
        else:
            # Tryb deweloperski (jako zwykły skrypt w Pythonie)
            subprocess.Popen([sys.executable, "wybierak_obszaru.py"])

# ==========================================
# Uruchomienie aplikacji Panelu Sterowania
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    panel = PanelSterowania()
    panel.show()
    sys.exit(app.exec())