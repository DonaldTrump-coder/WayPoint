; Waypoint - Windows 安装包脚本 (Inno Setup 6)
; 编译: ISCC.exe packaging/installer.iss
; 产物: dist/Waypoint-Setup-1.0.0.exe
;
; 设计要点:
; - 用户可选安装路径（默认 C:\Program Files\Waypoint，可改成任意盘）
; - 程序装到安装目录（Waypoint.exe + 卸载器）
; - 数据文件（waypoint.db / backups）存 %APPDATA%\Waypoint，与安装目录分离
;   → 升级/卸载程序不影响数据；卸载时默认保留数据（勾选删除才删）
; - 卸载时杀掉正在运行的 Waypoint 进程

#define MyAppName "Waypoint"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Waypoint"
#define MyAppExeName "Waypoint.exe"

[Setup]
AppId={{8F3B2C1A-4E5D-4F6A-9B7C-1A2B3C4D5E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Waypoint
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 数据目录固定 APPDATA，不随安装路径变化
PrivilegesRequired=admin
OutputDir=..\dist
OutputBaseFilename=Waypoint-Setup-{#MyAppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; one-dir 全部内容（启动器 + _internal 依赖）递归安装，保持目录结构
Source: "..\dist\Waypoint\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 使用说明
Source: "README-Waypoint.txt"; DestDir: "{app}"; Flags: ignoreversion

; 预创建空数据目录（waypoint.db / backups 运行时落在这里，跟随安装路径，不写系统盘）
[Dirs]
Name: "{app}\data"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\使用说明"; Filename: "{app}\README-Waypoint.txt"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后可选立即启动
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; 卸载前杀掉运行中的进程，避免文件占用
Filename: "taskkill.exe"; Parameters: "/F /IM Waypoint.exe"; Flags: runhidden waituntilterminated

[Code]
// 卸载时询问是否同时删除数据（默认不删）——用 MsgBox 弹窗，
// 避免 CreateInputOptionPage 依赖安装向导页面（卸载向导中不存在会报错）
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox('是否同时删除数据文件？' + Chr(13) + Chr(10) + Chr(13) + Chr(10) +
      '数据文件（项目、任务、笔记、AI 配置、聊天记录）保存在安装目录的 data 子目录。' + Chr(13) + Chr(10) +
      '勾选「是」将永久删除，无法恢复；「否」则保留，重装可继续使用。',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      DataDir := ExpandConstant('{app}\data');
      if DirExists(DataDir) then
        DelTree(DataDir, True, True, True);
    end;
  end;
end;
