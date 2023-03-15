import sys
import time, os
__file__ = sys.argv[0]

# path to roonapi folder
#sys.path.append('E:\\pyRoon\\pyRoonLib\\roonapi')
import roonapi, discovery, constants
import json
import socket
import subprocess, shlex

settings = None
dataFolder = None
dataFile = None
inDebugger = getattr(sys, 'gettrace', None)
appinfo = {
    "extension_id": "sonnabend.roon.eg",
    "display_name": "EG",
    "display_version": "1.0.0",
    "publisher": "sonnabend",
    "email": "",
}
roon = None


def main():
    try:
        global roon
        global settings
        loadSettings()
        # authorize if necessary
        try:
            if settings["core_id"].strip() == "" or settings["token"] == "":
                authorize()
        except:
            authorize()
        # connect to Roon core
        roon = connect(settings["core_id"], settings["token"])
        settings["core_id"] = roon.core_id
        settings["token"] = roon.token
        # subscribe to status notifications
        # roon.register_state_callback(state_change_callback)
        hostname = socket.gethostname()
        roon.register_volume_control("1", hostname, volume_control_callback, 0, "incremental")
        while True:
            time.sleep(0.1)
            pass

    finally:
        #finally, save settings
        if not (settings is None):
            saveSettings()

def connect(core_id, token):
    print("in connect\n  core_id: %s\n  token: %s" % (core_id,token))
    global appinfo
    try:
        discover = discovery.RoonDiscovery(core_id, sys.argv[0])
        print("discover object: %s" % discover)
        server = discover.first()
        print("server object: %s:%s" % (server[0], server[1]))
        roon = roonapi.RoonApi(appinfo, token, server[0], server[1], True)
        print("roon object: %s" % roon)
        return roon
    except:
        return None
    finally:
        discover.stop()

def authorize():
    print("authorizing")
    global appinfo
    global settings

    print("discovering servers")
    discover = discovery.RoonDiscovery(None)
    servers = discover.all()
    print("discover: %s\nservers: %s" % (discover, servers))

    print("Shutdown discovery")
    discover.stop()

    print("Found the following servers")
    print(servers)
    apis = [roonapi.RoonApi(appinfo, None, server[0], server[1], False) for server in servers]

    auth_api = []
    while len(auth_api) == 0:
        print("Waiting for authorisation")
        time.sleep(1)
        auth_api = [api for api in apis if api.token is not None]

    api = auth_api[0]

    print("Got authorisation")
    print("   host ip: " + api.host)
    print("   core name: " + api.core_name)
    print("   core id: " + api.core_id)
    print("   token: " + api.token)
    # This is what we need to reconnect
    settings["core_id"] = api.core_id
    settings["token"] = api.token

    print("leaving authorize with settings: %s" % settings)

    print("Shutdown apis")
    for api in apis:
        api.stop()


def state_change_callback(event, changed_ids):
    global roon
    """Call when something changes in roon."""
    print("\n-----")
    print("state_change_callback event:%s changed_ids: %s" % (event, changed_ids))
    print(" ")
    for zone_id in changed_ids:
        zone = roon.zones[zone_id]
        print("zone_id:%s zone_info: %s" % (zone_id, zone))

def volume_control_callback(control_key, event, value):
    global roon
    print("\n-----")
    print("volume_control_callback control_key: %s event: %s value: %s" % (control_key, event, value))
    command = None
    param = None
    if value == 1:
        command = settings["command_volume_up"]["command"]
        param = settings["command_volume_up"]["param"]
    elif value == -1:
        command = settings["command_volume_down"]["command"]
        param = settings["command_volume_down"]["param"]
    elif event == "set_mute":
        command = settings["command_volume_mute"]["command"]
        param = settings["command_volume_mute"]["param"]
    if not command == None:
        command = '"%s" %s' % (command,param)
        print("running command %s" % (command))
        try:
            subprocess.run(shlex.split(command))
        except:
            pass
    roon.update_volume_control(control_key, 0, False)


def loadSettings():
    global dataFolder
    global dataFile
    global settings
    print("running from %s" % __file__)
    # print(os.environ)
    if ("_" in __file__): # running in temp directory, so not from PyCharm
        dataFolder = os.path.join(os.getenv('APPDATA'), 'pyRoonEGVolume')  #os.path.abspath(os.path.dirname(__file__))
    else:
        dataFolder = os.path.dirname(__file__)
    dataFile = os.path.join(dataFolder , 'settings.dat')
    print("using dataFile: %s" % dataFile)
    if not os.path.isfile(dataFile):
        f = open(dataFile, 'a').close()
    try:
        f = open(dataFile, 'r')
        settings = json.load(f)
    except:
        settings = json.loads('{}')
    f.close()
    return settings

def saveSettings():
    global settings
    data = json.dumps(settings, indent=4)
    if (not data  == '{}') and (os.path.isfile(dataFile)):
        f = open(dataFile, 'w')
        f.write(data)
        f.close()

main()