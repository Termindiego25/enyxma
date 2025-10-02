# eNyxma Mythic Remote Webshell Payload

A lightweight PHP-based webshell payload for Mythic C2, offering a suite of file‑and‑shell commands over HTTP(S). Designed for quick deployment and easy extension.

---

## 📖 Overview

**eNyxma** lets you execute commands, transfer files, and browse remote directories on a compromised server via a Mythic callback.  
Key components:

- **Payload**: `enyxma.php` (PHP script deployed on target)
- **Mythic Plugin**: Python code under `commands/*.py`
- **WebshellRPC**: Handles GET/POST transport, Base64‑encoded JSON I/O, error handling

---

## ⚙️ Prerequisites

- **Target**: PHP ≥ 7.0 with `shell_exec()`, `file_get_contents()`, `scandir()`, `stat()`, etc.
- **Mythic Server**: Python 3.8+, Mythic v2.x
- **Network**: HTTP(S) connectivity between Mythic server and the payload URL

---

## 🚀 Installation

1. **Install the agent**  
   Install the agent on your Mythic instance:
   ```bash
   ./mythic-cli install github https://github.com/Termindiego25/enyxma
   ```
2. **Create a callback**
   Go to `Payloads > Actions > Generate a new payload` and configure the parameters, including enyxma_c2p C2 profile.
3. **Deploy** the generated payload on the target.
4. **Run Commands**:
   ```shell
   # Example commands
   checkin
   shell whoami
   list /var/www/html
   download /etc/passwd
   upload
   exit
   ```

---

## ⚙️ Configuration

The available C2 Profile parameters in the Mythic UI are the following:

| Parameter         | Description                                                                        | Example                           |
| ----------------- | ---------------------------------------------------------------------------------- | --------------------------------- |
| **request_type**  | Choose the request method to use for communication with the webshell (GET or POST) | `POST`                            |
| **cookie_name**   | Cookie name for authentication to webshell                                         | `session`                         |
| **query_param**   | Query parameter for paayload requests                                              | `id`                              |
| **URL**           | Full URL to the payload on the target                                              | `https:/example.com/enyxma.php`   |
| **user_agent**    | HTTP User‑Agent header                                                             | `Mozilla/5.0 (Windows NT 10.0…)`  |

---

## 📚 Supported Commands

| Command      | Description                                                                                                | Usage                                  |
|--------------|------------------------------------------------------------------------------------------------------------|----------------------------------------|
| **append**   | Append data to a file on the remote webshell.<br>⚠️ Intended for small payloads (a few KB).                | `append [<remote_path> <file_id>]`     |
| **checkin**  | Gather system information (IP, OS, user, host, domain, PID, arch).                                         | `checkin`                              |
| **create**   | Create a new, empty file at the specified path on the remote system.                                       | `create <file_path>`                   |
| **delete**   | Delete a file at the specified path on the remote system.                                                  | `delete <file_path>`                   |
| **download** | Download a file from the remote system to the Mythic server using the webshell’s native functions.         | `download <file_path>`                 |
| **exit**     | Terminate the remote webshell session and remove the callback from Mythic.                                 | `exit`                                 |
| **list**     | List files and directories at the given path on the remote system (defaults to CWD).                       | `list [directory_path]`                |
| **mkdir**    | Create a new directory at the specified path on the remote system.                                         | `mkdir <directory_path>`               |
| **pwd**      | Display the current working directory on the remote system.                                                | `pwd`                                  |
| **read**     | Read and return the contents of a file on the remote system.                                               | `read <file_path>`                     |
| **rmdir**    | Delete a directory and all its contents at the specified path on the remote system.                        | `rmdir <directory_path>`               |
| **shell**    | Execute arbitrary shell commands on the remote webshell.                                                   | `shell <command> [arguments]`          |
| **upload**   | Upload a local file to the remote webshell.<br>⚠️ Intended for small files (up to a few KB).               | `upload [<remote_path> <file_id>]`     |
| **whoami**   | Show the username under which the agent is running on the remote system.                                   | `whoami`                               |
| **write**    | Overwrite a file on the remote webshell with provided text.<br>⚠️ Intended for small payloads (a few KB).  | `write [<file_path> <text>]`           |

---

## 🐞 Debugging & Logging

- **Mythic Container Logs**: `$ docker logs enyxma`  
- **Python Plugin**: configure `LOG_LEVEL=DEBUG` in your Mythic environment  
- **Payload PHP**: errors returned as HTTP 204 or JSON `{"error":"..."}`  

---

## 🧩 Extending & Development

1. **Add a new command**:  
   - Create `agent_functions/commands/<cmd>.py` with `TaskArguments`, `create_go_tasking()`, `process_response()`.  
   - Update `agent_code/enyxma.php` with corresponding `process_<cmd>()` function and add it to the switch-case.  
   - Add MITRE mapping and browser_script if UI integration is desired.
2. **Test locally** with `pytest` or by curling your local PHP server.

---

## 🤝 Contributing

1. Fork this repo  
2. Create a feature branch  
3. Write tests and documentation  
4. Submit a PR  

Please follow **PEP8** and comment in **English**.

---

## 📜 License

Distributed under the **GPL-3.0 license**. See [LICENSE](LICENSE) for details. 

---

## 👨‍💻 Author

Developed by **[Termindiego25](https://www.diegosr.es)** as part of the **Master’s Thesis** of my **Master's Degree in Cybersecurity and Cyberintelligence**.
