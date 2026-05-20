import pydirectinput
import time

print("RADAR WŁĄCZONY!")
print("Wejdź do gry, najedź myszką na LEWY GÓRNY RÓG dywanu i nie ruszaj myszki.")
print("Spisz poniższe liczby. (Aby wyłączyć, wciśnij Ctrl+C w terminalu)\n")

while True:
    x, y = pydirectinput.position()
    # end='\r' sprawia, że linijka nadpisuje się w miejscu, nie śmiecąc w konsoli
    print(f"Twój cel -> LEFT: {x} | TOP: {y}        ", end='\r')
    time.sleep(0.1)