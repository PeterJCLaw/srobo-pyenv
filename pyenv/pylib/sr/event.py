"Event handling stuff"
import collections

def wait_for_named( **named ):
    C = collections.namedtuple( "WaitResults", named.keys )

    happened = False
    while not happened:
        res = {}
        for name, poll in named.iteritems():
            happened, val = poll.eval()

            if happened:
                res[name] = val
                break
            else:
                res[name] = None

    # Set the remaining values to None:
    for name in named.keys():
        if name not in res:
            res[name] = None

    return C(**res)

def wait_for( *polls, **named ):
    "Wait for at least one of the passed polls to happen"

    if len(named):
        if len(polls):
            raise Exception("wait_for supplied with both normal and keyword arguments")
        return wait_for_named( **named )

    happened = False
    while not happened:
        res = []

        for poll in polls:
            happened, val = poll.eval()

            if happened:
                res.append(val)
                break
            else:
                res.append(None)

    # bulk the results up to be the right length:
    res += [None] * (len(polls) - len(res))

    return tuple(res)
