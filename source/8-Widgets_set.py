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

cb = True
it = "input text"
current_rib = 0

while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(window): 
	
    _, width, height = hg.RenderResetToWindow(window, width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

    dt = hg.TickClock()
    dt_f = hg.time_to_sec_f(dt)
    keyboard.Update()
    mouse.Update()
    view_id = 0
	
    if hgui.begin_frame(dt, mouse, keyboard, width, height):
        if hgui.begin_window_2D("My window",  hg.Vec2(50, 50), hg.Vec2(1124, 600), 1, hgui.HGUIWF_HideTitle | hgui.HGUIWF_Invisible):
            
            hgui.set_inner_line_space_size(200)

            hgui.info_text("info1", "Information text")

            
            hgui.image("my image1", "textures/logo.png", hg.Vec2(90,80))
            
            hgui.same_line()
            hgui.image("Info image label", "textures/logo.png", hg.Vec2(90,80), show_label=True)
            
            f,it = hgui.input_text("Input text",it, show_label=False)
            
            
            hgui.same_line()
            f,it = hgui.input_text("Input text label",it)

            f = hgui.button("Button")
            f = hgui.button_image("Button image", "textures/coffee.png", hg.Vec2(20,20))
            hgui.same_line()
            f = hgui.button_image("label##button_image", "textures/coffee.png", hg.Vec2(20,20), show_label=True)
        
            
            """
            if hgui.button("My_button"):
                print("button")
            
            hgui.image("my image", "textures/logo.png", hg.Vec2(80,80))
            f,cb = hgui.check_box("my checkbox",cb)
            f,it = hgui.input_text("my input text",it)
            
            _, current_rib = hgui.radio_image_button("rib_0","textures/cube_1.png", current_rib, 0, hg.Vec2(64, 64))
            hgui.same_line()
            _, current_rib = hgui.radio_image_button("rib_1","textures/cube_2.png", current_rib, 1)
            hgui.same_line()
            _, current_rib = hgui.radio_image_button("rib_2","textures/cube_3.png", current_rib, 2)
            hgui.same_line()
            _, current_rib = hgui.radio_image_button("rib_3","textures/cube_4.png", current_rib, 3)
            """
            
            hgui.end_window()
		
        hgui.end_frame(view_id)

    hg.Frame()

    hg.UpdateWindow(window)

hg.RenderShutdown()
hg.DestroyWindow(window)
