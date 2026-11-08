# PixelPilot · 桌面自动化

Electron + TypeScript 控制台，配合 Python、OpenCV 和 PyAutoGUI 执行可配置的桌面自动化流程。当前仓库提供可运行的开发原型。

## 环境

- Node.js 20+
- Python 3.10+
- Windows 10/11（PyAutoGUI 操作要求桌面会话可用）

## 启动

```powershell
npm install
python -m pip install -r python/requirements.txt
npm run dev
```

也可先打开控制面板再安装 Python 依赖；界面会显示 Python 服务状态。开发时需保持 Vite 和 Electron 进程运行。

## 自动化步骤

控制台可编辑步骤标题与模板路径、匹配阈值，使用图片选择对话框挑选模板，添加等待步骤，并通过循环开关重复任务。任务配置会自动保存在当前用户的 Electron 应用数据目录中。后端 JSON 行命令支持 `match_click`、`click`、`key`、`wait`。`config/sample-task.json` 提供了配置示例。

模板匹配在整个屏幕或配置的 `region: [left, top, width, height]` 中搜索。`threshold` 范围为 0 到 1。匹配失败且 `required` 为真时，任务会报错并停止。截图和模板需使用相同缩放比例；Windows 显示缩放可能影响匹配效果。

## 安全与限制

- 按 `Esc` 发送停止命令；面板也提供暂停、继续、停止控制。
- 目前停止检查发生在步骤边界；已经开始的鼠标或键盘动作无法撤销。
- 当前原型没有目标窗口绑定、游戏兼容性保证或稳定性基准；仅对你有权自动化的应用使用。
- 本原型尚未加入目标窗口绑定、自动截取模板、循环间隔编辑和模板匹配预览。
- 任务配置通过本地 JSON 行协议传给 Python 服务，不会上传云端。

