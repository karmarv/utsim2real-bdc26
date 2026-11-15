#!/usr/bin/env bash
# Release 10.5 record Section 11 (the entrant, Nov 15: "wait for the efforts underway and then take the best"): when
# L14's build ends, L15 = the better parent (L14 if its upload rule passed, else L12e) + the wave-3 two-draw bags that
# pass their member checks against the incumbent bags (s10_5_iter.sh: bags built in place, then addmember).
#   bash common/pipeline/launch.sh <run> l15 common/pipeline/s10_5_chain.sh <run>
RUN=$1
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
cd "$REPO"; E=$RUN/events.txt
st() { ev "S10-5 lumpi routed-s10-5-l15: $*"; }
st "armed: waits for L14's build to end, then L15 = the better of L14 / L12e + the passing wave-3 bags"
until grep -qE "routed-s10-5-l14: DONE$" "$E"; do sleep 120; done
if grep -qE "routed-s10-5-l14: UPLOAD RULE: PASS" "$E"; then P=routed-s10-5-l14; else P=routed-s10-5-l12e; fi
Z=$(ls "$REPO"/model-lumpi-track/$P/submissions/*/lumpi_*_submission.zip | tail -n 1)
st "parent $P ($Z)"
bash "$REPO/common/pipeline/s10_5_iter.sh" "$RUN" "$P" routed-s10-5-l15 L15 "$Z" routed-s10-4-l8 \
  bpvrospyr6x:bag-pvrcnnpp-ros-pyr-g1v6x:bag-pvrcnnpp-ros-g1v6x bvrrosnpyr6x:bag-voxelrcnn-rosn-pyr-g1v6x:bag-voxelrcnn-rosn-g1v6x
