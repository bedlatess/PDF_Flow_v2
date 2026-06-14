"""HTML to PDF validation and rendering helpers."""

from __future__ import annotations

import ipaddress
import os
from pathlib import Path
import socket
from typing import Literal
from urllib.parse import urlparse

from fastapi import HTTPException, status


HTML_TO_PDF_MAX_HTML_BYTES = 512 * 1024
HTML_TO_PDF_RENDER_TIMEOUT_SECONDS = 30
HTML_TO_PDF_MAX_NAVIGATION_TIMEOUT_MS = 25_000
CHROMIUM_EXECUTABLE = os.getenv("CHROMIUM_EXECUTABLE", "/usr/bin/chromium")

PRIVATE_HOSTNAMES = {"localhost", "localhost.localdomain"}
BLOCKED_IPS = {
    ipaddress.ip_address("169.254.169.254"),
}

PageFormat = Literal["A4", "Letter", "Legal"]
Orientation = Literal["portrait", "landscape"]
MarginPreset = Literal["none", "narrow", "normal", "wide"]

PAGE_FORMATS: set[str] = {"A4", "Letter", "Legal"}
ORIENTATIONS: set[str] = {"portrait", "landscape"}
MARGIN_PRESETS: dict[str, dict[str, str]] = {
    "none": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
    "narrow": {"top": "0.25in", "right": "0.25in", "bottom": "0.25in", "left": "0.25in"},
    "normal": {"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"},
    "wide": {"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"},
}


def validate_url_for_html_to_pdf(raw_url: str) -> str:
    url = (raw_url or "").strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL is required")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only http and https URLs are supported",
        )
    if not parsed.hostname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL host is required")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL credentials are not supported")

    hostname = parsed.hostname.strip().lower().rstrip(".")
    if hostname in PRIVATE_HOSTNAMES or hostname.endswith(".localhost"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Private URLs are not allowed")

    try:
        ip = ipaddress.ip_address(hostname)
        _reject_private_ip(ip)
    except ValueError:
        try:
            addr_infos = socket.getaddrinfo(hostname, parsed.port or _default_port(parsed.scheme), type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL host could not be resolved") from exc
        for addr in addr_infos:
            _reject_private_ip(ipaddress.ip_address(addr[4][0]))

    return url


def validate_html_text(html: str) -> str:
    value = html or ""
    if not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTML content is required")
    if len(value.encode("utf-8")) > HTML_TO_PDF_MAX_HTML_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="HTML content is too large")
    return value


def normalize_page_options(
    *,
    page_size: str,
    orientation: str,
    margin: str,
) -> dict[str, object]:
    normalized_size = page_size if page_size in PAGE_FORMATS else "A4"
    normalized_orientation = orientation if orientation in ORIENTATIONS else "portrait"
    normalized_margin = margin if margin in MARGIN_PRESETS else "normal"
    return {
        "format": normalized_size,
        "landscape": normalized_orientation == "landscape",
        "margin": MARGIN_PRESETS[normalized_margin],
    }


def render_html_to_pdf(
    *,
    mode: str,
    source: str,
    output_path: str,
    page_size: str = "A4",
    orientation: str = "portrait",
    margin: str = "normal",
    timeout_seconds: int = HTML_TO_PDF_RENDER_TIMEOUT_SECONDS,
) -> dict:
    from playwright.sync_api import sync_playwright

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf_options = normalize_page_options(
        page_size=page_size,
        orientation=orientation,
        margin=margin,
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=CHROMIUM_EXECUTABLE if os.path.exists(CHROMIUM_EXECUTABLE) else None,
            args=[
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-sync",
                "--no-sandbox",
            ],
        )
        try:
            context = browser.new_context(ignore_https_errors=False)
            context.route("**/*", _guard_render_request)
            page = context.new_page()
            page.set_default_navigation_timeout(min(timeout_seconds * 1000, HTML_TO_PDF_MAX_NAVIGATION_TIMEOUT_MS))
            page.set_default_timeout(timeout_seconds * 1000)
            if mode == "url":
                safe_url = validate_url_for_html_to_pdf(source)
                page.goto(safe_url, wait_until="networkidle")
            else:
                html = validate_html_text(source)
                page.set_content(html, wait_until="networkidle", timeout=timeout_seconds * 1000)
            page.pdf(path=str(output), print_background=True, prefer_css_page_size=False, **pdf_options)
        finally:
            browser.close()

    return {
        "success": True,
        "output_path": str(output),
        "file_size": output.stat().st_size,
    }


def _guard_render_request(route) -> None:
    request = route.request
    url = request.url

    if url.startswith(("data:", "blob:", "about:")):
        route.continue_()
        return

    try:
        validate_url_for_html_to_pdf(url)
    except HTTPException:
        route.abort()
        return

    route.continue_()


def _reject_private_ip(ip: ipaddress._BaseAddress) -> None:
    if (
        ip in BLOCKED_IPS
        or ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
        or ip.is_reserved
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Private URLs are not allowed")


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80
