# Scene using the PBR shader

import harfang as hg
from harfang_gui import HarfangUI as hgui

hg.InputInit()
hg.WindowSystemInit()

width, height = 1280, 720
win = hg.RenderInit('Harfang GUI - 3D window', width, height, hg.RF_VSync | hg.RF_MSAA4X)

#
pipeline = hg.CreateForwardPipeline()
res = hg.PipelineResources()

hg.AddAssetsFolder("assets_compiled")

# load scene
scene = hg.Scene()
hg.LoadSceneFromAssets("playground/playground.scn", scene, res, hg.GetForwardPipelineInfo())
camera = scene.GetNode("Camera")
cam_pos = hg.Vec3(0, 1, -2)
cam_rot = hg.Deg3(-7, 0, 0)

# Setup HarfangGUI

hgui.init(["default.ttf"], [20], width, height)

# Setup inputs

keyboard = hg.Keyboard()
mouse = hg.Mouse()

# main loop

flag_check_box0 = False

while not hg.ReadKeyboard().Key(hg.K_Escape):
    
    dt = hg.TickClock()
    keyboard.Update()
    mouse.Update()
    
    # Fps
    hgui_state = hgui.is_mouse_used() | hgui.is_keyboard_used()
    if not hgui_state:
        hg.FpsController(keyboard, mouse, cam_pos, cam_rot, 20 if keyboard.Down(hg.K_LShift) else 8, dt)
        camera.GetTransform().SetPos(cam_pos)
        camera.GetTransform().SetRot(cam_rot)

    view_id = 0
    scene.Update(dt)
    view_id, pass_view = hg.SubmitSceneToPipeline(view_id, scene, hg.IntRect(0, 0, width, height), True, pipeline, res)

    if hgui.begin_frame(dt, mouse, keyboard, width, height, camera):
            
        if hgui.begin_window("my_window", hg.Vec3(-2, 2.65, 5), hg.Vec3(0, 0, 0), hg.Vec3(500, 300, 0), 10/1280 ):

            hgui.info_text("Simple Window3D")
            
            if hgui.button("Button 0"):
                print("Click btn 0")
            
            _, flag_check_box0 = hgui.check_box("Check box", flag_check_box0)

            hgui.end_window()

        hgui.end_frame(view_id)

    hg.Frame()
    hg.UpdateWindow(win)

hg.RenderShutdown()
hg.DestroyWindow(win)
