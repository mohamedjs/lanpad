; Inno Setup script for LANpad on Windows.
;   iscc /DAppVersion=1.0.0 packaging\windows\lanpad.iss
; Expects the PyInstaller folder at dist\lanpad and writes dist\LANpad-Setup-<version>.exe.

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{8B41D88E-632D-4C92-A28D-3E2A1C90D114}
AppName=LANpad
AppVersion={#AppVersion}
AppPublisher=Mohamed
AppPublisherURL=https://github.com/mohamedjs/lanpad
DefaultDirName={autopf}\LANpad
DefaultGroupName=LANpad
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\dist
OutputBaseFilename=LANpad-Setup-{#AppVersion}
SetupIconFile=..\icons\lanpad.ico
UninstallDisplayIcon={app}\lanpad.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "autostart"; Description: "Start LANpad automatically at sign-in"; GroupDescription: "Startup:"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\lanpad\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\LANpad"; Filename: "{app}\lanpad.exe"
Name: "{group}\Uninstall LANpad"; Filename: "{uninstallexe}"
Name: "{autodesktop}\LANpad"; Filename: "{app}\lanpad.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "LANpad"; \
  ValueData: """{app}\lanpad.exe"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\lanpad.exe"; Description: "Launch LANpad now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /IM lanpad.exe /F"; Flags: runhidden; RunOnceId: "StopLANpad"
