Erlaubt das Verbinden von GraviTrax Power RF Steinen mit dem PC mithilfe des BLE Connect Steines.

# Installation und Nutzung der Gravitrax Python Bibliothek

## Installation Python

Um die Bibliothek zu nutzen, benötigen Sie Python3. Es wird empfohlen mindestens Version 3.10 zu verwenden, da bei älteren Versionen nicht alle Funktionen ordnungsgemäß funktionieren. Dies ist bedingt durch Änderungen an dem asyncio Framework welches teil von Python ist. Für die Installation haben Sie mehrere Optionen.

### Installation über den Microsoft Store
Sie können python über den Microsoft Store beziehen. Hierfür reicht es idR. in der Windows Eingabeaufforderung oder im Ausführen Dialog(Win+R) "python3" einzugeben. Ist python3 nicht installiert sollten Sie auf direkt auf die Installationsseite gelangen. Alternativ können Sie im Microsoft Store nach python3 suchen. Installieren Sie hier die [neuste Version](https://www.microsoft.com/store/productId/9NRWMJP3717K) welche von der Python Software Foundation veröffentlicht wurde. 

### Installation von python.org

Eine aktuelle Version erhalten Sie unter https://www.python.org/downloads/. Wählen Sie bei der Installation aus, dass Sie python zur PATH Umgebungsvariable hinzufügen möchten.
Ob die Installation erfolgreich war, überprüfen sie in der Windows Eingabeaufforderung durch Eingabe der Kommandos. 

```shell
python -V 
```
und 
```shell
pip -V
```
In beiden Fällen sollte angezeigt werden, welche Versionsnummer aktuell auf ihrem System installiert ist.

## Installation der Bibliothek

1. Laden Sie die zip Datei, welche die Bibliothek beinhaltet herunter.

2. Navigieren Sie in das Download Verzeichnis und entpacken Sie die Zip-Datei.

3. Sie sollten nun einen Ordner mit dem Namen gravitraxconnect_X.X.X in ihrem Download Verzeichnis sehen. 
Öffnen Sie diesen Ordner und kopieren den Pfad aus der Adressleiste. Der Pfad sollte in etwa so aussehen "C:\Users\\"Ihr Benutzername"\Downloads\gravitraxconnect_X.X.X"

4. Öffnen Sie die Windows Eingabeaufforderung.

5. Installieren Sie die Bibliothek mit folgendem Kommando:
```shell
pip install <Pfad zu Ordner aus Schritt 3>
```

Alternativ können Sie über den Befehl
```shell
cd <Pfad zu Ordner aus Schritt 3>
```
in das Verzeichnis wechseln in welchem sich die pyproject.toml Datei befindet und folgendes Kommando zur Installation verwenden:
```shell
pip install . 
```

### Überprüfen der Installation

Um alle zusätzlich notwendigen Bibliotheken zu installieren, muss währen der installation eine Internetverbindung bestehen. Ob die Installation erfolgreich war, können Sie überprüfen, indem Sie das Kommando 
```shell
pip list
``` 
aufrufen. In der Liste sollten Sie nun in der Spalte Package die Bibliothek gravitraxconnect sowie die Bluetooth Bibliothek [bleak](https://github.com/hbldh/bleak) finden können. Wurde die bleak Bibliothek nicht installiert weil z.B. keine Internetverbindung zum Zeitpunkt der Installation zur Verfügung stand, muss diese separat installiert werden. 
Die einfachste Methode dies zu tun ist bei aktiver Internetverbindung folgendes Kommando
einzugeben:
```
pip install bleak
```

## Programme

Der Bibliothek´s Ordner beinhaltet einen Unterordner examples in welchem sich einige Beispielprogramme der grundlegenden Funktionen befinden. 

Ausführlichere Beispielprogramme finden Sie in dem Ordner Scripts welcher sich im selben Verzeichnis wie diese Datei befinden sollte. Hierfür werden ggf. zusätzliche Bibliotheken benötigt welche in der textdatei requirements.txt aufgeführt werden. Die Installation erfolgt in dem entsprechenden Verzeichnis mit dem Kommando: 
```shell
pip install -r .\requirements.txt
``` 

Im Ordner "Bleak Library Applications" befinden sich folgende Anwendungen:
- gravitrax_CLI: Ein kommandozeilen Programm welches das Senden und Empfangen von Signalen erlaubt
- gravitrax_GUI: Eine grafische Benutzeroberfläche welches das Senden und Empfangen von Signalen erlaubt.
- gravitrax_gpio: Ein Skript welches die GPIO-Pins eines Raspberry Pi verwendet
- ReactionGame: Ein Reaktionsspiel welches eine Gravitrax Bahn verwendet
- Timer: Ein Skript welches die Zeit zwischen dem Start einer Kugel und dem Passieren eines GraviTrax Power Finish Stein misst.
