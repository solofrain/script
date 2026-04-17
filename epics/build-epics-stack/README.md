# EPICS Build Utilities

Makefile to build the EPICS module stack from source. Module versions are resolved automatically from the synApps `configure/RELEASE` file.

>`setup_and_build_ad.sh` and `setup_and_build_motor.sh` were previously used and were absorbed into the Makefile.

## Targets

| Target   | What it builds                              | Depends on         |
|----------|---------------------------------------------|--------------------|
| `base`   | EPICS base R7.0.10                          | —                  |
| `asyn`   | asyn (motor/detector communication)         | base               |
| `autosave` | autosave (PV save/restore)                | base               |
| `sscan`  | sscan (scan records, sseq/swait)            | base               |
| `calc`   | calc (transform, sCalcout records)          | sscan              |
| `busy`   | busy (busy record for sequencing)           | asyn, autosave     |
| `ad`     | ADCore (areaDetector framework + plugins)   | asyn, busy, sscan, calc, autosave |
| `motor`  | motor (stepper/servo support)               | asyn               |
| `clean`  | Remove all modules (`/epics/modules/`)      | —                  |

## Quick Start

```bash
# Build everything needed for the Germanium detector IOC
make ad

# Build motor support (independent of ad)
make motor
```

`make ad` builds the full dependency chain:

```
base ─┬─ asyn ─────┬─ busy ──┐
      ├─ autosave ──┘         ├─ ADCore (with HDF5)
      ├─ sscan ─── calc ─────┘
      └────────────────────────
```

## What `make ad` installs

### EPICS modules (under `/epics/modules/`)

| Module   | Version | Purpose                                    |
|----------|---------|--------------------------------------------|
| asyn     | (auto)  | Device communication layer                 |
| autosave | (auto)  | PV save/restore across IOC restarts        |
| busy     | (auto)  | Busy record for scan sequencing            |
| sscan    | (auto)  | Scan engine, sseq/swait record types       |
| calc     | (auto)  | Calculation records (calc, transform, sCalcout) |
| ADCore   | (auto)  | areaDetector core + NDArray plugin library |

### ADCore plugins built

| Plugin          | Description                                   |
|-----------------|-----------------------------------------------|
| NDStdArrays     | Expose NDArray data as waveform PVs via CA    |
| NDFileHDF5      | Write NDArrays to HDF5 files                 |
| NDStats         | Array statistics (min/max/mean/sigma/centroid)|
| NDTimeSeries    | Time-series of statistics values              |
| NDROI           | Extract rectangular sub-region                |
| NDROIStat       | Statistics on multiple ROIs                   |
| NDProcess       | Background subtraction, flat-field, filters   |
| NDFFT           | 1-D/2-D FFT                                  |
| NDOverlay       | Draw overlays on images                       |
| NDTransform     | Rotate/mirror/transpose                       |
| NDColorConvert  | Color space conversion                        |
| NDCircularBuff  | Pre/post-trigger circular buffer              |
| NDCodec         | Array compression (when libs available)       |
| NDGather        | Merge arrays from multiple sources            |
| NDScatter       | Round-robin distribution to outputs           |
| NDAttrPlot      | Live attribute plotting                       |
| NDPosPlugin     | Position-based frame matching                 |

### ADCore file plugins NOT built (disabled)

| Plugin          | Reason                    | Enable via                |
|-----------------|---------------------------|---------------------------|
| NDFileNetCDF    | Library not installed     | `WITH_NETCDF = YES`      |
| NDFileNexus     | Library not installed     | `WITH_NEXUS = YES`       |
| NDFileTIFF      | Library not installed     | `WITH_TIFF = YES`        |
| NDFileJPEG      | Library not installed     | `WITH_JPEG = YES`        |
| NDFileMagick    | Library not installed     | `WITH_GRAPHICSMAGICK = YES` |

To enable these, install the corresponding system library and set the
flag in `/epics/modules/ADCore/configure/CONFIG_SITE`.

### System packages installed automatically

| Package        | Required by  | Install check              |
|----------------|--------------|----------------------------|
| `libtirpc-dev` | asyn         | `/usr/include/tirpc/rpc/rpc.h` |
| `libhdf5-dev`  | ADCore HDF5  | `/usr/include/hdf5/serial/hdf5.h` |
| `libxml2-dev`  | ADCore XML parsing (`<libxml/parser.h>`) | `/usr/include/libxml2/libxml/parser.h` |

### Patches applied automatically

| Patch | Target | Reason |
|-------|--------|--------|
| `_FORTIFY_SOURCE=2` | EPICS base ≤ R7.0.8 | GCC 14 / Ubuntu 24.04 defaults to level 3, which misidentifies EPICS record-type upcasts as buffer overflows (fixed upstream in PR #517). Only applied when `EPICS_BASE_TAG` is R7.0.8 or earlier. |
| Add `#include <shareLib.h>` | sscan `saveData_writeXDR.c` | Uses `READONLY` macro which is no longer transitively included via `cadef.h` in EPICS base ≥ R7.0.9 |
| Remove `-DH5_NO_DEPRECATED_SYMBOLS` | ADCore pluginSrc | Conflicts with HDF5 ≥ 1.10 API version selection |
| Ubuntu HDF5 paths | ADCore CONFIG_SITE | Debian/Ubuntu puts HDF5 in `/usr/include/hdf5/serial/` |
| XML2 include path (`XML2_INCLUDE=/usr/include/libxml2`) and external linkage (`XML2_EXTERNAL=YES`) | ADCore CONFIG_SITE | Ensures ADCore sources that include `<libxml/parser.h>` resolve correctly on Debian/Ubuntu layouts |
