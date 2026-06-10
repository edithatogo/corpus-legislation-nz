from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

log = logging.getLogger(__name__)


class ZenodoClient:
    """Zenodo deposition client using the REST depositions + bucket file API.

    This client keeps publication opt-in. It creates or reuses a draft, uploads files via the
    bucket URL where available, then optionally calls the publish action.
    """

    def __init__(self, *, api_url: str, token: str, timeout: float = 120):
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    @property
    def json_headers(self) -> dict[str, str]:
        return {**self.headers, "Content-Type": "application/json"}

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        response: requests.Response | None = None
        for attempt in range(1, 6):
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            if response.status_code >= 500 and attempt < 5:
                time.sleep(min(60, 2**attempt))
                continue
            return response
        if response is None:
            raise RuntimeError(f"Zenodo request loop did not execute: {method} {url}")
        return response

    def create_deposition(self) -> dict[str, Any]:
        url = f"{self.api_url}/deposit/depositions"
        response = self._request("POST", url, headers=self.json_headers, data="{}")
        response.raise_for_status()
        return response.json()

    def get_deposition(self, deposition_id: str) -> dict[str, Any]:
        response = self._request(
            "GET", f"{self.api_url}/deposit/depositions/{deposition_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def create_new_version(self, deposition_id: str) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"{self.api_url}/deposit/depositions/{deposition_id}/actions/newversion",
            headers=self.headers,
        )
        response.raise_for_status()
        parent = response.json()
        latest_draft = parent.get("links", {}).get("latest_draft")
        if not latest_draft:
            raise RuntimeError("Zenodo did not return a latest_draft link for the new version")
        draft_response = self._request("GET", latest_draft, headers=self.headers)
        draft_response.raise_for_status()
        return draft_response.json()

    def ensure_draft(self, deposition_id: str | None = None) -> dict[str, Any]:
        if not deposition_id:
            return self.create_deposition()
        existing = self.get_deposition(deposition_id)
        if existing.get("submitted"):
            return self.create_new_version(deposition_id)
        return existing

    def update_metadata(
        self,
        deposition_id: str,
        *,
        title: str,
        creators: list[dict[str, Any]],
        description: str,
        version: str,
        license_id: str,
        keywords: list[str] | None = None,
        related_identifiers: list[dict[str, Any]] | None = None,
        publication_date: str | None = None,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "title": title,
            "upload_type": "dataset",
            "description": description,
            "creators": creators,
            "version": version,
            "license": license_id,
            "keywords": keywords or ["New Zealand", "legislation", "corpus", "law", "open data"],
        }
        if related_identifiers:
            metadata["related_identifiers"] = related_identifiers
        if publication_date:
            metadata["publication_date"] = publication_date
        response = self._request(
            "PUT",
            f"{self.api_url}/deposit/depositions/{deposition_id}",
            headers=self.json_headers,
            data=json.dumps({"metadata": metadata}),
        )
        response.raise_for_status()
        return response.json()

    def list_files(self, deposition_id: str) -> list[dict[str, Any]]:
        response = self._request(
            "GET", f"{self.api_url}/deposit/depositions/{deposition_id}/files", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def delete_file(self, deposition_id: str, file_id: str) -> None:
        response = self._request(
            "DELETE",
            f"{self.api_url}/deposit/depositions/{deposition_id}/files/{file_id}",
            headers=self.headers,
        )
        if response.status_code not in {204, 404}:
            response.raise_for_status()

    def delete_duplicate_named_files(self, deposition_id: str, names: set[str]) -> None:
        for item in self.list_files(deposition_id):
            filename = item.get("filename") or item.get("key")
            if filename in names and item.get("id"):
                self.delete_file(deposition_id, str(item["id"]))

    def upload_file_via_bucket(self, deposition: dict[str, Any], path: Path) -> dict[str, Any]:
        bucket_url = deposition.get("links", {}).get("bucket")
        if not bucket_url:
            raise RuntimeError(
                "Zenodo draft does not expose a bucket URL; cannot use large-file API"
            )
        url = f"{bucket_url.rstrip('/')}/{path.name}"
        with path.open("rb") as f:
            response = self._request("PUT", url, headers=self.headers, data=f)
        response.raise_for_status()
        return response.json() if response.text else {"filename": path.name}

    def publish(self, deposition_id: str) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"{self.api_url}/deposit/depositions/{deposition_id}/actions/publish",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()


def upload_archive_to_zenodo(
    *,
    api_url: str,
    token: str,
    files: list[Path],
    title: str,
    creators: list[dict[str, Any]],
    description: str,
    version: str,
    license_id: str,
    deposition_id: str | None = None,
    publish: bool = False,
    related_identifiers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    client = ZenodoClient(api_url=api_url, token=token)
    draft = client.ensure_draft(deposition_id)
    draft_id = str(draft["id"])
    client.delete_duplicate_named_files(draft_id, {path.name for path in files})
    uploaded = [client.upload_file_via_bucket(draft, path) for path in files]
    draft = client.update_metadata(
        draft_id,
        title=title,
        creators=creators,
        description=description,
        version=version,
        license_id=license_id,
        related_identifiers=related_identifiers,
    )
    result = {"draft": draft, "uploaded": uploaded, "published": None}
    if publish:
        result["published"] = client.publish(draft_id)
    return result
