import cereal.messaging as messaging

sm = messaging.SubMaster(["liveLocationKalmanDEPRECATED"])


while True:
    sm.update(0)
    g = sm["liveLocationKalmanDEPRECATED"]
    print(g)
    print(sm)
