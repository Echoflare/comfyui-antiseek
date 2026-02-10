import os
from server import PromptServer
from .scripts import antiseek

def setup_hijack():
    server = PromptServer.instance
    app = server.app
    hijacked_routes = antiseek.setup_routes(app)
    
    targets = ["/view", "/api/view", "/upload/image", "/api/upload/image"]

    print("[Anti-Seek] 图像加密组件已加载")
    print("[Anti-Seek] 端点注入状态:")
    
    for target in targets:
        status = "✓" if target in hijacked_routes else "×"
        print(f"    {target}: {status}")

origin_add_routes = PromptServer.add_routes

def new_add_routes(self):
    origin_add_routes(self)
    setup_hijack()

PromptServer.add_routes = new_add_routes

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
WEB_DIRECTORY = "./web/js"