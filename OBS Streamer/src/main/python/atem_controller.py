import PyATEMMax

switcher = PyATEMMax.ATEMMax()
switcher.connect("192.168.1.146")
if switcher.waitForConnection(infinite=False):
    switcher.setMacroAction(switcher.atem.macros.macro8, switcher.atem.macroActions.runMacro)
    print("Settings updated")
else:
    print("ERROR: no response from switcher")

switcher.disconnect()
