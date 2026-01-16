[Setup]
AppName=Kono Transcriptor
AppVersion=1.0.0
DefaultDirName={autopf}\Kono Transcriptor
DefaultGroupName=Kono Transcriptor
OutputBaseFilename=KonoTranscriptorInstaller
Compression=lzma
SolidCompression=yes
; Usar el icono del proyecto para el instalador
SetupIconFile=icon.ico

[Files]
; Ejecutable generado por PyInstaller (generar en dist\\kono-transcriptor.exe)
Source: "dist\\kono-transcriptor.exe"; DestDir: "{app}"; Flags: ignoreversion
; Icono de la aplicación
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Archivos estáticos de la UI
Source: "index_test.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "imgs\\*"; DestDir: "{app}\\imgs"; Flags: recursesubdirs createallsubdirs ignoreversion
; ffmpeg local (incluye ffmpeg.exe y ffprobe.exe en la carpeta ffmpeg)
Source: "ffmpeg\\ffmpeg.exe"; DestDir: "{app}\\ffmpeg"; Flags: ignoreversion
Source: "ffmpeg\\ffprobe.exe"; DestDir: "{app}\\ffmpeg"; Flags: ignoreversion
; Opcional: bootstrapper de WebView2 si quieres incluirlo en el instalador
Source: "webview2\\MicrosoftEdgeWebView2RuntimeInstallerX64.exe"; DestDir: "{tmp}"; Flags: ignoreversion

[Icons]
Name: "{group}\\Kono Transcriptor"; Filename: "{app}\\kono-transcriptor.exe"; IconFilename: "{app}\\icon.ico"
Name: "{group}\\Uninstall Kono Transcriptor"; Filename: "{uninstallexe}"; IconFilename: "{app}\\icon.ico"

[Run]
; Instalar WebView2 silenciosamente si el bootstrapper fue incluido
Filename: "{tmp}\\MicrosoftEdgeWebView2RuntimeInstallerX64.exe"; Parameters: "/silent"; StatusMsg: "Instalando WebView2 Runtime..."; Flags: runhidden waituntilterminated; Check: FileExists(ExpandConstant('{tmp}\\MicrosoftEdgeWebView2RuntimeInstallerX64.exe'))
; Ejecutar la app después de la instalación (opcional)
Filename: "{app}\\kono-transcriptor.exe"; Description: "Ejecutar Kono Transcriptor"; Flags: nowait postinstall skipifsilent
