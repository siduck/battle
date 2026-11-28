"""Build and render six standalone vehicle studies in Blender."""
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(os.environ.get('OUT', Path(__file__).resolve().parent))
sys.path.insert(0, str(Path.home() / 'projects/dronefire/tools/blender/vehicles'))
import vkit

def mat(name, rgb, rough=.45, metal=0):
    m = bpy.data.materials.new(name)
    if STYLE in ('pickup','carrier','tractor'):
        rough=max(rough,.76)
        metal=0
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m

def coat(o, m, smooth=False):
    o.data.materials.clear()
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = smooth
    return o

def mesh(name, pts, faces, m):
    data = bpy.data.meshes.new(name)
    data.from_pydata(pts, [], faces)
    data.update()
    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    return coat(o, m)

def bevel(o, amount, segments=1):
    bpy.context.view_layer.objects.active = o
    mod = o.modifiers.new('Edge radii', 'BEVEL')
    mod.width, mod.segments = amount, segments
    mod.harden_normals = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mod = o.modifiers.new('Face normals', 'WEIGHTED_NORMAL')
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

def box(name, center, size, m, radius=.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    coat(o, m)
    return bevel(o, radius) if radius else o

def rod(name, a, b, r, m, sides=12):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=r, depth=(b-a).length, location=(a+b)/2)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    coat(o, m)
    for p in o.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    return o

def outline(name, points, radius, m):
    for a, b in zip(points, points[1:]):
        rod(name, a, b, radius, m, 5)

def panel(name, points, m):
    return mesh(name, points, [tuple(range(len(points)))], m)

def hull(name, sections, m, mode='car'):
    rings = []
    for y,w,lo,shoulder,top in sections:
        if mode == 'car':
            p = [(0,lo),(.71*w,lo),(.94*w,lo+.045),(w,shoulder-.09),(.98*w,shoulder),
                 (.89*w,top-.015),(.69*w,top-.025),(.43*w,top-.048),(0,top-.055)]
        else:
            p = [(0,lo),(.82*w,lo),(.98*w,lo+.09),(w,shoulder-.08),(.97*w,shoulder),
                 (.85*w,top),(.48*w,top),(0,top)]
        rings.append((y,p))
    return coat(vkit.loft(name,rings, vkit.c('steel_dark')),m, mode=='car')

def wheel(x,y,z,r,width,mud=False,spare=False):
    s=1 if x>0 else -1
    if spare:
        s=1
    axis=Vector((0,1,0) if spare else (s,0,0))
    center=Vector((x,y,z))
    forward=Vector((1,0,0) if spare else (0,1,0))
    up=Vector((0,0,1))
    seg=({'tractor': 38, 'carrier': 32, 'pickup': 22}[STYLE] if mud else 124 if STYLE=='hatchback' else 94 if STYLE=='f1-reference' else 100)
    rim=r*(.54 if mud else .73)
    profile=[(rim,-.49),(r*.87,-.52),(r*.96,-.45),(r,-.32),(r,.32),(r*.96,.45),(r*.87,.52),(rim,.49)]
    def ring(name, rows, material):
        pts=[center+axis*(offset*width)+rr*(forward*math.cos(t*math.tau/seg)+up*math.sin(t*math.tau/seg))
             for rr,offset in rows for t in range(seg)]
        faces=[(j*seg+t,j*seg+(t+1)%seg,(j+1)*seg+(t+1)%seg,(j+1)*seg+t)
               for j in range(len(rows)-1) for t in range(seg)]
        o=mesh(name,pts,faces,material)
        import bmesh
        bm=bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
        for p in o.data.polygons:
            p.use_smooth=True
    ring('Tire',profile,RUBBER)
    ring('Rim lip',[(rim,.48),(rim*.91,.52),(rim*.86,.47),(rim*.86,.27)],METAL)
    hub=center+axis*width*.38
    rod('Brake rotor',center-axis*width*.43,hub-axis*.022,rim*.87,DARK,24)
    if not mud:
        rod('Brake caliper',hub+up*rim*.67,hub+up*rim*.67+axis*.025,rim*.18,RED,10)
    rod('Wheel hub',hub-axis*.02,hub+axis*.035,rim*.26,METAL)
    for i in range(6 if mud else 5):
        a=i*math.tau/(6 if mud else 5)
        lug=hub+rim*.37*(forward*math.cos(a)+up*math.sin(a))
        rod('Wheel lug',lug+axis*.016,lug+axis*.047,rim*.056,METAL,6)
    spokes=6 if mud else 10
    for i in range(spokes):
        a=i*math.tau/spokes
        radial=forward*math.cos(a)+up*math.sin(a)
        tangent=forward*-math.sin(a)+up*math.cos(a)
        pts=[hub+radial*rad+tangent*off+axis*ax for rad,off,ax in
             [(rim*.19,-rim*.08,.024),(rim*.21,rim*.09,.024),(rim*.9,rim*.085,.044),(rim*.91,-rim*.04,.044)]]
        panel('Alloy spoke',pts,METAL)
    if mud:
        blocks=12 if STYLE=='pickup' else 16
        for i in range(blocks):
            a=i*math.tau/blocks
            radial=forward*math.cos(a)+up*math.sin(a)
            for j in (-1,1):
                tread=box('Shoulder tread',center+radial*(r*.987)+axis*(j*width*.32),
                          (width*.30,r*.19,r*.045), RUBBER,0)
                if spare:
                    tread.rotation_euler=(0,math.pi/2-a,math.pi/2)
                    tread.dimensions=(width*.3,r*.19,r*.045)
                else:
                    tread.rotation_euler.x=a-math.pi/2

def project(obj,name,poly,m,axis='z',side=1,lift=.003):
    """Clip graphics to visible mesh triangles so they follow creases cleanly."""
    from mathutils.geometry import tessellate_polygon
    direction=Vector((0,0,-1) if axis=='z' else (-side,0,0) if axis=='x' else (0,1,0))
    axes={'z':(0,1),'x':(1,2),'y':(0,2)}[axis]

    def cast(p):
        a,b=p
        origin=Vector((a,b,4) if axis=='z' else (4*side,a,b) if axis=='x' else (a,-8,b))
        hit,co,_,_=obj.ray_cast(origin,direction)
        return co-direction*lift if hit else None

    def cross(a,b):
        return a.x*b.y-a.y*b.x

    def flatten(p):
        return Vector((p[axes[0]],p[axes[1]]))

    def clip(points,a,b):
        result=[]
        last=points[-1]
        dl=cross(b-a,last-a)
        for pt in points:
            d=cross(b-a,pt-a)
            if (d>=0)!=(dl>=0):
                result.append(last.lerp(pt,dl/(dl-d)))
            if d>=0:
                result.append(pt)
            last,dl=pt,d
        return result

    poly=[Vector(q) for q in poly]
    pieces=tessellate_polygon([poly])
    obj.data.calc_loop_triangles()
    vertices=[]
    faces=[]
    for tri in obj.data.loop_triangles:
        if tri.normal.dot(direction)>-.035:
            continue
        a,b,c=[obj.data.vertices[i].co.copy() for i in tri.vertices]
        aa,bb,cc=map(flatten,(a,b,c))
        area=cross(bb-aa,cc-aa)
        if abs(area)<1e-8:
            continue
        boundary=(aa,bb,cc) if area>0 else (aa,cc,bb)
        for piece in pieces:
            points=[poly[i] for i in piece] if isinstance(piece[0],int) else list(piece)
            for start,end in zip(boundary,boundary[1:]+boundary[:1]):
                points=clip(points,start,end) if points else []
            if len(points)<3:
                continue
            def unproject(q):
                return a+(b-a)*cross(q-aa,cc-aa)/area+(c-a)*cross(bb-aa,q-aa)/area
            middle=sum(points,Vector((0,0)))/len(points)
            visible=cast(middle)
            if visible is None or (unproject(middle)-direction*lift-visible).length>.012:
                continue
            start=len(vertices)
            vertices.extend(unproject(q)-direction*lift for q in points)
            face=tuple(range(start,len(vertices)))
            if cross(points[1]-points[0],points[2]-points[0])*area<0:
                face=face[::-1]
            faces.append(face)
    if faces:
        mesh(name,vertices,faces,m)
    return cast

def canopy(sections, paint, angular=False):
    rings=[]
    for y,w,base,top in sections:
        rings.append((y,[(0,base),(w,base),(.97*w,base+(top-base)*.32),
                         (.85*w,top-.013),(.72*w,top),(.39*w,top+.016),(0,top+.02)]))
    o=coat(vkit.loft('Canopy and pillars',rings,vkit.c('steel_dark'),cap=False),paint,not angular)
    o.data.materials.append(GLASS)
    n=12
    for p in o.data.polygons:
        r,i=divmod(p.index,n)
        if (r in (1,2,3,len(sections)-3) or (4<r<len(sections)-3 and i in (1,2,3,8,9,10))) and i not in (0,11):
            p.material_index=1
    return o

def sport(style):
    classic=style=='f1'
    green=style=='wedge'
    paint=mat('Body paint',(.50,.485,.445) if classic else (.062,.30,.009) if green else (.49,.073,.013),.27,.27)
    sections=[
        (-2.27,.62,.22,.31,.35),(-2.23,.79,.17,.35,.42),(-2.12,.89,.155,.42,.47),
        (-1.92,.965,.15,.49,.555),(-1.68,1.005,.144,.58,.64),(-1.41,1.022,.14,.65,.71),
        (-1.15,1.021,.14,.683,.745),(-.89,1.00,.14,.66,.738),(-.58,.96,.14,.62,.717),
        (-.24,.945,.14,.58,.70),(.14,.95,.14,.59,.71),(.50,.98,.14,.64,.758),
        (.81,1.02,.145,.71,.801),(1.13,1.055,.15,.76,.827),(1.40,1.064,.15,.75,.825),
        (1.68,1.044,.155,.70,.80),(1.92,.997,.16,.65,.765),(2.11,.95,.17,.61,.726),
        (2.21,.87,.20,.55,.665),(2.24,.77,.23,.49,.63)]
    if green:
        sections=[
            (y, w * (1.035 + .055 * max(0, y) / 2.24), lo,
             shoulder - .045 * max(0, -y) / 2.27 + .07 * math.exp(-((y + 1.37) / .36)**2),
             top - .065 * max(0, -y) / 2.27 + .09 * math.exp(-((y + 1.37) / .36)**2) + .035 * max(0, y))
            for y,w,lo,shoulder,top in sections]
    elif not classic:
        sections=[
            (y, w + .07 * math.exp(-((abs(y) - 1.4) / .45)**2),
             lo - .017, shoulder + .055 * abs(y) / 2.27,
             top + .085 * math.exp(-((abs(y) - 1.4) / .55)**2) - .055 * (y > 1.8))
            for y,w,lo,shoulder,top in sections]
    else:
        sections=[
            (y + .33 * max(0, y - 1.45), w - .065 * math.exp(-((y + .18) / .67)**2),
             lo, shoulder + .025 * (y > 1), top)
            for y,w,lo,shoulder,top in sections]
    body=hull('Coachwork',sections,paint)
    radius=.328 if classic else .35
    axles=(-1.37,1.39)
    vkit.arches(body,[(y,radius) for y in axles],radius+.027,1.10,.41)
    coat(body,paint,True)
    body.data.set_sharp_from_angle(angle=math.radians(41))
    roof=1.18 if classic else 1.055 if green else 1.24
    greenhouse=[(-.88,.64,.678,.692),(-.82,.68,.688,.728),(-.65,.699,.693,.836),
            (-.40,.697,.695,.969),(-.15,.677,.7,roof-.065),(.01,.663,.703,roof-.013),
            (.105,.666,.707,roof),(.31,.675,.713,roof-.007),(.54,.702,.743,roof-.044),
            (.76,.718,.773,roof-.119),(.99,.717,.78,roof-.223),
            (1.24,.68,.79,.817),(1.34,.58,.789,.794)]
    if green:
        greenhouse=[(y+.07,w*1.04,base-.045,top) for y,w,base,top in greenhouse]
    elif not classic:
        greenhouse=[(y-.13,w*.88,base,top) for y,w,base,top in greenhouse]
    else:
        greenhouse=[(y,w*.93,base,top) for y,w,base,top in greenhouse]
    canopy(greenhouse,paint,green)
    if classic:
        project(body,'Graphite bonnet insert',[(-.39,-1.98),(.39,-1.98),(.49,-.91),(-.49,-.91)],DARK)
        box('Roof intake',(0,.22,roof+.035),(.41,.42,.08),DARK,.038)
    if style=='senna':
        for s in (-1,1):
            project(body,'Bonnet relief',[(s*x,y) for x,y in
                    ((.22,-1.71),(.47,-1.59),(.54,-1.10),(.31,-1.03))],DARK)
            project(body,'Lower door glazing',[(.11,.49),(.51,.54),(.43,.38),(.20,.34)],GLASS,'x',s,.013)
        box('Roof snorkel',(0,.28,roof+.052),(.19,.35,.086),DARK,.036)
        for s in (-1,1):
            box('Wing strut',(s*.55,1.77,.985),(.071,.24,.44),DARK,.022).rotation_euler.x=-.24
            box('Wing endplate',(s*.96,1.81,1.26),(.05,.46,.18),DARK,.021)
        box('Rear wing',(0,1.81,1.27),(1.96,.39,.076),DARK,.035)
    for s in (-1,1):
        for y in axles:
            wheel(s*.85,y,radius,radius,.285 if y<0 else .34)
        if classic:
            pod=[(.49,-1.93),(.83,-1.88),(.938,-1.60),(.62,-1.51)]
        else:
            pod=[(.46,-2.04),(.89,-1.92),(.956,-1.52),(.66,-1.73)] if green else [(.58,-2.05),(.88,-1.91),(.93,-1.56),(.73,-1.69)]
        cast=project(body,'Headlamp housing',[(s*x,y) for x,y in pod],DARK,lift=.014)
        if classic:
            for x,y,r in [(.66,-1.76,.067),(.795,-1.71,.077)]:
                p=cast((s*x,y))
                if p:
                    rod('Lamp bezel',p,p+Vector((0,-.012,.021)),r,METAL,16)
                    a=p+Vector((0,-.012,.021))
                    rod('Round projector',a,a+Vector((0,-.008,.016)),r*.71,LIGHT,16)
        else:
            points=[cast((s*x,y)) for x,y in ((.51 if green else .62,-2.005),(.842,-1.917),(.932,-1.575))]
            outline('LED signature',[p+Vector((0,0,.012)) for p in points if p],.013,LIGHT)
        side=[(-.64,.48),(.73,.64),(.92,.59),(.72,.37),(-.34,.22)] if classic else [(.14,.27),(.62,.65),(.86,.69),(.79,.34),(.49,.25)]
        project(body,'Door graphic' if classic else 'Side intake',side,DARK,'x',s,.012)
        if classic:
            project(body,'Red pinstripe',[(-.48,.34),(.77,.548),(.791,.53),(-.48,.325)],RED,'x',s,.016)
        project(body,'Door shut line',[(-.55,.37),(-.50,.612),(-.49,.612),(-.54,.37)],DARK,'x',s)
        project(body,'Flush door handle',[(.31,.608),(.49,.63),(.47,.606),(.31,.590)],DARK,'x',s)
        y=-.48 if classic else -.56
        rod('Mirror stem',(s*.69,y,.779),(s*.963,y-.045,.83),.027,DARK)
        box('Mirror housing',(s*1.004,y-.05,.848),(.235,.143,.104),DARK if classic else paint,.046)
        box('Mirror glass',(s*1.014,y+.019,.851),(.164,.012,.054),METAL,.005)
        box('Rear lamp',(s*.64,2.158,.595),(.39,.091,.043),RED,.018)
        cast=project(body,'Lower bumper opening',[(s*x,z) for x,z in ((.37,.205),(.86,.215),(.92,.31),(.70,.351),(.38,.317))],DARK,'y',lift=.011)
        for z in (.239,.265,.29):
            pts=[cast((s*x,z)) for x in (.43,.55,.68,.78)]
            outline('Intake fin',[p+Vector((0,-.011,0)) for p in pts if p],.005,METAL)
        if green:
            cast=project(body,'Angular bumper cutout',[(s*x,z) for x,z in
                         ((.28,.20),(.82,.22),(.92,.33),(.90,.416),(.63,.381),(.39,.29))],DARK,'y',lift=.016)
            contour=[cast((s*x,z)) for x,z in ((.40,.286),(.76,.348),(.873,.414))]
            outline('Bumper light blade',[p+Vector((0,-.005,0)) for p in contour if p],.009,LIGHT)
        if classic:
            project(body,'Amber marker',[(s*x,z) for x,z in ((.45,.375),(.65,.382),(.67,.404),(.46,.406))],AMBER,'y',lift=.016)
    box('Front splitter',(0,-2.03,.177),(1.77,.38,.074),DARK,.034)
    box('Sill left',(-.907,.05,.159),(.16,1.77,.08),DARK,.024)
    box('Sill right',(.907,.05,.159),(.16,1.77,.08),DARK,.024)
    box('Rear diffuser',(0,2.04,.214),(1.63,.4,.13),DARK,.035)
    for x in (-.61,-.31,0,.31,.61):
        box('Diffuser strake',(x,2.09,.17),(.029,.36,.081),DARK,.008)
    return 1.12

def chamfered(y0,y1,z0,z1,cut):
    return [(y0+cut,z0),(y1-cut,z0),(y1,z0+cut),(y1,z1-cut),
            (y1-cut,z1),(y0+cut,z1),(y0,z1-cut),(y0,z0+cut)]

def side_panel(name,s,x,profile,m):
    return panel(name,[(s*x,y,z) for y,z in profile],m)

def truck(carrier):
    paint=mat('Ceramic body color',(.105,.143,.092) if carrier else (.27,.105,.043),.43,.14)
    trim=mat('Secondary body color',(.052,.071,.047) if carrier else (.14,.044,.020),.49,.16)
    r=.50
    ys=(-1.62,1.63 if not carrier else 1.81)
    end=2.68 if carrier else 2.38
    body=hull('Lower coachwork',[
        (-2.49,.85,.69,1.23,1.29),(-2.38,1.01,.63,1.32,1.42),(-2.13,1.11,.59,1.37,1.49),
        (-1.65,1.13,.58,1.39,1.50),(-1.07,1.105,.59,1.43,1.52),
        (-.71,1.09,.55,1.43,1.51),(.72,1.09,.55,1.40,1.47),
        (1.44,1.13,.59,1.40,1.46),(2.18,1.12,.64,1.40,1.46),
        (end,1.04,.68,1.37,1.42)],paint,'truck')
    vkit.arches(body,[(y,r) for y in ys],.587,1.18,.43)
    coat(body,paint)
    cab_end=2.52 if carrier else .86
    roof_height=2.48 if carrier else 2.30
    cabin=hull('Cab shell',[
        (-.99,.93,1.39,1.48,1.53),(-.84,.964,1.39,1.7,1.77),(-.48,.962,1.4,2.16,2.24),
        (-.35,.97 if carrier else 1.025,1.4,2.22,2.30),(cab_end-.12,1.05 if carrier else .87,1.4,roof_height-.08,roof_height),
        (cab_end,.95 if carrier else .81,1.4,2.10,2.19)],paint,'truck')
    project(cabin,'Wide split windscreen',[(-.79,1.62),(.79,1.62),(.77,2.10),(.66,2.17),(-.66,2.17),(-.77,2.10)],GLASS,'y')
    project(cabin,'Windscreen centre bar',[(-.018,1.61),(.018,1.61),(.018,2.179),(-.018,2.179)],DARK,'y',lift=.009)
    box('Visor lip',(0,-.443,2.223),(1.88,.22,.085),DARK,.026)
    if carrier:
        for x in (-.63,.63):
            rod('Roof rail',(x,-.32,2.35),(x,2.38,roof_height+.038),.036,DARK,10)
        box('Roof pod',(0,-.21,2.38),(.84,.20,.092),DARK,.015)
        for x in (-.29,-.16,.16,.29):
            box('Roof marker',(x,-.314,2.38),(.09,.022,.046),AMBER,.006)
        box('Rear bumper',(0,2.70,.745),(2.08,.26,.21),DARK,.045)
    else:
        for side in (-1,1):
            box('Front bumper wing',(side*.82,-2.48,.79),(.55,.28,.22),DARK,.07)
            box('Side sill step',(side*1.12,-.08,.60),(.27,1.12,.14),DARK,.035)
        box('Flat cargo bed',(0,1.55,1.36),(1.96,1.49,.13),DARK,.026)
        box('Tailgate',(0,2.32,1.52),(1.91,.115,.38),paint,.026)
        for s in (-1,1):
            box('Cargo box rail',(s*.97,1.62,1.57),(.21,1.43,.34),paint,.039)
            rod('Bed reinforcement',(s*.79,.77,2.15),(s*.94,2.12,1.65),.055,DARK,8)
        wheel(0,2.49,1.61,.45,.29,True,True)
    for s in (-1,1):
        for y in ys:
            wheel(s*1.015,y,r,r,.405,True)
            arch=[(y-.68,.89),(y-.49,1.11),(y+.46,1.11),(y+.66,.89),
                  (y+.56,.84),(y+.37,1.015),(y-.40,1.015),(y-.59,.84)]
            side_panel('Armored arch trim',s,1.132,arch,DARK)
            outline('Arch lip',[(s*1.141,yy,zz) for yy,zz in arch[:4]],.025,trim)
        windows=[(-.57,.16,1.60,2.12),(.23,.74,1.63,2.11)] if not carrier else [
                 (-.57,.20,1.61,2.12),(.38,1.15,1.75,2.04),(1.35,2.20,1.75,2.04)]
        for i,(y0,y1,z0,z1) in enumerate(windows):
            project(cabin,'Window gasket',chamfered(y0-.028,y1+.028,z0-.03,z1+.025,.079),DARK,'x',s,.01)
            project(cabin,'Tinted armor glass',chamfered(y0,y1,z0,z1,.069),GLASS,'x',s,.023)
            if i==0 or not carrier:
                side_panel('Door outer stamping',s,1.101,chamfered(y0-.028,y1+.035,.80,1.375,.08),trim)
                side_panel('Door panel',s,1.109,chamfered(y0,y1+.015,.83,1.35,.07),paint)
                box('Black pull handle',(s*1.115,y1-.093,1.302),(.04,.17,.055),DARK,.013)
        if carrier:
            for z in (1.04,1.18):
                box('Equipment compartment rib',(s*1.114,1.19,z),(.036,1.83,.045),trim,.01)
            side_panel('Equipment hatch',s,1.12,chamfered(.96,1.83,1.47,1.64,.035),trim)
        for y in (-.48,.13) if carrier else (-.52,.25):
            for z in (.976,1.264):
                box('Door hinge',(s*1.109,y,z),(.051,.093,.046),trim,.007)
        box('Running board',(s*1.056,.05,.583),(.27,1.59,.091),DARK,.028)
        for y in (-.59,-.19,.21,.61):
            box('Step grip',(s*1.126,y,.636),(.1,.19,.016),METAL,.004)
        rod('Mirror bracket',(s*.96,-.76,1.72),(s*1.21,-.81,1.72),.035,DARK,8)
        box('Mirror',(s*1.244,-.81,1.76),(.135,.124,.221),DARK,.032)
        box('Tail lamp',(s*.88,end+.014,1.16),(.15,.061,.15),RED,.015)
        box('Headlight bucket',(s*.742,-2.487,1.227),(.31,.13,.184),DARK,.024)
        for x in (.666,.744,.822):
            rod('Projector',(s*x,-2.556,1.246),(s*x,-2.572,1.246),.029,LIGHT,12)
        box('Marker strip',(s*.744,-2.565,1.174),(.204,.014,.024),AMBER,.008)
        box('Bumper end',(s*.806,-2.445,.744),(.58,.35,.205),DARK,.045)
        box('Skid shoulder',(s*.70,-2.52,.917),(.45,.128,.123),trim,.02)
    box('Radiator surround',(0,-2.463,1.11),(1.15,.175,.423),trim,.055)
    box('Radiator',(0,-2.55,1.108),(1.01,.063,.318),DARK,.037)
    for z in (.997,1.06,1.12,1.18,1.241):
        box('Radiator crossbar',(0,-2.588,z),(.87,.035,.022),METAL,.005)
    box('Lower skid plate',(0,-2.49,.72),(1.58,.33,.155),DARK,.04)
    box('Hood boss',(0,-1.65,1.508),(1.30,1.12,.084),trim,.037)
    for x in (-.38,-.25,-.12,.12,.25,.38):
        box('Pressed hood vent',(x,-1.49,1.551),(.061,.29,.018),DARK,.006)
    return 2.27

def tractor():
    paint=mat('Industrial ochre',(.41,.24,.043),.45,.16)
    green=mat('Deep enamel',(.044,.113,.078),.46,.17)
    box('Cast chassis',(0,-.01,.65),(1.3,3.28,.45),DARK,.09)
    for s in (-1,1):
        wheel(s*.84,-1.19,.407,.407,.29,True)
        wheel(s*1.03,1.12,.783,.783,.50,True)
        box('Cab entry stair',(s*.741,.21,.53),(.42,.44,.10),DARK,.024)
        box('Cab entry stair',(s*.70,.16,.73),(.36,.36,.098),DARK,.019)
        rod('Door handrail',(s*.748,-.04,1.05),(s*.748,-.11,1.59),.023,METAL,8)
        box('Side engine air grille',(s*.568,-1.0,1.032),(.033,1.02,.23),DARK,.015)
        for y in (-1.44,-1.32,-1.2,-1.08,-.96,-.84,-.72,-.60):
            box('Engine grille bar',(s*.59,y,1.033),(.024,.027,.198),green,.005)
        pts=[(s*.81,.29,1.22),(s*.81,.54,1.48),(s*.81,.94,1.65),(s*.81,1.36,1.63),
             (s*.81,1.76,1.45),(s*.81,1.92,1.18)]
        outer=[(s*1.30,y,z) for _,y,z in pts]
        mesh('Rear rolled mudguard',pts+outer,[(j,j+1,j+7,j+6) for j in range(5)],paint)
        outline('Mudguard edge',outer,.037,paint)
        box('Rear reflector',(s*1.15,1.91,1.367),(.151,.061,.111),RED,.018)
        a=s*.677
        side_panel('Cab side glass',s,.683,[(-.30,1.46),(.78,1.46),(.79,2.40),(-.16,2.42)],GLASS)
        outline('Cab side frame',[(a,-.30,1.38),(a,-.19,2.46),(a,.80,2.46),
                (a,.81,1.40),(a,-.30,1.38)],.042,green)
        rod('Door pillar',(a,.45,1.42),(a,.45,2.46),.035,green,8)
        rod('Mirror arm',(a,-.16,2.2),(s*.991,-.28,2.19),.02,DARK,8)
        box('Cab mirror',(s*1.005,-.29,2.19),(.109,.095,.206),DARK,.022)
    hull('Tapered engine bonnet',[
        (-1.95,.44,.94,1.23,1.32),(-1.78,.51,.94,1.29,1.40),
        (-1.20,.57,.94,1.34,1.47),(-.62,.63,.94,1.42,1.54),
        (-.30,.65,.94,1.43,1.53)],green,'truck')
    box('Radiator front',(0,-1.938,1.177),(.90,.12,.348),DARK,.056)
    for x in (-.33,-.22,-.11,0,.11,.22,.33):
        box('Front radiator slat',(x,-2.01,1.173),(.028,.024,.25),METAL,.005)
    for s in (-1,1):
        box('Work light mount',(s*.40,-1.914,1.379),(.225,.104,.121),DARK,.025)
        box('Work light',(s*.40,-1.976,1.382),(.154,.023,.076),LIGHT,.01)
    box('Front counterweight',(0,-2.01,.55),(.92,.42,.30),DARK,.04)
    box('Cab lower body',(0,.25,1.28),(1.34,1.29,.33),green,.046)
    for y in (-.304,.799):
        top=y+.139 if y<0 else y-.014
        panel('Cab end glass',[(-.65,y,1.43),(.65,y,1.43),(.65,top,2.43),(-.65,top,2.43)],GLASS)
        for x in (-.66,.66):
            rod('Cab corner pillar',(x,y,1.40),(x,top,2.46),.046,green,8)
    hull('Raised cab canopy',[
        (-.46,.66,2.42,2.52,2.57),(-.32,.76,2.42,2.61,2.65),
        (.69,.76,2.42,2.61,2.65),(.98,.63,2.42,2.48,2.53)],paint,'truck')
    rod('Exhaust stack',(.49,-.63,1.44),(.49,-.63,2.19),.039,DARK,12)
    rod('Exhaust heat shield',(.49,-.63,1.49),(.49,-.63,1.91),.06,METAL,12)
    rod('Beacon foot',(0,.58,2.54),(0,.58,2.61),.09,DARK,12)
    rod('Amber beacon',(0,.58,2.61),(0,.58,2.72),.077,AMBER,16)
    for x in (-.40,.40):
        rod('Rear linkage',(x,1.52,.70),(x,1.97,.44),.064,DARK,8)
    return 2.55

def hatchback():
    paint=mat('Slate blue metallic',(.08,.18,.25),.36,.38)
    r=.31
    axles=(-1.28,1.24)
    body=hull('Hatchback body',[
        (-2.06,.67,.27,.59,.70),(-2,.79,.22,.67,.78),(-1.84,.87,.21,.74,.84),
        (-1.3,.90,.20,.77,.86),(-.88,.895,.20,.79,.89),
        (-.5,.88,.20,.81,.91),(.34,.88,.20,.82,.92),
        (1.16,.90,.20,.84,.94),(1.67,.89,.23,.84,.95),
        (1.91,.81,.27,.82,.92),(2,.72,.33,.77,.86)],paint)
    vkit.arches(body,[(y,r) for y in axles],.345,1.04,.37)
    cabin=hull('Five-door greenhouse',[
        (-.92,.73,.79,.84,.87),(-.70,.79,.79,.99,1.04),
        (-.39,.79,.79,1.31,1.39),(-.16,.78,.79,1.44,1.51),
        (.50,.77,.79,1.45,1.52),(1.24,.75,.79,1.40,1.47),
        (1.56,.73,.79,1.35,1.41),(1.85,.69,.79,1.01,1.09),
        (1.89,.67,.79,.87,.94)],paint,'truck')
    project(cabin,'Windscreen',[(-.63,.97),(.63,.97),(.57,1.42),(-.57,1.42)],GLASS,'y',lift=.008)
    for s in (-1,1):
        for y in axles:
            wheel(s*.76,y,r,r,.19)
        project(cabin,'Front door glass',[(-.61,1.02),(.20,1.02),(.20,1.42),(-.21,1.42)],GLASS,'x',s,.011)
        project(cabin,'Rear door glass',[(.25,1.02),(1.25,1.02),(1.14,1.39),(.25,1.42)],GLASS,'x',s,.011)
        for y in (.16,1.1):
            project(body,'Door shut line',[(y,.29),(y+.013,.29),(y+.013,.81),(y,.81)],DARK,'x',s,.003)
            box('Door pull',(s*.879,y-.117,.75),(.034,.143,.032),paint,.009)
        box('Mirror pod',(s*.94,-.53,1.025),(.20,.16,.095),paint,.037)
        project(body,'Headlight housing',[(s*x,z) for x,z in
                ((.43,.66),(.79,.657),(.81,.748),(.53,.755))],DARK,'y',lift=.013)
        project(body,'Headlight lens',[(s*x,z) for x,z in
                ((.47,.689),(.77,.684),(.78,.728),(.54,.734))],LIGHT,'y',lift=.019)
        box('Taillight',(s*.731,1.853,.864),(.23,.16,.09),RED,.02)
        box('Lower fog light',(s*.64,-1.994,.405),(.15,.044,.052),LIGHT,.013)
    box('Upper grille',(0,-2.055,.606),(.81,.055,.10),DARK,.023)
    box('Lower grille',(0,-2.041,.402),(1.10,.069,.129),DARK,.031)
    for z in (.37,.41,.45):
        box('Grille rib',(0,-2.08,z),(.94,.028,.012),METAL,.003)
    box('Rear window',(0,1.708,1.228),(1.13,.036,.39),GLASS,.035).rotation_euler.x=.70
    box('Plate recess',(0,1.986,.605),(.53,.038,.151),DARK,.018)
    return 1.55


def aircraft_shell(name, sections, paint, segments):
    # Elliptical fuselage sections on the longitudinal axis.
    coordinates=[(w*math.cos(a*math.tau/segments),y,z+h*math.sin(a*math.tau/segments))
                 for y,z,w,h in sections for a in range(segments)]
    faces=[(i*segments+a,i*segments+(a+1)%segments,(i+1)*segments+(a+1)%segments,(i+1)*segments+a)
           for i in range(len(sections)-1) for a in range(segments)]
    faces.extend([tuple(reversed(range(segments))),tuple(range(len(coordinates)-segments,len(coordinates)))])
    return coat(mesh(name,coordinates,[face[::-1] for face in faces],paint),paint,True)


def flight_surface(name, root, tip, paint):
    # Five points per section define an airfoil with a thin trailing edge.
    return coat(mesh(name,root+tip,[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
                     +[(4,3,2,1,0),(5,6,7,8,9)],paint),paint,True)


def jetplane():
    paint=mat('Warm white aircraft paint',(.60,.61,.60),.37,.24)
    accent=mat('Navy trim',(.027,.078,.16),.36,.28)
    fuselage=aircraft_shell('Pressurized fuselage',[
        (-3.20,1.25,.018,.022),(-3.07,1.26,.14,.16),(-2.85,1.27,.29,.29),
        (-2.58,1.30,.43,.42),(-2.28,1.33,.54,.51),(-1.94,1.35,.60,.59),
        (-1.61,1.35,.63,.63),(-1.20,1.35,.646,.634),(-.78,1.35,.65,.635),
        (-.34,1.35,.65,.635),(.13,1.35,.65,.635),(.59,1.35,.65,.635),
        (1.04,1.35,.64,.62),(1.46,1.36,.61,.59),(1.80,1.39,.56,.54),
        (2.12,1.42,.48,.49),(2.42,1.45,.38,.41),(2.70,1.49,.26,.32),
        (2.94,1.55,.145,.21),(3.10,1.59,.035,.06)],paint,176)
    for s in (-1,1):
        project(fuselage,'Cockpit glass',[(-2.76,1.54),(-2.15,1.58),(-2.03,1.84),(-2.29,1.82)],GLASS,'x',s,.008)
        for y in (-1.48,-1.10,-.72,-.34,.04,.42,.80,1.18):
            project(fuselage,'Cabin window',[(y-.10,1.42),(y+.10,1.42),(y+.10,1.56),(y+.07,1.60),(y-.07,1.60),(y-.10,1.56)],GLASS,'x',s,.006)
        project(fuselage,'Navy cheatline',[(-2.50,1.33),(2.76,1.34),(2.67,1.42),(-2.39,1.39)],accent,'x',s,.007)
        flight_surface('Swept wing',[(s*.48,y,z) for y,z in [(-.84,1.07),(-.43,1.20),(.36,1.18),(1.05,1.04),(-.28,.99)]],
                       [(s*3.20,y,z) for y,z in [(.56,1.19),(.65,1.22),(.91,1.22),(1.07,1.19),(.75,1.17)]],paint)
        flight_surface('T-tail stabilizer',[(s*.05,y,z) for y,z in [(2.28,2.99),(2.48,3.04),(2.81,3.04),(3.08,2.98),(2.65,2.96)]],
                       [(s*1.15,y,z) for y,z in [(2.75,3.01),(2.86,3.03),(3.02,3.03),(3.15,3.01),(2.93,2.99)]],paint)
        box('Engine pylon',(s*.69,1.63,1.47),(.58,.68,.16),paint,.045)
        engine=aircraft_shell('Turbofan nacelle',[(.92,1.54,.24,.24),(1.01,1.54,.30,.30),
             (1.17,1.54,.323,.323),(1.54,1.54,.324,.324),(1.92,1.54,.30,.30),
             (2.19,1.54,.24,.24),(2.26,1.54,.22,.22)],paint,64)
        engine.location.x=s*.89
        for y,r,m in [(0.912,.218,DARK),(2.261,.175,METAL)]:
            rod('Engine opening',(s*.89,y-.009,1.54),(s*.89,y+.009,1.54),r,m,40)
        rod('Main gear strut',(s*.73,.49,.32),(s*.59,.49,1.08),.052,METAL)
        rod('Main tire',(s*.81,.49,.22),(s*.65,.49,.22),.22,RUBBER,36)
        box('Wingtip navigation light',(s*3.17,.73,1.22),(.08,.18,.046),RED if s<0 else LIGHT,.01)
    flight_surface('Vertical stabilizer',[(x,y,1.72) for x,y in [(0,1.54),(.12,1.90),(.10,2.58),(0,3.06),(-.11,2.23)]],
                   [(x,y,2.99) for x,y in [(0,2.37),(.05,2.50),(.04,2.78),(0,3.04),(-.045,2.70)]],accent)
    rod('Nose strut',(0,-2.12,.22),(0,-2.12,.89),.045,METAL)
    rod('Nose tire',(-.12,-2.12,.16),(.12,-2.12,.16),.16,RUBBER,36)
    return 3.04


def helicopter():
    paint=mat('Utility blue',(.048,.22,.33),.41,.24)
    stripe=mat('Warm white trim',(.62,.60,.53),.39,.23)
    fuselage=aircraft_shell('Cabin fuselage',[
        (-1.94,1.25,.02,.08),(-1.84,1.27,.27,.32),(-1.66,1.29,.48,.54),
        (-1.48,1.32,.64,.67),(-1.20,1.33,.74,.77),(-.89,1.34,.77,.79),
        (-.59,1.34,.79,.81),(-.26,1.34,.80,.82),(.08,1.34,.80,.82),
        (.41,1.34,.79,.81),(.73,1.35,.77,.78),(1.01,1.36,.69,.71),
        (1.29,1.40,.56,.58),(1.52,1.47,.39,.42),(1.70,1.53,.23,.28)],paint,192)
    project(fuselage,'Windscreen',[(-.56,1.42),(.56,1.42),(.51,1.91),(.36,2.04),(-.36,2.04),(-.51,1.91)],GLASS,'y',lift=.012)
    aircraft_shell('Tapered tail boom',[(1.19,1.60,.35,.34),(1.60,1.64,.31,.29),(2.03,1.70,.25,.23),
         (2.58,1.77,.20,.18),(3.12,1.84,.15,.14),(3.61,1.92,.11,.12),(3.88,1.98,.09,.10)],paint,192)
    for s in (-1,1):
        for y0,y1 in [(-1.31,-.64),(-.51,.66)]:
            project(fuselage,'Cabin side glass',[(y0,1.44),(y1,1.44),(y1,1.92),(y0+.15,1.92)],GLASS,'x',s,.012)
        project(fuselage,'Side stripe',[(-1.63,1.09),(1.53,1.10),(1.57,1.21),(-1.68,1.20)],stripe,'x',s,.011)
        for y in (-.98,.77):
            rod('Skid strut',(s*.62,y,.67),(s*.97,y,.12),.051,METAL,24)
        rod('Landing skid',(s*.97,-1.47,.085),(s*.97,1.40,.085),.067,DARK,28)
        rod('Skid upturn',(s*.97,-1.73,.26),(s*.97,-1.47,.085),.067,DARK,28)
        box('Sliding door track',(s*.791,.20,1.27),(.043,1.17,.042),METAL,.012)
        box('Latch',(s*.785,-.31,1.40),(.06,.125,.052),DARK,.013)
    flight_surface('Tail fin',[(x,y,1.95) for x,y in [(0,3.17),(.09,3.36),(.09,3.62),(0,3.90),(-.08,3.54)]],
                   [(x,y,2.86) for x,y in [(0,3.66),(.044,3.75),(.04,3.91),(0,4.02),(-.04,3.83)]],stripe)
    box('Transmission cowling',(0,.16,2.14),(.97,1.47,.41),paint,.12)
    rod('Rotor mast',(0,.08,2.24),(0,.08,2.59),.077,METAL,32)
    rod('Rotor head',(0,.08,2.52),(0,.08,2.63),.15,DARK,32)
    for i in range(4):
        a=math.radians(24+90*i)
        blade=box('Main rotor blade',(1.88*math.cos(a),.08+1.88*math.sin(a),2.60),
                  (3.49,.237,.036),DARK,.012)
        blade.rotation_euler.z=a
    rod('Tail rotor hub',(.06,3.76,2.18),(.24,3.76,2.18),.07,METAL,24)
    for a in (math.radians(29),math.radians(119)):
        blade=box('Tail rotor blade',(.25,3.76,2.18),(.031,.95,.115),DARK,.012)
        blade.rotation_euler.x=a
    return 2.86


def reference_f1():
    paint=mat('Porcelain white',(.66,.65,.63),.39,.18)
    lamp=mat('Projector lens',(.25,.30,.35),.27,.26)
    body_sections=[
        (-2.26,.67,.21,.34,.39),(-2.22,.80,.18,.38,.44),(-2.13,.90,.17,.44,.51),
        (-1.99,.95,.16,.52,.57),(-1.79,.99,.15,.63,.64),(-1.55,1.015,.15,.72,.70),
        (-1.29,1.017,.15,.76,.72),(-1.03,1.002,.15,.735,.73),(-.80,.979,.15,.68,.74),
        (-.52,.952,.15,.64,.737),(-.20,.945,.15,.62,.73),(.14,.954,.15,.63,.74),
        (.47,.985,.15,.68,.76),(.78,1.018,.15,.74,.79),(1.07,1.043,.15,.79,.83),
        (1.39,1.05,.15,.80,.84),(1.68,1.038,.16,.76,.83),(1.96,1.01,.17,.70,.79),
        (2.18,.955,.18,.66,.755),(2.29,.88,.20,.60,.69)]
    body=hull('White coachwork and raised fenders',body_sections,paint)
    vkit.arches(body,[(-1.39,.333),(1.39,.344)],.367,1.1,.41)
    coat(body,paint,False)
    canopy([(-1.02,.64,.68,.702),(-.93,.69,.697,.736),(-.78,.70,.70,.843),
            (-.58,.704,.70,.982),(-.33,.698,.70,1.12),(-.12,.689,.71,1.19),
            (.11,.69,.72,1.222),(.37,.698,.738,1.215),(.61,.713,.752,1.15),
            (.83,.723,.777,1.063),(1.05,.706,.798,.953),(1.23,.64,.806,.848),
            (1.33,.57,.81,.82)],paint)
    GLASS.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.20
    project(body,'Tapered black bonnet',[(0,-2.013),(.265,-1.98),(.34,-1.83),
        (.44,-1.02),(.31,-.87),(-.31,-.87),(-.44,-1.02),(-.34,-1.83),(-.265,-1.98)],DARK)
    project(body,'Bonnet vent',[(-.25,-1.25),(.25,-1.25),(.19,-1.17),(-.19,-1.17)],
            mat('Vent shadow',(.005,.006,.007),.64),lift=.011)
    intake=box('Integrated roof intake',(0,.165,1.226),(.37,.48,.056),DARK,.019)
    intake.rotation_euler.x=-.055
    bumper_profile=[(-2.29,.55,.17,.29,.345),(-2.25,.75,.15,.31,.365),
        (-2.15,.91,.145,.322,.385),(-2.01,.952,.147,.325,.387),
        (-1.86,.967,.154,.29,.34)]
    bumper=hull('Wraparound black bumper',bumper_profile,DARK)
    box('Registration plate',(0,-2.306,.283),(.44,.028,.104),paint,.008)
    for side in (-1,1):
        for y,r in [(-1.39,.333),(1.39,.344)]:
            wheel(side*.869,y,r,r,.259 if y<0 else .313)
        pod=[(.469,-1.955),(.721,-1.974),(.934,-1.719),(.841,-1.563),(.646,-1.608)]
        cast=project(body,'Recessed lamp surround',[(side*x,y) for x,y in pod],DARK,lift=.006)
        lens=[(.504,-1.927),(.706,-1.94),(.896,-1.718),(.824,-1.609),(.659,-1.652)]
        project(body,'Smoked headlamp face',[(side*x,y) for x,y in lens],GLASS,lift=.009)
        for x,y,r in [(.638,-1.821,.061),(.768,-1.734,.077)]:
            point=cast((side*x,y))
            if point:
                rod('Projector bowl',point,point+Vector((0,-.008,.016)),r,METAL,18)
                rod('Projector lens',point+Vector((0,-.008,.013)),point+Vector((0,-.014,.024)),r*.81,lamp,18)
        project(body,'Amber bumper marker',[(side*x,z) for x,z in
            ((.50,.396),(.69,.402),(.73,.435),(.51,.433))],AMBER,'y',lift=.013)
        project(bumper,'Intake pocket',[(side*x,z) for x,z in
            ((.284,.213),(.755,.228),(.80,.274),(.72,.31),(.322,.305))],
            mat('Intake shadow',(.003,.004,.005),.7),'y',lift=.009)
        project(body,'Door livery',[(-.70,.397),(.68,.679),(1.01,.676),(.84,.409),
            (-.24,.245)],DARK,'x',side,.011)
        project(body,'Red livery stripe',[(-.49,.331),(.83,.531),(.845,.514),(-.48,.312)],
            RED,'x',side,.014)
        project(body,'Flush handle',[(.34,.659),(.49,.683),(.49,.66),(.34,.638)],
            DARK,'x',side,.014)
        rod('Mirror stalk',(side*.68,-.49,.797),(side*.938,-.55,.879),.027,DARK,10)
        box('Black mirror',(side*.964,-.556,.903),(.218,.143,.097),DARK,.026)
        box('Side sill',(side*.922,.10,.177),(.13,1.54,.10),DARK,.022)
        for x in (.58,.75):
            rod('Round tail lamp',(side*x,2.257,.54),(side*x,2.293,.54),.062,RED,22)
    box('Rear diffuser',(0,2.155,.218),(1.71,.32,.14),DARK,.046)
    return 1.25


def fighter():
    gray=mat('Blue gray airframe',(.22,.30,.36),.44,.24)
    pale=mat('Light gray trim',(.35,.41,.45),.46,.18)
    fuselage=aircraft_shell('Blended fuselage',[
        (-4.1,1.28,.024,.033),(-3.88,1.30,.14,.13),(-3.51,1.35,.25,.24),
        (-3.10,1.42,.36,.32),(-2.64,1.47,.49,.37),(-2.26,1.49,.57,.40),
        (-1.86,1.43,.64,.43),(-1.43,1.35,.83,.42),(-1.00,1.33,1.0,.40),
        (-.43,1.32,1.09,.38),(.28,1.31,1.11,.34),(1.12,1.30,1.08,.31),
        (1.94,1.29,1.01,.28),(2.59,1.28,.94,.23),(3.15,1.24,.80,.15),
        (3.58,1.20,.23,.088)],gray,88)
    canopy=aircraft_shell('Two-seat bubble canopy',[
        (-2.89,1.72,.04,.022),(-2.65,1.78,.23,.108),(-2.34,1.82,.31,.216),
        (-1.99,1.82,.33,.275),(-1.62,1.78,.315,.254),
        (-1.22,1.72,.25,.199),(-.91,1.67,.105,.081)],GLASS,60)
    for side in (-1,1):
        wing=[(-.96,1.40),(-.68,1.48),(.79,1.46),(1.87,1.31),(-.59,1.26)]
        flight_surface('Swept wing',[(side*.71,y,z) for y,z in wing],
            [(side*3.18,y,z) for y,z in [(.58,1.36),(.75,1.39),(1.13,1.38),(1.54,1.34),(.89,1.32)]],gray)
        flight_surface('Tailplane',[(side*.68,y,z) for y,z in
            [(1.55,1.34),(1.80,1.39),(2.36,1.35),(3.18,1.29),(1.79,1.28)]],
            [(side*2.05,y,z) for y,z in [(2.45,1.37),(2.60,1.39),(2.88,1.37),(3.05,1.34),(2.67,1.33)]],pale)
        flight_surface('Canted tail fin',[(side*x,y,1.42) for x,y in
            [(.63,1.12),(.75,1.39),(.79,2.34),(.68,3.09),(.58,1.66)]],
            [(side*x,y,2.68) for x,y in
            [(.88,2.06),(.925,2.24),(.937,2.60),(.893,2.90),(.858,2.28)]],gray)
        nacelle=aircraft_shell('Engine fairing',[
            (-1.52,1.04,.21,.24),(-1.18,1.04,.33,.32),(-.77,1.05,.40,.36),
            (.28,1.06,.417,.37),(1.45,1.075,.407,.355),(2.44,1.085,.36,.325),
            (3.05,1.087,.342,.297),(3.25,1.087,.30,.268)],gray,72)
        nacelle.location.x=side*.63
        box('Intake shadow',(side*.62,-1.46,.98),(.55,.14,.39),DARK,.064)
        rod('Exhaust ring',(side*.63,3.10,1.087),(side*.63,3.46,1.087),.258,METAL,54)
        rod('Exhaust dark interior',(side*.63,3.46,1.087),(side*.63,3.474,1.087),.210,DARK,48)
    project(fuselage,'Nose dielectric panel',[(-.20,-3.54),(.20,-3.54),(.35,-2.94),(-.35,-2.94)],pale)
    return 2.70


def game_export(objects, path):
    bpy.ops.object.select_all(action='DESELECT')
    copies=[]
    for o in objects:
        c=o.copy()
        c.data=o.data.copy()
        bpy.context.collection.objects.link(c)
        c.select_set(True)
        copies.append(c)
        for attr in list(c.data.color_attributes):
            c.data.color_attributes.remove(attr)
        colors=c.data.color_attributes.new(name='Color',type='BYTE_COLOR',domain='CORNER')
        for p in c.data.polygons:
            rgba=c.data.materials[p.material_index].diffuse_color
            for i in p.loop_indices:
                colors.data[i].color=rgba
        c.data.materials.clear()
        c.data.materials.append(GAME)
    bpy.context.view_layer.objects.active=copies[0]
    bpy.ops.object.join()
    joined=bpy.context.object
    joined.name=path.stem
    color=joined.data.color_attributes['Color']
    joined.data.color_attributes.active_color=color
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_vertex_color='ACTIVE',export_texcoords=False)
    bpy.data.objects.remove(joined,do_unlink=True)

def studio(style,height):
    scene=bpy.context.scene
    floor=mat('Studio cyclorama',(.09,.094,.098) if style!='f1' else (.092,.115,.146),.33)
    box('Studio floor',(0,0,-.076),(200,200,.14),floor,0)
    scene.world=bpy.data.worlds.new('Studio ambient')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.36,.43,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.21
    scene.world.color=(.31,.34,.38)
    def aim(o, target):
        o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    for name,loc,power,size,color in [
        ('Key',(-4,-4,7),1200,4,(1,.91,.80)),('Silhouette',(3,4,6),1400,4.0,(.76,.87,1)),
        ('Fill',(4,-3,4),265,4,(.87,.94,1)),('Overhead',(-1,1,7),345,3.3,(1,1,1))]:
        data=bpy.data.lights.new(name,'AREA')
        data.energy=power
        data.shape='DISK'
        data.size=size
        data.color=color
        obj=bpy.data.objects.new(name,data)
        scene.collection.objects.link(obj)
        obj.location=loc
        aim(obj,(0,0,.55))
    data=bpy.data.cameras.new('Three-quarter')
    camera=bpy.data.objects.new('Three-quarter',data)
    scene.collection.objects.link(camera)
    tall=height>2
    camera.location=(6.8,-8.8,4.3) if tall else (5.7,-8.3,3.0)
    if style=='f1-reference':
        camera.location=(5.1,-8.8,2.75)
    aim(camera,(0,.03,height*(.48 if tall else .38)))
    data.type='ORTHO'
    data.ortho_scale={'jetplane':9.8,'helicopter':9.4,'fighter':11.5,'f1-reference':5.12}.get(style,6.55 if tall else 5.62)
    scene.camera=camera
    scene.render.engine='CYCLES'
    scene.cycles.samples=16
    scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED'
    scene.render.threads=6
    scene.render.resolution_x=1180
    scene.render.resolution_y=790
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.27

def build(style):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global STYLE, DARK, GLASS, RUBBER, METAL, RED, AMBER, LIGHT, GAME
    STYLE=style
    DARK=mat('Graphite',(.022,.029,.034),.38,.22)
    GLASS=mat('Smoked glass',(.009,.018,.024),.22,.08)
    if style in ('hatchback','jetplane','helicopter'):
        GLASS.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.19
    RUBBER=mat('Tire rubber',(.019,.021,.023),.72)
    METAL=mat('Machined alloy',(.093,.102,.109),.44,.66)
    RED=mat('Tail lens',(.64,.029,.028),.24,.21)
    AMBER=mat('Amber lens',(1,.305,.024),.28,.12)
    LIGHT=mat('Optics',(.78,.91,1),.20,.16)
    p=LIGHT.node_tree.nodes.get('Principled BSDF')
    p.inputs['Emission Color'].default_value=(.67,.86,1,1)
    p.inputs['Emission Strength'].default_value=.215
    GAME=mat('Vertex color',(.8,.8,.8),.54)
    attr=GAME.node_tree.nodes.new('ShaderNodeVertexColor')
    attr.layer_name='Color'
    GAME.node_tree.links.new(attr.outputs['Color'],GAME.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    if style in ('f1','wedge','senna'):
        h=sport(style)
    elif style=='f1-reference':
        h=reference_f1()
    elif style=='fighter':
        h=fighter()
    elif style in ('hatchback','jetplane','helicopter'):
        h={'hatchback':hatchback,'jetplane':jetplane,'helicopter':helicopter}[style]()
    elif style=='tractor':
        h=tractor()
    else:
        h=truck(style=='carrier')
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in objects:
        o.data.calc_loop_triangles()
    triangles=sum(len(o.data.loop_triangles) for o in objects)
    minimum, maximum=(0,9999) if style in ('fighter','pickup','carrier','tractor') else (12000,15000)
    if not minimum <= triangles <= maximum:
        raise ValueError(f'{style} outside the {minimum:,}–{maximum:,} triangle range: {triangles}')
    print('VEHICLE',style,triangles,flush=True)
    game_export(objects,OUT/f'{style}.glb')
    studio(style,h)
    bpy.context.scene.render.filepath=str(OUT/f'{style}.png')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{style}.blend'))
    bpy.ops.render.render(write_still=True)

if __name__=='__main__':
    for style in (sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['f1','wedge','senna','pickup','carrier','tractor']):
        build(style)
