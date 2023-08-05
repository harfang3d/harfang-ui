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
window = hg.RenderInit('Harfang - GUI', width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

hg.AddAssetsFolder("assets_compiled")

res = hg.PipelineResources()
pipeline = hg.CreateForwardPipeline()
render_data = hg.SceneForwardPipelineRenderData()

# Setup HarfangUI

hgui.init(["roboto-light.ttf"], [20], width, height)
hgui.set_line_space_size(5)
hgui.set_inner_line_space_size(5)

# Setup inputs

keyboard = hg.Keyboard()
mouse = hg.Mouse()

# Main loop

flag_check_box0 = False
flag_check_box = False
flag_check_box2 = False
flag_check_box31 = True
my_text = "my text"
my_text2 = "Go"
my_text31 = "Hello"
current_rib = 0
toggle_idx = 0

while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(window): 
	
	_, width, height = hg.RenderResetToWindow(window, width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)
	
	dt = hg.TickClock()
	dt_f = hg.time_to_sec_f(dt)
	keyboard.Update()
	mouse.Update()
	view_id = 0
	
	if hgui.begin_frame(dt, mouse, keyboard, window):

		if hgui.begin_window_2D("My window",  hg.Vec2(50, 50), hg.Vec2(1124, 600), 1):

			hgui.set_line_space_size(10)

			f_pressed, f_down = hgui.button("Hello button 0")
			if f_pressed:
				print("Click btn 0")
			f, d = hgui.check_box("Check test", flag_check_box0)
			if f:
				flag_check_box0 = d

			hgui.info_text("info1", "Information text")

			hgui.same_line()

			hgui.image("img1", "textures/logo.png", hg.Vec2(221/2, 190/2))

			f, my_text = hgui.input_text("Input text", my_text)

			hgui.set_inner_line_space_size(1)
			hgui.set_line_space_size(1)

			if hgui.button("Hello button 1", align = hgui.HGUIAF_BOTTOMRIGHT )[0]:
				print("Click btn 1")
			hgui.same_line()
			if hgui.button("Hello button 2", align = hgui.HGUIAF_BOTTOM)[0]:
				print("Click btn 2")
			hgui.same_line()
			if hgui.button("Hello button 22", align = hgui.HGUIAF_BOTTOMLEFT)[0]:
				print("Click btn 22")

			if hgui.button("Hello button 3", align = hgui.HGUIAF_TOPRIGHT)[0]:
				print("Click btn 3")
			hgui.same_line()
			if hgui.button("Hello button 4", align = hgui.HGUIAF_TOP)[0]:
				print("Click btn 4")
			hgui.same_line()
			
			hgui.set_inner_line_space_size(10)
			hgui.set_line_space_size(20)

			if hgui.button("Hello button 23", align = hgui.HGUIAF_TOPLEFT)[0]:
				print("Click btn 23")
			
			_, current_rib = hgui.radio_image_button("rib_0","textures/cube_1.png", current_rib, 0, hg.Vec2(64, 64))
			hgui.same_line()
			_, current_rib = hgui.radio_image_button("rib_1","textures/cube_2.png", current_rib, 1)
			hgui.same_line()
			_, current_rib = hgui.radio_image_button("rib_2","textures/cube_3.png", current_rib, 2)
			hgui.same_line()
			_, current_rib = hgui.radio_image_button("rib_3","textures/cube_4.png", current_rib, 3)
			
			f, toggle_idx = hgui.toggle_image_button("arrows", ["textures/Button_Arrow_L.png", "textures/Button_Arrow_R.png"], toggle_idx, hg.Vec2(50, 50))
			if f:
				print(str(toggle_idx))


			hgui.set_cursor_pos(hg.Vec3(400,200,0))
			
			if hgui.button_image("image_1", "textures/logo.png", hg.Vec2(221, 190) / 6, show_label = True)[0]:
				print("click image button")
			
			if hgui.begin_window_2D("my_window_2", hg.Vec2(650, 100), hg.Vec2(400, 400), 1, hgui.HGUIWF_NoPointerMove ):
				if hgui.button("Hello button 5")[0]:
					print("Click btn 5")
				if hgui.begin_window_2D("my_window_2.1", hg.Vec2(50, 100), hg.Vec2(200, 200), 1 ):
					f, d = hgui.check_box("Check box 2", flag_check_box2)
					if f:
						flag_check_box2 = d
					f, my_text2 = hgui.input_text("Input text 2", my_text2)
					if hgui.button("My button 6")[0]:
						print("click btn 6")
					hgui.end_window()

				if hgui.begin_window_2D("my_window_2.2", hg.Vec2(70, 130), hg.Vec2(200, 100), 1, hgui.HGUIWF_HideTitle ):
					if hgui.button("My button 7")[0]:
						print("click btn 7")
					hgui.end_window()

				hgui.end_window()
			
			if hgui.begin_window_2D("my_window_3", hg.Vec2(670, 120), hg.Vec2(400, 400), 1 ):
				if hgui.button("Hello button 3.1")[0]:
					print("Click btn 3.1")
				
				
				if hgui.begin_window_2D("my_window_3.1", hg.Vec2(-50, 100), hg.Vec2(200, 100), 1, hgui.HGUIWF_HideTitle ):
					f, d = hgui.check_box("Check box 3.1", flag_check_box31)
					if f:
						flag_check_box31 = d
					f, my_text31 = hgui.input_text("Input text 3.1", my_text31)
					if hgui.button("My button 3.2")[0]:
						print("click btn 3.2")
					hgui.end_window()
				

				if hgui.begin_window_2D("my_window_3.2", hg.Vec2(70, 130), hg.Vec2(200, 100), 1):
					if hgui.button("My button 3.3")[0]:
						print("click btn 3.3")
					hgui.end_window()

				hgui.end_window()

			hgui.end_window()
	
		hgui.end_frame(view_id)

	hg.Frame()

	hg.UpdateWindow(window)

hg.RenderShutdown()
hg.DestroyWindow(window)
