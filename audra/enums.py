"""Copyright © 2025, EvieePy

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import enum


__all__ = ("ReceiveEvent", "SendEvent")


class SendEvent(enum.Enum):
    HTTPResponseStart = "http.response.start"
    HTTPResponseBody = "http.response.body"
    WSAccept = "websocket.accept"
    WSSend = "websocket.send"
    WSClose = "websocket.close"
    LSStartupComplete = "lifespan.startup.complete"
    LSStartupFailed = "lifespan.startup.failed"
    LSShutdownComplete = "lifespan.shutdown.complete"
    LSShutdownFailed = "lifespan.shutdown.failed"


class ReceiveEvent(enum.Enum):
    HTTPRequest = "http.request"
    HTTPDisconnect = "http.disconnect"
    WSConnect = "websocket.accept"
    WSReceive = "websocket.receive"
    WSDisconnect = "websocket.disconnect"
    LSStartup = "lifespan.startup"
    LSShutdown = "lifespan.shutdown"
