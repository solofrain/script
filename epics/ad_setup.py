class epics_module:
    def __init__(self):
        self.name = ''
        self.version = ''
        self.mandatory = []
        self.optional = []
        self.base = []


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
                      

#========================================
AD_DIR=areaDetector-${ad_ver}
AREA_DETECTOR=${SUPPORT_DIR}/${AD_DIR}

git clone -b ${ad_ver} --recursive https://github.com/areaDetector/areaDetector.git areaDetector-${ad_ver}

cd ${AD_DIR}/configure
cp EXAMPLE_RELEASE.local         RELEASE.local
cp EXAMPLE_RELEASE_LIBS.local    RELEASE_LIBS.local
cp EXAMPLE_RELEASE_PRODS.local   RELEASE_PRODS.local
cp EXAMPLE_CONFIG_SITE.local     CONFIG_SITE.local

# Replace the definitions in RELEASE_LIBS.local

# Replace the definitions in RELEASE_PRODS.local

# Uncomment the modules to be built in RELEASE.local


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

