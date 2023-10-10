# TODO: Deprecate


def get_dimension_match(haystack, needle_map, default_value=""):
    """
    Searches a string for the first key with all values matching the haystack
    """

    dimension_value = default_value

    for key, needles in needle_map.iteritems():
        if len(needles) == 0:
            continue
        
        match = True
        
        for needle in needles:
            if needle not in haystack:
                match = False
                break

        if match:
            dimension_value = key
            break

    return dimension_value

