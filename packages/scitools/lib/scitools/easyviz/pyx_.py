"""
This backend is based on the Python graphics package PyX which creates
PostScript and PDF files. The PyX backend does not produce any output until
the hardcopy method is called. One can specify this backend by

  python somefile.py --SCITOOLS_easyviz_backend pyx

or one can specify the backend in the SciTools configuration file
scitools.cfg under the [easyviz] section

  [easyviz]
  backend = pyx

and then

  from scitools.all import *

or if just easyviz is needed

  from scitools.easyviz import *

REQUIREMENTS:

pyx

TODO:

- add support for mesh and surf (requires PyX from svn)

- add support for axes in arbitrary positions, i.e., axes(viewport=...)

"""

from __future__ import division

from common import *
from scitools.globaldata import DEBUG, VERBOSE
from misc import _cmpPlotProperties

import pyx 
import math

def _cmpPlotProperties(a,b):
    """Sort cmp-function for PlotProperties"""
    plotorder = [Volume, Streams, Surface, Contours, VelocityVectors, Line] 
    assert isinstance(a, PlotProperties)
    assert isinstance(b, PlotProperties)
    assert len(PlotProperties.__class__.__subclasses__(PlotProperties)) == \
               len(plotorder) # Check all subclasses is in plotorder
    return cmp(plotorder.index(a.__class__),plotorder.index(b.__class__))


class PyXBackend(BaseClass):
    def __init__(self):
        BaseClass.__init__(self)
        self._init()
        
    def _init(self, *args, **kwargs):
        """Perform initialization that is special for this backend."""
        
        # Set docstrings of all functions to the docstrings of BaseClass
        # The exception is if something is very different
        # Alex had a nice function for this.
        
        self.figure(self.get('curfig'))

        # convert tables for format strings:
        self._markers = {
            '': None,   # no marker
            '.': None,  # dot
            'o': pyx.graph.style.symbol.circle,    # circle
            'x': pyx.graph.style.symbol.cross,     # cross
            '+': pyx.graph.style.symbol.plus,      # plus sign
            '*': None,  # asterisk
            's': pyx.graph.style.symbol.square,    # square
            'd': pyx.graph.style.symbol.diamond,   # diamond
            '^': pyx.graph.style.symbol.triangle,  # triangle (up)
            'v': pyx.graph.style.symbol.triangle,  # triangle (down)
            '<': pyx.graph.style.symbol.triangle,  # triangle (left)
            '>': pyx.graph.style.symbol.triangle,  # triangle (right)
            'p': None,  # pentagram
            'h': None,  # hexagram
            }
               
        self._colors = {
            '': None,   # no color --> blue
            'r': pyx.graph.style.color.cmyk.Red,      # red
            'g': pyx.graph.style.color.cmyk.Green,    # green
            'b': pyx.graph.style.color.cmyk.Blue,     # blue
            'c': pyx.graph.style.color.cmyk.Cyan,     # cyan
            'm': pyx.graph.style.color.cmyk.Magenta,  # magenta
            'y': pyx.graph.style.color.cmyk.Yellow,   # yellow
            'k': pyx.graph.style.color.cmyk.Black,    # black
            'w': pyx.graph.style.color.cmyk.White,    # white
            }
        
        self._line_styles = {
            '': None,                              # no line
            '-': pyx.style.linestyle.solid,        # solid line
            ':': pyx.style.linestyle.dotted,       # dotted line
            '-.': pyx.style.linestyle.dashdotted,  # dash-dot line
            '--': pyx.style.linestyle.dashed       # dashed line
            }

        # convert table for colorbar location:
        self._colorbar_locations = {
            'North': None,
            'South': None,
            'East': None,
            'West': None,
            'NorthOutside': None,
            'SouthOutside': None,
            'EastOutside': None,
            'WestOutside': None,
            }

        if DEBUG:
            print "Setting backend standard variables"
            for disp in 'self._markers self._colors self._line_styles'.split():
                print disp, eval(disp)

    def _get_scale(self, ax):
        # return a linear or logarithmic (base 10) axis 
        if DEBUG:
            print "Get axis scales"
        scale = ax.get('scale')
        if scale == 'loglog':
            # use logarithmic scale on both x- and y-axis
            xaxis = pyx.graph.axis.log
            yaxis = pyx.graph.axis.log
        elif scale == 'logx':
            # use logarithmic scale on x-axis and linear scale on y-axis
            xaxis = pyx.graph.axis.log
            yaxis = pyx.graph.axis.lin
        elif scale == 'logy':
            # use linear scale on x-axis and logarithmic scale on y-axis
            xaxis = pyx.graph.axis.lin
            yaxis = pyx.graph.axis.log
        elif scale == 'linear':
            # use linear scale on both x- and y-axis
            xaxis = pyx.graph.axis.lin
            yaxis = pyx.graph.axis.lin
        return xaxis, yaxis
    
    def _set_labels(self, ax):
        """Add text labels for x-, y-, and z-axis."""
        if DEBUG:
            print "Setting labels"
        xlabel = ax.get('xlabel')
        ylabel = ax.get('ylabel')
        zlabel = ax.get('zlabel')
        g = self._g.items[-1]
        if xlabel:
            # add a text label on x-axis
            g.axes['x'].axis.title = xlabel
        if ylabel:
            # add a text label on y-axis
            g.axes['y'].axis.title = ylabel
        if zlabel:
            # add a text label on z-axis
            pass
        
    def _set_title(self, ax):
        """Add a title at the top of the axis."""
        if DEBUG:
            print "Setting title"
        title = ax.get('title')
        if title:
            # set title
            g = self._g.items[-1]
            g.text(g.width/2+g.xpos, g.height+0.2+g.ypos, title, 
                   [pyx.text.halign.center,
                    pyx.text.valign.bottom,
                    pyx.text.size.Large])
    
    def _get_limits(self, ax):
        # return axis limits in x, y, and z direction
        if DEBUG:
            print "Setting axis limits"
        mode = ax.get('mode')
        limits = [None]*6
        if mode == 'auto':
            # let plotting package set 'nice' axis limits in the x, y,
            # and z direction. If this is not automated in the plotting
            # package, one can use the following limits:
            #xmin, xmax, ymin, ymax, zmin, zmax = ax.get_limits()
            pass
        elif mode == 'manual':
            # (some) axis limits are frozen
            xmin = ax.get('xmin')
            xmax = ax.get('xmax')
            if xmin is not None and xmax is not None:
                # set x-axis limits
                limits[0] = xmin
                limits[1] = xmax
            else:
                # let plotting package set x-axis limits or use
                #xmin, xmax = ax.get('xlim')
                pass

            ymin = ax.get('ymin')
            ymax = ax.get('ymax')
            if ymin is not None and ymax is not None:
                # set y-axis limits
                limits[2] = ymin
                limits[3] = ymax
            else:
                # let plotting package set y-axis limits or use
                #ymin, ymax = ax.get('ylim')
                pass

            zmin = ax.get('zmin')
            zmax = ax.get('zmax')
            if zmin and zmax:
                # set z-axis limits
                limits[4] = zmin
                limits[5] = zmax
            else:
                # let plotting package set z-axis limits or use
                #zmin, zmax = ax.get('zlim')
                pass
        elif mode == 'tight':
            # set the limits on the axis to the range of the data. If
            # this is not automated in the plotting package, one can
            # use the following limits:
            #xmin, xmax, ymin, ymax, zmin, zmax = ax.get_limits()
            limits = ax.get_limits()
        elif mode == 'fill':
            # not sure about this
            pass
        return limits

    def _set_position(self, ax):
        """Set axes position."""
        rect = ax.get('viewport')
        if rect:
            # axes position is defined. In Matlab rect is defined as
            # [left,bottom,width,height], where the four parameters are
            # location values between 0 and 1 ((0,0) is the lower-left
            # corner and (1,1) is the upper-right corner).
            # NOTE: This can be different in the plotting package.
            pass

    def _set_daspect(self, ax):
        """Set data aspect ratio."""
        if ax.get('daspectmode') == 'manual':
            dar = ax.get('daspect')  # dar is a list (len(dar) is 3).
            pass
        else:
            # daspectmode is 'auto'. Plotting package handles data
            # aspect ratio automatically.
            pass
        
    def _set_axis_method(self, ax):
        method = ax.get('method')
        if method == 'equal':
            # tick mark increments on the x-, y-, and z-axis should
            # be equal in size.
            pass
        elif method == 'image':
            # same effect as axis('equal') and axis('tight')
            pass
        elif method == 'square':
            # make the axis box square in size
            pass
        elif method == 'normal':
            # full size axis box
            pass
        elif method == 'vis3d':
            # freeze data aspect ratio when rotating 3D objects
            pass

    def _set_coordinate_system(self, ax):
        """
        Use either the default Cartesian coordinate system or a
        matrix coordinate system.
        """
        
        direction = ax.get('direction')
        if direction == 'ij':
            # Use matrix coordinates. The origin of the coordinate
            # system is the upper-left corner. The i-axis should be
            # vertical and numbered from top to bottom, while the j-axis
            # should be horizontal and numbered from left to right.
            pass
        elif direction == 'xy':
            # use the default Cartesian axes form. The origin is at the
            # lower-left corner. The x-axis is vertical and numbered
            # from left to right, while the y-axis is vertical and
            # numbered from bottom to top.
            pass

    def _set_box(self, ax):
        """Turn box around axes boundary on or off."""
        if DEBUG:
            print "Setting box"
        if ax.get('box'):
            # display box 
            pass
        else:
            # do not display box
            pass
        
    def _set_grid(self, ax):
        """Turn grid lines on or off."""
        if DEBUG:
            print "Setting grid"
        if ax.get('grid'):
            # turn grid lines on
            pass
        else:
            # turn grid lines off
            pass

    def _set_hidden_line_removal(self, ax):
        """Turn on/off hidden line removal for meshes."""
        if DEBUG:
            print "Setting hidden line removal"
        if ax.get('hidden'):
            # turn hidden line removal on
            pass
        else:
            # turn hidden line removal off
            pass

    def _set_colorbar(self, ax):
        """Add a colorbar to the axis."""
        if DEBUG:
            print "Setting colorbar"
        cbar = ax.get('colorbar')
        if cbar.get('visible'):
            # turn on colorbar
            cbar_title = cbar.get('cbtitle')
            cbar_location = self._colorbar_locations[cbar.get('cblocation')]
            # ...
        else:
            # turn off colorbar
            pass

    def _set_caxis(self, ax):
        """Set the color axis scale."""
        if DEBUG:
            print "Setting caxis"
        if ax.get('caxismode') == 'manual':
            cmin, cmax = ax.get('caxis')
            # NOTE: cmin and cmax might be None:
            if cmin is None or cmax is None:
                cmin, cmax = [0,1]
            # set color axis scaling according to cmin and cmax
            pass
        else:
            # use autoranging for color axis scale
            pass

    def _set_colormap(self, ax):
        """Set the colormap."""
        if DEBUG:
            print "Setting colormap"
        cmap = ax.get('colormap')
        # cmap is plotting package dependent

    def _set_view(self, ax):
        """Set viewpoint specification."""
        if DEBUG:
            print "Setting view"
        cam = ax.get('camera')
        view = cam.get('view')
        if view == 2:
            # setup a default 2D view
            pass
        elif view == 3:
            az = cam.get('azimuth')
            el = cam.get('elevation')
            if az is None or el is None:
                # azimuth or elevation is not given. Set up a default
                # 3D view (az=-37.5 and el=30 is the default 3D view in
                # Matlab).
                pass
            else:
                # set a 3D view according to az and el
                pass
            
            if cam.get('cammode') == 'manual':
                # for advanced camera handling:
                roll = cam.get('camroll')
                zoom = cam.get('camzoom')
                dolly = cam.get('camdolly')
                target = cam.get('camtarget')
                position = cam.get('campos')
                up_vector = cam.get('camup')
                view_angle = cam.get('camva')
                projection = cam.get('camproj')

    def _set_axis_props(self, ax):
        if DEBUG:
            print "Setting axis properties"
        self._set_title(ax)
        self._set_position(ax)
        self._set_axis_method(ax)
        self._set_daspect(ax)
        self._set_coordinate_system(ax)
        self._set_hidden_line_removal(ax)
        self._set_colorbar(ax)
        self._set_caxis(ax)
        self._set_colormap(ax)
        self._set_view(ax)
        if ax.get('visible'):
            self._set_labels(ax)
            self._set_box(ax)
            self._set_grid(ax)
        else:
            # turn off all axis labeling, tickmarks, and background
            pass

    def _get_linespecs(self, item):
        """
        Return the line marker, line color, line style, and
        line width of the item.
        """
        
        marker = self._markers[item.get('linemarker')]
        color = self._colors[item.get('linecolor')]
        style = self._line_styles[item.get('linetype')]
        width = item.get('linewidth')
        if width:
            width = pyx.style.linewidth(float(width)*pyx.unit.w_pt)
        return marker, color, style, width

    def _add_line(self, item):
        """Add a 2D or 3D curve to the scene."""
        if DEBUG:
            print "Adding a line"
        # get data:
        x = item.get('xdata')
        y = item.get('ydata')
        z = item.get('zdata')
        # get line specifiactions:
        marker, color, style, width = self._get_linespecs(item)

        styles = []
        lineattrs = []
        if style:
            lineattrs.append(style)
            if color:
                lineattrs.append(color)
            if width:
                lineattrs.append(width)
            styles.append(pyx.graph.style.line(lineattrs=lineattrs))
        if marker:
            if color: 
                styles.append(pyx.graph.style.symbol(marker,
                                                     symbolattrs=[color]))
            else:
                styles.append(pyx.graph.style.symbol(marker))
        else:
            if not styles:
                styles = [pyx.graph.style.line([pyx.color.gradient.Rainbow])]

        data = []
        if z is not None:
            # zdata is given, add a 3D curve:
            pass
        else:
            # no zdata, add a 2D curve:
            for i in range(len(x)):
                data.append([x[i], y[i]])

        legend = item.get('legend')
        if not legend:
            legend = None
        self._g.items[-1].plot(pyx.graph.data.list(data,x=1,y=2,title=legend),
                               styles=styles)

    def _add_surface(self, item, shading='faceted'):
        if DEBUG:
            print "Adding a surface"
        x = item.get('xdata')  # grid component in x-direction
        y = item.get('ydata')  # grid component in y-direction
        z = item.get('zdata')  # scalar field
        c = item.get('cdata')  # pseudocolor data (can be None)
        
        data = []
        m, n = shape(z)
        if shape(x) != shape(z) and shape(y) != shape(z):
            x, y = meshgrid(x,y,sparse=False)
        for i in range(m):
            for j in range(n):
                data.append([x[i,j], y[i,j], z[i,j]])
        
        contours = item.get('contours')
        if contours:
            # the current item is produced by meshc or surfc and we
            # should therefore add contours at the bottom:
            self._add_contours(contours, placement='bottom')

        styles = []
        if item.get('wireframe'):
            # wireframe mesh (as produced by mesh or meshc)
            styles.append(pyx.graph.style.line())
        else:
            # colored surface (as produced by surf, surfc, or pcolor)
            # use keyword argument shading to set the color shading mode
            styles.append(pyx.graph.style.surface())
            
        legend = item.get('legend')
        if not legend:
            legend = None
        g = self._g.items[-1]
        g.plot(pyx.graph.data.list(data, x=1, y=2, color=3, title=legend),
               styles=styles)
        g.dodata()

    def _add_contours(self, item, placement=None):
        # The placement keyword can be either None or 'bottom'. The
        # latter specifies that the contours should be placed at the
        # bottom (as in meshc or surfc).
        if DEBUG:
            print "Adding contours"
        x = item.get('xdata')  # grid component in x-direction
        y = item.get('ydata')  # grid component in y-direction
        z = item.get('zdata')  # scalar field

        filled = item.get('filled')  # draw filled contour plot if True

        cvector = item.get('cvector')
        clevels = item.get('clevels')  # number of contour levels
        if cvector is None:
            # the contour levels are chosen automatically
            #cvector =
            pass

        location = item.get('clocation')
        if location == 'surface':
            # place the contours at the corresponding z level (contour3)
            pass
        elif location == 'base':
            if placement == 'bottom':
                # place the contours at the bottom (as in meshc or surfc)
                pass
            else:
                # standard contour plot
                pass

        if item.get('clabels'):
            # add labels on the contour curves
            pass
    
    def _add_vectors(self, item):
        if DEBUG:
            print "Adding vectors"
        # uncomment the following command if there is no support for
        # automatic scaling of vectors in the current plotting package:
        #item.scale_vectors()

        # grid components:
        x, y, z = item.get('xdata'), item.get('ydata'), item.get('zdata')
        # vector components:
        u, v, w = item.get('udata'), item.get('vdata'), item.get('wdata')
        # get line specifiactions (marker='.' means no marker):
        marker, color, style, width = self._get_linespecs(item)

        # scale the vectors according to this variable (scale=0 should
        # turn off automatic scaling):
        scale = item.get('arrowscale')

        filled = item.get('filledarrows') # draw filled arrows if True

        if z is not None and w is not None:
            # draw velocity vectors as arrows with components (u,v,w) at
            # points (x,y,z):
            pass
        else:
            # draw velocity vectors as arrows with components (u,v) at
            # points (x,y):
            pass

    def _add_streams(self, item):
        if DEBUG:
            print "Adding streams"
        # grid components:
        x, y, z = item.get('xdata'), item.get('ydata'), item.get('zdata')
        # vector components:
        u, v, w = item.get('udata'), item.get('vdata'), item.get('wdata')
        # starting positions for streams:
        sx, sy, sz = item.get('startx'), item.get('starty'), item.get('startz')

        if item.get('tubes'):
            # draw stream tubes from vector data (u,v,w) at points (x,y,z)
            n = item.get('n') # no points along the circumference of the tube
            scale = item.get('tubescale')
            pass
        elif item.get('ribbons'):
            # draw stream ribbons from vector data (u,v,w) at points (x,y,z)
            width = item.get('ribbonwidth')
            pass
        else:
            if z is not None and w is not None:
                # draw stream lines from vector data (u,v,w) at points (x,y,z)
                pass
            else:
                # draw stream lines from vector data (u,v) at points (x,y)
                pass
            pass

    def _add_isosurface(self, item):
        if DEBUG:
            print "Adding a isosurface"
        # grid components:
        x, y, z = item.get('xdata'), item.get('ydata'), item.get('zdata')
        v = item.get('vdata')  # volume
        c = item.get('cdata')  # pseudocolor data
        isovalue = item.get('isovalue')

    def _add_slices(self, item):
        if DEBUG:
            print "Adding slices in a volume"
        # grid components:
        x, y, z = item.get('xdata'), item.get('ydata'), item.get('zdata')
        v = item.get('vdata')  # volume

        sx, sy, sz = item.get('slices')
        if rank(sz) == 2:
            # sx, sy, and sz defines a surface
            pass
        else:
            # sx, sy, and sz is either numbers or vectors with numbers
            pass
        pass

    def _add_contourslices(self, item):
        if DEBUG:
            print "Adding contours in slice planes"
        # grid components:
        x, y, z = item.get('xdata'), item.get('ydata'), item.get('zdata')
        v = item.get('vdata')  # volume

        sx, sy, sz = item.get('slices')
        if rank(sz) == 2:
            # sx, sy, and sz defines a surface
            pass
        else:
            # sx, sy, and sz is either numbers or vectors with numbers
            pass

        cvector = item.get('cvector')
        clevels = item.get('clevels')  # number of contour levels per plane
        if cvector is None:
            # the contour levels are chosen automatically
            #cvector =
            pass
        pass

    def _get_figure_size(self, fig):
        if DEBUG:
            print "Get figure size"
        width, height = fig.get('size')
        if width is None or height is None:
            # use the default width and height in plotting package
            width = 15
            ratio = 0.5*(math.sqrt(5)+1)  # golden mean
            height = (1.0/ratio)*width
        return width, height

    def figure(self, *args, **kwargs):
        # Extension of BaseClass.figure:
        # add a plotting package figure instance as fig._g and create a
        # link to it as self._g
        BaseClass.figure(self, *args, **kwargs) 
        fig = self.gcf()
        try:
            fig._g
        except:
            # create plotting package figure and save figure instance
            # as fig._g
            if DEBUG:
                name = 'Fig ' + str(self.get('curfig'))
                print "creating figure %s in backend" % name

            fig._g = pyx.canvas.canvas()
            
        self._g = fig._g # link for faster access

    figure.__doc__ = BaseClass.figure.__doc__

    def _replot(self):
        """Replot all axes and all plotitems in the backend."""
        # NOTE: only the current figure (gcf) is redrawn.
        if DEBUG:
            print "Doing replot in backend"
        
        fig = self.gcf()
        # reset the plotting package instance in fig._g now if needed
        self._g.items = []
        
        width, height = self._get_figure_size(fig)
        xpos = 0;  ypos = 0
        tmp_xpos = 0;  tmp_ypos = 0

        row = 1;  column = 1
        nrows, ncolumns = fig.get('axshape')
        sbsp = 1.8  # space between subplots
        w = width/ncolumns-sbsp  # subplot width
        h = height/nrows-sbsp    # subplot height
        for axnr, ax in fig.get('axes').items():
            legends = False
            xaxis, yaxis = self._get_scale(ax)
            xmin, xmax, ymin, ymax, zmin, zmax = self._get_limits(ax)
            kwargs = {'x': xaxis(min=xmin, max=xmax),
                      'y': yaxis(min=ymin, max=ymax)}
            pth = ax.get('pth')
            if pth:
                # create axes in tiled position
                # this is subplot(nrows,ncolumns,pth)
                xpos = tmp_xpos;  ypos = tmp_ypos
                if column < ncolumns:
                    column += 1
                    tmp_xpos += w + sbsp
                else:
                    column = 1
                    tmp_xpos = 0
                    if row <= nrows:
                        row += 1
                        tmp_ypos -= h + sbsp
                kwargs.update({'width': w, 'height': h})
            else:
                #xpos, ypos, width, height = self._get_viewport(ax)
                kwargs.update({'width': width, 'height': height})
            graph = pyx.graph.graphxy(xpos, ypos, **kwargs)
            #graph = pyx.graph.graphxyz(xpos, ypos, width=5, height=5, depth=5)
            plotitems = ax.get('plotitems')
            plotitems.sort(_cmpPlotProperties)
            if plotitems:
                self._g.insert(graph)  # insert graph into figure canvas
                self._set_axis_props(ax)
            for item in plotitems:
                func = item.get('function') # function that produced this item
                if isinstance(item, Line):
                    self._add_line(item)
                elif isinstance(item, Surface):
                    self._add_surface(item, shading=ax.get('shading'))
                elif isinstance(item, Contours):
                    self._add_contours(item)
                elif isinstance(item, VelocityVectors):
                    self._add_vectors(item)
                elif isinstance(item, Streams):
                    self._add_streams(item)
                elif isinstance(item, Volume):
                    if func == 'isosurface':
                        self._add_isosurface(item)
                    elif func == 'slice_':
                        self._add_slices(item)
                    elif func == 'contourslice':
                        self._add_contourslices(item)
                legend = item.get('legend')
                if legend:
                    # add legend to plot
                    legends = True

            if legends:
                graph.key = pyx.graph.key.key(pos="tr", dist=0.1)
                    
        if self.get('show'):
            # display plot on the screen
            if DEBUG:
                print "\nDumping plot data to screen\n"
                debug(self)
            pass

    def hardcopy(self, filename, **kwargs):
        """
        Supported extensions: .pdf, .ps, .eps
        """
        self.set(**kwargs)
        color = self.get('color')
        self._replot()

        if DEBUG:
            print "Hardcopy to %s" % filename

        basename, ext = os.path.splitext(filename)
        if not ext:
            # no extension given, assume PostScript
            filename += '.ps'
        self._g.writetofile(filename)

    hardcopy.__doc__ = BaseClass.hardcopy.__doc__ + hardcopy.__doc__

    # reimplement methods like clf, closefig, closefigs
    def clf(self):
        fig = self.gcf()
        del fig._g
        BaseClass.clf(self)

    # implement colormap functions here
    #def jet(self, m=None):
    #    """Variant of hsv."""
    #    pass
    

plt = PyXBackend()   # create backend instance
use(plt, globals())  # export public namespace of plt to globals()
