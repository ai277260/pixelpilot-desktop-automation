"""JSON-lines control service for the Electron desktop app."""
from __future__ import annotations
import json, sys, threading, time
from pathlib import Path

try:
    import cv2
    import numpy as np
    import pyautogui
    DEPENDENCIES_OK = True
except Exception as exc:
    DEPENDENCIES_OK = False
    DEPENDENCY_ERROR = str(exc)

lock = threading.Lock()
state = {"status": "idle", "stop": False, "paused": False}

def emit(kind: str, **payload):
    print(json.dumps({"type": kind, **payload}, ensure_ascii=False), flush=True)

def match_template(template_path: str, threshold: float = 0.86, region=None):
    if not DEPENDENCIES_OK: raise RuntimeError("请先安装 python/requirements.txt 中的依赖")
    template = cv2.imread(template_path)
    if template is None: raise ValueError(f"无法读取模板: {template_path}")
    shot = pyautogui.screenshot(region=tuple(region) if region else None)
    screen = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, point = cv2.minMaxLoc(result)
    h, w = template.shape[:2]
    if score < threshold: return None, float(score)
    x0, y0 = (region[0], region[1]) if region else (0, 0)
    return (x0 + point[0] + w // 2, y0 + point[1] + h // 2), float(score)

def run_task(config: dict):
    with lock: state.update(status="running", stop=False, paused=False)
    emit("status", status="running", detail="任务已启动")
    steps = config.get("steps", [])
    if not steps:
        emit("status", status="error", detail="任务没有步骤，无法启动")
        with lock: state["status"] = "idle"
        return
    try:
        repeat = bool(config.get("loop", False))
        while True:
            for index, step in enumerate(steps):
                while state["paused"] and not state["stop"]: time.sleep(.1)
                if state["stop"]: break
                emit("step", index=index, total=len(steps), label=step.get("label", f"步骤 {index + 1}"))
                if step.get("type") == "wait":
                    deadline = time.monotonic() + max(0, float(step.get("seconds", 1)))
                    while time.monotonic() < deadline and not state["stop"]:
                        while state["paused"] and not state["stop"]: time.sleep(.1)
                        time.sleep(min(.1, max(0, deadline - time.monotonic())))
                elif step.get("type") == "click":
                    if not DEPENDENCIES_OK: raise RuntimeError("请先安装 python/requirements.txt 中的依赖")
                    pyautogui.click(int(step["x"]), int(step["y"]))
                elif step.get("type") == "key":
                    if not DEPENDENCIES_OK: raise RuntimeError("请先安装 python/requirements.txt 中的依赖")
                    pyautogui.press(str(step["key"]))
                elif step.get("type") == "match_click":
                    point, score = match_template(step["template"], float(step.get("threshold", .86)), step.get("region"))
                    emit("recognition", score=round(score, 4), matched=point is not None)
                    if point:
                        if step.get("click", True): pyautogui.click(*point)
                    elif step.get("required", True): raise RuntimeError(f"未识别到目标: {step.get('label', step['template'])}")
                emit("progress", current=index + 1, total=len(steps))
            if state["stop"] or not repeat: break
            emit("cycle", detail="本轮完成，开始下一轮")
        final = "stopped" if state["stop"] else "completed"
        emit("status", status=final, detail="任务已停止" if state["stop"] else "任务已完成")
    except Exception as exc: emit("status", status="error", detail=str(exc))
    finally:
        with lock: state["status"] = "idle"

def handle(command: dict):
    action = command.get("action")
    if action == "start":
        if state["status"] == "running": return
        threading.Thread(target=run_task, args=(command.get("config", {}),), daemon=True).start()
    elif action == "pause": state["paused"] = True; emit("status", status="paused", detail="任务已暂停")
    elif action == "resume": state["paused"] = False; emit("status", status="running", detail="任务继续运行")
    elif action == "stop": state["stop"] = True; state["paused"] = False; emit("status", status="stopping", detail="正在停止…")
    elif action == "ping": emit("status", status="ready" if DEPENDENCIES_OK else "setup", detail="Python 服务已连接" if DEPENDENCIES_OK else f"依赖未安装：{DEPENDENCY_ERROR}")

if __name__ == "__main__":
    emit("status", status="ready" if DEPENDENCIES_OK else "setup", detail="Python 服务已连接" if DEPENDENCIES_OK else f"依赖未安装：{DEPENDENCY_ERROR}")
    for raw in sys.stdin:
        try: handle(json.loads(raw))
        except Exception as exc: emit("log", message=f"命令处理失败: {exc}")

