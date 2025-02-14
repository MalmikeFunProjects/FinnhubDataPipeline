
from typing import Any
from httpx import Response
import requests
import json

import utils.settings as UTILS


class KsqlHandlerMethods:
    def headers(self):
        return {"Content-Type": "application/vnd.ksql.v1+json"}

    def stream_properties(self):
        return {"auto.offset.reset": "earliest"}

    def payload(self, statement: str, streamsProperties={}):
        return {"ksql": statement, "streamsProperties": streamsProperties}

    def stream_payload(self, statement: str, streamsProperties={}):
        return {"sql": statement, "properties": streamsProperties}

    def request(self, headers: dict[str, str], payload: dict[str, Any], request_type: str = "ksql") -> Response:
        response = requests.post(
            f"{UTILS.KSQLDB_URL}/{request_type}", headers=headers, data=json.dumps(payload))
        if (response.status_code == 200):
            return response.json()
        else:
            raise Exception(f"Error: {response.text}")
