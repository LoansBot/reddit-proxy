"""This service simply delegates requests to the actual endpoints implemented
in endpoints/
"""
import importlib
import os
from inspect import signature, _empty


class Reddit:
    """This is a very low-level wrapper around the reddit API, which is not
    exposed directly via RabbitMQ. This just provides an extremely convenient
    interface to each endpoint, as well as the appropriate docstrings for each
    of the endpoints, without actually implementing all the endpoints in a
    single file.
    """
    pass

# All this does is take BarEndpoint which has name bar and convert
# BarEndpoint.make_request into Reddit.bar. 90% of the work is getting this
# to be invisible in the docstring.

# I tried several approaches, including building the function using makefun,
# but they all didn't look right in the docstring. The hardest part was
# getting it to look like bar(self, foo) and not bar(foo) in the docstring
# while still passing along the correct self to the endpoint.

# The major downside of this approach is that default values whose repr
# doesn't create the code which creates a copy won't work, but at least this
# can be worked around pretty easily and works fine for e.g. numbers, strings,
# empty arrays, empty dicts, and None which covers 99% of default param values

# One pretty significant upside is that as long as we have inspect.signature,
# this is pretty unlikely to break in the future. It seems much more probable
# that something breaks makefun


def _wrap_endpoint(endpoint):
    prms_arr_with_defaults = []
    prms_arr_no_defaults = []
    for prm in signature(endpoint.make_request).parameters.values():
        prm_s = prm.name
        prms_arr_no_defaults.append(prm_s)
        if prm.default != _empty:
            prm_s = f'{prm_s}={repr(prm.default)}'
        prms_arr_with_defaults.append(prm_s)

    func_def_str = ', '.join(['self'] + prms_arr_with_defaults)
    args_str = ', '.join(prms_arr_no_defaults)

    my_func_str = (
        'def wrapped(' + func_def_str + '):\n'
        '  global endpoint\n'
        '  return endpoint.make_request(' + args_str + ')\n'
    )

    glbls = {'endpoint': endpoint}
    lcls = {}
    exec(my_func_str, glbls, lcls)

    wrapped = lcls['wrapped']
    wrapped.__name__ = wrapped.__qualname__ = endpoint.name
    wrapped.__doc__ = endpoint.make_request.__doc__
    return wrapped


def _default_headers():
    return {
        'User-Agent': os.environ['USER_AGENT']
    }


def _load_endpoints():
    headers = _default_headers()
    endpoints = []
    for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), 'endpoints')):
        mod_base = []
        my_root = root
        while True:
            my_root, nm = os.path.split(my_root)
            mod_base.append(nm)
            if nm == 'endpoints':
                break
        mod_base = '.'.join(reversed(mod_base))
        if mod_base != '':
            mod_base += '.'

        for f in files:
            if f.endswith('.py'):
                mod_nm = mod_base + f[:-3]
                mod = importlib.import_module(mod_nm)
                if hasattr(mod, 'register_endpoints'):
                    mod.register_endpoints(endpoints, headers)

    for e in endpoints:
        setattr(Reddit, e.name, _wrap_endpoint(e))


_load_endpoints()
