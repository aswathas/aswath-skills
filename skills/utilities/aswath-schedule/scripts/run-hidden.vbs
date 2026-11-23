' run-hidden.vbs - run one command line with no console window.
'
' Usage: wscript.exe //nologo run-hidden.vbs <command-file>
'
' The command file holds a single command line, one line of plain text. It is
' run through WScript.Shell.Run with window style 0 (hidden) and the command's
' exit code becomes this script's exit code.
'
' Why a file and not an argument: a task's Arguments field is a Windows command
' line, so any quote inside the command would be eaten by the parser before
' the script ever sees it. The file keeps the command exactly as written.
'
' Installed to %USERPROFILE%\.claude\tools\run-hidden.vbs by schedule.py.
Option Explicit

Dim sh, fso, f, cmd, rc

If WScript.Arguments.Count < 1 Then
  WScript.Quit 2
End If

Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FileExists(WScript.Arguments(0)) Then
  WScript.Quit 2
End If

Set f = fso.OpenTextFile(WScript.Arguments(0), 1)
cmd = f.ReadAll
f.Close

' Trim only spaces: a trailing CR or LF would end up inside the last argument
' of the command and be passed to the program as part of it.
Do While Len(cmd) > 0
  Select Case Right(cmd, 1)
    Case " ", vbTab, vbCr, vbLf
      cmd = Left(cmd, Len(cmd) - 1)
    Case Else
      Exit Do
  End Select
Loop

If cmd = "" Then
  WScript.Quit 2
End If

Set sh = CreateObject("WScript.Shell")
rc = sh.Run(cmd, 0, True)
WScript.Quit rc
