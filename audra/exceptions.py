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

import http

from .headers import Headers


__all__ = (
    "AudraException",
    "HTTPBadGateway",
    "HTTPBadRequest",
    "HTTPConflict",
    "HTTPContentTooLarge",
    "HTTPException",
    "HTTPExpectationFailed",
    "HTTPFailedDependency",
    "HTTPForbidden",
    "HTTPFound",
    "HTTPGatewayTimeout",
    "HTTPGone",
    "HTTPInsufficientStorage",
    "HTTPInternalServerError",
    "HTTPLengthRequired",
    "HTTPLocked",
    "HTTPLoopDetected",
    "HTTPMethodNotAllowed",
    "HTTPMisdirectedRequest",
    "HTTPMovedPermanently",
    "HTTPMultipleChoices",
    "HTTPNetworkAuthenticationRequired",
    "HTTPNotAcceptable",
    "HTTPNotExtended",
    "HTTPNotFound",
    "HTTPNotImplemented",
    "HTTPNotModified",
    "HTTPPaymentRequired",
    "HTTPPermanentRedirect",
    "HTTPPreconditionFailed",
    "HTTPPreconditionRequired",
    "HTTPProxyAuthenticationRequired",
    "HTTPRangeNotSatisfiable",
    "HTTPRequestHeaderFieldsTooLarge",
    "HTTPRequestTimeout",
    "HTTPSeeOther",
    "HTTPServiceUnavailable",
    "HTTPTeapot",
    "HTTPTemporaryRedirect",
    "HTTPTooEarly",
    "HTTPTooManyRequests",
    "HTTPUnauthorized",
    "HTTPUnavailableForLegalReasons",
    "HTTPUnprocessableContent",
    "HTTPUnsupportedMediaType",
    "HTTPUpgradeRequired",
    "HTTPUriTooLong",
    "HTTPVariantAlsoNegotiates",
    "HTTPVersionNotSupported",
    "InvalidRouterError",
    "MiddlewareLoadException",
    "RouteAlreadyExists",
)


class AudraException(Exception): ...


class MiddlewareLoadException(AudraException): ...


class InvalidRouterError(AudraException): ...


class RouteAlreadyExists(AudraException): ...


class ClientDisconnected(AudraException): ...


class BaseHTTPException(AudraException):
    status: int

    def __init__(self, *, status: int | None = None, details: str | None = None, headers: Headers | None = None) -> None:
        self.status = getattr(self, "status", status) or 500
        self.details = details or http.HTTPStatus(self.status).phrase


class HTTPException(BaseHTTPException):
    def __init__(self, *, status: int, details: str | None = None, headers: Headers | None = None) -> None:
        super().__init__(status=status, details=details, headers=headers)


class HTTPMultipleChoices(BaseHTTPException):
    status = 300


class HTTPMovedPermanently(BaseHTTPException):
    status = 301


class HTTPFound(BaseHTTPException):
    status = 302


class HTTPSeeOther(BaseHTTPException):
    status = 303


class HTTPNotModified(BaseHTTPException):
    status = 304


class HTTPTemporaryRedirect(BaseHTTPException):
    status = 307


class HTTPPermanentRedirect(BaseHTTPException):
    status = 308


class HTTPBadRequest(BaseHTTPException):
    status = 400


class HTTPUnauthorized(BaseHTTPException):
    status = 401


class HTTPPaymentRequired(BaseHTTPException):
    status = 402


class HTTPForbidden(BaseHTTPException):
    status = 403


class HTTPNotFound(BaseHTTPException):
    status = 404


class HTTPMethodNotAllowed(BaseHTTPException):
    status = 405


class HTTPNotAcceptable(BaseHTTPException):
    status = 406


class HTTPProxyAuthenticationRequired(BaseHTTPException):
    status = 407


class HTTPRequestTimeout(BaseHTTPException):
    status = 408


class HTTPConflict(BaseHTTPException):
    status = 409


class HTTPGone(BaseHTTPException):
    status = 410


class HTTPLengthRequired(BaseHTTPException):
    status = 411


class HTTPPreconditionFailed(BaseHTTPException):
    status = 412


class HTTPContentTooLarge(BaseHTTPException):
    status = 413


class HTTPUriTooLong(BaseHTTPException):
    status = 414


class HTTPUnsupportedMediaType(BaseHTTPException):
    status = 415


class HTTPRangeNotSatisfiable(BaseHTTPException):
    status = 416


class HTTPExpectationFailed(BaseHTTPException):
    status = 417


class HTTPTeapot(BaseHTTPException):
    status = 418


class HTTPMisdirectedRequest(BaseHTTPException):
    status = 421


class HTTPUnprocessableContent(BaseHTTPException):
    status = 422


class HTTPLocked(BaseHTTPException):
    status = 423


class HTTPFailedDependency(BaseHTTPException):
    status = 424


class HTTPTooEarly(BaseHTTPException):
    status = 425


class HTTPUpgradeRequired(BaseHTTPException):
    status = 426


class HTTPPreconditionRequired(BaseHTTPException):
    status = 428


class HTTPTooManyRequests(BaseHTTPException):
    status = 429


class HTTPRequestHeaderFieldsTooLarge(BaseHTTPException):
    status = 431


class HTTPUnavailableForLegalReasons(BaseHTTPException):
    status = 451


class HTTPInternalServerError(BaseHTTPException):
    status = 500


class HTTPNotImplemented(BaseHTTPException):
    status = 501


class HTTPBadGateway(BaseHTTPException):
    status = 502


class HTTPServiceUnavailable(BaseHTTPException):
    status = 503


class HTTPGatewayTimeout(BaseHTTPException):
    status = 504


class HTTPVersionNotSupported(BaseHTTPException):
    status = 505


class HTTPVariantAlsoNegotiates(BaseHTTPException):
    status = 506


class HTTPInsufficientStorage(BaseHTTPException):
    status = 507


class HTTPLoopDetected(BaseHTTPException):
    status = 508


class HTTPNotExtended(BaseHTTPException):
    status = 510


class HTTPNetworkAuthenticationRequired(BaseHTTPException):
    status = 511
