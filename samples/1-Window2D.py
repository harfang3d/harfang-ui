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
window = hg.RenderInit('Harfang GUI - 2D window', width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

hg.AddAssetsFolder("assets_compiled")

# Setup HarfangUI

hgui.init(["roboto-light.ttf"], [20], width, height)

# Setup inputs

keyboard = hg.Keyboard()
mouse = hg.Mouse()

flag_check_box0 = False

# Main loop

while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(window): 
	
    _, width, height = hg.RenderResetToWindow(window, width, height, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

    dt = hg.TickClock()
    keyboard.Update()
    mouse.Update()
    view_id = 0
	
    if hgui.begin_frame(dt, mouse, keyboard, window):
        
        if hgui.begin_window_2D("My window",  hg.Vec2(50, 50), hg.Vec2(500, 300), 1):

            hgui.info_text("info1", "Simple Window2D")
            
            f_pressed, f_down = hgui.button("Button")
            if f_pressed:
                print("Click btn")
            
            _, flag_check_box0 = hgui.check_box("Check box", flag_check_box0)

            hgui.end_window()

        hgui.end_frame(view_id)

    hg.Frame()

    hg.UpdateWindow(window)

hg.RenderShutdown()
hg.DestroyWindow(window)
