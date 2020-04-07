class epics_module:
    def __init__(self):
        self.name = ''
        self.version = ''
        self.mandatory = []
        self.optional = []

# AREADETECTOR
areaDetector = epics_module()
areaDetector.name = 'areaDetector'
areaDetector.mandatory = [ 'asyn',
                           'busy',
                           'calc',
                           'sscan',
                           'autosave' ]
areaDetector.base = [ 'ADCore',
                      'ADSupport' ]
                      

# ASYN
asyn = epics_module()
asyn.name = 'asyn'

# IOCSTATS
iocStats = epics_module()
iocStats.name = 'iocStats'

# QUADEM
quadEM = epics_module()
quadEM.name = 'quadEM'
quadEM.mandatory = [ 'asyn',
                     'ADCore',
                     'busy',
                     'ipUnidig',
                     'ipac',
                     'autosave',
                     'sscan',
                     'calc' ]

# SSCAN
sscan = epics_module()
sscan.name = 'sscan'

