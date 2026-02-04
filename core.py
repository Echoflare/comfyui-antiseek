import numpy as np
from PIL import Image, ImageDraw
import hashlib
import random

def get_random_seed():
    return int(np.random.randint(0, 4294967295, dtype=np.uint32))

def mix_seed(seed, salt):
    if not salt:
        return seed
    payload = f"{seed}{salt}"
    h = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    return int(h[:8], 16)

def get_image_hash(image):
    return hashlib.md5(image.tobytes()).hexdigest()

def process_image(image, seed):
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        img_array = np.array(image)
        rng = np.random.default_rng(seed)
        noise = rng.integers(0, 256, img_array.shape, dtype=np.uint8)
        processed_array = np.bitwise_xor(img_array, noise)
        return Image.fromarray(processed_array)
    except Exception:
        return image

def generate_fake_image(width, height):
    bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img, 'RGBA')
    
    for _ in range(random.randint(20, 50)):
        shape_type = random.choice(['rect', 'ellipse', 'polygon'])
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(100, 255))
        
        if shape_type == 'rect':
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = random.randint(0, width), random.randint(0, height)
            draw.rectangle([min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2)], fill=color)
        elif shape_type == 'ellipse':
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = random.randint(0, width), random.randint(0, height)
            draw.ellipse([min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2)], fill=color)
        elif shape_type == 'polygon':
            points = [(random.randint(0, width), random.randint(0, height)) for _ in range(random.randint(3, 6))]
            draw.polygon(points, fill=color)
            
    return img