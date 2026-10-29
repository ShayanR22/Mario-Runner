#version 330
uniform sampler2D world_tex;
uniform int biome;
in vec2 uv;
out vec4 frag;
void main(){
 vec3 c=texture(world_tex,uv).rgb;
 float light=0.0;
 if(biome==1) light=smoothstep(.45,.85,c.g)*smoothstep(.10,.28,c.b-c.r);
 else if(biome==3) light=smoothstep(.68,.95,c.r)*smoothstep(.22,.55,c.g)*(1.0-smoothstep(.32,.6,c.b));
 else light=smoothstep(.82,1.0,c.r)*smoothstep(.65,.9,c.g)*(1.0-smoothstep(.35,.7,c.b))*.25;
 frag=vec4(c*light,1.0);
}
