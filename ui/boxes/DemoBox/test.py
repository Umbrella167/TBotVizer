import dearpygui.dearpygui as dpg
import numpy as np
from PIL import Image
import os


def load_image(image_path):
    """安全地加载图像"""
    try:
        # 确保图像路径存在
        if not os.path.exists(image_path):
            print(f"图像文件不存在: {image_path}")
            return None
        # 打开图像
        img = Image.open(image_path)
        # 转换为RGBA
        img = img.convert("RGBA")
        # 调整大小
        img = img.resize((800, 600), Image.LANCZOS)
        # 转换为numpy数组
        img_data = np.array(img)
        # 归一化并展平
        texture_data = img_data.flatten() / 255.0
        return texture_data
    except Exception as e:
        print(f"加载图像时出错: {e}")
        return None


def main():
    dpg.create_context()
    # 图像路径 - 请替换为你的实际路径
    image_path = "img.jpg"
    # 加载图像
    texture_data = load_image(image_path)
    if texture_data is None:
        print("无法加载图像")
        return
    try:
        # 创建纹理
        with dpg.texture_registry():
            dpg.add_raw_texture(width=800, height=600, default_value=texture_data, format=dpg.mvFormat_Float_rgba, tag="texture_tag")
        # 创建窗口
        with dpg.window(label="Image Viewer", width=800, height=600):
            dpg.add_image("texture_tag", width=800, height=600)
        # 视口设置
        dpg.create_viewport(title="Image Viewer", width=800, height=600)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
    except Exception as e:
        print(f"DPG操作出错: {e}")
    finally:
        dpg.destroy_context()


if __name__ == "__main__":
    main()
