; [Setup] section: defines installer-wide settings
[Setup]
; AppName: visible name of the application in the installer UI
AppName=Prism
; AppVersion: version string embedded in the installer
AppVersion=1.0.0
; AppId: unique identifier for the application (used in registry, upgrade detection)
AppId=Prism
; DefaultDirName: default installation folder, {autopf} expands to Program Files
DefaultDirName={autopf}\Prism
; DefaultGroupName: default Start Menu group name
DefaultGroupName=Prism
; OutputDir: where the compiled installer (.exe) will be written
OutputDir=..\dist
; OutputBaseFilename: base name for the generated installer file
OutputBaseFilename=PrismInstaller
; Compression: compression algorithm used for the installer payload
Compression=lzma
; SolidCompression: whether to use solid compression for better size
SolidCompression=yes
; DisableWelcomePage: controls if the initial welcome page is shown (yes/no)
DisableWelcomePage=no

; [Files] section: files to include in the installer and where to place them
[Files]
; Source: path on build machine; DestDir: destination on target system ("{app}" = chosen install folder)
; Flags: additional behaviors; recursesubdirs = include subfolders; createallsubdirs = create folders
Source: "..\build\Prism\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

; [Icons] section: shortcuts to create
[Icons]
; Name: shortcut location in Start Menu group; Filename: target executable
Name: "{group}\Prism"; Filename: "{app}\Python311\Prism.exe"

; [Code] section: Pascal Script code to run during install (event handlers, helpers)
[Code]
// InitializeSetup: event function run before the wizard starts
function InitializeSetup(): Boolean;
var
  // PrevInstallPath: stores detected previous install folder path
  PrevInstallPath: string;
  // IsUpdate: boolean flag indicating if this is an update of existing install
  IsUpdate: Boolean;
begin
  // RegQueryStringValue: reads a string value from the Windows Registry
  // HKLM = HKEY_LOCAL_MACHINE (machine-wide); the first call checks typical Uninstall key
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism_is1', 'InstallLocation', PrevInstallPath) then
  begin
    IsUpdate := True;
    // WizardForm.DirEdit.Text: sets the install folder field in the UI to the previous path
    WizardForm.DirEdit.Text := PrevInstallPath;
  end
  // HKCU = HKEY_CURRENT_USER (per-user); fallback registry location check
  else if RegQueryStringValue(HKCU, 'Software\Prism', 'InstallPath', PrevInstallPath) then
  begin
    IsUpdate := True;
    WizardForm.DirEdit.Text := PrevInstallPath;
  end;
  
  // Return True to continue setup; returning False would abort installer
  Result := True;
end;

// NextButtonClick: event handler called when the Next button is pressed
// CurPageID: numeric identifier of the current wizard page (e.g., wpSelectDir)
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  // wpSelectDir: constant for the directory selection page
  if CurPageID = wpSelectDir then
  begin
    // MsgBox: show an information dialog to the user
    MsgBox('This will update your existing Prism installation at: ' + WizardForm.DirEdit.Text, mbInformation, MB_OK);
  end;
  // Returning True allows the wizard to proceed to the next page
  Result := True;
end;