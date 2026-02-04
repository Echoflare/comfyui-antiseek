import os
import json
import io
import sys
from PIL import Image, PngImagePlugin, ImageOps
from aiohttp import web
import folder_paths
from server import PromptServer
from .core import process_image, get_random_seed, mix_seed, get_image_hash, generate_fake_image

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.json")

config = {
    "antiseek_salt": "",
    "antiseek_keyname": "s_tag"
}

if os.path.exists(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config.update(json.load(f))
    except Exception as e:
        print(f"[Anti-Seek] 加载配置文件失败: {e}")

_original_save = Image.Image.save
_original_open = Image.open

def antiseek_save(self, fp, format=None, **params):
    if 'e_info' in (self.info or {}):
        return _original_save(self, fp, format=format, **params)

    filename = ""
    if hasattr(fp, "name"):
        filename = fp.name
    elif isinstance(fp, str):
        filename = fp

    if not filename:
        return _original_save(self, fp, format=format, **params)

    back_img = self.copy()
    
    try:
        orig_hash = get_image_hash(self)
        seed = get_random_seed()
        salt = config["antiseek_salt"]
        key_name = config["antiseek_keyname"]
        
        eff_seed = mix_seed(seed, salt)
        encrypted = process_image(self, eff_seed)
        
        self.paste(encrypted)
        
        pnginfo = params.get('pnginfo')
        if pnginfo is None:
            pnginfo = PngImagePlugin.PngInfo()
            
        for k, v in (self.info or {}).items():
            if k not in ['e_info', key_name] and v:
                try:
                    pnginfo.add_text(str(k), str(v))
                except:
                    pass

        pnginfo.add_text(key_name, str(seed))
        pnginfo.add_text('e_info', orig_hash)
        params['pnginfo'] = pnginfo
        
        return _original_save(self, fp, format="PNG", **params)
    except Exception as e:
        print(f"[Anti-Seek] 加密保存失败: {e}")
        return _original_save(back_img, fp, format="PNG", **params)
    finally:
        self.paste(back_img)

def antiseek_open(fp, mode="r", formats=None):
    image = _original_open(fp, mode=mode, formats=formats)
    pnginfo = image.info or {}
    
    if 'e_info' in pnginfo:
        try:
            key_name = config["antiseek_keyname"]
            salt = config["antiseek_salt"]
            
            if key_name in pnginfo:
                seed = int(pnginfo[key_name])
                eff_seed = mix_seed(seed, salt)
                decrypted = process_image(image, eff_seed)
                
                check_hash = get_image_hash(decrypted)
                
                if check_hash == pnginfo['e_info']:
                    pnginfo_clean = image.info.copy()
                    if key_name in pnginfo_clean: del pnginfo_clean[key_name]
                    if 'e_info' in pnginfo_clean: del pnginfo_clean['e_info']
                    
                    decrypted.info = pnginfo_clean
                    return decrypted
            
            fake_img = generate_fake_image(image.width, image.height)
            fake_img.info = image.info
            return fake_img
            
        except Exception as e:
            print(f"[Anti-Seek] 解密失败: {e}")
            fake_img = generate_fake_image(image.width, image.height)
            fake_img.info = image.info
            return fake_img
            
    return image

Image.Image.save = antiseek_save
Image.open = antiseek_open

async def hooked_view_image(request):
    if "filename" in request.rel_url.query:
        filename = request.rel_url.query["filename"]
        filename, output_dir = folder_paths.annotated_filepath(filename)

        if not filename:
            return web.Response(status=400)

        if filename[0] == '/' or '..' in filename:
            return web.Response(status=400)

        if output_dir is None:
            type = request.rel_url.query.get("type", "output")
            output_dir = folder_paths.get_directory_by_type(type)

        if output_dir is None:
            return web.Response(status=400)

        if "subfolder" in request.rel_url.query:
            full_output_dir = os.path.join(output_dir, request.rel_url.query["subfolder"])
            if os.path.commonpath((os.path.abspath(full_output_dir), output_dir)) != output_dir:
                return web.Response(status=403)
            output_dir = full_output_dir

        filename = os.path.basename(filename)
        file_path = os.path.join(output_dir, filename)

        if os.path.isfile(file_path):
            try:
                img = Image.open(file_path)
                
                image_format = 'png'
                quality = 90
                
                if 'preview' in request.rel_url.query:
                    preview_info = request.rel_url.query['preview'].split(';')
                    image_format = preview_info[0]
                    if image_format not in ['webp', 'jpeg'] or 'a' in request.rel_url.query.get('channel', ''):
                        image_format = 'webp'
                    if preview_info[-1].isdigit():
                        quality = int(preview_info[-1])
                
                if 'channel' in request.rel_url.query:
                    channel = request.rel_url.query["channel"]
                    if channel == 'rgb':
                        img = img.convert("RGB")
                    elif channel == 'a':
                        if img.mode == "RGBA":
                            _, _, _, a = img.split()
                        else:
                            a = Image.new('L', img.size, 255)
                        img = Image.new('RGBA', img.size)
                        img.putalpha(a)
                
                elif image_format in ['jpeg']:
                    img = img.convert("RGB")

                buffer = io.BytesIO()
                img.save(buffer, format=image_format, quality=quality)
                buffer.seek(0)
                
                return web.Response(body=buffer.read(), content_type=f'image/{image_format}',
                                    headers={"Content-Disposition": f"filename=\"{filename}\""})
            except Exception as e:
                print(f"[Anti-Seek] 处理视图请求出错: {e}")
                pass

    return web.Response(status=404)

def setup_hijack():
    server = PromptServer.instance
    app = server.app
    routes_to_hijack = ["/view", "/api/view"]
    hijacked_info = {}

    for resource in app.router.resources():
        info = resource.get_info()
        path = info.get("path") or info.get("formatter")
        if path in routes_to_hijack:
            for route in resource:
                route._handler = hooked_view_image
                if path not in hijacked_info:
                    hijacked_info[path] = 0
                hijacked_info[path] += 1

    print("[Anti-Seek] 图像加密组件已加载")
    if hijacked_info:
        info_str = ", ".join([f"{k} * {v}" for k, v in hijacked_info.items()])
        print(f"[Anti-Seek] 成功注入端点: {info_str}")
    else:
        print("[Anti-Seek] 警告: 未能注入任何视图端点")

origin_add_routes = PromptServer.add_routes

def new_add_routes(self):
    origin_add_routes(self)
    setup_hijack()

PromptServer.add_routes = new_add_routes

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}