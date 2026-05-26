[Setup]
AppName=Prism
AppVersion=1.0.0
DefaultDirName={autopf}\Prism
DefaultGroupName=Prism
OutputDir=..\dist
OutputBaseFilename=PrismInstaller
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\build\Prism\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Prism"; Filename: "{app}\Python311\Prism.exe"