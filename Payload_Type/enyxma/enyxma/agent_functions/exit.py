import logging
from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
from enyxma.WebshellRPC import WebshellRPC

logger = logging.getLogger(__name__)

class ExitArguments(TaskArguments):
    """
    No arguments are needed for the exit command.
    """
    def __init__(self, command_line: str = "", **kwargs):
        super().__init__(command_line, **kwargs)
        # no args
        self.args = []

    async def parse_arguments(self):
        # nothing to parse
        pass

class ExitCommand(CommandBase):
    cmd = "exit"
    needs_admin = False
    help_cmd = "exit"
    description = "Terminate the remote webshell file and remove the callback from Mythic"
    version = 1
    author = "@Termindiego25"
    argument_class = ExitArguments
    # This makes the command show up as a builtin on the callback table
    supported_ui_features = ["callback_table:exit"]
    is_exit = True
    attackmapping = ["T1070.004", "T1071.001", "T1132.001"]
    attributes = CommandAttributes(
        builtin=True
    )

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        """
        Send the 'exit' command to the webshell to delete itself and tell Mythic to remove the callback.
        """
        # Build the response to Mythic so that it knows the task succeeded
        response = PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=True,
            Completed=True
        )

        # Prepare the payload: simply 'exit'
        payload = "exit"
        logger.info(f"[exit] sending payload: {payload}")

        try:
            # Choose GET or POST based on C2 profile
            method = taskData.C2Profiles[0].Parameters.get("request_type", "POST").upper()
            if method == "GET":
                await WebshellRPC.GetRequest(
                    taskData.Payload.UUID,
                    payload.encode("UTF-8"),
                    taskData
                )
            else:
                await WebshellRPC.PostRequest(
                    taskData.Payload.UUID,
                    payload.encode("UTF-8"),
                    taskData
                )
        except Exception as e:
            # If it fails, still complete but log the error back in UI
            err = f"[exit] error sending exit: {e}"
            logger.exception(err)
            
        # emit the standard exit artifact that Mythic’s UI watches for
        await SendMythicRPCArtifactCreate(
            MythicRPCArtifactCreateMessage(
                TaskID=taskData.Task.ID,
                ArtifactMessage="$.NSApplication.sharedApplication.terminate",
                BaseArtifactType="API"
            )
        )
        return response

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        # no further processing required
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)