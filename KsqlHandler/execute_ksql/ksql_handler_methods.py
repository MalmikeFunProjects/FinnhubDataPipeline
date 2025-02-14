from typing import Any
from httpx import Response
import requests
import json

import utils.settings as UTILS

class KsqlHandlerMethods:
    """
    A class containing helper methods for handling ksqlDB requests.
    """

    def headers(self) -> dict[str, str]:
        """
        Returns the headers required for ksqlDB requests.

        :return: Dictionary containing headers.
        """
        return {"Content-Type": "application/vnd.ksql.v1+json"}

    def stream_properties(self) -> dict[str, str]:
        """
        Returns default stream properties for ksqlDB.

        :return: Dictionary containing stream properties.
        """
        return {"auto.offset.reset": "earliest"}

    def payload(self, statement: str, streamsProperties={}):
        """
        Constructs the payload for ksqlDB queries.

        :param statement: The ksqlDB query statement.
        :param streamsProperties: Additional stream properties, default is empty.
        :return: Dictionary representing the payload.
        """
        return {"ksql": statement, "streamsProperties": streamsProperties}

    def stream_payload(self, statement: str, streamsProperties={}):
        """
        Constructs the payload for SQL queries on streams.

        :param statement: The SQL query statement.
        :param streamsProperties: Additional stream properties, default is empty.
        :return: Dictionary representing the stream payload.
        """
        return {"sql": statement, "properties": streamsProperties}

    def request(self, headers: dict[str, str], payload: dict[str, Any], request_type: str = "ksql") -> Response:
        """
        Sends a request to the ksqlDB server.

        :param headers: Headers required for the request.
        :param payload: The request payload containing query details.
        :param request_type: The type of request, default is "ksql".
        :return: The response from the ksqlDB server.
        :raises Exception: If the request fails.
        """
        response = requests.post(
            f"{UTILS.KSQLDB_URL}/{request_type}", headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.text}")
