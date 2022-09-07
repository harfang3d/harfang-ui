$input v_texcoord0,v_color0

#include<bgfx_shader.sh>

SAMPLER2D(u_tex,0);

void main(){
	vec4 c = texture2D(u_tex,v_texcoord0);
	c.a = (1.0 - c.a) * 1.0 - pow(c.a - 1.0, 4.0) + c.a * (1.0 - pow(c.a - 1.0, 2.0));
	gl_FragColor =  c * v_color0;
}
