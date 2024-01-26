Python Bibliothek, welche die Verbindung und Kommunikation mit dem GraviTrax POWER Element Connect realisiert. Beinhaltet GUI- und Konsolenbeispielanwendung, welche das Steuern von POWER RF Steinen über die GravitraxConnect ermöglichen.

# Installation und Nutzung der Gravitrax Python Bibliothek

## Installation Python

Um die Bibliothek zu nutzen, wird Python3 benötigt. Es wird empfohlen mindestens Version 3.10 zu verwenden, da bei älteren Versionen nicht alle Funktionen ordnungsgemäß funktionieren. Dies ist bedingt durch Änderungen an dem asyncio Framework, welches Teil von Python ist. Für die Installation gibt es mehrere Optionen.

### Installation über python.org

Eine aktuelle Version gibt es unter https://www.python.org/downloads/. Bei den Installationsoptionen Python zur PATH Umgebungsvariable hinzufügen.

### Installation über den Microsoft Store
Python kann alternativ über den Microsoft Store installiert werden. [Hier ist die neuste Version](https://www.microsoft.com/store/productId/9NRWMJP3717K), welche von der Python Software Foundation veröffentlicht wurde.

Durch folgende Kommandos in der Windows Eingabeaufforderung lässt sich prüfen, ob die Installation erfolgreich war.

```shell
python -V 
```
und 
```shell
pip -V
```
In beiden Fällen sollte angezeigt werden, welche Versionsnummer aktuell auf ihrem System installiert ist.

## Installation der Bibliothek

1. Code als ZIP-Datei herunterladen.

2. In das Download-Verzeichnis navigieren, die Zip-Datei "GraviTrax-Connect-main.zip" entpacken und in gewünschten Zielordner verschieben.

3. In den Bibliotheks-Ordner navigieren und den Pfad kopieren. Dieser könnte bspw. so aussehen: "C:\Users\Username\Downloads\GraviTrax-Connect-main\GraviTrax-Connect-Python-Library"

4. Windows Eingabeaufforderung öffnen.

5. Bibliothek mit folgendem Kommando installieren:
```shell
pip install <Pfad zu Ordner aus Schritt 3>
```

Alternativ funktionieren die Befehle
```shell
cd <Pfad zu Ordner aus Schritt 3>
```
um in das Verzeichnis zu wechseln, in welchem sich die pyproject.toml Datei befindet. Anschließend folgendes Kommando zur Installation verwenden:
```shell
pip install . 
```

### Überprüfen der Installation

Um alle zusätzlich notwendigen Bibliotheken zu installieren, muss während der installation eine Internetverbindung bestehen. Mit dem Kommando
```shell
pip list
``` 
lässt sich überprüfen, ob die Installation erfolgreich war. In der Liste sollte in der Spalte Package die Bibliothek gravitraxconnect sowie die Bluetooth Bibliothek [bleak](https://github.com/hbldh/bleak) zu sehen sein. Wurde die bleak Bibliothek nicht installiert weil z.B. keine Internetverbindung zum Zeitpunkt der Installation zur Verfügung stand, muss diese separat installiert werden. 
Die einfachste Methode dies zu tun ist bei aktiver Internetverbindung folgendes Kommando
einzugeben:
```
pip install bleak
```

## Programme

Der Bibliothek´s Ordner beinhaltet einen Unterordner "examples" in welchem sich einige Beispielprogramme grundlegender Funktionen befinden. 

Ausführlichere Beispielprogramme finden Sie in dem Ordner "Applications". Hierfür werden ggf. zusätzliche Bibliotheken benötigt, welche in der textdatei requirements.txt aufgeführt werden. Die Installation erfolgt nach Navigation in entsprechendes Verzeichnis mit dem Kommando: 
```shell
pip install -r .\requirements.txt
``` 

Folgende Anwendungen befinden sich in dem Ordner:
- gravitrax_CLI: Ein kommandozeilen Programm welches das Senden und Empfangen von Signalen erlaubt
- gravitrax_GUI: Eine grafische Benutzeroberfläche welches das Senden und Empfangen von Signalen erlaubt.
- gravitrax_gpio: Ein Skript welches die GPIO-Pins eines Raspberry Pi verwendet
- ReactionGame: Ein Reaktionsspiel welches eine Gravitrax Bahn verwendet
