# handlers/util/api_client.py
import os
import json
import requests
from typing import Dict, Any, Optional, Union, BinaryIO

from ..logger_config import get_logger

logger = get_logger(__name__)


class APIClient:
    """Client for making requests to the backend API"""

    def __init__(self):
        self.base_url = os.getenv("BACKEND_API_URL", "http://api:5000/api/v1")
        logger.debug(f"API Client initialized with base URL: {self.base_url}")
        # Test connectivity
        try:
            requests.get(f"{self.base_url}/health-check", timeout=2)
        except Exception as e:
            logger.error(f"API connection test failed: {str(e)}")

    def _construct_url(self, endpoint: str) -> str:
        """Construct full URL from endpoint"""
        # Ensure endpoint starts with a slash
        if not endpoint.startswith('/'):
            endpoint = f"/{endpoint}"

        return f"{self.base_url}{endpoint}"

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to API"""
        url = self._construct_url(endpoint)
        logger.debug(f"Making GET request to {url}")

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            raise

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request with JSON data to API"""
        url = self._construct_url(endpoint)
        logger.debug(f"Making POST request to {url} with data: {data}")

        try:
            response = requests.post(url, json=data)
            logger.debug(f"Response status: {response.status_code}, content: {response.text}")
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                logger.error(f"Non-JSON response: {response.text}")
                raise ValueError(f"Expected JSON response, got: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise


    def upload_file(self, endpoint: str, file_data: BinaryIO, filename: str,
                    file_field: str = 'file', extra_fields: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload a file to the API"""
        url = self._construct_url(endpoint)
        logger.debug(f"Uploading file to {url}")

        try:
            files = {file_field: (filename, file_data)}
            data = extra_fields if extra_fields else {}

            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"File upload error: {str(e)}")
            raise