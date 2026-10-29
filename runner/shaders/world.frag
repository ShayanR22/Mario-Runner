#version 330
uniform sampler2D world_tex;
uniform sampler2D interface_tex;
uniform sampler2D protection_tex;
uniform sampler2D bloom_tex;
uniform int biome;
uniform float effect_amount;
uniform float time;
uniform bool reduced_motion;
uniform float bloom_amount;
uniform bool heat_enabled;
uniform vec4 lights[8];
uniform vec3 light_colors[8];
in vec2 uv;
out vec4 frag;
void main(){
 vec2 sample_uv=uv;
 float protected_pixel=texture(protection_tex,uv).r;
 vec3 original=texture(world_tex,uv).rgb;
 // Only background above the runway may move. Actors and pickups are protected.
 if(biome==3&&heat_enabled&&!reduced_motion&&uv.y>.22){
  float shimmer=sin(uv.y*60.0+time*2.4)+.25*sin(uv.y*125.0-time*3.0);
  float heat=smoothstep(.45,.85,original.r)*smoothstep(.15,.50,original.r-original.b);
  heat*=smoothstep(.25,.60,1.0-uv.y);
  sample_uv.x=clamp(uv.x+shimmer*.0007*heat*(1.0-protected_pixel)*effect_amount,.001,.999);
 }
 vec3 c=texture(world_tex,sample_uv).rgb;
 vec3 ambient=vec3(1.0);
 if(biome==1)ambient=vec3(.76,.84,.98);
 if(biome==3)ambient=vec3(.89,.78,.82);
 c*=mix(ambient,vec3(1.0),protected_pixel*.85);
 vec2 p=vec2(uv.x,1.0-uv.y);
 for(int i=0;i<8;i++){
  vec2 delta=(p-lights[i].xy)*vec2(1.777778,1.0);
  float attenuation=pow(max(0.0,1.0-length(delta)/max(lights[i].z,.001)),2.0);
  c+=light_colors[i]*attenuation*lights[i].w*.20;
 }
 float bloom_strength=biome==1?.40:biome==3?.30:.12;
 c+=texture(bloom_tex,uv).rgb*bloom_strength*bloom_amount;
 float vignette=smoothstep(.25,.85,length((uv-.5)*vec2(1.2,1.0)));
 c*=1.0-vignette*.10*(1.0-protected_pixel);
 c=mix(original,c,effect_amount);
 vec4 ui=texture(interface_tex,uv);
 frag=vec4(mix(c,ui.rgb,ui.a),1.0);
}
