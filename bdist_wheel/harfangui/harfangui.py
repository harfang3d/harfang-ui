import harfang as hg
from math import sin, cos, inf, pi, floor
from harfangui.mouse_pointer_3d import MousePointer3D
import json
from harfangui.vr_controllers import VRControllersHandler
from os import path

def get_assets_path():
    return path.dirname(path.abspath(__file__))

def min_type(a, b): # Issue
	if a.__class__ == hg.Vec2:
		return hg.Vec2(min(a.x, b.x), min(a.y, b.y))
	elif a.__class__ == hg.Vec3:
		return hg.Vec3(min(a.x, b.x), min(a.y, b.y), min(a.z, b.z))
	elif a.__class__ == hg.Vec4:
		return hg.Vec4(min(a.x, b.x), min(a.y, b.y), min(a.z, b.z), min(a.w, b.w))
	elif a.__class__ == hg.Color:
		return hg.Color(min(a.r, b.r), min(a.g, b.g), min(a.b, b.b), min(a.a, b.a))
	else:
		return min(a, b)

def max_type(a, b):
	if a.__class__ == hg.Vec2:
		return hg.Vec2(max(a.x, b.x), max(a.y, b.y))
	elif a.__class__ == hg.Vec3:
		return hg.Vec3(max(a.x, b.x), max(a.y, b.y), max(a.z, b.z))
	elif a.__class__ == hg.Vec4:
		return hg.Vec4(max(a.x, b.x), max(a.y, b.y), max(a.z, b.z), max(a.w, b.w))
	elif a.__class__ == hg.Color:
		return hg.Color(max(a.r, b.r), max(a.g, b.g), max(a.b, b.b), max(a.a, b.a))
	else:
		return max(a, b)

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

	frame_buffers_scale = 2 # For AA

	# sprites
	textures = {}
	textures_info = {}

	@classmethod
	def init(cls, fonts_files, fonts_sizes):
		cls.vtx_layout = hg.VertexLayout() # $$ function unique
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
		cls.box_overlay_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Disabled, hg.FC_Disabled, False)
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
	def draw_convex_polygon(cls, vid:int, vertices:list, color:hg.Color):

		cls.vtx.Clear()
		cls.uniforms_values_list.clear()
		cls.uniforms_textures_list.clear()
		# triangles fan:
		idx = []
		n = len(vertices)
		for v_idx in range(n):
			if v_idx < n-2:
				idx += [0, v_idx + 1, v_idx + 2]
			cls.vtx.Begin(v_idx).SetPos(vertices[v_idx] * cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()
		
		shader = cls.shader_flat
		rs = cls.box_render_state
		hg.DrawTriangles(vid, idx, cls.vtx, shader, cls.uniforms_values_list, cls.uniforms_textures_list, rs)
	
	@classmethod
	def draw_rounded_borders(cls, vid:int, vertices_ext:list, vertices_in:list, color:hg.Color):

		cls.vtx.Clear()
		cls.uniforms_values_list.clear()
		cls.uniforms_textures_list.clear()
		# triangles fan:
		idx = []
		n = len(vertices_ext)
		for v_idx in range(n):
			v1 = (v_idx+1) % n
			idx += [v_idx, v1, v_idx + n, v_idx + n, v1, v1 + n]
		
		vertices = vertices_ext + vertices_in
		for v_idx in range(n*2):
			cls.vtx.Begin(v_idx).SetPos(vertices[v_idx] * cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()
		
		shader = cls.shader_flat
		rs = cls.box_render_state
		hg.DrawTriangles(vid, idx, cls.vtx, shader, cls.uniforms_values_list, cls.uniforms_textures_list, rs)
	
	
	@classmethod
	def draw_box(cls, vid:int, vertices:list, color:hg.Color, texture_path = None, flag_opaque = False):
		cls.vtx.Clear()
		cls.uniforms_values_list.clear()
		cls.uniforms_textures_list.clear()
		idx = [0, 1, 2, 0, 2, 3]
		cls.vtx.Begin(0).SetPos(vertices[0]* cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()
		cls.vtx.Begin(1).SetPos(vertices[1]* cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(0, 1)).End()
		cls.vtx.Begin(2).SetPos(vertices[2]* cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(1, 1)).End()
		cls.vtx.Begin(3).SetPos(vertices[3]* cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(1, 0)).End()
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
		cls.vtx.Begin(0).SetPos(vertices[0]* cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()
		cls.vtx.Begin(1).SetPos(vertices[1]* cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(0, 1)).End()
		cls.vtx.Begin(2).SetPos(vertices[2]* cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(1, 1)).End()
		cls.vtx.Begin(3).SetPos(vertices[3]* cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(1, 0)).End()
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
			cls.vtx.Begin(i).SetPos(vertices[i]* cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()
		
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
		cls.vtx.Begin(0).SetPos(matrix * hg.Vec3(pos.x, pos.y, pos.z) * cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()

		idx = []
		num_sections = 32
		step = angle / num_sections
		for i in range(num_sections + 1):
			alpha = i * step + angle_start
			cls.vtx.Begin(i + 1).SetPos(matrix * hg.Vec3(pos.x + cos(alpha) * r, pos.y + sin(alpha) * r, pos.z) * cls.frame_buffers_scale).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()
			if i > 0:
				idx += [0, i + 1, i]

		hg.DrawTriangles(vid, idx, cls.vtx, cls.shader_flat, cls.uniforms_values_list, cls.uniforms_textures_list, cls.box_render_state)

	@classmethod
	def compute_text_size(cls, font_id, text):
		rect = hg.ComputeTextRect(cls.fonts[font_id], text)
		return hg.Vec2(rect.ex, rect.ey)

	@classmethod
	def draw_text(cls, vid, matrix:hg.Mat4, text, font_id, color):
		scale = hg.GetScale(matrix) * cls.frame_buffers_scale
		pos = hg.GetT(matrix) * cls.frame_buffers_scale
		rot = hg.GetR(matrix)
		mat = hg.TransformationMat4(pos, rot, scale)
		cls.text_uniform_values = [hg.MakeUniformSetValue('u_color', hg.Vec4(color.r, color.g, color.b, color.a))]
		hg.DrawText(vid, cls.fonts[font_id], text, cls.font_prg, 'u_tex', 0, mat, hg.Vec3(0, 0, 0), hg.DTHA_Left, hg.DTVA_Bottom, cls.text_uniform_values, [], cls.text_render_state)

	@classmethod
	def render_widget_container(cls, view_id, container):
		"""
		Renders a widget container.
		It first retrieves the draw list for the container and sets up the view with the appropriate frame buffer, 
		mode, rectangle, and orthographic settings. It then loops through each draw element in the draw list and calls
		the appropriate draw function based on the type of the draw element. Finally, it sets the view id of the container
		and returns the next view id.
		"""
		draw_list = HarfangGUISceneGraph.widgets_containers_displays_lists[container["name"]]
		hg.SetViewFrameBuffer(view_id, container["frame_buffer"].handle)
	
		hg.SetViewMode(view_id, hg.VM_Sequential)
		w, h = int(container["size"].x * cls.frame_buffers_scale), int(container["size"].y * cls.frame_buffers_scale)
		hg.SetViewRect(view_id, 0, 0, w, h)
		
		hg.SetViewOrthographic(view_id, 0, 0, w, h, hg.TransformationMat4(hg.Vec3(w / 2 + container["scroll_position"].x * cls.frame_buffers_scale, h / 2 + container["scroll_position"].y * cls.frame_buffers_scale, 0), hg.Vec3(0, 0, 0), hg.Vec3(1, -1, 1)), 0, 101, h)
		hg.SetViewClear(view_id, hg.CF_Depth | hg.CF_Color, hg.Color(0, 0, 0, 0), 1, 0)

		for draw_element in draw_list:
			if draw_element["type"] == "box":
					cls.draw_box(view_id, draw_element["vertices"], draw_element["color"], draw_element["texture"])
			elif draw_element["type"] == "convex_polygon":
					cls.draw_convex_polygon(view_id, draw_element["vertices"], draw_element["color"])
			elif draw_element["type"] == "rounded_borders":
					cls.draw_rounded_borders(view_id, draw_element["vertices_ext"], draw_element["vertices_in"], draw_element["color"])
			elif draw_element["type"] == "box_border":
					cls.draw_box_border(view_id, draw_element["vertices"], draw_element["color"])
			elif draw_element["type"] == "opaque_box":
					cls.draw_box(view_id, draw_element["vertices"], draw_element["color"], draw_element["texture"], True)
			elif draw_element["type"] == "text":
					cls.draw_text(view_id, draw_element["matrix"], draw_element["text"], draw_element["font_id"], draw_element["color"])
			elif draw_element["type"] == "rendered_texture_box":
					cls.draw_rendered_texture_box(view_id, draw_element["vertices"], draw_element["color"], draw_element["texture"])
			elif draw_element["type"] == "circle":
					cls.draw_circle(view_id, draw_element["matrix"], draw_element["position"], draw_element["radius"],0, 2 * pi, draw_element["color"])
					
		container["view_id"] = view_id
		
		return view_id + 1

	@classmethod
	def create_output(cls, resolution: hg.Vec2, view_state: hg.ViewState, frame_buffer: hg.FrameBuffer):
		return {"resolution": resolution, "view_state": view_state, "frame_buffer": frame_buffer }

	@classmethod
	def render(cls, view_id, outputs2D: list, outputs3D: list):
		"""
		Sets up and renders 2D and 3D views for given outputs. 
		It first sets up the 3D and 2D views based on the provided outputs. 
		Then, it renders the widget containers to textures and displays them to frame buffers or the screen. 
		It handles both 3D and 2D containers, rendering each to a texture and then displaying it. 
		Finally, it returns the view_id, render_views_3D, and render_views_2D.
		"""
		
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
				
				if container["flag_overlay"]:
					rs = cls.box_overlay_render_state
				else:
					rs = cls.box_render_state
				
				for vid in render_views_3D:
					hg.DrawTriangles(vid, idx, cls.vtx, shader, cls.uniforms_values_list, cls.uniforms_textures_list, rs)
		
		# Render 2D containers
		if len(render_views_2D) > 0:
			for container in HarfangGUISceneGraph.widgets_containers2D_children_order:
				
				view_id = cls.render_widget_container(view_id, container)
				
				# Display 3D widgets containers
				if container["parent"]["name"] == "MainContainer2D":
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
					
					if container["flag_overlay"]:
						rs = cls.box_overlay_render_state
					else:
						rs = cls.box_render_state
					
					for vid in render_views_2D:
						hg.DrawTriangles(vid, idx, cls.vtx, shader, cls.uniforms_values_list, cls.uniforms_textures_list, rs)
		
		return view_id, render_views_3D, render_views_2D

class HarfangUISkin:
	"""
	The HarfangUISkin class manages the visual appearance of a UI in the Harfang 3D engine.
	It provides methods for:
	- Initializing class variables such as textures, colors, and properties of UI components and widgets.
	- Interpolating between values for smooth transitions.
	- Loading and saving UI properties from/to JSON files.
	- Converting color properties between different formats and to hg.Color objects.
	"""

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

		cls.check_texture, cls.check_texture_info = hg.LoadTextureFromAssets("hgui_textures/icon_check.png", 0)

		cls.keyboard_cursor_color = hg.Color(1, 1, 1, 0.75)

		cls.properties = cls.load_properties(path.join(get_assets_path(), 'properties.json'))

		cls.primitives = {
			"box":{
				"background_color":{
					"type": "RGB24_APercent",
					"value": ["#555555", 100]
					},
				"border_color":{
					"type": "RGB24_APercent",
					"value": ["#aaaaaa", 100]
					},
				"border_thickness":{
					"type": "float",
					"value": 1
					}
				},
			
			"filled_box":{
				"background_color":{
					"type": "RGB24_APercent",
					"value": ["#555555", 100]
					}
				},
			
			"box_borders":{
				"border_color":{
					"type": "RGB24_APercent",
					"value": ["#aaaaaa", 100]
					},
				"border_thickness":{
					"type": "float",
					"value": 1
					}
				},
			
			"rounded_box":{
				"background_color":{
					"type": "RGB24_APercent",
					"value": ["#555555", 100]
					},
				"border_color":{
					"type": "RGB24_APercent",
					"value": ["#aaaaaa", 100]
					},
				"border_thickness":{
					"type": "float",
					"value": 1
					}, 
				"corner_radius":{
					"type": "vec4",
					"value": [0.5, 0.5, 0.5, 0.5]
					}
				},

			"filled_rounded_box":{
				"background_color":{
					"type": "RGB24_APercent",
					"value": ["#555555", 100]
					},
				 "corner_radius":{
					"type": "vec4",
					"value": [0.5, 0.5, 0.5, 0.5]
					}
				},

			"rounded_box_borders":{
				"border_color":{
					"type": "RGB24_APercent",
					"value": ["#aaaaaa", 100]
					},
				"border_thickness":{
					"type": "float",
					"value": 1
					},
				"corner_radius":{
					"type": "vec4",
					"value": [0.5, 0.5, 0.5, 0.5]
					}
				},
			
			"text":{
				"text_color":{
					"type": "RGB24_APercent",
					"value": ["#ffffff", 100]
					},
				"text_size":{
					"type": "float",
					"value": 1
					},
				"text":{
					"type":"string"
					},
				"forced_text_width":{
					"type": float
					}
				},
			
			"input_text":{
				"text_color":{
					"type": "RGB24_APercent",
					"value": ["#ffffff", 100]
					},
				"cursor_color":{
					"type": "RGB24_APercent",
					"value": ["#dddddd", 100]
					},
				"text_size":{
					"type": "float",
					"value": 1
					},
				"text":{
					"type":"string"
					},
				"forced_text_width":{
					"type": float
					}
				},
			
			"texture":{
				"texture":{
						"type": "string"
					},
				"texture_color":{
					"type": "RGB24_APercent",
					"value": ["#ffffff", 100]
					},
				"texture_size":{
						"type": "vec2",
						"value":[1, 1]
					},
				"texture_scale":{
						"type": "vec2",
						"value":[1, 1]
					}
				},

			"texture_toggle_fading":{
				"textures":{
						"type": "list"
					},
				"texture_color":{
					"type": "RGB24_APercent",
					"value": ["#ffffff", 100]
					},
				"texture_size":{
						"type": "vec2",
						"value":[1, 1]
					},
				"texture_scale":{
						"type": "vec2",
						"value":[1, 1]
					},
				"toggle_idx":{
					"type": "int",
					"value": 0
					},
				"fading_delay":{
					"type": "float",
					"value": 0.2
					}
				},
			
			"text_toggle_fading":{
				"text_color":{
					"type": "RGB24_APercent",
					"value": ["#ffffff", 100]
					},
				"text_size":{
					"type": "float",
					"value": 1
					},
				"texts":{
					"type":"list"
					},
				"forced_text_width":{
					"type": float
					},
				"toggle_idx":{
					"type": "int",
					"value": 0
					},
				"fading_delay":{
					"type": "float",
					"value": 0.2
					}
				},
			
			"circle":{
				"background_color":{
					"type": "RGB24_APercent",
					"value": ["#28282c", 100]
					},
				"border_color":{
					"type": "RGB24_APercent",
					"value": ["#ffffff", 100]
					},
				"border_thickness":{
					"type": "float",
					"value": 2
					},
				"radius":{
					"type": "float",
					"value": 10
					}
			}
		}
		# Références par noms pour le script, à transformer en références par indices dans une list globale d'objets.
		cls.components = {
			"window_background": {
				"primitives":[{"type": "filled_rounded_box", "name":"window_background.1"}],
				"cursor_auto": False,
				"size_factor": [1, 1, 1]
				},
			"window_title": {
				"overlay": True,
				"align": HarfangUI.HGUIAF_LEFT,
				"primitives":[{"type": "filled_rounded_box", "name":"window_title.1"}, {"type": "text", "name":"window_title.2"}],
				"cursor_auto": False,
				"size_factor": [1, -1, -1]
				},
			"window_border": {
				"overlay": True,
				"primitives":[{"type": "rounded_box_borders", "name":"window_border.1"}],
				"cursor_auto": False,
				"size_factor": [1, 1, 1]
				},
			
			"widget_group_background":{
				"primitives":[{"type": "filled_rounded_box", "name":"wg_background.box"}],
				"cursor_auto": False,
				"size_factor": [1, 1, 1]
			},
			"widget_group_title": {
				"overlay": True,
				"align": HarfangUI.HGUIAF_CENTER,
				"primitives":[{"type": "text", "name":"widget_group_title.text"}],
				"cursor_auto": False,
				"size_factor": [1, -1, -1],
				"margins": [25, 25, 0]
				},

			"info_text": {
				"primitives":[{"type": "text", "name": "info_text.1"}],
				"margins":[15, 0, 0]
				},
			"info_image": {
				"primitives":[{"type":"texture", "name": "info_image.1"}]
				},
			"info_image_label": {
				"primitives":[{"type": "text", "name": "info_image_label.1"}]
				},

			"basic_label": {
				"primitives": [{"type": "text", "name": "basic_label.1"}]
				},
			"input_box": {
				"primitives": [{"type": "filled_rounded_box", "name": "input_box.1"}, {"type": "input_text", "name": "input_box.2"}],
				"align": HarfangUI.HGUIAF_LEFT
				},
			"button_component": {
				"primitives":[{"type": "filled_rounded_box", "name": "button_component.1"}, {"type": "text", "name": "button_component.2"}],
				"margins": [15, 5, 0]
				},
			"image_button": {
				"primitives": [{"type": "filled_rounded_box", "name": "image_button.1"}, {"type": "texture", "name": "image_button.2"}, {"type": "text", "name": "image_button.3"}],
				"margins": [50, 15, 0], "space_size": 20
				},
			"check_box":{
				"primitives": [{"type": "filled_rounded_box", "name": "check_box.1"}, {"type": "texture","name": "check_box.2", "texture": "hgui_textures/icon_check.png", "texture_size": [15, 15]}],
				},
			"toggle_image": {
				"primitives": [{"type": "filled_rounded_box", "name": "toggle_image.box"}, {"type": "texture_toggle_fading", "name": "toggle_image.textures"}]
				},
			"scrollbar": {
				"primitives":[{"type": "filled_box", "name": "scrollbar.background","background_color": ["#141414", 100]}, {"type": "filled_rounded_box", "name": "scrollbar.bar", "corner_radius": [1, 1, 1, 1]}],
				"scrollbar_thickness": 8, "flag_horizontal": False, "part_size": 1, "total_size": 3, "scrollbar_position":0, "scrollbar_position_dest": 0, "bar_inertia": 0.25
				},
			"radio_image_button": {
				"primitives": [{"type": "rounded_box", "name": "radio_image_button.1"}, {"type": "texture", "name": "radio_image_button.2"}],
				"margins": [5, 5, 0],
				},
			"toggle_button_box": {
				"primitives": [{"type": "filled_rounded_box", "name": "toggle_button.box"}, {"type": "text_toggle_fading", "name": "toggle_button.texts"}],
				"margins": [15, 10, 0]
				},
			"text_select":{
				"primitives": [{"type": "filled_box", "name": "text_select.background"}, {"type": "text", "name": "text_select.text"}],
				"align": HarfangUI.HGUIAF_LEFT
			},
			"list_box": {
				"primitives": [{"type": "filled_rounded_box", "name": "list_box.background"}],
				"selected_idx": 0, "items_list": [], "line_space_factor": 1, "margins": [5, 5, 0],
			},
			"sliderbar": {
				"primitives":[{"type": "filled_rounded_box", "name": "sliderbar.background"}, {"type": "filled_rounded_box", "name": "sliderbar.bar"}, {"type": "circle", "name": "sliderbar.plot"}],
				"bar_thickness": 2, "value_start": 0, "value_end": 10, "inertial_value": 0, "value_dest": 0, "bar_inertia": 0.25, "flag_horizontal": True,
				"margins": [10, 10, 0]
				},
			"number_display": {
				"primitives": [{"type": "filled_rounded_box", "name": "number_display.background", "corner_radius": [1, 1, 1, 1], "background_color": ["#2a2a2e", 100]}, {"type": "text", "name": "number_display.text"}],
				"num_digits": 2, "margins": [5, 5, 0]
			}
			}

		cls.widgets_models = {
			"window" : {"components": ["window_background", "window_border", "window_title"],
						"properties" : ["window_box_color", "window_border_color", "window_rounded_radius",
						"window_title_margins", "window_title_background_color", "window_title_color", "window_title_rounded_radius"],
						"margins": [15, 15, 0], "align": HarfangUI.HGUIAF_LEFT
						},

			"widget_group" : {"components": ["widget_group_background", "widget_group_title"],
							"properties" : ["widget_group_box_color", "widget_group_rounded_radius",
							"widget_group_title_margins", "widget_group_title_color"],
							"margins": [25, 25, 25]
							},

			"info_text" : {"components": ["info_text"],
							"properties": ["info_text_color"]
						},
			
			"info_image" : {"components": ["info_image", "info_image_label"], "stacking": HarfangUI.HGUI_STACK_VERTICAL,
							"properties": ["info_image_margins", "info_image_label_margins", "info_image_label_text_color"]
						},
			
			"input_text": {"components": ["basic_label", "input_box"],
							"properties": ["basic_label_margins", "basic_label_text_color",
										"input_text_margins", "input_box_color", "widget_rounded_radius", "input_text_color"]
							},
	
			"button": {"components": ["button_component"],
						"properties": ["button_box_color", "button_text_color", "widget_rounded_radius"]
						},
	
			"image_button": {"components": ["image_button"],
						"properties": ["button_box_color", "widget_rounded_radius", "image_button_label_color"]
						},
	
			"check_box": {"components": ["basic_label", "check_box"],
						"properties": ["basic_label_margins", "basic_label_text_color",
									"checkbox_margins", "checkbox_rounded_radius", "checkbox_box_color", "check_color"],
						},
			
			"toggle_image_button": {"components": ["basic_label", "toggle_image"],
									"properties": ["basic_label_margins", "basic_label_text_color",
												"toggle_image_margins","widget_rounded_radius", "toggle_image_box_color"]
									},
			
			"scrollbar": {"components": ["scrollbar"],
							"properties": ["scrollbar_color"]
						},
			
			"radio_image_button": {"components": ["radio_image_button"], "radio_idx": 0,
								"properties": ["radio_image_offset", "radio_button_box_color","radio_image_bg_size",
								"radio_image_rounded_radius", "radio_image_border_color", "radio_image_border_thickness"
								]
						},
			
			"toggle_button": {"components": ["basic_label", "toggle_button_box"], "toggle_idx": 0,
								"properties": ["basic_label_margins", "basic_label_text_color", "button_box_color", "button_text_color", "widget_rounded_radius"]
								},
			
			"text_select":{"components": ["text_select"],
							"properties": ["text_select_box_color", "text_select_margins", "text_select_text_color"]},

			"list_box": {"components": ["basic_label", "list_box"], "current_idx": 0,
						"properties": ["basic_label_margins", "basic_label_text_color","listbox_background_color", "listbox_rounded_radius"]
						},
			
			"slider_float": {"components":["basic_label", "sliderbar", "number_display"],
						"properties":["basic_label_margins", "basic_label_text_color", "sliderbar_bg_color", "sliderbar_color", "sliderbar_plot_radius", "sliderbar_thickness"],
						"forced_number_width": 40, "number_size": 1}

			#"dropdown": {"components": ["basic_label", "toggle_button_box", "list_box"], "current_idx":0,
			#			"properties": ["basic_label_margins", "basic_label_text_color", "button_box_color", "button_text_color", "button_text_margins", "widget_rounded_radius"]}
			
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
	def convert_properties_color_to_RGBA32(cls):
		for property_name, property in cls.properties.items():
			if property["type"] == "color":
				property["type"] = "RGBA32"
				for layer in property["layers"]:
					for state_name, state in layer["states"].items():
						v = state["value"]
						vrgba32 = (int(v[0] * 255) << 24) + (int(v[1] * 255) << 16) + (int(v[2] * 255) << 8) + int(v[3] * 255)
						state["value"] = str(hex(vrgba32))
		
		cls.save_properties("properties_rgba32.json")
	
	@classmethod
	def convert_properties_RGBA32_to_RGB24_APercent(cls):
		for property_name, property in cls.properties.items():
			if property["type"] == "RGBA32":
				property["type"] = "RGB24_APercent"
				for layer in property["layers"]:
					for state_name, state in layer["states"].items():
						v = hg.ColorFromRGBA32(hg.ARGB32ToRGBA32(int(state["value"].replace("#", "0x"),16)))
						vrgb24 = (int(v.r * 255) << 16) + (int(v.g * 255) << 8) + int(v.b * 255)
						state["value"] = [str(hex(vrgb24)).replace("0x", "#"), int(v.a * 100)]
		
		cls.save_properties("properties_rgb24_apercent.json")

	@staticmethod
	def RGBA32_to_Color(value:str):
		return hg.ColorFromRGBA32(hg.ARGB32ToRGBA32(int(value.replace("#", "0x"),16)))

	@staticmethod
	def RGB24_APercent_to_Color(value:list):
		return hg.ColorFromRGBA32(hg.ARGB32ToRGBA32((int(value[0].replace("#", "0x"),16)<<8) + int(value[1]/100 * 255)))


	@classmethod
	def save_properties(cls, output_file_name):

		json_script = json.dumps(cls.properties, indent=4)
		file = open(output_file_name, "w")
		file.write(json_script)
		file.close()
		

class HarfangGUISceneGraph:
	"""
	The HarfangGUISceneGraph class manages the graphical representation of widgets in a UI scene. It provides methods for:
	- Initializing and clearing the scene graph.
	- Adding, sorting, and retrieving widget containers.
	- Setting the current container and its display list.
	- Adding various graphical elements to the scene, such as boxes, rounded boxes, borders, circles, and text.
	- Computing the vertices for rounded rectangles.
	"""

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
		cls.widgets_containers_displays_lists[widgets_container["name"]] = [] # Intégrer les display lists aux containers ?
	

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
	def add_box(cls, matrix:hg.Mat4, pos:hg.Vec3, size:hg.Vec3, color:hg.Color):

		p0 = matrix * pos
		p1 = matrix * hg.Vec3(pos.x, pos.y + size.y, pos.z)
		p2 = matrix * hg.Vec3(pos.x + size.x, pos.y + size.y, pos.z)
		p3 = matrix * hg.Vec3(pos.x + size.x, pos.y, pos.z)

		cls.widgets_containers_displays_lists[cls.current_container_id].append({"type": "box", "vertices": [p0, p1, p2, p3], "color": color, "texture": None})
	
	@classmethod
	def compute_rounded_rectangle(cls, matrix:hg.Mat4, pos:hg.Vec3, size:hg.Vec3, corner_radius:hg.Vec4):
		num_steps = 8
		max_radius = min(size.x, size.y) / 2
		a_step = pi/(2*num_steps)
		rs = corner_radius * max_radius
		
		centers = [
			pos.x + rs.x, pos.y + rs.x, 
			pos.x + size.x - rs.y, pos.y + rs.y,
			pos.x + size.x - rs.z, pos.y + size.y - rs.z,
			pos.x + rs.w, pos.y + size.y - rs.w
			]
		
		a = pi
		
		vertices = []
		rsl = [rs.x, rs.y, rs.z, rs.w]
		for c_part in range(4):
			cx, cy = centers[c_part * 2], centers[c_part * 2 + 1]
			r = rsl[c_part]
			for i in range(num_steps+1):
				px = r * cos(a) + cx
				py = r * sin(a) + cy
				vertices.append(matrix * hg.Vec3(px, py, 0))
				if i < num_steps:
					a += a_step
		return vertices
	
	@classmethod
	def add_rounded_box(cls, matrix:hg.Mat4, pos:hg.Vec3, size:hg.Vec3, color:hg.Color, corner_radius:hg.Vec4):
		vertices = cls.compute_rounded_rectangle(matrix, pos, size, corner_radius)
		cls.widgets_containers_displays_lists[cls.current_container_id].append({"type": "convex_polygon", "vertices": vertices, "color": color})

	@classmethod
	def add_rounded_border(cls, matrix:hg.Mat4, pos:hg.Vec3, size:hg.Vec3, border_thickness:float, color:hg.Color, corner_radius:hg.Vec4):

		vertices_ext = cls.compute_rounded_rectangle(matrix, pos, size, corner_radius)
		pos_in = pos + hg.Vec3(border_thickness, border_thickness, 0)
		size_in = size - hg.Vec3(2*border_thickness, 2*border_thickness, 0)
		max_radius = min(size_in.x, size_in.y)
		
		def comp_cin(corner):
			return (max_radius * corner - border_thickness) / (max_radius - border_thickness)
		
		corner_radius_in = hg.Vec4(comp_cin(corner_radius.x), comp_cin(corner_radius.y), comp_cin(corner_radius.z), comp_cin(corner_radius.w) )
		vertices_in = cls.compute_rounded_rectangle(matrix, pos_in, size_in, corner_radius_in )

		cls.widgets_containers_displays_lists[cls.current_container_id].append({"type": "rounded_borders", "vertices_ext": vertices_ext, "vertices_in": vertices_in, "color": color})

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
	def add_circle(cls, matrix, pos, radius, color):
		cls.widgets_containers_displays_lists[cls.current_container_id].append({"type": "circle", "matrix": matrix, "position": pos, "radius": radius, "color": color})

	@classmethod
	def add_text(cls, matrix, pos, scale, text, font_id, color):
		mat = matrix * hg.TransformationMat4(pos, hg.Vec3.Zero, hg.Vec3(scale, scale, scale))
		cls.widgets_containers_displays_lists[cls.current_container_id].append({"type": "text","matrix":mat, "text": text, "font_id": font_id, "color": color})




class HarfangUI:
	"""
	The HarfangUI class manages the user interface (UI) for both 2D and VR environments. It provides methods for:
	- Initializing the UI with specified fonts, screen width, and height.
	- Handling various UI states such as main, widget keyboard focus, widget mouse focus, and mouse down out.
	- Managing widgets, their containers, and the cursor.
	- Handling signals for UI events.
	- Managing controllers for user input.
	- Handling keyboard input for text editing.
	- Setting up main containers for 3D and 2D UIs.
	- Handling VR-specific features such as VR state and framebuffers.
	"""

	# VR
	flag_vr = False
	vr_state = None
	left_fb = None
	right_fb = None

	left_fb = None
	right_fb = None

	flag_use_mouse_VR = True

	# Screen
	window = None
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

	# Cursor stacking:

	HGUI_STACK_HORIZONTAL = 0
	HGUI_STACK_VERTICAL = 1

	# Components order
	HGUI_ORDER_DEFAULT = 0
	HGUI_ORDER_REVERSE = 1

	# Widgets alignments flags
	HGUIAF_CENTER = 0
	HGUIAF_TOP = 1
	HGUIAF_BOTTOM = 2
	HGUIAF_LEFT = 3
	HGUIAF_RIGHT = 4
	HGUIAF_TOPLEFT = 5
	HGUIAF_TOPRIGHT = 6
	HGUIAF_BOTTOMLEFT = 7
	HGUIAF_BOTTOMRIGHT = 8
	

	# Windows flags:
	HGUIWF_2D = 0x1
	HGUIWF_NoPointerMove = 0x2
	HGUIWF_HideTitle = 0x4
	HGUIWF_Invisible = 0x8
	HGUIWF_HideScrollbars = 0x10
	HGUIWF_Overlay = 0x20

	# Frame datas (updated on each frame)

	flag_same_line = False
	flag_set_cursor_pos = False
	widgets_same_line = []
	line_max_y_size = 0 # Used for auto-positionning with same_line(): the biggest widget Ysize in the line
	line_widgets_width = 0
	line_space_size = 3 # Space between lines in pixels
	inner_line_space_size = 3 # space between widgets in same line
	current_font_id = 0
	mouse = None
	keyboard = None
	dt = 0
	timestamp = 0

	new_signals = {} # Signals sended in frame
	current_signals = {} # Prec. frame signals, read in current frame
	
	UI_STATE_MAIN = 0 # Widgets mouse hovering / mouse click / keyboard shortcuts
	UI_STATE_WIDGET_KEYBOARD_FOCUS = 1 # The content of a widget is being edited (Text input)
	UI_STATE_WIDGET_MOUSE_FOCUS = 2 # A widget is using mouse (Scrollbar...)
	UI_STATE_MOUSE_DOWN_OUT = 3 # Mouse down out of hgui windows, another api can keep the mouse control even if pointer hover any hgui window
	
	ui_state = 0

	camera = None
	focal_distance = 1
	camera3D_matrix = None
	camera2D_matrix = None
	
	controllers = {}
	focussed_containers = []

	kb_cursor_pos = 0 # Used to edit input texts
	kb_cursor_down_t0 = 0
	kb_cursor_repeat_delay = 0.5 # Delay before repeat starts
	kb_cursor_current_key_down = None

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
		cls.main_widgets_container_3D["name"] = "MainContainer3D"
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
		cls.main_widgets_container_2D["name"] = "MainContainer2D"
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
			"enabled": True,
			"ray_p0": None, # Vec3, position
			"ray_p1": None, # Vec3, direction
			"world_intersection": None, # Vec3
			"focused_container": None # widgets_container
		}

	@classmethod
	def new_gui_object(cls, type):
		return {
			"type": type,
			"name": "",
			"classe":"gui_object",
			"hidden": False,
			"enable": True,
			"parent": None, # Parent container ID
			"local_matrix": None,
			"world_matrix": None,
			"position": hg.Vec3(0, 0, 0),
			"rotation": hg.Vec3(0, 0, 0),
			"scale": hg.Vec3(1, 1, 1),	# Global scale, used to compute final render matrix
			"offset": hg.Vec3(0, 0, 0),
			"size": hg.Vec3(0, 0, 0),
			"cursor_auto": True	# False if cursor is not incremented in object rendering
		}

	@classmethod
	def new_component(cls, type):
		component = cls.new_gui_object(type)
		component["classe"] = "component"
		
		component.update(
			{
				"primitives": [], # Render shapes
				"objects_dict": {},
				"stacking": cls.HGUI_STACK_HORIZONTAL, # Text & textures primitives stacking
				"align": cls.HGUIAF_CENTER,
				"cursor_position": hg.Vec3(0, 0, 0),
				"space_size": 10, # Distance between primitives
				"margins": hg.Vec3(0, 0, 0),
				"overlay": False, # Used for widgets containers. If True: component is rendered over children widgets
				"content_size": hg.Vec3(0, 0, 0), # Stacked primitives size, out of margins or component auto-sizing
				"size_factor": hg.Vec3(-1, -1, -1) # Size linked to container size. factor <= 0 : no proportional size correction. factor > 0 : size = max(component_size * factor, container_size) 
			}
		)
		for primitive_def in HarfangUISkin.components[type]["primitives"]:
			primitive = cls.new_primitive(primitive_def)
			primitive["parent"] = component
			component["primitives"].append(primitive)
			component["objects_dict"][primitive["name"]] = primitive
		return component


	@staticmethod
	def transcrypt_var(v, t):
		if t == "color": 			vt = hg.Color(v[0], v[1], v[2], v[3])
		elif t == "RGBA32":			vt = HarfangUISkin.RGBA32_to_Color(v)
		elif t == "RGB24_APercent": vt = HarfangUISkin.RGB24_APercent_to_Color(v)
		elif t == "float":			vt = v
		elif t == "string":			vt = v
		elif t == "int":			vt = v
		elif t == "list":			vt = v
		elif t == "vec2":			vt = hg.Vec2(v[0], v[1])
		elif t == "vec3":			vt = hg.Vec3(v[0], v[1], v[2])
		elif t == "vec4":			vt = hg.Vec4(v[0], v[1], v[2], v[3])
		return vt


	@classmethod
	def new_primitive(cls, primitive_def):
		new_primitive = cls.new_gui_object(primitive_def["type"])
		new_primitive .update ({
			"classe": "primitive",
			"name": primitive_def["name"]
		})
		# Create basic occurence
		primitive_model = HarfangUISkin.primitives[primitive_def["type"]]
		for variable_name, vd in primitive_model.items():
			t = vd["type"]
			if "value" in vd:
				v = cls.transcrypt_var(vd["value"], t)
			else:
				v = None
			new_primitive[variable_name] = v
		# Overwrites/create occurence vars
		ex_vars = ["type", "name"]
		for variable_name, v in primitive_def.items():
			if variable_name not in ex_vars:
				if variable_name in primitive_model:
					new_primitive[variable_name] = cls.transcrypt_var(v, primitive_model[variable_name]["type"])
				else:
					new_primitive[variable_name] = v
		# Specific internal vars:
		if new_primitive["type"] == "texture_toggle_fading":
			new_primitive["t"] = 0
			new_primitive["toggle_t0"] = 0
			new_primitive["toggle_idx_start"] = 0
		if new_primitive["type"] == "text_toggle_fading":
			new_primitive["t"] = 0
			new_primitive["toggle_t0"] = 0
			new_primitive["toggle_idx_start"] = 0
			new_primitive["texts_d"] = []
		return new_primitive

	@classmethod
	def get_property_value(cls, widget, property_name):
		return widget["properties"][property_name]["value"]
	
	@classmethod
	def get_property_states_value(cls, widget, property_name, states):
		if property_name in widget["properties"]:
			property = widget["properties"][property_name]
			value = None
			for layer_id in range(len(property["layers"])):
				layer = property["layers"][layer_id]
				for state_name in states:
					if state_name in layer["states"]:
						state = layer["states"][state_name]
						if value is None or layer["operator"] == "set":
							value = state["value"]
						elif layer["operator"] == "add":
							value += state["value"]
						elif layer["operator"] == "multiply":
							value *= state["value"]
						break # One state by layer
			return value
		print("!!! ERROR - Unknown property: " + property_name + " - Widget: " + widget["name"])
		return None

	@classmethod
	def new_single_widget(cls, type):
		"""
		Creates a new widget of a specified type, including properties for  alignment, stacking, cursor position,
		size, opacity, components, rendering order, pointers, and states. 
		It also includes flags for indicating whether the widget is new or if its size needs to be updated.
		"""

		widget = cls.new_gui_object(type)
		widget["classe"] = "widget"
		widget.update({
			"flag_new": True,	# True at widget creation, else False (see get_widget())
			"flag_update_rest_size": True, # True if widget rest size must be updated (e.g.: input strings)
			"rest_size": hg.Vec3(0, 0, 0), # Widget reference size used for positionning (center)
			"align": cls.HGUIAF_CENTER,
			"v_align": cls.HGUIAF_CENTER,
			"stacking": cls.HGUI_STACK_HORIZONTAL,
			"cursor": hg.Vec3(0, 0, 0),
			"cursor_start_line": hg.Vec3(0, 0, 0),
			"default_cursor_start_line": hg.Vec3(0, 0, 0),
			"space_size": 10, # Distance between components
			"opacity": 1,
			"max_size": hg.Vec3(0, 0, 0), # Used for window worksapce computation (scroll bars...)
			"components": {},
			"components_render_order": [],
			"components_order": cls.HGUI_ORDER_DEFAULT,
			"objects_dict": {}, # Components & primitives in same dict to optimize properties links referencement
			"properties": {},
			"pointers": {"mouse": cls.new_pointer("mouse")},
			"sub_widgets": [], # Sub-widgets are widgets générated by the widget (e.g: listbox, generates text_select widgets)
			"states": []
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
		"""
		Creates a new widget container, which is a special type of widget designed to hold and manage other widgets. 
		The container has properties for layout (margins, stacking direction), visibility and rendering (frame buffer, view ID), 
		as well as workspace properties defining the area where widgets can be placed. 
		This method is used when a new group of widgets needs to be created and managed together in the user interface.
		"""

		container = cls.new_single_widget(type)
		container["classe"] = "widgets_container"
		container.update({
			"margins": hg.Vec3(5, 5, 5),
			"stacking": cls.HGUI_STACK_VERTICAL,
			"flag_2D": False,
			"flag_invisible": False,
			"flag_overlay": False,
			"flag_scrollbar_v": False,
			"flag_scrollbar_h": False,
			"flag_hide_scrollbars": False,
			"children_order": [],
			"widgets_stack": [],	# List of rows lists, to compute children widgets stacking and alignment at end_[container]() function
			"sort_weight": 0,		# Sort weight = distance to camera-pointer ray for 3D windows. Sort weight = align position for 2D windows
			"child_depth": 0,
			"containers_2D_children_align_order": [],	# 2D Overlays order are user-focus dependant for 2D containers - Used for final rendering order
			"containers_3D_children_align_order": [],	# for the moment, 3D Overlays order are user-order dependant for 3D containers
			"align_position": 0, # Index in parent["containers_2D_children_align_order"] - Used in sorting to find pointer focus
			"workspace_min": hg.Vec3(0, 0, 0), # Where workspace begins (could be < 0)
			"workspace_max": hg.Vec3(0, 0, 0),
			"workspace_size": hg.Vec3(0, 0, 0),
			"frame_buffer_size": hg.iVec2(0, 0),
			"scroll_position": hg.Vec3(0, 0, 0),	# Set with new_scroll_position at frame beginning
			"new_scroll_position": hg.Vec3(0, 0, 0), # Next frame scroll position
			"color_texture": None,
			"depth_texture": None,
			"frame_buffer": None,	# Widgets rendering frame buffer
			"view_id": -1 # Container rendering view_id
		})
		return container

	@classmethod
	def create_component(cls, component_type, widget):
		if component_type in HarfangUISkin.components:
			
			#Basic component occurence
			component = cls.new_component(component_type)
			component["name"] = component_type						### ! Define a real name when components will be defined with a JSON script
			component_model = HarfangUISkin.components[component_type]
			
			#Overwrites and create vars
			vec3_types = ["size_factor", "margins"] #fields that needs list_to_vec3 conversion
			ex_vars = ["primitives"]
			for key, value in component_model.items():
				if key not in ex_vars:
					if key in vec3_types:
						component[key] = hg.Vec3(value[0], value[1], value[2])
					else:
						component[key] = value
			return component
		return None


	@classmethod
	def create_widget(cls, widget_type, widget_id):
		"""
		Creates a new widget of a given type and id. 
		It first checks if the widget type is valid and then creates either a container or a single widget. 
		It then creates the components and properties of the widget based on the widget model. 
		It also handles the creation of linked values, which are values that are linked to other objects in the widget. 
		Finally, it returns the created widget or None if the widget type is not valid.
		"""

		# Widgets types of "widgets_container" classe:
		widgets_type_containers = ["window", "widget_group"]

		if widget_type in HarfangUISkin.widgets_models:

			if widget_type in widgets_type_containers:
				widget = cls.new_widgets_container(widget_type)
			else:
				widget = cls.new_single_widget(widget_type)

			components_order = []
			widget_model = HarfangUISkin.widgets_models[widget_type]
			for component_type in widget_model["components"]:
				component = cls.create_component(component_type, widget)
				component["parent"] = widget
				components_order.append(component)

			#Creation of a dictionnary to facilitate access to components
			components_dict = {}
			primitives_dict = {}
			for component in components_order:
				components_dict[component["type"]] = component
				for primitive in component["primitives"]:
					primitives_dict[primitive["name"]] = primitive

			widget["name"] = widget_id
			widget["components"] = components_dict
			widget["components_render_order"] = components_order
			widget["objects_dict"].update(components_dict)
			widget["objects_dict"].update(primitives_dict)
			widget["cursor_start_line"].x = widget["default_cursor_start_line"].x
			widget["cursor_start_line"].y = widget["default_cursor_start_line"].y
			widget["cursor_start_line"].z = widget["default_cursor_start_line"].z
			
			# Create or override values
			ex_vars = ["components", "properties"]
			vec3_types = ["margins"] 
			for key, value in widget_model.items():
				if key not in ex_vars:
					if key in vec3_types:
						widget[key]= hg.Vec3(value[0], value[1], value[2])
					else:
						widget[key] = value # !!! If Value is a Harfang Object, add a deepcopy
			
			# Create properties
			for property_name in widget_model["properties"]:
				if property_name in  HarfangUISkin.properties:
					class_property = HarfangUISkin.properties[property_name]
					# Creates layers occurences:
					property_layers = []
					for layer_id in range(len(class_property["layers"])):
						class_layer = class_property["layers"][layer_id]
						
						property_layer_states = {}
						for class_state_name, class_state in class_layer["states"].items():
							property_layer_states[class_state_name] = dict(class_state)
							property_layer_states[class_state_name]["value"] = cls.transcrypt_var(class_state["value"], class_property["type"])
						
						default_state_name = class_layer["default_state"]
						default_value = property_layer_states[default_state_name]["value"]
						if layer_id == 0:
							default_final_value = default_value
						else:
							if class_layer["operator"] == "set":
								default_final_value = default_value
							elif class_layer["operator"] == "add":
								default_final_value += default_value
							elif class_layer["operator"] == "multiply":
								default_final_value *= default_value
							elif class_layer["operator"] == "min":
								default_final_value = min_type(default_value, default_final_value)
							elif class_layer["operator"] == "max":
								default_final_value = max_type(default_value, default_final_value)

						property_layer = {"operator": class_layer["operator"], "current_state":default_state_name, "current_state_t0":0, "value":default_value, "value_start":default_value, "value_end":default_value, "states":property_layer_states}
						property_layers.append(property_layer)
					
					widget_property = {"layers":property_layers, "value":default_final_value}
					
					# Linked value setup:
					if "linked_value" in class_property:
						lv = class_property["linked_value"]
						w_lv = {"objects":[], "name": lv["name"], "operator": lv["operator"]}
						
						if "objects" in lv:
							for obj_name in lv["objects"]:
								if obj_name in widget["objects_dict"]:
									obj = widget["objects_dict"][obj_name]
									
									if lv["name"] in obj:
										w_lv["objects"].append(obj)
									if obj["classe"] == "component":
										for primitive in obj["primitives"]:
											if lv["name"] in primitive:
												w_lv["objects"].append(primitive)
							
						else:
							# Search objects with property name
							for _, obj in widget["objects_dict"].items():
								
								if lv["name"] in obj:
									w_lv["objects"].append(obj)
								if obj["classe"] == "component":
									for primitive in obj["primitives"]:
										if lv["name"] in primitive:
											w_lv["objects"].append(obj)
						
						# Set property value in objects linked vars
						v = widget_property["value"]
						o = w_lv["operator"]
						for obj in w_lv["objects"]:
							if o == "set":
								obj[w_lv["name"]] = v
							elif o == "add":
								obj[w_lv["name"]] += v
							elif o == "multiply":
								obj[w_lv["name"]] *= v
							elif o == "min":
								obj[w_lv["name"]] = min_type(v, obj[w_lv["name"]])
							elif o == "max":
								obj[w_lv["name"]] = max_type(v, obj[w_lv["name"]])

						widget_property["linked_value"] = w_lv

					widget["properties"][property_name] = widget_property
			
			return widget
		return None	


	@classmethod
	def get_widget(cls, widget_type, widget_id, args:dict = None):
		if not widget_id in cls.widgets:
			widget = cls.create_widget(widget_type, widget_id)
			widget["flag_new"] = True
			cls.widgets[widget_id] = widget
		else:
			widget = cls.widgets[widget_id]
			widget["flag_new"] = False
		if args is not None:
			for k, v in args.items():
				if k in widget:
					widget[k] = v
		cls.add_widget_to_render_list(widget)
		return widget

	@classmethod
	def add_widget_to_render_list(cls, widget):
		container = HarfangGUISceneGraph.get_current_container()
		container["children_order"].append(widget)
		widget["parent"] = container

	@classmethod
	def update_camera2D(cls):
		sp = cls.main_widgets_container_2D["scroll_position"]
		cls.camera2D_matrix = hg.TranslationMat4( sp * hg.Vec3(1, -1, 1))

	@classmethod
	def reset_main_containers(cls):
		for w_container in [cls.main_widgets_container_2D, cls.main_widgets_container_3D]:
			w_container["size"].x, w_container["size"].y = cls.width, cls.height
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
			if cls.flag_use_mouse_VR:
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
			for n in VRControllersHandler.controllers:
				if n not in cls.controllers:
					cls.controllers[n] = cls.new_controller(n)
				cls.controllers[n]["enable"] = True if n in VRControllersHandler.connected_controllers else False
		#Other controllers ?
		else:
			pass

	@classmethod
	def begin_frame(cls, dt, mouse: hg.Mouse, keyboard: hg.Keyboard, window, camera: hg.Node = None):
		"""
		Sets up the initial state for a new frame in the GUI. It updates the class variables with the 
		current mouse, keyboard, window, and camera states. It also calculates the window size and the camera's 3D 
		transformation matrix and focal distance if a camera is provided. 
		Then, it updates the state of the controllers and the 2D camera, and processes any signals, such as a mouse click. 
		If the mouse button is down, it sends a signal indicating this. If the mouse button is down outside of a widget, 
		it resets the UI state to the main state. Finally, it resets the main containers and clears the scene graph.
		"""

		cls.flag_vr = False

		cls.camera = camera
		cls.window = window
		_, cls.width, cls.height = hg.GetWindowClientSize(window)

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
		# We use internal signals to indicate a mouse button press because:
		# - It allows us to differentiate the state based on the pointer's location. 
		#   For instance, a mouse button press on a widget is not the same as a mouse button press outside of a widget.
		# If the mouse button is pressed, we send a "MLB_down" signal.
		# If the UI state indicates a mouse button press outside of a widget, we reset the UI state to the main state.
		# Finally, we reset the main containers and clear the scene graph.
		if cls.mouse.Down(hg.MB_0):
			cls.send_signal("MLB_down")
		elif cls.ui_state == cls.UI_STATE_MOUSE_DOWN_OUT:
			cls.set_ui_state(cls.UI_STATE_MAIN)
		cls.reset_main_containers()
		HarfangGUISceneGraph.clear()
		
		return True
	
	@classmethod
	def begin_frame_vr(cls, dt, mouse: hg.Mouse, keyboard: hg.Keyboard, screenview_camera: hg.Node,  window, vr_state: hg.OpenVRState, left_fb: hg.FrameBuffer, right_fb: hg.FrameBuffer):
		
		cls.flag_vr = True

		if True: #hg.OpenVRIsHMDMounted():
			cls.activate_mouse_VR(True)
		else:
			cls.activate_mouse_VR(False)

		cls.window = window
		_, cls.width, cls.height = hg.GetWindowClientSize(window)

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
		
		if cls.flag_use_mouse_VR:
			cls.focal_distance = hg.ExtractZoomFactorFromProjectionMatrix(vr_state.left.projection, hg.ComputeAspectRatioX(cls.width, cls.height))
			cls.camera3D_matrix = vr_state.head
		else:
			cls.camera3D_matrix = screenview_camera.GetTransform().GetWorld()
			
		cls.update_controllers()

		cls.update_camera2D()
		
		cls.update_signals()
		# We use internal signals to indicate a mouse button press because:
		# - It allows us to differentiate the state based on the pointer's location. 
		#   For instance, a mouse button press on a widget is not the same as a mouse button press outside of a widget.
		# If the mouse button is pressed, we send a "MLB_down" signal.
		# If the UI state indicates a mouse button press outside of a widget, we reset the UI state to the main state.
		# Finally, we reset the main containers and clear the scene graph.
		if cls.mouse.Down(hg.MB_0):
			cls.send_signal("MLB_down")
		elif cls.ui_state == cls.UI_STATE_MOUSE_DOWN_OUT:
			cls.set_ui_state(cls.UI_STATE_MAIN)
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
			if cls.flag_use_mouse_VR:
				fov = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(cls.vr_state.left.projection, hg.ComputeAspectRatioX(cls.width, cls.height)))
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
	def push_widgets_container(cls, w_container):
		"""
		This function adds a widget container to the stack and sets its child depth. 
		It also updates the parent's children order list and sets the cursor start line and workspace boundaries. 
		It handles both 2D and 3D containers and ensures that even if they are no longer displayed by the user, 
		the containers remain in the parent's children order list.
		"""

		HarfangGUISceneGraph.widgets_containers_stack.append(w_container)
		w_container["children_order"] = []
		w_container["child_depth"] = len(HarfangGUISceneGraph.widgets_containers_stack) - 1 # First child depth = 1, 0 is Main Widget container
		if w_container["flag_new"]:
			if w_container["flag_2D"]:
				w_container["parent"]["containers_2D_children_align_order"].insert(0, w_container)	# !!! Even if they are no longer displayed by user, the containers remain in this list. !!!
			else:
				w_container["parent"]["containers_3D_children_align_order"].insert(0, w_container)	# !!! Even if they are no longer displayed by user, the containers remain in this list. !!!
		cls.set_cursor_start_line(w_container["default_cursor_start_line"])
		
		cp = w_container["cursor"]
		p = w_container["default_cursor_start_line"]
		cp.x, cp.y, cp.z = p.x, p.y, p.z
		
		p = w_container["workspace_min"] 
		p.x, p.y, p.z = 0, 0, 0 #min(0, p.x), min(0, p.y), min(0, p.z)
		p = w_container["workspace_max"]
		p.x, p.y, p.z = w_container["size"].x, w_container["size"].y, w_container["size"].z  #max(p.x, w_container["size"].x), max(p.y, w_container["size"].y), max(p.z, w_container["size"].z)
	
	@classmethod
	def pop_widgets_container(cls):
		"""
		The pop_widgets_container method is part of a common pattern used in IMGUIs,
		often referred to as "push-pop". This pattern is used to manage the hierarchical structure
		of the UI elements (also known as widgets).
		"""

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
		parent = widgets_container["parent"]
		wc_pointer = widgets_container["pointers"][pointer_id]
		p_pointer = parent["pointers"][pointer_id]
		pointer_dt = p_pointer["pointer_local_dt"]
		
		if parent["name"] == "MainContainer3D":
			if wc_pointer["pointer_world_position"] is not None:
				rotmat = hg.GetRotationMatrix(cls.camera3D_matrix)
				ax = hg.GetX(rotmat)
				ay = hg.GetY(rotmat)
				
				height = cls.height
				
				if cls.flag_vr:
					if pointer_id !="mouse" or (pointer_id == "mouse" and cls.flag_use_mouse_VR):
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
	def update_widgets_stacking(cls, container):
		"""
		Updates the stacking of widgets within a container. 
		It iterates over each row of widgets in the container's stack and adjusts their positions based on alignment settings. 
		It handles both horizontal and vertical alignment, allowing widgets to be centered, right-aligned, or bottom-aligned within their row.
		"""

		w_stacking = container["widgets_stack"]
		workspace_width = container["workspace_max"].x - container["workspace_min"].x
		v = hg.Vec3(0, 0, 0)
		for row in w_stacking:
			v.x = 0
			if not row["fixed_position"]:
				if row["align"] == cls.HGUIAF_CENTER:
					margin = (workspace_width - row["width"]) / 2
					v.x = margin - (row["widgets"][0]["position"].x - container["workspace_min"].x) + container["workspace_min"].x
				elif row["align"] == cls.HGUIAF_RIGHT:
					w = row["widgets"][-1]
					v.x = (container["workspace_max"].x - container["margins"].x) - (w["position"].x + w["rest_size"].x)
			for widget in row["widgets"]:
				v.y = 0
				if row["v_align"] == cls.HGUIAF_CENTER:
					v.y = (row["max_height"] - widget["rest_size"].y) / 2
				elif row["v_align"] == cls.HGUIAF_BOTTOM:
					v.y = row["max_height"] - widget["rest_size"].y
				cls.move_widget(widget, v)
			
	@classmethod
	def begin_widget_group_2D(cls, widget_id):
		n = len(HarfangGUISceneGraph.widgets_containers_stack)
		if  n==0 or (n > 0 and HarfangGUISceneGraph.widgets_containers_stack[0] == cls.main_widgets_container_2D):
			# HDPI scaling, only for 2D windows in Main 2D container:
			scale_hdpi = hg.GetWindowContentScale(cls.window).x
		else:
			scale_hdpi = 1
		position = cls.get_cursor_position()
		flag = cls.begin_widget_group(widget_id, position, hg.Vec3(0, 0, 0), scale_hdpi, cls.HGUIWF_2D)	# size: in pixels
		return flag

	@classmethod
	def begin_widget_group(cls, widget_id, position:hg.Vec3 , rotation:hg.Vec3, scale:float = 1, widget_group_flags:int = 0):
		"""
		Begin the creation of a new widget group with the given parameters.
		The widget group flags can be combined to customize the widget group. The flags include:
		- HGUIWF_2D: If set, the widget group will be 2D.
		- HGUIWF_Overlay: If set, the widget group will be an overlay.
		- HGUIWF_HideTitle: If set, the title of the widget group will be hidden.
		- HGUIWF_HideScrollbars: If set, the scrollbars of the widget group will be hidden.

		The method first checks the current container's depth and orientation (2D or 3D). It then retrieves the widget group with the given ID and sets its properties according to the parameters and flags. The widget group is then pushed onto the stack of widget containers, marking the start of its definition.
		"""
		flag_2D = False if (widget_group_flags & cls.HGUIWF_2D) == 0 else True
		flag_overlay = False if (widget_group_flags & cls.HGUIWF_Overlay) == 0 else True
		flag_hide_title = False if (widget_group_flags & cls.HGUIWF_HideTitle) == 0 else True
		flag_hide_scrollbars = False if (widget_group_flags & cls.HGUIWF_HideScrollbars) == 0 else True

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
					print("HarfangUI ERROR - 3D container can't be child of 2D container - " + widget_id)
					return False
		else:
			if HarfangGUISceneGraph.get_current_container_child_depth() == 0:
				HarfangGUISceneGraph.widgets_containers_stack.append(cls.main_widgets_container_2D)
		
		widget = cls.get_widget("widget_group", widget_id)
		
		widget["widgets_stack"] = []

		widget["flag_2D"] = flag_2D
		widget["flag_move"] = False
		widget["flag_hide_title"] = flag_hide_title
		widget["components"]["widget_group_title"]["hidden"] = flag_hide_title
		widget["flag_invisible"] = False
		widget["flag_hide_scrollbars"] = flag_hide_scrollbars
		widget["flag_overlay"] = flag_overlay
		
		nsp = widget["new_scroll_position"]
		sp = widget["scroll_position"]
		sp.x, sp.y, sp.z = nsp.x, nsp.y, nsp.z

		widget["scale"].x =  widget["scale"].y = widget["scale"].z = scale
		s = widget["size"]
		s.x, s.y, s.z = 0, 0, 0

		if widget["flag_new"]:
			widget["position"].x, widget["position"].y, widget["position"].z = position.x, position.y * pyf, position.z
			widget["rotation"].x, widget["rotation"].y, widget["rotation"].z = rotation.x * rxf, rotation.y, rotation.z * rzf

			widget["default_cursor_start_line"].x = widget["margins"].x
			widget["default_cursor_start_line"].y = widget["margins"].y
			widget["objects_dict"]["widget_group_title.text"]["text"] = cls.get_label_from_id(widget["name"])
		
		else:
			if not flag_hide_title:
				widget["default_cursor_start_line"].y = 5 + widget["components"]["widget_group_title"]["size"].y
			#if not flag_move:
			widget["position"].x, widget["position"].y, widget["position"].z = position.x, position.y * pyf, position.z
			widget["rotation"].x, widget["rotation"].y, widget["rotation"].z = rotation.x * rxf, rotation.y, rotation.z * rzf
		
		cls.push_widgets_container(widget)
		return True

	@classmethod
	def end_widget_group(cls):
		"""
		Finalizes a widget group by updating its workspace, handling scrollbars, and adjusting scroll position. 
		It first checks if the workspace size exceeds the widget size and adds scrollbars if necessary. 
		It then clamps the scroll position to ensure it's within the workspace boundaries. 
		If the widget group has vertical or horizontal scrollbars, it adjusts the scroll position accordingly. 
		Finally, it pops the widget container from the stack, updates the widgets stacking, and updates the widget and cursor.
		"""

		if len(HarfangGUISceneGraph.widgets_containers_stack) <= 1:
			print("HarfangUI ERROR - Widgets containers stack is empty !")
		else:
			scrollbar_size = 20
			widget = HarfangGUISceneGraph.get_current_container()

			#Update workspace
			# Windows2D move don't affect scrollbars. Scrollbars only concerns simple widgets.
			
			w_size = widget["size"]
			mn = widget["workspace_min"]
			mx = widget["workspace_max"]
			mx.x += widget["margins"].x
			mx.y += widget["margins"].y
			widget["workspace_size"] = mx - mn
			ws_size = widget["workspace_size"]
			
			w_size.x, w_size.y = ws_size.x, ws_size.y
			if widget["flag_new"] or widget["flag_update_rest_size"]:
				widget["rest_size"].x, widget["rest_size"].y, widget["rest_size"].z = w_size.x, w_size.y, w_size.z
		
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

			bt = 0 #if widget["flag_invisible"] else widget["objects_dict"]["window_borders.1"]["border_thickness"]
			
			# Add scroll bars if necessary

			px, py = widget["scroll_position"].x - mn.x, widget["scroll_position"].y - mn.y

			if widget["flag_scrollbar_v"]:
				title_height = bt if (widget["flag_hide_title"] or widget["flag_invisible"])  else widget["components"]["widget_group_title"]["size"].y
				cursor = hg.Vec3(spos)
				cursor.x += w_size.x - scrollbar_size - bt
				cursor.y += title_height
				cls.set_cursor_pos(cursor)
				height = w_size.y - (bt + title_height)
				py = cls.scrollbar(widget["name"] + ".scoll_v", scrollbar_size, height, w_size.y, ws_size.y, spy, flag_reset_bar_v, cursor_auto = False, align=cls.HGUIAF_TOPLEFT, flag_horizontal = False) + mn.y
			
			if widget["flag_scrollbar_h"]:
				cursor = hg.Vec3(spos)
				cursor.y += w_size.y - scrollbar_size - bt
				cursor.x += bt
				cls.set_cursor_pos(cursor)
				width = w_size.x - 2 * bt if ws_size.y <= w_size.y else w_size.x - 2 * bt - scrollbar_size
				px = cls.scrollbar(widget["name"] + ".scoll_h", width, scrollbar_size, w_size.x, ws_size.x, spx, flag_reset_bar_h, cursor_auto = False, align=cls.HGUIAF_TOPLEFT, flag_vertical = True) + mn.x

			cls.set_scroll_position(widget["name"], px, py, 0)

			cls.pop_widgets_container()
			
			# Remove Main container if root window:
			if HarfangGUISceneGraph.get_current_container_child_depth() == 1:
				cls.pop_widgets_container() 


			cls.update_widgets_stacking(widget)
			cls.update_widget(widget)
			if widget["flag_2D"]:
				cls.update_cursor(widget)


	@classmethod
	def begin_window_2D(cls, widget_id, position:hg.Vec2, size:hg.Vec2, scale:float = 1, window_flags:int = 0, **args):
		n = len(HarfangGUISceneGraph.widgets_containers_stack)
		if  n==0 or (n > 0 and HarfangGUISceneGraph.widgets_containers_stack[0] == cls.main_widgets_container_2D):
			# HDPI scaling, only for 2D windows in Main 2D container:
			scale_hdpi = hg.GetWindowContentScale(cls.window).x
		else:
			scale_hdpi = 1 
		return cls.begin_window(widget_id, hg.Vec3(position.x, position.y, 0), hg.Vec3(0, 0, 0), hg.Vec3(size.x, size.y, 0), scale * scale_hdpi, window_flags | cls.HGUIWF_2D, **args)	# size: in pixels
	
	# scale: pixel size
	@classmethod
	def begin_window(cls, widget_id, position:hg.Vec3 , rotation:hg.Vec3, size:hg.Vec3, scale:float = 1, window_flags:int = 0, **args):
		
		cls.flag_same_line = False
		cls.flag_set_cursor_pos = False

		flag_2D = False if (window_flags & cls.HGUIWF_2D) == 0 else True
		flag_move = True if (window_flags & cls.HGUIWF_NoPointerMove) == 0 else False
		flag_hide_title = False if (window_flags & cls.HGUIWF_HideTitle) == 0 else True
		flag_invisible = False if (window_flags & cls.HGUIWF_Invisible) == 0 else True
		flag_hide_scrollbars = False if (window_flags & cls.HGUIWF_HideScrollbars) == 0 else True
		flag_overlay = False if (window_flags & cls.HGUIWF_Overlay) == 0 else True

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
					print("HarfangUI ERROR - 3D container can't be child of 2D container - " + widget_id)
					return False
		else:
			if HarfangGUISceneGraph.get_current_container_child_depth() == 0:
				HarfangGUISceneGraph.widgets_containers_stack.append(cls.main_widgets_container_2D)
		
		widget = cls.get_widget("window", widget_id, args)

		widget["widgets_stack"] = []
		
		widget["flag_2D"] = flag_2D
		widget["flag_move"] = flag_move
		widget["flag_hide_title"] = flag_hide_title
		widget["components"]["window_title"]["hidden"] = flag_hide_title
		widget["flag_invisible"] = flag_invisible
		widget["components"]["window_background"]["hidden"] = flag_invisible
		widget["flag_hide_scrollbars"] = flag_hide_scrollbars
		widget["flag_overlay"] = flag_overlay
		
		nsp = widget["new_scroll_position"]
		sp = widget["scroll_position"]
		sp.x, sp.y, sp.z = nsp.x, nsp.y, nsp.z

		widget["scale"].x =  widget["scale"].y = widget["scale"].z = scale
		
		if widget["flag_new"]:
			widget["position"].x, widget["position"].y, widget["position"].z = position.x, position.y * pyf, position.z
			widget["rotation"].x, widget["rotation"].y, widget["rotation"].z = rotation.x * rxf, rotation.y, rotation.z * rzf
			
			
			s = widget["size"]
			s.x, s.y, s.z = size.x, size.y, size.z
			
			thickness = 0 #if flag_invisible else cls.get_property_states_value(widget, "window_box_border_thickness",["focus"] )
			widget["default_cursor_start_line"].x = widget["margins"].x + thickness
			widget["default_cursor_start_line"].y = widget["margins"].y + thickness
			widget["objects_dict"]["window_title.2"]["text"] = cls.get_label_from_id(widget["name"])
		
		else:
			if not flag_move:
				widget["position"].x, widget["position"].y, widget["position"].z = position.x, position.y * pyf, position.z
				widget["rotation"].x, widget["rotation"].y, widget["rotation"].z = rotation.x * rxf, rotation.y, rotation.z * rzf

			if not (flag_hide_title or flag_invisible): #!!! ATTENTION if hide title or invisible change !!!
				widget["default_cursor_start_line"].y = widget["margins"].y + widget["components"]["window_title"]["size"].y

			if "mouse_move" in widget["states"]:
				if "MLB_down" not in cls.current_signals:
					cls.set_widget_state(widget, "mouse_idle")
					cls.set_ui_state(cls.UI_STATE_MAIN)
				elif cls.ui_state == cls.UI_STATE_WIDGET_MOUSE_FOCUS:
					cls.move_widgets_container(widget, "mouse")
					
			else:		
				if widget["flag_move"] and "MLB_pressed" in cls.current_signals and widget["name"] in cls.current_signals["MLB_pressed"]:
					cls.set_widget_state(widget, "mouse_move")
					cls.set_ui_state(cls.UI_STATE_WIDGET_MOUSE_FOCUS)
		
		cls.push_widgets_container(widget)
		return True


	@classmethod
	def end_window(cls):
		if len(HarfangGUISceneGraph.widgets_containers_stack) <= 1:
			print("HarfangUI ERROR - Widgets containers stack is empty !")
		else:
			scrollbar_size = 20
			widget = HarfangGUISceneGraph.get_current_container()

			#Update workspace
			# Windows2D move don't affect scrollbars. Scrollbars only concerns simple widgets.
			
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

			bt = 0 #if widget["flag_invisible"] else widget["objects_dict"]["window_borders.1"]["border_thickness"]
			
			# Add scroll bars if necessary

			px, py = widget["scroll_position"].x - mn.x, widget["scroll_position"].y - mn.y

			if widget["flag_scrollbar_v"]:
				title_height = bt if (widget["flag_hide_title"] or widget["flag_invisible"])  else widget["components"]["window_title"]["size"].y
				cursor = hg.Vec3(spos)
				cursor.x += w_size.x - scrollbar_size - bt
				cursor.y += title_height
				cls.set_cursor_pos(cursor)
				height = w_size.y - (bt + title_height)
				py = cls.scrollbar(widget["name"] + ".scoll_v", scrollbar_size, height, w_size.y, ws_size.y, spy, flag_reset_bar_v, align=cls.HGUIAF_TOPLEFT, cursor_auto = False, flag_horizontal = False) + mn.y
			
			if widget["flag_scrollbar_h"]:
				cursor = hg.Vec3(spos)
				cursor.y += w_size.y - scrollbar_size - bt
				cursor.x += bt
				cls.set_cursor_pos(cursor)
				width = w_size.x - 2 * bt if ws_size.y <= w_size.y else w_size.x - 2 * bt - scrollbar_size
				px = cls.scrollbar(widget["name"] + ".scoll_h", width, scrollbar_size, w_size.x, ws_size.x, spx, flag_reset_bar_h, align=cls.HGUIAF_TOPLEFT, cursor_auto = False, flag_horizontal = True) + mn.x

			cls.set_scroll_position(widget["name"], px, py, 0)

			cls.pop_widgets_container()
			
			# Remove Main container if root window:
			if HarfangGUISceneGraph.get_current_container_child_depth() == 1:
				cls.pop_widgets_container() 

			cls.update_widgets_stacking(widget)
			cls.update_widget(widget)


# ------------ Widgets system
	@classmethod
	def move_widget(cls, widget, v:hg.Vec3):
		widget["position"].x += v.x
		widget["position"].y += v.y
		widget["position"].z += v.z
		for w in widget["sub_widgets"]:
			w["position"].x += v.x
			w["position"].y += v.y
			w["position"].z += v.z

	@classmethod
	def same_line(cls):
		cls.flag_same_line= True
		cls.flag_set_cursor_pos = False
		cursor = HarfangGUISceneGraph.get_current_container()["cursor"]
		cursor.x = cls.last_widget["position"].x + cls.last_widget["rest_size"].x + cls.inner_line_space_size
		cursor.y = cls.last_widget["position"].y
		cursor.z = cls.last_widget["position"].z
	
	@classmethod
	def set_align(cls, align:int):
		container = HarfangGUISceneGraph.get_current_container()
		container["align"] = align

	@classmethod
	def set_line_space_size(cls,line_space_size:float):
		cls.line_space_size = line_space_size
	
	@classmethod
	def set_inner_line_space_size(cls,inner_line_space_size:float):
		cls.inner_line_space_size = inner_line_space_size

	@classmethod
	def get_cursor_position(cls):
		current_container = HarfangGUISceneGraph.get_current_container()
		return hg.Vec3(current_container["cursor"])

	@classmethod
	def set_cursor_pos(cls, position: hg.Vec3):
		cls.flag_set_cursor_pos = True
		cursor = HarfangGUISceneGraph.get_current_container()["cursor"]
		cursor.x, cursor.y, cursor.z = position.x, position.y, position.z
		cls.flag_same_line = False
	
	@classmethod
	def set_cursor_start_line(cls, position: hg.Vec3):
		csl = HarfangGUISceneGraph.get_current_container()["cursor_start_line"]
		csl.x, csl.y, csl.z = position.x, position.y, position.z

	@classmethod
	def new_widgets_row(cls,widget):
		return {"widgets":[widget],
				"max_height": widget["rest_size"].y,
				"width": widget["rest_size"].x,
				"align":cls.HGUIAF_LEFT,
				"v_align":cls.HGUIAF_CENTER,
				"fixed_position": False #If row is positionned by user with set_cursor_pos
				}

	@classmethod
	def update_cursor(cls, widget):
		if widget["cursor_auto"]:
			w_container = HarfangGUISceneGraph.get_current_container()
			cursor = w_container["cursor"]
			csl = w_container["cursor_start_line"]
			cursor.x = csl.x
			
			if not cls.flag_same_line:
				row = cls.new_widgets_row(widget)
				row["align"] = w_container["align"]
				row["v_align"] = w_container["v_align"]
				row["fixed_position"] = cls.flag_set_cursor_pos
				w_container["widgets_stack"].append(row)
				cls.flag_set_cursor_pos = False
			else:
				row = w_container["widgets_stack"][-1]
				row["widgets"].append(widget)
				row["width"] += cls.inner_line_space_size + widget["rest_size"].x
				row["max_height"] = max(row["max_height"], widget["rest_size"].y)
				cls.flag_same_line = False
			
			cursor.y = widget["position"].y + row["max_height"] + cls.line_space_size
			cursor.z = csl.z

			wpos_s = widget["position"]
			wpos_e = wpos_s + widget["rest_size"]
			wss, wse = w_container["workspace_min"], w_container["workspace_max"]
			wss.x = min(wss.x, wpos_s.x)
			wss.y = min(wss.y, wpos_s.y)
			wss.z = min(wss.z, wpos_s.z)
			
			wse.x = max(wse.x, wpos_e.x)
			wse.y = max(wse.y, wpos_e.y)
			wse.z = max(wse.z, wpos_e.z)

			cls.last_widget = widget
		else:
			cls.flag_same_line = False
			cls.flag_set_cursor_pos = False

	@classmethod
	def update_widget_states(cls, widget):
		widget["states"] = []
		for property in widget["properties"].values():
			for layer_id in range(len(property["layers"])):
				property_layer_state = property["layers"][layer_id]["current_state"]
				if property_layer_state not in widget["states"]:
					widget["states"].append(property_layer_state)

	@classmethod
	def set_widget_state(cls, widget, state_name):
		for property in widget["properties"].values():
			for layer_id in range(len(property["layers"])):
				property_layer = property["layers"][layer_id]
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
	def mouse_hover(cls, widget, pointer_id, pointer_pos):
		if cls.ui_state is not cls.UI_STATE_WIDGET_MOUSE_FOCUS:
			if widget["position"].x < pointer_pos.x < widget["position"].x + widget["size"].x + widget["offset"].x and widget["position"].y < pointer_pos.y < widget["position"].y + widget["size"].y + widget["offset"].y:
				if not ("mouse_hover" in cls.current_signals and widget["name"] in cls.current_signals["mouse_hover"]):
					if not "edit" in widget["states"]:
						cls.set_widget_state(widget, "mouse_hover")
				cls.send_signal("mouse_hover", widget["name"])
				return True
			else:
				cls.set_widget_state(widget, "idle")
				return False
		#If pointer is focused, update widget local pointer position
		else:
			if widget["position"].x < pointer_pos.x < widget["position"].x + widget["size"].x + widget["offset"].x and widget["position"].y < pointer_pos.y < widget["position"].y + widget["size"].y + widget["offset"].y:
				if pointer_id not in widget["pointers"]:
					widget["pointers"][pointer_id] = cls.new_pointer(pointer_id)
				if widget["pointers"][pointer_id]["pointer_local_position"] is None:
					widget["pointers"][pointer_id]["pointer_local_position"] = hg.Vec3(0, 0, 0)
				p = widget["pointers"][pointer_id]["pointer_local_position"]
				p.x, p.y = pointer_pos.x - widget["position"].x, pointer_pos.y - widget["position"].y
		return False
	
	@classmethod
	def update_mouse_click(cls, widget):
		if "mouse_hover" in cls.current_signals and widget["name"] in cls.current_signals["mouse_hover"]:
			if cls.mouse.Down(hg.MB_0):
				if not "edit" in widget["states"]:
					cls.set_widget_state(widget, "MLB_down")
				cls.send_signal("MLB_down", widget["name"])
			
			elif "MLB_down" in cls.current_signals and widget["name"] in cls.current_signals["MLB_down"]:
				if not "edit" in widget["states"]:
					cls.set_widget_state(widget, "mouse_hover")
				cls.send_signal("mouse_click", widget["name"])

	@classmethod
	def update_component(cls, widget, component):
		"""
		Updates a component of a widget.
		It first calculates the size of the component based on its type and the sizes of its primitives. 
		It then adjusts the position and size of each primitive within the component. 
		The function handles different types of components, including 'sliderbar', 'scrollbar', and others. 
		For each type, it adjusts the positions and sizes of the component's primitives accordingly. 
		The function also handles the stacking of primitives within the component, either horizontally or vertically, 
		and adjusts the size of the component based on its content size. 
		Finally, it aligns the stackable primitives and updates the position and size of responsive primitives.
		"""

		# Component display vars
		sx, sy = 0, 0
		flag_compute_size = False # "text", "input_text" and "texture" primitives affects component size. 
		cp = component["cursor_position"]
		cp.x, cp.y = 0, 0
		stackable_primitives = ["texture", "texture_toggle_fading","text_toggle_fading" ,"text", "input_text"] # All other primitives are size-responsive
		# Compute content size
		
		if component["type"] == "sliderbar":
		
			obj_bg = component["objects_dict"]["sliderbar.background"]
			obj_bar = component["objects_dict"]["sliderbar.bar"]
			obj_plot = component["objects_dict"]["sliderbar.plot"]
			
			obj_plot["size"].x = obj_plot["size"].y = obj_plot["radius"]
			total_size = (component["value_end"] - component["value_start"])
			t = (component["inertial_value"] - component["value_start"]) / total_size

			if component["flag_horizontal"]:
				obj_bar["size"].y = obj_bg["size"].y = component["bar_thickness"]
				tx = t * component["size"].x
				
				obj_bg["position"].x = 0
				obj_bg["position"].y = obj_plot["radius"] - obj_bg["size"].y / 2
				obj_bg["size"].x = component["size"].x
				
				obj_bar["position"].x = 0
				obj_bar["position"].y = obj_bg["position"].y
				obj_bar["size"].x = tx
				
				obj_plot["position"].x = tx + (1 - 2 * t) * obj_plot["radius"]
				obj_plot["position"].y = obj_plot["radius"]
				
				sx = component["size"].x
				sy = obj_plot["radius"] * 2
			
			else:
				obj_bar["size"].x = obj_bg["size"].x = component["bar_thickness"]
				ty = (1-t) * component["size"].y
				
				obj_bg["position"].y = 0
				obj_bg["position"].x = obj_plot["radius"] - obj_bg["size"].x / 2
				obj_bg["size"].y = component["size"].y
				
				obj_bar["position"].y = ty
				obj_bar["position"].x = obj_bg["position"].x
				obj_bar["size"].y = component["size"].y - ty
				
				obj_plot["position"].y = ty - (1 - 2 * t) * obj_plot["radius"]
				obj_plot["position"].x = obj_plot["radius"]
				
				sx = obj_plot["radius"] * 2
				sy = component["size"].y
			

			component["content_size"].x, component["content_size"].y = sx, sy
			component["size"].x = sx + component["margins"].x * 2
			component["size"].y = sy + component["margins"].y * 2
			for obj in [obj_bar, obj_bg, obj_plot]:
				obj["position"].x += component["margins"].x
				obj["position"].y += component["margins"].y
		
		elif component["type"] == "scrollbar":
			obj_bg = component["objects_dict"]["scrollbar.background"]
			obj_bar = component["objects_dict"]["scrollbar.bar"]
			if component["flag_horizontal"]:
				bar_height = component["scrollbar_thickness"]
				margin = max(0, component["size"].y - bar_height)
				s = component["size"].x - margin
				bar_width = component["part_size"] / component["total_size"] * s
				bar_pos = hg.Vec3(margin / 2 + component["scrollbar_position"] / component["total_size"] * s, margin / 2, 0)
			else:
				bar_width = component["scrollbar_thickness"]
				margin = max(0, component["size"].x - bar_width)
				s = component["size"].y - margin
				bar_height = component["part_size"] / component["total_size"] * s
				bar_pos = hg.Vec3(margin / 2, margin / 2 + component["scrollbar_position"] / component["total_size"] * s, 0)
						
			obj_bar["position"].x, obj_bar["position"].y = bar_pos.x, bar_pos.y
			obj_bar["size"].x, obj_bar["size"].y = bar_width, bar_height
			obj_bg["size"].x, obj_bg["size"].y = component["size"].x, component["size"].y

		else:
			for primitive in component["primitives"]:
				
				if primitive["type"] in stackable_primitives:
					
					flag_compute_size = True
					primitive["position"].x, primitive["position"].y = cp.x, cp.y
					tsx, tsy = -1, -1

					if primitive["type"] == "texture":
						if primitive["texture"] is not None:
							tsx, tsy = primitive["texture_size"].x, primitive["texture_size"].y
							tsx *= primitive["texture_scale"].x
							tsy *= primitive["texture_scale"].y
					
					elif primitive["type"] == "texture_toggle_fading":
						if primitive["textures"] is not None:
							tsx, tsy = primitive["texture_size"].x, primitive["texture_size"].y
							tsx *= primitive["texture_scale"].x
							tsy *= primitive["texture_scale"].y

					elif primitive["type"] == "text":
						if primitive["text"] is not None:
							txt_size = HarfangGUIRenderer.compute_text_size(cls.current_font_id, primitive["text"])
							tsx, tsy = txt_size.x, txt_size.y
							if primitive["forced_text_width"] is not None:
								if component["align"] == cls.HGUIAF_CENTER:
									primitive["position"].x += (primitive["forced_text_width"] - tsx) / 2
								tsx = primitive["forced_text_width"]
							tsx *= primitive["text_size"]
							tsy *= primitive["text_size"]

					elif primitive["type"] == "text_toggle_fading":
						if primitive["texts"] is not None:
							primitive["t"] = (cls.timestamp - primitive["toggle_t0"]) / hg.time_from_sec_f(primitive["fading_delay"])
							txt_size0 = primitive["texts_sizes"][primitive["toggle_idx"]] # HarfangGUIRenderer.compute_text_size(cls.current_font_id, primitive["texts"][primitive["toggle_idx"]])
							txt_size1 = primitive["texts_sizes"][primitive["toggle_idx_start"]]
							txt_d0 = primitive["texts_d"][primitive["toggle_idx"]]
							txt_d1 = primitive["texts_d"][primitive["toggle_idx_start"]]
							tsx, tsy = max(txt_size0.x, txt_size1.x), max(txt_size0.y, txt_size1.y)
							if primitive["forced_text_width"] is not None:
								tsx = primitive["forced_text_width"]

							if component["align"] == cls.HGUIAF_CENTER:
								if txt_size0.x < tsx:
									txt_d0.x = ((tsx - txt_size0.x) / 2) * primitive["text_size"]
								if txt_size1.x < tsx:
									txt_d1.x = ((tsx - txt_size1.x) / 2) * primitive["text_size"]
							else:
								txt_d0.x = 0
								txt_d1.x = 0

							tsx *= primitive["text_size"]
							tsy *= primitive["text_size"]
					
					elif primitive["type"] == "input_text":
						if primitive["display_text"] is not None:
							txt_size = HarfangGUIRenderer.compute_text_size(cls.current_font_id, primitive["display_text"])
							tsx, tsy = txt_size.x, txt_size.y
							if primitive["forced_text_width"] is not None:
								#if component["align"] == cls.HGUIAF_CENTER:
								#	dx = (primitive["forced_text_width"] * primitive["text_size"] - tsx) / 2
								#	primitive["position"].x += dx
								tsx = primitive["forced_text_width"]
							tsx *= primitive["text_size"]
							tsy *= primitive["text_size"]
					
					primitive["size"].x, primitive["size"].y = tsx, tsy #Keep the string size for special displays (keyboard cursor for inputs widgets...)
					
					#Stacking
					if component["stacking"] == cls.HGUI_STACK_HORIZONTAL:
						if tsx > 0:
							cp.x += tsx + component["space_size"]
							sy = max(sy, tsy)
					elif component["stacking"] == cls.HGUI_STACK_VERTICAL:
						if tsy > 0:
							cp.y += tsy + component["space_size"]
							sx = max(sx, tsx)
					#sx, sy = max(sx, tsx), max(sy, tsy)

			#Content size:
			if component["stacking"] == cls.HGUI_STACK_HORIZONTAL:
					sx = cp.x - component["space_size"]
			elif component["stacking"] == cls.HGUI_STACK_VERTICAL:
				sy = cp.y - component["space_size"]
		
			component["content_size"].x, component["content_size"].y = sx, sy
			
			#Component size from content size:
			if flag_compute_size:	
				component["size"].x, component["size"].y = sx, sy
			
			# /!\ If no stackable primitive, component size must be set specifically by widget_type function to avoid component size infinite growth
			component["size"].x += component["margins"].x * 2
			component["size"].y += component["margins"].y * 2

			# If componentsize is widget size proportionnal
			sf = component["size_factor"]
			if sf.x > 0:
				component["size"].x = max(component["size"].x, widget["size"].x * sf.x)
			if sf.y > 0:
				component["size"].y = max(component["size"].y, widget["size"].y * sf.y)
			if sf.z > 0:
				component["size"].z = max(component["size"].z, widget["size"].z * sf.z)
			
			# Align stackable primitives:
			for primitive in component["primitives"]:
				if primitive["type"] in stackable_primitives:
					dx, dy = 0, 0
					if component["align"] == cls.HGUIAF_LEFT:
						dx = component["margins"].x
						dy = (component["size"].y - primitive["size"].y) / 2
					elif component["align"] == cls.HGUIAF_CENTER:
						dx = (component["size"].x - component["content_size"].x) / 2
						dy = (component["size"].y - primitive["size"].y) / 2
					else:
						dx = component["margins"].x
						dy = component["margins"].y
					primitive["position"].x += dx
					primitive["position"].y += dy
					

			# Responsive primitives:
			for primitive in component["primitives"]:
				if primitive["type"] not in stackable_primitives:
					p = primitive["position"]
					s = primitive["size"]
					p.x, p.y, p.z = 0, 0, 0 # Implement offset ?
					s.x, s.y, s.z = component["size"].x, component["size"].y, component["size"].z

	
	@classmethod
	def reset_stack(cls, cursor_pos:hg.Vec3, container_size:hg.Vec3, stacking:int, align:int):
		if stacking == cls.HGUI_STACK_HORIZONTAL:
			if align == cls.HGUIAF_CENTER or align == cls.HGUIAF_LEFT or align == cls.HGUIAF_RIGHT:
				cursor_pos.x, cursor_pos.y, cursor_pos.z = 0, container_size.y / 2, 0
			elif align == cls.HGUIAF_TOP or align == cls.HGUIAF_TOPLEFT or align == cls.HGUIAF_TOPRIGHT:
				cursor_pos.x, cursor_pos.y, cursor_pos.z = 0, 0, 0
			elif align == cls.HGUIAF_BOTTOM or align == cls.HGUIAF_BOTTOMLEFT or align == cls.HGUIAF_BOTTOMRIGHT:
				cursor_pos.x, cursor_pos.y, cursor_pos.z = 0, container_size.y, 0
		
		elif stacking == cls.HGUI_STACK_VERTICAL:
			if align == cls.HGUIAF_CENTER or align == cls.HGUIAF_TOP or align == cls.HGUIAF_BOTTOM:
				cursor_pos.x, cursor_pos.y, cursor_pos.z = container_size.x / 2, 0, 0
			elif align == cls.HGUIAF_LEFT or align == cls.HGUIAF_TOPLEFT or align == cls.HGUIAF_BOTTOMLEFT:
				cursor_pos.x, cursor_pos.y, cursor_pos.z = 0, 0, 0
			elif align == cls.HGUIAF_RIGHT or align == cls.HGUIAF_TOPRIGHT or align == cls.HGUIAF_BOTTOMRIGHT:
				cursor_pos.x, cursor_pos.y, cursor_pos.z = container_size.x, 0, 0

	@classmethod
	def record_stack(cls, cursor_pos:hg.Vec3, element_position:hg.Vec3, container_size:hg.Vec3, stacking:int, align:int):
		if stacking == cls.HGUI_STACK_HORIZONTAL:
			if align == cls.HGUIAF_CENTER or align == cls.HGUIAF_LEFT or align == cls.HGUIAF_RIGHT:
				element_position.x, element_position.y, element_position.z = cursor_pos.x, cursor_pos.y - container_size.y / 2, cursor_pos.z
			elif align == cls.HGUIAF_TOP or align == cls.HGUIAF_TOPLEFT or align == cls.HGUIAF_TOPRIGHT:
				element_position.x, element_position.y, element_position.z = cursor_pos.x, cursor_pos.y, cursor_pos.z
			elif align == cls.HGUIAF_BOTTOM or align == cls.HGUIAF_BOTTOMLEFT or align == cls.HGUIAF_BOTTOMRIGHT:
				element_position.x, element_position.y, element_position.z = cursor_pos.x, cursor_pos.y - container_size.y, cursor_pos.z
		
		elif stacking == cls.HGUI_STACK_VERTICAL:
			if align == cls.HGUIAF_CENTER or align == cls.HGUIAF_TOP or align == cls.HGUIAF_BOTTOM:
				element_position.x, element_position.y, element_position.z = cursor_pos.x - container_size.x / 2, cursor_pos.y, cursor_pos.z
			elif align == cls.HGUIAF_LEFT or align == cls.HGUIAF_TOPLEFT or align == cls.HGUIAF_BOTTOMLEFT:
				element_position.x, element_position.y, element_position.z = cursor_pos.x, cursor_pos.y, cursor_pos.z
			elif align == cls.HGUIAF_RIGHT or align == cls.HGUIAF_TOPRIGHT or align == cls.HGUIAF_BOTTOMRIGHT:
				element_position.x, element_position.y, element_position.z = cursor_pos.x - container_size.x, cursor_pos.y, cursor_pos.z
				

	@classmethod
	def update_properties(cls, widget):
		# Applies properties
		for property_name, property in widget["properties"].items():
			if property_name in HarfangUISkin.properties:
				for layer_id in range(len(property["layers"])):
					layer = property["layers"][layer_id]
					state_delay = layer["states"][layer["current_state"]]["delay"]
					t = (cls.timestamp - layer["current_state_t0"]) / max(1e-5,hg.time_from_sec_f(state_delay))
					if abs(state_delay) < 1e-5 or t >= 1:
						layer["value"] = layer["value_end"]
					elif 0 <= t <1 :
							layer["value"] = HarfangUISkin.interpolate_values(layer["value_start"], layer["value_end"], t)
					if layer["operator"] == "set":
						property["value"] = layer["value"]
					elif layer["operator"] == "multiply":
						property["value"] *= layer["value"]
					elif layer["operator"] == "add":
						property["value"] += layer["value"]
					elif layer["operator"] == "max":
						property["value"] = max_type(layer["value"], property["value"])
					elif layer["operator"] == "min":
						property["value"] = min_type(layer["value"], property["value"])
		
				if "linked_value" in property:
					lv = property["linked_value"]
					
					for obj in lv["objects"]:
						v = property["value"]
						o = lv["operator"]
						if o == "set":
							obj[lv["name"]] = v
						elif o == "add":
							obj[lv["name"]] += v
						elif o == "multiply":
							obj[lv["name"]] += v
						elif o == "max":
							obj[lv["name"]] = max_type(v, obj[lv["name"]])
						elif o == "min":
							obj[lv["name"]] = min_type(v, obj[lv["name"]])

	@classmethod
	def update_widget(cls, widget):
		mn = hg.Vec3(inf, inf, inf)
		mx = hg.Vec3(-inf, -inf, -inf)
		cp = widget["cursor"]
		if widget["classe"] == "widgets_container":
			cp.x, cp.y, cp.z = 0, 0, 0
		else:
			cls.reset_stack(cp, widget["size"], widget["stacking"], widget["align"])

		cls.update_properties(widget)

		if widget["components_order"] == cls.HGUI_ORDER_DEFAULT:
			idx_s, idx_e, stp = 0, len(widget["components_render_order"]), 1
		elif widget["components_order"] == cls.HGUI_ORDER_REVERSE:
			idx_s, idx_e, stp = len(widget["components_render_order"])-1, -1, -1

		for component_idx in range(idx_s, idx_e, stp):
			component = widget["components_render_order"][component_idx]
			if component["hidden"]:
				continue
			cls.update_component(widget, component)
			if component["cursor_auto"]:
				#Component positionning:

				cls.record_stack(cp, component["position"], component["size"], widget["stacking"], widget["align"])
				
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
			
			#Cursor stacking:
			if component["cursor_auto"]:
				if widget["stacking"] == cls.HGUI_STACK_HORIZONTAL:
					cp.x += component["size"].x + component["offset"].x + widget["space_size"]
				elif widget["stacking"] == cls.HGUI_STACK_VERTICAL:
					cp.y += component["size"].y + component["offset"].y + widget["space_size"]

		ws = mx - mn
		widget["size"] = ws
		
		if widget["classe"] != "widgets_container":
			# Alignment
			if widget["flag_new"] or widget["flag_update_rest_size"]: # Is that condition ok for rest_size setup ?
				widget["rest_size"].x, widget["rest_size"].y, widget["rest_size"].z = ws.x, ws.y, ws.z
				widget["flag_update_rest_size"] = False
			
			delta = (widget["rest_size"] - widget["size"]) / 2

			if widget["align"] == cls.HGUIAF_CENTER: 
				widget["offset"].x, widget["offset"].y  = delta.x, delta.y
			elif widget["align"] == cls.HGUIAF_TOP: 
				widget["offset"].x, widget["offset"].y = delta.x, 0
			elif widget["align"] == cls.HGUIAF_BOTTOM: 
				widget["offset"].x, widget["offset"].y = delta.x, delta.y * 2
			elif widget["align"] == cls.HGUIAF_LEFT:
				widget["offset"].x, widget["offset"].y = 0, delta.y
			elif widget["align"] == cls.HGUIAF_RIGHT: 
				widget["offset"].x, widget["offset"].y = delta.x * 2, delta.y
			elif widget["align"] == cls.HGUIAF_TOPLEFT: 
				widget["offset"].x, widget["offset"].y = 0, 0
			elif widget["align"] == cls.HGUIAF_TOPRIGHT: 
				widget["offset"].x, widget["offset"].y = delta.x * 2, 0
			elif widget["align"] == cls.HGUIAF_BOTTOMLEFT: 
				widget["offset"].x, widget["offset"].y = 0, delta.y * 2
			elif widget["align"] == cls.HGUIAF_BOTTOMRIGHT: 
				widget["offset"].x, widget["offset"].y = delta.x * 2, delta.y * 2
		
		# Max size (used to compute window workspace)
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
			HarfangGUISceneGraph.set_container_display_list(widgets_container["name"])
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
				widgets_container["frame_buffer"] = None
				widgets_container["color_texture"] = None
				widgets_container["depth_texture"] = None
			fb_size.x, fb_size.y = fb_size_x, fb_size_y

		if widgets_container["frame_buffer"] is None:
			
			widgets_container["color_texture"] = hg.CreateTexture(int(fb_size.x * HarfangGUIRenderer.frame_buffers_scale), int(fb_size.y* HarfangGUIRenderer.frame_buffers_scale), widgets_container["name"] + "_ctex", hg.TF_RenderTarget | hg.TF_SamplerMinAnisotropic, hg.TF_RGBA8)
			widgets_container["depth_texture"] =  hg.CreateTexture(int(fb_size.x* HarfangGUIRenderer.frame_buffers_scale), int(fb_size.y* HarfangGUIRenderer.frame_buffers_scale), widgets_container["name"] + "_dtex", hg.TF_RenderTarget, hg.TF_D32F)
			widgets_container["frame_buffer"] = hg.CreateFrameBuffer(widgets_container["color_texture"], widgets_container["depth_texture"], widgets_container["name"] + "_fb")
	
	@classmethod
	def build_widgets_container_2Dcontainers(cls, widgets_container, containers_2D_children):
		#call AFTER build_widget(), and BEFORE build_widgets_container_overlays()
		#widget states already updated
		for container in reversed(containers_2D_children):
			if container["name"] in cls.widgets: #Controls if container updated by user in this frame
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

			if component["overlay"] and not component["hidden"]:
				cls.build_primitives(widgets_container, component, matrix, cpos, opacity)

	@classmethod
	def build_widget(cls, widgets_container, matrix, widget):

		HarfangGUISceneGraph.set_container_display_list(widgets_container["name"])
		cls.update_widget_states(widget)
		
		opacity = hg.Color(1, 1, 1, 1 if widget["classe"] == "widgets_container" else widget["opacity"])

		if "scroll_position" in widget:
			scroll_pos = widget["scroll_position"]
		else:
			scroll_pos = hg.Vec3.Zero

		for component in widget["components_render_order"]:
			if component["hidden"] or component["overlay"]:
				continue
			cpos = component["position"] + component["offset"] + scroll_pos
			cls.build_primitives(widget, component, matrix, cpos, opacity)
			

	@classmethod
	def build_primitives(cls, widget, component, matrix, cpos, opacity):
		for primitive in component["primitives"]:
			if not primitive["hidden"]:
				ppos = cpos + primitive["position"]
				primitive_id = primitive["type"]
				if primitive_id == "box":
					HarfangGUISceneGraph.add_box(matrix, ppos, primitive["size"], primitive["background_color"] * opacity)
					HarfangGUISceneGraph.add_box_border(matrix, ppos, primitive["size"], primitive["border_thickness"], primitive["border_color"] * opacity)
				elif primitive_id == "filled_box":
					HarfangGUISceneGraph.add_box(matrix, ppos, primitive["size"],primitive["background_color"] * opacity)
				elif primitive_id == "box_borders":
					HarfangGUISceneGraph.add_box_border(matrix, ppos, primitive["size"], primitive["border_thickness"], primitive["border_color"] * opacity)

				elif primitive_id == "rounded_box":
					HarfangGUISceneGraph.add_rounded_box(matrix, ppos, primitive["size"],primitive["background_color"] * opacity, primitive["corner_radius"])
					HarfangGUISceneGraph.add_rounded_border(matrix, ppos, primitive["size"], primitive["border_thickness"], primitive["border_color"] * opacity, primitive["corner_radius"])
				elif primitive_id == "filled_rounded_box":
					HarfangGUISceneGraph.add_rounded_box(matrix, ppos, primitive["size"],primitive["background_color"] * opacity, primitive["corner_radius"])
				elif primitive_id == "rounded_box_borders":
					HarfangGUISceneGraph.add_rounded_border(matrix, ppos, primitive["size"], primitive["border_thickness"], primitive["border_color"] * opacity, primitive["corner_radius"])

				elif primitive_id == "circle":
					HarfangGUISceneGraph.add_circle(matrix, ppos, primitive["radius"], primitive["border_color"] * opacity)
					HarfangGUISceneGraph.add_circle(matrix, ppos, primitive["radius"] - primitive["border_thickness"], primitive["background_color"] * opacity)
				
				elif primitive_id == "text":
					if primitive["text"] is not None:
						HarfangGUISceneGraph.add_text(matrix, ppos, primitive["text_size"], primitive["text"], cls.current_font_id, primitive["text_color"] * opacity)

				elif primitive_id == "input_text":
					if primitive["display_text"] is not None:
						HarfangGUISceneGraph.add_text(matrix, ppos, primitive["text_size"], primitive["display_text"], cls.current_font_id, primitive["text_color"] * opacity)
						if "edit" in widget["states"]:
							idx = cls.kb_cursor_pos - primitive["display_text_start_idx"]
							tc_txt = primitive["display_text"][:idx]
							tc_size = HarfangGUIRenderer.compute_text_size(cls.current_font_id, tc_txt)
							tc_size *= primitive["text_size"]
							p = hg.Vec3(ppos)
							p.x += tc_size.x
							HarfangGUISceneGraph.add_box(matrix,  p, hg.Vec3(2, primitive["size"].y, 0), primitive["cursor_color"] * opacity)
					
				elif primitive_id == "texture":
					if primitive["texture"] is not None:
						HarfangGUISceneGraph.add_texture_box(matrix, ppos, primitive["texture_scale"]  * primitive["texture_size"], primitive["texture_color"] * opacity, primitive["texture"])

				elif primitive_id == "texture_toggle_fading":
						if primitive["textures"] is not None:
							fading = False
							if "toggle_t0" not in primitive:
								texture = primitive["textures"][primitive["toggle_idx"]]
							else:
								t = (cls.timestamp - primitive["toggle_t0"]) / hg.time_from_sec_f(primitive["fading_delay"])
								if t >= 1:
									texture = primitive["textures"][primitive["toggle_idx"]]
								else:
									fading = True
									a = primitive["texture_color"].a
									cs = hg.Color(primitive["texture_color"])
									ce = hg.Color(cs)
									cs.a = (1 - t) * a
									ce.a = t * a
									texture_s = primitive["textures"][primitive["toggle_idx_start"]]
									texture_e = primitive["textures"][primitive["toggle_idx"]]

									
							if fading:
								HarfangGUISceneGraph.add_texture_box(matrix, ppos, primitive["texture_scale"]  * primitive["texture_size"], ce * opacity, texture_e)
								HarfangGUISceneGraph.add_texture_box(matrix, ppos, primitive["texture_scale"]  * primitive["texture_size"], cs * opacity, texture_s)

							else:
								HarfangGUISceneGraph.add_texture_box(matrix, ppos, primitive["texture_scale"]  * primitive["texture_size"], primitive["texture_color"] * opacity, texture)

				elif primitive_id == "text_toggle_fading":
						if primitive["texts"] is not None:
							fading = False
							
							t = primitive["t"]
							if t >= 1:
								text = primitive["texts"][primitive["toggle_idx"]]
								p = hg.Vec3(ppos)
								p.x += primitive["texts_d"][primitive["toggle_idx"]].x
							else:
								fading = True
								a = primitive["text_color"].a
								cs = hg.Color(primitive["text_color"])
								ce = hg.Color(cs)
								cs.a = (1 - t) * a
								ce.a = t * a
								text_s = primitive["texts"][primitive["toggle_idx_start"]]
								text_e = primitive["texts"][primitive["toggle_idx"]]
								ps = hg.Vec3(ppos)
								ps.x += primitive["texts_d"][primitive["toggle_idx_start"]].x
								pe = hg.Vec3(ppos)
								pe.x += primitive["texts_d"][primitive["toggle_idx"]].x

									
							if fading:
								HarfangGUISceneGraph.add_text(matrix, ps, primitive["text_size"], text_s, cls.current_font_id, cs * opacity)
								HarfangGUISceneGraph.add_text(matrix, pe, primitive["text_size"], text_e, cls.current_font_id, ce * opacity)

							else:
								HarfangGUISceneGraph.add_text(matrix, p, primitive["text_size"], text, cls.current_font_id, primitive["text_color"] * opacity)

	@classmethod
	def activate_mouse_VR(cls, flag: bool):
		cls.flag_use_mouse_VR = flag
		if flag:
			pass #hg.DisableCursor()
		else:
			hg.ShowCursor()

	@classmethod
	def set_container_align_front(cls,container):
		#For the moment, only 2D container are aligned to front
		if container["flag_2D"]:
			parent = container["parent"]
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
		if cls.ui_state == cls.UI_STATE_MOUSE_DOWN_OUT:
			return

		focussed_container = cls.raycast_pointer_position("mouse")
		
		if focussed_container is not None:
			
			cls.focussed_containers.append(focussed_container)

			pointer_position = hg.Vec2(focussed_container["pointers"]["mouse"]["pointer_local_position"])

			# Overlay components hover test (not affected by scroll position)
			# e.g.: for widgets below a window title not to be detected as hovered.
			flag_hover_container = False
			hoverable_primitives = ["box", "filled_box", "rounded_box", "filled_rounded_box"]
			for component in focussed_container["components_render_order"]:
				if component["overlay"] and not component["hidden"]:
					
					for primitive in component["primitives"]:
						if primitive["type"] in hoverable_primitives: 
							cpos = component["position"] + component["offset"]
							csize = component["size"]
							if cpos.x < pointer_position.x < cpos.x + csize.x and cpos.y < pointer_position.y < cpos.y + csize.y:
								flag_hover_container = True # flag_hover_container: True if only container is hovered, and no container's child
							break
					if flag_hover_container:
						break
			
			# Widgets hover test (affected by scroll position)
			
			pointer_position.x += focussed_container["scroll_position"].x
			pointer_position.y += focussed_container["scroll_position"].y
			
			flag_hover_widget = False
			for widget in reversed(focussed_container["children_order"]):
				if flag_hover_widget or flag_hover_container:
					cls.set_widget_state(widget, "idle")
				else:
					flag_hover_widget = cls.mouse_hover(widget, "mouse", pointer_position)
					cls.update_mouse_click(widget)
			
			if not flag_hover_widget:
				flag_hover_container = True

			if cls.ui_state is not cls.UI_STATE_WIDGET_MOUSE_FOCUS:
				cls.set_widget_state(focussed_container, "mouse_hover")
				cls.send_signal("mouse_hover", focussed_container["name"])
				if flag_hover_container:
					cls.update_mouse_click(focussed_container)
			
			if "MLB_pressed" in cls.current_signals:
				cls.set_widget_state(focussed_container, "focus")
				cls.set_container_align_front(focussed_container)
		

		elif "MLB_pressed" in cls.new_signals:
			cls.set_ui_state(cls.UI_STATE_MOUSE_DOWN_OUT)
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
	def get_label_from_id(cls, widget_id:str):
		if "##" in widget_id:
			return widget_id[:widget_id.find("##")]
		else:
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
			if cls.flag_vr and cls.flag_use_mouse_VR:
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
			parent = widgets_container["parent"]
			p_pointer = parent["pointers"][controller_id]
			if p_pointer["pointer_world_position"] is not None:
				impact_2Dpos = window_inv * p_pointer["pointer_world_position"]
				# !!! Get an eye on scroll position hierarchy !!!
				impact_2Dpos.x += parent["scroll_position"].x
				impact_2Dpos.y += parent["scroll_position"].y
		
				if 0 < impact_2Dpos.x < widgets_container["size"].x and 0 < impact_2Dpos.y < widgets_container["size"].y:
					wc_pointer["pointer_world_position"] = p_pointer["pointer_world_position"] # !!! New Vec3 if necessary !!!
					flag_pointer_in = True
				impact_2Dpos = hg.Vec2(impact_2Dpos.x, impact_2Dpos.y)
		else:
			#window_pos = hg.GetT(widgets_container["world_matrix"])
			#window_size = widgets_container["size"]
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
		wc = widgets_container
		while wc["parent"]["name"] != "MainContainer2D": #Find a way to resolve this hierarchy with matrix
			local_pointer.x +=  wc["parent"]["scroll_position"].x
			local_pointer.y +=  wc["parent"]["scroll_position"].y
			wc =  wc["parent"]
		
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
	def start_edit_string(cls, widget, primitive):
		primitive["text_mem"] = primitive["text"]
		cls.set_widget_state(widget, "edit")
		cls.set_ui_state(cls.UI_STATE_WIDGET_KEYBOARD_FOCUS) # Get keyboard control
		cls.set_widget_state(widget,"idle")
		cls.kb_cursor_pos = len(primitive["text"])
		cls.ascii_connect = hg.OnTextInput.Connect(on_key_press)

	@classmethod
	def stop_edit_string(cls, widget, primitive):
		cls.set_widget_state(widget, "no_edit")
		cls.set_ui_state(cls.UI_STATE_MAIN)	# Resume keyboard control to ui
		primitive["text"] = primitive["text_mem"]
		widget["flag_update_rest_size"] = True
		if cls.ascii_connect is not None:
			hg.OnTextInput.Disconnect(cls.ascii_connect)
			cls.ascii_connect = None
	
	
	@classmethod
	def clip_input_text(cls, widget, primitive):
		if "display_text_start_idx" not in primitive:
					primitive["display_text_start_idx"] = 0
		if "display_text" not in primitive:
			primitive["display_text"] = primitive["text"]

		if primitive["display_text_start_idx"] > cls.kb_cursor_pos:
					primitive["display_text_start_idx"] = max(0, cls.kb_cursor_pos - 10)

		if primitive["forced_text_width"] is not None:
			txt_size = (HarfangGUIRenderer.compute_text_size(cls.current_font_id, primitive["text"])).x
			if txt_size > primitive["forced_text_width"]:
				
				t1 = (HarfangGUIRenderer.compute_text_size(cls.current_font_id, primitive["text"][primitive["display_text_start_idx"]:cls.kb_cursor_pos])).x
				str_size = cls.kb_cursor_pos - primitive["display_text_start_idx"]
				strt = primitive["display_text_start_idx"]
				while t1 > primitive["forced_text_width"] and str_size >= 2:
					str_size = int(2 * str_size / 3)
					strt = cls.kb_cursor_pos - str_size
					t1 = (HarfangGUIRenderer.compute_text_size(cls.current_font_id, primitive["text"][strt:cls.kb_cursor_pos])).x
				primitive["display_text_start_idx"] = strt
			
			primitive["display_text"] = cls.clip_text(primitive["text"], primitive["display_text_start_idx"], primitive["forced_text_width"])

		else:
			primitive["display_text"] = primitive["text"]
			primitive["display_text_start_idx"] = 0
	
	@classmethod
	def clip_text(cls, text, start_idx, max_width):
		l_disp = len(text)
		t_disp = (HarfangGUIRenderer.compute_text_size(cls.current_font_id, text[start_idx:l_disp])).x
		if t_disp <= max_width:
			return text[start_idx:l_disp]
		while t_disp > max_width:
			l_disp -= 1
			t_disp = (HarfangGUIRenderer.compute_text_size(cls.current_font_id, text[start_idx:l_disp]+"..." )).x

		return text[start_idx:l_disp] + "..."

	@classmethod
	def update_edit_string(cls, widget, primitive_id):
		
		primitive = widget["objects_dict"][primitive_id]
		flag_move_cursor = False
		
		if not "edit" in widget["states"]:
			if "mouse_click" in cls.current_signals and widget["name"] in cls.current_signals["mouse_click"]:
				cls.start_edit_string(widget, primitive)

		else:
			if "MLB_pressed" in cls.current_signals and not widget["name"] in cls.current_signals["MLB_pressed"]:
				cls.stop_edit_string(widget, primitive)
			
			elif cls.ui_state == cls.UI_STATE_WIDGET_KEYBOARD_FOCUS:

				str_l = len(primitive["text"])

				flag_k_down = False
				for k in range(hg.K_Last):
					if cls.keyboard.Down(k):
						if cls.kb_cursor_current_key_down != k:
							cls.kb_cursor_down_t0 = cls.timestamp
							cls.kb_cursor_current_key_down = k
							t = -1
							flag_k_down = True
							break
						else:
							t = (cls.timestamp - cls.kb_cursor_down_t0) / hg.time_from_sec_f(cls.kb_cursor_repeat_delay)
							flag_k_down = True
							break
				
				if not flag_k_down:
					cls.kb_cursor_current_key_down = None

				elif t<0 or t>1:
				
					if cls.kb_cursor_current_key_down == hg.K_Right and cls.kb_cursor_pos < str_l:
							cls.kb_cursor_pos +=1
							flag_move_cursor = True
						
					elif cls.kb_cursor_current_key_down == hg.K_Left and cls.kb_cursor_pos > 0:
						cls.kb_cursor_pos -=1
						flag_move_cursor = True
					
					elif cls.kb_cursor_current_key_down == hg.K_Backspace and cls.kb_cursor_pos > 0:
						cls.kb_cursor_pos -= 1
						primitive["text"] = primitive["text"][:cls.kb_cursor_pos] + primitive["text"][cls.kb_cursor_pos+1:]
						widget["flag_update_rest_size"] = True
						flag_move_cursor = True
			
					elif cls.kb_cursor_current_key_down == hg.K_Suppr and cls.kb_cursor_pos < str_l:
						primitive["text"] = primitive["text"][:cls.kb_cursor_pos] + primitive["text"][cls.kb_cursor_pos+1:]
						widget["flag_update_rest_size"] = True
						flag_move_cursor = True

					elif cls.kb_cursor_current_key_down == hg.K_Return or cls.kb_cursor_current_key_down == hg.K_Enter:
						cls.set_widget_state(widget, "no_edit")
						cls.set_ui_state(cls.UI_STATE_MAIN)	# Resume keyboard control to ui
						widget["flag_update_rest_size"] = True
						cls.clip_input_text(widget, primitive)
						return True #String changed
					else:
						if cls.ascii_code is not None:
							primitive["text"] = primitive["text"][:cls.kb_cursor_pos] + cls.ascii_code + primitive["text"][cls.kb_cursor_pos:]
							cls.kb_cursor_pos += 1
							widget["flag_update_rest_size"] = True
							cls.ascii_code = None
							flag_move_cursor = True

		if flag_move_cursor or widget["flag_new"] or widget["flag_update_rest_size"]:
			cls.clip_input_text(widget, primitive)
		return False #String unchanged


	# ------------ Widgets ui


	@classmethod
	def info_text(cls, widget_id, text, **args):
		widget = cls.get_widget("info_text", widget_id, args)
		widget["objects_dict"]["info_text.1"]["text"] = text
		widget["position"] = cls.get_cursor_position()
		cls.update_widget(widget)
		cls.update_cursor(widget)

	@classmethod
	def image(cls, widget_id, texture_path, image_size: hg.Vec2, **args):
		widget = cls.get_widget("info_image", widget_id, args)
		obj_label = widget["objects_dict"]["info_image_label.1"]
		widget["position"] = cls.get_cursor_position()
		if "show_label" in args:
			widget["components"]["info_image_label"]["hidden"] = not args["show_label"]
		else:
			widget["components"]["info_image_label"]["hidden"] = True
		obj = widget["objects_dict"]["info_image.1"]
		obj["texture_size"].x = image_size.x
		obj["texture_size"].y = image_size.y
		obj["texture"] = texture_path
		obj_label["text"] = cls.get_label_from_id(widget_id)
		cls.update_widget(widget)
		cls.update_cursor(widget)

	@classmethod
	def input_text(cls, widget_id, text = None, **args):
		widget = cls.get_widget("input_text", widget_id, args)
		obj_text = widget["objects_dict"]["input_box.2"]
		obj_label = widget["objects_dict"]["basic_label.1"]
		if "forced_text_width" in args:
			obj_text["forced_text_width"] = args["forced_text_width"]
		else:
			obj_text["forced_text_width"] = 150
		if text != obj_text["text"]:
			widget["flag_update_rest_size"] = True
			obj_text["display_text"] = text
		if text is not None:
			obj_text["text"] = text
		
		flag_changed = cls.update_edit_string(widget, "input_box.2")

		if "show_label" in args:
			widget["components"]["basic_label"]["hidden"] = not args["show_label"]
		else:
			widget["components"]["basic_label"]["hidden"] = False

		widget["position"] = cls.get_cursor_position()
		
		obj_label["text"] = cls.get_label_from_id(widget_id)
		cls.update_widget(widget)
		cls.update_cursor(widget)

		return flag_changed, obj_text["text"]


	@classmethod
	def button(cls, widget_id, **args):
		widget = cls.get_widget("button", widget_id, args)
		obj_label = widget["objects_dict"]["button_component.2"]
		mouse_click = False
		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			mouse_click = True
		obj_label["text"] = cls.get_label_from_id(widget_id)
		widget["position"] = cls.get_cursor_position()
		cls.update_widget(widget)
		cls.update_cursor(widget)
		return mouse_click, "MLB_down" in widget["states"]

	@classmethod
	def button_image(cls, widget_id, texture_path, image_size: hg.Vec2, **args):
		widget = cls.get_widget("image_button", widget_id, args)
		obj_texture = widget["objects_dict"]["image_button.2"]
		obj_label = widget["objects_dict"]["image_button.3"]
		mouse_click = False
		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			mouse_click = True
		widget["position"] = cls.get_cursor_position()
		if "show_label" in args and args["show_label"]:
			obj_label["text"] = cls.get_label_from_id(widget_id)
			obj_label["hidden"] = False
		else:
			obj_label["hidden"] = True
		obj_texture["texture_size"].x = image_size.x
		obj_texture["texture_size"].y = image_size.y
		obj_texture["texture"] = texture_path
		
		cls.update_widget(widget)
		cls.update_cursor(widget)
		return mouse_click, "MLB_down" in widget["states"]
	

	@classmethod
	def check_box(cls, widget_id, checked: bool, **args):
		widget = cls.get_widget("check_box", widget_id, args)
		obj_label = widget["objects_dict"]["basic_label.1"]
		mouse_click = False
		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			checked = not checked
			mouse_click = True
		
		if checked:
			cls.set_widget_state(widget, "checked")
		else:
			cls.set_widget_state(widget,"unchecked")
		
		if "show_label" in args:
			widget["components"]["basic_label"]["hidden"] = not args["show_label"]
		else:
			widget["components"]["basic_label"]["hidden"] = False

		obj_label["text"] = cls.get_label_from_id(widget_id)
		widget["position"] = cls.get_cursor_position()
		
		cls.update_widget(widget)
		cls.update_cursor(widget)

		return mouse_click, checked

	@classmethod
	def toggle_image_button(cls, widget_id, textures_paths: list, current_idx, image_size: hg.Vec2, **args):
		widget = cls.get_widget("toggle_image_button", widget_id, args)
		obj_label = widget["objects_dict"]["basic_label.1"]
		obj_textures = widget["objects_dict"]["toggle_image.textures"]
		mouse_click = False
		
		# !!! Extract to a primitive function ? - Set toggle image current idx
		current_idx_clamp = min(len(textures_paths)-1, current_idx)
		if obj_textures["toggle_idx"] != current_idx_clamp:
			obj_textures["toggle_idx_start"] = obj_textures["toggle_idx"]
			obj_textures["toggle_idx"] = current_idx_clamp
			obj_textures["toggle_t0"] = cls.timestamp

		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			mouse_click = True
			current_idx = (current_idx + 1) % len(textures_paths)
		
		if "show_label" in args:
			widget["components"]["basic_label"]["hidden"] = not args["show_label"]
		else:
			widget["components"]["basic_label"]["hidden"] = True
		obj_label["text"] = cls.get_label_from_id(widget_id)

		widget["position"] = cls.get_cursor_position()
		obj_textures["texture_size"].x = image_size.x
		obj_textures["texture_size"].y = image_size.y
		obj_textures["textures"] = textures_paths
		cls.update_widget(widget)
		cls.update_cursor(widget)
		return mouse_click, current_idx
	
	@classmethod
	def scrollbar(cls, widget_id, width, height, part_size, total_size, scroll_position, flag_reset, **args):
		widget = cls.get_widget("scrollbar", widget_id, args)
		comp_sb = widget["objects_dict"]["scrollbar"]
		
		if "flag_horizontal" in args:
			comp_sb["flag_horizontal"] = args["flag_horizontal"]
		flag_horizontal = comp_sb["flag_horizontal"]
		
		comp_sb["size"].x = width if flag_horizontal else max(comp_sb["scrollbar_thickness"], width)
		comp_sb["size"].y = max(comp_sb["scrollbar_thickness"], height) if flag_horizontal else height

		if scroll_position is None:
					scroll_position = comp_sb["scrollbar_position_dest"]

		# Scroll using pointer
		if "mouse_move" in widget["states"]:
			if "MLB_down" not in cls.current_signals:
				cls.set_widget_state(widget, "mouse_idle")
				cls.set_ui_state(cls.UI_STATE_MAIN)
			elif cls.ui_state == cls.UI_STATE_WIDGET_MOUSE_FOCUS:
				pointer_dt = HarfangGUISceneGraph.get_current_container()["pointers"]["mouse"]["pointer_local_dt"]
				s = total_size / (comp_sb["size"].x if flag_horizontal else comp_sb["size"].y)
				scroll_step = pointer_dt.x if flag_horizontal else pointer_dt.y
				scroll_position += scroll_step * s
		else:
			if "MLB_pressed" in cls.current_signals and widget["name"] in cls.current_signals["MLB_pressed"]:
				cls.set_widget_state(widget, "mouse_move")
				cls.set_ui_state(cls.UI_STATE_WIDGET_MOUSE_FOCUS)

		# Scroll with mouse wheel
		if cls.current_focused_widget is not None:
			if cls.current_focused_widget == widget["parent"]:
				mw = cls.mouse.Wheel()
				if not cls.keyboard.Down(hg.K_LShift) and not flag_horizontal:
					s = total_size / comp_sb["size"].y
					scroll_position -= mw * s * 20
				elif cls.keyboard.Down(hg.K_LShift) and flag_horizontal:
					s = total_size / comp_sb["size"].x
					scroll_position += mw * s * 20
		
		comp_sb["part_size"] = part_size
		comp_sb["total_size"] = total_size
		comp_sb["scrollbar_position_dest"] = max(0, min(total_size - part_size, scroll_position))

		widget["position"] = cls.get_cursor_position()
		cls.update_widget(widget)
		cls.update_cursor(widget)
		if flag_reset:
			comp_sb["scrollbar_position"] = comp_sb["scrollbar_position_dest"]
		else:
			comp_sb["scrollbar_position"] += (comp_sb["scrollbar_position_dest"] - comp_sb["scrollbar_position"]) * comp_sb["bar_inertia"]
		return comp_sb["scrollbar_position"]


	@classmethod
	def radio_image_button(cls, widget_id, texture_path, current_idx, radio_idx, image_size: hg.Vec2 = None, **args):
		widget = cls.get_widget("radio_image_button", widget_id, args)
		obj_texture = widget["objects_dict"]["radio_image_button.2"]
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
		obj_texture["texture_size"].x = image_size.x
		obj_texture["texture_size"].y = image_size.y
		obj_texture["texture"] = texture_path
		cls.update_widget(widget)
		cls.update_cursor(widget)
		return mouse_click, current_idx

	@classmethod
	def toggle_button(cls, widget_id, texts: list, current_idx, **args):
		widget = cls.get_widget("toggle_button", widget_id, args)
		obj_text = widget["objects_dict"]["toggle_button.texts"]
		obj_label = widget["objects_dict"]["basic_label.1"]
		
		if "show_label" in args:
			widget["components"]["basic_label"]["hidden"] = not args["show_label"]
		else:
			widget["components"]["basic_label"]["hidden"] = True
		obj_label["text"] = cls.get_label_from_id(widget_id)
		# !!! Extract to a primitive function ? - Set toggle image current idx
		current_idx_clamp = min(len(texts)-1, current_idx)
		if obj_text["toggle_idx"] != current_idx_clamp:
			obj_text["toggle_idx_start"] = obj_text["toggle_idx"]
			obj_text["toggle_idx"] = current_idx_clamp
			obj_text["toggle_t0"] = cls.timestamp
		
		# Setup texts sizes and deltas
		if texts is not None and obj_text["texts"] != texts:
			obj_text["texts_sizes"] = []
			obj_text["texts_d"] = []
			for i in range(len(texts)):
				obj_text["texts_d"].append(hg.Vec2(0, 0))
			mx = 0
			for text in texts:
				ts = HarfangGUIRenderer.compute_text_size(cls.current_font_id, text)
				obj_text["texts_sizes"].append(ts)
				mx = max(mx, ts.x)
			obj_text["forced_text_width"] = mx
		
		#Forced width
		if "forced_text_width" in args:
			obj_text["forced_text_width"] = args["forced_text_width"]
		
		obj_text["texts"] = texts
		mouse_click = False
		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			mouse_click = True
			current_idx = (current_idx + 1) % len(texts)
		widget["position"] = cls.get_cursor_position()
		cls.update_widget(widget)
		cls.update_cursor(widget)
		return mouse_click, current_idx
	
	@classmethod
	def text_select(cls, widget_id, text:str, selected: bool, **args):
		widget = cls.get_widget("text_select", widget_id, args)
		obj_text = widget["objects_dict"]["text_select.text"]
		mouse_click = False
		
		if "forced_text_width" in args:
			obj_text["forced_text_width"] = args["forced_text_width"]
		else:
			obj_text["forced_text_width"] = 150

		if "mouse_click" in cls.current_signals and widget_id in cls.current_signals["mouse_click"]:
			selected = True
			mouse_click = True
		
		if selected:
			cls.set_widget_state(widget, "selected")
		else:
			cls.set_widget_state(widget,"unselected")

		obj_text["text"] = cls.clip_text(text, 0, obj_text["forced_text_width"])
		if widget["cursor_auto"]:
			widget["position"] = cls.get_cursor_position()
		
		cls.update_widget(widget)

		if widget["cursor_auto"]:
			cls.update_cursor(widget)

		return mouse_click, selected


	@classmethod
	def list_box(cls, widget_id, current_idx: int, items_list: list, **args):
		widget = cls.get_widget("list_box", widget_id, args)
		widget["position"] = cls.get_cursor_position()
		lb_component = widget["components"]["list_box"]
		obj_label = widget["objects_dict"]["basic_label.1"]
		obj_label["text"] = cls.get_label_from_id(widget_id)
		if "show_label" in args:
			widget["components"]["basic_label"]["hidden"] = not args["show_label"]
		else:
			widget["components"]["basic_label"]["hidden"] = False

		mouse_click = False
		
		if "forced_text_width" in args:
			forced_ts_width = args["forced_text_width"]
		else:
			forced_ts_width = 150
		#Update text_select widgets:
		lb_component["text_select_list"] = []
		n = 0
		y_pos = 0
		widget["sub_widgets"] = []
		for item_name in items_list:
			ts_id = widget_id + ".ts##" + str(n)
			mc, _ = cls.text_select(ts_id, item_name, n == current_idx, cursor_auto = False, forced_text_width = forced_ts_width)
			if mc:
				mouse_click = True
				current_idx = n
			ts = cls.widgets[ts_id]
			widget["sub_widgets"].append(ts)
			ts["opacity"] = widget["opacity"]
			ts["position"].x = widget["position"].x + lb_component["position"].x + lb_component["margins"].x
			ts["position"].y = widget["position"].y + lb_component["position"].y + lb_component["margins"].y + y_pos
			ts["position"].z = widget["position"].z
			y_pos += ts["size"].y * lb_component["line_space_factor"]
			n += 1
		lb_component["items_list"] = items_list
		lb_component["size"].x = ts["size"].x
		lb_component["size"].y = y_pos
		lb_component["selected_idx"] = current_idx
		cls.update_widget(widget)
		cls.update_cursor(widget)

		return mouse_click, current_idx

	@staticmethod
	def compute_primitive_matrix_relative_to_widget(primitive):
		if primitive["classe"] == "primitive":
			mat_primitive = hg.TransformationMat4(primitive["position"] + primitive["offset"], primitive["rotation"], primitive["scale"])
			component = primitive["parent"]
			mat_component = hg.TransformationMat4(component["position"] + component["offset"], component["rotation"], component["scale"])
			return mat_component * mat_primitive
		return None

	@classmethod
	def slider_float(cls, widget_id, value_start, value_end, value, **args):
		widget = cls.get_widget("slider_float", widget_id, args)
		obj_slider = widget["components"]["sliderbar"]
		obj_label = widget["objects_dict"]["basic_label.1"]
		obj_num = widget["objects_dict"]["number_display"]
		obj_num_t = widget["objects_dict"]["number_display.text"]
		
		flag_change = False
		
		if "forced_size" in args:
			slider_size = args["forced_size"]
		else:
			slider_size = 150

		if "show_label" in args:
			widget["components"]["basic_label"]["hidden"] = not args["show_label"]
		else:
			widget["components"]["basic_label"]["hidden"] = False

		obj_label["text"] = cls.get_label_from_id(widget_id)

		if "flag_horizontal" in args:
			flag_horizontal = args["flag_horizontal"]
		else:
			flag_horizontal = True

		obj_slider["flag_horizontal"] = flag_horizontal

		if flag_horizontal:
			obj_slider["size"].x = slider_size
		else:
			obj_slider["size"].y = slider_size
		
		if "forced_label_width" in args:
			obj_label["forced_text_width"] = args["forced_label_width"]
		
		if "num_digits" in args:
			obj_num["num_digits"] = args["num_digits"]

		total_size = value_end - value_start

		if "mouse_move" in widget["states"]:
			if "MLB_down" not in cls.current_signals:
				cls.set_widget_state(widget, "mouse_idle")
				cls.set_ui_state(cls.UI_STATE_MAIN)
			elif cls.ui_state == cls.UI_STATE_WIDGET_MOUSE_FOCUS:
				obj_bar = widget["objects_dict"]["sliderbar.background"]
				mat = cls.compute_primitive_matrix_relative_to_widget(obj_bar)
				bar_pos = hg.GetT(mat)
				pointer_pos = widget["pointers"]["mouse"]["pointer_local_position"]
				s = total_size / slider_size
				if flag_horizontal:
					pointer_v = pointer_pos.x - bar_pos.x
				else:
					pointer_v = slider_size - pointer_pos.y + bar_pos.y

				if 0 < pointer_v < slider_size:
					value =  pointer_v * s + value_start
		else:
			if "MLB_pressed" in cls.current_signals and widget["name"] in cls.current_signals["MLB_pressed"]:
				cls.set_widget_state(widget, "mouse_move")
				cls.set_ui_state(cls.UI_STATE_WIDGET_MOUSE_FOCUS)

		obj_slider["value_start"] = value_start
		obj_slider["value_end"] = value_end
		value_dest = max(min(value_start,value_end), min(max(value_start,value_end), value))
		if value_dest != obj_slider["value_dest"]:
			obj_slider["value_dest"] = value_dest
			flag_change = True
		
		widget["position"] = cls.get_cursor_position()

		if widget["flag_new"]:
			obj_slider["inertial_value"] = obj_slider["value_dest"]
		else:
			obj_slider["inertial_value"] += (obj_slider["value_dest"] - obj_slider["inertial_value"]) * obj_slider["bar_inertia"]
		
		
		obj_num_t["forced_text_width"] = widget["forced_number_width"]
		obj_num_t["text_size"] = widget["number_size"]
		fmt = "%."+str(obj_num["num_digits"])+"f"
		n =  fmt % obj_slider["inertial_value"]
		obj_num_t["text"] = n

		cls.update_widget(widget)
		cls.update_cursor(widget)
		
		return flag_change, obj_slider["value_dest"], obj_slider["inertial_value"]


	@classmethod
	def dropdown(cls, widget_id, current_idx:int, items_list:list, **args):
		return False, current_idx

