"Event handling stuff"

def wait_for( *polls ):
    "Wait for at least one of the passed polls to happen"

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
