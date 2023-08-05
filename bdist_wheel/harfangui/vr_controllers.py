import harfang as hg

class VRControllersHandler:
    
    controllers = None
    connected_controllers = None

    #Idx in connected controllers list:
    controllers_map = []
    lines_program = None

    vtx_layout = None

    line_color_0 = None
    line_color_1 = None

    @classmethod
    def init(cls):
        cls.vtx_layout = hg.VertexLayout()
        cls.vtx_layout.Begin()
        cls.vtx_layout.Add(hg.A_Position, 3, hg.AT_Float)
        cls.vtx_layout.Add(hg.A_Color0, 4, hg.AT_Float)
        cls.vtx_layout.End()
        cls.vtx = hg.Vertices(cls.vtx_layout, 2)
        cls.lines_program = hg.LoadProgramFromAssets('hgui_shaders/hgui_pos_rgb')
        cls.line_color_0 = hg.Color(1, 1, 1, 1)
        cls.line_color_1 = hg.Color(0.5, 1, 1, 1)
        cls.controllers = {}

    @classmethod
    def draw_line(cls,view_id, p0, p1, c0, c1):
        cls.vtx.Begin(0).SetPos(p0).SetColor0(c0).End()
        cls.vtx.Begin(1).SetPos(p1).SetColor0(c1).End()
        hg.DrawLines(view_id, cls.vtx, cls.lines_program)

    @classmethod
    def update_connected_controller(cls):
        # Check if a new controller just came in
        cls.connected_controllers = []

        vr_controller_names = hg.GetVRControllerNames()
        for n in vr_controller_names:
            # Get all possible controllers and add them to the main controller's dict
            if n not in cls.controllers:
                controller = hg.VRController(n)
                cls.controllers[n] = {"input": controller, "world": hg.Mat4()}

            # If the controller is connected, we need to setup it
            controller = cls.controllers[n]["input"]
            controller.Update()
            if controller.IsConnected():
                cls.connected_controllers.append(n)
                cls.controllers[n]["world"] = controller.World()
    
    @classmethod
    def is_controller_connected(cls):
        if len(cls.connected_controllers) > 0:
            return True
        return False

    @classmethod
    def update_displays(cls, views_ids: list ):
        i = 0
        for n in cls.connected_controllers:
            mat = cls.controllers[n]["world"]
            p0 = hg.GetT(mat)
            p1 = p0 + hg.GetZ(mat)
            for vid in views_ids:
                cls.draw_line(vid, p0, p1, cls.line_color_0, cls.line_color_1)
            i += 1
            if i > 1:
                break
                
    

