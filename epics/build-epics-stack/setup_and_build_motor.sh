#!/usr/bin/env bash
set -e

# -------------------------------
# User configuration
# -------------------------------
EPICS_BASE=/epics/base
MODULES_DIR=/epics/modules

EPICS_BASE_REPO=https://github.com/epics-base/epics-base.git
EPICS_BASE_TAG=R7.0.8

SYNAPPS_CONFIG_REPO=https://github.com/EPICS-synApps/configure.git
SYNAPPS_TAG=master

declare -A REPO_MAP
REPO_MAP[ASYN]="https://github.com/epics-modules/asyn.git"
REPO_MAP[MOTOR]="https://github.com/epics-modules/motor.git"

# -------------------------------
# Step 0: EPICS base
# -------------------------------
if [ ! -d "$EPICS_BASE" ]; then
  git clone --depth 1 --branch $EPICS_BASE_TAG $EPICS_BASE_REPO $EPICS_BASE
fi

if [ ! -f "$EPICS_BASE/configure/RULES_TOP" ]; then
  echo "Invalid EPICS base"
  exit 1
fi

if [ ! -d "$EPICS_BASE/lib" ]; then
  make -C $EPICS_BASE -j$(nproc)
fi

# -------------------------------
# Step 1: libtirpc
# -------------------------------
if [ ! -f /usr/include/tirpc/rpc/rpc.h ]; then
  if command -v apt >/dev/null; then
    sudo apt update && sudo apt install -y libtirpc-dev
  elif command -v dnf >/dev/null; then
    sudo dnf install -y libtirpc-devel
  else
    echo "Install libtirpc manually"
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
MOTOR_VER=$(extract_version "$(strip_var_prefix "$(grep '^MOTOR=' $RELEASE_FILE | cut -d= -f2)")")

echo "ASYN=$ASYN_VER"
echo "MOTOR=$MOTOR_VER"

# -------------------------------
# Step 3: Clone modules
# -------------------------------
mkdir -p ${MODULES_DIR}

clone_module() {
  NAME=$1
  URL=$2
  TAG=$3

  if [ ! -d "${MODULES_DIR}/$NAME" ]; then
    git clone --depth 1 --branch $TAG $URL ${MODULES_DIR}/$NAME
  fi
}

clone_module asyn ${REPO_MAP[ASYN]} ${ASYN_VER}
clone_module motor ${REPO_MAP[MOTOR]} ${MOTOR_VER}

# -------------------------------
# Step 4: CLEAN motor/modules
# -------------------------------
echo "Cleaning motor/modules..."

MOTOR_MODULES_DIR=${MODULES_DIR}/motor/modules

if [ -d "$MOTOR_MODULES_DIR" ]; then
  # Remove all motor* directories
  find "$MOTOR_MODULES_DIR" -mindepth 1 -maxdepth 1 -type d -name "motor*" -exec rm -rf {} +

  MOTOR_MODULES_MK=${MOTOR_MODULES_DIR}/Makefile

  if [ -f "$MOTOR_MODULES_MK" ]; then
    # Remove SUBMODULES line entirely
    sed -i '/^SUBMODULES/d' $MOTOR_MODULES_MK

    # Remove conditional blocks (IPAC, MX, LUA)
    sed -i '/ifdef IPAC/,/endif/d' $MOTOR_MODULES_MK
    sed -i '/ifdef MX/,/endif/d' $MOTOR_MODULES_MK
    sed -i '/ifdef LUA/,/endif/d' $MOTOR_MODULES_MK
  fi
fi

# -------------------------------
# Step 5: Disable asyn test apps
# -------------------------------
sed -i '/test.*App/d' ${MODULES_DIR}/asyn/Makefile

# -------------------------------
# Step 6: Configure TIRPC
# -------------------------------
ASYN_CONFIG=${MODULES_DIR}/asyn/configure/CONFIG_SITE
touch $ASYN_CONFIG

cat >> $ASYN_CONFIG <<EOF
USR_CPPFLAGS += -I/usr/include/tirpc
USR_SYS_LIBS += tirpc
EOF

# -------------------------------
# Step 7: RELEASE.local
# -------------------------------
cat > ${MODULES_DIR}/RELEASE.local <<EOF
EPICS_BASE=${EPICS_BASE}
ASYN=${MODULES_DIR}/asyn
MOTOR=${MODULES_DIR}/motor
EOF

for m in ${MODULES_DIR}/*; do
  [ -d "$m/configure" ] && cp ${MODULES_DIR}/RELEASE.local $m/configure/RELEASE.local
done

# -------------------------------
# Step 8: Clean
# -------------------------------
make -C ${MODULES_DIR}/asyn clean || true
make -C ${MODULES_DIR}/motor clean || true

# -------------------------------
# Step 9: Build
# -------------------------------
make -C ${MODULES_DIR}/asyn -j$(nproc)
make -C ${MODULES_DIR}/asyn

make -C ${MODULES_DIR}/motor -j$(nproc)
make -C ${MODULES_DIR}/motor

echo "Motor minimal build complete."
