def ranges_to_set(ranges, length, include_zero=False):
    """
    Returns a set of integers based of ranges over a reference list. Ranges are
    inclusive both in the lower and upper bound, unlike in python where they are
    inclusive only in the lower but not the upper bound.
    
    Parameters
    ----------
    ranges : str
        a list of ranges represented by a string. Each range is comma separated.
        A range is a couple of integers colon separated.
        If the index 0 in not present in the list, it is automatically added.
    length : int
        the reference length to use in case of negative indexing.
    """
    result = set()
    
    for current_range in ranges.split(','):
        if ':' in current_range:
            lo, hi = [int(i) for i in current_range.split(":")]
        else:
            lo = int(current_range)
            hi = lo
        
        if (hi < lo): continue
        
        if lo < 0: lo = length + lo
        if hi < 0: hi = length + hi
        
        for i in xrange(lo, hi+1): result.add(i)
    
    if include_zero: result.add(0)
    
    return result

def to_dhms(laps):
    def add_time(s, laps, period, name):
        if laps > period:
            if period != 0:
                rem = laps % period
                if rem != 0:
                    l = (laps - rem) / period
                else:
                    l = laps / period
            else:
                rem = 0
                l   = laps
            if s == "":
                s = "%i %s%s" %(l, name, ("" if l == 1 else "s"))
            else:
                s += " %i %s%s" %(l, name, ("" if l == 1 else "s"))
            laps = rem
        elif laps == period:
            if period != 0:
                l = 1
                if s == "":
                    s = "%i %s%s" %(l, name, ("" if l == 1 else "s"))
                else:
                    s += " %i %s%s" %(l, name, ("" if l == 1 else "s"))
                laps = 0
        return (s, laps)
    
    sid = 86400 # seconds in a day
    sih = 3600  # seconds in a hour
    sim = 60    # seconds in a minute
    s   = ""
    
    s, laps = add_time(s, laps, sid, "day")
    s, laps = add_time(s, laps, sih, "hour")
    s, laps = add_time(s, laps, sim, "minute")
    s, laps = add_time(s, laps,   0, "second")
    
    return s

def last_index(s, e):
    if e in s:
        return len(s) - s[::-1].index(e[::-1]) - 1
    else:
        return -1