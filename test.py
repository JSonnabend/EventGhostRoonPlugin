import sys
sys.path.insert(0, './plugins/Roon')
import roonapi
import discovery

_appinfo = {
    "extension_id": "sonnabend.roon.eventghostplugin",
    "display_name": "Roon Eventghost Plugin",
    "display_version": "0.1",
    "publisher": "sonnabend",
    "email": "",
}
def authorize(event):
    print('in {} with event {}'.format(sys._getframe().f_code.co_name, event))
    import discovery
    print("discovering servers")
    discover = discovery.RoonDiscovery(None)
    servers = discover.all()
    print("discover: %s\nservers: %s" % (discover, servers))

    print("Shutdown discovery")
    discover.stop()

    print("Found the following servers")
    print(servers)
    apis = []
    for server in servers:
        apis.append(roonapi.RoonApi(_appinfo, None, server[0], server[1], False))
    print(apis)

    auth_api = []
    # while len(auth_api) == 0:
    #     print("Waiting for authorisation")
    #     time.sleep(1)
    #     auth_api = [api for api in apis if api.token is not None]
    #
    # api = auth_api[0]
    #
    # print("Got authorisation\n\t\thost ip: {}\
    #                   \n\t\tcore name: {}\n\t\tcore id: {}\
    #                   \n\t\ttoken: {}".format(api.host, api.core_name, api.core_id, api.token))
    # # This is what we need to reconnect
    # self.settings["core_id"] = api.core_id
    # self.settings["token"] = api.token
    #
    # # print("leaving authorize with settings: {self.settings}")
    #
    # print("Shutdown apis")
    # for api in apis:
    #     api.stop()

if __name__ == "__main__":
    authorize('info')
