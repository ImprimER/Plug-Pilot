#define MyAppName "PlugPilot"
#ifndef MyAppVersion
  #define MyAppVersion Trim(FileRead(FileOpen("VERSION.txt")))
#endif
#define MyAppPublisher "PlugPilot"
#define MyAppExeName "PlugPilot.exe"

[Setup]
AppId={{8A3E450F-2CB0-44D8-B21A-723773CF86D8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=PlugPilot-Setup
SetupIconFile=assets\plugpilot.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
UsePreviousTasks=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le bureau"; GroupDescription: "Raccourcis :"
Name: "startup"; Description: "Lancer PlugPilot au démarrage de Windows"; GroupDescription: "Démarrage :"; Flags: unchecked

[Files]
Source: "dist\PlugPilot\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\PlugPilot"; Filename: "{app}\PlugPilot.exe"
Name: "{autodesktop}\PlugPilot"; Filename: "{app}\PlugPilot.exe"; Tasks: desktopicon
Name: "{userstartup}\PlugPilot"; Filename: "{app}\PlugPilot.exe"; Tasks: startup

[Run]
Filename: "{app}\PlugPilot.exe"; Description: "Lancer PlugPilot"; Flags: nowait postinstall skipifsilent
Filename: "{app}\PlugPilot.exe"; Flags: nowait runasoriginaluser; Check: WizardSilent
