## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################


# $Header: /opt/cvs/python/packages/share1.5/DejaVu/IndexedPolygons.py,v 1.41.2.1 2008/11/19 21:20:36 vareille Exp $
#
# $Id: IndexedPolygons.py,v 1.41.2.1 2008/11/19 21:20:36 vareille Exp $
#

import os
import numpy.oldnumeric as Numeric

from opengltk.OpenGL import GL
from IndexedPolylines import IndexedPolylines
from DejaVu.Geom import Geom
from DejaVu.IndexedGeom import IndexedGeom
import datamodel, viewerConst
from viewerFns import checkKeywords


def IndexedPolygonsFromFile(filename, name=None):
    """IndexedPolygons <- indexedPolygonsFromFile(name, filename)
Create an IndexedPolygons object from a file saved using the
geom.saveIndexedPolygons method. 
The extension of filename (if any) will be remove.
filename.vert and filename.face should be present.
The name arguemnt will be the name of the Geom object. If omitted, filename
will be used.
"""
    filename = os.path.splitext(filename)[0]

    from string import split
    f = open(filename+'.indpolvert')
    data = map(split, f.readlines())
    f.close()
    verts = map( lambda x: (float(x[0]), float(x[1]), float(x[2])), data )
    norms = map( lambda x: (float(x[3]), float(x[4]), float(x[5])), data )

    f = open(filename+'.indpolface')
    data = map(split, f.readlines())
    f.close()
    faces = []
    fnorms = []
    for line in data:
        faces.append( map( int, line[:-3]) )
        fnorms.append( map( float, line[-3:]) )
    if name is None:
        name = filename

    import numpy.oldnumeric as Numeric
    faces = Numeric.array(faces)
    if min(faces.ravel())==1:
        faces = faces - 1
        
    pol = IndexedPolygons(name, vertices=verts, vnormals=norms, faces=faces)
    # FIXME face normals have to be set after the constructor else they are
    # overwritten with computed ones
    pol.Set(fnormals=fnorms, shading=GL.GL_FLAT)
    return pol


class IndexedPolygons(IndexedPolylines):
    """Set of polygons sharing vertices
"""

    def __init__(self, name=None, check=1, redo=1, replace=True, **kw):
        #print "IndexedPolygons.__init__", name

        kw['replace'] = replace

        apply( IndexedPolylines.__init__, (self, name, check), kw)


    def Set(self, check=1, redo=1, updateOwnGui=True, **kw):
        """set data for this object: Set polygon's vertices, faces, normals or materials
check=1 : verify that all the keywords present can be handle by this func 
redo=1 : append self to viewer.objectsNeedingRedo
updateOwnGui=True : allow to update owngui at the end this func
"""
        redrawFlag, \
        updateOwnGuiFlag, \
        redoViewerDisplayListFlag, \
        redoDisplayListFlag, \
        redoTemplateFlag, \
        redoDisplayChildrenListFlag = apply( IndexedPolylines.Set, (self, check, 0), kw )

        if    hasattr(self, 'faceSet') \
          and len(self.faceSet.faces.array) > 0 \
          and len(self.faceSet.faces.array[0]) > 2 :
            self._PrimitiveType()

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



    def delete(self):
        self.vertexSet.normals.Compute = None
        self.faceSet.normals.Compute = None

    
    def sortPoly(self, order=-1):
        """None <- sortPoly(order=-1)
Sorts the geometry polygons according to z values of polygon's
geomtric centers. Order=-1 sorts by furthest z first, order=1 sorts
by closest z first"""
        # FIXME will not work with instance matrices
        mat = self.GetMatrix()
        mat = Numeric.reshape(mat, (4,4))
        vt = self.vertexSet.vertices*mat
        if vt is None:
            return
        triv = Numeric.take(vt, self.faceSet.faces.array)
        trig = Numeric.sum(triv,1)/3.
        trigz = trig[:,2]  #triangle's center of gravity z value
        
        ind = Numeric.argsort(trigz) # sorted indices
        
        if len(self.faceSet.faces.array):
            faces = Numeric.take(self.faceSet.faces.array, ind[::order])
        
            if self.shading==GL.GL_FLAT: # we also need to re-arrange the
                                       # face normals
                if self.normals is None:
                    normals = None
                else:
                    if len(self.normals)>1:
                        normals = Numeric.take(self.normals, ind[::order])
                    else:
                        normals = self.normals
            else:
                normals = None

            self.Set(faces=faces, fnormals=normals)


    def asIndexedPolygons(self, run=1, removeDupVerts=0, **kw):
        """Should return an IndexedPolygons object if this object can be
        represented using triangles, else return None. run=0 returns 1
        if this geom can be represented as an IndexedPolygon and None if not
        run=1 returns the IndexedPolygon object."""

        if run==0:
            return 1 # yes, I can be represented as IndexedPolygons
        
        if removeDupVerts==0:
            return self
        else:
            vu, fu = self.removeDuplicatedVertices()
            return IndexedPolygons('copy_'+self.name, vertices=vu, faces=fu,
                                   visible=1, 
                                   invertNormals=self.invertNormals)


    def writeToFile(self, filename):
        """swriteToFile(filename)
Creates a .vert and a face file describing this indexed polygons geoemtry.
only vertices, and noramsl are saved the the .vert file (x y z nx ny nz)
and 0-based topoly in the .face file (i, j, k, ... ).
"""
        verts = self.getVertices()
        vnorms = self.getVNormals()
        fnorms = self.getFNormals()
        faces = self.getFaces()

        file = open(filename+'.indpolvert', 'w')
        map( lambda v, n, f=file: \
             f.write("%f %f %f %f %f %f\n"%tuple(tuple(v)+tuple(n))),
             verts, vnorms)
        file.close()

        file = open(filename+'.indpolface', 'w')
        for v, face in zip(fnorms, faces):
            map( lambda ind, f=file: f.write("%d "%ind ), face )
            file.write("%f %f %f\n"%tuple(v))
        file.close()
