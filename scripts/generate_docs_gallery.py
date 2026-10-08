"""Generate the complete deterministic documentation gallery."""

from __future__ import annotations

from _generate_docs_gallery_base import main as _base_main
from generate_docs_gallery_extra import main as _extra_main
from generate_docs_gallery_pages import main as _pages_main
from generate_sparse_mfpca_docs_figure import main as _sparse_mfpca_docs_main
from generate_workflow_gallery import main as _workflow_main
from generate_e1_e4_docs_gallery import main as _experimental_workflow_gallery_main


def main() -> None:
    """Generate qualified assets, sparse-planar docs figures, public coverage, and pages."""

    _base_main()
    _sparse_mfpca_docs_main()
    _workflow_main()
    _extra_main()
    _pages_main()
    _experimental_workflow_gallery_main()


if __name__ == "__main__":
    main()
