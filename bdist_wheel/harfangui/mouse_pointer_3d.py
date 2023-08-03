import harfang as hg
from math import tan, pi

class MousePointer3D:
    vtx_layout = None
    vtx = None
    shader_texture = None
    uniforms_values_list = None
    uniforms_textures_list = None
    pointer_texture = None
    pointer_ti = None
    mouse_pointer_size = 10 # Height in pixels
    mouse_pointer_default_distance = 2
    mouse_pointer_distance = 2 # distance from camera
    pointer_center = None #position in pointer texture, pixels (origine on left top corner)

    pixel_size = 0
    pointer_world_matrix = None

    mouse_vr_pos = None
    flag_update_vr_head_offset = True
    vr_head_offset = None

    @classmethod
    def init(cls):
        cls.vtx_layout = hg.VertexLayout()
        cls.vtx_layout.Begin()
        cls.vtx_layout.Add(hg.A_Position, 3, hg.AT_Float)
        cls.vtx_layout.Add(hg.A_Color0, 4, hg.AT_Float)
        cls.vtx_layout.Add(hg.A_TexCoord0, 3, hg.AT_Float)
        cls.vtx_layout.End()

        cls.vtx = hg.Vertices(cls.vtx_layout, 256)

        cls.shader_texture = hg.LoadProgramFromAssets('hgui_shaders/hgui_texture')

        cls.uniforms_values_list = hg.UniformSetValueList()
        cls.uniforms_textures_list = hg.UniformSetTextureList()

        cls.pointer_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_LessEqual, hg.FC_Disabled, False)

        cls.pointer_texture, cls.pointer_ti = hg.LoadTextureFromAssets("hgui_textures/mouse_pointer.png", 0)
        cls.mouse_pointer_size = 20
        cls.mouse_pointer_distance = 2
        cls.mouse_pointer_default_distance = 2
        cls.pointer_center = hg.Vec2(1, 1)

        cls.mouse_vr_pos = hg.Vec2(0, 0)

    @classmethod
    def update_vr(cls, vr_state: hg.OpenVRState, mouse: hg.Mouse, mouse_pointer_intersection = None):

        dx, dy = mouse.DtX(), mouse.DtY()
        cls.mouse_vr_pos.x += dx
        cls.mouse_vr_pos.y += dy
        
        if dx !=0 or dy !=0:
            flag_move = True
            cls.flag_update_vr_head_offset = True
        else:
            flag_move = False

        if cls.flag_update_vr_head_offset:
            cls.vr_head_offset = hg.GetT(vr_state.head) - hg.GetT(vr_state.body)
            cls.flag_update_vr_head_offset = False

        resolution = hg.Vec2(vr_state.width, vr_state.height)
        fov = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(vr_state.left.projection, hg.ComputeAspectRatioX(vr_state.width, vr_state.height)))

        if mouse_pointer_intersection is None:
            new_mouse_pointer_distance = cls.mouse_pointer_default_distance
        else:
            new_mouse_pointer_distance = hg.Len(mouse_pointer_intersection - (hg.GetT(vr_state.body) + cls.vr_head_offset ))

        if flag_move:
            cls.mouse_pointer_distance = new_mouse_pointer_distance

        screen_height = tan(fov/2) * cls.mouse_pointer_distance * 2
        cls.pixel_size = screen_height / resolution.y

        mouse_phi = cls.mouse_vr_pos.x / 1080 * pi/2
        mouse_theta = -cls.mouse_vr_pos.y / 1080 * pi/2
        pointer_pos = hg.RotationMat3(mouse_theta, mouse_phi, 0) * hg.Vec3(0, 0, cls.mouse_pointer_distance)
        
        pointer_world_pos= vr_state.body * (cls.vr_head_offset + pointer_pos)
        cls.pointer_world_matrix = hg.Mat4LookAt(pointer_world_pos, hg.GetT(vr_state.head))

    @classmethod
    def update(cls, camera, mouse, width, height):
        cam = camera.GetCamera()
        camera_matrix = camera.GetTransform().GetWorld()
        view_state = hg.ComputePerspectiveViewState(camera_matrix, cam.GetFov(), cam.GetZNear(), cam.GetZFar(), hg.ComputeAspectRatioX(width, height))
        cls.update_low_level(view_state, hg.Vec2(width, height), camera_matrix, hg.Vec2(mouse.X(), mouse.Y()))

    @classmethod
    def update_low_level(cls, view_state:hg.ViewState, resolution: hg.Vec2, camera_matrix: hg.Mat4, mouse_screen_pos: hg.Vec2):
        fov = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(view_state.proj, hg.ComputeAspectRatioX(resolution.x, resolution.y)))
        screen_height = tan(fov/2) * cls.mouse_pointer_distance * 2
        cls.pixel_size = screen_height / resolution.y
        mouse_pos = (mouse_screen_pos - resolution / 2) * cls.pixel_size
        pointer_pos = hg.Vec3(mouse_pos.x,mouse_pos.y, cls.mouse_pointer_distance)
        cls.pointer_world_matrix = camera_matrix * hg.TransformationMat4(pointer_pos,hg.Vec3(0,0,0), hg.Vec3(1, -1, 1))
        
    @classmethod
    def draw_pointer(cls, views_ids: list, resolution_y: int, user_position: hg.Vec3, fov: float, mouse_world_intersection: hg.Vec3 = None):
        
        if mouse_world_intersection is None:
            pixel_size = cls.pixel_size
            pointer_display_matrix = cls.pointer_world_matrix
        else:
            mouse_pointer_v = mouse_world_intersection - user_position
            screen_height = tan(fov/2) * hg.Len(mouse_pointer_v) * 2
            pixel_size = screen_height / resolution_y
            pointer_display_matrix = hg.TransformationMat4(mouse_world_intersection, hg.GetR(cls.pointer_world_matrix))

        pointer_size =  pixel_size * cls.mouse_pointer_size
        size = hg.Vec2(float(cls.pointer_ti.width) / float(cls.pointer_ti.height), 1.0) * pointer_size
        p0 = cls.pointer_center * pixel_size
        p1 = p0 - size

        cls.vtx.Clear()
        cls.uniforms_values_list.clear()
        cls.uniforms_textures_list.clear()
        idx = [0, 1, 2, 0, 2, 3]
        c= hg.Color.White
        cls.vtx.Begin(0).SetPos(pointer_display_matrix * hg.Vec3(p0.x, p0.y, 0)).SetColor0(c).SetTexCoord0(hg.Vec2(0, 0)).End()
        cls.vtx.Begin(1).SetPos(pointer_display_matrix * hg.Vec3(p0.x, p1.y, 0)).SetColor0(c).SetTexCoord0(hg.Vec2(0, 1)).End()
        cls.vtx.Begin(2).SetPos(pointer_display_matrix * hg.Vec3(p1.x, p1.y, 0)).SetColor0(c).SetTexCoord0(hg.Vec2(1, 1)).End()
        cls.vtx.Begin(3).SetPos(pointer_display_matrix * hg.Vec3(p1.x, p0.y, 0)).SetColor0(c).SetTexCoord0(hg.Vec2(1, 0)).End()
        cls.uniforms_textures_list.push_back(hg.MakeUniformSetTexture("u_tex", cls.pointer_texture, 0))
         
        for vid in views_ids:
            hg.DrawTriangles(vid, idx, cls.vtx, cls.shader_texture, cls.uniforms_values_list, cls.uniforms_textures_list, cls.pointer_render_state)
        return vid + 1
   
       