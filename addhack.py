# A horrible hack for adding new coroutines
# Getting different modules to talk about the same list
# was like pulling my eyes through a sieve.
# Unfortunately, I don't have enough time to learn about
# how Python things namespaces should work.
# Putting the list in it's own module works.

new_coroutines = []

def add_coroutine(f):
    new_coroutines.append( f() )
