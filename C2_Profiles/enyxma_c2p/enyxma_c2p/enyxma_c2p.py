from mythic_container.C2ProfileBase import *
from pathlib import Path

class Enyxma_C2P(C2Profile):
    name = "enyxma_c2p"
    description = "Enhanced C2 Profile for securely interacting with a remote webshell, through an encrypted P2P channel, eliminating the need for intermediary servers through either GET or POST requests."
    author = "@Termindiego25"
    is_p2p = True
    is_server_routed = False
    server_folder_path = Path(".") / "c2_code"
    server_binary_path = server_folder_path / "server.py"
    parameters = [
        C2ProfileParameter(name="user_agent",
                           description="User Agent",
                           default_value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"),
        C2ProfileParameter(name="cookie_name",
                           parameter_type=ParameterType.String,
                           description="Cookie name for authentication to webshell",
                           default_value="session", required=False),
        C2ProfileParameter(name="query_param",
                           parameter_type=ParameterType.String,
                           description="Query parameter for GET requests",
                           default_value="id", required=False),
        C2ProfileParameter(name="url",
                           parameter_type=ParameterType.String,
                           description="Remote URL to target where agent will live or redirector that will forward the message",
                           default_value="https://example.com/webshell.php", required=True),
        C2ProfileParameter(name="request_type",
                           parameter_type=ParameterType.ChooseOne,
                           description="Choose the request method to use for communication with the webshell (GET or POST)",
                           default_value="POST", 
                           choices=["GET", "POST"], required=False),
    ]

    async def config_check(self, inputMsg: C2ConfigCheckMessage) -> C2ConfigCheckMessageResponse:
        try:
            return C2ConfigCheckMessageResponse(Success=True, Message="C2 Profile configuration is valid.")
        except Exception as e:
            return C2ConfigCheckMessageResponse(Success=False, Error=str(sys.exc_info()[-1].tb_lineno) + str(e))

    async def redirect_rules(self, inputMsg: C2GetRedirectorRulesMessage) -> C2GetRedirectorRulesMessageResponse:
        """Generate Apache ModRewrite rules if needed."""
        return C2GetRedirectorRulesMessageResponse(Success=True, Message="#Not Implemented")

    async def host_file(self, inputMsg: C2HostFileMessage) -> C2HostFileMessageResponse:
        """This P2P profile does not support file hosting."""
        response = C2HostFileMessageResponse(Success=False)
        try:
            response.Error = "Can't host files through a P2P profile"
        except Exception as e:
            response.Error = f"{e}"
        return response