Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Run pythonw.exe as Administrator, completely invisible
Set objShell = CreateObject("Shell.Application")
objShell.ShellExecute "pythonw.exe", """" & currentDir & "\app.py""", currentDir, "runas", 0
