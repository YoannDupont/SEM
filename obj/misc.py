def ranges_to_set(ranges, reference):
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
    reference : list
        the reference list. It is used in case of negative indexing.
    """
    length = len(reference)
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
    
    if 0 not in result: result.add(0)
    
    return result
