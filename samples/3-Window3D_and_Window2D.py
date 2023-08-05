import harfang as hg
from harfangui import get_assets_path, HarfangUI as hgui
from os import path
import harfang.bin
from shutil import copy

# Build the assets locally

harfang.bin.assetc(path.join(get_assets_path(), 'assets', '-quiet'), 'assets_compiled')

# Init Harfang

hg.InputInit()
hg.WindowSystemInit()

width, height = 1280, 720
window = hg.RenderInit('Harfang GUI - 2D & 3D windows', width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

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

# Setup HarfangUI

hgui.init(["roboto-light.ttf"], [20], width, height)

# Setup inputs

keyboard = hg.Keyboard()
mouse = hg.Mouse()

# main loop

flag_check_box0 = False
flag_check_box1 = False
hgui_state = False

while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(window):
    
    _, width, height = hg.RenderResetToWindow(window, width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

    dt = hg.TickClock()
    keyboard.Update()
    mouse.Update()
    
    # Fps
    if hgui.is_a_window_hovered() | hgui.want_capture_mouse():
        dx, dy, mbt = 0, 0, False
    else:
        dx, dy, mbt = mouse.DtX(), mouse.DtY(), mouse.Down(hg.MB_0)
    
    if hgui.want_capture_keyboard():
        k_up, k_down, k_right, k_left = False, False, False, False
    else:
        k_up, k_down, k_right, k_left = keyboard.Down(hg.K_Up) | keyboard.Down(hg.K_W), keyboard.Down(hg.K_Down) | keyboard.Down(hg.K_S), keyboard.Down(hg.K_Right) | keyboard.Down(hg.K_D), keyboard.Down(hg.K_Left) | keyboard.Down(hg.K_A)

    hg.FpsController(k_up, k_down, k_left, k_right, mbt, dx, dy, cam_pos, cam_rot, 20 if keyboard.Down(hg.K_LShift) else 8, dt)
    camera.GetTransform().SetPos(cam_pos)
    camera.GetTransform().SetRot(cam_rot)

    view_id = 0
    scene.Update(dt)
    view_id, pass_view = hg.SubmitSceneToPipeline(view_id, scene, hg.IntRect(0, 0, width, height), True, pipeline, res)

    if hgui.begin_frame(dt, mouse, keyboard, window, camera):

        if hgui.begin_window("Harfang GUI 3D Window", hg.Vec3(-2, 2.65, 5), hg.Vec3(0, 0, 0), hg.Vec3(500, 300, 0), 10/1280 ):

            hgui.info_text("info1", "Simple Window3D")
            
            f_pressed, f_down = hgui.button("Button 0")
            if f_pressed:
                print("Click btn 0")
            
            _, flag_check_box0 = hgui.check_box("Check box", flag_check_box0)

            hgui.end_window()
        
        if hgui.begin_window_2D("HGUI 2D window",  hg.Vec2(50, 50), hg.Vec2(500, 300), 1 ):

            hgui.info_text("info2", "Window2D with window 3D")
            hgui.same_line()
            hgui.image("img1", "textures/logo.png", hg.Vec2(221, 190))
            
            f_pressed, f_down = hgui.button("Button 1")
            if f_pressed:
                print("Click btn 1")
            
            _, flag_check_box1 = hgui.check_box("Check box 2", flag_check_box1)

            hgui.end_window()

        hgui.end_frame(view_id)

    hg.Frame()
    hg.UpdateWindow(window)

hg.RenderShutdown()
hg.DestroyWindow(window)
