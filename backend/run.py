"""
=====  本地开发服务器启动脚本  =====

这是启动 SOAR 系统开发服务器的快捷方式。
直接运行此文件即可启动 FastAPI 应用。

用法：
    python backend/run.py

服务将启动在 http://127.0.0.1:8000
"""

import uvicorn


if __name__ == "__main__":
    """
    使用 uvicorn ASGI 服务器启动 FastAPI 应用。

    参数说明：
        app: "app.main:app" 指向 app/main.py 中的 app 实例
        host: 监听 127.0.0.1（仅本地访问，如需公网访问改为 "0.0.0.0"）
        port: 监听 8000 端口
        reload: 开发模式，代码变更时自动重启
    """
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)