' Double-click to start Desk Todo without a console window.
' Requires Python 3.10+ with PySide6 (see README).
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
entry = fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), "desk_todo.pyw")

On Error Resume Next
' Prefer the Python launcher (ships with python.org installers), else pythonw on PATH.
sh.Run "pyw -3 """ & entry & """", 0, False
If Err.Number <> 0 Then
    Err.Clear
    sh.Run "pythonw """ & entry & """", 0, False
End If
