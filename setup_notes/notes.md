# Openpilot Setup Notes

This file contains my notes for my attempts to setup OpenPilot.

## Attempt 6

```{bash}
git clone https://github.com/commaai/openpilot.git
cd openpilot
conda create -n openpilot6 python=3.12 -y
conda activate openpilot6
tools/op.sh setup
.venv/bin/activate
scons -u -j$(nproc)
./tools/replay/replay --demo
./tools/replay/replay d34c14daa88a1e86/0000013e--0859dd3dcc
./tools/replay/replay "d34c14daa88a1e86/0000013e--0859dd3dcc"
```

After doing this, it seems the replay system is not able to load the files correctly. I get this:

╰─❯❯❯ ./tools/replay/replay "d34c14daa88a1e86/0000013e--0859dd3dcc"
active services: accelerometer, alertDebug, androidLog, audioFeedback, cameraOdometry, can, carControl, carOutput, carParams, carState, clocks, controlsState, customReservedRawData0, customReservedRawData1, customReservedRawData2, deviceState, driverAssistance, driverCameraState, driverEncodeData, driverEncodeIdx, driverMonitoringState, driverStateV2, drivingModelData, errorLogMessage, gnssMeasurements, gpsLocation, gpsLocationExternal, gpsNMEA, gyroscope, lightSensor, liveCalibration, liveDelay, liveParameters, livePose, liveTorqueParameters, liveTracks, livestreamDriverEncodeData, livestreamDriverEncodeIdx, livestreamRoadEncodeData, livestreamRoadEncodeIdx, livestreamWideRoadEncodeData, livestreamWideRoadEncodeIdx, logMessage, longitudinalPlan, magnetometer, managerState, modelV2, navInstruction, navRoute, navThumbnail, onroadEvents, pandaStates, peripheralState, procLog, qRoadEncodeData, qRoadEncodeIdx, qcomGnss, radarState, rawAudioData, roadCameraState, roadEncodeData, roadEncodeIdx, selfdriveState, sendcan, soundPressure, temperatureSensor, testJoystick, thumbnail, touch, ubloxGnss, ubloxRaw, uploaderState, wideRoadCameraState, wideRoadEncodeData, wideRoadEncodeIdx
loading route 
no valid segments in route: d34c14daa88a1e86|0000013e--0859dd3dcc

## Attempt 7

```{bash}
git clone --filter=blob:none --recurse-submodules --also-filter-submodules https://github.com/commaai/openpilot.git
cd openpilot
git checkout v0.9.8
git lfs pull
conda create -n openpilot7 python=3.12 -y
tools/op.sh setup # this errors due to a hash mismatch
uv lock --refresh
tools/op.sh setup # now it works
source .venv/bin/activate
scons -u -j$(nproc)
```

*WORKS*


git update-index --chmod=+x scripts/setup-openpilot.sh