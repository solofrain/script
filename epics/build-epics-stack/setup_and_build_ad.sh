#!/usr/bin/env bash
set -e

# -------------------------------
# User configuration
# -------------------------------
EPICS_BASE=/epics/base
MODULES_DIR=/epics/modules

EPICS_BASE_REPO=https://github.com/epics-base/epics-base.git
EPICS_BASE_TAG=R7.0.8   # adjust if needed

SYNAPPS_CONFIG_REPO=https://github.com/EPICS-synApps/configure.git
SYNAPPS_TAG=master

declare -A REPO_MAP
REPO_MAP[ASYN]="https://github.com/epics-modules/asyn.git"
REPO_MAP[ADCORE]="https://github.com/areaDetector/ADCore.git"

# -------------------------------
# Step 0: Setup EPICS base
# -------------------------------
echo "Setting up EPICS base..."

if [ ! -d "$EPICS_BASE" ]; then
  echo "Cloning EPICS base..."
  git clone --depth 1 --branch $EPICS_BASE_TAG $EPICS_BASE_REPO $EPICS_BASE
else
  echo "EPICS base already exists"
fi

if [ ! -f "$EPICS_BASE/configure/RULES_TOP" ]; then
  echo "ERROR: Invalid EPICS base at $EPICS_BASE"
  exit 1
fi

if [ ! -d "$EPICS_BASE/lib" ]; then
  echo "Building EPICS base..."
  make -C $EPICS_BASE -j$(nproc)
else
  echo "EPICS base already built"
fi

# -------------------------------
# Step 1: Install libtirpc
# -------------------------------
if [ ! -f /usr/include/tirpc/rpc/rpc.h ]; then
  echo "Installing libtirpc..."
  if command -v apt >/dev/null; then
    sudo apt update && sudo apt install -y libtirpc-dev
  elif command -v dnf >/dev/null; then
    sudo dnf install -y libtirpc-devel
  elif command -v yum >/dev/null; then
    sudo yum install -y libtirpc-devel
  else
    echo "ERROR: Unsupported package manager"
    exit 1
  fi
fi

# -------------------------------
# Step 2: synApps configure
# -------------------------------
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

git clone --depth 1 ${SYNAPPS_CONFIG_REPO} ${TMP_DIR}/configure
RELEASE_FILE="${TMP_DIR}/configure/RELEASE"

strip_var_prefix() { echo "$1" | sed -E 's/\$\([A-Z_]+\)\///g'; }
extract_version() { echo "$1" | sed -E 's/^[^-]+-//'; }

ASYN_VER=$(extract_version "$(strip_var_prefix "$(grep '^ASYN=' $RELEASE_FILE | cut -d= -f2)")")
AD_VER=$(extract_version "$(strip_var_prefix "$(grep '^AREA_DETECTOR=' $RELEASE_FILE | cut -d= -f2)")")

echo "ASYN=$ASYN_VER"
echo "ADCore=$AD_VER"

# -------------------------------
# Step 3: Clone modules
# -------------------------------
mkdir -p ${MODULES_DIR}

clone_module() {
  NAME=$1
  URL=$2
  TAG=$3

  if [ ! -d "${MODULES_DIR}/$NAME" ]; then
    echo "Cloning $NAME ($TAG)..."
    git clone --depth 1 --branch $TAG $URL ${MODULES_DIR}/$NAME
  else
    echo "$NAME already exists"
  fi
}

clone_module asyn ${REPO_MAP[ASYN]} ${ASYN_VER}
clone_module ADCore ${REPO_MAP[ADCORE]} ${AD_VER}

# -------------------------------
# Step 4: Disable asyn test apps
# -------------------------------
echo "Disabling asyn test apps..."
ASYN_TOP_MK=${MODULES_DIR}/asyn/Makefile
sed -i '/test.*App/d' $ASYN_TOP_MK

# -------------------------------
# Step 5: Configure TIRPC
# -------------------------------
ASYN_CONFIG=${MODULES_DIR}/asyn/configure/CONFIG_SITE
touch $ASYN_CONFIG

cat >> $ASYN_CONFIG <<EOF
USR_CPPFLAGS += -I/usr/include/tirpc
USR_SYS_LIBS += tirpc
EOF

# -------------------------------
# Step 6: RELEASE.local
# -------------------------------
cat > ${MODULES_DIR}/RELEASE.local <<EOF
EPICS_BASE=${EPICS_BASE}
ASYN=${MODULES_DIR}/asyn
ADCORE=${MODULES_DIR}/ADCore
EOF

for m in ${MODULES_DIR}/*; do
  [ -d "$m/configure" ] && cp ${MODULES_DIR}/RELEASE.local $m/configure/RELEASE.local
done

# -------------------------------
# Step 7: Trim ADCore
# -------------------------------
sed -i 's/^DIRS += ADApp\/plugin/#&/' ${MODULES_DIR}/ADCore/Makefile || true
sed -i 's/^DIRS += ADApp\/iocBoot/#&/' ${MODULES_DIR}/ADCore/Makefile || true

# -------------------------------
# Step 8: Clean
# -------------------------------
make -C ${MODULES_DIR}/asyn clean || true
make -C ${MODULES_DIR}/ADCore clean || true

# -------------------------------
# Step 9: Build
# -------------------------------
echo "Building asyn..."
make -C ${MODULES_DIR}/asyn -j$(nproc)
make -C ${MODULES_DIR}/asyn

echo "Building ADCore..."
make -C ${MODULES_DIR}/ADCore -j$(nproc)
make -C ${MODULES_DIR}/ADCore

echo "Build complete."
