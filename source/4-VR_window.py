import harfang as hg
from harfang_gui import HarfangUI as hgui

# Init Harfang

hg.InputInit()
hg.WindowSystemInit()

width, height = 1280, 720
window = hg.RenderInit('Harfang GUI - VR 3D window', width, height, hg.RF_VSync | hg.RF_MSAA4X)

hg.AddAssetsFolder("assets_compiled")

res = hg.PipelineResources()
pipeline = hg.CreateForwardPipeline()
render_data = hg.SceneForwardPipelineRenderData()

# Setup VR

ground_vr_mat = hg.TransformationMat4(hg.Vec3(0, 0.5, 2), hg.Deg3(0, 0, 0))

if not hg.OpenVRInit():
    hg.Error("Can't open OpenVR")
else:
    vr_left_fb = hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)
    vr_right_fb = hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)

# Setup 3D Scene

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

    vr_state = hg.OpenVRGetState(ground_vr_mat, 0.01, 1000)
    left, right = hg.OpenVRStateToViewState(vr_state)
    vr_eye_rect = hg.IntRect(0, 0, vr_state.width, vr_state.height)

    # Prepare the left eye render data then draw to its framebuffer
    view_id, pass_view = hg.PrepareSceneForwardPipelineViewDependentRenderData(view_id, left, scene, render_data, pipeline, res, pass_view)
    view_id, pass_view = hg.SubmitSceneToForwardPipeline(view_id, scene, vr_eye_rect, left, pipeline, render_data, res, vr_left_fb.GetHandle())
    
    # Prepare the right eye render data then draw to its framebuffer
    view_id, pass_view = hg.PrepareSceneForwardPipelineViewDependentRenderData(view_id, right, scene, render_data, pipeline, res, pass_view)
    view_id, pass_view = hg.SubmitSceneToForwardPipeline(view_id, scene, vr_eye_rect, right, pipeline, render_data, res, vr_right_fb.GetHandle())

    # Main screen
    view_id, pass_view = hg.PrepareSceneForwardPipelineViewDependentRenderData(view_id, view_state, scene, render_data, pipeline, res, pass_view)
    view_id, pass_view = hg.SubmitSceneToForwardPipeline(view_id, scene, hg.IntRect(0, 0, width, height), view_state, pipeline, render_data, res)

    if hgui.begin_frame_vr(dt, mouse, keyboard, scene.GetCurrentCamera(), width, height, vr_state, vr_left_fb, vr_right_fb):
    
        if hgui.begin_window("My window", hg.Vec3(-2, 2.65, 5), hg.Vec3(0, 0, 0), hg.Vec3(500, 300, 0), 10/1280 ):

            hgui.info_text("info1", "Simple Window3D")
            
            if hgui.button("Button 0"):
                print("Click btn 0")
            
            _, flag_check_box0 = hgui.check_box("Check box", flag_check_box0)

            hgui.end_window()
        
        hgui.end_frame(view_id)

    hg.Frame()
    hg.OpenVRSubmitFrame(vr_left_fb, vr_right_fb)
    hg.UpdateWindow(window)

hg.RenderShutdown()
hg.DestroyWindow(window)
