"""Make figures with SVG."""

import math

import svgwrite


class SvgFig(object):

    draw_grid = False

    @classmethod
    def set_options(cls, draw_grid=None):
        if draw_grid is not None:
            cls.draw_grid = draw_grid

    def __init__(self, size, frame_num=None, **extra):
        self.frame_num = frame_num

        self.dwg = svgwrite.Drawing(debug=True, size=size, **extra)

        # Define our arrow.
        self.arrow = self.dwg.marker(
            insert=(10,5), size=(10,10), orient="auto",
        )
        self.arrow.viewbox(0, 0, 10, 10)
        self.arrow.add(self.dwg.path(d="M 0,0 L 10,5 L 0,10 L 1,5 z", stroke="none", fill="black"))
        self.dwg.defs.add(self.arrow)

        # Draw a grid if desired.
        if self.draw_grid:
            grid = self.dwg.g(class_="grid")
            self.dwg.add(grid)

            def lineclass(d):
                if d == 0:
                    return "whole"
                elif d == 50:
                    return "half"
                else:
                    return "tiny"

            w, h = size
            for x in range(0, w, 100):
                grid.add(self.dwg.text(str(x), insert=(x+2, 7), class_="number"))
                for d in range(0, 100, 10):
                    grid.add(self.dwg.polyline([(x+d, 0), (x+d, h)], class_=lineclass(d)))
            for y in range(0, h, 100):
                grid.add(self.dwg.text(str(y), insert=(2, y+7), class_="number"))
                for d in range(0, 100, 10):
                    grid.add(self.dwg.polyline([(0, y+d), (w, y+d)], class_=lineclass(d)))

    def tostring(self):
        return self.dwg.tostring()

    def should_draw(self, box):
        if self.frame_num is None:
            return True

        return box.rise <= self.frame_num < box.set

    def rect(self, **args):
        box = Box(args)
        text = poparg(args, text=None)
        if self.should_draw(box):
            r = self.dwg.rect(
                insert=(box.left, box.top),
                size=box.size,
                **args
            )
            self.dwg.add(r)

            self.text_for_box(text, box)
        return box

    def circle(self, **args):
        box = Box(args)
        text = poparg(args, text=None)
        if self.should_draw(box):
            c = self.dwg.circle(
                center=box.center,
                r=box.size[0]/2,
                **args
            )
            self.dwg.add(c)

            self.text_for_box(text, box)
        return box

    def text_for_box(self, text, box, **args):
        if text and self.should_draw(box):
            t = self.dwg.text(text, insert=box.center, text_anchor="middle", dy=[".3em"], **args)
            self.dwg.add(t)

    def line(self, start, end, **extra):
        l = self.dwg.polyline([start, end], **extra)
        l['marker-end'] = self.arrow.get_funciri()
        self.dwg.add(l)

    def connect(self, start, startdir, end, enddir, jump=None, **args):
        # Bleh: hack to get should_draw info from args.
        args['center'] = start
        args['size'] = (0,0)
        should_draw_box = Box(args)

        if self.should_draw(should_draw_box):
            if jump is None:
                jump = distance(start, end) / 4
            start_jump = offset(start, startdir, jump)
            end_jump = offset(end, enddir+180, jump)
            mid = midpoint(start_jump, end_jump)
            pre_mid = toward(mid, jump, start_jump)
            post_mid = toward(mid, jump, end_jump)

            pathops = []
            pathops.append(pathop("M", start))
            pathops.append(pathop("C", start_jump, pre_mid, mid))
            pathops.append(pathop("C", post_mid, end_jump, end))

            p = self.dwg.path(" ".join(pathops), fill="none", **args)
            p['marker-end'] = self.arrow.get_funciri()
            self.dwg.add(p)



def pathop(op, *coords):
    res = op
    for x, y in coords:
        res += " {0:d},{1:d}".format(int(x), int(y))
    return res


def offset(point, angle, dist):
    x, y = point
    angle = math.radians(angle)
    x += dist * math.cos(angle)
    y += dist * math.sin(angle)
    return x, y

def distance(start, end):
    x0, y0 = start
    x1, y1 = end
    dx = x1 - x0
    dy = y1 - y0
    start_to_end = math.sqrt(dx*dx + dy*dy)
    return start_to_end

def midpoint(start, end):
    x0, y0 = start
    x1, y1 = end
    return (x0+x1)/2, (y0+y1)/2

def toward(start, dist, end):
    x0, y0 = start
    x1, y1 = end
    dx = x1 - x0
    dy = y1 - y0
    start_to_end = math.sqrt(dx*dx + dy*dy)
    frac = float(dist) / start_to_end
    return x0 + frac*dx, y0 + frac*dy


class Box(object):
    def __init__(self, args):
        other_box = poparg(args, box=None)
        if other_box is not None:
            # Copy all the attributes of the other box.
            self.__dict__.update(other_box.__dict__)
            return

        size = poparg(args, size=None)
        assert size, "Have to specify a size!"

        pos_name = pos = None
        arg_names = "left center right topleft topright".split()
        for arg_name in arg_names:
            arg = poparg(args, **{arg_name: None})
            if arg is not None:
                assert pos is None, "Got duplicate position: %s" % pos_name
                pos_name = arg_name
                pos = arg

        # Can specify position as pos=('topright', (100,200))
        pos_arg = poparg(args, pos=None)
        if pos_arg is not None:
            assert pos is None, "Got duplicate position: pos"
            pos_name, pos = pos_arg

        if pos_name == 'left':
            center = (pos[0]+size[0]/2, pos[1])
        elif pos_name == 'right':
            center = (pos[0]-size[0]/2, pos[1])
        elif pos_name == 'center':
            center = pos
        elif pos_name == 'topleft':
            center = (pos[0]+size[0]/2, pos[1]+size[1]/2)
        elif pos_name == 'topright':
            center = (pos[0]-size[0]/2, pos[1]+size[1]/2)
        else:
            assert False, "Have to specify a position!"

        self.center = center
        self.size = size

        self.cx, self.cy = center
        self.w, self.h = size

        self.rise = poparg(args, rise=0)
        self.set = poparg(args, set=999999)

    def translate(self, dx, dy):
        self.cx += dx
        self.cy += dy
        self.center = self.cx, self.cy

    @property
    def top(self):
        return self.cy - self.h/2

    @property
    def bottom(self):
        return self.cy + self.h/2

    @property
    def left(self):
        return self.cx - self.w/2

    @property
    def right(self):
        return self.cx + self.w/2

    @property
    def north(self):
        return self.cx, self.top

    @property
    def south(self):
        return self.cx, self.bottom

    @property
    def east(self):
        return self.right, self.cy

    @property
    def west(self):
        return self.left, self.cy

class PyFig(SvgFig):
    def name(self, **args):
        class_ = add_class("name", poparg(args, class_=None))
        return self.rect(class_=class_, **args)

    def int(self, **args):
        defarg(args, size=(50,50))
        class_ = add_class("int value", poparg(args, class_=None))
        return self.circle(class_=class_, **args)

    def list(self, **args):
        texts = poparg(args, texts=['x', 'y', 'z'])
        box = Box(args)
        class_ = poparg(args, class_=None)
        class_ = add_class("list", class_)
        boxes = []
        for text in texts:
            b = self.rect(box=box, class_=class_, text=text, **args)
            boxes.append(b)
            box.translate(box.w, 0)
        return boxes

    def reference(self, name, val, **args):
        if self.should_draw(name) and self.should_draw(val):
            self.connect(name.east, 0, val.west, 0, class_="arrow", **args)

    def frame(self, **args):
        text = poparg(args, text=None)
        class_ = poparg(args, class_=None)
        rclass = add_class("frame", class_)
        box = self.rect(class_=rclass, rx=20, ry=20, **args)
        tclass = add_class("framelabel", class_)
        if self.should_draw(box):
            text_box = Box({'center':(box.cx, box.top+25), 'size':(box.w, 25)})
            self.text_for_box(text, box=text_box, class_=tclass)
        return box


def poparg(args, **argdef):
    name, value = argdef.popitem()
    return args.pop(name, value)

def defarg(args, **argdef):
    name, value = argdef.popitem()
    args.setdefault(name, value)

def add_class(add, class_):
    if class_:
        class_ += " "
    else:
        class_ = ""
    return class_ + add


class PyLayout(object):
    def __init__(self, y=100, y_stride=75, name_right=200, val_gap=100):
        self.y = y
        self.y_stride = y_stride
        self.name_right = name_right
        self.val_left = self.name_right + val_gap

    def next_name(self):
        """Produce a position for the next name."""
        topright = (self.name_right, self.y)
        self.y += self.y_stride
        return ('topright', topright)

    def val_for_name(self, name):
        """Produce a position for a val alongside `name`."""
        left = (self.val_left, name.cy)
        return ('left', left)

    def next_frame(self):
        """Produce a position for the next frame."""
        topright = (self.name_right + 25, self.y)
        self.y += 50
        return ('topright', topright)

# DSL hackery:
#   
#   >>> def u(*args, **kwargs):
#   ...  for a in args:
#   ...   kwargs.update(a)
#   ...  return kwargs
#   ...
#   >>> def f(**kwargs): print kwargs
#   ...
#   >>> f(**u(a=1,b=2))
#   {'a': 1, 'b': 2}
#   >>> f(**u(a=1,b=2,{'c':23}))
#     File "<stdin>", line 1
#   SyntaxError: non-keyword arg after keyword arg      # :( :(
#   >>> f(**u({'c':23},a=1,b=2))
#   {'a': 1, 'c': 23, 'b': 2}
#   >>> f(**u({'c':23},{'d':45},a=1,b=2))
#   {'a': 1, 'c': 23, 'b': 2, 'd': 45}
