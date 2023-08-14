// spiral sampling from https://blog.voxagon.se/2018/05/04/bokeh-depth-of-field-in-single-pass.html

#include <forward_pipeline.sh>

SAMPLER2D(u_color, 0);
SAMPLER2D(u_attr0, 1);

uniform vec4 u_params; // x: focus point, y: focus_length

#define GOLDEN_ANGLE 2.39996323
#define MAX_BLUR_SIZE 20.0
#define RAD_SCALE 0.75 // Smaller = nicer blur, larger = faster

float ComputeCoC(float depth) {
	return clamp(abs(depth - u_params.x) / u_params.y, 0.0, 1.0) * MAX_BLUR_SIZE;
}

void main() {
	// reference pixel
	vec2 uv = gl_FragCoord.xy / uResolution.xy;
	vec4 ref_color = texture2D(u_color, uv);
	float ref_depth = texture2D(u_attr0, uv).w;

	float ref_coc = ComputeCoC(ref_depth);

	// sample CoC
	float smp_count = 1.0;
	vec4 dof_out = ref_color;

	float radius = RAD_SCALE;

	for (float a = 0.0; radius < MAX_BLUR_SIZE; a += GOLDEN_ANGLE) {
		vec2 smp_uv = (gl_FragCoord.xy + vec2(cos(a) * radius, sin(a) * radius)) / uResolution.xy;

		float smp_depth = texture2D(u_attr0, smp_uv).w;
		vec4 smp_color = texture2D(u_color, smp_uv);

		float coc = ref_coc;

		if (smp_depth <= ref_depth) {
			float smp_coc = ComputeCoC(smp_depth);
			coc = min(ref_coc, smp_coc);
		}

		float k = smoothstep(radius - 0.5, radius + 0.5, coc);
		dof_out += mix(dof_out / smp_count, smp_color, k);

		smp_count += 1.0;
		radius += RAD_SCALE / radius;
	}

	gl_FragColor = dof_out / smp_count;
}
