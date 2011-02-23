# A hack for maintaining a global list of coroutines to be executed
# This allows the @coroutine decorator to function
import __builtin__

try:
    n = len(__builtin__.__addhack_new_coroutines)
except:
    __builtin__.__addhack_new_coroutines = []
    __builtin__.__addhack_decorated = []
    __builtin__.__queue_decorated = True

def add_coroutine(f, *args, **keys):
    print "Adding coroutine"
    __builtin__.__addhack_new_coroutines.append( (f, args, keys) )

def coroutine(f):
    "Decorator to add a function as a coroutine "
    if __builtin__.__queue_decorated:
        __builtin__.__addhack_decorated.append(f)
    else:
        add_coroutine(f)

    # Don't modify the function
    return f

def clear_coroutines():
    __builtin__.__addhack_new_coroutines = []

def get_coroutines():
    return __builtin__.__addhack_new_coroutines

def show_coroutines():
    print "%i coroutines queued" % len(__builtin__.__addhack_new_coroutines)

def add_queued():
    __builtin__.__queue_decorated = False
    for x in __builtin__.__addhack_decorated:
        add_coroutine(x)
    __builtin__.__addhack_decorated = []

    
