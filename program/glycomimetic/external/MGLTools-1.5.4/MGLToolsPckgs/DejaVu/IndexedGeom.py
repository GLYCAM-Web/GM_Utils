## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: 2000 Authors: Michel F. SANNER, Daniel Stoffler, Guillaume Vareille
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel F. SANNER, Daniel Stoffler, Guillaume Vareille and TSRI
#
#########################################################################
#
# $Header$
#
# $Id$
#


import numpy.oldnumeric as Numeric
import warnings

from opengltk.OpenGL import GL
from opengltk.extent.utillib import glDrawIndexedGeom
from geomutils.geomalgorithms import  TriangleNormals
from DejaVu.datamodel import FaceSet
from DejaVu.viewerFns import checkKeywords
from DejaVu import viewerConst
from DejaVu.Geom import Geom


class IndexedGeom(Geom):
    """Geometry specified by a VertexSet and a FaceSet
"""

    keywords = Geom.keywords + [
        'type',
        'faces',
        'fnormals',
        'freshape',
        ]

    def __init__(self, name=None, check=1, **kw):

        #self.outlList = GL.glGenLists(1)

        if not kw.get('shape'):
            kw['shape'] = (0,3)    # default shape for sphere set

        self.faceSet = FaceSet( shape= (0,0) )
        apply( Geom.__init__, (self, name, check), kw)

        self._modified = False
        

    def getFaces(self):
        """returns a handle to the faces array"""
        return self.faceSet.faces.array


    def getFNormals(self):
        """returns a handle to the face normals"""
        if self.faceSet.normals.status == viewerConst.NONE:
            self.faceSet.normals.GetProperty()

        return self.faceSet.normals.array

        
    def removeFacesWithoutHighlightedVertices(self):
        if self.highlight:
            lFacesWithHighlightedVertices = []
            for face in self.faceSet.faces.array:
               for lVertexIndex in face:
                   if self.highlight[lVertexIndex]:
                       lFacesWithHighlightedVertices.append(face)
                       break
            self.Set(faces=lFacesWithHighlightedVertices)


    def _FixedLengthFaces(self):
	"""sets self.fixedLength to the number of vertices perface if all faces
        have the same number of vertices, else self.fixedLength=0.
        Check if there are negative indices finishing faces lists"""

	ind = self.faceSet.faces.array
	min = Numeric.minimum.reduce( Numeric.minimum.reduce (ind) )
	if min > -1 and ind.shape[1] < 5: self.fixedLength = ind.shape[1]
	else: self.fixedLength = False


    def _PrimitiveType(self, type=None):
	"""Set the geometric primitives type for indexed geometries
        Type can be: None, GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP
                           GL_TRIANGLES, GL_QUADS, GL_POLYGON, GL_TRIANGLE_FAN
"""
        #print "IndexedGeom._PrimitiveType", self, type
        #
        # - GL_POINTS, GL_TRIANGLE_STRIP and GL_QUAD_STRIP are not
        #   considred because they are not indexed geometries
        #
        # - GL_LINES, GL_TRIANGLES, GL_QUADS, are NOT pickable but fast
        #
        # - GL_LINE_STRIP, GL_LINE_LOOPS, GL_POLYGON, GL_TRIANGLE_FAN
        #   return per primitive picking info
        #
	assert type in viewerConst.PRIMITIVES+(None,)
        if len(self.faceSet)==0: return
	self._FixedLengthFaces()
	old = self.primitiveType

        # no type has been given
        # so use the most efficient primitive
        if type is None:
            if not self.pickableVertices:
                if self.fixedLength==2:
                    self.primitiveType = GL.GL_LINES
                elif self.fixedLength==3:
                    self.primitiveType = GL.GL_TRIANGLES
                elif self.fixedLength==4:
                    self.primitiveType = GL.GL_QUADS
                else:
                    self.primitiveType = GL.GL_POLYGON
                    self.pickableVertices = True # it will pickable
            else:
                if self.fixedLength==2:
                    # MS DEC 02: we make it a line strip so the display list
                    # build by the *DSPL function will let pick parts
                    self.primitiveType = GL.GL_LINE_STRIP
                elif self.fixedLength==3:
                    self.primitiveType = GL.GL_TRIANGLES
                elif self.fixedLength==4:
                    self.primitiveType = GL.GL_QUADS
                else:
                    self.primitiveType = GL.GL_POLYGON
                
        else: # type has been provided
            if type == GL.GL_LINES:
                if self.fixedLength==2: 
                    self.primitiveType = GL.GL_LINES
                    self.pickableVertices = False
                else:
                    raise AttributeError('Bad faces for GL.GL_LINES')

            elif type == GL.GL_TRIANGLES:
                if self.fixedLength==3: 
                    self.primitiveType = GL.GL_TRIANGLES
                    self.pickableVertices = False
                else:
                    raise AttributeError('Bad faces for GL.GL_TRIANGLES')

            elif type == GL.GL_QUADS:
                if self.fixedLength==4:
                    self.primitiveType = GL.GL_QUADS
                    self.pickableVertices = False
                else: raise AttributeError('Bad faces for GL.GL_QUADS')

            elif type == GL.GL_TRIANGLE_FAN:
                self.primitiveType = GL.GL_QUADS
                self.pickableVertices = True

            else:
                self.primitiveType = type
                self.pickableVertices = True

        if old != self.primitiveType:
            self.redoDspLst = 1


    def Add(self, check=1, redo=1, **kw):
	"""add faces (polygon or lines) to this object
"""
        #print "IndexedGeom.Add"

        if __debug__:
            if check:
                apply( checkKeywords, (self.name,self.keywords), kw)
            
        t = kw.get( 'type')
	f = kw.get( 'faces')
	fn = kw.get( 'fnormals')
	if f:
            self.redoDspLst = 1
	    self.faceSet.faces.AddValues( f )

	if fn:
            self.redoDspLst = 1
            self.faceSet.faces.AddValues(fn)

        Geom.Add(self, check=0, redo=0,
		 vertices = kw.get( 'vertices'),
		 vnormals = kw.get( 'vnormals'),
		 materials = kw.get( 'materials'),
		 polyFace = kw.get( 'polyFace'),
		 matBind = kw.get( 'matBind'),
		 propName = kw.get( 'propName') )

	if f:
            pf = kw.get( 'polyFace')
            pn = kw.get( 'propName')
            mbm = kw.get( 'matBind')
            self._PrimitiveType(t)
            self.MaterialBindingMode(pn, face=pf, mode=mbm)
            
        if f or fn:
            if self.shading==GL.GL_FLAT:
                self.GetNormals()

        if self.viewer and redo:
            if self.redoDspLst:
                self.viewer.objectsNeedingRedo[self] = None
#                self.RedoDisplayList()


    def Set(self, check=1, redo=1, updateOwnGui=True, **kw):
        """set data for this object: add faces (polygon or lines) to this object
check=1 : verify that all the keywords present can be handle by this func 
redo=1 : append self to viewer.objectsNeedingRedo
updateOwnGui=True : allow to update owngui at the end this func
"""
        #print "IndexedPolygons.Set"

        #import pdb; pdb.set_trace()

        redoDisplayListFlag0 = False

        # Exceptionnaly this has to be before the call to Geom.Set
        # because we want to override the treatment of it by Geom.Set
        invertNormals = kw.get('invertNormals')
        if invertNormals is not None:
            kw.pop('invertNormals')
            if self.invertNormals != invertNormals:
                self.invertNormals = invertNormals
                redoDisplayListFlag0 = True

        redrawFlag, \
        updateOwnGuiFlag, \
        redoViewerDisplayListFlag, \
        redoDisplayListFlag, \
        redoTemplateFlag, \
        redoDisplayChildrenListFlag = apply( Geom.Set, (self, check, 0), kw)
        
        redoDisplayListFlag = redoDisplayListFlag or redoDisplayListFlag0
            
        if kw.has_key('faces'):
            self.faceSet.faces.SetValues( [] )

        t = kw.get( 'type')
        f = kw.get( 'faces')
        reshape = kw.get( 'freshape')
        fn = kw.get( 'fnormals')

        if not f is None:
            try:
                len(f)
            except TypeError:
                raise TypeError ("faces should be sequences of integers")

            if len(f)==1 and len(f[0])==0:  # handle [[]]
                f = []

            ind = Numeric.array(f)
            if len(ind.ravel()) > 0:
                m = Numeric.minimum.reduce(ind)
                if m.size > 1:
                    m = min(m)
                m = max(0, m)
                if ( m < 0 ):
                    raise ValueError ("vertex index %d out of range" % m)

                m = Numeric.maximum.reduce(ind)
                if m.size > 1:
                    m = max(m)
                if ( m >= len(self.vertexSet) ):
                    raise ValueError ("vertex index %d out of range, max %d" %
                                      (m, len(self.vertexSet)-1) )

            redoDisplayListFlag = True
	    self.faceSet.faces.SetValues( f, reshape)
	    assert len(self.faceSet.faces.ashape)==2

        if not fn is None:
            redoDisplayListFlag = True
            self.faceSet.normals.SetValues(fn)

        if not f is None or t or kw.get( 'pickableVertices'):
            pf = kw.get( 'polyFace')
            pn = kw.get( 'propName')
            mbm = kw.get( 'matBind')
            self._PrimitiveType(t)
            self.MaterialBindingMode(pn, face=pf, mode=mbm)

        if f is not None or fn is not None:
            if self.shading==GL.GL_FLAT:
                redoDisplayListFlag = True
                self.faceSet.normals.PropertyStatus(len(self.faceSet))
                if self.lighting:
                    self.GetNormals()

        if self.faceSet.normals.status < 24:
            if self.lighting:
                self.GetNormals()

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



    def ComputeVertexNormals(self):
	"""Compute the vertex normals"""
	v = self.vertexSet.vertices.array
        f = self.faceSet.faces.array
	if len(v) > 2 and len(f) > 1:
            return TriangleNormals( v, f[:,:3], 'PER_VERTEX')
	else: return None


    def ComputeFaceNormals(self):
	"""Compute the face normals"""

	v = self.vertexSet.vertices.array
	f = self.faceSet.faces.array
	if len(v) > 2 and len(f) > 0:
            return TriangleNormals( v, f[:,:3], 'PER_FACE')
	else: return None


    def VertexNormalFunction(self, func=None, args=()):
	"""Set the function used to compute vertices normals"""
	if func is None: return self.vertexSet.normals.Compute
	assert callable(func)
	self.vertexSet.normals.ComputeFunction( func, args )


    def FaceNormalFunction(self, func=None, args=()):
	"""Set the function used to compute faces normal"""

	if func is None: return self.faceSet.normals.Compute
	assert callable(func)
	self.faceSet.normals.ComputeFunction( func, args )

            
    def DisplayFunction(self):
	"""display a set of indexed geometric primitives"""
        
        if self.dpyList:

#            print "DisplayFunction", self.dpyList, self.fullName

                #was self.drawOutline \
            if self.getDrawOutlineMode() and self.viewer.hasOffsetExt:

                outl = self.outline

                if   self.frontPolyMode == GL.GL_FILL \
                  or self.backPolyMode == GL.GL_FILL:

                    mode = GL.GL_POLYGON_OFFSET_FILL

                    GL.glEnable(mode)
                    self.viewer.polyOffset( outl.factor, outl.unit)
                    Geom.DisplayFunction(self)
                    GL.glDisable(mode)

                    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
                    if not outl.colorAsMaterial:
                        if outl.lighting:
                            GL.glMaterialfv( GL.GL_FRONT_AND_BACK,
                                             GL.GL_EMISSION,
                                             outl.color )
                        else:
                            GL.glDisable(GL.GL_LIGHTING)
                            GL.glColor4fv (outl.color)

                    GL.glLineWidth(outl.lineWidth)
                    if outl.dpyList:
                        currentcontext = self.viewer.currentCamera.tk.call(self.viewer.currentCamera._w, 'getcurrentcontext')
                        if currentcontext != outl.dpyList[1]:
                            warnings.warn("""DisplayFunction failed because the current context is the wrong one""")
                            #print "currentcontext != outl.dpyList[1]", currentcontext, outl.dpyList[1]
                        else:
                            #print '#%d'%outl.dpyList[0], currentcontext, "glCallList IndexedGeom"
                            GL.glCallList(outl.dpyList[0])
                else:
                    Geom.DisplayFunction(self)
            else:
                Geom.DisplayFunction(self)


    def Draw(self):
        """ draw geom
"""
        #print "IndexedGeom.Draw", self.name

        if len(self.faceSet) and len(self.vertexSet):
            if self.materials[GL.GL_FRONT] and \
                   not self.inheritMaterial:
                mat = self.materials[GL.GL_FRONT]
                fpProp = []
                fpBind = []
                for propInd in range(4):
                    b, p = mat.GetProperty(propInd)
                    fpProp.append(p)
                    fpBind.append(b)
                fpProp.append(mat.prop[4])
                fpBind.append(mat.binding[4])
            else:
                fpProp = None
                fpBind = None

            if self.materials[GL.GL_BACK] and \
               not self.inheritMaterial:
                mat = self.materials[GL.GL_BACK]
                bpProp = []
                bpBind = []
                for propInd in range(4):
                    b, p = mat.GetProperty(propInd)
                    bpProp.append(p)
                    bpBind.append(b)
                bpProp.append(mat.prop[4])
                bpBind.append(mat.binding[4])

            else:
                bpProp = None
                bpBind = None

            texCoords = None
            if hasattr(self.vertexSet, "texCoords"):
                if self.vertexSet.texCoords.status >= viewerConst.COMPUTED:
                    texCoords = self.vertexSet.texCoords.array

            if self.lighting:
                if (self.invertNormals) and (self.normals is not None):
                    norms = - self.normals
                else:
                    norms = self.normals
            else:
                norms = None

            from DejaVu import preventIntelBug_BlackTriangles
            if preventIntelBug_BlackTriangles:
                preventIntelBug = 1
            else:
                preventIntelBug = 0

            lsharpColorBoundaries = self.getSharpColorBoundaries()

            if self.disableStencil is True:
                GL.glDisable(GL.GL_STENCIL_TEST)

            status = glDrawIndexedGeom(
                self.primitiveType,
                self.vertexSet.vertices.array,
                self.faceSet.faces.array,
                norms,
                texCoords,
                fpProp, bpProp, fpBind, bpBind,
                self.frontAndBack, 1,
                lsharpColorBoundaries,
                preventIntelBug,
                highlight=self.highlight,
                )

            if self.disableStencil is True:
                GL.glEnable(GL.GL_STENCIL_TEST)

            return status


    def RedoDisplayList(self):
            #print "IndexedGeom.RedoDisplayList", self.name
##          if __debug__:
##              print 'IndexedGeom RedoDisplayList for', self.fullName

        Geom.RedoDisplayList(self)

        if len(self.faceSet) and len(self.vertexSet):

            # we always build this, that way we don't have to built on demand
            outl = self.outline
            if outl.colorAsMaterial:
                if self.materials[GL.GL_FRONT] and \
                       not self.inheritMaterial:
                    mat = self.materials[GL.GL_FRONT]
                    fpProp = []
                    fpBind = []
                    for propInd in range(4):
                        b, p = mat.GetProperty(propInd)
                        fpProp.append(p)
                        fpBind.append(b)
                    fpProp.append(mat.prop[4])
                    fpBind.append(mat.binding[4])
                else:
                    fpProp = None
                    fpBind = None

                if self.materials[GL.GL_BACK] and \
                   not self.inheritMaterial:
                    mat = self.materials[GL.GL_BACK]
                    bpProp = []
                    bpBind = []
                    for propInd in range(4):
                        b, p = mat.GetProperty(propInd)
                        bpProp.append(p)
                        bpBind.append(b)
                    bpProp.append(mat.prop[4])
                    bpBind.append(mat.binding[4])

                else:
                    bpProp = None
                    bpBind = None
            else:
                fpProp = bpProp = fpBind = bpBind = None

            texCoords = None

            if outl.lighting:
                norms = self.normals
            else:
                norms = None

            # WARNING: if texture, fpProp, bpProp, fpBind, bpBind,
            # are not passed (either None or arrays) we get a segmentation
            # fault if the surface has many colors (i.e. color MSMS by atom
            # type and dispaly outline seg faults)

            # calling with too many arguments segaults too
            # just add  None, None, None, None, after the line with colors

            lNewList = GL.glGenLists(1)
            #lNewList = self.outlList
            #print "lNewList IndexedGeom.RedoDisplayList", lNewList, self.name
            lCurrentContext = self.viewer.currentCamera.tk.call(self.viewer.currentCamera._w, 'getcurrentcontext')
            outl.dpyList = ( lNewList, lCurrentContext)
                             
            GL.glNewList(outl.dpyList[0], GL.GL_COMPILE)
            #print '+%d'%outl.dpyList[0], lCurrentContext, "glNewList IndexedGeom"
            status=glDrawIndexedGeom(
                GL.GL_LINE_LOOP,
                self.vertexSet.vertices.array,
                self.faceSet.faces.array,
                norms,
                texCoords,
                fpProp, bpProp, fpBind, bpBind,
                self.frontAndBack,
                1)  # 1 means use diffuse component if no lighting
            #print '*%d'%GL.glGetIntegerv(GL.GL_LIST_INDEX), "glEndList IndexedGeom"
            GL.glEndList()
            if not status:
                #print '-%d'%outl.dpyList[0], "glDeleteLists IndexedGeom"
                GL.glDeleteLists(outl.dpyList[0], 1)
                outl.dpyList = None


    def setTransparency(self, val):
        #print "setTransparency", val
        Geom.setTransparency(self, val)
        if self.viewer:
            if self.transparent in (1, True):
                for c in self.viewer.cameras:
                    c.addButtonUpCB(self.sortPoly_cb)
            else:
                for c in self.viewer.cameras:
                    if self.sortPoly_cb in c.onButtonUpCBlist:
                        c.delButtonUpCB(self.sortPoly_cb)


    def removeDuplicatedVertices(self):
        """find duplicated vertices and remove them, re-index face list"""
        # hash vertices
        d = {}
        for vert in self.vertexSet.vertices.array:
            d['%f,%f,%f'%tuple(vert)] = []

        # build list of unique vertices and lookup table
        lookup = {}
        nv = []
        nn = []
        i = 0
        for k in d.keys():
            nv.append(eval(k))
            lookup[k] = i
            i = i + 1

        # new facelist
        v = self.vertexSet.vertices.array
        nflist = []
        for face in self.faceSet.faces.array:
            nf = []
            for vind in face:
                nf.append(lookup['%f,%f,%f'%tuple(v[vind])])
            nflist.append(nf)

        return nv, nflist


#    def modifiedFacesAndVerticesForSharpColorBoundaries(self):
##        self.vertexSet.vertices.array,
##        self.faceSet.faces.array,
##        self.normals,
##        fpProp, bpProp, fpBind, bpBind,
##        self.frontAndBack,
#
#        if not \
#           (    ( self.faceSet.faces.array.shape[1] == 3 ) \
#            and ( fpBind ) \
#            and (   ( fpBind [ 0 ] == PER_VERTEX ) \
#                 or ( fpBind [ 1 ] == PER_VERTEX ) \
#                 or ( fpBind [ 2 ] == PER_VERTEX ) \
#                 or ( fpBind [ 3 ] == PER_VERTEX ) \
#                 or ( fpBind [ 4 ] == PER_VERTEX ) \
#                 or (    ( not self.frontAndBack )
#                     and ( backMatBind ) 
#                     and (   ( backMatBind [ 0 ] == PER_VERTEX )
#                          or ( backMatBind [ 1 ] == PER_VERTEX )
#                          or ( backMatBind [ 2 ] == PER_VERTEX )
#                          or ( backMatBind [ 3 ] == PER_VERTEX )
#                          or ( backMatBind [ 4 ] == PER_VERTEX ) 
#                         )
#                    )
#                )
#           ):
#            return
#
#        if self.normals:
#  {
#                if (lennorm[0] == lencoord) 
#                        normBinding = PER_VERTEX;
#    else if (lennorm[0] == lenind[0]) 
#                        normBinding = PER_PART;
#    else if (lennorm[0] == 1) 
#            normBinding = OVERALL;
#    else normBinding = NONE;
#  }
#  else normBinding = NONE;
#
#

