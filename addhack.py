# A horrible hack for adding new coroutines
# Getting different modules to talk about the same list
# was like pulling my eyes through a sieve.
# Unfortunately, I don't have enough time to learn about
# how Python things namespaces should work.
# Putting the list in it's own module works.

try:
    n = len(__builtins__.__addhack_new_coroutines)
except:
    __builtins__["__addhack_new_coroutines"] = []
    __builtins__["__addhack_decorated"] = []
    __builtins__["__queue_decorated"] = True

def add_coroutine(f, *args, **keys):
    print "Adding coroutine"
    __builtins__["__addhack_new_coroutines"].append( (f, args, keys) )

def coroutine(f):
    "Decorator to add a function as a coroutine "
    if __builtins__["__queue_decorated"]:
        __builtins__["__addhack_decorated"].append(f)
    else:
        add_coroutine(f)

    # Don't modify the function
    return f

def clear_coroutines():
    __builtins__["__addhack_new_coroutines"] = []

def get_coroutines():
    return __builtins__["__addhack_new_coroutines"]

def show_coroutines():
    print "%i coroutines queued" % len(__builtins__["__addhack_new_coroutines"])

def add_queued():
    __builtins__["__queue_decorated"] = False
    for x in __builtins__["__addhack_decorated"]:
        add_coroutine(x)
    __builtins__["__addhack_decorated"] = []

    
