"""Optional GPU atmosphere, protected actors, untouched UI, and software fallback."""
from array import array
import logging
import pygame as pg
from .config import WIDTH,HEIGHT,INK,ROOT
SHADERS=ROOT/"runner"/"shaders"
BIOMES={"grass":0,"cave":1,"sky":2,"castle":3}

def viewport(size):
    width,height=size
    scale=min(width/WIDTH,height/HEIGHT)
    w,h=max(1,int(WIDTH*scale)),max(1,int(HEIGHT*scale))
    return ((width-w)//2,(height-h)//2,w,h)

class GLPipeline:
    def __init__(self,context):
        import moderngl as gl
        self.gl,self.ctx=gl,context
        self.resources=[]
        self.has_frame=False
        self.fade=1.
        self.vaos={}
        try:
            vertex=(SHADERS/"quad.vert").read_text()
            vertices=array("f",(-1,-1,0,0, 1,-1,1,0, -1,1,0,1, 1,1,1,1))
            self.vbo=self.own(context.buffer(vertices.tobytes()))
            self.programs={}
            for name in ("bright","blur","world","present","copy"):
                program=self.own(context.program(vertex_shader=vertex,fragment_shader=(SHADERS/f"{name}.frag").read_text()))
                self.programs[name]=program
                self.vaos[name]=self.own(context.vertex_array(program,[(self.vbo,"2f 2f","in_position","in_uv")]))
            self.world=self.texture((WIDTH,HEIGHT))
            self.interface=self.texture((WIDTH,HEIGHT))
            self.protection=self.texture((WIDTH,HEIGHT))
            self.small=[self.target((240,135)) for _ in range(2)]
            self.frame=self.target((WIDTH,HEIGHT))
            self.previous=self.target((WIDTH,HEIGHT))
            self.previous[1].clear(0,0,0,1)
            self.programs["bright"]["world_tex"]=0
            self.programs["blur"]["image"]=0
            self.programs["copy"]["image"]=0
            for name,unit in (("world_tex",0),("interface_tex",1),("protection_tex",2),("bloom_tex",3)):
                self.programs["world"][name]=unit
            self.programs["present"]["current_tex"]=0
            self.programs["present"]["previous_tex"]=1
            context.disable(gl.BLEND)
        except Exception:
            self.close()
            raise

    def own(self,obj):
        self.resources.append(obj)
        return obj

    def texture(self,size):
        texture=self.own(self.ctx.texture(size,4))
        mode=self.gl.LINEAR if size!=(WIDTH,HEIGHT) else self.gl.NEAREST
        texture.filter=(mode,mode)
        texture.repeat_x=texture.repeat_y=False
        return texture

    def target(self,size):
        texture=self.texture(size)
        return texture,self.own(self.ctx.framebuffer(color_attachments=[texture]))

    def begin_transition(self):
        if self.has_frame:
            # A textured copy avoids driver-specific framebuffer blit enums on macOS.
            self.previous[1].use()
            self.ctx.viewport=(0,0,WIDTH,HEIGHT)
            self.frame[0].use(0)
            self.vaos["copy"].render(self.gl.TRIANGLE_STRIP)
            self.fade=0.

    def tick(self,dt,reduced):
        self.fade=1. if reduced else min(1.,self.fade+dt/.24)

    def render(self,world,interface,protection,biome,time,lights,enhanced=True,reduced=False,bloom=.6,heat=True):
        for texture,surface in ((self.world,world),(self.interface,interface),(self.protection,protection)):
            texture.write(pg.image.tobytes(surface,"RGBA",True))
        self.small[0][1].use()
        self.ctx.viewport=(0,0,240,135)
        self.world.use(0)
        self.programs["bright"]["biome"]=BIOMES[biome]
        self.vaos["bright"].render(self.gl.TRIANGLE_STRIP)
        self.small[1][1].use()
        self.small[0][0].use(0)
        self.programs["blur"]["direction"]=(1/240,0)
        self.vaos["blur"].render(self.gl.TRIANGLE_STRIP)
        self.small[0][1].use()
        self.small[1][0].use(0)
        self.programs["blur"]["direction"]=(0,1/135)
        self.vaos["blur"].render(self.gl.TRIANGLE_STRIP)
        self.frame[1].use()
        self.ctx.viewport=(0,0,WIDTH,HEIGHT)
        self.world.use(0);self.interface.use(1);self.protection.use(2);self.small[0][0].use(3)
        program=self.programs["world"]
        program["biome"]=BIOMES[biome]
        program["effect_amount"]=float(enhanced)
        program["time"]=0. if reduced else time
        program["reduced_motion"]=reduced
        program["bloom_amount"]=bloom
        program["heat_enabled"]=heat
        positions=[];colors=[]
        for x,y,radius,strength,color in (lights+[(0,0,.001,0,(0,0,0))]*8)[:8]:
            positions.extend((x/WIDTH,y/HEIGHT,radius,strength))
            colors.extend(color)
        program["lights"].write(array("f",positions).tobytes())
        program["light_colors"].write(array("f",colors).tobytes())
        self.vaos["world"].render(self.gl.TRIANGLE_STRIP)
        self.has_frame=True

    def show(self,size):
        self.ctx.screen.use()
        self.ctx.viewport=(0,0,*size)
        self.ctx.clear(*(v/255 for v in INK),1)
        self.ctx.viewport=viewport(size)
        self.frame[0].use(0);self.previous[0].use(1)
        self.programs["present"]["reveal"]=self.fade
        self.vaos["present"].render(self.gl.TRIANGLE_STRIP)

    def capture(self):
        return pg.image.frombytes(self.frame[1].read(components=4,alignment=1),(WIDTH,HEIGHT),"RGBA",True)

    def close(self):
        for resource in reversed(self.resources):
            try:resource.release()
            except Exception:pass
        self.resources.clear()

class Presenter:
    def __init__(self,mode="auto"):
        self.mode=mode
        self.pipeline=None
        self.reason=""
        self.fade=1.
        self.last_frame=None
        self.previous_frame=None
        self.bloom=.6;self.heat=True
        self.window=self.open()

    @property
    def accelerated(self):
        return self.pipeline is not None

    def open(self):
        if self.mode!="software" and pg.display.get_driver()!="dummy":
            try:
                import moderngl
                pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION,3)
                pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION,3)
                pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,pg.GL_CONTEXT_PROFILE_CORE)
                pg.display.gl_set_attribute(pg.GL_CONTEXT_FLAGS,pg.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG)
                window=pg.display.set_mode((WIDTH,HEIGHT),pg.OPENGL|pg.DOUBLEBUF|pg.RESIZABLE)
                self.pipeline=GLPipeline(moderngl.create_context(require=330))
                return window
            except Exception as exc:
                self.reason=f"{type(exc).__name__}: {exc}"
                if self.pipeline:self.pipeline.close()
                self.pipeline=None
                if self.mode=="opengl":
                    raise RuntimeError(f"OpenGL renderer unavailable: {self.reason}") from exc
                logging.warning("OpenGL unavailable; using standard renderer (%s)",self.reason)
        elif self.mode=="opengl":
            raise RuntimeError("OpenGL is unavailable with SDL's dummy display driver")
        return pg.display.set_mode((WIDTH,HEIGHT),pg.RESIZABLE)

    def begin_transition(self,reduced=False):
        if reduced:return
        if self.pipeline:self.pipeline.begin_transition()
        elif self.last_frame is not None:
            self.previous_frame=self.last_frame.copy()
            self.fade=0.

    def tick(self,dt,reduced=False):
        if self.pipeline:self.pipeline.tick(dt,reduced)
        self.fade=1. if reduced else min(1.,self.fade+dt/.24)

    def present(self,canvas,world,interface,protection,biome,time,lights,enhanced,reduced):
        window=pg.display.get_surface()
        if self.pipeline:
            try:
                self.pipeline.render(world,interface,protection,biome,time,lights,enhanced,reduced,self.bloom,self.heat)
                self.pipeline.show(pg.display.get_window_size())
            except Exception as exc:
                if self.mode=="opengl":raise
                self.reason=str(exc)
                self.pipeline.close()
                self.pipeline=None
                self.window=pg.display.set_mode(window.get_size(),pg.RESIZABLE)
                logging.warning("GPU rendering failed; using standard renderer (%s)",exc)
                return self.present(canvas,world,interface,protection,biome,time,lights,False,reduced)
        else:
            frame=canvas
            if self.previous_frame is not None and self.fade<1:
                frame=self.previous_frame.copy()
                incoming=canvas.copy()
                incoming.set_alpha(int(self.fade*self.fade*(3-2*self.fade)*255))
                frame.blit(incoming,(0,0))
            self.last_frame=frame.copy()
            x,y,w,h=viewport(window.get_size())
            window.fill(INK)
            window.blit(pg.transform.scale(frame,(w,h)),(x,y))
        pg.display.flip()

    def toggle_fullscreen(self):
        if self.pipeline:
            self.pipeline.close()
            self.pipeline=None
        try:
            pg.display.toggle_fullscreen()
            if self.mode!="software" and pg.display.get_surface().get_flags()&pg.OPENGL:
                import moderngl
                self.pipeline=GLPipeline(moderngl.create_context(require=330))
        except Exception as exc:
            self.reason=str(exc)
            self.pipeline=None
            pg.display.set_mode((WIDTH,HEIGHT),pg.RESIZABLE)
        self.window=pg.display.get_surface()

    def capture(self,canvas):
        return self.pipeline.capture() if self.pipeline and self.pipeline.has_frame else canvas.copy()

    def close(self):
        if self.pipeline:
            self.pipeline.close()
            self.pipeline=None
