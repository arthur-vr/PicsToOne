import bpy
import os
import json
import math
import numpy as np
import random
from concurrent.futures import ThreadPoolExecutor
from bpy.props import StringProperty, IntProperty, BoolProperty, IntVectorProperty
from bpy.types import Operator

import sys
import subprocess
import importlib

# Pillowがインストールされているかチェックし、なければインストール
try:
    import PIL
except ImportError:
    # BlenderのPythonパスを指定してPillowをインストール
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    importlib.reload(sys)  # sysモジュールを再読み込み

# Pillowをインポート
from PIL import Image

bl_info = {
    "name": "PicsToOne",
    "blender": (4, 2, 0),
    "category": "Object",
    "description": "Multiple pics to one",
    "author": "Smiley Cat",
    "version": (1, 0, 0),
    "location": "View3D > Object > PicsToOne",
}

PRODUCT_NAME = "PicsToOne"
PRODUCT_SHORT_NAME = "pics_to_one"
AUTHOR = "Smiley Cat"
VERSION_NAME = "apple"
VERSION_STRING = f"1.0.0({VERSION_NAME})"

OPERATORS = {
    "main": {
        "name":f"object.{PRODUCT_SHORT_NAME}_add_custom_property",
        "label":f"{PRODUCT_NAME} v{VERSION_STRING}",
        "description": "Multiple pics to one",
    }
}

SAVE_VARIABLES = {
    "rootDir": {
        "name": "rootDir",
        "default": f"C:/Users/{os.getlogin()}/Downloads",
    },
    "column": {
        "name": "column",
        "default": 6,
    },
    "row": {
        "name": "row",
        "default": 5,
    },
    "outputFilePath": {
        "name": "outputFilePath",
        "default": f"C:/Users/{os.getlogin()}/Downloads/output.png",
    },
    "isShuffle": {
        "name": "isShuffle",
        "default": False,
    },
    "compressionLevel": {
        "name": "compressionLevel",
        "default": 5,
    },
    "outputSizeX": {
        "name": "outputSizeX",
        "default": 1920,
    },
    "outputSizeY": {
        "name": "outputSizeY",
        "default": 1080,
    },
}

class ExternalStorage:
    def __init__(self):
        self.file_path = os.path.join(bpy.utils.user_resource('SCRIPTS'), "addons", f"{PRODUCT_NAME}_settings_{VERSION_STRING}.json")
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return {
            SAVE_VARIABLES["rootDir"]["name"]: SAVE_VARIABLES["rootDir"]["default"],
            SAVE_VARIABLES["column"]["name"]: SAVE_VARIABLES["column"]["default"],
            SAVE_VARIABLES["row"]["name"]: SAVE_VARIABLES["row"]["default"],
            SAVE_VARIABLES["outputFilePath"]["name"]: SAVE_VARIABLES["outputFilePath"]["default"],
            SAVE_VARIABLES["isShuffle"]["name"]: SAVE_VARIABLES["isShuffle"]["default"],
            SAVE_VARIABLES["compressionLevel"]["name"]: SAVE_VARIABLES["compressionLevel"]["default"],
            SAVE_VARIABLES["outputSizeX"]["name"]: SAVE_VARIABLES["outputSizeX"]["default"],
            SAVE_VARIABLES["outputSizeY"]["name"]: SAVE_VARIABLES["outputSizeY"]["default"],
        }

    def save_data(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f)
    
    def save_properties(self, properties):
        for key, value in properties.items():
            self.set(key, value)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save_data()
        
def SEARCH_OBJECT_OT_picsToOne_add_custom_property(self, context):
    self.layout.operator(OBJECT_OT_picsToOne_add_custom_property.bl_idname)

class OBJECT_OT_picsToOne_add_custom_property(Operator):
    bl_idname = OPERATORS["main"]["name"]
    bl_label = OPERATORS["main"]["label"]
    bl_description = OPERATORS["main"]["description"]
    bl_options = {'REGISTER', 'UNDO'}
    storage = ExternalStorage()

    rootDir: StringProperty(name=SAVE_VARIABLES["rootDir"]["name"], maxlen=32767, default=SAVE_VARIABLES["rootDir"]["default"])
    column: IntProperty(name=SAVE_VARIABLES["column"]["name"], default=6)
    row: IntProperty(name=SAVE_VARIABLES["row"]["name"], default=5)
    outputFilePath: StringProperty(name=SAVE_VARIABLES["outputFilePath"]["name"], maxlen=32767, default=SAVE_VARIABLES["outputFilePath"]["default"])
    isShuffle: BoolProperty(name=SAVE_VARIABLES["isShuffle"]["name"], default=SAVE_VARIABLES["isShuffle"]["default"])
    compressionLevel: IntProperty(
        name=SAVE_VARIABLES["compressionLevel"]["name"],
        default=SAVE_VARIABLES["compressionLevel"]["default"],
        min=1,
        max=10,
        description="PNG compression level (1-10, higher = smaller file but slower)"
    )
    outputSizeX: IntProperty(name=SAVE_VARIABLES["outputSizeX"]["name"], default=SAVE_VARIABLES["outputSizeX"]["default"])
    outputSizeY: IntProperty(name=SAVE_VARIABLES["outputSizeY"]["name"], default=SAVE_VARIABLES["outputSizeY"]["default"])
    def draw(self, context):
        layout = self.layout

        layout.prop(self, SAVE_VARIABLES["rootDir"]["name"])
        layout.prop(self, SAVE_VARIABLES["outputFilePath"]["name"])
        layout.prop(self, SAVE_VARIABLES["isShuffle"]["name"])
        row = layout.row()
        row.prop(self, SAVE_VARIABLES["column"]["name"])
        row.prop(self, SAVE_VARIABLES["row"]["name"])
        row.prop(self, SAVE_VARIABLES["compressionLevel"]["name"])
        row.prop(self, SAVE_VARIABLES["outputSizeX"]["name"])
        row.prop(self, SAVE_VARIABLES["outputSizeY"]["name"])

    def invoke(self, context, event):
        window_width = context.window.width
        desired_width = int(window_width * 0.4)  
        self.load_properties()
        return context.window_manager.invoke_props_dialog(self, width=desired_width)
    
    def load_properties(self):
        self.rootDir = self.storage.get(SAVE_VARIABLES["rootDir"]["name"], SAVE_VARIABLES["rootDir"]["default"])
        self.column = self.storage.get(SAVE_VARIABLES["column"]["name"], SAVE_VARIABLES["column"]["default"])
        self.row = self.storage.get(SAVE_VARIABLES["row"]["name"], SAVE_VARIABLES["row"]["default"])
        self.outputFilePath = self.storage.get(SAVE_VARIABLES["outputFilePath"]["name"], SAVE_VARIABLES["outputFilePath"]["default"])
        self.isShuffle = self.storage.get(SAVE_VARIABLES["isShuffle"]["name"], SAVE_VARIABLES["isShuffle"]["default"])
        self.compressionLevel = self.storage.get(SAVE_VARIABLES["compressionLevel"]["name"], SAVE_VARIABLES["compressionLevel"]["default"])
        self.outputSizeX = self.storage.get(SAVE_VARIABLES["outputSizeX"]["name"], SAVE_VARIABLES["outputSizeX"]["default"])
        self.outputSizeY = self.storage.get(SAVE_VARIABLES["outputSizeY"]["name"], SAVE_VARIABLES["outputSizeY"]["default"])
    def execute(self, context):
        self.storage.save_properties({
            "rootDir": self.rootDir,
            "column": self.column,
            "row": self.row,
            "outputFilePath": self.outputFilePath,
            "isShuffle": self.isShuffle,
            "compressionLevel": self.compressionLevel,
            "outputSizeX": self.outputSizeX,
            "outputSizeY": self.outputSizeY,
        })
        rootDir = trim(self.rootDir)
        main(
            self,
            rootDir,
            self.column,
            self.row,
            self.outputFilePath,
            self.isShuffle,
            self.compressionLevel,
            (self.outputSizeX, self.outputSizeY)
        )
        self.report({'INFO'}, f"{PRODUCT_NAME} executed.")
        return {'FINISHED'}

def trim(path):
    path = replaceDoubleQuote(path)
    return path

def replaceDoubleQuote(path):
    return path.replace("\"", "")

def readAllImages(rootDir):
    images = []
    for filename in os.listdir(rootDir):
        filepath = os.path.join(rootDir, filename)
        if os.path.isfile(filepath) and filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
            images.append(filepath)
    return images

def main(self,rootDir, column, row, outputFilePath, isShuffle, compressionLevel, outputSize):
    images = readAllImages(rootDir)
    total = column * row
    if len(images) < total:
        self.report({'ERROR'}, f"The number of images is less than the total number of images required ({total}).")
        return
    if isShuffle:
        random.shuffle(images)
    createIntegratedOneImage(images, column, row, outputFilePath, compressionLevel, outputSize)

def createIntegratedOneImage(images, column, row, outputFilePath, compressionLevel, outputSize):
    size = len(images)
    onePicSize = (int(outputSize[0] / column), int(outputSize[1] / row))
    # Calculate total dimensions based on specified column and row
    total_width = column * onePicSize[0]
    total_height = row * onePicSize[1]
    
    # Create output image
    output_image = np.zeros((total_height, total_width, 4), dtype=np.float32)

    # Process images one by one
    def process_image(i):
        if i >= size:
            return
            
        # Calculate position based on column and row
        x = i % column
        y = math.floor(i / column)
        
        # Skip if position exceeds specified rows
        if y >= row:
            return
            
        try:
            # Load and scale current image
            image = bpy.data.images.load(images[i])
            if image is not None:
                image.scale(onePicSize[0], onePicSize[1])

                # Convert image pixels to numpy array
                pixels = np.array(image.pixels)
                image_np = pixels.reshape(onePicSize[1], onePicSize[0], 4)

                # Copy image to output
                start_y = y * onePicSize[1]
                end_y = (y + 1) * onePicSize[1]
                start_x = x * onePicSize[0]
                end_x = (x + 1) * onePicSize[0]
                output_image[start_y:end_y, start_x:end_x] = image_np

                bpy.data.images.remove(image)

        except Exception as e:
            print(f"Failed to process image {images[i]}: {e}")

    # Use ThreadPoolExecutor to process images in parallel
    with ThreadPoolExecutor() as executor:
        executor.map(process_image, range(column * row))

    # Create PIL image and save with compression
    image_pil = Image.fromarray(np.uint8(np.flipud(output_image) * 255)).convert("RGBA")
    image_pil = image_pil.resize(outputSize, Image.Resampling.LANCZOS)
    output_file_path_base, output_file_path_ext = os.path.splitext(outputFilePath)
    uid = generate_uid()
    final_output_file_path = output_file_path_base + "_" + uid + output_file_path_ext
    while os.path.exists(final_output_file_path):
        uid = generate_uid()
        final_output_file_path = output_file_path_base + "_" + uid + output_file_path_ext
    image_pil.save(final_output_file_path, "PNG", compress_level=compressionLevel)

def generate_uid(length=6):
    characters = 'abcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.choice(characters) for _ in range(length))
    
def register():
    bpy.utils.register_class(OBJECT_OT_picsToOne_add_custom_property)
    bpy.types.VIEW3D_MT_object.append(SEARCH_OBJECT_OT_picsToOne_add_custom_property)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_picsToOne_add_custom_property)
    bpy.types.VIEW3D_MT_object.remove(SEARCH_OBJECT_OT_picsToOne_add_custom_property)

if __name__ == "__main__":
    register()
