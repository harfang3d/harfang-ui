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
window = hg.RenderInit('Harfang GUI - VR 3D window', width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

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

# Setup HarfangUI

hgui.init(["roboto-light.ttf"], [20], width, height)

# Setup inputs

keyboard = hg.Keyboard()
mouse = hg.Mouse()

# Main loop

flag_check_box0 = False


while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(window): 
	
    _, width, height = hg.RenderResetToWindow(window, width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

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

    if hgui.begin_frame_vr(dt, mouse, keyboard, scene.GetCurrentCamera(), window, vr_state, vr_left_fb, vr_right_fb):
    
        if hgui.begin_window("My window", hg.Vec3(-2, 2.65, 5), hg.Vec3(0, 0, 0), hg.Vec3(500, 300, 0), 10/1280 ):

            hgui.info_text("info1", "Simple Window3D")
            
            f_pressed, f_down = hgui.button("Button 0")
            if f_pressed:
                print("Click btn 0")
            
            _, flag_check_box0 = hgui.check_box("Check box", flag_check_box0)

            hgui.end_window()
        
        hgui.end_frame(view_id)

    hg.Frame()
    hg.OpenVRSubmitFrame(vr_left_fb, vr_right_fb)
    hg.UpdateWindow(window)

hg.RenderShutdown()
hg.DestroyWindow(window)
