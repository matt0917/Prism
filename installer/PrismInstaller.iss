[Setup]
AppName=Prism
AppVersion=1.0.0
AppId=Prism
DefaultDirName={autopf}\Prism
DefaultGroupName=Prism
OutputDir=..\dist
OutputBaseFilename=PrismInstaller
Compression=lzma
SolidCompression=yes
DisableWelcomePage=no

[Files]
Source: "..\build\Prism\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Prism"; Filename: "{app}\Python311\Prism.exe"

[Code]
function InitializeSetup(): Boolean;
var
  PrevInstallPath: string;
  IsUpdate: Boolean;
begin
  // Try to find previous installation path from registry
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism_is1', 'InstallLocation', PrevInstallPath) then
  begin
    IsUpdate := True;
    // Change install path to previous location (auto-detect)
    WizardForm.DirEdit.Text := PrevInstallPath;
  end
  else if RegQueryStringValue(HKCU, 'Software\Prism', 'InstallPath', PrevInstallPath) then
  begin
    IsUpdate := True;
    WizardForm.DirEdit.Text := PrevInstallPath;
  end;
  
  Result := True;
end;

procedure NextButtonClick(CurPageID: Integer);
begin
  // Show update message on directory selection page
  if CurPageID = wpSelectDir then
  begin
    MsgBox('This will update your existing Prism installation at: ' + WizardForm.DirEdit.Text, mbInformation, MB_OK);
  end;
end;