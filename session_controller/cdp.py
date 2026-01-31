"""
Chrome DevTools Protocol control for Session Desktop.

Requires Session to be running with --remote-debugging-port=9222

Requires: websocket-client or pyppeteer
Install: pip install websocket-client
"""

import json
import subprocess
import time
import platform
from typing import Optional, Any
from pathlib import Path


class SessionCDP:
    """
    Control Session Desktop via Chrome DevTools Protocol.

    Session must be started with remote debugging enabled:
        /Applications/Session.app/Contents/MacOS/Session --remote-debugging-port=9222

    Example:
        cdp = SessionCDP()
        cdp.connect()
        conversations = cdp.get_conversations()
        cdp.send_message("05abc123...", "Hello!")
    """

    DEFAULT_PORT = 9222

    def __init__(self, port: int = DEFAULT_PORT, host: str = "localhost"):
        self.port = port
        self.host = host
        self._ws = None
        self._message_id = 0

    @property
    def debug_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _get_websocket_url(self) -> str:
        """Get WebSocket debugger URL from Chrome DevTools."""
        import urllib.request

        try:
            with urllib.request.urlopen(f"{self.debug_url}/json") as response:
                pages = json.loads(response.read())
                # Find the main page (background.html)
                for page in pages:
                    if "background.html" in page.get("url", ""):
                        return page["webSocketDebuggerUrl"]
                # Fallback to first page
                if pages:
                    return pages[0]["webSocketDebuggerUrl"]
        except Exception as e:
            raise ConnectionError(
                f"Cannot connect to Session at {self.debug_url}. "
                f"Make sure Session is running with --remote-debugging-port={self.port}\n"
                f"Error: {e}"
            )

        raise ConnectionError("No debuggable pages found")

    def connect(self) -> None:
        """Connect to Session via WebSocket."""
        try:
            import websocket
        except ImportError:
            raise ImportError(
                "websocket-client not installed. Install with: pip install websocket-client"
            )

        ws_url = self._get_websocket_url()
        self._ws = websocket.create_connection(ws_url)
        self._message_id = 0

    def close(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            self._ws.close()
            self._ws = None

    def __enter__(self) -> "SessionCDP":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _send_command(self, method: str, params: Optional[dict] = None) -> dict:
        """Send a CDP command and wait for response."""
        if not self._ws:
            raise ConnectionError("Not connected. Call connect() first.")

        self._message_id += 1
        message = {"id": self._message_id, "method": method, "params": params or {}}

        self._ws.send(json.dumps(message))

        # Wait for response with matching ID
        while True:
            response = json.loads(self._ws.recv())
            if response.get("id") == self._message_id:
                if "error" in response:
                    raise RuntimeError(f"CDP error: {response['error']}")
                return response.get("result", {})

    def evaluate(self, expression: str) -> Any:
        """
        Evaluate JavaScript in the Session renderer context.

        Args:
            expression: JavaScript code to evaluate

        Returns:
            The result of the evaluation
        """
        result = self._send_command(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )

        if "exceptionDetails" in result:
            raise RuntimeError(f"JS error: {result['exceptionDetails']}")

        return result.get("result", {}).get("value")

    # === High-level API ===

    def get_conversations(self) -> list[dict]:
        """Get all conversations."""
        return self.evaluate("""
            (function() {
                const controller = window.getConversationController();
                return controller.getConversations().map(c => ({
                    id: c.id,
                    type: c.get('type'),
                    name: c.getNicknameOrRealUsernameOrPlaceholder ?
                          c.getNicknameOrRealUsernameOrPlaceholder() :
                          (c.get('nickname') || c.get('displayNameInProfile') || c.id.substring(0, 8)),
                    displayName: c.get('displayNameInProfile'),
                    nickname: c.get('nickname'),
                    lastMessage: c.get('lastMessage'),
                    activeAt: c.get('active_at'),
                    unreadCount: c.get('unreadCount') || 0
                }));
            })()
        """)

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get a specific conversation."""
        return self.evaluate(f"""
            (function() {{
                const c = window.getConversationController().get('{conversation_id}');
                if (!c) return null;
                return {{
                    id: c.id,
                    type: c.get('type'),
                    name: c.getNicknameOrRealUsernameOrPlaceholder ?
                          c.getNicknameOrRealUsernameOrPlaceholder() :
                          (c.get('nickname') || c.get('displayNameInProfile') || c.id.substring(0, 8)),
                    displayName: c.get('displayNameInProfile'),
                    nickname: c.get('nickname'),
                    lastMessage: c.get('lastMessage'),
                    activeAt: c.get('active_at'),
                    unreadCount: c.get('unreadCount') || 0
                }};
            }})()
        """)

    def send_message(self, conversation_id: str, body: str) -> bool:
        """
        Send a text message to a conversation.

        Args:
            conversation_id: The Session ID or group ID
            body: Message text

        Returns:
            True if message was sent successfully
        """
        # Escape the body for JS
        body_escaped = json.dumps(body)

        result = self.evaluate(f"""
            (async function() {{
                const convo = window.getConversationController().get('{conversation_id}');
                if (!convo) {{
                    throw new Error('Conversation not found');
                }}
                await convo.sendMessage({{ body: {body_escaped} }});
                return true;
            }})()
        """)
        return result is True

    def send_attachment(
        self, conversation_id: str, file_path: str, caption: Optional[str] = None
    ) -> bool:
        """
        Send a file attachment to a conversation.

        Note: This is more complex and may require additional setup.
        The file must be accessible to Session.
        """
        # This would require more complex handling through the staged attachments system
        raise NotImplementedError(
            "Attachment sending via CDP is complex. "
            "Consider using the database approach for reading attachments, "
            "or implement staged attachment handling."
        )

    def get_our_pubkey(self) -> str:
        """Get our own Session ID."""
        return self.evaluate("""
            window.textsecure.storage.user.getNumber()
        """) or self.evaluate("""
            require('./ts/session/utils').UserUtils.getOurPubKeyStrFromCache()
        """)

    def get_redux_state(self) -> dict:
        """Get the full Redux store state."""
        return self.evaluate("""
            window.inboxStore.getState()
        """)

    def mark_conversation_read(self, conversation_id: str) -> bool:
        """Mark all messages in a conversation as read."""
        return self.evaluate(f"""
            (async function() {{
                const convo = window.getConversationController().get('{conversation_id}');
                if (!convo) return false;
                await convo.markAllAsRead();
                return true;
            }})()
        """)

    def accept_request(self, request_id: str) -> bool:
        """
        Accept a pending request (contact or message request).

        Args:
            request_id: The Session ID or conversation ID to accept

        Returns:
            True if request was accepted successfully
        """
        result = self.evaluate(f"""
            (async function() {{
                const controller = window.getConversationController();
                const convo = controller.get('{request_id}');
                if (!convo) {{
                    throw new Error('Conversation not found');
                }}
                // Accept the request using conversation controller
                await controller.acceptPendingConversation('{request_id}');
                return true;
            }})()
        """)
        return result is True

    def decline_request(self, request_id: str) -> bool:
        """
        Decline a pending request without blocking.

        Args:
            request_id: The Session ID or conversation ID to decline

        Returns:
            True if request was declined successfully
        """
        result = self.evaluate(f"""
            (async function() {{
                const controller = window.getConversationController();
                const convo = controller.get('{request_id}');
                if (!convo) {{
                    throw new Error('Conversation not found');
                }}
                // Delete the conversation without blocking
                await controller.deleteConversation('{request_id}', false);
                return true;
            }})()
        """)
        return result is True

    def block_request(self, request_id: str) -> bool:
        """
        Decline a pending request and block the sender.

        Args:
            request_id: The Session ID or conversation ID to block

        Returns:
            True if sender was blocked successfully
        """
        result = self.evaluate(f"""
            (async function() {{
                const controller = window.getConversationController();
                const convo = controller.get('{request_id}');
                if (!convo) {{
                    throw new Error('Conversation not found');
                }}
                // Delete and block the conversation
                await controller.deleteConversation('{request_id}', true);
                return true;
            }})()
        """)
        return result is True

    # === Group Management ===

    def _get_our_session_id_js(self) -> str:
        """Return JavaScript snippet to get our Session ID safely."""
        return """
            (function() {
                try {
                    if (window.textsecure && window.textsecure.storage && window.textsecure.storage.user) {
                        return window.textsecure.storage.user.getNumber();
                    }
                } catch(e) {}
                try {
                    const state = window.inboxStore.getState();
                    if (state && state.user && state.user.ourNumber) {
                        return state.user.ourNumber;
                    }
                } catch(e) {}
                try {
                    return require('./ts/session/utils').UserUtils.getOurPubKeyStrFromCache();
                } catch(e) {}
                return null;
            })()
        """

    def get_group_members(self, group_id: str) -> Optional[dict]:
        """
        Get members and admins of a group.

        Args:
            group_id: The group conversation ID

        Returns:
            Dict with 'members' and 'admins' lists, or None if not a group
        """
        return self.evaluate(f"""
            (function() {{
                const convo = window.getConversationController().get('{group_id}');
                if (!convo) return null;
                const type = convo.get('type');
                if (type !== 'group' && type !== 'groupv2') return null;

                // Get our Session ID safely
                let ourId = null;
                try {{
                    if (window.textsecure && window.textsecure.storage && window.textsecure.storage.user) {{
                        ourId = window.textsecure.storage.user.getNumber();
                    }}
                }} catch(e) {{}}
                if (!ourId) {{
                    try {{
                        const state = window.inboxStore.getState();
                        if (state && state.user && state.user.ourNumber) {{
                            ourId = state.user.ourNumber;
                        }}
                    }} catch(e) {{}}
                }}

                const admins = convo.get('groupAdmins') || [];
                return {{
                    id: convo.id,
                    name: convo.get('displayNameInProfile') || convo.get('name') || 'Unknown Group',
                    type: type,
                    members: convo.get('members') || [],
                    admins: admins,
                    weAreAdmin: ourId ? admins.includes(ourId) : false
                }};
            }})()
        """)

    def add_group_member(self, group_id: str, session_id: str) -> bool:
        """
        Add a member to a group.

        Args:
            group_id: The group conversation ID
            session_id: Session ID of the user to add

        Returns:
            True if member was added successfully
        """
        result = self.evaluate(f"""
            (async function() {{
                const convo = window.getConversationController().get('{group_id}');
                if (!convo) throw new Error('Group not found');
                const type = convo.get('type');
                if (type !== 'group' && type !== 'groupv2') throw new Error('Not a group');

                // Get our Session ID safely
                let ourId = null;
                try {{
                    if (window.textsecure && window.textsecure.storage && window.textsecure.storage.user) {{
                        ourId = window.textsecure.storage.user.getNumber();
                    }}
                }} catch(e) {{}}
                if (!ourId) {{
                    try {{
                        const state = window.inboxStore.getState();
                        if (state && state.user && state.user.ourNumber) {{
                            ourId = state.user.ourNumber;
                        }}
                    }} catch(e) {{}}
                }}

                // Check if we're admin
                const admins = convo.get('groupAdmins') || [];
                if (!ourId || !admins.includes(ourId)) throw new Error('You must be an admin to add members');

                // Add the member
                const members = convo.get('members') || [];
                if (members.includes('{session_id}')) throw new Error('User is already a member');

                await convo.addMembers(['{session_id}']);
                return true;
            }})()
        """)
        return result is True

    def remove_group_member(self, group_id: str, session_id: str) -> bool:
        """
        Remove a member from a group.

        Args:
            group_id: The group conversation ID
            session_id: Session ID of the user to remove

        Returns:
            True if member was removed successfully
        """
        result = self.evaluate(f"""
            (async function() {{
                const convo = window.getConversationController().get('{group_id}');
                if (!convo) throw new Error('Group not found');
                const type = convo.get('type');
                if (type !== 'group' && type !== 'groupv2') throw new Error('Not a group');

                // Get our Session ID safely
                let ourId = null;
                try {{
                    if (window.textsecure && window.textsecure.storage && window.textsecure.storage.user) {{
                        ourId = window.textsecure.storage.user.getNumber();
                    }}
                }} catch(e) {{}}
                if (!ourId) {{
                    try {{
                        const state = window.inboxStore.getState();
                        if (state && state.user && state.user.ourNumber) {{
                            ourId = state.user.ourNumber;
                        }}
                    }} catch(e) {{}}
                }}

                // Check if we're admin
                const admins = convo.get('groupAdmins') || [];
                if (!ourId || !admins.includes(ourId)) throw new Error('You must be an admin to remove members');

                await convo.removeMembers(['{session_id}']);
                return true;
            }})()
        """)
        return result is True

    def promote_to_admin(self, group_id: str, session_id: str) -> bool:
        """
        Promote a member to admin.

        Args:
            group_id: The group conversation ID
            session_id: Session ID of the user to promote

        Returns:
            True if member was promoted successfully
        """
        result = self.evaluate(f"""
            (async function() {{
                const convo = window.getConversationController().get('{group_id}');
                if (!convo) throw new Error('Group not found');
                const type = convo.get('type');
                if (type !== 'group' && type !== 'groupv2') throw new Error('Not a group');

                // Get our Session ID safely
                let ourId = null;
                try {{
                    if (window.textsecure && window.textsecure.storage && window.textsecure.storage.user) {{
                        ourId = window.textsecure.storage.user.getNumber();
                    }}
                }} catch(e) {{}}
                if (!ourId) {{
                    try {{
                        const state = window.inboxStore.getState();
                        if (state && state.user && state.user.ourNumber) {{
                            ourId = state.user.ourNumber;
                        }}
                    }} catch(e) {{}}
                }}

                // Check if we're admin
                const admins = convo.get('groupAdmins') || [];
                if (!ourId || !admins.includes(ourId)) throw new Error('You must be an admin to promote members');

                // Check if user is a member
                const members = convo.get('members') || [];
                if (!members.includes('{session_id}')) throw new Error('User is not a member of this group');

                // Check if already admin
                if (admins.includes('{session_id}')) throw new Error('User is already an admin');

                await convo.addAdmin('{session_id}');
                return true;
            }})()
        """)
        return result is True

    def demote_admin(self, group_id: str, session_id: str) -> bool:
        """
        Demote an admin to regular member.

        Args:
            group_id: The group conversation ID
            session_id: Session ID of the admin to demote

        Returns:
            True if admin was demoted successfully
        """
        result = self.evaluate(f"""
            (async function() {{
                const convo = window.getConversationController().get('{group_id}');
                if (!convo) throw new Error('Group not found');
                const type = convo.get('type');
                if (type !== 'group' && type !== 'groupv2') throw new Error('Not a group');

                // Get our Session ID safely
                let ourId = null;
                try {{
                    if (window.textsecure && window.textsecure.storage && window.textsecure.storage.user) {{
                        ourId = window.textsecure.storage.user.getNumber();
                    }}
                }} catch(e) {{}}
                if (!ourId) {{
                    try {{
                        const state = window.inboxStore.getState();
                        if (state && state.user && state.user.ourNumber) {{
                            ourId = state.user.ourNumber;
                        }}
                    }} catch(e) {{}}
                }}

                // Check if we're admin
                const admins = convo.get('groupAdmins') || [];
                if (!ourId || !admins.includes(ourId)) throw new Error('You must be an admin to demote members');

                // Check if user is admin
                if (!admins.includes('{session_id}')) throw new Error('User is not an admin');

                await convo.removeAdmin('{session_id}');
                return true;
            }})()
        """)
        return result is True

    def leave_group(self, group_id: str) -> bool:
        """
        Leave a group.

        Args:
            group_id: The group conversation ID

        Returns:
            True if successfully left the group
        """
        result = self.evaluate(f"""
            (async function() {{
                const convo = window.getConversationController().get('{group_id}');
                if (!convo) throw new Error('Group not found');
                const type = convo.get('type');
                if (type !== 'group' && type !== 'groupv2') throw new Error('Not a group');

                await convo.leaveGroup();
                return true;
            }})()
        """)
        return result is True

    def create_group(self, name: str, members: list[str]) -> Optional[str]:
        """
        Create a new group.

        Args:
            name: Name for the new group
            members: List of Session IDs to add as members

        Returns:
            The new group's conversation ID, or None if failed
        """
        members_json = json.dumps(members)
        name_escaped = json.dumps(name)

        return self.evaluate(f"""
            (async function() {{
                const controller = window.getConversationController();
                const members = {members_json};
                const name = {name_escaped};

                // Create the group using Session's group creation API
                const group = await controller.createGroup(members, name);
                if (!group) throw new Error('Failed to create group');

                return group.id;
            }})()
        """)

    def rename_group(self, group_id: str, new_name: str) -> bool:
        """
        Rename a group.

        Args:
            group_id: The group conversation ID
            new_name: New name for the group

        Returns:
            True if group was renamed successfully
        """
        name_escaped = json.dumps(new_name)

        result = self.evaluate(f"""
            (async function() {{
                const convo = window.getConversationController().get('{group_id}');
                if (!convo) throw new Error('Group not found');
                const type = convo.get('type');
                if (type !== 'group' && type !== 'groupv2') throw new Error('Not a group');

                // Get our Session ID safely
                let ourId = null;
                try {{
                    if (window.textsecure && window.textsecure.storage && window.textsecure.storage.user) {{
                        ourId = window.textsecure.storage.user.getNumber();
                    }}
                }} catch(e) {{}}
                if (!ourId) {{
                    try {{
                        const state = window.inboxStore.getState();
                        if (state && state.user && state.user.ourNumber) {{
                            ourId = state.user.ourNumber;
                        }}
                    }} catch(e) {{}}
                }}

                // Check if we're admin
                const admins = convo.get('groupAdmins') || [];
                if (!ourId || !admins.includes(ourId)) throw new Error('You must be an admin to rename the group');

                await convo.setGroupName({name_escaped});
                return true;
            }})()
        """)
        return result is True

    # === Utility ===

    @staticmethod
    def launch_session(
        port: int = DEFAULT_PORT,
        app_path: Optional[str] = None,
        start_in_tray: bool = False,
        allow_origins: str = "*",
    ) -> subprocess.Popen:
        """
        Launch Session with remote debugging enabled.

        Args:
            port: Remote debugging port
            app_path: Path to Session executable (auto-detected if None)
            start_in_tray: Start minimized to tray
            allow_origins: Origins to allow for WebSocket connections ("*" for all)

        Returns:
            Popen object for the Session process
        """
        if app_path is None:
            system = platform.system()
            if system == "Darwin":
                app_path = "/Applications/Session.app/Contents/MacOS/Session"
            elif system == "Linux":
                # Common locations
                for path in [
                    "/usr/bin/session-desktop",
                    "/opt/Session/session-desktop",
                ]:
                    if Path(path).exists():
                        app_path = path
                        break
            if app_path is None:
                raise FileNotFoundError("Could not find Session executable")

        args = [
            app_path,
            f"--remote-debugging-port={port}",
            f"--remote-allow-origins={allow_origins}",
        ]
        if start_in_tray:
            args.append("--start-in-tray")

        return subprocess.Popen(args)

    @staticmethod
    def get_launch_command(port: int = DEFAULT_PORT) -> str:
        """Get the command to launch Session with CDP enabled."""
        system = platform.system()
        if system == "Darwin":
            app = "/Applications/Session.app/Contents/MacOS/Session"
        else:
            app = "session-desktop"
        return f'{app} --remote-debugging-port={port} --remote-allow-origins="*"'

    @classmethod
    def wait_for_session(
        cls, port: int = DEFAULT_PORT, timeout: float = 30.0
    ) -> "SessionCDP":
        """
        Wait for Session to be ready and return connected CDP instance.

        Args:
            port: Remote debugging port
            timeout: Maximum seconds to wait

        Returns:
            Connected SessionCDP instance
        """
        import urllib.request
        import urllib.error

        start = time.time()
        while time.time() - start < timeout:
            try:
                with urllib.request.urlopen(f"http://localhost:{port}/json", timeout=1):
                    cdp = cls(port=port)
                    cdp.connect()
                    return cdp
            except (urllib.error.URLError, ConnectionError):
                time.sleep(0.5)

        raise TimeoutError(f"Session did not become ready within {timeout} seconds")
