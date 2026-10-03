#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{7982C8AF-E29A-495A-89B6-2989B74AF058}
AppName=VARD EEG-ERP
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\VARD-EEG-ERP
DefaultGroupName=VARD EEG-ERP
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installer
OutputBaseFilename=VARD-EEG-ERP-Setup-{#AppVersion}-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
Uninstallable=yes
UninstallDisplayName=VARD EEG-ERP
UninstallDisplayIcon={app}\VARD-EEG-ERP.exe
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; Flags: unchecked

[Files]
Source: "..\dist\VARD-EEG-ERP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\VARD EEG-ERP"; Filename: "{app}\VARD-EEG-ERP.exe"
Name: "{group}\Uninstall VARD EEG-ERP"; Filename: "{uninstallexe}"
Name: "{autodesktop}\VARD EEG-ERP"; Filename: "{app}\VARD-EEG-ERP.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\VARD-EEG-ERP.exe"; Description: "Jalankan VARD EEG-ERP"; Flags: nowait postinstall skipifsilent
