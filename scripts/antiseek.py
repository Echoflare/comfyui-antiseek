import os
import json
import io
import hashlib
from PIL import Image, PngImagePlugin
from aiohttp import web
import folder_paths
from .core.core import process_image, get_random_seed, mix_seed, get_image_hash, generate_fake_image

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
config_path = os.path.join(root_dir, "config.json")

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

def get_dir_by_type(dir_type):
    if dir_type is None:
        dir_type = "input"

    if dir_type == "input":
        type_dir = folder_paths.get_input_directory()
    elif dir_type == "temp":
        type_dir = folder_paths.get_temp_directory()
    elif dir_type == "output":
        type_dir = folder_paths.get_output_directory()
    else:
        type_dir = folder_paths.get_input_directory()

    return type_dir, dir_type

def compare_image_hash(filepath, image):
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        img_pos = image.file.tell()
        image.file.seek(0)
        upload_hash = hashlib.sha256(image.file.read()).hexdigest()
        image.file.seek(img_pos)
        
        return file_hash == upload_hash
    return False

async def hooked_upload_image(request):
    post = await request.post()
    image = post.get("image")
    overwrite = post.get("overwrite")
    image_is_duplicate = False

    image_upload_type = post.get("type")
    upload_dir, image_upload_type = get_dir_by_type(image_upload_type)

    if image and image.file:
        filename = image.filename
        if not filename:
            return web.Response(status=400)

        subfolder = post.get("subfolder", "")
        full_output_folder = os.path.join(upload_dir, os.path.normpath(subfolder))
        filepath = os.path.abspath(os.path.join(full_output_folder, filename))

        if os.path.commonpath((upload_dir, filepath)) != upload_dir:
            return web.Response(status=400)

        if not os.path.exists(full_output_folder):
            os.makedirs(full_output_folder)

        split = os.path.splitext(filename)

        if overwrite is not None and (overwrite == "true" or overwrite == "1"):
            pass
        else:
            i = 1
            while os.path.exists(filepath):
                if compare_image_hash(filepath, image):
                    image_is_duplicate = True
                    break
                filename = f"{split[0]} ({i}){split[1]}"
                filepath = os.path.join(full_output_folder, filename)
                i += 1

        if not image_is_duplicate:
            try:
                img = Image.open(image.file)
                img.save(filepath)
            except Exception as e:
                print(f"[Anti-Seek] 上传处理失败: {e}")
                with open(filepath, "wb") as f:
                    image.file.seek(0)
                    f.write(image.file.read())

        return web.json_response({"name" : filename, "subfolder": subfolder, "type": image_upload_type})
    else:
        return web.Response(status=400)

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

async def get_config(request):
    return web.json_response(config)

async def update_config(request):
    try:
        data = await request.json()
        config.update(data)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return web.json_response({"status": "success"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

def setup_routes(app):
    routes_to_hijack = {
        "/view": hooked_view_image,
        "/api/view": hooked_view_image,
        "/upload/image": hooked_upload_image,
        "/api/upload/image": hooked_upload_image
    }
    
    hijacked_list = set()

    for resource in app.router.resources():
        info = resource.get_info()
        path = info.get("path") or info.get("formatter")
        if path in routes_to_hijack:
            for route in resource:
                route._handler = routes_to_hijack[path]
                hijacked_list.add(path)
    
    app.router.add_get("/antiseek/config", get_config)
    app.router.add_post("/antiseek/config", update_config)
    
    return hijacked_list