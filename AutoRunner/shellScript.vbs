Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.Run Chr(34) & "C:\your_project_folder\your_script_folder\script.bat" & Chr(34), 0
Set WinScriptHost = Nothing