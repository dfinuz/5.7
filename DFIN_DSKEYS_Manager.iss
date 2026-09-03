[Setup]
AppId={{B10CFE17-5380-48B1-986A-03F4A8872332}
AppName=DFIN DSKEYS Manager
AppVersion=5.7
AppPublisher=www.dfin.uz
DefaultDirName={autopf}\DFIN DSKEYS Manager
DefaultGroupName=DFIN DSKEYS Manager
OutputDir=installer
OutputBaseFilename=DFIN_DSKEYS_Manager_Setup_v5.7_DIAGNOSTIC_FULL
SetupIconFile=dfin_logo.ico
UninstallDisplayIcon={app}\DFIN_DSKEYS_Manager.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: checkedonce
[Files]
Source: "dist\DFIN_DSKEYS_Manager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "vendor\python-3.13.7-amd64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "vendor\*.whl"; DestDir: "{tmp}\wheels"; Flags: deleteafterinstall
[Icons]
Name: "{autoprograms}\DFIN DSKEYS Manager"; Filename: "{app}\DFIN_DSKEYS_Manager.exe"
Name: "{autodesktop}\DFIN DSKEYS Manager"; Filename: "{app}\DFIN_DSKEYS_Manager.exe"; Tasks: desktopicon
[Run]
Filename: "{tmp}\python-3.13.7-amd64.exe"; Parameters: "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_launcher=1 InstallLauncherAllUsers=1 Include_test=0"; StatusMsg: "Installing Python 3.13.7 and Python launcher..."; Flags: waituntilterminated
Filename: "{sys}\cmd.exe"; Parameters: "/C ""C:\Program Files\Python313\python.exe"" -m pip install --no-index --find-links=""{tmp}\wheels"" send2trash cryptography websocket-client > ""{app}\python-install.log"" 2>&1"; StatusMsg: "Installing Python libraries..."; Flags: runhidden waituntilterminated
Filename: "{sys}\cmd.exe"; Parameters: "/C ""C:\Program Files\Python313\python.exe"" --version > ""{app}\python-check.txt"" 2>&1 && ""C:\Program Files\Python313\python.exe"" -c ""import send2trash,cryptography,websocket;print('All Python libraries OK')"" >> ""{app}\python-check.txt"" 2>&1"; StatusMsg: "Verifying Python installation..."; Flags: runhidden waituntilterminated
Filename: "{app}\DFIN_DSKEYS_Manager.exe"; Description: "Launch DFIN DSKEYS Manager"; Flags: nowait postinstall skipifsilent
