"""Generate the complete deterministic documentation gallery."""

from __future__ import annotations

from _generate_docs_gallery_base import main as _base_main
from generate_docs_gallery_extra import main as _extra_main
from generate_docs_gallery_pages import main as _pages_main


def main() -> None:
    """Generate qualified assets, complete public coverage, and gallery pages."""

    _base_main()
    _extra_main()
    _pages_main()


if __name__ == "__main__":
    main()
