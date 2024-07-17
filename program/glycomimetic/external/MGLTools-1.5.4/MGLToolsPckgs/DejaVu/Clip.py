## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/Clip.py,v 1.36.6.1 2009/06/11 23:00:24 vareille Exp $
#
# $Id: Clip.py,v 1.36.6.1 2009/06/11 23:00:24 vareille Exp $
#

from opengltk.OpenGL import GL
from opengltk.extent.utillib import glCleanRotMat

import numpy.oldnumeric as Numeric
from viewerFns import getkw
from math import sqrt
from Transformable import Transformable
from colorTool import OneColor, glMaterialWithCheck, resetMaterialMemory

class ClippingPlane(Transformable):

    clipPlaneNames = [ GL.GL_CLIP_PLANE0, GL.GL_CLIP_PLANE1,
		       GL.GL_CLIP_PLANE2, GL.GL_CLIP_PLANE3,
		       GL.GL_CLIP_PLANE4, GL.GL_CLIP_PLANE5 ]


    def __init__(self, object, num, viewer):
	"""Create a arbitrary clipping plane.  self.translation represents the
        point in the plane's parent's space about which the plane will
        rotate.  self.eqn is a vector of the  4 coefficients for the equation
        of a plane."""

        self.name = 'ClipPlane'+str(num)
        Transformable.__init__(self, viewer)
	self.num = num
	self.id = self.clipPlaneNames[num]
	self.object = object
        self.Reset()


    def Reset(self):
        # FIXME since clipping planes are added to objectsas they are created
        # this seems superfluous
        # the consequence is that one cannot disable a clipping plane without
        # loosing it! so we should have an add clipping plane button which
        # is separated from enabling the clipping plane
        self.hasBeenCurrent = False

	self.color = [1.,1.,1.,1.]
	self.lineWidth = 2
	#self.antiAliased = 0
	self.visible = False
        self.enabled = False
        #self.antialiased = False
	self.eqn = Numeric.array( [1.0, 0.0, 0.0, 0.0], Numeric.Float )
        # this is coefficient vector of the equation of a plane Ax+By+Cz+D = 0
	self.n = 1.0
	self.FrameTransform()
	self.polyMode = GL.GL_LINE_STRIP
        self._modified = False
        

    def ResetTransformation(self, redo=1):
	"""Reset the clipping plane's transformation"""

	Transformable.ResetTransformation(self)
	self.eqn = Numeric.array( [1.0, 0.0, 0.0, 0.0] )
	self.n = 1.0


    def __repr__(self):
	return '<ClippingPlane %s, eqn=%s>' % (self.name,str(self.eqn) )


    def FrameTransform(self, camera=None):
	"""Build the R an RI, the object's frame transformation and inverse"""

	GL.glPushMatrix()
	self.Si = Numeric.ones( (3, ) )
	GL.glLoadIdentity()
	m = Numeric.reshape( self.object.rotation, (4,4) )
	upd = Numeric.reshape( Numeric.transpose(m), (16, ) )
	GL.glMultMatrixf(self.object.Ri)
	GL.glMultMatrixf(upd)
        GL.glMultMatrixf(self.object.MatrixRotInv)
        self.Si = self.Si * self.object.Si / (self.object.scale *
                                              self.object.MatrixScale)

	self.Ri = Numeric.array(GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)).astype('f')
	GL.glPopMatrix()
	#self.Ri = Numeric.reshape(glCleanRotMat(self.Ri), (4,4) )
        self.Ri = glCleanRotMat(self.Ri)
	self.R = Numeric.reshape( Numeric.transpose(self.Ri), (16, ) ).astype('f')
	self.Ri = Numeric.reshape(self.Ri, (16, )).astype('f')

	if self.redirectXform: self.redirectXform.FrameTransform(camera)
	for o in self.copyXform: o.FrameTransform(camera)


    def _NormalizeN(self):
	eqn = Numeric.zeros( (3,), Numeric.Float )
	for i in (0,1,2):
	    eqn[i] = self.rotation[i]
	n = Numeric.add.reduce(eqn*eqn)
	assert n > 0.0
	if n > 0.00001:
	    self.n = 1.0 / sqrt( n )
	    self.eqn[:3] = eqn
	else: 
	    self.n = 1.0
	    self.eqn[:3] = [1.0, 0.0, 0.0]


    def ConcatRotation(self, matrix):
	"""Overwrite rotation methods"""

        self._modified = True
	Transformable.ConcatRotation(self, matrix)
	self.rotation.shape = (4,4)
        eqn = Numeric.array(self.rotation[0,:3]) # because direction is (1.,0.,0.)
        #print '================================================='
        #print 'eqn', eqn
        self.n = 1.0 / sqrt( Numeric.add.reduce(eqn*eqn) )
        self.eqn[:3] = eqn
        #print 'self.eqn',self.eqn
        self.eqn[3] = -Numeric.dot(self.eqn[:3], self.translation)
        #print self.eqn

        #get the value so that the plane is equivalent to having the proper
        #normal vector and a translation from the origin along the vector
	for o in self.copyXform: o._NormalizeN()
	self.rotation.shape = (16, )
        self.viewer.deleteOpenglList()


    def ConcatTranslation(self, trans):
	"""Overwrite translation methods
"""
        self._modified = True
        self.translation = self.translation + trans
        self.eqn[3] = -Numeric.dot(self.eqn[:3], self.translation)

        for o in self.copyXform:
            o.ConcatTranslation(trans)
        self.viewer.deleteOpenglList()


    def _Enable(self, side):
	"""Activate the clipping plane"""

	eqnt = self.eqn * side
        #eqnt[3] = 0.0 - eqnt[3]
	GL.glClipPlane(self.clipPlaneNames[self.num], eqnt)
	GL.glEnable(self.clipPlaneNames[self.num])


    def _Disable(self):
	"""Deactivate the clipping plane"""
	GL.glDisable(self.clipPlaneNames[self.num])


    def Set(self, **kw):
	"""Set various clipping plane parameters"""

	self.hasBeenCurrent = True # remember the light has been changed

        tagModified = True
        val = getkw(kw, 'tagModified')
        if val is not None:
            tagModified = val
        assert tagModified in [True, False]
        self._modified = tagModified

	val = getkw(kw, 'enabled')
	if not val is None:
	    if val is True:
                self._Enable(1)
	    elif val is False:
                self._Disable()
	    else: raise AttributeError('enable can only be True or False')
            self.enabled = val

	val = getkw(kw, 'name')
	if not val is None: self.name = val

	val = getkw(kw, 'visible')
	if not val is None:
	    if val in [False,True]:
                self.visible = val
	    else:
                raise AttributeError('visible can only be 0 or 1')

	val = getkw(kw, 'color')
	if not val is None:
	    col = OneColor( val )
	    if col:
		self.color = col

	val = getkw(kw, 'lineWidth')
	if not val is None:
	    try:
	        int(val)
	    except:
	        raise ValueError ('lineWidth must be a positive int')
	    if val>=1:
	        self.lineWidth = int(val)
	    else:
	        raise ValueError ('lineWidth must be a positive int')
            

#	val = getkw(kw, 'antialiased')
#	if not val is None:
#	    if val in (True, False) :
#		self.antialiased = val
#	    else: raise ValueError ('antialiased can only be YES or NO')

	val = getkw(kw, 'rotation')
	if not val is None:
            self.rotation = Numeric.identity(4, 'f').ravel()
            mat = Numeric.reshape(Numeric.array(val), (16,)).astype('f')
            self.ConcatRotation(mat)

	val = getkw(kw, 'translation')
	if not val is None:
            self.translation = Numeric.zeros( (3,), 'f')
            mat = Numeric.reshape(Numeric.array(val), (3,)).astype('f')
            self.ConcatTranslation(mat)

	val = getkw(kw, 'scale')
	if not val is None:
            self.SetScale( val )

	val = getkw(kw, 'pivot')
	if not val is None:
            self.SetPivot( val )

	if len(kw):
	    print 'WARNING1: Keyword(s) %s not used' % kw.keys()

        if self.object.viewer:
            self.object.viewer.objectsNeedingRedo[self.object] = None
            self.object.viewer.Redraw()


    def setColor(self, val):
        self.Set(color=val)


    def getState(self):
        """return a dictionary describing this object's state
This dictionary can be passed to the Set method to restore the object's state
"""
        return {'enabled':self.enabled,
                'name':self.name,
                'visible':self.visible,
                'color':self.color,
                'lineWidth':self.lineWidth,
                #'antialiased':self.antialiased,
                'rotation':list(self.rotation),
                'translation':list(self.translation),
                'scale':list(self.scale),
                'pivot':list(self.pivot)
                }


    def DisplayFunction(self):
        """Draw a square with diagonals to represent the clipping plane
"""
        #print "ClippingPlane.DisplayFunction"
	#trans = self.eqn[3]*(self.eqn[:3]*self.n)
        resetMaterialMemory()
        trans = self.translation
	GL.glPushMatrix()
	#GL.glTranslatef(-trans[0],-trans[1],-trans[2])
        GL.glTranslatef(float(trans[0]),
                        float(trans[1]),
                        float(trans[2]))
	GL.glMultMatrixf(self.rotation)
	GL.glScalef(float(self.scale[0]),
                    float(self.scale[1]),
                    float(self.scale[2]))

	if self.polyMode == GL.GL_QUADS:

	    GL.glPushAttrib(GL.GL_CURRENT_BIT | GL.GL_LIGHTING_BIT |
			    GL.GL_POLYGON_BIT)
            GL.glDisable(GL.GL_LIGHTING)

	    GL.glMaterialWithCheck(GL.GL_FRONT_AND_BACK, GL.GL_AMBIENT,
                                self.color)
            if self.viewer is not None:
                self.viewer.enableOpenglLighting()
	    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

	    GL.glBegin (GL.GL_QUADS)
	    GL.glVertex3f (0.0, -5.0, -5.0)
	    GL.glVertex3f (0.0, -5.0,  5.0)
	    GL.glVertex3f (0.0,  5.0,  5.0)
	    GL.glVertex3f (0.0,  5.0, -5.0)
	    GL.glVertex3f (0.0, -5.0, -5.0)
	    GL.glEnd ()

	    GL.glPopAttrib()

	else:
# MS disabling GL.GL_BLEND breaks display of transparent surfaces
##  	    if self.antialiased==True:
##  		GL.glEnable(GL.GL_LINE_SMOOTH)
##  		GL.glEnable(GL.GL_BLEND)
##  	    else:
##  		GL.glDisable(GL.GL_LINE_SMOOTH)
##  		GL.glDisable(GL.GL_BLEND)

	    GL.glColor4fv (self.color)
	    GL.glLineWidth(self.lineWidth)
	
	    # could and should be a display list made once for all planes
	    GL.glBegin (GL.GL_LINE_STRIP)
	    GL.glVertex3f (0.0, -5.0, -5.0)
	    GL.glVertex3f (0.0, -5.0,  5.0)
	    GL.glVertex3f (0.0,  5.0,  5.0)
	    GL.glVertex3f (0.0,  5.0, -5.0)
	    GL.glVertex3f (0.0, -5.0, -5.0)
	    GL.glVertex3f (0.0,  5.0,  5.0)
	    GL.glVertex3f (0.0, -5.0,  5.0)
	    GL.glVertex3f (0.0,  5.0, -5.0)
	    GL.glEnd ()

	GL.glPopMatrix()

