## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Authors: Michel F. SANNER, Daniel Stoffler
#
#    sanner@scripps.edu
#    stoffler@scripps.edu
#
# Copyright: M. Sanner, Daniel Stoffler TSRI 2000
#
#############################################################################


#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/Spheres.py,v 1.84 2008/09/03 21:49:01 vareille Exp $
#
# $Id: Spheres.py,v 1.84 2008/09/03 21:49:01 vareille Exp $
#

from opengltk.OpenGL import GL, GLU
from opengltk.extent.utillib import glDrawSphereSet, extractedGlutSolidSphere


from Geom import Geom
import datamodel, viewerConst
import numpy.oldnumeric as Numeric, math
from viewerFns import checkKeywords
from DejaVu.colorTool import glMaterialWithCheck, resetMaterialMemory
import warnings

try:
    from UTpackages.UTimposter import utimposterrend
    UTImposterRendererFound = True
except ImportError:
    #warnings.warn('UTpackages.UTimposter not found')
    UTImposterRendererFound = False

    
class GLUSpheres(Geom):
    """Class for sets of spheres"""

    if glDrawSphereSet:
        fastSpheres = 1
    else:
        fastSpheres = 0

    keywords = Geom.keywords + [
        'centers',
        'quality',
        'radii',
        'slices',
        'stacks'
        ]


    def __init__(self, name=None, check=1, **kw):
        #print "Spheres.__init__"
        v = kw.get('centers')
        if v:
            kw['vertices'] = v     # rename centers in vertices for Geom.__init
        elif not kw.get('shape'):
            kw['shape'] = (0,3)    # default shape for sphere set

        self.templateDSPL = None # (displayList, openglContext)
        #self.firstList = GL.glGenLists(3)

        self.culling = GL.GL_BACK
        self.inheritCulling = 0

        self.frontPolyMode = GL.GL_FILL
        self.inheritFrontPolyMode = viewerConst.NO

        self.oneRadius = viewerConst.YES
        self.radius = 1.0

        if not kw.get('quality'):
            kw['quality'] = 0

        #self.immediateRendering = True

        apply( Geom.__init__, (self, name, check), kw )
        assert len(self.vertexSet.vertices.ashape)==2
        
        self._modified = False


    def Set(self, check=1, redo=1, updateOwnGui=True, **kw):
        """set data for this object
check=1 : verify that all the keywords present can be handle by this func 
redo=1 : append self to viewer.objectsNeedingRedo
updateOwnGui=True : allow to update owngui at the end this func
"""
        redoDisplayListFlag0 = False
        
        # Exceptionnaly this has to be before the call to Geom.Set
        v = kw.get( 'centers')
        if v:
            kw['vertices'] = v     # rename centers in vertices for Geom.__init

        # Exceptionnaly this has to be before the call to Geom.Set
        # because we want to override the treatment of it by Geom.Set
        invertNormals = kw.get('invertNormals')
        if invertNormals is not None:
            kw.pop('invertNormals')
            if self.invertNormals != invertNormals:
                self.invertNormals = invertNormals
                self.chooseTemplate()
                redoDisplayListFlag0 = True

        redrawFlag, \
        updateOwnGuiFlag, \
        redoViewerDisplayListFlag, \
        redoDisplayListFlag, \
        redoTemplateFlag, \
        redoDisplayChildrenListFlag = apply( Geom.Set, (self, check, 0), kw)
        
        redoDisplayListFlag = redoDisplayListFlag or redoDisplayListFlag0

        rad = kw.get('radii')
        if rad is not None:
            if type(rad).__name__ in ('float','int'):
                self.oneRadius = viewerConst.YES
                self.radius = rad
                self.vertexSet.radii = datamodel.ScalarProperties('radii',
                           shape=(0,), datatype=viewerConst.FPRECISION)
            else: # type(rad).__name__ in ('list', 'tuple', 'ndarray'):
                if len(rad)==1:
                    self.oneRadius = viewerConst.YES
                    self.radius = rad[0]
                self.vertexSet.radii = datamodel.ScalarProperties('radii', rad,
                              datatype=viewerConst.FPRECISION)
        elif hasattr(self.vertexSet, 'radii') is False:
            self.vertexSet.radii = datamodel.ScalarProperties(
                                        'radii',
                                        shape=(0,), 
                                        datatype=viewerConst.FPRECISION)

        if rad is not None or v is not None:
            redoDisplayListFlag = True
            self.vertexSet.radii.PropertyStatus(len(self.vertexSet))
            if self.vertexSet.radii.status < viewerConst.COMPUTED:
                self.oneRadius = viewerConst.YES
            else:
                self.oneRadius = viewerConst.NO

        quality = kw.get( 'quality')
        if quality != None:
            if quality < 3:
                if len(self.vertexSet.vertices.array) < 500:
                    quality = 20
                elif len(self.vertexSet.vertices.array) < 5000:
                        quality = 15
                elif len(self.vertexSet.vertices.array) < 10000:
                        quality = 10
                else:
                        quality = 5
            self.slices = quality
            self.stacks = quality
            if self.templateDSPL is not None:
                redoTemplateFlag = True
                redoDisplayListFlag = True


        slices = kw.get( 'slices')
        if slices != None:
            if slices > 2:
                self.slices = slices
                if self.templateDSPL is not None:
                    redoTemplateFlag = True
                    redoDisplayListFlag = True

        stacks = kw.get( 'stacks')
        if stacks != None:
            if stacks > 2:
                self.stacks = stacks
                if self.templateDSPL is not None:
                    redoTemplateFlag = True
                    redoDisplayListFlag = True

        if redo and self.viewer:
            if redoTemplateFlag is True:
                self.redoTemplate()
                redrawFlag = True
            if redoDisplayListFlag is True:
                if self not in self.viewer.objectsNeedingRedo.keys():
                    self.viewer.objectsNeedingRedo[self] = None
                redrawFlag = True
            if redoDisplayChildrenListFlag is True:
                lObjectsNeedingRedo = self.viewer.objectsNeedingRedo.keys()
                for child in self.AllObjects():
                    if child not in lObjectsNeedingRedo:
                        self.viewer.objectsNeedingRedo[child] = None
                redrawFlag = True
            if redoViewerDisplayListFlag is True:
                self.viewer.deleteOpenglList()
                redrawFlag = True
            if updateOwnGui is True and updateOwnGuiFlag is True and self.ownGui is not None:
                self.updateOwnGui()
            if redrawFlag is True:
                self.viewer.Redraw()
        return redrawFlag, updateOwnGuiFlag, redoViewerDisplayListFlag, redoDisplayListFlag, redoTemplateFlag, redoDisplayChildrenListFlag



    def deleteTemplate(self):
        #print "Spheres.deleteTemplate", self.templateDSPL
        # it is asumed the right OpenGL context is active
        if GL.glGetIntegerv(GL.GL_LIST_INDEX) == [0]:
            assert self.templateDSPL is not None
            currentcontext = self.viewer.currentCamera.tk.call(self.viewer.currentCamera._w, 'getcurrentcontext')
            if currentcontext != self.templateDSPL[1]:
                import traceback;traceback.print_stack()
                warnings.warn('deleteTemplate failed because the current context is the wrong one')
                print "currentcontext != self.templateDSPL[1]", currentcontext, self.templateDSPL[1]
            else:
                #print '-%d'%self.templateDSPL[0], currentcontext, "glDeleteLists Spheres0"
                #print '-%d'%(self.templateDSPL[0]+1), currentcontext, "glDeleteLists Spheres1"
                #print '-%d'%(self.templateDSPL[0]+2), currentcontext, "glDeleteLists Spheres2"
                GL.glDeleteLists(self.templateDSPL[0], 3)
                self.templateDSPL = None


    def makeTemplate(self):
        #print "Spheres.makeTemplate"
        # it is asumed the right OpenGL context is active
        # make sure we are not already in a newlist
        if GL.glGetIntegerv(GL.GL_LIST_INDEX) == [0]:
            assert self.templateDSPL is None
            lFirstList = GL.glGenLists(3)
            #lFirstList = self.firstList
            #print "Spheres.makeTemplate", lFirstList
            #print "lFirstList Spheres.makeTemplate", lFirstList, self.name
            lCurrentContext = self.viewer.currentCamera.tk.call(self.viewer.currentCamera._w,
                                                        'getcurrentcontext')
            self.templateDSPL = ( lFirstList, lCurrentContext )

            GL.glNewList(lFirstList+1, GL.GL_COMPILE)
            #print '+%d'%(lFirstList+1), lCurrentContext, "glNewList Spheres1"
            extractedGlutSolidSphere(1, self.slices, self.stacks, 0)
            #print '*%d'%GL.glGetIntegerv(GL.GL_LIST_INDEX), "glEndList Spheres1"
            GL.glEndList()
        
            GL.glNewList(lFirstList+2, GL.GL_COMPILE)
            #print '+%d'%(lFirstList+2), lCurrentContext, "glNewList Spheres2"
            extractedGlutSolidSphere(1, self.slices, self.stacks, 1)
            #print '*%d'%GL.glGetIntegerv(GL.GL_LIST_INDEX), "glEndList Spheres2"
            GL.glEndList()

            self.chooseTemplate()


    def redoTemplate(self):
        if self.viewer:
            lSuspendRedraw = self.viewer.suspendRedraw
            self.viewer.suspendRedraw = True
        self.deleteTemplate()
        self.makeTemplate()
        if self.viewer:
            self.viewer.suspendRedraw = lSuspendRedraw


    def chooseTemplate(self):
        # make sure we are not already in a newlist
        if GL.glGetIntegerv(GL.GL_LIST_INDEX) == [0]:
            GL.glNewList(self.templateDSPL[0], GL.GL_COMPILE)
            #print '+%d'%self.templateDSPL[0], "glNewList Spheres0"
            if self.invertNormals:
                #print "GLU_INSIDE reversed normals"
                #print '#%d'%(self.templateDSPL[0]+2), "glCallList Spheres2"
                GL.glCallList(self.templateDSPL[0]+2)
            else:
                #print "GLU_OUTSIDE regular normals"
                #print '#%d'%(self.templateDSPL[0]+1), "glCallList Spheres1"
                GL.glCallList(self.templateDSPL[0]+1)
            #print '*%d'%GL.glGetIntegerv(GL.GL_LIST_INDEX), "glEndList Spheres0"
            GL.glEndList()
        

    def Add(self, check=1, redo=1, **kw):
	"""Add spheres"""

        if __debug__:
            if check:
                apply( checkKeywords, (self.name,self.keywords), kw)

	v = kw.get( 'centers')
	if v:
	    kw['vertices'] = v     # rename centers in vertices for Geom.__init
        apply( Geom.Add, (self,0,0), kw)

	rad = kw.get( 'radii')
	if rad:
	    if type(rad).__name__ == 'float':
		self.oneRadius = viewerConst.YES
		self.radius = rad
	    else:
		self.vertexSet.radii.AddValues( rad )

	if rad or v:
            self.redoDspLst=1
	    self.vertexSet.radii.PropertyStatus(len(self.vertexSet))
	    if self.vertexSet.radii.status < viewerConst.COMPUTED:
		self.oneRadius = viewerConst.YES
	    else:
		self.oneRadius = viewerConst.NO

        if self.viewer and redo:
            if self.redoDspLst and self not in self.viewer.objectsNeedingRedo:
                self.viewer.objectsNeedingRedo[self] = None
#                self.RedoDisplayList()


    def Draw(self):
        """Draw function of the geom
return status 0 or 1
If you want fast rendering, you need to set self.templateDSPL
using MakeTemplate.
"""
        #print "Spheres.Draw", self.name

        assert self.templateDSPL is not None

        currentcontext = self.viewer.currentCamera.tk.call(
            self.viewer.currentCamera._w, 'getcurrentcontext')
        if currentcontext != self.templateDSPL[1]:
            import traceback;traceback.print_stack()
            warnings.warn("""draw failed because the current context is the wrong one""")
            #print "currentcontext != self.templateDSPL[1]", currentcontext, self.templateDSPL[1]
            return 0
            
        centers = self.vertexSet.vertices.array
        if len(centers) == 0: 
            return 0

        if self.fastSpheres:
            #print "self.fastSpheres", self.fastSpheres
            if self.oneRadius == viewerConst.NO:
                radii = self.vertexSet.radii.array
                #FIXME: quick fix because can be called from base class Set
                # method after centers have been set BUT before radii have been
                # set
                if len(self.vertexSet.vertices) != len(radii):
                    return 0
            else:
                radii = Numeric.ones( centers.shape[0] ) * self.radius
            radii.shape = (-1,1)
            coords = Numeric.concatenate ( (centers, radii), 1 )

            if not self.inheritMaterial:
                mat = self.materials[GL.GL_FRONT]
                fpProp = []
                for propInd in range(4):
                    b, p = mat.GetProperty(propInd)
                    fpProp.append(p)
                fpProp.append(mat.prop[4])
                #fpProp = self.materials[GL.GL_FRONT].prop[:5]
            else:
                fpProp = None

            status = glDrawSphereSet( 
                                  self.templateDSPL[0],
                                  coords.astype('f'),
                                  fpProp, #self.materials[GL.GL_FRONT].prop,
                                  slices=self.slices,
                                  stacks=self.stacks,
                                  highlight=self.highlight,
                                  )
            #print "Spheres, status: ", status
            return status
        else:
            resetMaterialMemory()
            if self.oneRadius == viewerConst.NO:
                radii = self.vertexSet.radii.array
            else:
                radii = Numeric.ones( centers.shape[0] ) * self.radius

            if len(self.vertexSet.vertices) != len(radii):
                return 0
            
            if self.inheritMaterial:
                fp = None
                bp = None
            else:
                fp = self.materials[GL.GL_FRONT]
                colorFront = Numeric.array(self.materials[GL.GL_FRONT].prop[1], copy=1)
                if self.frontAndBack:
                    bp = None
                    face = GL.GL_FRONT_AND_BACK
                else:
                    bp = self.materials[GL.GL_BACK]
                    face = GL.GL_FRONT

            if fp:
                for m in (0,1,2,3,4):
                    if fp.binding[m] == viewerConst.OVERALL:
                        glMaterialWithCheck( face,
                                             viewerConst.propConst[m],
                                             fp.prop[m][0])
                if fp.binding[1] == viewerConst.OVERALL:
                    GL.glColor4fv(colorFront[0])

            for i in xrange(centers.shape[0]):
                GL.glPushName(i)

                if fp:
                    for m in (0,1,2,3,4):
                        if fp.binding[m] != viewerConst.OVERALL:
                            glMaterialWithCheck( face,
                                                 viewerConst.propConst[m],
                                                 fp.prop[m][i])

                    if fp.binding[1] != viewerConst.OVERALL:
                        GL.glColor4fv(colorFront[i])
                if bp:
                    for m in (0,1,2,3,4):
                        if bp.binding[m] != viewerConst.OVERALL:
                            glMaterialWithCheck( GL.GL_BACK,
                                                 viewerConst.propConst[m],
                                                 bp.prop[m][i] )

                GL.glPushMatrix()
                GL.glTranslatef(float(centers[i][0]),
                                float(centers[i][1]),
                                float(centers[i][2]))
                if not self.oneRadius:
                    GL.glScalef(float(radii[i]),float(radii[i]),float(radii[i]))
                else:
                    GL.glScalef(float(self.radius), float(self.radius), float(self.radius))
                print '#%d'%self.templateDSPL[0], "glCallList Spheres0"
                GL.glCallList(self.templateDSPL[0])
                GL.glPopMatrix()
                GL.glPopName()
            return 1


    def asIndexedPolygons(self, run=1, quality=None, **kw):
        """ run=0 returns 1 if this geom can be represented as an
        IndexedPolygon and None if not. run=1 returns the IndexedPolygon
        object."""

        if run==0:
            return 1 # yes, I can be represented as IndexedPolygons
        
        if quality is None:
            quality = 2
        
        # get centers
        centers = self.vertexSet.vertices.array

        # get radii
        if self.oneRadius == viewerConst.NO:
            radii = self.vertexSet.radii.array
        else:
            radii = Numeric.ones( centers.shape[0] ) * self.radius

        # create template sphere
        S = TriangulateIcosByEdgeCenterPoint(quality=quality)
        tmpltVertices = S.getVertices(quality=quality)
        tmpltFaces = S.getFaces(quality=quality)
        tmpltNormals = S.getVNormals(quality=quality)

        # these lists will store the data for the new spheres
        vertices = []
        faces = []
        normals = []

        # loop over spheres
        for i in range(len(centers)):
            vert = Numeric.array(tmpltVertices[:])*radii[i] + centers[i]
            vertices.extend(list(vert))
            fac = Numeric.array(tmpltFaces[:]) + i*len(tmpltVertices)
            faces.extend(list(fac))
            norm = Numeric.array(tmpltNormals[:])
            normals.extend(list(norm))

        from DejaVu.IndexedPolygons import IndexedPolygons
        sphGeom = IndexedPolygons("sph", vertices=Numeric.array(vertices),
                               faces=faces, vnormals=Numeric.array(normals),
                               visible=1, invertNormals=self.invertNormals)

        # copy Spheres materials into sphGeom
        matF = self.materials[GL.GL_FRONT]
        matB = self.materials[GL.GL_BACK]
        sphGeom.materials[GL.GL_FRONT].binding = matF.binding[:]
        sphGeom.materials[GL.GL_FRONT].prop = matF.prop[:]
        sphGeom.materials[GL.GL_BACK].binding = matB.binding[:]
        sphGeom.materials[GL.GL_BACK].prop = matB.prop[:]

        if sphGeom.materials[GL.GL_FRONT].binding[1] == viewerConst.PER_VERTEX:
            newprop = []
            index = 0
            cnt = 0
            for i in range(len(vertices)):
                newprop.append(sphGeom.materials[GL.GL_FRONT].prop[1][index])
                cnt = cnt + 1
                if cnt == len(tmpltVertices):
                    index = index + 1
                    cnt = 0
            
            sphGeom.materials[GL.GL_FRONT].prop[1] = newprop         
        return sphGeom



if UTImposterRendererFound:
    class UTSpheres(GLUSpheres):

        #del keywords['quality']
        #del keywords['stacks']
        #del keywords['slices']
        keywords = list(GLUSpheres.keywords)
        for kw in ['quality', 'stacks', 'slices']:
            keywords.remove(kw)


        def makeTemplate(self):
            pass
        
        def Set(self, check=1, redo=1, **kw):
            """Set spheres"""

            if __debug__:
                if check:
                    apply( checkKeywords, (self.name,self.keywords), kw)

            v = kw.get( 'centers')
            if v:
                kw['vertices'] = v     # rename centers in vertices for Geom.__init

            mat = kw.has_key('materials')

            apply( Geom.Set, (self, 0, 0), kw)

            rad = kw.get( 'radii')
            if rad != None:
                if type(rad).__name__ in ('float','int'):
                    self.oneRadius = viewerConst.YES
                    self.radius = rad
                    self.vertexSet.radii = datamodel.ScalarProperties('radii',
                                       shape=(0,), datatype=viewerConst.FPRECISION)
                else:
                    self.vertexSet.radii = datamodel.ScalarProperties('radii', rad,
                                                  datatype=viewerConst.FPRECISION)

            if mat or rad or v:
                self.redoDspLst=1
                coords = self.vertexSet.vertices.array
                rad = self.vertexSet.radii.array
                mat = self.materials[GL.GL_FRONT].prop[1]
                self.initializeImposterRenderer(coords, rad, mat)

            if self.viewer and redo:
                if self.redoDspLst and self not in self.viewer.objectsNeedingRedo:
                    self.viewer.objectsNeedingRedo[self] = None


        def initializeImposterRenderer(self, coords, rad, col):
            status = self.imposterRenderer.initRenderer()
            print "initializeImposterRenderer status:", status
            if not status:
                print "Could not initialize the imposter renderer\n"
                return False
            self.imposterRenderer.initSubRenderers(0)
            self.imposterRenderer.clear()
            #brp = utimposterrend.BallRendererPtr(self.imposterRenderer.m_BallRenderer)

            #print "coords:", coords
            #print "radius:", rad
            #print "colors:", col
            if type(coords) == Numeric.ndarray:
                coords = coords.tolist()
            if type(rad)== Numeric.ndarray: 
                rad = rad.tolist()
            if type(col) == Numeric.ndarray:
                col = col.tolist()
            print "adding spheres...", len(rad)
            brp = self.imposterRenderer.m_BallRenderer
            if len(col) == len(coords):
                for i in range(len(coords)):
                    #print "adding ball", i
                    brp.addBall(coords[i][0], coords[i][1], coords[i][2], rad[i], col[i][0], col[i][1], col[i][2])
            elif len(rad) == len(coords):
                for i in range(len(coords)):
                    #print "adding ball", i
                    brp.addBall(coords[i][0], coords[i][1], coords[i][2], rad[i], col[0][0], col[0][1], col[0][2])
            else:
                for i in range(len(coords)):
                    #print "adding ball", i
                    brp.addBall(coords[i][0], coords[i][1], coords[i][2], 1., col[0][0], col[0][1], col[0][2])
            print "done"    
                                                             
            return True


        def __init__(self, name=None, check=1, **kw):

            if __debug__:
                if check:
                    apply( checkKeywords, (name,self.keywords), kw)

            self.imposterRenderer = utimposterrend.ImposterRenderer()

            v = kw.get('centers')
            if v:
                kw['vertices'] = v     # rename centers in vertices for Geom.__init
            elif not kw.get('shape'):
                kw['shape'] = (0,3)    # default shape for sphere set

            apply(Geom.__init__, (self, name, 0), kw )
            self.culling = GL.GL_BACK
            self.inheritCulling = 0
            self.templateDSPL = None # (displayList, openglContext)
            assert len(self.vertexSet.vertices.ashape)==2

            self.frontPolyMode = GL.GL_FILL
            self.inheritFrontPolyMode = viewerConst.NO
            self.lighting = viewerConst.YES

            rad = kw.get( 'radii')
            if rad:
                GLUSpheres.Set(self, check=0, redo=0, radii = rad )
            else:
                self.vertexSet.radii = datamodel.ScalarProperties('radii',
                                     shape=(0,), datatype=viewerConst.FPRECISION)

            self._modified = False
            self.immediateRendering = 1
            self.transparent = 0
            self.inheritMaterial = 1
            self.inheritXform = 1


        def Draw(self):
            self.imposterRenderer.renderBuffer(True, False, None, None, 0, False, 1.0)

Spheres = GLUSpheres  # UTSpheres GLUSpheres


class TriangulateIcos:
    """Base class to compute vertices, faces and normals of a sphere based
    on icosahedral subdivision. Subclassed will implement different
    subdivision methods.
    A quality can be passed to the constructur which will trigger the
    precomputation of spheres of quality 0 to quality.
    To access the data, use getVertices(quality=val), getFaces(quality=val),
    getVNormals(quality=val) where val is the quality level """
    

    def __init__(self, quality=None):
        if quality is None:
            quality = 5 # set default to 5
        self.quality = quality

        self.vertices=[] # stores vertices
                         # face lists are created dynamically later on
                         # normals == vertices
        
        X = 0.525731112119133606 # X coord
        Z = 0.850650808352039932 # Y coord

        # build initial icosahedron (lowest quality)
        self.vertices = [
            [-X, 0., Z], [X, 0., Z], [-X, 0., -Z], [X, 0., -Z],
            [0., Z, X], [0., Z, -X], [0., -Z, X], [0., -Z, -X],
            [Z, X, 0.], [-Z, X, 0.], [Z, -X, 0.], [-Z, -X, 0.]
            ]

        self.facesQ0 = [
            [11,6,0], [9,11,0], [0,6,1], [6,10,1], [9,5,2], [7,11,2], [5,3,2],
            [8,10,3], [5,8,3], [0,1,4], [9,4,5], [4,8,5], [7,10,6], [2,3,7],
            [4,1,8], [0,4,9], [8,1,10], [7,3,10], [7,6,11], [9,2,11]
            ]


    def subsample(self, vertices, faces, quality):
        lenF = len(faces)
        lenV = len(vertices)

        for i in xrange(lenF):
            v0 = vertices[faces[i][0]]
            v1 = vertices[faces[i][1]]
            v2 = vertices[faces[i][2]]
            self.subdivideVert(v0, v1, v2)

        self.subdivideFaces(faces, lenV, quality)
    

    def normalize(self, v):
        d = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
        if d == 0.0:
            print 'Zero length vector!'
            return
        return [v[0] / d, v[1] / d, v[2] / d]


    def getVertices(self, quality=0):
        """ has to be implemented by subclass """
        pass

    def getVNormals(self, quality=0):
        """ has to be implemented by subclass """
        pass
    
    def getFaces(self, quality=0):
        return getattr(self, 'facesQ%d'%quality)


class TriangulateIcosByEdgeCenterPoint(TriangulateIcos):
    
    def __init__(self, quality=None):
        TriangulateIcos.__init__(self, quality)
    
        if self.quality > 0:
            for qu in range(1, self.quality+1):
                self.subsample(self.vertices,
                               getattr(self, 'facesQ%d'%(qu-1,) ),
                               qu)


    def subdivideVert(self, v0, v1, v2):
        # called by subsample
        v01 = []
        v12 = []
        v20 = []
        
        for i in range(3):
            v01.append(v0[i] + v1[i])
            v12.append(v1[i] + v2[i])
            v20.append(v2[i] + v0[i])

        v01=self.normalize(v01)
        v12=self.normalize(v12)
        v20=self.normalize(v20)

        self.vertices.append(v01)
        self.vertices.append(v12)
        self.vertices.append(v20)
        

    def subdivideFaces(self, faces, lenV, quality):
        # called by subsample
        newFaces = []
        
        for i in xrange(len(faces)):
            j = i
            j = j * 3
            f0 = faces[i][0]
            f1 = faces[i][1]
            f2 = faces[i][2]
            f01 = j+lenV
            f12 = j+lenV+1
            f20 = j+lenV+2
            newFaces.append([f0, f01, f20])
            newFaces.append([f01, f12, f20])
            newFaces.append([f01, f1, f12])
            newFaces.append([f20, f12, f2])

        # dynamically create a self.facesQ<quality>
        setattr(self, 'facesQ%d'%quality, newFaces[:])


    def getVertices(self, quality=0):
        # the vertex list is very big, since vertices are added to this
        # list after every subsampling. Thus, only what is needed is returned
        v = 12 # vertices of icosahedron
        f = 20 # faces of icosahedron
        
        for i in range(quality):
            v = v+f*3
            f = f*4
        return self.vertices[:v]


    def getVNormals(self, quality=0):
        # normals == vertices
        self.normals = self.getVertices(quality=quality)[:]
        return self.normals


class TriangulateIcosByFaceCenterPoint(TriangulateIcos):
    """ This class subdivides each face in 3 new faces by putting a center
    in the middle of a face triangle."""

    def __init__(self, quality=None):
        TriangulateIcos.__init__(self, quality)
        
        if self.quality > 0:
            for qu in range(1, self.quality+1):
                self.subsample(self.vertices,
                               getattr(self, 'facesQ%d'%(qu-1,) ),
                               qu)


    def subdivideVert(self, v0, v1, v2):
        # called by subsample
        v012 = []
                
        for i in range(3):
            v012.append(v0[i] + v1[i] + v2[i])

        v012 = self.normalize(v012)
        self.vertices.append(v012)


    def subdivideFaces(self, faces, lenV, quality):
        # called by subsample
        newFaces = []
        
        for i in xrange(len(faces)):
            f0 = faces[i][0]
            f1 = faces[i][1]
            f2 = faces[i][2]
            f012 = i+lenV
            newFaces.append([f0, f1, f012])
            newFaces.append([f1, f2, f012])
            newFaces.append([f2, f0, f012])

        # dynamically create a self.facesQ<quality>
        setattr(self, 'facesQ%d'%quality, newFaces[:])


    def getVertices(self, quality=0):
        # the vertex list is very big, since vertices are added to this
        # list after every subsampling. Thus, only what is needed is returned
        v = 12 # vertices of icosahedron
        f = 20 # faces of icosahedron
        
        for i in range(quality):
            v = v+f
            f = f*3
        return self.vertices[:v]


    def getVNormals(self, quality=0):
        # normals == vertices
        return self.getVertices(quality=quality)

