# Gravitrax GUI Application
A Python script that displays a Graphical user Interface for the gravitraxconnect Library. 


![](gravitraxGUI_screenshot.PNG)

# Dependencies
- PySimpleGUI>=4.60.4
- gravitraxconnect >= 0.3.0

# Manual

## Signal Options

### Status 
The Status ID of the Signal usually specifies that only certain Stones will react to the Signal, but it also is used by Stones to transmit additional Information. The Starter Stone for example uses a Status value to signal that a marble was released manually.
### Stone 
The Stone ID identifies the source of a signal. Receiving Stones might react differently to Signals depending on this Value. An example for this would be that Bridge Stones filter out all Signals with the Stone ID set to Bridge, otherwise the Bridge would detect it's own signals.
### Count 
The Count option specifies how many Signals should be send. If this Value is set to 0 no signal is send but the specified Pause duration is awaited.
### Resends
How often the same signal should be transmitted. A higher value decreases the likelihood for package loss to occur. A lower value speeds up the transmission when sending many Signals.
### Resend Gap
Additional wait time in Seconds after every Signal transmission. This can help against package loss, but it's usually best to keep this at 0 and increase the amount of resends instead.
### Pause
Wait time in between every Signal. If the Count for a Signal is set to 0 the duration is awaited without a signal being send.
### Preset
Presets for Signal options can be accessed here.The preset is applied when clicking it in the dropdown list. 
### Add
The Add Button can be used to save the currently selected Signal Options in the presets List. Enter a fitting name for the preset in the presets combobox before pressing this button.
### Save Presets
Save the current Preset List in a json File. This overwrites the previous File when an existing file is selected. 
### Load Presets
Load a Preset List from a json File. 
### Reset
Reset the Signal Options to the Default values.

## Signal Buttons
### Color Buttons (Keyboard Shortcuts: F1, F2, F3)
During normal operation the Buttons Red(F1), Green(F2) and Blue(F3) send Signals in the corresponding Color. If one of the special Modes is active the inputs from the Buttons are used to queue up Signals, set conditions etc.
### Lock Buttons (Keyboard Shortcuts: F4, F5)
The Lock Button(F4) sends out a Signal that puts receiving Stones in Bridge-Only Mode. In this Mode they will only accept Signals where the Stone value is set to Bridge.The Unlock button(F5) reverses this. The Count parameter is ignored when using both the Lock and the Unlock Button.

## Mode Buttons

### Timer (Keyboard Shortcut: F6)
The Timer Button(F6) is used to measures the time between 2 Signals. When the Button is pressed the Signals that start and stop the timer are entered. Whenever a Stop Signal is received after a Start Signal the time in between is printed in the log. The Timer mode can be stopped by pressing the Cancel Button.
### If/Then: (Keyboard Shortcut: F7)
The If/Then Button(F7) allows to implement simple If/Then logic. The first Signal entered after pressing the Button is used as the IF-Condition. Other Signals can be queued afterwards. If the Signal that was set as the IF-Condition is received all Queued up Signals are send. An Example how this can be used is to set a Red Signal from a Remote as the Condition an Queue up 7 Signals with the Status STARTER. A single press on the red remote button will empty a full starter this way.
### Queuemode (Keyboard Shortcut: F8)
The Queuemode Button(F8) starts the Queuemode. In this Mode Signals are put into a queue instead of being send directly. After pressing the Button the Buttontext changes to Send. Pressing the button then sends the queued Up Signals.

## Connection Buttons

### Connect
The Connect Button is used to establish a connection to a Bride. The button is disabled when there is already an active connection to a Bridge.
### Disconnect
Disconnect from the Bridge. If there is no active connection the Button is used to Close the Application.


# License
MIT License

Copyright (c) 2020 University of Pennsylvania

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.