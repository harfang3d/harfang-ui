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

width, height = 1600, 900
window = hg.RenderInit('Harfang - GUI', width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

hg.AddAssetsFolder("assets_compiled")

res = hg.PipelineResources()
pipeline = hg.CreateForwardPipeline()
render_data = hg.SceneForwardPipelineRenderData()

# Setup 3D Scene:

scene = hg.Scene()
hg.LoadSceneFromAssets('playground/playground.scn', scene, res, hg.GetForwardPipelineInfo())

camera = scene.GetNode("Camera")
cam_pos = hg.Vec3(0, 1, -2)
cam_rot = hg.Deg3(-7, 0, 0)

# Setup HarfangUI

hgui.init(["roboto-light.ttf"], [20], width, height)

# Setup inputs

keyboard = hg.Keyboard()
mouse = hg.Mouse()

# Main loop

flag_check_box0 = False
flag_check_box = False
flag_check_box2 = False
flag_check_box3 = False
flag_check_box31 = False
my_text = "Hello world"
my_text2 = "Go"
my_text3 = "Hello !"
my_text4 = "World"
my_text31 = "HarfangUI"

current_rib = 0
toggle_btn_idx = 0
toggle_image_idx = 0

while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(window): 
	
    #_, width, height = hg.RenderResetToWindow(window, width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

    dt = hg.TickClock()
    dt_f = hg.time_to_sec_f(dt)
    keyboard.Update()
    mouse.Update()
    view_id = 0

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

    scene.Update(dt)
    view_state = scene.ComputeCurrentCameraViewState(hg.ComputeAspectRatioX(width, height))
    pass_view = hg.SceneForwardPipelinePassViewId()
    view_id, pass_view = hg.PrepareSceneForwardPipelineCommonRenderData(view_id, scene, render_data, pipeline, res, pass_view)
    view_id, pass_view = hg.PrepareSceneForwardPipelineViewDependentRenderData(view_id, view_state, scene, render_data, pipeline, res, pass_view)
    view_id, pass_view = hg.SubmitSceneToForwardPipeline(view_id, scene, hg.IntRect(0, 0, width, height), view_state, pipeline, render_data, res)
	
    if hgui.begin_frame(dt, mouse, keyboard, window, camera):

        if hgui.begin_window("my_window", hg.Vec3(-5, 5.65, 10), hg.Vec3(0, 0, 0), hg.Vec3(1280, 720, 0), 10/1280,0):
            
            hgui.set_line_space_size(10)

            if hgui.button("Hello button 0")[0]:
                print("Click btn 0")
            f, d = hgui.check_box("Check test", flag_check_box0)
            if f:
                flag_check_box0 = d

            hgui.info_text("info1", "Information text")

            hgui.same_line()

            hgui.image("img1", "textures/logo.png", hg.Vec2(221, 190))

            f, my_text = hgui.input_text("Input text",my_text, stacking = hgui.HGUI_STACK_VERTICAL, align = hgui.HGUIAF_LEFT, components_order = hgui.HGUI_ORDER_DEFAULT)
            hgui.same_line()

            f, my_text2 = hgui.input_text("Input text 2 ",my_text2, show_label = False)

            if hgui.button("Hello button 1")[0]:
                print("Click btn 1")
            
            if hgui.button("My button 2")[0]:
                print("click btn 2")
            
            hgui.same_line()
            f, d = hgui.check_box("Check this", flag_check_box, show_label = False)
            if f:
                flag_check_box = d
            
            if hgui.begin_widget_group_2D("Select texture"): #, cpos, hg.Vec2(373, 190)):
                #hgui.set_inner_line_space_size(10)

                _, current_rib = hgui.radio_image_button("rib_0","textures/cube_1.png", current_rib, 0, hg.Vec2(64, 64))
                hgui.same_line()
                _, current_rib = hgui.radio_image_button("rib_1","textures/cube_2.png", current_rib, 1)
                hgui.same_line()
                _, current_rib = hgui.radio_image_button("rib_2","textures/cube_3.png", current_rib, 2)
                hgui.same_line()
                _, current_rib = hgui.radio_image_button("rib_3","textures/cube_4.png", current_rib, 3)
                hgui.end_widget_group()
    
            lbl_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            f, toggle_btn_idx = hgui.toggle_button("Texts_toggle", lbl_list, toggle_btn_idx)
            if f:
                print(str(toggle_btn_idx))

            tex_list = ["textures/Button_Arrow_L.png", "textures/Button_Arrow_R.png"]
            f, toggle_image_idx = hgui.toggle_image_button("arrows", tex_list, toggle_image_idx, hg.Vec2(50, 50))
            if f:
                print(str(toggle_image_idx))

            hgui.set_cursor_pos(hg.Vec3(500,200,0))
            
            if hgui.button_image("image_1", "textures/logo.png", hg.Vec2(221, 190) / 4, show_label = True, stacking = hgui.HGUI_STACK_HORIZONTAL, align = hgui.HGUIAF_CENTER, components_order = hgui.HGUI_ORDER_REVERSE)[0]:
                print("click image button")
            
            hgui.same_line()

            if hgui.button("Test cursor")[0]:
                print("Test cursor")
            
            if hgui.begin_window("my_window_2", hg.Vec3(700, 100, -100), hg.Deg3(0, 0, 0), hg.Vec3(400, 600, 0), 1, hgui.HGUIWF_Overlay):
                hgui.info_text("info_win_2", "This window is in OVERLAY mode")
                if hgui.button("Hello button 3")[0]:
                    print("Click btn 3")
                if hgui.begin_window_2D("my_window_2.1", hg.Vec2(50, 100), hg.Vec2(200, 100), 1 ):
                    f, d = hgui.check_box("Check box 2", flag_check_box2)
                    if f:
                        flag_check_box2 = d
                    f, my_text3 = hgui.input_text("Input text 3", my_text3)
                    if hgui.button("My button 4")[0]:
                        print("click btn 4")
                    hgui.end_window()

                if hgui.begin_window_2D("my_window_2.2", hg.Vec2(70, 130), hg.Vec2(200, 100), 1 ):
                    if hgui.button("My button 5")[0]:
                        print("click btn 5")
                    hgui.end_window()
                
                hgui.end_window()

            if hgui.begin_window_2D("my_window_3.1", hg.Vec2(500, 100), hg.Vec2(200, 100), 1 ):
                f, d = hgui.check_box("Check box 3.1", flag_check_box31)
                if f:
                    flag_check_box31 = d
                f, my_text31 = hgui.input_text("Input text 3.1", my_text31)
                if hgui.button("My button 3.2")[0]:
                    print("click btn 3.2")
                hgui.end_window()

            hgui.end_window()
            
        if hgui.begin_window_2D("my_window_2D_1", hg.Vec2(10, 10), hg.Vec2(200, 300), 1 ):
            hgui.set_line_space_size(20)
            f, d = hgui.check_box("Check box 3", flag_check_box3, stacking = hgui.HGUI_STACK_HORIZONTAL, align = hgui.HGUIAF_CENTER)
            if f:
                flag_check_box3 = d
            f, my_text4 = hgui.input_text("Input text 4", my_text4)
            if hgui.button("My button 6")[0]:
                print("click btn 6")
            hgui.end_window()
            
        hgui.end_frame(view_id)

    hg.Frame()
    hg.UpdateWindow(window)

hg.RenderShutdown()
hg.DestroyWindow(window)
