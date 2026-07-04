"""GitHub URL mirror acceleration.

Converts GitHub raw/release URLs to mirror equivalents and tries
them as fallbacks when the original URL fails.
"""

from __future__ import annotations

from urllib.parse import urlparse

from loguru import logger

# Hosts recognized as GitHub raw content
_GITHUB_RAW_HOSTS = {"raw.githubusercontent.com"}

# Hosts recognized as GitHub releases
_GITHUB_RELEASE_HOSTS = {"github.com", "releases.githubusercontent.com"}

# Default mirror prefixes (applied to the path after the original host)
DEFAULT_GITHUB_MIRRORS: list[str] = [
    "https://gh-proxy.com/",
    "https://ghproxy.net/",
    "https://ghproxy.homeboyc.cn/",
    "https://github.akams.cn/",
]


def is_github_url(url: str) -> bool:
    """Check if a URL points to a GitHub resource that can be mirrored."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return host in _GITHUB_RAW_HOSTS or host in _GITHUB_RELEASE_HOSTS


def build_mirror_urls(url: str, mirrors: list[str] | None = None) -> list[str]:
    """Build a list of mirror URLs for a GitHub URL.

    Returns a list starting with the original URL, followed by mirror alternatives.
    For non-GitHub URLs, returns just the original URL.
    """
    if not is_github_url(url):
        return [url]

    mirror_list = mirrors if mirrors else DEFAULT_GITHUB_MIRRORS
    result = [url]

    for mirror_base in mirror_list:
        mirror_url = _build_single_mirror(url, mirror_base)
        if mirror_url and mirror_url != url:
            result.append(mirror_url)

    return result


def _build_single_mirror(url: str, mirror_base: str) -> str | None:
    """Convert a GitHub URL to a single mirror URL.

    Mirror sites typically accept the full GitHub URL as a path suffix:
      https://gh-proxy.com/https://raw.githubusercontent.com/user/repo/main/file.txt
    """
    base = mirror_base.rstrip("/")
    if not base:
        return None

    # The mirror format is: {mirror_base}/{original_url}
    # Most GitHub proxy services accept the full URL as path
    return f"{base}/{url}"


def log_mirror_attempt(mirror_url: str, original_url: str) -> None:
    """Log a mirror fallback attempt."""
    mirror_host = urlparse(mirror_url).hostname or "unknown"
    logger.info("Trying GitHub mirror {} for {}", mirror_host, original_url)
