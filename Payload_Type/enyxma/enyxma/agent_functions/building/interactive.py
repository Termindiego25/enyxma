# commands/interactive.py
import base64
from mythic_container.MythicCommandBase import (
    CommandBase,
    TaskArguments,
    PTTaskMessageAllData,
    PTTaskCreateTaskingMessageResponse,
    PTTaskProcessResponseMessageResponse,
    CommandAttributes,
)

class InteractiveArguments(TaskArguments):
    async def parse_arguments(self):
        # no tenemos argumentos “tradicionales”
        pass

class InteractiveCommand(CommandBase):
    cmd                  = "interactive"
    needs_admin          = False
    help_cmd             = "interactive"
    description          = "Shell interactiva ficticia – siempre responde 'recibido'"
    version              = 0
    author               = "@Termindiego25"
    argument_class       = InteractiveArguments
    attributes           = CommandAttributes(
        supported_ui_features=["task_response:interactive"]
    )

    async def create_tasking(self, taskData: PTTaskMessageAllData):
        # con esto le decimos a Mythic “abre el prompt interactivo”
        taskData.args.set_manual_args("")
        return PTTaskCreateTaskingMessageResponse(
            TaskID    = taskData.Task.ID,
            Success   = True,
            Completed = False,        # ojo, sin cerrarlo
        )

    async def process_response(self, taskMsg, response: str):
        # response viene con lo que teclea el operador
        # pero aquí siempre devolvemos “recibido\n”
        payload = {
            "task_id"     : taskMsg.Task.ID,
            "data"        : base64.b64encode(b"recibido\n").decode(),
            "message_type": 1,       # Output
        }
        resp = PTTaskProcessResponseMessageResponse(
            TaskID  = taskMsg.Task.ID,
            Success = True,
        )
        # el cliente corregido inyecta esto en el JSON de vuelta
        resp.interactive = [payload]
        return resp
