from collections import defaultdict
from _thread import RLock
from functools import update_wrapper



def lrut_cache(maxsize=128):
    """Simplified functools. lru_cache decorator for one argument."""

    # todo add timeout support
    def decorator(function):
        sentinel = object()
        cache = {}
        get = cache.get
        lock = RLock()
        root = []
        root_full = [root, False]
        root[:] = [root, root, None, None]

        if maxsize == 0:
            def wrapper(obj,arg):
                res = function(obj, arg)
                return res
        elif maxsize is None:
            def wrapper(obj, arg):
                res = get(arg, sentinel)
                if res is not sentinel:
                    return res
                res = function(obj, arg)
                cache[arg] = res
                return res
        else:
            def wrapper(obj, arg):
                with lock:
                    link = get(arg)
                    if link is not None:
                        root = root_full[0]
                        prev, next, _arg, res = link
                        prev[1] = next
                        next[0] = prev
                        last = root[0]
                        last[1] = root[0] = link
                        link[0] = last
                        link[1] = root
                        return res
                res = function(obj, arg)
                with lock:
                    root, full = root_full
                    if arg in cache:
                        pass
                    elif full:
                        oldroot = root
                        oldroot[2] = arg
                        oldroot[3] = res
                        root = root_full[0] = oldroot[1]
                        oldarg = root[2]
                        oldres = root[3]  # keep reference
                        root[2] = root[3] = None
                        del cache[oldarg]
                        cache[arg] = oldroot
                    else:
                        last = root[0]
                        link = [last, root, arg, res]
                        last[1] = root[0] = cache[arg] = link
                        if len(cache) >= maxsize:
                            root_full[1] = True
                return res

        wrapper.__wrapped__ = function
        return update_wrapper(wrapper, function)

    return decorator


dict1={"1":"abc", "2":"def", "3":"ghi"}
@lrut_cache(None)
def func1(obj_id):
    print("in func1")
    return dict1.get(str(obj_id))


if __name__  == "__main__":
    print(func1(1))
    print(func1(2))
    print(func1(3))
    print(func1(1))
    print(func1(4))
    print(func1(4))

