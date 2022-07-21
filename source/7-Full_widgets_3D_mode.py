import harfang as hg
from harfang_gui import HarfangUI as hgui

# Init Harfang

hg.InputInit()
hg.WindowSystemInit()

width, height = 1280, 720
window = hg.RenderInit('Harfang - GUI', width, height, hg.RF_VSync | hg.RF_MSAA4X)

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

# Setup HarfangGUI

hgui.init(["default.ttf"], [20], width, height)

# Setup inputs

keyboard = hg.Keyboard()
mouse = hg.Mouse()

# Main loop

flag_check_box0 = False
flag_check_box = False
flag_check_box2 = False
flag_check_box3 = False
my_text2 = "Go"
my_text3 = "Hello !"

current_rib = 0

while not hg.ReadKeyboard().Key(hg.K_Escape): 
	
    dt = hg.TickClock()
    dt_f = hg.time_to_sec_f(dt)
    keyboard.Update()
    mouse.Update()
    view_id = 0

    # Fps
    hgui_state = hgui.is_mouse_used() | hgui.is_keyboard_used()
    if not hgui_state:
        hg.FpsController(keyboard, mouse, cam_pos, cam_rot, 20 if keyboard.Down(hg.K_LShift) else 8, dt)
        camera.GetTransform().SetPos(cam_pos)
        camera.GetTransform().SetRot(cam_rot)

    scene.Update(dt)
    view_state = scene.ComputeCurrentCameraViewState(hg.ComputeAspectRatioX(width, height))
    pass_view = hg.SceneForwardPipelinePassViewId()
    view_id, pass_view = hg.PrepareSceneForwardPipelineCommonRenderData(view_id, scene, render_data, pipeline, res, pass_view)
    view_id, pass_view = hg.PrepareSceneForwardPipelineViewDependentRenderData(view_id, view_state, scene, render_data, pipeline, res, pass_view)
    view_id, pass_view = hg.SubmitSceneToForwardPipeline(view_id, scene, hg.IntRect(0, 0, width, height), view_state, pipeline, render_data, res)
	
    if hgui.begin_frame(dt, mouse, keyboard, width, height, camera):

        if hgui.begin_window("my_window", hg.Vec3(-5, 5.65, 10), hg.Vec3(0, 0, 0), hg.Vec3(1280, 720, 0), 20/1280 ):

            if hgui.button("Hello button 0"):
                print("Click btn 0")
            f, d = hgui.check_box("Check test", flag_check_box0)
            if f:
                flag_check_box0 = d

            hgui.info_text("Information text")

            hgui.same_line()

            hgui.image("img1", "textures/logo.png", hg.Vec2(221, 190))

            f, my_text = hgui.input_text("Input text")

            if hgui.button("Hello button 1"):
                print("Click btn 1")
            
            if hgui.button("My button 2"):
                print("click btn 2")
            
            hgui.same_line()
            f, d = hgui.check_box("Check this", flag_check_box)
            if f:
                flag_check_box = d
            
            _, current_rib = hgui.radio_image_button("rib_0","textures/cube_1.png", current_rib, 0, hg.Vec2(64, 64))
            hgui.same_line()
            _, current_rib = hgui.radio_image_button("rib_1","textures/cube_2.png", current_rib, 1)
            hgui.same_line()
            _, current_rib = hgui.radio_image_button("rib_2","textures/cube_3.png", current_rib, 2)
            hgui.same_line()
            _, current_rib = hgui.radio_image_button("rib_3","textures/cube_4.png", current_rib, 3)
    

            hgui.set_cursor_pos(hg.Vec3(500,200,0))
            
            if hgui.button_image("image_1", "textures/logo.png", hg.Vec2(221, 190) / 4):
                print("click image button")
            
            if hgui.begin_window("my_window_2", hg.Vec3(700, 100, -100), hg.Deg3(0, 0, 0), hg.Vec3(400, 600, 0), 1 ):
                if hgui.button("Hello button 3"):
                    print("Click btn 3")
                if hgui.begin_window_2D("my_window_2.1", hg.Vec2(50, 100), hg.Vec2(200, 100), 1 ):
                    f, d = hgui.check_box("Check box 2", flag_check_box2)
                    if f:
                        flag_check_box2 = d
                    f, my_text2 = hgui.input_text("Input text 2", my_text2)
                    if hgui.button("My button 4"):
                        print("click btn 4")
                    hgui.end_window()

                if hgui.begin_window_2D("my_window_2.2", hg.Vec2(70, 130), hg.Vec2(200, 100), 1 ):
                    if hgui.button("My button 5"):
                        print("click btn 5")
                    hgui.end_window()
                
                hgui.end_window()


            hgui.end_window()
            
        if hgui.begin_window_2D("my_window_2D_1", hg.Vec2(10, 10), hg.Vec2(200, 300), 1 ):
            f, d = hgui.check_box("Check box 3", flag_check_box3)
            if f:
                flag_check_box3 = d
            f, my_text3 = hgui.input_text("Input text 3", my_text3)
            if hgui.button("My button 6"):
                print("click btn 6")
            hgui.end_window()
            
        hgui.end_frame(view_id)

    hg.Frame()
    hg.UpdateWindow(window)

hg.RenderShutdown()
hg.DestroyWindow(window)
