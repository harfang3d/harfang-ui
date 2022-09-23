import harfang as hg
from harfang_gui import HarfangUI as hgui

# Init Harfang

hg.InputInit()
hg.WindowSystemInit()

width, height = 1280, 720 
window = hg.RenderInit('Harfang - GUI', width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

hg.AddAssetsFolder("assets_compiled")

res = hg.PipelineResources()
pipeline = hg.CreateForwardPipeline()
render_data = hg.SceneForwardPipelineRenderData()

# Setup HarfangGUI

hgui.init(["default.ttf"], [20], width, height)
hgui.set_line_space_size(5)
hgui.set_inner_line_space_size(5)

# Setup inputs

keyboard = hg.Keyboard()
mouse = hg.Mouse()

# Main loop

while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(window): 
	
    _, width, height = hg.RenderResetToWindow(window, width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

    dt = hg.TickClock()
    dt_f = hg.time_to_sec_f(dt)
    keyboard.Update()
    mouse.Update()
    view_id = 0
	
    if hgui.begin_frame(dt, mouse, keyboard, width, height):
        if hgui.begin_window_2D("My window",  hg.Vec2(50, 50), hg.Vec2(1124, 600), 1):
            
            hgui.info_text("info1", "Information text")
            
            f= hgui.button("My_button")
            
            hgui.end_window()
		
        hgui.end_frame(view_id)

    hg.Frame()

    hg.UpdateWindow(window)

hg.RenderShutdown()
hg.DestroyWindow(window)
