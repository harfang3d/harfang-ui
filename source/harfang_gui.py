import harfang as hg
from math import sin, cos, inf
from mouse_pointer_3d import MousePointer3D
import json
import copy
from vr_controllers import VRControllersHandler


def on_key_press(text: str):
	HarfangUI.ascii_code = text

class HarfangGUIRenderer:

	vtx_layout = None
	vtx = None
	shader = None
	shader_texture = None
	uniforms_values_list = None
	uniforms_textures_list = None
	text_uniform_values = None
	text_render_state = None

	fonts = []
	fonts_sizes = []

	box_render_state = None

	# sprites
	textures = {}
	textures_info = {}

	@classmethod
	def init(cls, fonts_files, fonts_sizes):
		cls.vtx_layout = hg.VertexLayout()
		cls.vtx_layout.Begin()
		cls.vtx_layout.Add(hg.A_Position, 3, hg.AT_Float)
		cls.vtx_layout.Add(hg.A_Color0, 4, hg.AT_Float)
		cls.vtx_layout.Add(hg.A_TexCoord0, 3, hg.AT_Float)
		cls.vtx_layout.End()

		cls.vtx = hg.Vertices(cls.vtx_layout, 256)

		cls.shader_flat = hg.LoadProgramFromAssets('hgui_shaders/hgui_pos_rgb')
		cls.shader_texture = hg.LoadProgramFromAssets('hgui_shaders/hgui_texture')
		cls.shader_texture_opacity = hg.LoadProgramFromAssets('hgui_shaders/hgui_texture_opacity')

		cls.uniforms_values_list = hg.UniformSetValueList()
		cls.uniforms_textures_list = hg.UniformSetTextureList()

		cls.box_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_LessEqual, hg.FC_Disabled, False)
		cls.box_render_state_opaque = hg.ComputeRenderState(hg.BM_Opaque, hg.DT_LessEqual, hg.FC_Disabled, True)

		cls.fonts_sizes = fonts_sizes
		for i in range(len(fonts_files)):
			cls.fonts.append(hg.LoadFontFromAssets('font/' + fonts_files[i], fonts_sizes[i], 1024, 1, 
			"!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"))
		cls.font_prg = hg.LoadProgramFromAssets('hgui_shaders/hgui_font')
		cls.current_font_id = 0

		# text uniforms and render state
		cls.text_uniform_values = [hg.MakeUniformSetValue('u_color', hg.Vec4(1, 1, 0))]
		w_z, w_r, w_g, w_b, w_a = False, True, True, True, True
		cls.text_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Disabled, hg.FC_Disabled, w_z, w_r, w_g, w_b, w_a)

	@classmethod
	def get_texture(cls, texture_path):
		if texture_path not in cls.textures:
			cls.textures[texture_path], cls.textures_info[texture_path] = hg.LoadTextureFromAssets(texture_path, 0)
		return cls.textures[texture_path]

	@classmethod
	def draw_box(cls, vid: int, vertices, color: hg.Color, texture_path = None, flag_opaque = False):
		cls.vtx.Clear()
		cls.uniforms_values_list.clear()
		cls.uniforms_textures_list.clear()
		idx = [0, 1, 2, 0, 2, 3]
		cls.vtx.Begin(0).SetPos(vertices[0]).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()
		cls.vtx.Begin(1).SetPos(vertices[1]).SetColor0(color).SetTexCoord0(hg.Vec2(0, 1)).End()
		cls.vtx.Begin(2).SetPos(vertices[2]).SetColor0(color).SetTexCoord0(hg.Vec2(1, 1)).End()
		cls.vtx.Begin(3).SetPos(vertices[3]).SetColor0(color).SetTexCoord0(hg.Vec2(1, 0)).End()
		if texture_path is not None:
			cls.uniforms_textures_list.push_back(hg.MakeUniformSetTexture("u_tex", cls.get_texture(texture_path), 0))
			shader = cls.shader_texture
		else:
			shader = cls.shader_flat
		if flag_opaque:
			rs = cls.box_render_state_opaque
		else:
			rs = cls.box_render_state
		hg.DrawTriangles(vid, idx, cls.vtx, shader, cls.uniforms_values_list, cls.uniforms_textures_list, rs)
	
	@classmethod
	def draw_rendered_texture_box(cls, vid: int, vertices, color: hg.Color, texture: hg.Texture):
		cls.vtx.Clear()
		cls.uniforms_values_list.clear()
		cls.uniforms_textures_list.clear()
		idx = [0, 1, 2, 0, 2, 3]
		cls.vtx.Begin(0).SetPos(vertices[0]).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()
		cls.vtx.Begin(1).SetPos(vertices[1]).SetColor0(color).SetTexCoord0(hg.Vec2(0, 1)).End()
		cls.vtx.Begin(2).SetPos(vertices[2]).SetColor0(color).SetTexCoord0(hg.Vec2(1, 1)).End()
		cls.vtx.Begin(3).SetPos(vertices[3]).SetColor0(color).SetTexCoord0(hg.Vec2(1, 0)).End()
		cls.uniforms_textures_list.push_back(hg.MakeUniformSetTexture("u_tex", texture, 0))
		hg.DrawTriangles(vid, idx, cls.vtx, cls.shader_texture_opacity, cls.uniforms_values_list, cls.uniforms_textures_list, cls.box_render_state)
	
	@classmethod
	def draw_box_border(cls, vid: int, vertices, color: hg.Color, flag_opaque = False):
		cls.vtx.Clear()
		cls.uniforms_values_list.clear()
		cls.uniforms_textures_list.clear()
		idx = [0, 1, 5, 0, 5, 4, 
				1, 2, 6, 1, 6, 5,
				2, 3, 7, 2, 7, 6,
				3, 0, 4, 3, 4, 7]
		
		for i in range(8):
			cls.vtx.Begin(i).SetPos(vertices[i]).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()
		
		if flag_opaque:
			rs = cls.box_render_state_opaque
		else:
			rs = cls.box_render_state
		hg.DrawTriangles(vid, idx, cls.vtx, cls.shader_flat, cls.uniforms_values_list, cls.uniforms_textures_list, rs)

	@classmethod
	def draw_circle(cls, vid, matrix:hg.Mat4, pos, r, angle_start, angle, color):
		cls.vtx.Clear()
		cls.uniforms_values_list.clear()
		cls.uniforms_textures_list.clear()
		cls.vtx.Begin(0).SetPos(matrix * hg.Vec3(pos.x, pos.y, pos.z)).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()

		idx = []
		num_sections = 32
		step = angle / num_sections
		for i in range(num_sections + 1):
			alpha = i * step + angle_start
			cls.vtx.Begin(i + 1).SetPos(matrix * hg.Vec3(pos.x + cos(alpha) * r, pos.y + sin(alpha) * r, pos.z)).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()
			if i > 0:
				idx += [0, i + 1, i]

		hg.DrawTriangles(vid, idx, cls.vtx, cls.shader_flat, cls.uniforms_values_list, cls.uniforms_textures_list, cls.box_render_state)

	@classmethod
	def compute_text_size(cls, font_id, text):
		rect = hg.ComputeTextRect(cls.fonts[font_id], text)
		return hg.Vec2(rect.ex, rect.ey)

	@classmethod
	def draw_text(cls, vid, matrix:hg.Mat4, text, font_id, color):
		cls.text_uniform_values = [hg.MakeUniformSetValue('u_color', hg.Vec4(color.r, color.g, color.b, color.a))]
		hg.DrawText(vid, cls.fonts[font_id], text, cls.font_prg, 'u_tex', 0, matrix, hg.Vec3(0, 0, 0), hg.DTHA_Center, hg.DTVA_Center, cls.text_uniform_values, [], cls.text_render_state)

	@classmethod
	def render_widget_container(cls, view_id, container):
		draw_list = HarfangGUISceneGraph.widgets_containers_displays_lists[container["widget_id"]]
		hg.SetViewFrameBuffer(view_id, container["frame_buffer"].handle)
	
		hg.SetViewMode(view_id, hg.VM_Sequential)
		w, h = int(container["size"].x), int(container["size"].y)
		hg.SetViewRect(view_id, 0, 0, w, h)
		
		hg.SetViewOrthographic(view_id, 0, 0, w, h, hg.TransformationMat4(hg.Vec3(w / 2 + container["scroll_position"].x, h / 2 + container["scroll_position"].y, 0), hg.Vec3(0, 0, 0), hg.Vec3(1, -1, 1)), 0, 101, h)
		hg.SetViewClear(view_id, hg.CF_Depth | hg.CF_Color, hg.Color(1, 1, 1, 0), 1, 0)

		for draw_element in draw_list:
			if draw_element["type"] == "box":
					cls.draw_box(view_id, draw_element["vertices"], draw_element["color"], draw_element["texture"])
			elif draw_element["type"] == "box_border":
					cls.draw_box_border(view_id, draw_element["vertices"], draw_element["color"])
			elif draw_element["type"] == "opaque_box":
					cls.draw_box(view_id, draw_element["vertices"], draw_element["color"], draw_element["texture"], True)
			elif draw_element["type"] == "text":
					cls.draw_text(view_id, draw_element["matrix"], draw_element["text"], draw_element["font_id"], draw_element["color"])
			elif draw_element["type"] == "rendered_texture_box":
					cls.draw_rendered_texture_box(view_id, draw_element["vertices"], draw_element["color"], draw_element["texture"])

		container["view_id"] = view_id
		
		return view_id + 1

	@classmethod
	def create_output(cls, resolution: hg.Vec2, view_state: hg.ViewState, frame_buffer: hg.FrameBuffer):
		return {"resolution": resolution, "view_state": view_state, "frame_buffer": frame_buffer }

	@classmethod
	def render(cls, view_id, outputs2D: list, outputs3D: list):
		
		# Setup 3D views
		render_views_3D = []
		for output in outputs3D:
			resolution = output["resolution"]
			view_state = output["view_state"]
			if resolution is not None and view_state is not None:
				fb = output["frame_buffer"]
				
				if fb is None:
					hg.SetViewFrameBuffer(view_id, hg.InvalidFrameBufferHandle)
				else:
					hg.SetViewFrameBuffer(view_id, fb.GetHandle())
				
				hg.SetViewMode(view_id, hg.VM_Sequential)
				hg.SetViewRect(view_id, 0, 0, int(resolution.x), int(resolution.y))
				hg.SetViewTransform(view_id, view_state.view, view_state.proj)
				hg.SetViewClear(view_id, 0, hg.Color.Black, 1, 0)
				
				render_views_3D.append(view_id)
				view_id += 1

		# Setup 2D views
		render_views_2D = []
		for output in outputs2D:
			resolution = output["resolution"]
			view_state = output["view_state"]
			if resolution is not None:
				fb = output["frame_buffer"]
				if fb is None:
					hg.SetViewFrameBuffer(view_id, hg.InvalidFrameBufferHandle)
				else:
					hg.SetViewFrameBuffer(view_id, fb.GetHandle())
				if view_state is None:
					hg.SetViewOrthographic(view_id, 0, 0, int(resolution.x), int(resolution.y), hg.TransformationMat4(hg.Vec3(resolution.x / 2, -resolution.y / 2, 0), hg.Vec3(0, 0, 0), hg.Vec3(1, 1, 1)), 0.1, 1000, resolution.y)
				else:
					hg.SetViewTransform(view_id, view_state.view, view_state.proj)
				hg.SetViewMode(view_id, hg.VM_Sequential)
				hg.SetViewRect(view_id, 0, 0, int(resolution.x), int(resolution.y))
				if view_id == 0:
					hg.SetViewClear(view_id, hg.CF_Color | hg.CF_Depth, hg.Color.Black, 1, 0)
				else:
					hg.SetViewClear(view_id, hg.CF_Depth, hg.Color.Black, 1, 0)
				
				render_views_2D.append(view_id)
				view_id += 1

		# Render widgets containers to textures then display to fbs or screen
		
		cls.uniforms_values_list.clear()
		shader = cls.shader_texture_opacity
		rs = cls.box_render_state
		idx = [0, 1, 2, 0, 2, 3]

		# Render 3D containers
		for container in HarfangGUISceneGraph.widgets_containers3D_children_order:
			
			view_id = cls.render_widget_container(view_id, container)
		
		for container in reversed(HarfangGUISceneGraph.widgets_containers3D_children_order):
			# Display 3D widgets containers
			if not container["flag_2D"]:
				# Render widgets container to texture:
				c = hg.Color(1, 1, 1, container["opacity"])
				matrix =container["world_matrix"]
				pos = hg.Vec3(0, 0, 0)
				size = container["size"]
				p0 = matrix * pos
				p1 = matrix * hg.Vec3(pos.x, pos.y + size.y, pos.z)
				p2 = matrix * hg.Vec3(pos.x + size.x, pos.y + size.y, pos.z)
				p3 = matrix * hg.Vec3(pos.x + size.x, pos.y, pos.z)
				tex = container["color_texture"]

				# Display widgets container
				cls.vtx.Clear()
				cls.uniforms_textures_list.clear()
				
				cls.vtx.Begin(0).SetPos(p0).SetColor0(c).SetTexCoord0(hg.Vec2(0, 0)).End()
				cls.vtx.Begin(1).SetPos(p1).SetColor0(c).SetTexCoord0(hg.Vec2(0, 1)).End()
				cls.vtx.Begin(2).SetPos(p2).SetColor0(c).SetTexCoord0(hg.Vec2(1, 1)).End()
				cls.vtx.Begin(3).SetPos(p3).SetColor0(c).SetTexCoord0(hg.Vec2(1, 0)).End()


				cls.uniforms_textures_list.push_back(hg.MakeUniformSetTexture("u_tex", tex, 0))
				
				for vid in render_views_3D:
					hg.DrawTriangles(vid, idx, cls.vtx, shader, cls.uniforms_values_list, cls.uniforms_textures_list, rs)
		
		# Render 2D containers
		if len(render_views_2D) > 0:
			for container in HarfangGUISceneGraph.widgets_containers2D_children_order:
				
				view_id = cls.render_widget_container(view_id, container)
				
				# Display 3D widgets containers
				if container["parent_id"] == "MainContainer2D":
					# Render widgets container to texture:
					c = hg.Color(1, 1, 1, container["opacity"])
					matrix = container["world_matrix"]
					pos = hg.Vec3(0, 0, 0)
					size = container["size"]
					p0 = matrix * pos
					p1 = matrix * hg.Vec3(pos.x, pos.y + size.y, pos.z)
					p2 = matrix * hg.Vec3(pos.x + size.x, pos.y + size.y, pos.z)
					p3 = matrix * hg.Vec3(pos.x + size.x, pos.y, pos.z)
					tex = container["color_texture"]

					# Display widgets container
					cls.vtx.Clear()
					cls.uniforms_textures_list.clear()
					
					cls.vtx.Begin(0).SetPos(p0).SetColor0(c).SetTexCoord0(hg.Vec2(0, 0)).End()
					cls.vtx.Begin(1).SetPos(p1).SetColor0(c).SetTexCoord0(hg.Vec2(0, 1)).End()
					cls.vtx.Begin(2).SetPos(p2).SetColor0(c).SetTexCoord0(hg.Vec2(1, 1)).End()
					cls.vtx.Begin(3).SetPos(p3).SetColor0(c).SetTexCoord0(hg.Vec2(1, 0)).End()


					cls.uniforms_textures_list.push_back(hg.MakeUniformSetTexture("u_tex", tex, 0))
					
					for vid in render_views_2D:
						hg.DrawTriangles(vid, idx, cls.vtx, shader, cls.uniforms_values_list, cls.uniforms_textures_list, rs)
		
		return view_id, render_views_3D, render_views_2D

class HarfangUISkin:

	check_texture = None
	check_texture_info = None

	keyboard_cursor_color = None

	# Level 0 primitives
	properties = {}

	# Components
	components = {}

	# Widgets models
	widgets_models = {}

	@classmethod
	def init(cls):
		idle_t = 0.2
		hover_t = 0.15
		mb_down_t = 0.05
		check_t = 0.2
		edit_t = 0.1

		cls.check_texture, cls.check_texture_info = hg.LoadTextureFromAssets("hgui_textures/check.png", 0)

		cls.keyboard_cursor_color = hg.Color(1, 1, 1, 0.75)

		cls.properties = cls.load_properties("properties.json")

		cls.components = {
			"window_background": {
				"cursor_auto": False,
				"size_factor": [1, 1, 1],
				"properties": ["window_box_color", "window_box_border_thickness", "window_box_border_color"] #"widget_opacity"
				},
			"window_title": {
				"display_text": "label",
				"text_size": 1,
				"cursor_auto": False,
				"size_factor": [1, -1, -1],
				"properties": ["window_box_border_color", "window_title_margins", "window_title_color"]
			},
			"scrollbar": {
				"properties": ["scrollbar_thickness", "scrollbar_background_color", "scrollbar_color", "scrollbar_thikness"]
			},
			"info_text": {
				"display_text": "text",
				"text_size": 1,
				"properties": ["info_text_color", "text_size", "info_text_margins"]
				},
			"info_image": {
				"texture": None,
				"properties": ["info_image_offset", "info_image_margins", "texture_box_color"]
				},
			"button_box": {
				"display_text": "label",
				"text_size": 1,
				"properties": ["button_offset", "button_box_color", "button_text_color", "text_size", "button_text_margins", "widget_border_thickness", "widget_border_color"]
				},
			"label_box": {
				"display_text": "label",
				"text_size": 1,
				"properties": ["text_size", "label_text_margins", "label_box_color", "label_text_color"]
				},
			"image_button": {
				"texture": None,
				"properties": ["button_offset", "button_image_margins", "button_box_color", "texture_box_color", "widget_border_thickness", "widget_border_color"]
				},
			"check_box":{
				"texture": "hgui_textures/check.png",
				"properties": ["button_offset","check_size", "checkbox_margins", "button_box_color", "check_color"]
				},
			"input_box": {
				"display_text": "text",
				"input_text": "edit_text",
				"text_size": 1,
				"properties": ["text_size", "label_text_margins", "input_box_color", "input_text_color"]
				},
			"radio_image_button": {
				"texture": None,
				"properties": ["radio_image_offset","radio_button_image_margins", "radio_button_box_color", "texture_box_color", "radio_image_border_color", "radio_image_border_thickness"]
				},
			"toggle_button_box": {
				"display_text": "text",
				"forced_text_width": None,
				"texts": None,
				"text_size": 1,
				"properties": ["button_offset", "button_box_color", "button_text_color", "text_size", "button_text_margins", "widget_border_thickness", "widget_border_color"]
				},
			"toggle_image_button": {
				"textures": None,
				"properties": ["toggle_image_button_offset","toggle_image_button_margins", "toggle_image_button_box_color", "toggle_image_button_texture_box_color", "toggle_image_button_border_color", "toggle_image_button_border_thickness"]
				}
		}

		cls.widgets_models = {
			"window" : {"components": ["window_background", "window_title"]},
			"scrollbar_v": {"components": ["scrollbar"], "part_size": 1, "total_size": 3, "scrollbar_position":0, "scrollbar_position_dest": 0, "bar_inertia": 0.25},
			"scrollbar_h": {"components": ["scrollbar"], "part_size": 1, "total_size": 3, "scrollbar_position":0, "scrollbar_position_dest": 0, "bar_inertia": 0.25},
			"info_text" : {"components": ["info_text"]},
			"info_image" : {"components": ["info_image"]},
			"button": {"components": ["button_box"]},
			"image_button": {"components": ["image_button"]},
			"check_box": {"components": ["check_box", "label_box"]},
			"input_text": {"components": ["label_box", "input_box"]},
			"radio_image_button": {"components": ["radio_image_button"], "radio_idx": 0},
			"toggle_button": {"components": ["toggle_button_box"], "toggle_idx": 0},
			"toggle_image_button": {"components": ["toggle_image_button"], "toggle_idx": 0}
		}


	@classmethod
	def interpolate_values(cls, v_start, v_end, t):
		t = max(0, min(1, t))
		v = v_start * (1-t) + v_end * t
		return v
	
	@classmethod
	def load_properties(cls, file_name):
		file = open(file_name, "r")
		json_script = file.read()
		file.close()
		if json_script != "":
			return json.loads(json_script)
		else:
			print("HGUISkin - ERROR - Can't open properties json file !")
		return None

	@classmethod
	def save_properties(cls, output_file_name):

		json_script = json.dumps(cls.properties, indent=4)
		file = open(output_file_name, "w")
		file.write(json_script)
		file.close()
		

class HarfangGUISceneGraph:

	widgets_containers_stack = [] #Used for matrices computations
	
	widgets_containers3D_user_order = []
	widgets_containers3D_children_order = []

	widgets_containers2D_user_order = []
	widgets_containers2D_children_order = []

	flag_2D_list = False

	widgets_containers_displays_lists = {}
	depth_scale = 10
	current_container_id = ""

	@classmethod
	def init(cls):
		pass

	@classmethod
	def clear(cls):
		cls.widgets_containers_stack = []
		cls.widgets_containers3D_user_order = []
		cls.widgets_containers3D_children_order = []
		cls.widgets_containers2D_user_order = []
		cls.widgets_containers2D_children_order = []
		cls.widgets_containers_displays_lists = {}

	@classmethod
	def add_widgets_container(cls,widgets_container):
		if cls.flag_2D_list:
			cls.widgets_containers2D_user_order.append(widgets_container)
		else:
			cls.widgets_containers3D_user_order.append(widgets_container)
		cls.widgets_containers_displays_lists[widgets_container["widget_id"]] = [] # Intégrer les display lists aux conteners ?
	

	@classmethod
	def set_containers2D_list(cls):
		cls.flag_2D_list = True
	
	@classmethod
	def set_containers3D_list(cls):
		cls.flag_2D_list = False

	@classmethod
	def get_current_container(cls):
		if len(cls.widgets_containers_stack) > 0:
			return cls.widgets_containers_stack[-1]
		return None

	@classmethod
	def get_current_container_child_depth(cls):
		return len(cls.widgets_containers_stack)

	@classmethod
	def set_container_display_list(cls, container_id):
		cls.current_container_id = container_id

	@classmethod
	#Sort for rendering
	def sort_widgets_containers(cls):
		
		if len(cls.widgets_containers3D_user_order) > 0:
			#align_order = sorted(cls.widgets_containers3D_user_order, key = lambda wc: wc["align_position"])
			cls.widgets_containers3D_children_order = sorted(cls.widgets_containers3D_user_order, key = lambda wc: wc["child_depth"], reverse = True)
			
		n=len(cls.widgets_containers2D_user_order)
		if n > 0:
			#align_order = sorted(cls.widgets_containers2D_user_order, key = lambda wc: wc["align_position"])
			cls.widgets_containers2D_children_order = sorted(cls.widgets_containers2D_user_order, key = lambda wc: wc["child_depth"], reverse = True)
			
	
	@classmethod
	def add_box(cls, matrix, pos, size, color):

		p0 = matrix * pos
		p1 = matrix * hg.Vec3(pos.x, pos.y + size.y, pos.z)
		p2 = matrix * hg.Vec3(pos.x + size.x, pos.y + size.y, pos.z)
		p3 = matrix * hg.Vec3(pos.x + size.x, pos.y, pos.z)

		cls.widgets_containers_displays_lists[cls.current_container_id].append({"type": "box", "vertices": [p0, p1, p2, p3], "color": color, "texture": None})
	
	@classmethod
	def add_box_border(cls, matrix, pos, size, border_thickness, color):
		
		p0 = pos
		p1 = hg.Vec3(pos.x, pos.y + size.y, pos.z)
		p2 = hg.Vec3(pos.x + size.x, pos.y + size.y, pos.z)
		p3 = hg.Vec3(pos.x + size.x, pos.y, pos.z)

		p4 = p0 + hg.Vec3(border_thickness, border_thickness, 0)
		p5 = p1 + hg.Vec3(border_thickness, -border_thickness, 0)
		p6 = p2 + hg.Vec3(-border_thickness, -border_thickness, 0)
		p7 = p3 + hg.Vec3(-border_thickness, border_thickness, 0)

		v = [p0, p1, p2, p3, p4, p5, p6, p7]
		for i in range(len(v)):
			v[i] = matrix * v[i]

		cls.widgets_containers_displays_lists[cls.current_container_id].append({"type": "box_border", "vertices": v, "color": color})

	@classmethod
	def add_opaque_box(cls, matrix, pos, size, color):
		
		p0 = matrix * pos
		p1 = matrix * hg.Vec3(pos.x, pos.y + size.y, pos.z)
		p2 = matrix * hg.Vec3(pos.x + size.x, pos.y + size.y, pos.z)
		p3 = matrix * hg.Vec3(pos.x + size.x, pos.y, pos.z)

		cls.widgets_containers_displays_lists[cls.current_container_id].append({"type": "opaque_box", "vertices": [p0, p1, p2, p3], "color": color, "texture": None})

	@classmethod
	def add_texture_box(cls, matrix, pos, size, color, texture = None, type_id = "box"):
		p0 = matrix * pos
		p1 = matrix * hg.Vec3(pos.x, pos.y + size.y, pos.z)
		p2 = matrix * hg.Vec3(pos.x + size.x, pos.y + size.y, pos.z)
		p3 = matrix * hg.Vec3(pos.x + size.x, pos.y, pos.z)
		cls.widgets_containers_displays_lists[cls.current_container_id].append({"type": type_id, "vertices": [p0, p1, p2, p3], "color": color, "texture": texture})

	@classmethod
	def add_text(cls, matrix, pos, scale, text, font_id, color):
		mat = matrix * hg.TransformationMat4(pos, hg.Vec3.Zero, hg.Vec3(scale, scale, scale))
		cls.widgets_containers_displays_lists[cls.current_container_id].append({"type": "text","matrix":mat, "text": text, "font_id": font_id, "color": color})




class HarfangUI:

	# VR
	flag_vr = False
	vr_state = None
	left_fb = None
	right_fb = None

	left_fb = None
	right_fb = None

	flag_use_pointer_VR = True

	# Screen
	width = 0
	height = 0

	# Widgets

	last_widget = None # Used to compute cursor position
	widgets = {}
	
	current_focused_widget = None

	radio_image_button_size = None

	# Widgets containers
	main_widgets_container_3D = None
	main_widgets_container_2D = None

	output_framebuffer_2D = None

	# Windows flags:
	HGUIWF_2D = 0x1
	HGUIWF_NoPointerMove = 0x2
	HGUIWF_HideTitle = 0x4
	HGUIWF_Invisible = 0x8
	HGUIWF_HideScrollbars = 0x10

	# Frame datas (updated on each frame)

	flag_same_line = False
	line_max_y_size = 0 #Used for auto-positionning with same_line(): the biggest widget Ysize in the line
	line_space_size = 3 # Space between lines in pixels
	current_font_id = 0
	mouse = None
	keyboard = None
	dt = 0
	timestamp = 0

	new_signals = {} #Signals sended in frame
	current_signals = {} # Prec. frame signals, read in current frame
	
	UI_STATE_MAIN = 0 # Widgets mouse hovering / mouse click / keyboard shortcuts
	UI_STATE_WIDGET_KEYBOARD_FOCUS = 1 # The content of a widget is being edited (Text input)
	UI_STATE_WIDGET_MOUSE_FOCUS = 2 # A widget is using mouse (Scrollbar...)
	
	ui_state = 0

	camera = None
	focal_distance = 1
	camera3D_matrix = None
	camera2D_matrix = None
	
	controllers = {}
	focussed_containers = []

	kb_cursor_pos = 0 # Used to edit input texts

	ascii_code = None
	ascii_connect = None

	@classmethod
	# Scene and resources only needed for VR mode
	def init(cls, fonts_files, fonts_sizes, width, height):
		HarfangGUIRenderer.init(fonts_files, fonts_sizes)
		HarfangUISkin.init()
		HarfangGUISceneGraph.init()
		cls.cursor = hg.Vec3(0, 0, 0)
		cls.flag_same_line = False
		cls.timestamp = 0
		cls.new_signals = {}
		cls.current_signals = {}
		cls.ui_state = HarfangUI.UI_STATE_MAIN

		cls.radio_image_button_size = hg.Vec2(64, 64)

		# Setup mouse controller:
		cls.controllers["mouse"] = cls.new_controller("mouse")

		# Setup main containers:

		pos, rot,scale = hg.Vec3(0, 0, 0), hg.Deg3(0, 0, 0), hg.Vec3(1, -1, 1)
		cls.main_widgets_container_3D = cls.new_widgets_container("Main_container")
		cls.main_widgets_container_3D["widget_id"] = "MainContainer3D"
		cls.main_widgets_container_3D["scale"] = scale
		cls.main_widgets_container_3D["size"] = hg.Vec3(width, height, 0)
		cls.main_widgets_container_3D["position"] = pos
		cls.main_widgets_container_3D["rotation"] = rot
		cls.main_widgets_container_3D["local_matrix"] =  hg.TransformationMat4(pos, rot, scale)		
		cls.main_widgets_container_3D["world_matrix"] =  hg.Mat4.Identity * cls.main_widgets_container_3D["local_matrix"]
		
		for _, pointer in cls.main_widgets_container_3D["pointers"].items():
			pointer["pointer_local_position"] = hg.Vec2(0, 0)
			pointer["pointer_local_dt"] = hg.Vec2(0, 0)

		pos, rot,scale = hg.Vec3(0, 0, 100), hg.Deg3(0, 0, 0), hg.Vec3(1, -1, 1)
		cls.main_widgets_container_2D = cls.new_widgets_container("Main_container")
		cls.main_widgets_container_2D["widget_id"] = "MainContainer2D"
		cls.main_widgets_container_2D["scale"] = scale
		cls.main_widgets_container_2D["size"] = hg.Vec3(width, height, 0)
		cls.main_widgets_container_2D["position"] = pos
		cls.main_widgets_container_2D["rotation"] = rot
		cls.main_widgets_container_2D["local_matrix"] =  hg.TransformationMat4(pos, rot, scale)		
		cls.main_widgets_container_2D["world_matrix"] =  hg.Mat4.Identity * cls.main_widgets_container_2D["local_matrix"]
		cls.main_widgets_container_2D["flag_2D"] =  True
		
		for _, pointer in cls.main_widgets_container_2D["pointers"].items():
			pointer["pointer_local_position"] = hg.Vec2(0, 0)
			pointer["pointer_local_dt"] = hg.Vec2(0, 0)
		
		cls.ascii_code = None

		VRControllersHandler.init()
		MousePointer3D.init()

	@classmethod
	def set_ui_state(cls, state_id):
		cls.ui_state = state_id

	@classmethod
	def want_capture_mouse(cls):
		if cls.mouse is None:
			return False
		
		# Capture new mouse click:
		if cls.mouse.Down(hg.MB_0):
			if "MLB_pressed" not in cls.new_signals and "MLB_down" not in cls.new_signals:
				return True
		
		# Mouse click detected but not stil updated in widgets:
		if cls.ui_state == cls.UI_STATE_WIDGET_MOUSE_FOCUS or "MLB_pressed" in cls.new_signals:
			return True
		return False
	@classmethod
	def want_capture_keyboard(cls):
		if cls.ui_state == cls.UI_STATE_WIDGET_KEYBOARD_FOCUS:
			return True
		return False

	@classmethod
	def is_a_window_hovered(cls):
		if len(cls.focussed_containers) > 0:
			return True
		return False

	@classmethod
	def new_controller(cls, id):
		return {
			"id": id,
			"ray_p0": None, #Vec3, position
			"ray_p1": None, #vec3, direction
			"world_intersection": None, #Vec3
			"focused_container": None #widgets_container
		}

	@classmethod
	def new_gui_object(cls, type):
		return {
			"type": type,
			"classe":"gui_object",
			"hidden": False,
			"enable": True,
			"local_matrix": None,
			"world_matrix": None,
			"position": hg.Vec3(0, 0, 0),
			"rotation": hg.Vec3(0, 0, 0),
			"scale": hg.Vec3(1, 1, 1),
			"offset": hg.Vec3(0, 0, 0),
			"size": hg.Vec3(0, 0, 0),
			"states": []
		}

	@classmethod
	def new_component(cls, type):
		component = cls.new_gui_object(type)
		component["classe"] = "component"
		component.update(
			{
				"properties" : {},
				"cursor_auto": True,	#False if cursor is not incremented in widget rendering
				"size_factor": hg.Vec3(-1, -1, -1) # Size linked to container size. factor <= 0 : no proportional size correction. factor > 0 : size = max(component_size * factor, container_size) 
			}
		)
		return component

	@classmethod
	def get_property_value(cls, component, property_name):
		return component["properties"][property_name]["value"]
	
	@classmethod
	def get_property_states_value(cls, component, property_name, states):
		class_property = HarfangUISkin.properties[property_name]
		component_property = component["properties"][property_name]
		value = None
		for layer_id in range(len(component_property["layers"])):
			class_layer = class_property["layers"][layer_id]
			property_layer = component_property["layers"][layer_id]
			for state_name in states:
				if state_name in property_layer["states"]:
					property_state = property_layer["states"][state_name]
					if value is None or class_layer["operator"] == "set":
						value = property_state["value"]
					elif class_layer["operator"] == "add":
						value += property_state["value"]
					elif class_layer["operator"] == "multiply":
						value *= property_state["value"]
					break # One state by layer
		return value

	@classmethod
	def new_single_widget(cls, type):
		widget = cls.new_gui_object(type)
		widget["classe"] = "widget"
		widget.update({
			"flag_new": True,	#True at widget creation, else False (see get_widget())
			"cursor": hg.Vec3(0, 0, 0),
			"cursor_start_line": hg.Vec3(0, 0, 0),
			"default_cursor_start_line": hg.Vec3(0, 0, 0),
			"opacity": 1,
			"widget_id": "",
			"max_size": hg.Vec3(0, 0, 0),
			"components": {},
			"components_render_order": [],
			"parent_id": None # Parent container ID
		})
		return widget

	@classmethod
	def new_pointer(cls, type):
		return {
			"type": type,
			"pointer_world_position": None,
			"pointer_local_position": None,
			"pointer_local_dt": None,
			"enabled": True
		}

	@classmethod
	def new_widgets_container(cls, type):
		container = cls.new_single_widget(type)
		container["classe"] = "widgets_container"
		container.update({
			"flag_2D": False,
			"flag_invisible": False,
			"children_order": [],
			"pointers": {"mouse": cls.new_pointer("mouse")},
			"sort_weight": 0,		# Sort weight = distance to camera-pointer ray for 3D windows. Sort weight = align position for 2D windows
			"child_depth": 0,
			"containers_2D_children_align_order": [],	#2D Overlays order are user-focus dependant for 2D containers - Used for final rendering order
			"containers_3D_children_align_order": [],	#for the moment, 3D Overlays order are user-order dependant for 3D containers
			"align_position": 0, #Index in parent["containers_2D_children_align_order"] - Used in sorting to find pointer focus
			"workspace_min": hg.Vec3(0, 0, 0), #Where workspace begins (could be < 0)
			"workspace_max": hg.Vec3(0, 0, 0),
			"workspace_size": hg.Vec3(0, 0, 0),
			"frame_buffer_size": hg.iVec2(0, 0),
			"scroll_position": hg.Vec3(0, 0, 0),	#Set with new_scroll_position at frame beginning
			"new_scroll_position": hg.Vec3(0, 0, 0), #Next frame scroll position
			"flag_scrollbar_v": False,
			"flag_scrollbar_h": False,
			"flag_hide_scrollbars": False,
			"color_texture": None,
			"depth_texture": None,
			"frame_buffer": None,	#Widgets rendering frame buffer
			"view_id": -1 #Container rendering view_id
		})
		return container


	@classmethod
	def create_component(cls,component_type):
		if component_type in HarfangUISkin.components:
			component = cls.new_component(component_type)
			component_model = HarfangUISkin.components[component_type]
			vec3_types = ["size_factor"] #fields that needs Vec3 copy
			for key, value in component_model.items():
				if key != "properties":
					if key in vec3_types:
						component[key] = hg.Vec3(value[0], value[1], value[2])
					else:
						component[key] = value
			if "display_text" in component:
				text_field = component["display_text"]
				component[text_field] = "undefined"
				component["display_text_size"] = hg.Vec3(0, 0, 0)
			if "input_text" in component:
				input_field = component["input_text"]
				component[input_field] = "undefined"
			for property_name in component_model["properties"]:
				if property_name in  HarfangUISkin.properties:
					class_property = HarfangUISkin.properties[property_name]
					# Creates layers occurences:
					component_layers = []
					for layer_id in range(len(class_property["layers"])):
						class_layer = class_property["layers"][layer_id]
						
						component_layer_states = {}
						for class_state_name, class_state in class_layer["states"].items():
							component_layer_states[class_state_name] = dict(class_state)
							v = class_state["value"]
							if class_property["type"] == "float":
								component_layer_states[class_state_name]["value"] = v
							elif class_property["type"] == "vec2":
								component_layer_states[class_state_name]["value"] = hg.Vec2(v[0], v[1])
							elif class_property["type"] == "vec3":
								component_layer_states[class_state_name]["value"] = hg.Vec3(v[0], v[1], v[2])
							elif class_property["type"] == "color":
								component_layer_states[class_state_name]["value"] = hg.Color(v[0], v[1], v[2], v[3])
						
						default_state_name = class_layer["default_state"]
						default_value = component_layer_states[default_state_name]["value"]
						if layer_id == 0:
							default_final_value = default_value
						else:
							if class_layer["operator"] == "set":
								default_final_value = default_value
							elif class_layer["operator"] == "add":
								default_final_value += default_value
							elif class_layer["operator"] == "multiply":
								default_final_value *= default_value

						component_layer = {"current_state":default_state_name, "current_state_t0":0, "value":default_value, "value_start":default_value, "value_end":default_value, "states":component_layer_states}
						component_layers.append(component_layer)
					
					component["properties"][property_name] = {"layers":component_layers, "value":default_final_value}
			return component
		return None


	@classmethod
	def create_widget(cls, widget_type, widget_id):
		
		# Widgets types of "widgets_container" classe:
		widgets_type_containers = ["window"]

		if widget_type in HarfangUISkin.widgets_models:
			components_order = []
			widget_model = HarfangUISkin.widgets_models[widget_type]
			for component_type in widget_model["components"]:
				component = cls.create_component(component_type)
				components_order.append(component)

			#Creation of a dictionnary to facilitate access to components
			components_dict = {}
			for component in components_order:
				components_dict[component["type"]] = component

			if widget_type in widgets_type_containers:
				widget = cls.new_widgets_container(widget_type)
			else:
				widget = cls.new_single_widget(widget_type)
			
			widget["widget_id"] = widget_id
			widget["components"] = components_dict
			widget["components_render_order"] = components_order
			widget["cursor_start_line"].x = widget["default_cursor_start_line"].x
			widget["cursor_start_line"].y = widget["default_cursor_start_line"].y
			widget["cursor_start_line"].z = widget["default_cursor_start_line"].z
			
			for key, value in widget_model.items():
				if key not in widget:
					widget[key] = value # !!! If Value is a Harfang Object, add a deepcopy
			return widget
		return None	


	@classmethod
	def get_widget(cls, widget_type, widget_id):
		if not widget_id in cls.widgets:
			widget = cls.create_widget(widget_type, widget_id)
			widget["flag_new"] = True
			cls.widgets[widget_id] = widget
		else:
			widget = cls.widgets[widget_id]
			widget["flag_new"] = False
		cls.add_widget_to_render_list(widget)
		return widget

	@classmethod
	def add_widget_to_render_list(cls, widget):
		container = HarfangGUISceneGraph.get_current_container()
		container["children_order"].append(widget)
		widget["parent_id"] = container["widget_id"]

	@classmethod
	def update_camera2D(cls):
		sp = cls.main_widgets_container_2D["scroll_position"]
		cls.camera2D_matrix = hg.TranslationMat4( sp * hg.Vec3(1, -1, 1))

	@classmethod
	def reset_main_containers(cls):
		for w_container in [cls.main_widgets_container_2D, cls.main_widgets_container_3D]:
			w_container["children_order"] = []
			w_container["child_depth"] = 0
			cp = w_container["cursor"]
			csl = w_container["cursor_start_line"]
			dcsl = w_container["default_cursor_start_line"]
			csl.x, csl.y, csl.z = cp.x, cp.y, cp.z = dcsl.x, dcsl.y, dcsl.z
			p = w_container["workspace_min"] 
			p.x, p.y, p.z = 0, 0, 0 #min(0, p.x), min(0, p.y), min(0, p.z)
			p = w_container["workspace_max"]
			p.x, p.y, p.z = w_container["size"].x, w_container["size"].y, w_container["size"].z  #max(p.x, w_container["size"].x), max(p.y, w_container["size"].y), max(p.z, w_container["size"].z)
			mdt = w_container["pointers"]["mouse"]["pointer_local_dt"]
			mdt.x, mdt.y = cls.mouse.DtX(), -cls.mouse.DtY()
			plp = w_container["pointers"]["mouse"]["pointer_local_position"]
			plp.x, plp.y = cls.mouse.X(), cls.mouse.Y()

	@classmethod
	def update_controllers(cls):
		# Mouse:
		cls.controllers["mouse"]["world_intersection"] = None
		if cls.flag_vr:
			cls.controllers["mouse"]["ray_p0"] = hg.GetT(cls.camera3D_matrix)
			if cls.flag_use_pointer_VR:
				MousePointer3D.update_vr(cls.vr_state, cls.mouse, cls.controllers["mouse"]["world_intersection"])
			else:
				MousePointer3D.update(cls.camera, cls.mouse, cls.width, cls.height)
			cls.controllers["mouse"]["ray_p1"] = hg.GetT(MousePointer3D.pointer_world_matrix)
		else:
			if cls.camera is None:
				cls.controllers["mouse"]["ray_p0"] = None
				cls.controllers["mouse"]["ray_p1"] = None
			else:
				cls.controllers["mouse"]["ray_p0"] = hg.GetT(cls.camera3D_matrix)
				MousePointer3D.update(cls.camera, cls.mouse, cls.width, cls.height)
				cls.controllers["mouse"]["ray_p1"] = hg.GetT(MousePointer3D.pointer_world_matrix)
		
		# VR controllers:
		if cls.flag_vr:
			VRControllersHandler.update_connected_controller()
		else:
			pass

	@classmethod
	def begin_frame(cls, dt, mouse: hg.Mouse, keyboard: hg.Keyboard, width: int, height: int, camera: hg.Node = None):
		
		cls.flag_vr = False

		cls.camera = camera
		cls.width = width
		cls.height = height

		cls.mouse = mouse
		cls.keyboard = keyboard
		cls.dt = dt
		cls.timestamp += dt
		cls.last_widget = None

		if camera is not None:
			cls.camera3D_matrix = camera.GetTransform().GetWorld()
			cls.focal_distance = hg.FovToZoomFactor(camera.GetCamera().GetFov())
		else:
			cls.focal_distance = 1
			cls.camera3D_matrix = None

		cls.update_controllers()

		cls.update_camera2D()
		
		cls.update_signals()
		# Pourquoi passer par les signaux internes pour indiquer que le bouton souris est down:
		# - Permet de déterminer le state en fonction de la localisation du pointeur (DOWN sur un widget != DOWN hors widget)
		if cls.mouse.Down(hg.MB_0):
			cls.send_signal("MLB_down")
		cls.reset_main_containers()
		HarfangGUISceneGraph.clear()
		
		return True
	
	@classmethod
	def begin_frame_vr(cls, dt, mouse: hg.Mouse, keyboard: hg.Keyboard, screenview_camera: hg.Node,  width: int, height: int, vr_state: hg.OpenVRState, left_fb: hg.FrameBuffer, right_fb: hg.FrameBuffer):
		
		cls.flag_vr = True

		cls.width = width
		cls.height = height

		cls.vr_state = vr_state
		cls.left_fb = left_fb
		cls.right_fb = right_fb
		cls.camera = screenview_camera

		cls.mouse = mouse
		cls.keyboard = keyboard

		cls.dt = dt
		cls.timestamp += dt
		cls.last_widget = None

		if cls.camera is not None:
			cls.focal_distance = hg.FovToZoomFactor(cls.camera.GetCamera().GetFov())
		else:
			cls.focal_distance = 1
		
		if cls.flag_use_pointer_VR:
			cls.focal_distance = hg.ExtractZoomFactorFromProjectionMatrix(vr_state.left.projection)
			cls.camera3D_matrix = vr_state.head
		else:
			cls.camera3D_matrix = screenview_camera.GetTransform().GetWorld()
			
		cls.update_controllers()

		cls.update_camera2D()
		
		cls.update_signals()
		# Pourquoi passer par les signaux internes pour indiquer que le bouton souris est down:
		# - Permet de déterminer le state en fonction de la localisation du pointeur (DOWN sur un widget != DOWN hors widget)
		if cls.mouse.Down(hg.MB_0):
			cls.send_signal("MLB_down")
		cls.reset_main_containers()
		HarfangGUISceneGraph.clear()

		return True

	@classmethod
	def end_frame(cls, vid):
		HarfangGUISceneGraph.set_containers3D_list()
		cls.build_widgets_container(hg.Mat4.Identity, cls.main_widgets_container_3D)
		HarfangGUISceneGraph.set_containers2D_list()
		cls.build_widgets_container(hg.Mat4.Identity, cls.main_widgets_container_2D)
		cls.update_align_positions(cls.main_widgets_container_2D, 0)
		cls.update_align_positions(cls.main_widgets_container_3D, 0)
		cls.update_widgets_inputs()

		#2D display
		p = hg.GetT(cls.camera2D_matrix) + hg.Vec3(cls.width / 2, -cls.height / 2, 0)
		view_state_2D = hg.ComputeOrthographicViewState(hg.TranslationMat4(p), cls.height, 1, 101, hg.ComputeAspectRatioX(cls.width, cls.height))
		outputs_2D = [HarfangGUIRenderer.create_output(hg.Vec2(cls.width, cls.height), view_state_2D, None)]

		#3D display
		outputs_3D = []
		if cls.camera is not None:
			cam = cls.camera.GetCamera()
			view_state_3D = hg.ComputePerspectiveViewState(cls.camera.GetTransform().GetWorld(), cam.GetFov(), cam.GetZNear(), cam.GetZFar(), hg.ComputeAspectRatioX(cls.width, cls.height))
			outputs_3D.append(HarfangGUIRenderer.create_output(hg.Vec2(cls.width, cls.height), view_state_3D, None))
		
		if cls.flag_vr:
			left, right = hg.OpenVRStateToViewState(cls.vr_state)
			vr_res = hg.Vec2(cls.vr_state.width, cls.vr_state.height)
			outputs_3D.append(HarfangGUIRenderer.create_output(vr_res, left, cls.left_fb))
			outputs_3D.append(HarfangGUIRenderer.create_output(vr_res, right, cls.right_fb))

		HarfangGUISceneGraph.sort_widgets_containers()

		vid, render_views_3D, render_views_2D = HarfangGUIRenderer.render(vid, outputs_2D, outputs_3D)
		if cls.flag_vr:
			VRControllersHandler.update_displays(render_views_3D)
			if cls.flag_use_pointer_VR:
				fov = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(cls.vr_state.left.projection))
				ry = cls.vr_state.height
				view_pos =hg.GetT(cls.vr_state.head)
				MousePointer3D.draw_pointer(render_views_3D, ry, view_pos, fov, cls.controllers["mouse"]["world_intersection"])

		return vid
	
	@classmethod
	def send_signal(cls, signal_id, widget_id = None):
		#New signal will be dispatched at next frame
		if signal_id not in cls.new_signals:
			cls.new_signals[signal_id] = []
		if signal_id == "MLB_down":
			if "MLB_down" not in cls.current_signals and "MLB_pressed" not in cls.new_signals:
				cls.new_signals["MLB_pressed"] = []
		
		if widget_id is not None:
			if widget_id not in cls.new_signals[signal_id]:
				cls.new_signals[signal_id].append(widget_id)
			if signal_id == "MLB_down":
				if "MLB_pressed" in cls.new_signals and widget_id not in cls.new_signals["MLB_pressed"]:
					cls.new_signals["MLB_pressed"].append(widget_id)
		
	@classmethod
	def update_signals(cls):
		cls.current_signals = cls.new_signals
		cls.new_signals = {}

# ------------ Widgets containers system (windows are particular widgets containers)
	@classmethod
	def get_parent_container(cls, container):
		parent_id = container["parent_id"]
		if parent_id == "MainContainer3D":
			return cls.main_widgets_container_3D
		elif parent_id == "MainContainer2D":
			return cls.main_widgets_container_2D
		return cls.widgets[parent_id]

	@classmethod
	def push_widgets_container(cls, w_container):
		
		HarfangGUISceneGraph.widgets_containers_stack.append(w_container)
		w_container["children_order"] = []
		w_container["child_depth"] = len(HarfangGUISceneGraph.widgets_containers_stack) - 1 # First child depth = 1, 0 is Main Widget container
		if w_container["flag_new"]:
			parent = cls.get_parent_container(w_container)
			if w_container["flag_2D"]:
				parent["containers_2D_children_align_order"].insert(0, w_container)	# !!! Even if they are no longer displayed by user, the containers remain in this list. !!!
			else:
				parent["containers_3D_children_align_order"].insert(0, w_container)	# !!! Even if they are no longer displayed by user, the containers remain in this list. !!!
		cls.set_cursor_start_line(w_container["default_cursor_start_line"])
		cls.set_cursor_pos(w_container["default_cursor_start_line"])
		p = w_container["workspace_min"] 
		p.x, p.y, p.z = 0, 0, 0 #min(0, p.x), min(0, p.y), min(0, p.z)
		p = w_container["workspace_max"]
		p.x, p.y, p.z = w_container["size"].x, w_container["size"].y, w_container["size"].z  #max(p.x, w_container["size"].x), max(p.y, w_container["size"].y), max(p.z, w_container["size"].z)
	
	@classmethod
	def pop_widgets_container(cls):
		if  len(HarfangGUISceneGraph.widgets_containers_stack) > 0:
			return HarfangGUISceneGraph.widgets_containers_stack.pop()
		return None

	@classmethod
	def set_scroll_position(cls, widget_id, x, y, z):
		if widget_id in cls.widgets:
			widget = cls.widgets[widget_id]
			scroll_max = widget["workspace_min"] + widget["workspace_size"] - widget["size"]
			widget["new_scroll_position"].x = max(widget["workspace_min"].x, min(x, scroll_max.x))
			widget["new_scroll_position"].y = max(widget["workspace_min"].y, min(y, scroll_max.y))
			widget["new_scroll_position"].z = max(widget["workspace_min"].z, min(z, scroll_max.z))

	
	
	@classmethod
	def move_widgets_container(cls, widgets_container, pointer_id):
		parent = cls.get_parent_container(widgets_container)
		wc_pointer = widgets_container["pointers"][pointer_id]
		p_pointer = parent["pointers"][pointer_id]
		pointer_dt = p_pointer["pointer_local_dt"]
		
		if parent["widget_id"] == "MainContainer3D":
			if wc_pointer["pointer_world_position"] is not None:
				rotmat = hg.GetRotationMatrix(cls.camera3D_matrix)
				ax = hg.GetX(rotmat)
				ay = hg.GetY(rotmat)
				
				height = cls.height
				
				if cls.flag_vr:
					if pointer_id !="mouse" or (pointer_id == "mouse" and cls.flag_use_pointer_VR):
						height = cls.vr_state.height
					
				mdt = (pointer_dt) * (hg.Len(wc_pointer["pointer_world_position"] - hg.GetT(cls.camera3D_matrix)) / cls.focal_distance ) * 2 / height

				v =  (ax * mdt.x) - (ay * mdt.y)
				v.y *= -1

				widgets_container["position"] += v
		else:
			wpos = widgets_container["position"]
		
			if parent["scroll_position"].x < p_pointer["pointer_local_position"].x < parent["size"].x + parent["scroll_position"].x :
				wpos.x = wpos.x + pointer_dt.x
			if parent["scroll_position"].y < p_pointer["pointer_local_position"].y < parent["size"].y + parent["scroll_position"].y :
				wpos.y = wpos.y + pointer_dt.y
	
	@classmethod
	def begin_window_2D(cls, widget_id, position:hg.Vec2, size:hg.Vec2, scale:float = 1, window_flags:int = 0):
		return cls.begin_window(widget_id, hg.Vec3(position.x, position.y, 0), hg.Vec3(0, 0, 0), hg.Vec3(size.x, size.y, 0), scale, window_flags | cls.HGUIWF_2D)	# size: in pixels
	# scale: pixel size
	@classmethod
	def begin_window(cls, widget_id, position:hg.Vec3 , rotation:hg.Vec3, size:hg.Vec3, scale:float = 1, window_flags:int = 0):
		
		flag_2D = False if (window_flags & cls.HGUIWF_2D) == 0 else True
		flag_move = True if (window_flags & cls.HGUIWF_NoPointerMove) == 0 else False
		flag_hide_title = False if (window_flags & cls.HGUIWF_HideTitle) == 0 else True
		flag_invisible = False if (window_flags & cls.HGUIWF_Invisible) == 0 else True
		flag_hide_scrollbars = False if (window_flags & cls.HGUIWF_HideScrollbars) == 0 else True

		# If first parent window is 3D, Y is space relative, Y-increment is upside. Else, Y-increment is downside
		pyf, rxf, rzf = 1, 1, 1
		if not flag_2D:
			if HarfangGUISceneGraph.get_current_container_child_depth() == 0:
				pyf = -1
				rxf *= -1
				rzf *= -1
				HarfangGUISceneGraph.widgets_containers_stack.append(cls.main_widgets_container_3D)
			else:
				parent = HarfangGUISceneGraph.get_current_container()
				if parent is not None and parent["flag_2D"]:
					print("HarfangGUI ERROR - 3D container can't be child of 2D container - " + widget_id)
					return False
		else:
			if HarfangGUISceneGraph.get_current_container_child_depth() == 0:
				HarfangGUISceneGraph.widgets_containers_stack.append(cls.main_widgets_container_2D)
		
		widget = cls.get_widget("window", widget_id)
		
		widget["flag_2D"] = flag_2D
		widget["flag_move"] = flag_move
		widget["flag_hide_title"] = flag_hide_title
		widget["flag_invisible"] = flag_invisible
		widget["flag_hide_scrollbars"] = flag_hide_scrollbars
		
		nsp = widget["new_scroll_position"]
		sp = widget["scroll_position"]
		sp.x, sp.y, sp.z = nsp.x, nsp.y, nsp.z
		
		if widget["flag_new"]:
			widget["position"].x, widget["position"].y, widget["position"].z = position.x, position.y * pyf, position.z
			widget["rotation"].x, widget["rotation"].y, widget["rotation"].z = rotation.x * rxf, rotation.y, rotation.z * rzf
			widget["scale"].x =  widget["scale"].y = widget["scale"].z = scale
			
			s = widget["size"]
			s.x, s.y, s.z = size.x, size.y, size.z
			
			thickness = 0 if flag_invisible else cls.get_property_states_value(widget["components"]["window_background"], "window_box_border_thickness",["focus"] )
			widget["default_cursor_start_line"].x = 5 + thickness
			widget["default_cursor_start_line"].y = 5 + thickness
			widget["components"]["window_title"]["label"] = cls.get_label_from_id(widget["widget_id"])
		
		else:
			if not flag_move:
				widget["position"].x, widget["position"].y, widget["position"].z = position.x, position.y * pyf, position.z
				widget["rotation"].x, widget["rotation"].y, widget["rotation"].z = rotation.x * rxf, rotation.y, rotation.z * rzf

			if not (flag_hide_title or flag_invisible):
				widget["default_cursor_start_line"].y = 5 + widget["components"]["window_title"]["size"].y

			if "mouse_move" in widget["states"]:
				if "MLB_down" not in cls.current_signals:
					cls.set_widget_state(widget, "mouse_idle")
					cls.set_ui_state(cls.UI_STATE_MAIN)
				elif cls.ui_state == cls.UI_STATE_WIDGET_MOUSE_FOCUS:
					cls.move_widgets_container(widget, "mouse")
					
			else:		
				if widget["flag_move"] and "MLB_pressed" in cls.current_signals and widget["widget_id"] in cls.current_signals["MLB_pressed"]:
					cls.set_widget_state(widget, "mouse_move")
					cls.set_ui_state(cls.UI_STATE_WIDGET_MOUSE_FOCUS)
		
		cls.push_widgets_container(widget)
		return True


	@classmethod
	def end_window(cls):
		if len(HarfangGUISceneGraph.widgets_containers_stack) <= 1:
			print("HarfangGUI ERROR - Widgets containers stack is empty !")
		else:
			scrollbar_size = 20
			widget = HarfangGUISceneGraph.get_current_container()

			#Update workspace
			# Windows2D move don't affect scrollbars. Scrollbars only concerns simple widgets.
			"""
			if len(widget["containers_2D_children_align_order"]) > 0:
				wsmn = widget["workspace_min"]
				wsmx = widget["workspace_max"]
				for wc in widget["containers_2D_children_align_order"]:
					wsmn.x = min(wsmn.x, wc["position"].x)
					wsmn.y = min(wsmn.y, wc["position"].y)
					wsmn.z = min(wsmn.z, wc["position"].z)
					cmx = wc["position"] + wc["size"]
					wsmx.x = max(wsmx.x,cmx.x)
					wsmx.y = max(wsmx.y,cmx.y)
					wsmx.z = max(wsmx.z,cmx.z)
			"""
			
			w_size = widget["size"]
			mn = widget["workspace_min"]
			mx = widget["workspace_max"]
			widget["workspace_size"] = mx - mn
			ws_size = widget["workspace_size"]
		
			# Scroll bars

			spx = spy = None
			flag_reset_bar_v = flag_reset_bar_h = False

			if widget["flag_hide_scrollbars"]:
				widget["flag_scrollbar_v"] = False
				widget["flag_scrollbar_h"] = False
			else:
				# Vertical
				if ws_size.y > w_size.y:
					mx.y += scrollbar_size * 2
					ws_size.y += scrollbar_size * 2
					if not widget["flag_scrollbar_v"]:
						spy = widget["scroll_position"].y - mn.y
						flag_reset_bar_v = True
					widget["flag_scrollbar_v"] = True
				else:
					widget["flag_scrollbar_v"] = False
				
				# Horizontal
				if ws_size.x > w_size.x:
					mx.x += scrollbar_size * 2
					ws_size.x += scrollbar_size * 2
					if not widget["flag_scrollbar_h"]:
						spx = widget["scroll_position"].x - mn.x
						flag_reset_bar_h = True
					widget["flag_scrollbar_h"] = True
				else:
					widget["flag_scrollbar_h"] = False

			# clamp scroll position

			spos = widget["scroll_position"]
			spos.x = min(mx.x - w_size.x, max(spos.x, mn.x))
			spos.y = min(mx.y - w_size.y, max(spos.y, mn.y))
			spos.z = min(mx.z - w_size.z, max(spos.z, mn.z))

			bt = 0 if widget["flag_invisible"] else cls.get_property_value(widget["components"]["window_background"],"window_box_border_thickness")
			
			# Add scroll bars if necessary

			px, py = widget["scroll_position"].x - mn.x, widget["scroll_position"].y - mn.y

			if widget["flag_scrollbar_v"]:
				title_height = bt if (widget["flag_hide_title"] or widget["flag_invisible"])  else widget["components"]["window_title"]["size"].y
				cursor = hg.Vec3(spos)
				cursor.x += w_size.x - scrollbar_size - bt
				cursor.y += title_height
				cls.set_cursor_pos(cursor)
				height = w_size.y - (bt + title_height)
				py = cls.scrollbar_v(widget["widget_id"] + ".scoll_v", scrollbar_size, height, w_size.y, ws_size.y, spy, flag_reset_bar_v) + mn.y
			
			if widget["flag_scrollbar_h"]:
				cursor = hg.Vec3(spos)
				cursor.y += w_size.y - scrollbar_size - bt
				cursor.x += bt
				cls.set_cursor_pos(cursor)
				width = w_size.x - 2 * bt if ws_size.y <= w_size.y else w_size.x - 2 * bt - scrollbar_size
				px = cls.scrollbar_h(widget["widget_id"] + ".scoll_h", width, scrollbar_size, w_size.x, ws_size.x, spx, flag_reset_bar_h) + mn.x

			cls.set_scroll_position(widget["widget_id"], px, py, 0)

			cls.pop_widgets_container()
			
			# Remove Main container if root window:
			if HarfangGUISceneGraph.get_current_container_child_depth() == 1:
				cls.pop_widgets_container() 

			cls.update_widget_components(widget)


# ------------ Widgets system

	@classmethod
	def same_line(cls):
		cls.flag_same_line= True
		cursor = HarfangGUISceneGraph.get_current_container()["cursor"]
		cursor.x = cls.last_widget["position"].x + cls.last_widget["size"].x + cls.last_widget["offset"].x
		cursor.y = cls.last_widget["position"].y + cls.last_widget["offset"].y
		cursor.z = cls.last_widget["position"].z + cls.last_widget["offset"].z
	
	@classmethod
	def set_line_space_size(cls,line_space_size:float):
		cls.line_space_size = line_space_size

	@classmethod
	def get_cursor_position(cls):
		current_container = HarfangGUISceneGraph.get_current_container()
		return hg.Vec3(current_container["cursor"])

	@classmethod
	def set_cursor_pos(cls, position: hg.Vec3):
		cursor = HarfangGUISceneGraph.get_current_container()["cursor"]
		cursor.x, cursor.y, cursor.z = position.x, position.y, position.z
	
	@classmethod
	def set_cursor_start_line(cls, position: hg.Vec3):
		csl = HarfangGUISceneGraph.get_current_container()["cursor_start_line"]
		csl.x, csl.y, csl.z = position.x, position.y, position.z

	@classmethod
	def update_cursor(cls, widget):
		w_container = HarfangGUISceneGraph.get_current_container()
		cursor = w_container["cursor"]
		csl = w_container["cursor_start_line"]
		cursor.x = csl.x
		if not cls.flag_same_line:
			cls.line_max_y_size = 0
		else:
			cls.flag_same_line = False
		cls.line_max_y_size = max(cls.line_max_y_size, widget["size"].y + widget["offset"].y)
		cursor.y = widget["position"].y + cls.line_max_y_size + cls.line_space_size
		cursor.z = csl.z

		wpos_s = widget["position"] + widget["offset"]
		wpos_e = wpos_s + widget["max_size"]
		wss, wse = w_container["workspace_min"], w_container["workspace_max"]
		wss.x = min(wss.x, wpos_s.x)
		wss.y = min(wss.y, wpos_s.y)
		wss.z = min(wss.z, wpos_s.z)
		
		wse.x = max(wse.x, wpos_e.x)
		wse.y = max(wse.y, wpos_e.y)
		wse.z = max(wse.z, wpos_e.z)

		cls.last_widget = widget

	@classmethod
	def update_widget_states(cls, widget):
		widget["states"] = []
		for component in widget["components_render_order"]:
			component["states"] = []
			for component_property in component["properties"].values():
				for layer_id in range(len(component_property["layers"])):
					property_layer_state = component_property["layers"][layer_id]["current_state"]
					if property_layer_state not in widget["states"]:
						widget["states"].append(property_layer_state)
					if property_layer_state not in component["states"]:
						component["states"].append(property_layer_state)


	@classmethod
	def set_widget_state(cls, widget, state_name):
		for component in widget["components_render_order"]:
			for component_property in component["properties"].values():
				for layer_id in range(len(component_property["layers"])):
					property_layer = component_property["layers"][layer_id]
					if state_name in property_layer["states"]:
						if property_layer["current_state"] != state_name:
							if state_name == "focus":
								cls.current_focused_widget = widget
							elif state_name == "no_focus":
								if cls.current_focused_widget == widget:
									cls.current_focused_widget = None
							property_layer["current_state"] = state_name
							property_layer["current_state_t0"] = cls.timestamp
							property_layer["value_start"] = property_layer["value"]
							property_layer["value_end"] = property_layer["states"][state_name]["value"]

						
	@classmethod
	def mouse_hover(cls, widget, pointer_pos):
		if cls.ui_state is not cls.UI_STATE_WIDGET_MOUSE_FOCUS:
			if widget["position"].x < pointer_pos.x < widget["position"].x + widget["size"].x + widget["offset"].x and widget["position"].y < pointer_pos.y < widget["position"].y + widget["size"].y + widget["offset"].y:
				if not ("mouse_hover" in cls.current_signals and widget["widget_id"] in cls.current_signals["mouse_hover"]):
					if not "edit" in widget["states"]:
						cls.set_widget_state(widget, "mouse_hover")
				cls.send_signal("mouse_hover", widget["widget_id"])
				return True
			else:
				cls.set_widget_state(widget, "idle")
				return False
		return False
	
	@classmethod
	def update_mouse_click(cls, widget):
		if "mouse_hover" in cls.current_signals and widget["widget_id"] in cls.current_signals["mouse_hover"]:
			if cls.mouse.Down(hg.MB_0):
				if not "edit" in widget["states"]:
					cls.set_widget_state(widget, "MLB_down")
				cls.send_signal("MLB_down", widget["widget_id"])
			
			elif "MLB_down" in cls.current_signals and widget["widget_id"] in cls.current_signals["MLB_down"]:
				if not "edit" in widget["states"]:
					cls.set_widget_state(widget, "mouse_hover")
				cls.send_signal("mouse_click", widget["widget_id"])

	@classmethod
	def update_component_properties(cls, widget, component):
		flag_text = False
		text_field = ""
		if "display_text" in component:
			text_field = component["display_text"]
			flag_text = True
		if flag_text:
			txt_size = HarfangGUIRenderer.compute_text_size(cls.current_font_id, component[text_field])
			if "forced_text_width" in component and component["forced_text_width"] is not None:
				txt_size.x = component["forced_text_width"]
			component["size"] = hg.Vec3(txt_size.x, txt_size.y, 0)
			if "text_size" in component:
				component["size"] *= component["text_size"]
			component["display_text_size"].x, component["display_text_size"].y = component["size"].x, component["size"].y #Keep the string size for special displays (keyboard cursor for inputs widgets...)
		
		for property_name, component_property in component["properties"].items():
			if property_name in HarfangUISkin.properties:
				class_property = HarfangUISkin.properties[property_name]
				for layer_id in range(len(component_property["layers"])):
					class_layer = class_property["layers"][layer_id]
					property_layer = component_property["layers"][layer_id]
					state_delay = property_layer["states"][property_layer["current_state"]]["delay"]
					if abs(state_delay) < 1e-5:
						property_layer["value"] = property_layer["value_end"]
					else:
						t = (cls.timestamp - property_layer["current_state_t0"]) / hg.time_from_sec_f(state_delay)
						property_layer["value"] = HarfangUISkin.interpolate_values(property_layer["value_start"], property_layer["value_end"], t)
					if class_layer["operator"] == "set":
						component_property["value"] = property_layer["value"]
					elif class_layer["operator"] == "multiply":
						component_property["value"] *= property_layer["value"]
					elif class_layer["operator"] == "add":
						component_property["value"] += property_layer["value"]
		
				if "linked_value" in class_property:
					lv = class_property["linked_value"]
					
					if "parent" in lv:
						parent_classe = lv["parent"]
						if parent_classe == "widget":
							obj = widget
						elif parent_classe == "component":
							obj = component
						else:
							obj = component
					else:
						obj = component
					
					if lv["name"] in obj:
						v = component_property["value"]
						if "factor" in lv:
							v *= lv["factor"]
						if lv["operator"] == "set":
							obj[lv["name"]] = v
						elif lv["operator"] == "add":
							obj[lv["name"]] += v

		sf = component["size_factor"]
		if sf.x > 0:
			component["size"].x = max(component["size"].x, widget["size"].x * sf.x)
		if sf.y > 0:
			component["size"].y = max(component["size"].y, widget["size"].y * sf.y)
		if sf.z > 0:
			component["size"].z = max(component["size"].z, widget["size"].z * sf.z)
			


	@classmethod
	def update_widget_components(cls, widget):
		mn = hg.Vec3(inf, inf, inf)
		mx = hg.Vec3(-inf, -inf, -inf)
		if widget["classe"] == "widgets_container":
			cursor_pos = hg.Vec3.Zero
		else:
			cursor_pos = widget["cursor_start_line"]
		widget["cursor"].x, widget["cursor"].y, widget["cursor"].z = cursor_pos.x, cursor_pos.y, cursor_pos.z
		for component in widget["components_render_order"]:
			if component["cursor_auto"]:
				component["position"] = hg.Vec3(widget["cursor"])
			cls.update_component_properties(widget, component)
			
			#update widget size:
			cmnx = component["position"].x if component["offset"].x > 0 else component["position"].x + component["offset"].x
			cmny = component["position"].y if component["offset"].y > 0 else component["position"].y + component["offset"].y
			cmnz = component["position"].z if component["offset"].z > 0 else component["position"].z + component["offset"].z
			mn.x = min(mn.x, cmnx)
			mn.y = min(mn.y, cmny)
			mn.z = min(mn.z, cmnz)
			cmx = component["position"] + component["offset"] + component["size"]
			mx.x = max(mx.x,cmx.x)
			mx.y = max(mx.y,cmx.y)
			mx.z = max(mx.z,cmx.z)
			
			#Next component position: # Simple alignement sur X, à développer pour des widgets plus complexes.
			if component["cursor_auto"]:
				widget["cursor"] += hg.Vec3(component["size"].x, 0, 0) + component["offset"]
		ws = mx - mn
		widget["size"] = ws
		wsm = widget["max_size"]
		wsm.x, wsm.y, wsm.z = max(wsm.x, ws.x), max(wsm.y, ws.y), max(wsm.z, ws.z)

	@classmethod
	def build_widgets_container(cls, matrix, widgets_container):
		if widgets_container["type"] != "Main_container":
			HarfangGUISceneGraph.add_widgets_container(widgets_container)
			widgets_container["local_matrix"] =  hg.TransformationMat4(widgets_container["position"] + widgets_container["offset"], widgets_container["rotation"], widgets_container["scale"])		
			widgets_container["world_matrix"] =  matrix * widgets_container["local_matrix"]	

			cls.build_widget(widgets_container, hg.Mat4.Identity, widgets_container)
		
		#containers_2D_children = []
		for widget in widgets_container["children_order"]:
			if widget["classe"] =="widgets_container":
				cls.build_widgets_container(widgets_container["world_matrix"], widget)
				#if widget["flag_2D"]:
				#	containers_2D_children.append(widget)
			else:
				widget["local_matrix"] = hg.TransformationMat4(widget["position"] + widget["offset"], widget["rotation"], widget["scale"])
				widget["world_matrix"] = widgets_container["world_matrix"] * widget["local_matrix"]
				cls.build_widget(widgets_container, widget["local_matrix"], widget)

		if widgets_container["type"] != "Main_container":
			HarfangGUISceneGraph.set_container_display_list(widgets_container["widget_id"])
			if len(widgets_container["containers_2D_children_align_order"]) > 0:
				cls.build_widgets_container_2Dcontainers(widgets_container, widgets_container["containers_2D_children_align_order"])
			if not widgets_container["flag_invisible"]:
				cls.build_widgets_container_overlays(widgets_container, hg.Mat4.Identity)

		fb_size = widgets_container["frame_buffer_size"]

		fb_size_x = int(widgets_container["size"].x)
		fb_size_y = int(widgets_container["size"].y)
		if fb_size_x != fb_size.x or fb_size_y != fb_size.y:
			if widgets_container["frame_buffer"] is not None:
				hg.DestroyFrameBuffer(widgets_container["frame_buffer"])
				hg.DestroyTexture(widgets_container["color_texture"])
				hg.DestroyTexture(widgets_container["depth_texture"])
			fb_size.x, fb_size.y = fb_size_x, fb_size_y

		if widgets_container["frame_buffer"] is None:
			
			widgets_container["color_texture"] = hg.CreateTexture(fb_size.x, fb_size.y, widgets_container["widget_id"] + "_ctex", hg.TF_RenderTarget, hg.TF_RGBA8)
			widgets_container["depth_texture"] =  hg.CreateTexture(fb_size.x, fb_size.y, widgets_container["widget_id"] + "_dtex", hg.TF_RenderTarget, hg.TF_D32F)
			widgets_container["frame_buffer"] = hg.CreateFrameBuffer(widgets_container["color_texture"], widgets_container["depth_texture"], widgets_container["widget_id"] + "_fb")
	
	@classmethod
	def build_widgets_container_2Dcontainers(cls, widgets_container, containers_2D_children):
		#call AFTER build_widget(), and BEFORE build_widgets_container_overlays()
		#widget states already updated
		for container in reversed(containers_2D_children):
			if container["widget_id"] in cls.widgets: #Controls if container updated by user in this frame
				color = hg.Color(1, 1, 1, container["opacity"])
				HarfangGUISceneGraph.add_texture_box(container["local_matrix"], hg.Vec3(0, 0, 0), container["size"], color, container["color_texture"], "rendered_texture_box")


	@classmethod
	def build_widgets_container_overlays(cls, widgets_container, matrix):
		#call AFTER build_widgets_container_2Dcontainers()
		#widget states already updated
		scroll_pos = widgets_container["scroll_position"]
		opacity = hg.Color(1, 1, 1, widgets_container["opacity"])
		for component in widgets_container["components_render_order"]:

			cpos = component["position"] + component["offset"] + scroll_pos

			if  component["type"]=="window_background":
				HarfangGUISceneGraph.add_box_border(matrix, cpos, component["size"], cls.get_property_value(component,"window_box_border_thickness"), cls.get_property_value(component,"window_box_border_color") * opacity)
			
			elif component["type"] == "window_title":
				if not widgets_container["flag_hide_title"]:
					HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"window_box_border_color") * opacity)
					HarfangGUISceneGraph.add_text(matrix, cpos + component["size"] / 2, component["text_size"], component[component["display_text"]], cls.current_font_id, cls.get_property_value(component,"window_title_color") * opacity)

	@classmethod
	def build_widget(cls, widgets_container, matrix, widget):

		HarfangGUISceneGraph.set_container_display_list(widgets_container["widget_id"])
		cls.update_widget_states(widget)
		
		opacity = hg.Color(1, 1, 1, 1 if widget["classe"] == "widgets_container" else widget["opacity"])
		
		#matrix = widget["world_matrix"]
		
		if "scroll_position" in widget:
			scroll_pos = widget["scroll_position"]
		else:
			scroll_pos = hg.Vec3.Zero

		for component in widget["components_render_order"]:

			cpos = component["position"] + component["offset"] + scroll_pos
			
			if  component["type"]=="window_background":
				if not widget["flag_invisible"]:
					HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"window_box_color") * opacity)
			
			elif component["type"]=="button_box":
				HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"button_box_color") * opacity)
				HarfangGUISceneGraph.add_text(matrix, cpos + component["size"] / 2, component["text_size"], component[component["display_text"]], cls.current_font_id, cls.get_property_value(component,"button_text_color") * opacity)
				HarfangGUISceneGraph.add_box_border(matrix, cpos, component["size"], cls.get_property_value(component,"widget_border_thickness"), cls.get_property_value(component,"widget_border_color") )
			
			elif component["type"] == "info_text":
				HarfangGUISceneGraph.add_text(matrix, cpos + component["size"] / 2, component["text_size"], component[component["display_text"]], cls.current_font_id, cls.get_property_value(component,"info_text_color") * opacity)

			elif component["type"] == "image_button":
				margins = cls.get_property_value(component,"button_image_margins")
				HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"button_box_color") * opacity)
				HarfangGUISceneGraph.add_texture_box(matrix, cpos + margins, component["size"] - margins * 2, cls.get_property_value(component,"texture_box_color") * opacity, component["texture"])
				HarfangGUISceneGraph.add_box_border(matrix, cpos, component["size"], cls.get_property_value(component,"widget_border_thickness"), cls.get_property_value(component,"widget_border_color") )
			
			elif component["type"] == "radio_image_button":
				margins = cls.get_property_value(component,"radio_button_image_margins")
				HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"radio_button_box_color") * opacity)
				HarfangGUISceneGraph.add_texture_box(matrix, cpos + margins, component["size"] - margins * 2, cls.get_property_value(component,"texture_box_color") * opacity, component["texture"])
				HarfangGUISceneGraph.add_box_border(matrix, cpos, component["size"], cls.get_property_value(component,"radio_image_border_thickness"), cls.get_property_value(component,"radio_image_border_color"))
			
			elif component["type"]=="toggle_button_box":
				HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"button_box_color") * opacity)
				HarfangGUISceneGraph.add_text(matrix, cpos + component["size"] / 2, component["text_size"], component[component["display_text"]], cls.current_font_id, cls.get_property_value(component,"button_text_color") * opacity)
				HarfangGUISceneGraph.add_box_border(matrix, cpos, component["size"], cls.get_property_value(component,"widget_border_thickness"), cls.get_property_value(component,"widget_border_color") )
			
			elif component["type"] == "toggle_image_button":
				margins = cls.get_property_value(component,"toggle_image_button_margins")
				HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"toggle_image_button_box_color") * opacity)
				HarfangGUISceneGraph.add_texture_box(matrix, cpos + margins, component["size"] - margins * 2, cls.get_property_value(component,"toggle_image_button_texture_box_color") * opacity, component["textures"][widget["toggle_idx"]])
				HarfangGUISceneGraph.add_box_border(matrix, cpos, component["size"], cls.get_property_value(component,"toggle_image_button_border_thickness"), cls.get_property_value(component,"toggle_image_button_border_color") )


			elif component["type"] == "info_image":
				margins = cls.get_property_value(component,"info_image_margins")
				HarfangGUISceneGraph.add_texture_box(matrix, cpos + margins, component["size"] - margins * 2, cls.get_property_value(component,"texture_box_color") * opacity, component["texture"])

			elif component["type"] == "check_box":
				margins = cls.get_property_value(component,"checkbox_margins")
				HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"button_box_color") * opacity)
				HarfangGUISceneGraph.add_texture_box(matrix, cpos + margins, cls.get_property_value(component,"check_size"), cls.get_property_value(component,"check_color") * opacity, component["texture"])
			
			elif component["type"] == "label_box":
				HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"label_box_color") * opacity)
				HarfangGUISceneGraph.add_text(matrix, cpos + component["size"] / 2, component["text_size"], component[component["display_text"]], cls.current_font_id,  cls.get_property_value(component,"label_text_color") * opacity)
			
			elif component["type"] == "input_box":
				HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"input_box_color") * opacity)
				HarfangGUISceneGraph.add_text(matrix, cpos + component["size"] / 2, component["text_size"], component[component["display_text"]], cls.current_font_id,  cls.get_property_value(component,"input_text_color") * opacity)
				#Draw keyboard cursor:
				if "edit" in component["states"]:
					tc_txt = component["edit_text"][:cls.kb_cursor_pos]
					tc_size = HarfangGUIRenderer.compute_text_size(cls.current_font_id, tc_txt)
					if "text_size" in component:
						tc_size *= component["text_size"]
					p = cpos + component["size"] / 2 - component["display_text_size"] / 2
					p.x += tc_size.x
					HarfangGUISceneGraph.add_box(matrix,  p, hg.Vec3(2, component["display_text_size"].y, 0), HarfangUISkin.keyboard_cursor_color * opacity)
			
			elif component["type"]=="scrollbar":
				if widget["type"] == "scrollbar_v":
					bar_width = cls.get_property_value(component,"scrollbar_thickness")
					margin = max(0, component["size"].x - bar_width)
					s = component["size"].y - margin
					bar_height = widget["part_size"] / widget["total_size"] * s
					bar_pos = hg.Vec3(margin / 2, margin / 2 + widget["scrollbar_position"] / widget["total_size"] * s, 0)
					
				elif widget["type"] == "scrollbar_h":
					bar_height = cls.get_property_value(component,"scrollbar_thickness")
					margin = max(0, component["size"].y - bar_height)
					s = component["size"].x - margin
					bar_width = widget["part_size"] / widget["total_size"] * s
					bar_pos = hg.Vec3(margin / 2 + widget["scrollbar_position"] / widget["total_size"] * s, margin / 2, 0)
				else:
					margin = 0
				margins = hg.Vec2(margin, margin)
				HarfangGUISceneGraph.add_box(matrix, cpos, component["size"], cls.get_property_value(component,"scrollbar_background_color") * opacity)
				HarfangGUISceneGraph.add_box(matrix, cpos + bar_pos, hg.Vec3(bar_width, bar_height, 0), cls.get_property_value(component,"scrollbar_color") * opacity)
	
	@classmethod
	def activate_pointer_VR(cls, flag: bool):
		cls.flag_use_pointer_VR = flag

	@classmethod
	def set_container_align_front(cls,container):
		#For the moment, only 2D container are aligned to front
		if container["flag_2D"]:
			parent = cls.get_parent_container(container)
			if parent["type"] != "Main_container":
						cls.set_container_align_front(parent)
			for i, w in enumerate(parent["containers_2D_children_align_order"]):
				if w == container:
					
					if i > 0:
						parent["containers_2D_children_align_order"].pop(i)
						parent["containers_2D_children_align_order"].insert(0, container)
					break

	@classmethod
	def update_align_positions(cls, widgets_container, align_position):
		for container in widgets_container["containers_2D_children_align_order"]:
			align_position = cls.update_align_positions(container, align_position)
		if widgets_container["flag_2D"]:
			widgets_container["align_position"] = align_position
			align_position += 1
		else:
			for container in widgets_container["containers_3D_children_align_order"]:
				align_position = cls.update_align_positions(container, align_position)
		return align_position

	@classmethod
	def update_widgets_inputs(cls):
		
		cls.focussed_containers = []

		focussed_container = cls.raycast_pointer_position("mouse")
		
		if focussed_container is not None:
			
			cls.focussed_containers.append(focussed_container)

			pointer_position = hg.Vec2(focussed_container["pointers"]["mouse"]["pointer_local_position"])
			
			if focussed_container["flag_invisible"]:
				title_height = 0
			elif focussed_container["flag_hide_title"]:
				title_height = cls.get_property_value(focussed_container["components"]["window_background"],"window_box_border_thickness")
			else:
				title_height = focussed_container["components"]["window_title"]["size"].y

			if pointer_position.y < title_height:
				flag_hover_container = True # flag_hover_container: True if only container is hoverd, and no container's child
			else:
				flag_hover_container = False
			
			pointer_position.x += focussed_container["scroll_position"].x
			pointer_position.y += focussed_container["scroll_position"].y
			
			flag_hover_widget = False
			for widget in reversed(focussed_container["children_order"]):
				if flag_hover_widget or flag_hover_container:
					cls.set_widget_state(widget, "idle")
				else:
					flag_hover_widget = cls.mouse_hover(widget, pointer_position)
					cls.update_mouse_click(widget)
			
			if not flag_hover_widget:
				flag_hover_container = True

			if cls.ui_state is not cls.UI_STATE_WIDGET_MOUSE_FOCUS:
				cls.set_widget_state(focussed_container, "mouse_hover")
				cls.send_signal("mouse_hover", focussed_container["widget_id"])
				if flag_hover_container:
					cls.update_mouse_click(focussed_container)
			
			if "MLB_pressed" in cls.current_signals:
				cls.set_widget_state(focussed_container, "focus")
				cls.set_container_align_front(focussed_container)
				
		# Unfocus containers
		w_containers = HarfangGUISceneGraph.widgets_containers2D_user_order + HarfangGUISceneGraph.widgets_containers3D_user_order

		for w_container in w_containers:
			if w_container not in cls.focussed_containers:
				cls.set_widget_state(w_container, "idle")
				if "MLB_pressed" in cls.current_signals:
					cls.set_widget_state(w_container, "no_focus")
				for widget in w_container["children_order"]:
					if widget != focussed_container:
						cls.set_widget_state(widget, "idle")

	@classmethod
	def get_label_from_id(cls, widget_id):
		return widget_id


	# ------------ Pointer position (Mouse or VR Controller)
	# Raycasts only computed in widgets_containers quads.
	@classmethod
	def raycast_pointer_position(cls, controller_id):
		widgets_containers3D_pointer_in = []
		for wc in HarfangGUISceneGraph.widgets_containers3D_user_order:
			if cls.compute_pointer_position_3D(controller_id, wc):
				widgets_containers3D_pointer_in.append(wc)
		
		### Voir comment gérer les widgets 2D hors VR
		widgets_containers2D_pointer_in = []
		for wc in HarfangGUISceneGraph.widgets_containers2D_user_order:
			if cls.flag_vr and cls.flag_use_pointer_VR:
				wc["pointers"]["mouse"]["pointer_world_position"] = None # deactivate mouse pointer in 2D UI ?? Encore utile avec "widgets_containers2D_pointer_in" ??
			else:
				cam2Dpos = hg.GetT(cls.camera2D_matrix)
				if cls.compute_pointer_position_2D(hg.Vec2(cls.mouse.X() + cam2Dpos.x, cls.mouse.Y()-cls.height - cam2Dpos.y), wc, "mouse"):
					widgets_containers2D_pointer_in.append(wc)
		###

		wc = cls.sort_widgets_containers_focus(widgets_containers2D_pointer_in, widgets_containers3D_pointer_in)
		if wc is not None:
			cls.controllers[controller_id]["world_intersection"] =  wc["pointers"][controller_id]["pointer_world_position"]
		return wc

	@classmethod
	def sort_widgets_containers_focus(cls, widgets_containers2D_pointer_in, widgets_containers3D_pointer_in):
		
		wc_focussed = None
		widgets_containers2D_focus_order = []
		widgets_containers3D_focus_order = []

		if len(widgets_containers2D_pointer_in) > 0:
			widgets_containers2D_focus_order = sorted(widgets_containers2D_pointer_in, key = lambda wc: wc["align_position"])
			# = sorted(temp_sort, key = lambda wc: wc["child_depth"], reverse = True)
			wc_focussed = widgets_containers2D_focus_order[0]

		if wc_focussed is None:
			if len(widgets_containers3D_pointer_in) > 0:
				vp = hg.GetT(cls.camera3D_matrix)
				for wc in widgets_containers3D_pointer_in:
					wc["sort_weight"] = round(hg.Len(wc["pointers"]["mouse"]["pointer_world_position"] - vp), 5)
				temp_sort = sorted(widgets_containers3D_pointer_in, key = lambda wc: wc["align_position"])
				temp_sort = sorted(temp_sort, key = lambda wc: wc["sort_weight"])
				widgets_containers3D_focus_order = sorted(temp_sort, key = lambda wc: wc["child_depth"], reverse = True)
				wc_focussed = widgets_containers3D_focus_order[0]
		
		return wc_focussed

	@classmethod
	def compute_pointer_position_3D(cls, controller_id, widgets_container):
		
		window_inv = hg.InverseFast(widgets_container["world_matrix"])

		wc_pointer = widgets_container["pointers"][controller_id]
		wc_pointer["pointer_world_position"] = None
		
		flag_pointer_in = False
		impact_2Dpos = None
		pointer_dt = hg.Vec2(0, 0)

		# Window2D have same pointer3D world position as its parent container
		if widgets_container["flag_2D"]:
			parent = cls.widgets[widgets_container["parent_id"]]
			p_pointer = parent["pointers"][controller_id]
			if p_pointer["pointer_world_position"] is not None:
				impact_2Dpos = window_inv * p_pointer["pointer_world_position"]
				if 0 < impact_2Dpos.x < widgets_container["size"].x and 0 < impact_2Dpos.y < widgets_container["size"].y:
					wc_pointer["pointer_world_position"] = p_pointer["pointer_world_position"] # !!! New Vec3 if necessary !!!
					flag_pointer_in = True
				impact_2Dpos = hg.Vec2(impact_2Dpos.x, impact_2Dpos.y)
		else:
			window_pos = hg.GetT(widgets_container["world_matrix"])
			window_size = widgets_container["size"]
			
			#ray_distance = hg.Len(window_pos - p0)
			#if ray_distance < max(window_size.x, window_size.y) * widgets_container["scale"].x * 4: # Widget container distance to ray origin limitation
			p0_local = window_inv * cls.controllers[controller_id]["ray_p0"]
			p1_local = window_inv * cls.controllers[controller_id]["ray_p1"]
			p1_local_ray = hg.Normalize(p1_local - p0_local)
			if p1_local_ray.z <= 1e-5:
				impact_2Dpos = None
			else:
				p1_local_inter = p0_local + p1_local_ray * (abs(p0_local.z) / p1_local_ray.z)
				if 0 < p1_local_inter.x < widgets_container["size"].x and 0 < p1_local_inter.y < widgets_container["size"].y:
					wc_pointer["pointer_world_position"] = widgets_container["world_matrix"] * p1_local_inter
					flag_pointer_in = True
				impact_2Dpos = hg.Vec2(p1_local_inter.x, p1_local_inter.y)
		
		if impact_2Dpos is not None and wc_pointer["pointer_local_position"] is not None:
			pointer_dt = impact_2Dpos - wc_pointer["pointer_local_position"]

		wc_pointer["pointer_local_position"] = impact_2Dpos
		wc_pointer["pointer_local_dt"] = pointer_dt
		return flag_pointer_in
	
	@classmethod
	def compute_pointer_position_2D(cls, pointer_pos2D, widgets_container, pointer_id):
		wc_pointer = widgets_container["pointers"][pointer_id]
		wc_pointer["pointer_world_position"] = None
		flag_pointer_in = False
		impact_2Dpos = None
		pointer_dt = hg.Vec2(0, 0)

		window_inv = hg.InverseFast(widgets_container["world_matrix"])

		local_pointer = window_inv * hg.Vec3(pointer_pos2D.x, pointer_pos2D.y, hg.GetT(widgets_container["world_matrix"]).z)
		
		impact_2Dpos = hg.Vec2(local_pointer.x, local_pointer.y)
		if 0 < local_pointer.x < widgets_container["size"].x and 0 < local_pointer.y < widgets_container["size"].y:
				wc_pointer["pointer_world_position"] = widgets_container["world_matrix"] * local_pointer
				flag_pointer_in = True
		if wc_pointer["pointer_local_position"] is not None:
				pointer_dt = impact_2Dpos - wc_pointer["pointer_local_position"]
		wc_pointer["pointer_local_position"] = impact_2Dpos
		wc_pointer["pointer_local_dt"] = pointer_dt
		return flag_pointer_in

	# ------------ String edition

	@classmethod
	def start_edit_string(cls, widget, widget_property):
		widget_property["edit_text"] = widget_property["text"]
		widget_property["display_text"] = "edit_text"
		cls.set_widget_state(widget, "edit")
		cls.set_ui_state(cls.UI_STATE_WIDGET_KEYBOARD_FOCUS) # Get keyboard control
		cls.set_widget_state(widget,"idle")
		cls.kb_cursor_pos = len(widget_property["edit_text"])
		cls.ascii_connect = hg.OnTextInput.Connect(on_key_press)

	@classmethod
	def stop_edit_string(cls, widget, widget_property):
		cls.set_widget_state(widget, "no_edit")
		widget_property["display_text"] = "text"
		cls.set_ui_state(cls.UI_STATE_MAIN)	# Resume keyboard control to ui
		if cls.ascii_connect is not None:
			hg.OnTextInput.Disconnect(cls.ascii_connect)
			cls.ascii_connect = None
	
	@classmethod
	def update_edit_string(cls, widget, widget_property_id):
		
		widget_property = widget["components"][widget_property_id]
		
		if not "edit" in widget["states"]:
			if "mouse_click" in cls.current_signals and widget["widget_id"] in cls.current_signals["mouse_click"]:
				cls.start_edit_string(widget, widget_property)

		else:
			if "MLB_pressed" in cls.current_signals and not widget["widget_id"] in cls.current_signals["MLB_pressed"]:
				cls.stop_edit_string(widget, widget_property)
			
			elif cls.ui_state == cls.UI_STATE_WIDGET_KEYBOARD_FOCUS:

				str_l = len(widget_property["edit_text"])
				if cls.keyboard.Pressed(hg.K_Right) and cls.kb_cursor_pos < str_l:
					cls.kb_cursor_pos +=1
					
				elif cls.keyboard.Pressed(hg.K_Left) and cls.kb_cursor_pos > 0:
					cls.kb_cursor_pos -=1
				
				elif cls.keyboard.Pressed(hg.K_Backspace) and cls.kb_cursor_pos > 0:
					cls.kb_cursor_pos -= 1
					widget_property["edit_text"] = widget_property["edit_text"][:cls.kb_cursor_pos] + widget_property["edit_text"][cls.kb_cursor_pos+1:]
		
				elif cls.keyboard.Pressed(hg.K_Suppr) and cls.kb_cursor_pos < str_l:
					widget_property["edit_text"] = widget_property["edit_text"][:cls.kb_cursor_pos] + widget_property["edit_text"][cls.kb_cursor_pos+1:]

				elif cls.keyboard.Pressed(hg.K_Return) or cls.keyboard.Pressed(hg.K_Enter):
					widget_property["text"] = widget_property["edit_text"]
					cls.set_widget_state(widget, "no_edit")
					widget_property["display_text"] = "text"
					cls.set_ui_state(cls.UI_STATE_MAIN)	# Resume keyboard control to ui
					return True #String changed
				else:
					if cls.ascii_code is not None:
						widget_property["edit_text"] = widget_property["edit_text"][:cls.kb_cursor_pos] + cls.ascii_code + widget_property["edit_text"][cls.kb_cursor_pos:]
						cls.kb_cursor_pos += 1
						cls.ascii_code = None

		return False #String unchanged


	# ------------ Widgets ui


	@classmethod
	def info_text(cls, label, text):
		widget = cls.get_widget("info_text", label)
		widget["components"]["info_text"]["text"] = text
		widget["position"] = cls.get_cursor_position()
		cls.update_widget_components(widget)
		cls.update_cursor(widget)


	@classmethod
	def button(cls, widget_id):
		widget = cls.get_widget("button", widget_id)
		mouse_click = False
		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			mouse_click = True
		widget["components"]["button_box"]["label"] = cls.get_label_from_id(widget_id)
		widget["position"] = cls.get_cursor_position()
		cls.update_widget_components(widget)
		cls.update_cursor(widget)
		return mouse_click	

	@classmethod
	def button_image(cls, widget_id, texture_path, image_size: hg.Vec2):
		widget = cls.get_widget("image_button", widget_id)
		mouse_click = False
		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			mouse_click = True
		widget["position"] = cls.get_cursor_position()
		widget["components"]["image_button"]["size"].x = image_size.x
		widget["components"]["image_button"]["size"].y = image_size.y
		widget["components"]["image_button"]["texture"] = texture_path
		cls.update_widget_components(widget)
		cls.update_cursor(widget)
		return mouse_click
	
	@classmethod
	def image(cls, widget_id, texture_path, image_size: hg.Vec2):
		widget = cls.get_widget("info_image", widget_id)
		widget["position"] = cls.get_cursor_position()
		widget["components"]["info_image"]["size"].x = image_size.x
		widget["components"]["info_image"]["size"].y = image_size.y
		widget["components"]["info_image"]["texture"] = texture_path
		cls.update_widget_components(widget)
		cls.update_cursor(widget)

	@classmethod
	def check_box(cls, widget_id, checked: bool):
		widget = cls.get_widget("check_box", widget_id)
		mouse_click = False
		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			checked = not checked
			mouse_click = True
		
		if checked:
			cls.set_widget_state(widget, "checked")
		else:
			cls.set_widget_state(widget,"unchecked")
		
		widget["components"]["label_box"]["label"] = cls.get_label_from_id(widget_id)
		widget["position"] = cls.get_cursor_position()
		
		cls.update_widget_components(widget)
		cls.update_cursor(widget)

		return mouse_click, checked

	@classmethod
	def input_text(cls, widget_id, text = None):
		widget = cls.get_widget("input_text", widget_id)
		if text is not None:
			widget["components"]["input_box"]["text"] = text
		
		flag_changed = cls.update_edit_string(widget, "input_box")

		widget["position"] = cls.get_cursor_position()
		widget["components"]["label_box"]["label"] = cls.get_label_from_id(widget_id)
		cls.update_widget_components(widget)
		cls.update_cursor(widget)

		return flag_changed, widget["components"]["input_box"]["text"]
	
	@classmethod
	def scrollbar(cls, widget_id, width, height, part_size, total_size, scroll_position = None, flag_reset = False, flag_horizontal = False):
		widget = cls.get_widget("scrollbar_h" if flag_horizontal else "scrollbar_v", widget_id)
		
		widget["components"]["scrollbar"]["size"].x = width if flag_horizontal else max(cls.get_property_value(widget["components"]["scrollbar"], "scrollbar_thickness"), width)
		widget["components"]["scrollbar"]["size"].y = max(cls.get_property_value(widget["components"]["scrollbar"], "scrollbar_thickness"), height) if flag_horizontal else height

		if scroll_position is None:
					scroll_position = widget["scrollbar_position_dest"]

		if "mouse_move" in widget["states"]:
			if "MLB_down" not in cls.current_signals:
				cls.set_widget_state(widget, "mouse_idle")
				cls.set_ui_state(cls.UI_STATE_MAIN)
			elif cls.ui_state == cls.UI_STATE_WIDGET_MOUSE_FOCUS:
				pointer_dt = HarfangGUISceneGraph.get_current_container()["pointers"]["mouse"]["pointer_local_dt"]
				s = total_size / (widget["components"]["scrollbar"]["size"].x if flag_horizontal else widget["components"]["scrollbar"]["size"].y)
				scroll_step = pointer_dt.x if flag_horizontal else pointer_dt.y
				scroll_position += scroll_step * s
		else:
			if "MLB_pressed" in cls.current_signals and widget["widget_id"] in cls.current_signals["MLB_pressed"]:
				cls.set_widget_state(widget, "mouse_move")
				cls.set_ui_state(cls.UI_STATE_WIDGET_MOUSE_FOCUS)
		
		widget["part_size"] = part_size
		widget["total_size"] = total_size
		widget["scrollbar_position_dest"] = max(0, min(total_size - part_size, scroll_position))

		widget["position"] = cls.get_cursor_position()
		cls.update_widget_components(widget)
		cls.update_cursor(widget)
		if flag_reset:
			widget["scrollbar_position"] = widget["scrollbar_position_dest"]
		else:
			widget["scrollbar_position"] += (widget["scrollbar_position_dest"] - widget["scrollbar_position"]) * widget["bar_inertia"]
		return widget["scrollbar_position"]


	@classmethod
	def scrollbar_v(cls, widget_id, width, height, part_size, total_size, scroll_position = None, flag_reset = False):
		return cls.scrollbar(widget_id, width, height, part_size, total_size, scroll_position, flag_reset, False)


	@classmethod
	def scrollbar_h(cls, widget_id, width, height, part_size, total_size, scroll_position = None, flag_reset = False):
		return cls.scrollbar(widget_id, width, height, part_size, total_size, scroll_position, flag_reset, True)
		
	@classmethod
	def radio_image_button(cls, widget_id, texture_path, current_idx, radio_idx, image_size: hg.Vec2 = None):
		widget = cls.get_widget("radio_image_button", widget_id)
		
		widget["radio_idx"] = radio_idx
		if image_size is None:
			image_size = cls.radio_image_button_size
		else:
			cls.radio_image_button_size = image_size

		mouse_click = False
		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			current_idx = widget["radio_idx"]
			mouse_click = True
		
		if current_idx == widget["radio_idx"]:
			if "unselected" in widget["states"]:
				cls.set_widget_state(widget, "selected")
		else:
			if "selected" in widget["states"]:
				cls.set_widget_state(widget,"unselected")

		widget["position"] = cls.get_cursor_position()
		widget["components"]["radio_image_button"]["size"].x = image_size.x
		widget["components"]["radio_image_button"]["size"].y = image_size.y
		widget["components"]["radio_image_button"]["texture"] = texture_path
		cls.update_widget_components(widget)
		cls.update_cursor(widget)
		return mouse_click, current_idx

	@classmethod
	def toggle_button(cls, widget_id, texts: list, forced_text_width = None):
		widget = cls.get_widget("toggle_button", widget_id)
		widget["components"]["texts"] = texts
		widget["components"]["toggle_button_box"]["forced_text_width"] = forced_text_width
		mouse_click = False
		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			mouse_click = True
			widget["toggle_idx"] += 1
			if widget["toggle_idx"] >= len(texts):
				widget["toggle_idx"] = 0
		widget["components"]["toggle_button_box"]["text"] = widget["components"]["texts"][widget["toggle_idx"]]
		widget["position"] = cls.get_cursor_position()
		cls.update_widget_components(widget)
		cls.update_cursor(widget)
		return mouse_click, widget["toggle_idx"]

	@classmethod
	def toggle_image_button(cls, widget_id, textures_paths: list, image_size: hg.Vec2):
		widget = cls.get_widget("toggle_image_button", widget_id)
		mouse_click = False
		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			mouse_click = True
			widget["toggle_idx"] += 1
			if widget["toggle_idx"] >= len(textures_paths):
				widget["toggle_idx"] = 0
		widget["position"] = cls.get_cursor_position()
		widget["components"]["toggle_image_button"]["size"].x = image_size.x
		widget["components"]["toggle_image_button"]["size"].y = image_size.y
		widget["components"]["toggle_image_button"]["textures"] = textures_paths
		cls.update_widget_components(widget)
		cls.update_cursor(widget)
		return mouse_click, widget["toggle_idx"]
