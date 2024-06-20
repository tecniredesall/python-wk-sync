import json
import requests

from fastapi import status
from fastapi_cache import caches

from app.models.settings import get_settings
from app.auth.auth_handler import decode_jwt_general
from utils.constans import (
    APP_FEDERATION,
    APP_TRANSFORMATIONS,
    APP_TRUMMODITY
)
from lib.logging import get_logger

local_logger = get_logger(__name__)
config = get_settings()

class API:
    def __init__(self, app: str = None, endpoint: str = None, data: str = None):
        self.endpoint = endpoint
        self.app = app
        self.header_json = False
        if self.app == APP_FEDERATION:
            self.endpoint = config.FEDERATION_URL
        elif self.app == APP_TRANSFORMATIONS:
            self.header_json = True
            self.endpoint = config.TRANSFORMATIONS_URL
        elif self.app == APP_TRUMMODITY:
           self.endpoint = config.TRUMMODITY_BASE_URL
        self.token = self._get_token(data)


    def _get_variable_cache(self, key):
        return caches.get(key)


    def _set_variable_cache(self, key, value):
        if self._get_variable_cache(key):
            caches.remove(key)
        caches.set(key, value)


    def _get_token(self, data: str):
        if self.app:
            token = self._get_variable_cache(f'token_{self.app}')
            if token:
                is_valid = decode_jwt_general(token)
                if is_valid:
                    return token
        return self._process_token(data)


    def _process_token(self, data: str):
        path = '/sign'
        endpoint = self.endpoint
        if self.app == APP_FEDERATION:
            endpoint = config.AUTHENTICATION_URL
            path = ''
            data = {
                "client_id": config.CLIENT_ID,
                "client_secret": config.CLIENT_SECRET,
                "audience": config.AUDIENCE_URL,
                "grant_type": config.GRANT_TYPE
            }
        elif self.app == APP_TRANSFORMATIONS:
            data = {
                "email": config.TRANSFORMATIONS_USER,
                "password": config.TRANSFORMATIONS_PASSWORD
            }
        elif self.app == APP_TRUMMODITY:
            data = {
                "email": config.TRUMMODITY_USER,
                "password": config.TRUMMODITY_PASSWORD
            }
        try:
            response = requests.post((endpoint + path), json=data)
            data = response.json()
            if response.status_code == status.HTTP_200_OK:
                token = None
                if "token" in data:
                    token = data["token"]
                elif "access_token" in data:
                    token = data["access_token"]
                else:
                    local_logger.info(f"Token {self.app} default: {data}")
                    token = data
                if self.app:
                    self._set_variable_cache(f'token_{self.app}', token)
                return token
            else:
                local_logger.error(f"Path {(endpoint + path)}, body: {json.dumps(data)}")
                local_logger.error(f"Error {self.app} token: {json.loads(response.content.decode('utf-8'))}")
        except Exception as err:
            local_logger.error(f"Path {(endpoint + path)}, body: {json.dumps(data)}")
            local_logger.error(f"Error {self.app} token: {err}")
        return None


    def _get_auth_headers(self):
        header = {
            'Authorization': f'Bearer {self.token}'
        }
        if self.header_json:
            header['Content-Type'] = 'application/json'
        return header


    def _get_response(self, response, request: dict):
        data_response = {
            "status":  response.status_code,
            "data": response.json()
        }
        if not data_response["status"] in (status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_204_NO_CONTENT):
            local_logger.error(f'Error consuming method: {request["method"]}, path: {request["path"]}, body {request["body"]}')
            local_logger.error(f'Error consuming the {self.app} api {data_response["status"]}: {data_response["data"]}')
        return data_response


    def _error_response(self, error):
        return {
            "status":  status.HTTP_400_BAD_REQUEST,
            "data": str(error)
        }


    def get(self, path: str, params: str = None):
        try:
            response = requests.get(
                (self.endpoint + path),
                headers=self._get_auth_headers(),
                params=params
            )
            return self._get_response(
                response,
                {
                    "path": path,
                    "method":   "get",
                    "body": None
                }
            )
        except Exception as err:
            local_logger.error(f"Error {self.app}  endpoint (get: {path}, params: {params}): {err}")
            return self._error_response(err)


    def post(self, path: str, data: dict = None):
        try:
            data = json.dumps(data)
            response = requests.post(
                (self.endpoint + path),
                headers=self._get_auth_headers(),
                data=data
            )
            return self._get_response(
                response,
                {
                    "path": path,
                    "method":   "post",
                    "body": data
                }
            )
        except Exception as err:
            local_logger.error(f"Error {self.app} endpoint (post: {path}): {err}  \nbody: {data}")
            return self._error_response(err)


    def patch(self, path: str, data: dict = None):
        if self.header_json:
            data = json.dumps(data)
        try:
            response = requests.patch(
                (self.endpoint + path),
                headers=self._get_auth_headers(),
                data=data
            )
            data = data if self.header_json else json.dumps(data)
            return self._get_response(
                response,
                {
                    "path": path,
                    "method":   "patch",
                    "body": data
                }
            )
        except Exception as err:
            local_logger.error(f"Error {self.app} endpoint (patch: {path}): {err} \n body: {data}")
            return self._error_response(err)


    def put(self, path: str, data: dict = None):
        if self.header_json:
            data = json.dumps(data)
        try:
            response = requests.put(
                (self.endpoint + path),
                headers=self._get_auth_headers(),
                data=data
            )
            data = data if self.header_json else json.dumps(data)
            return self._get_response(
                response,
                {
                    "path": path,
                    "method":   "put",
                    "body": data
                }
            )
        except Exception as err:
            local_logger.error(f"Error {self.app} endpoint (put: {path}): {err} \n body: {data}")
            return self._error_response(err)


    def delete(self, path: str):
        try:
            response = requests.delete(
                (self.endpoint + path),
                headers=self._get_auth_headers()
            )
            return self._get_response(
                response,
                {
                    "path": path,
                    "method":   "delete",
                    "body": None
                }
            )
        except Exception as err:
            local_logger.error(f"Error {self.app} endpoint (delete: {path}): {err}")
            return self._error_response(err)
