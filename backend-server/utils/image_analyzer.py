from PIL import Image
import io
import base64

def process_image_with_pil(image_path):
    # 打开图片
    image = Image.open(image_path)
    
    # 调整图片大小（可选，避免图片过大）
    max_size = (1024, 1024)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # 转换为RGB模式（如果需要）
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 保存到字节流并编码
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return base64_image