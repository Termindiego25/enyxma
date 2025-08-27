function(task, responses) {
    // Check if the task has encountered an error.
    if(task.status.includes("error")) {
        // If an error occurred, combine all response messages into a single plain text output.
        const combined = responses.reduce((prev, cur) => prev + cur, "");
        return { 'plaintext': combined };
    }
    // If the task has completed successfully
    else if(task.completed) {
        // Check if there are any responses from the agent.
        if(responses.length > 0) {
            try {
                // We expect the response to have a specific format:
                //   - First line: "Successfully downloaded file <filename>"
                //   - Second line: "FileID: <agent_file_id>"
                // Split the response into lines.
                let lines = responses[0].split("\n");
                // Extract the filename from the first line.
                let filename = lines[0].split("Successfully downloaded file ")[1];
                // Extract the file ID from the second line.
                let agentFileId = lines[1].split("FileID: ")[1];

                // Return the formatted media object for the Mythic UI.
                return {
                    "media": [{
                        "filename": filename,
                        "agent_file_id": agentFileId,
                    }]
                };
            } catch(error) {
                // If parsing the response fails, combine all responses into plain text.
                const combined = responses.reduce((prev, cur) => prev + cur, "");
                return { 'plaintext': combined };
            }
        }
        else if(responses.status == 204) {
            return { "plaintext": "The file was not found, check if the path is valid." };
        }
        else {
            // If there are no responses, return a message stating that no data is available.
            return { "plaintext": "No data available from the agent." };
        }
    }
    // If the task has not yet completed, indicate that no response has been received.
    else {
        return { "plaintext": "Task is still in progress; no response received yet." };
    }
}