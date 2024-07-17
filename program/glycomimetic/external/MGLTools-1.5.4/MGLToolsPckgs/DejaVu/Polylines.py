#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/Polylines.py,v 1.26 2007/07/31 00:40:05 vareille Exp $
#
# $Id: Polylines.py,v 1.26 2007/07/31 00:40:05 vareille Exp $
#

from opengltk.OpenGL import GL
from opengltk.extent import _gllib as gllib

from Geom import Geom
import datamodel, viewerConst, types
import numpy.oldnumeric as Numeric
from viewerFns import checkKeywords

class Polylines(Geom):
    """Class for sets of lines"""

    keywords = Geom.keywords + [
        'type',
        ]

    def __init__(self, name=None, check=1, **kw):

        if not kw.get('shape'):
            kw['shape'] = (0,0,3)    # default shape for line's vertex set

        if kw.has_key('type') is False:
            kw['type'] = None
        
        apply( Geom.__init__, (self, name, check), kw)


    def Set(self, check=1, redo=1, updateOwnGui=True, **kw):
        """set data for this object:
check=1 : verify that all the keywords present can be handle by this func 
redo=1 : append self to viewer.objectsNeedingRedo
updateOwnGui=True : allow to update owngui at the end this func
"""
        redrawFlag, \
        updateOwnGuiFlag, \
        redoViewerDisplayListFlag, \
        redoDisplayListFlag, \
        redoTemplateFlag, \
        redoDisplayChildrenListFlag = apply( Geom.Set, (self, check, 0), kw )

        if kw.has_key('type'):
            Polylines._PrimitveType(self, kw['type'])

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


    def MaterialBindingMode(self, propName, face=GL.GL_FRONT, mode=None):
	"""Figure out how materials should be used to color the object
        we overwrite the method from Geom because the number of parts
        corresponds to the nuber of lines which is
        vertexSet.vertices.array.shape[0]"""

        if propName is None: propName = 'ambi'
        if face is None: face = GL.GL_FRONT
	if type(propName) is types.StringType:
            num = getattr(self.materials[GL.GL_FRONT], propName)
        else:
            num = propName
        #num = self.materials[GL.GL_FRONT].GetPropNum(propName)
	f = face
	if face == GL.GL_FRONT_AND_BACK:
	    f = GL.GL_FRONT
	    self.frontAndBack = viewerConst.YES

	nn = self.materials[f].prop[num].shape[0]
	self.inheritMaterial = viewerConst.NO

	if not mode:
	    if nn == 1:
		self.materials[f].binding[num] = viewerConst.OVERALL
	    elif nn == len(self.vertexSet.vertices):
		self.materials[f].binding[num] = viewerConst.PER_VERTEX
            elif nn == self.vertexSet.vertices.array.shape[0]:
		self.materials[f].binding[num] = viewerConst.PER_PART
	    else:
		self.materials[f].binding[num] = -1
		self.inheritMaterial = viewerConst.YES

	else: # a mode is  requested

	    if mode==viewerConst.INHERIT:
		self.materials[f].binding[num] = viewerConst.INHERIT
	    if mode==viewerConst.PER_VERTEX and \
	       nn >= len(self.vertexSet.vertices):
		self.materials[f].binding[num] = viewerConst.PER_VERTEX
            elif nn == self.vertexSet.vertices.array.shape[0]:
		self.materials[f].binding[num] = viewerConst.PER_PART
	    elif mode==viewerConst.OVERALL and nn >= 1:
		self.materials[f].binding[num] = viewerConst.OVERALL
	    else:
		self.materials[f].binding[num] = -1
		self.inheritMaterial = viewerConst.YES


    def __repr__(self):
        return '<%s> %s with %d lines' % (self.__class__,
                          self.name, len(self.vertexSet) )


    def _PrimitveType(self, type=None):
	"""Find out out what type of lines"""

	assert type in viewerConst.PRIMITIVES+(None,)

	self.fixedLength = self.vertexSet.vertices.ashape[1]
	if self.fixedLength == 2 and (type is None or type==GL.GL_LINES):
	    self.primitiveType = GL.GL_LINES
	elif type:
	    if self.fixedLength > viewerConst.MINIMUM_LENGTH[type]:
		self.primitiveType = type
	    else:
		self.fixedLength = viewerConst.NO
		self.primitiveType = GL.GL_LINE_STRIP
	else: self.primitiveType = GL.GL_LINE_STRIP


    def Add(self, check=1, redo=1, **kw):
	"""Add lines"""

        if __debug__:
            if check:
                apply( checkKeywords, (self.name,self.keywords), kw)

        apply( Geom.Add, (self, 0, 0), kw)

	Polylines._PrimitveType(self, kw.get( 'type'))

        if self.viewer and redo:
            if self.redoDspLst:
                self.viewer.objectsNeedingRedo[self] = None
#                self.RedoDisplayList()


    def Draw(self):
        c = self.vertexSet.vertices.array
        if len(c)==0: return
        GL.glDisable(GL.GL_LIGHTING)

        binding = viewerConst.OVERALL
        if self.materials[GL.GL_FRONT]:
            mat = self.materials[GL.GL_FRONT]
            binding = self.materials[GL.GL_FRONT].binding[mat.diff]

        if binding == viewerConst.OVERALL:
            if self.materials[GL.GL_FRONT]:
                col = mat.prop[mat.diff][0]
            GL.glColor4fv(col)
            for i in xrange(c.shape[0]): #loop over lines
                GL.glPushName(i)
                GL.glBegin(self.primitiveType)
                for v in c[i]:
                    #GL.glVertex3dv(v.tolist())
                    #gllib.glVertex3dv(v)
                    gllib.glVertex3fv(v)
                GL.glEnd()
                GL.glPopName()

        elif binding == viewerConst.PER_VERTEX:
            if self.materials[GL.GL_FRONT]:
                col = mat.prop[mat.diff]
            vi = 0
            for i in xrange(c.shape[0]):
                GL.glPushName(i)
                GL.glBegin(self.primitiveType)
                for v in c[i]:
                    GL.glColor4fv(col[vi])
                    vi = vi + 1
                    #GL.glVertex3dv(v.tolist())
                    #gllib.glVertex3dv(v)
                    gllib.glVertex3fv(v)
                GL.glEnd()
                GL.glPopName()

        elif binding == viewerConst.PER_PART: # i.e. line
            if self.materials[GL.GL_FRONT]:
                col = mat.prop[mat.diff]
            for i in xrange(c.shape[0]):
                GL.glColor4fv(col[i])
                GL.glPushName(i)
                GL.glBegin(self.primitiveType)
                for v in c[i]:
                    #GL.glVertex3dv(v.tolist())
                    #gllib.glVertex3dv(v)
                    gllib.glVertex3fv(v)
                GL.glEnd()
                GL.glPopName()

        #glEnable(GL_LIGHTING)
        if self.viewer is not None:
            self.viewer.enableOpenglLighting()
        return True
