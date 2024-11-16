import math
import numpy as np
import pygfx as gfx
import dearpygui.dearpygui as dpg
import pylinalg as la
import imageio.v3 as iio
from wgpu.gui.offscreen import WgpuCanvas
class World:
    def __init__(self):
        self.world = gfx.Group()
    def add_plane(self,width=10,height=10,position=(0,0,0),rotation=(0,0,0),flat_shading=True,color=(1,1,1,1)):
        plane = gfx.Mesh(
                gfx.plane_geometry(width, height),
                gfx.MeshBasicMaterial(color=color, flat_shading=flat_shading),
            )
        self.world.add(plane)
        return plane
    def add_object(self,obj:gfx.Mesh):
        self.world.add(obj)
class Scene:
    def __init__(self):
        pass
    def add(self):
        pass
class Camera():
    def __init__(self):
        pass
class GfxEngine:
    def __init__(self,size=(800,600),pixel_ratio=1,max_fps=999):
        self.canvas = WgpuCanvas(
            size=size,
            pixel_ratio=pixel_ratio,
            max_fps=max_fps,
        )
        self.renderer = gfx.renderers.WgpuRenderer(self.canvas)

    def draw(self,scene,camera):
        self.canvas.request_draw(lambda:self.renderer.render(scene,camera))


if __name__ == "__main__":
    pass
    # path = ''
    # engine = GfxEngine()
    # new_sence = engine.add_sence()
    # camera = engine.camera.create()
    # arm_model = engine.load_urdf(path)
    # new_sence.append(arm_model)
    # camera.position = (x,y,z)
    # camera.rotation = 
    # engine.draw(new_sence,camera)
