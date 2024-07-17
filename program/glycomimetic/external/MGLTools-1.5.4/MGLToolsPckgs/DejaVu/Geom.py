## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER, Daniel Stoffler
#
# Copyright: M. Sanner, Daniel Stoffler TSRI 2000
#
# Revision: Guillaume Vareille
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/Geom.py,v 1.204.2.1 2008/12/03 23:21:06 vareille Exp $
#
# $Id: Geom.py,v 1.204.2.1 2008/12/03 23:21:06 vareille Exp $
#

import numpy.oldnumeric as Numeric, types, warnings
from opengltk.OpenGL import GL
import Materials, datamodel, Clip
from DejaVu.colorTool import OneColor, resetMaterialMemory
from DejaVu.Transformable import Transformable
from DejaVu.Displayable import Displayable
from DejaVu.viewerFns import checkKeywords
from DejaVu import viewerConst
from DejaVu.Common2d3dObject import Common2d3dObject

class Geom(Common2d3dObject, Transformable, Displayable):
    """Base class for objects that can be displayed in a camera
"""

    _numberOfDeletedGeoms  = 0
##      def __del__(self):
##          self.__class__._numberOfDeletedGeoms = self.__class__._numberOfDeletedGeoms + 1
##          print 'Free Geom ', self.__class__.__name__

    keywords = Common2d3dObject.keywords + [
                #'antialiased',
                'backPolyMode',
                'blendFunctions',
                'culling',
                'depthMask',
                'disableStencil',
                'frontPolyMode',
                'highlight',
                'inheritBackPolyMode',
                'inheritCulling',
                'inheritFrontPolyMode',
                'inheritLighting',
                'inheritStippleLines',
                'inheritLineWidth',
                'inheritMaterial',
                'inheritPointWidth',
                'inheritStipplePolygons',
                'inheritShading',
                'inheritSharpColorBoundaries',
                'inheritXform',
                'instanceMatrices',
                'invertNormals',
                'lighting',
                'lineWidth',
                'matBind',
                'materials',
                'matInd',
                'matMask',
                'matName',
                'opacity',
                'outline',
                'pickableVertices',
                'pivot',
                'pointWidth',
                'polyFace',
                'propName',
                'rawMaterial',
                'rotation',
                'scale',
                'scissor',
                'scissorAspectRatio',
                'scissorH',
                'scissorX',
                'scissorY',
                'scissorW',
                'shading',
                'shape',
                'sharpColorBoundaries',
                'stippleLines',
                'stipplePolygons',
                'texture',
                'textureCoords',
                'transient',
                'translation',
                'vertices',
                'vnormals',
                'vreshape',
                ]

    sourceBlendFunctions = [
        GL.GL_ZERO,
        GL.GL_ONE,
        GL.GL_DST_COLOR,
        GL.GL_ONE_MINUS_DST_COLOR,
        GL.GL_SRC_ALPHA,
        GL.GL_ONE_MINUS_SRC_ALPHA,
        GL.GL_DST_ALPHA,
        GL.GL_ONE_MINUS_DST_ALPHA,
        GL.GL_SRC_ALPHA_SATURATE
        ]
    destBlendFunctions = [ GL.GL_ZERO, GL.GL_ONE,
                           GL.GL_SRC_COLOR, GL.GL_ONE_MINUS_SRC_COLOR,
                           GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA,
                           GL.GL_DST_ALPHA, GL.GL_ONE_MINUS_DST_ALPHA ]


    def __init__(self, name=None, check=1, **kw):
        #print "Geom.__init__"

        Transformable.__init__(self)
        Displayable.__init__(self)

        self.clipP = []         # list of clipping planes clipping only self
        self.clipPI = []        # list of clipping planes that are inherited
        self.clipSide = []      # 1 or -1 for each cliping plane
                                    # FIXME side should be stored in clipping plane
        self.scissor = 0
        self.scissorX = 0
        self.scissorY = 0
        self.scissorW = 200
        self.scissorH = 200
        self.scissorAspectRatio = 1.0
        
        self.drawBB = False        
        self.colorBB = (1.0, 1.0, 1.0, 1.0)
        self.lineWidthBB = 1.0
        self.pickableVertices = False # when set individual vertices
                                           # in geom can be picked

        # bounding box defaults, get overwritten in ObjSubTreeBB
        self.maxBB = None
        self.minBB = None

        self.lighting = True

        self.dpyList = None     # display list for drawing
        self.redoDspLst = 0       # set to 1 to for Display List re-calculation

        self.pickDpyList = None # display list for picking
        
        self.normals = None

        self.vertexNormals = False
        self.faceNormals = False
        self.invertNormals = False

        self.sharpColorBoundaries = None
        if kw.has_key('sharpColorBoundaries') is False:
            kw['sharpColorBoundaries'] = True

        self.inheritSharpColorBoundaries = None
        if kw.has_key('inheritSharpColorBoundaries') is False:
            kw['inheritSharpColorBoundaries'] = True

        #print "kw['inheritSharpColorBoundaries']", kw['inheritSharpColorBoundaries']

        if not kw.get('disableStencil'):
            kw['disableStencil'] = False

        self.highlight = []

        apply( Common2d3dObject.__init__, (self, name, check), kw)

        assert len(self.vertexSet.vertices.ashape) < 4


    def getState(self):
        """return a dictionary describing this object's state
This dictionary can be passed to the Set method to restore the object's state
"""
        state = Common2d3dObject.getState(self).copy()
        lUpdate = {
            #'antialiased':self.antialiased,
            'backPolyMode':viewerConst.POLYGON_MODES_REV[self.backPolyMode],
            #'blendFunctions': see bellow
            'culling':viewerConst.CULLINGS_REV[self.culling], #see bellow
            'depthMask':self.depthMask,
            'disableStencil': self.disableStencil,
            'frontPolyMode':viewerConst.POLYGON_MODES_REV[self.frontPolyMode],
            'inheritBackPolyMode':self.inheritBackPolyMode,
            'inheritCulling':self.inheritCulling,
            'inheritFrontPolyMode':self.inheritFrontPolyMode,
            'inheritLighting':self.inheritLighting,
            'inheritStippleLines':self.inheritStippleLines,
            'inheritLineWidth':self.inheritLineWidth,
            'inheritMaterial':self.inheritMaterial,
            'inheritPointWidth':self.inheritPointWidth,
            'inheritStipplePolygons':self.inheritStipplePolygons,
            'inheritShading':self.inheritShading,
            'inheritSharpColorBoundaries': self.inheritSharpColorBoundaries,
            'inheritXform':self.inheritXform,
            'instanceMatrices':self.instanceMatrices.tolist(),
            'invertNormals':self.invertNormals,
            'lighting':self.lighting,            
            'lineWidth':self.lineWidth,
            #'matBind': covered by materialCode
            #'materials': covered by materialCode
            #'matInd': covered by materialCode
            #'matMask': covered by materialCode
            #'matName': covered by materialCode
            #'opacity': covered by materialCode
            'outline':self.drawOutline,
            'pickableVertices':self.pickableVertices,
            'pivot':list(self.pivot),
            'pointWidth':self.pointWidth,
            #'polyFace': covered by materialCode
            #'propName': covered by materialCode
            #'rawMaterial': covered by materialCode
            'rotation':list(self.rotation),
            'scale':list(self.scale),
            'shading':viewerConst.SHADINGS_REV[self.shading],
            #'shape': geometry definition rather than attributes
            'stippleLines':self.stippleLines,
            'stipplePolygons':self.stipplePolygons,
            'scissor':self.scissor,
            'scissorAspectRatio':self.scissorAspectRatio,
            'scissorH':self.scissorH,
            'scissorX':self.scissorX,
            'scissorY':self.scissorY,
            'scissorW':self.scissorW,
            'sharpColorBoundaries':self.sharpColorBoundaries,
            #'texture': FIXME TODO
            #'textureCoords': FIXME TODO
            #'transient': covered by visible
            'translation':list(self.translation),
            #'vertices': geometry definition rather than attributes
            #'vnormals': geometry definition rather than attributes
            #'vreshape': geometry definition rather than attributes
            } 
        state.update(lUpdate)

#        val = self.culling
#        if   val==viewerConst.INHERIT: val="inherit"
#        elif val==GL.GL_NONE: val="none"
#        elif val==GL.GL_FRONT: val="front"
#        elif val==GL.GL_BACK: val="back"
#        elif val==GL.GL_FRONT_AND_BACK: val="front_and_back"
#        state['culling']=val
        
        val = self.srcBlendFunc
        if val==GL.GL_ZERO: val1="GL_ZERO"
        elif val==GL.GL_ONE: val1="GL_ONE"
        elif val==GL.GL_DST_COLOR: val1="GL_DST_COLOR"
        elif val==GL.GL_ONE_MINUS_DST_COLOR: val1="GL_ONE_MINUS_DST_COLOR"
        elif val==GL.GL_SRC_ALPHA: val1="GL_SRC_ALPHA"
        elif val==GL.GL_ONE_MINUS_SRC_ALPHA: val1="GL_ONE_MINUS_SRC_ALPHA"
        elif val==GL.GL_DST_ALPHA: val1="GL_DST_ALPHA"
        elif val==GL.GL_ONE_MINUS_DST_ALPHA: val1="GL_ONE_MINUS_DST_ALPHA"
        elif val==GL.GL_SRC_ALPHA_SATURATE: val1="GL_SRC_ALPHA_SATURATE"
        
        val = self.dstBlendFunc
        if val==GL.GL_ZERO: val2="GL_ZERO"
        elif val==GL.GL_ONE: val2="GL_ONE"
        elif val==GL.GL_SRC_COLOR: val2 = "GL_SRC_COLOR"
        elif val==GL.GL_ONE_MINUS_SRC_COLOR: val2 = "GL.GL_ONE_MINUS_SRC_COLOR"
        elif val==GL.GL_SRC_ALPHA: val2 = "GL_SRC_ALPHA"
        elif val==GL.GL_ONE_MINUS_SRC_ALPHA: val2="GL_ONE_MINUS_SRC_ALPHA"
        elif val==GL.GL_DST_ALPHA: val2="GL_DST_ALPHA"
        elif val==GL.GL_ONE_MINUS_DST_ALPHA: val2="GL_ONE_MINUS_DST_ALPHA"

        state['blendFunctions'] = (val1,val2)

        return state
            

    def getGeomMaterialCode(self, geomName, indent='', includePerVertexOrFace=True):
        """Returns a list of strings containing Python code to restore the
material of this geoemtry.
indent is the level of indentation that is desired.
geomName is the name of the Geom object in the source code generated.
"""
        lines = []
        lines.append(indent+"## Material for %s\n"%self.name)
        lines.append(indent+"if %s:\n"%geomName)
        fmat = self.materials[GL.GL_FRONT]
        if fmat._modified:
            lines.append(indent+"    from opengltk.OpenGL import GL\n")
            lines.append(indent+"    state = %s\n"%str(fmat.getState(includePerVertexOrFace)))
            lines.append(indent+"    apply(%s.materials[GL.GL_FRONT].Set, (), state)\n\n"%(geomName))

        bmat = self.materials[GL.GL_BACK]
        if bmat._modified:
            lines.append(indent+"    from opengltk.OpenGL import GL\n")
            lines.append(indent+"    state = %s\n"%str(bmat.getState()))
            lines.append(indent+"    apply(%s.materials[GL.GL_BACK].Set, (), state)\n\n"%(geomName))
        lines.append(indent+"    pass  ## needed in case there no modif\n")
        lines.append(indent+"## End Materials for %s\n\n"%self.name)

        return lines
            

    def getGeomClipPlanesCode(self, geomName, indent=''):
        """Returns a list of strings containing Python code to restore the
clipping planes of this geoemtry.
indent is the level of indentation that is desired.
geomName is the name of the Geom object in the source code generated.
"""
        lines = []
        lines.append(indent+"## Clipping Planes for %s\n"%self.name)
        lines.append(indent+"if %s:\n"%geomName)
        lines.append(indent+"    %s.clipP = []\n"%geomName)
        lines.append(indent+"    %s.clipPI = []\n"%geomName)
        for i,c in enumerate(self.clipP):
            lines.append(indent+"    clip = %s.viewer.clipP[%d]\n"%(
                geomName, i))
            lines.append(indent+"    %s.AddClipPlane(clip, %s.clipSide[clip.num], False)\n"%(geomName,geomName))
        for i,c in enumerate(self.clipPI):
            lines.append(indent+"    clip = %s.viewer.clipP[%d]\n"%(
                geomName, i))
            lines.append(indent+"    %s.AddClipPlane(clip, %s.clipSide[clip.num], True)\n"%(geomName,geomName))
        lines.append(indent+"    pass  ## needed in case there no modif\n")
        lines.append(indent+"## End Clipping Planes for %s\n\n"%self.name)

        return lines
    
        
    def delete(self):
        pass


    def getVertices(self):
        """returns a handle to the vertices array"""
        return self.vertexSet.vertices.array


    def getVNormals(self):
        """returns a handle to the vertices array"""
        if self.vertexSet.normals.status == viewerConst.NONE:
            self.vertexSet.normals.GetProperty()

        return self.vertexSet.normals.array
        

    def getOcclusionPointsDir(self):
        v = self.getVertices()
        n = self.getVNormals()
        return v, n

    def getDepthMask(self):
        obj = self
        while obj.inheritMaterial:
            if obj.parent: obj = obj.parent
            else: break
        return obj.depthMask


    def SetPolyMode(self, face, mode):
        """Modify polymode"""

        obj = self
        if obj.viewer:
            if obj==self.viewer.rootObject and mode==viewerConst.INHERIT:
                return
        if mode==viewerConst.OUTLINED:
            if face==GL.GL_FRONT:
                obj.Set(outline=True, frontPolyMode=GL.GL_FILL)
            elif face==GL.GL_BACK:
                obj.Set(outline=True, backPolyMode=GL.GL_FILL)
            elif face==GL.GL_FRONT_AND_BACK:
                obj.Set(outline=True, frontPolyMode=GL.GL_FILL,
                        backPolyMode=GL.GL_FILL)
        else:
            if face==GL.GL_FRONT:
                obj.Set(outline=False, frontPolyMode=mode)
            elif face==GL.GL_BACK:
                obj.Set(outline=False, backPolyMode=mode)
            elif face==GL.GL_FRONT_AND_BACK:
                obj.Set(outline=False, frontPolyMode=mode, backPolyMode=mode)

        
    def SetFrontPolyMode(self, val):
    	"""Modify the current Object's frontPolyMode"""

        obj = self
        if obj.frontAndBack:
            obj.SetPolyMode( GL.GL_FRONT_AND_BACK, val )
        else:
            self.SetPolyMode( GL.GL_FRONT, val )


    def SetBackPolyMode(self, val):
        """Modify the current Object's frontPolyMode"""

        obj = self
        obj.frontAndBack = viewerConst.NO
        obj.SetPolyMode( GL.GL_BACK, val )


    def SetFrontBackPolyMode(self, val):
        """Modify the current Object's frontPolyMode"""
    
        obj = self
        obj.frontAndBack = viewerConst.YES
        obj.SetPolyMode( GL.GL_FRONT_AND_BACK, val )


    def GetFrontPolyMode(self):
        obj = self
        while obj.inheritFrontPolyMode:
            if obj.parent: obj = obj.parent
            else: break
        return obj.frontPolyMode


    def getDrawOutlineMode(self):
        obj = self
        while obj.inheritFrontPolyMode:
            if obj.parent: obj = obj.parent
            else: break
        return obj.drawOutline


    def GetShading(self):
        obj = self
        while obj.inheritShading:
            if obj.parent: obj = obj.parent
            else: break
        return obj.shading


    def GetLighting(self):
        obj = self
        while obj.inheritLighting:
            if obj.parent: obj = obj.parent
            else: break
        return obj.lighting


    def getSharpColorBoundaries(self):
        #print "getSharpColorBoundaries", self.name
        obj = self
        while obj.inheritSharpColorBoundaries:
            if obj.parent:
                obj = obj.parent
            else:
                break
            
        return obj.sharpColorBoundaries


    def MaterialBindingMode(self, num, face=GL.GL_FRONT, mode=None):
	"""Figure out how materials should be used to color the object"""

        if num is None:
            num = self.materials[GL.GL_FRONT].diff
        elif type(num) is types.StringType:
            num = getattr(self.materials[GL.GL_FRONT], num)

        if face is None: face = GL.GL_FRONT
	f = face
	if face == GL.GL_FRONT_AND_BACK:
	    f = GL.GL_FRONT
	    self.frontAndBack = True

	nn = self.materials[f].prop[num].shape[0]
	#self.inheritMaterial = False

	if not mode:
	    if nn == 1:
		self.materials[f].binding[num] = viewerConst.OVERALL
	    elif nn == len(self.vertexSet.vertices):
		self.materials[f].binding[num] = viewerConst.PER_VERTEX
	    elif hasattr(self, 'faceSet') and nn == len(self.faceSet):
		self.materials[f].binding[num] = viewerConst.PER_PART
	    elif nn == len(self.instanceMatrices):
		self.materials[f].binding[num] = viewerConst.PER_INSTANCE
	    else:
		self.materials[f].binding[num] = -1
		#self.inheritMaterial = True

	else: # a mode is  requested

	    if mode==viewerConst.INHERIT:
		self.materials[f].binding[num] = viewerConst.INHERIT
	    if mode==viewerConst.PER_VERTEX and \
	       nn >= len(self.vertexSet.vertices):
		self.materials[f].binding[num] = viewerConst.PER_VERTEX
	    elif hasattr(self, 'faceSet') and \
		 mode==viewerConst.PER_PART and  nn >= len(self.faceSet):
		self.materials[f].binding[num] = viewerConst.PER_PART
	    elif mode==viewerConst.OVERALL and nn >= 1:
		self.materials[f].binding[num] = viewerConst.OVERALL
	    elif mode==viewerConst.PER_INSTANCE and nn >= len(self.instanceMatrices):
		self.materials[f].binding[num] = viewerConst.PER_INSTANCE
	    else:
		self.materials[f].binding[num] = -1
		#self.inheritMaterial = True


    def AddMaterial(self, values, propNum=None, face=GL.GL_FRONT,
		    mode=None):
	"""Add materials to the current set"""

	if not values: return

        if propNum is None:
            propNum = self.materials[GL.GL_FRONT].diff
        elif type(propNum) is types.StringType:
            propNum = getattr(self.materials[GL.GL_FRONT], propNum)

	f = face
	if face == GL.GL_FRONT_AND_BACK:
	    f = GL.GL_FRONT
	    self.frontAndBack = True

	if self.materials[f].prop[propNum].shape[0]==1 and \
	   self.materials[f].binding[propNum] == viewerConst.OVERALL:
	    self.materials[f].prop[propNum] = Numeric.array( (),
					      viewerConst.FPRECISION )
	    if propNum < 4:
		self.materials[f].prop[propNum].shape = (0,4)
	    else:
		self.materials[f].prop[propNum].shape = (0,)

	values = Numeric.array( values ).astype(viewerConst.FPRECISION)
	if propNum < 4:
	    if values.shape[1] == 3:
		alpha = Numeric.ones( (values.shape[0], 1),
				      viewerConst.FPRECISION )
		values = Numeric.concatenate( (values, alpha), 1 )
	self.materials[f].prop[propNum] = \
	   Numeric.concatenate( (self.materials[f].prop[propNum], values) )
	self.MaterialBindingMode(propNum, face, mode)


    def SetMaterial(self, values, propNum, face=GL.GL_FRONT,
		    mode=None):
	"""Set the materials
        WARNING: when back face colors are set, two sided lighting has to
        be enabled"""

	if not values: return
        if propNum is None:
            propNum = self.materials[GL.GL_FRONT].diff
        elif type(propNum) is types.StringType:
            propNum = getattr(self.materials[GL.GL_FRONT], propNum)

	f = face
	if face == GL.GL_FRONT_AND_BACK: f = GL.GL_FRONT
        elif face == GL.GL_BACK:
            self.viewer.lightModel.Set(twoSide = 1)
	self.materials[f].prop[propNum] = Numeric.array( (),
                                                viewerConst.FPRECISION )
	if propNum < 4:
	    self.materials[f].prop[propNum].shape = (0,4)
	else:
	    self.materials[f].prop[propNum].shape = (0,)
	self.AddMaterial(values, propNum, face, mode)

#        mat = self.materials[f].prop[propNum]
#        if len(mat) and propNum==1: # diffuse
#            alphaMin = Numeric.minimum.reduce( mat[:,3] )
#            if alphaMin < 1.0:
#                self.setTransparency(1)
#            else:
#                self.setTransparency(0)


    def GetNormals(self):
        """Find the normals to be used for a given shading
"""
        lShadeModel = self.GetShading() #self.shading
        if lShadeModel == GL.GL_NONE:
            self.normals = None
        elif lShadeModel == GL.GL_FLAT:
            if hasattr(self, 'faceSet'):
                self.normals = self.faceSet.normals.GetProperty()
            else:
                self.normals = None
        elif lShadeModel == GL.GL_SMOOTH:
            self.normals = self.vertexSet.normals.GetProperty()


    def Add(self, check=1, redo=1, **kw):
	"""add data to this object
set self.redoDspLst to 1 to force re-building of geometries DpyList
which implies recontruction of main display list.
set redoMain to 1 to force on reconstruction of main DpyList"""
        print "Geom.Add"

        if __debug__:
            if check:
                apply( checkKeywords, (self.name,self.keywords), kw)
            
	v = kw.get( 'vertices')
	n = kw.get( 'vnormals')
	m = kw.get( 'materials')
	pf = kw.get( 'polyFace')
	mbm = kw.get( 'matBind')
	pn = kw.get( 'propName')

	if v: self.vertexSet.vertices.AddValues( v )
	if n: self.vertexSet.normals.AddValues( n )

	if v or n:
            self.redoDspLst = 1
	    self.vertexSet.normals.PropertyStatus(len(self.vertexSet))

        # expect a set of 4x4 transformation matrices with translation in
        # last column. We store a flat version of the transposed matrix since
        # this is what can be passed to OpenGL directly
	imat = kw.get( 'instanceMatrices')
        if imat:
            imat = Numeric.array(imat).astype('f')
            imat = Numeric.reshape(imat, (-1,4,4))
            assert len(imat.shape)==3 and imat.shape[1:]==(4,4)
            for m in imat:
                m = Numeric.reshape( Numeric.transpose(m), (1,16))
                conc = Numeric.concatenate
                self.instanceMatrices = conc( (self.instanceMatrices, m) )
            self.redoDspLst = 1

	if m:
            self.redoDspLst = 1
            self.AddMaterial( m, propNum=pn, mode=mbm )
	elif v or imat:
	    self.MaterialBindingMode(pn, face=pf, mode=mbm)

        if v or n:
            if self.shading==GL.GL_SMOOTH:
                if self.lighting:
                    self.GetNormals()


        if self.viewer and redo:
            if self.redoDspLst:
                self.viewer.objectsNeedingRedo[self] = None


    def SetForChildren(self, recursive=False, **kw):
        """set properties for children of this object.  If recursive is True
the properties are set for the entire subtree.
"""
        #print "SetForChildren", kw
        for c in self.children:
            apply( c.Set, (), kw)
            if recursive in (True, 1):
                apply( c.SetForChildren, (True,), kw)


    def Set(self, check=1, redo=1, updateOwnGui=True, **kw):
        """set data for this object
check=1 : verify that all the keywords present can be handle by this func 
redo=1 : append self to viewer.objectsNeedingRedo
updateOwnGui=True : allow to update owngui at the end this func
"""

        transparent = kw.pop( 'transparent', None)

        #print "Geom.Set"
        redrawFlag, \
        updateOwnGuiFlag, \
        redoViewerDisplayListFlag, \
        redoDisplayListFlag, \
        redoTemplateFlag, \
        redoDisplayChildrenListFlag = apply( Common2d3dObject.Set, (self, check, 0), kw)

        imat = kw.get( 'instanceMatrices')
        if imat is not None:
            imat = Numeric.array(imat).astype('f')
            imat = Numeric.reshape(imat, (-1,4,4))
            assert len(imat.shape)==3 and imat.shape[1:]==(4,4)
            mats = []
            for ma in imat:
                mats.append( Numeric.reshape(Numeric.transpose(ma), (16,) ) )
            self.instanceMatrices = Numeric.array(mats, 'f')
            redoDisplayListFlag = True

        v = kw.get( 'vertices')
        reshape = kw.get( 'vreshape')
        n = kw.get( 'vnormals')
        t = kw.get( 'texture')
        m = kw.get( 'materials')
        lPf = kw.get( 'polyFace')
        mbm = kw.get( 'matBind')
        pn = kw.get( 'propName')
        
        if hasattr(self, 'vertexSet') is False:
            s = kw.get( 'shape')
            if v is None and s is None: 
                s = (0,0)
            self.vertexSet = datamodel.VertexSet( v, s )

        # set default face side and default material property
        if type(lPf) is types.StringType:
            lPf = lPf.lower()
            if lPf == 'none': lPf=GL.GL_NONE
            elif lPf == 'back': lPf=GL.GL_BACK
            elif lPf == 'front': lPf=GL.GL_FRONT
            elif lPf == 'frontandback': lPf=GL.GL_FRONT_AND_BACK
        if lPf is None:
            lPf = GL.GL_FRONT

        if not v is None:
            self.vertexSet.vertices.SetValues( v, reshape )
        if not n is None:
            self.vertexSet.normals.SetValues( n, reshape )

        if (v is not None) or (n is not None):
            redoDisplayListFlag = True
            # the following line causes vnormals to be overwritten I think (MS)
            #self.vertexSet.normals.status = viewerConst.UNKNOWN

            # the line below does not force re-computation we the number
            # of coordinates is the same change
	    self.vertexSet.normals.PropertyStatus(len(self.vertexSet))

        if v is not None:
            if n is None:
                self.vertexSet.normals.status = viewerConst.NONE
            if hasattr(self, 'faceSet') or kw.has_key('faces'):
                self.faceSet.normals.status = viewerConst.NONE

        if t is not None:
            from Texture import Texture
            assert isinstance(t, Texture)
            self.texture = t
            t.objects.append(self)
            t.viewer = self.viewer
            redoDisplayListFlag = True
            if t.format==GL.GL_RGBA:
                self.setTransparency(1)
                self.inheritMaterial=0
            else:
                self.setTransparency('implicit')
                
        tx = kw.get( 'textureCoords')
        if tx is not None:
            redoDisplayListFlag = True
            self.vertexSet.texCoords = datamodel.VectorProperties('texCoords',
					  tx, datatype=viewerConst.FPRECISION)

	    shp = self.vertexSet.texCoords.ashape
	    assert len(shp)==2 and (shp[1] in (1,2,3,4))
            if hasattr(self, 'texture') and self.texture:
                self.texture.auto = 0
            
	if not v is None or tx is not None:
	    if hasattr(self.vertexSet, 'texCoords'):
		self.vertexSet.texCoords.PropertyStatus(len(self.vertexSet))

	fmode = kw.get( 'frontPolyMode')
	if fmode:
            redoDisplayListFlag = True
            if type(fmode) == types.StringType:
                fmode = viewerConst.POLYGON_MODES[fmode]
            assert fmode in viewerConst.POLYGON_MODES.values()
            self.frontPolyMode = fmode
            if fmode==viewerConst.INHERIT:
                self.inheritFrontPolyMode = True
            else:
                self.inheritFrontPolyMode = False
            if self.viewer and fmode in [GL.GL_FILL, viewerConst.OUTLINED] \
               and self.lighting:
                self.GetNormals()
                
	bmode = kw.get( 'backPolyMode')
	if bmode is not None:
            redoDisplayListFlag = True
            if type(bmode) == types.StringType:
                bmode = viewerConst.POLYGON_MODES[bmode]
            assert bmode in viewerConst.POLYGON_MODES.values()
            self.backPolyMode = bmode
            if bmode==viewerConst.INHERIT:
                self.inheritBackPolyMode = True
            else:
                self.inheritBackPolyMode = False
            if self.viewer and bmode in [GL.GL_FILL, viewerConst.OUTLINED] \
               and self.lighting:
                self.GetNormals()
            
	smode = kw.get('shading')
	if smode is not None:
            redoDisplayListFlag = True
            if type(smode) == types.StringType:
                smode = viewerConst.SHADINGS[smode]
            assert smode in viewerConst.SHADINGS.values()
            if smode==viewerConst.INHERIT:
                self.inheritShading = True
            else:
                self.inheritShading = False
            self.shading = smode
            if self.viewer: # and self.lighting:
                self.GetNormals()
                for object in self.AllObjects():
                    if isinstance(object, Geom):
                        object.GetNormals()
            redoDisplayChildrenListFlag = True
        
        if lPf == GL.GL_FRONT_AND_BACK:
            pfList = [GL.GL_FRONT, GL.GL_BACK]
        elif lPf == GL.GL_FRONT:
            pfList = [GL.GL_FRONT]
        elif lPf == GL.GL_BACK:
            pfList = [GL.GL_BACK]
        
        for pf in pfList:
	    if not m is None:
                try:
                    m = Numeric.array(m, 'f')                
                except ValueError, e:
                    raise ValueError, e

                self.materials[pf].SetMaterial( m, pn, self._modified )
                if pn is None or pn==1 or pn in ['diffuse', 'DIFFUSE',
                                                 'diff', 'DIFF']:
                    if len(m.shape)==2 and m.shape[1]==4: # opacity info was provided
                        mat = self.materials[pf]
                        self.MaterialBindingMode(mat.opac)
                        mat.SetMaterial( m[:,3], mat.opac, self._modified )
    
                self.MaterialBindingMode(pn, face=pf, mode=mbm )
                redoDisplayListFlag = True
            elif (v is not None or imat is not None) and not self.inheritMaterial:
                self.MaterialBindingMode(pn, face=pf, mode=mbm)
            elif mbm:
                redoDisplayListFlag = True
                self.MaterialBindingMode(pn, face=pf, mode=mbm)

            matName = kw.get( 'matName')
            matInd = kw.get( 'matInd')
            if matName is not None and matInd is not None:
                mat = Materials.Materials(matName, matInd)
                self.materials[pf] = mat
                #self.inheritMaterial = 0
                redoDisplayListFlag = True

            rawMat = kw.get( 'rawMaterial')
            if rawMat is not None:
                assert len(rawMat)==6
                mat = self.materials[pf]
                mask = kw.get( 'matMask')
                if mask is None:
                    # default mask sets all properties
                    mask = ( 1, 1, 1, 1, 1, 1 )
            
                for i in (0,1,2,3,4,5):
                    if mask[i]:
                        mat.SetMaterial( rawMat[i], i, self._modified )
                        self.MaterialBindingMode(i, face=pf, mode=mbm)
            
                if mask[mat.diffuse] or mask[mat.opac]:
                    self.MaterialBindingMode(pn, face=pf)
            
                #self.inheritMaterial = 0
                redoDisplayListFlag = True

            val = kw.get( 'opacity' )
            if val is not None:
                try:
                    l = len(val)
                except:
                    val = [val]
                mat = self.materials[pf]
                mat.SetMaterial( val, mat.opac, self._modified )
                self.MaterialBindingMode(mat.opac)
                redoDisplayListFlag = True

	# Schedules this object to hide in val seconds
	val = kw.get( 'transient')
	if not val is None:
	    assert isinstance(val, types.IntType)
	    if self.viewer:
		self.visible = 1
                self.redoDspLst =1 
                self.viewer.cameras[0].after(val*100, self._Hide)
	    else: raise NameError ("Object %s isn't in a viewer"
				   % (self.name,))

#	#val = kw.get( 'antialiased') # works only for linewidth <= 1.0
#        val = kw.get( 'antialiased') # works only for linewidth <= 1.0
#	if not val is None:
#	    if val in (True, False):
#		self.antialiased = val
#	    else: raise ValueError("antialiased can only be True or False")

	val = kw.get( 'lineWidth')
	if not val is None:
	    assert type(val) == type(0.0) or type(val) == type(0)
	    assert val >= 1
	    self.lineWidth = int(val)
            redoDisplayListFlag = True
	    
	val = kw.get( 'pointWidth')
	if  not val is None:
	    assert type(val) == type(0.0) or type(val) == type(0)
	    assert val >= 1
	    self.pointWidth = int(val)
            redoDisplayListFlag = True

	val = kw.get( 'visible')
	if  not val is None:
	    if val in (True, False):
                if val != self.visible and self.viewer:
                    redoDisplayListFlag = True
		self.visible = val
	    else: raise ValueError("visible can only be True or False")

        val = kw.get('lighting')
        if not val is None:
            if val in (True, False):
                if self.lighting != val:
                    self.lighting = val
                    updateOwnGuiFlag = True
                    redoDisplayListFlag = True
            else:
                raise ValueError("lighting can only be True or False")
            if self.lighting and self.normals is None:
                self.GetNormals()

        val = kw.get( 'inheritLighting')
        if val is not None:
            assert val in (False, True), "only False or True are possible"
            if self.inheritLighting != val:
                self.inheritLighting = val
                updateOwnGuiFlag = True
                redoDisplayListFlag = True

	val = kw.get( 'stippleLines')
	if  not val is None:
	    if val in (True, False):
		self.stippleLines = val
	    else: raise ValueError("stippleLines can only be True or False")

	val = kw.get( 'stipplePolygons')
	if  not val is None:
            if val in (True, False):
		self.stipplePolygons = val
	    else: raise ValueError("stipplePolygons can only be True or False")

	val = kw.get( 'outline')
	if  not val is None:
	    if val in (True, False):
		self.drawOutline = val
	    else: raise ValueError("outline can only be True or False")

	val = kw.get( 'culling')
	if val is not None:
            if type(val) is types.StringType:
                if val.lower()=="inherit": val=viewerConst.INHERIT
                elif val.lower()=="none": val=GL.GL_NONE
                elif val.lower()=="front": val=GL.GL_FRONT
                elif val.lower()=="back": val=GL.GL_BACK
                elif val.lower()=="front_and_back": val=GL.GL_FRONT_AND_BACK
	    assert val in (viewerConst.INHERIT, GL.GL_NONE,
			   GL.GL_BACK, GL.GL_FRONT_AND_BACK,
			   GL.GL_FRONT) 
            redoDisplayListFlag = True
	    if val in (GL.GL_BACK, GL.GL_NONE, GL.GL_FRONT,
			GL.GL_FRONT_AND_BACK ):
		self.inheritCulling = False
		self.culling = val
	    elif val == viewerConst.INHERIT:
		self.inheritCulling = True

 	val = kw.get( 'pickableVertices')
 	if  not val is None:
 	    if val in (True, False):
 		self.pickableVertices = val
 	    else: raise ValueError("pickableVertices can only be True or False")            
 	val = kw.get( 'scissor' )
 	if  not val is None:
 	    if val in (True, False):
 		self.scissor = val
                if self.viewer is not None:
                  if val is True:
                    self.viewer.activeScissor = self.viewer.activeScissor+1
                  else:
                    self.viewer.activeScissor = self.viewer.activeScissor-1
                redoViewerDisplayListFlagFlag = True
 	    else: raise ValueError("scissor can only be True or False")

        val = kw.get( 'scissorX' )
 	if  not val is None:
            if val < 0 : val=0
            self.scissorX = int(val)
            redoViewerDisplayListFlag = True

 	val = kw.get( 'scissorY' )
 	if  not val is None:
            if val < 0 : val=0
            self.scissorY = int(val)
            redoViewerDisplayListFlag = True

        val = kw.get( 'scissorW' )
 	if  not val is None:
            if val < 1 : val=1
            self.scissorW = int(val)
            self.scissorAspectRatio = float(self.scissorW) /self.scissorH
            redoViewerDisplayListFlag = True

        val = kw.get( 'scissorH' )
 	if  not val is None:
            if val < 1 : val=1
            self.scissorH = int(val)
            self.scissorAspectRatio = float(self.scissorW) /self.scissorH
            redoViewerDisplayListFlag = True

        val = kw.get( 'scissorAspectRatio' )
 	if  not val is None:
            if val < 0.0 : val=-val
            self.scissorAspectRatio = float(val)
            self.scissorW = int(self.scissorAspectRatio * self.scissorH)
            redoViewerDisplayListFlag = True

        val = kw.get( 'depthMask' )
 	if  not val is None:
 	    if val in (True, False):
 		self.depthMask = val
                redoDisplayListFlag = True
 	    else:
                raise ValueError("depthMask can only be True or False")

        val = kw.get( 'blendFunctions')
 	if  not val is None:
            assert len(val)==2, "arguemnt should be a 2-tuple"
            src, dst = val
            if   src=="GL_ZERO": src=GL.GL_ZER
            elif src=="GL_ONE": src=GL.GL_ONE
            elif src=="GL_DST_COLOR": src=GL.GL_DST_COLOR
            elif src=="GL_ONE_MINUS_DST_COLOR": src=GL.GL_ONE_MINUS_DST_COLOR
            elif src=="GL_SRC_ALPHA": src=GL.GL_SRC_ALPHA
            elif src=="GL_ONE_MINUS_SRC_ALPHA": src=GL.GL_ONE_MINUS_SRC_ALPHA
            elif src=="GL_DST_ALPHA": src=GL.GL_DST_ALPHA
            elif src=="GL_ONE_MINUS_DST_ALPHA": src=GL.GL_ONE_MINUS_DST_ALPHA
            elif src=="GL_SRC_ALPHA_SATURATE": src=GL.GL_SRC_ALPHA_SATURATE

            if   dst=="GL_ZERO": dst=GL.GL_ZERO
            elif dst=="GL_ONE": dst=GL.GL_ONE
            elif dst=="GL_SRC_COLOR":  dst=GL.GL_SRC_COLOR
            elif dst=="GL.GL_ONE_MINUS_SRC_COLOR": dst=GL.GL_ONE_MINUS_SRC_COLOR
            elif dst=="GL_SRC_ALPHA": dst=GL.GL_SRC_ALPHA
            elif dst=="GL_ONE_MINUS_SRC_ALPHA": dst=GL.GL_ONE_MINUS_SRC_ALPHA
            elif dst=="GL_DST_ALPHA": dst=GL.GL_DST_ALPHA
            elif dst=="GL_ONE_MINUS_DST_ALPHA": dst=GL.GL_ONE_MINUS_DST_ALPHA
            
            assert src in self.sourceBlendFunctions
            assert dst in self.destBlendFunctions
            self.srcBlendFunc = src
            self.dstBlendFunc = dst
            redoDisplayListFlag = True

        val = kw.get( 'inheritMaterial' )
        if not val is None:
           self.inheritMaterial = val
           redoDisplayListFlag = True

        val = kw.get( 'inheritXform')
        if val is not None:
            assert val in [False, True], "only False or True are possible"
            self.inheritXform = val
            redoDisplayListFlag = True

        val = kw.get( 'inheritPointWidth')
        if val is not None:
            assert val in [False, True], "only False or True are possible"
            self.inheritPointWidth = val
            redoDisplayListFlag = True # if container we force rebuilding main dpyList

        val = kw.get( 'inheritLineWidth')
        if val is not None:
            assert val in [False,True], "only False or True are possible"
            self.inheritLineWidth = val
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True # if container we force rebuilding main dpyList

        val = kw.get( 'inheritStippleLines')
        if val is not None:
            assert val in [False, True], "only False or True are possible"
            self.inheritStippleLines = val
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True # if container we force rebuilding main dpyList

        val = kw.get( 'inheritStipplePolygons')
        if val is not None:
            assert val in [False, True], "only False or True are possible"
            self.inheritStipplePolygons = val
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True

        val = kw.get( 'inheritFrontPolyMode')
        if val is not None:
            assert val in [False, True], "only False or True are possible"
            self.inheritFrontPolyMode = val
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True

        val = kw.get( 'inheritBackPolyMode')
        if val is not None:
            assert val in [False, True], "only False or True are possible"
            self.inheritBackPolyMode = val
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True

        val = kw.get( 'inheritShading')
        if val is not None:
            assert val in [False, True], "only False or True are possible"
            self.inheritShading = val
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True

        val = kw.get( 'inheritCulling')
        if val is not None:
            assert val in [False, True], "only False or True are possible"
            self.inheritCulling = val
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True

        invertNormals = kw.get('invertNormals')
        if invertNormals is not None:
            if self.invertNormals != invertNormals:
                self.invertNormals = invertNormals

        val = kw.get( 'rotation')
        if not val is None:
            mat = Numeric.reshape(Numeric.array(val), (16,)).astype('f')
            self.rotation = mat
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True

        val = kw.get( 'translation')
        if not val is None:
            mat = Numeric.reshape(Numeric.array(val), (3,)).astype('f')
            self.translation = mat
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True

        val = kw.get( 'scale' )
        if not val is None:
            try:
                mat = Numeric.reshape(Numeric.array(val), (3,)).astype('f')
            except ValueError, e:
                raise ValueError, e

            self.scale = mat
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True

        val = kw.get( 'pivot' )
        if not val is None:
            mat = Numeric.reshape(Numeric.array(val), (3,)).astype('f')
            self.pivot = mat

        inheritSharpColorBoundaries = kw.get('inheritSharpColorBoundaries')
        if inheritSharpColorBoundaries  in [True, False, 1, 0]:
            if self.inheritSharpColorBoundaries != inheritSharpColorBoundaries:
                self.inheritSharpColorBoundaries = inheritSharpColorBoundaries
                redoDisplayChildrenListFlag = True

        sharpColorBoundaries = kw.get('sharpColorBoundaries')
        if sharpColorBoundaries  in [True, False, 1, 0]:
            if self.sharpColorBoundaries != sharpColorBoundaries:
                self.sharpColorBoundaries = sharpColorBoundaries
                redoDisplayChildrenListFlag = True

        highlight = kw.get('highlight')
        if highlight is not None:
            if self.highlight != highlight:
                self.highlight = highlight
                redoDisplayListFlag = True

        disableStencil = kw.get( 'disableStencil')
        if disableStencil is not None:
            self.disableStencil = disableStencil
            redoDisplayListFlag = True

        if transparent is not None:
            self.setTransparency(transparent)
            redoDisplayListFlag = True
            redoViewerDisplayListFlag = True # if container we force rebuilding main dpyList

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


    def setTransparency(self, val):
        #print "setTransparency", val
        lDetectedTransparency =   self.materials[GL.GL_FRONT].fixOpacity() \
                               or self.materials[GL.GL_BACK].fixOpacity() \
                               or (self.drawOutline is True and self.outline.color[3]<1.0)
        if val == 'implicit':
            val = lDetectedTransparency
        elif val is True:
            val = 1
        elif val is False:
            val = 0
        assert val in [0,1], "only 0 or 1 are possible"
        self.transparent = val


    def __repr__(self):
	v = hasattr(self, 'vertexSet')
	f = hasattr(self, 'faceSet')
	if v and f:
	    return '<%s> %s with %d vertices and %d faces' % (self.__class__,
			  self.name, len(self.vertexSet), len(self.faceSet) )
	if v:
	    return '<%s> %s with %d vertices' % (self.__class__,
					self.name,  len(self.vertexSet) )

	return '<%s> ' % (self.__class__, )


    def BoundingBox(self, display=None, color=None, lineWidth=None):
	"""Turn Bounding Box drawing on and off, set attributs"""

	if not display is None:
	    assert display in viewerConst.BB_MODES
	    self.drawBB = display

	if color:
	    color = OneColor( color )
	    if color: self.colorBB = color

	if lineWidth:
	    self.lineWidthBB = lineWidth


    def Draw(self):
        """ function that make the opengl call to draw the geom
Should be call by RedoDisplayList in between glNewList/ glEndList
"""
        #print "Geom.Draw", self.name
        pass


    def deleteOpenglTemplateList(self):
        #print "Common2d3dObject.deleteOpenglTemplateList", self
        if hasattr(self, 'makeTemplate') is True:
            if self.templateDSPL is not None:
                #viewer.currentCamera.tk.call(viewer.currentCamera._w, 'makecurrent')
                self.deleteTemplate()                


    def deleteOpenglList(self):
        #print "Geom.deleteOpenglList", self

        Common2d3dObject.deleteOpenglList(self)
        
        if self.outline.dpyList is not None:
            currentcontext = self.viewer.currentCamera.tk.call(self.viewer.currentCamera._w, 'getcurrentcontext')
            if currentcontext != self.outline.dpyList[1]:
                warnings.warn("""deleteOpenglList failed because the current context is the wrong one""")
                #print "currentcontext != self.outline.dpyList[1]", currentcontext, self.outline.dpyList[1]
            else:
                #print '-%d'%self.outline.dpyList[0], currentcontext, "glDeleteLists Geom"
                GL.glDeleteLists(self.outline.dpyList[0], 1)
                self.outline.dpyList = None


    def RedoDisplayList(self):
        #print "Geom.RedoDisplayList", self
##          if __debug__:
##              print 'Spheres RedoDisplayList for', self.fullName

        resetMaterialMemory()
        Common2d3dObject.RedoDisplayList(self)


    def AddClipPlane(self, cp, side=-1, clipChildren=True, tagModified=True):
	"""Add the arbitrary clipping plane 'cp' to this geometry"""

        self._modified = tagModified
        
	if not isinstance(cp, Clip.ClippingPlane):
	    msg = 'First agument has to be an instance of a ClippingPlane'
	    raise AttributeError(msg)

	if not self.viewer:
	    msg = 'clipping plane can only be added after the is in a viewer'
	    raise RuntimeError(msg)

	if side in (-1,1):
            self.clipSide[cp.num] = side
	else:
            raise AttributeError('side can only be 1 or -1')
        
	if clipChildren is True:
            self.clipPI.append( cp )
	elif clipChildren is False:
            self.clipP.append( cp )
	else:
            raise AttributeError('clipChildren can only be True or False')

        self.viewer.activeClippingPlanes = self.viewer.activeClippingPlanes + 1
        if not self.viewer.currentClip:
	    self.viewer.currentClip = cp


    def RemoveClipPlane(self, cp):
	"""Remove the clip. plane from the list of CP clipping this object"""

	if not isinstance(cp, Clip.ClippingPlane):
	    msg = 'First agument has to be an instance of ClippingPlane'
	    raise AttributeError(msg)

	if cp in self.clipPI:
            self.clipPI.remove(cp)
	elif cp in self.clipP:
            self.clipP.remove(cp)

        self.viewer.activeClippingPlanes = self.viewer.activeClippingPlanes - 1


    def ApplyParentsTransform(self, coords, instance=None):
        """Return a vector of 3D coordinates transformed by all
        transformations up to root (excluded)"""
        mat = self.GetMatrix( self.LastParentBeforeRoot(), instance )
	one = Numeric.ones( (coords.shape[0], 1), coords.dtype.char )
	c = Numeric.concatenate( (coords, one), 1 )
        return Numeric.dot(c, Numeric.transpose(mat))[:, :3]


    def TransformedCoords(self, root=None, instance=None):
	"""Return the vertices after applying the current transformation"""

        if root is None:
            root = self.viewer.rootObject
	if len(self.vertexSet):
	    m = self.GetMatrix(root, instance)
	    return self.vertexSet.vertices * m
	else:
	    return None
    

##     def GravityCenterSubtree(self):
## 	"""Compute the center of gravity of the object subtree"""

## 	allObj = self.AllObjects()
## 	center = Numeric.zeros( (3, ), viewerConst.FPRECISION)
## 	for o in allObj:
## 	    if not o.visible: continue
## 	    if len(o.vertexSet):
## 		m = o.GetMatrix(self)
## 		p = Numeric.concatenate( (o.vertices.GravityCenter(), [1.0]) )
## 		p = Numeric.dot(m, p)
## 		center = center + p[:3]
## 	return center/len(allObj)

        

    def ObjSubTreeBB(self, obj):

        GL.glPushMatrix()
        obj.MakeMat()

        for m in obj.instanceMatrices:
            GL.glPushMatrix()
            GL.glMultMatrixf(m)

            for child in obj.children:
                if child.visible and isinstance(child, Transformable):
                    self.ObjSubTreeBB(child)

            if len(obj.vertexSet):
                v = obj.vertexSet.vertices.array
                v = Numeric.reshape(v, (-1,3)).astype('f')
            else:
                if obj.maxBB is not None and obj.minBB is not None:
                    v = Numeric.array( [obj.maxBB, obj.minBB], 'f')
                else:
                    v = []

            if len(v):
                v = Numeric.reshape(v, (-1,3))
                ones = Numeric.ones( (len(v),1) ).astype('f')
                vhom = Numeric.concatenate( (v,ones), 1)

                mat = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
                mat = Numeric.reshape(mat,(4,4))
                # apply current matrix to coordinates and check against bb
                ct = Numeric.dot( vhom, mat )

                maxo = Numeric.maximum.reduce(ct)[:3]
                if self.__maxBB is None:
                    self.__maxBB = maxo
                else:
                    self.__maxBB = Numeric.maximum.reduce((self.__maxBB, maxo))

                mino = Numeric.minimum.reduce(ct)[:3]

                if self.__minBB is None:
                    self.__minBB = mino
                else:
                    self.__minBB = Numeric.minimum.reduce((self.__minBB, mino))

            GL.glPopMatrix()

	GL.glPopMatrix()     # Restore the matrix

               
    def ComputeBB(self):
        """This method computes the bounding box of the visible objects
        in the tree rooted at this object.
        This method handles properly instance matrices
        """
        # simulate a full redraw to build Xform matrices, apply to points
        # and find bounding box
        self.__minBB = None
        self.__maxBB = None
        GL.glPushMatrix()
        GL.glLoadIdentity()
        self.ObjSubTreeBB(self)
        GL.glPopMatrix()
        maxBB = self.__maxBB
        minBB = self.__minBB
        del self.__maxBB
        del self.__minBB
        if minBB is None:
            minBB = (-10, -10, -10)
        if maxBB is None:
            maxBB = (10, 10, 10)
        return Numeric.array(minBB), Numeric.array(maxBB)


    def _DrawBox(self, bbmin, bbmax):
	"""Draw the bounding box using lines"""

	GL.glPushAttrib(GL.GL_CURRENT_BIT | GL.GL_LIGHTING_BIT |
			GL.GL_LINE_BIT )
	GL.glShadeModel(GL.GL_FLAT)
	GL.glDisable(GL.GL_LIGHTING)
	GL.glColor4fv ( self.colorBB )
	GL.glLineWidth( self.lineWidthBB )
        #FIXME build a display list for a cube once
        # just scale the 3 dimensions and translate

        GL.glBegin(GL.GL_LINE_STRIP)
        GL.glVertex3f(float(bbmin[0]),float(bbmin[1]),float(bbmin[2]))
        GL.glVertex3f(float(bbmax[0]),float(bbmin[1]),float(bbmin[2]))
        GL.glVertex3f(float(bbmax[0]),float(bbmax[1]),float(bbmin[2]))
        GL.glVertex3f(float(bbmin[0]),float(bbmax[1]),float(bbmin[2]))
        GL.glVertex3f(float(bbmin[0]),float(bbmin[1]),float(bbmin[2]))
        GL.glEnd()
        
        GL.glBegin(GL.GL_LINE_STRIP)
        GL.glVertex3f(float(bbmin[0]),float(bbmin[1]),float(bbmax[2]))
        GL.glVertex3f(float(bbmax[0]),float(bbmin[1]),float(bbmax[2]))
        GL.glVertex3f(float(bbmax[0]),float(bbmax[1]),float(bbmax[2]))
        GL.glVertex3f(float(bbmin[0]),float(bbmax[1]),float(bbmax[2]))
        GL.glVertex3f(float(bbmin[0]),float(bbmin[1]),float(bbmax[2]))
        GL.glEnd()

        GL.glBegin(GL.GL_LINES)
        GL.glVertex3f(float(bbmin[0]),float(bbmin[1]),float(bbmin[2]))
        GL.glVertex3f(float(bbmin[0]),float(bbmin[1]),float(bbmax[2]))

        GL.glVertex3f(float(bbmin[0]),float(bbmax[1]),float(bbmin[2]))
        GL.glVertex3f(float(bbmin[0]),float(bbmax[1]),float(bbmax[2]))

        GL.glVertex3f(float(bbmax[0]),float(bbmax[1]),float(bbmin[2]))
        GL.glVertex3f(float(bbmax[0]),float(bbmax[1]),float(bbmax[2]))

        GL.glVertex3f(float(bbmax[0]),float(bbmin[1]),float(bbmin[2]))
        GL.glVertex3f(float(bbmax[0]),float(bbmin[1]),float(bbmax[2]))
        GL.glEnd()
	GL.glPopAttrib()


    def DrawTreeBoundingBox(self):
	"""Draw's the bounding box of this object and all of its visible
	   descendants"""

	#bbmin, bbmax = self.BoundingBoxSubtree()
        #print 'DrawTreeBoundingBox', bbmin, bbmax
        bbmin, bbmax = self.ComputeBB()
	self._DrawBox( bbmin, bbmax )


    def DrawBoundingBox(self):
	"""Draw's the objects bounding box"""

	self._DrawBox( self.vertexSet.vertices.bbmin, 
		       self.vertexSet.vertices.bbmax )
        

    def addVertexNormalsGeom(self):
        #print "addVertexNormalsGeom"
        if self is self.viewer.rootObject:
            return None
        if self.name.endswith('_vertexnormals'):
            return None
        for c in self.children:
            if c.name.endswith('_vertexnormals'):
                return None
        n = self.getVNormals()
        if len(n) == 0:
            return None
        v = self.getVertices()
        if len(n) == 0:
            return None
        pts = map(lambda x,y: (x, (x[0]+y[0],x[1]+y[1],x[2]+y[2])), v,n)
        from DejaVu.Polylines import Polylines
        g = Polylines(self.name+'_vertexnormals', vertices=pts)
        g.inheritedNormarrow = GL.GL_NONE
        self.viewer.AddObject(g, parent=self)
        self.vertexNormals = True
        return g

    def faceCenterVector(self, faceIndex):
        v0 = self.vertexSet.vertices.array[self.faceSet.faces.array[faceIndex][0]]
        v1 = self.vertexSet.vertices.array[self.faceSet.faces.array[faceIndex][1]]
        v2 = self.vertexSet.vertices.array[self.faceSet.faces.array[faceIndex][2]]
        center = ( (v0[0] + v1[0] + v2[0]) * 0.33333333333333333333333333 ,
                   (v0[1] + v1[1] + v2[1]) * 0.33333333333333333333333333 ,
                   (v0[2] + v1[2] + v2[2]) * 0.33333333333333333333333333 )
        normal = self.faceSet.normals.array[faceIndex]
        outsidePoint = (center[0]+normal[0],center[1]+normal[1],center[2]+normal[2])
        return center, outsidePoint

    def addFaceNormalsGeom(self):
        if not hasattr(self, 'faceSet'):
            return None
        if self is self.viewer.rootObject:
            return None
        if self.name.endswith('_facenormals'):
            return None
        for c in self.children:
            if c.name.endswith('_facenormals'):
                return None
        n = self.getFNormals()
        if len(n) == 0:
            return None
        f = self.getFaces()
        if len(n) == 0:
            return None
        v = self.getVertices()
        if len(n) == 0:
            return None
        
        pts = []
        for i in range(len(self.faceSet.faces.array)):
            pts.append(self.faceCenterVector(i))
        
        from DejaVu.Polylines import Polylines
        g = Polylines(self.name+'_facenormals', vertices=pts)
        g.inheritedNormarrow = GL.GL_NONE
        self.viewer.AddObject(g, parent=self)
        self.faceNormals = True
        return g


    def removeVertexNormalsGeom(self):
        if self is self.viewer.rootObject:
            return None
        if self.name.endswith('_vertexnormals'):
            return None
        for c in self.children:
            if c.name.endswith('_vertexnormals'):
                self.viewer.RemoveObject(c)
                self.vertexNormals = False


    def removeFaceNormalsGeom(self):
        if self is self.viewer.rootObject:
            return None
        if self.name.endswith('_facenormals'):
            return None
        for c in self.children:
            if c.name.endswith('_facenormals'):
                self.viewer.RemoveObject(c)
                self.faceNormals = False


    def RenderMode(self, mode=None, shading=None, face=GL.GL_FRONT, redo=1):
	"""Set the render mode"""
        warnings.warn('RenderMode is deprecated, use .Set(frontPolyMode=, shading=)',
                      DeprecationWarning, stacklevel=2)
        
        if not mode is None:
            if type(mode) == types.StringType:
                mode = viewerConst.POLYGON_MODES[mode]
	    if mode in viewerConst.POLYGON_MODES.values():
		if face==GL.GL_BACK:
		    self.backPolyMode = mode
		    self.inheritBackPolyMode = False
		else:
		    self.frontPolyMode = mode
		    self.inheritFrontPolyMode = False
	    elif mode==viewerConst.INHERIT:
		if face==GL.GL_BACK:
		    self.inheritBackPolyMode = True
		else:
		    self.inheritFrontPolyMode = True
	    else:
		raise AttributeError('Invalide polygon mode')
            
        if not shading is None:
            inhSet = False
            if shading == viewerConst.INHERIT:
                shading = GL.GL_NONE
        	self.inheritShading = True
        	inhSet = True
        
            if shading in viewerConst.SHADINGS:
        	if not inhSet:
        	    self.inheritShading = False
        	    self.shading = shading
            else:
        	raise AttributeError('Invalid shading model %d' % (shading,))
        
            if self.viewer:
                if (mode==GL.GL_FILL or shading != 'ignore'):
                    self.redoDspLst = 1
                if self.lighting:
                    self.GetNormals()
                if redo:
                    self.viewer.objectsNeedingRedo[self] = None
        
        
    def asIndexedPolygons(self, **kw):
        """Should return an IndexedPolygons object if this object can be
        represented using triangles, else return None"""
        return None


    def sortPoly(self, order=-1):
        """None <- sortPoly(order=-1)
        Sorts the geometry polygons according to z values of polygon's
        geomtric centers. Order=-1 sorts by furthest z first,, order=1 sorts
        by closest z first"""
        for g in self.children:
            if len(g.faceSet):
                g.sortPoly(order)


    def sortPoly_cb(self, event=None):
        self.sortPoly()


    def setViewer(self, viewer, buildDisplayList):
        """set viewer in all children of geom object
"""
        Common2d3dObject.setViewer(self, viewer, buildDisplayList)

        if hasattr(self, 'texture') and self.texture:
            self.texture.viewer = viewer
