from rest_framework.response import Response

def check_params(required_params):
    def decorator(method):
        def wrapper(request):
            for param in required_params:
                if param not in request.GET:
                    return Response("Missing required param: " + param)

            return method(request)
        return wrapper
    return decorator

def getQueryValue(request, param):
    return dict(request.GET)[param][0]

def getQueryDict(request, keys=None):
    _pre = dict(request.GET)
    value = dict()

    if keys == None:
        keys = _pre.keys()

    for key in keys:
        value[key] = _pre[key][0]

    return value