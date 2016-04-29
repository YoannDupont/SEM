class Segmentation(object):
    """
    Segmentation is just a holder for bounds. Those bounds can be word
    bounds or sentence bounds for example.
    By itself, it is not very useful, it become good in the context of
    a document for which it hold minimum useful information
    """
    def __init__(self, bounds):
        self._bounds = []
    
    @property
    def bounds(self):
        return self._bounds
