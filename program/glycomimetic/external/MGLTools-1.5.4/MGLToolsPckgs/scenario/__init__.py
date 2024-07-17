##
##  Author Michel F. Sanner Nov 11 2004
##
__version__ = "0.0.1"

"""
This package implements objects usable to defining and executing a scenario.
A scenario is defined as a sequence of events happening on a time line.
This package is using the SimPy package for the genration of the events.

The Director object

The Actor object:

An Actor object manages the value of an attribute of a Python object over the time of the simulation. It is implemented as a SimPy process.

It is create

## The highest level object is the Animator object.  This object contains a list of ObjectAnimators.  It provides high level control to run the scenario, go to a particular frame, etc.
## An AnimatorObject allows to modify a particular attribute of a Python object at each time step.  This object is implemented as SimPy Process object.  These Process objects are instanciated and activated automatically in the Animator when the scenario is run.
## The AnimatorObjects are instanciated from an ObjectAnimatorDescriptor object.  Such an object specifies:
##     - the Python object on which the ObjectAnimator will operate,
##     - a function to be called for each event,
##     - positional arguments to be passed to this function (posArgs),
##     - named arguments arguments to be passed to this function (namedArgs),
##     - an optional interpolator which is used to calculate a value at each frame
##     - an optional name for passing the value from the interpolator into
##       the function 
##       if no interpolator is specified the ObjectAnimator will call:
##           apply( func, posArgs, namedArgs)
##       else, if an interpolator is given but no name for the value:
##           apply( func, (value,)+posArgs, namedArgs)
##       else 
##       apply( func, posArgs, namedArgs+{name:value})
##       - the first and last frame at which this animator has to modify the object
## ObjectAnimatorDescriptor objects can be added to an Animator

## The interpolator objects use a starting and ending values
## They implement a getValue method which returns the appropriate value for a
## given step.
## We currently support linear interpolation of scalar and list of scalars and
## interpolators using functions.

## An interpolator can be declared sequential, meaning that the value at step i cannot be computed directly but the iterator has to be called from the first step up to step i.  An iterator adding incremental values at each step would be an example of a sequential iterator.

example:
    
"""
