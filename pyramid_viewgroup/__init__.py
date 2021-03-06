import itertools

from pyramid.response import Response

from pyramid.exceptions import Forbidden
from pyramid.view import render_view_to_iterable
from pyramid.view import render_view
from zope.interface import Interface
from pyramid.interfaces import (
    IViewClassifier,
    IView,
    IRequest,
    )

class ViewGroup(object):
    def __init__(self, name, viewnames):
        self.name = name
        self._viewnames = []
        self.add_views(viewnames)
        
    def add_views(self, names):
        for v in names:
            if v in self._viewnames:
                raise ValueError('View %s already in viewgroup' % v)
        
        for v in names:
            self._viewnames.append(v)

    def __call__(self, context, request):
        renderings = []

        for viewname in self._viewnames:
            try:
                iterable = render_view_to_iterable(context, request, viewname)
            except Forbidden:
                continue
            if iterable is None:
                raise ValueError(
                    'No such view named %s for viewgroup %s' %
                    (viewname, self.name)
                    )
            renderings.append(iterable)

        return Response(app_iter=itertools.chain(*renderings))

class Provider(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, name='', secure=True):
        return render_view(self.context, self.request, name, secure)

def add_viewgroup(config, name, viewnames, context=None):
    reg = config.registry
    _context = context or Interface
    wrapper = reg.adapters.lookup(
        (IViewClassifier, IRequest, _context), IView, name=name)
    if not wrapper:
        viewgroup = ViewGroup(name, viewnames)
        config.add_view(viewgroup, name=name, context=context)
        return
    viewgroup = wrapper.__original_view__
    viewgroup.add_views(viewnames)


def includeme(config):
    config.add_directive('add_viewgroup', add_viewgroup)
    
