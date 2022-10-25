import harfang as hg
from harfang_gui import HarfangUI as hgui

# Init Harfang

hg.InputInit()
hg.WindowSystemInit()

width, height = 1920, 1080 
window = hg.RenderInit('Harfang - GUI', width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

hg.AddAssetsFolder("assets_compiled")

res = hg.PipelineResources()
pipeline = hg.CreateForwardPipeline()
render_data = hg.SceneForwardPipelineRenderData()

# Setup HarfangGUI

hgui.init(["default.ttf"], [20], width, height)
hgui.set_line_space_size(5)
hgui.set_inner_line_space_size(5)


imgui_prg = hg.LoadProgramFromAssets('core/shader/imgui')
imgui_img_prg = hg.LoadProgramFromAssets('core/shader/imgui_image')

hg.ImGuiInit(10, imgui_prg, imgui_img_prg)

# Setup inputs

keyboard = hg.Keyboard()
mouse = hg.Mouse()

# Main loop

cb = True
it = "input text"
current_rib = 0
toggle_image_idx = 0
toggle_btn_idx = 0
current_item = 0
items_list = ["Item 0", "Item 1", "Item 2sdfzrzerzrzrzerzrzerz", "Item 3"]
slider_float_value = 0

while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(window): 
	
    _, width, height = hg.RenderResetToWindow(window, width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)
    dt = hg.TickClock()
    dt_f = hg.time_to_sec_f(dt)
    keyboard.Update()
    mouse.Update()
    view_id = 0
    
    
    if hgui.begin_frame(dt, mouse, keyboard, window):
        if hgui.begin_window_2D("My window",  hg.Vec2(50, 50), hg.Vec2(1500, 1000), 1): #, hgui.HGUIWF_HideTitle | hgui.HGUIWF_Invisible):
            

            hgui.set_inner_line_space_size(200)

            
            hgui.info_text("info1", "Information text")

            
            hgui.image("my image1", "textures/logo.png", hg.Vec2(90,80))
            
            
            hgui.same_line()
            hgui.image("Info image label", "textures/logo.png", hg.Vec2(90,80), show_label=True)
            
            
            f,it = hgui.input_text("Input text",it, show_label=False, forced_text_width = 150)
            
            hgui.same_line()
            f,it = hgui.input_text("Input text label",it)

            f_pressed, f_down = hgui.button("Button")
            
            f_pressed, f_down = hgui.button_image("Button image", "textures/coffee.png", hg.Vec2(20,20))
            
            hgui.same_line()
            f_pressed, f_down = hgui.button_image("label##button_image", "textures/coffee.png", hg.Vec2(20,20), show_label=True)
            
            f, cb = hgui.check_box("Checkbox", cb, show_label=False)
            hgui.same_line()
            
            f,cb = hgui.check_box("Checkbox##label", cb)
            
            
            tex_list = ["hgui_textures/Icon_Pause.png", "hgui_textures/Icon_Play.png"]
            f, toggle_image_idx = hgui.toggle_image_button("Toggle", tex_list, toggle_image_idx, hg.Vec2(15, 15))
            
            hgui.same_line()
            f, toggle_image_idx = hgui.toggle_image_button("Toggle##label", tex_list, toggle_image_idx, hg.Vec2(15, 15), show_label=True)
            

            lbl_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            f, toggle_btn_idx = hgui.toggle_button("Texts_toggle", lbl_list, toggle_btn_idx)
            hgui.same_line()
            f, toggle_btn_idx = hgui.toggle_button("Texts_toggle##label", lbl_list, toggle_btn_idx, show_label=True)

            #f, cb = hgui.text_select("txt_select", "Item 0", cb)
            
            f, current_item = hgui.list_box("My listbox", current_item, items_list, show_label = False)
            hgui.same_line()
            f, current_item = hgui.list_box("My listbox##2", current_item, items_list)
            
            #f, current_item = hgui.dropdown("Dropdown", current_item, ["Item 0", "Item 1", "Item 2", "Item 3"])
            

            if hgui.begin_widget_group_2D("Select texture"): #, cpos, hg.Vec2(373, 190)):
                hgui.set_inner_line_space_size(25)

                _, current_rib = hgui.radio_image_button("rib_0","textures/cube_1.png", current_rib, 0, hg.Vec2(64, 64))
                hgui.same_line()
                _, current_rib = hgui.radio_image_button("rib_1","textures/cube_2.png", current_rib, 1)
                hgui.same_line()
                _, current_rib = hgui.radio_image_button("rib_2","textures/cube_3.png", current_rib, 2)
                hgui.same_line()
                _, current_rib = hgui.radio_image_button("rib_3","textures/cube_4.png", current_rib, 3)
                hgui.end_widget_group()
            hgui.set_inner_line_space_size(200)
            
            f, slider_float_value = hgui.slider_float("horizontal slider float##1", 0, 3, slider_float_value, show_label = False)
            hgui.same_line()
            f, slider_float_value = hgui.slider_float("horizontal slider float##2", 0, 3, slider_float_value)
            
            f, slider_float_value = hgui.slider_float("vertical slider float##1", 0, 3, slider_float_value, show_label = False, flag_horizontal = False )
            hgui.same_line()
            f, slider_float_value = hgui.slider_float("vertical slider float##2", 0, 3, slider_float_value, flag_horizontal = False )
            
            
            hgui.info_text("Slider value", "%.2f" % slider_float_value)
            
            hgui.end_window()
        
        view_id = hgui.end_frame(view_id)
    
    
    hg.SetView2D(view_id, 0, 0, width, height, -1, 1, hg.CF_Depth, hg.Color.Black, 1, 0)
    
    hg.ImGuiBeginFrame(width, height, hg.TickClock(), hg.ReadMouse(), hg.ReadKeyboard())
    
    if hg.ImGuiBegin('Window'):
        _, current_item = hg.ImGuiCombo("ComboBox", current_item, items_list)
        _, slider_float_value = hg.ImGuiSliderFloat("Slider float", slider_float_value, 0, 3, "%.1f")

    hg.ImGuiEnd()
    
    hg.ImGuiEndFrame(view_id)
    hg.Frame()

    hg.UpdateWindow(window)

hg.RenderShutdown()
hg.DestroyWindow(window)
