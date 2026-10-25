"""No-dependency contracts for production-default independent navigation previews."""
from __future__ import annotations

from prepare_navigation_prune_preview import FEATURE, prepare


def run() -> None:
    sample = "site_name: Example\ntheme:\n  name: material\n  features:\n    - navigation.indexes\n    - navigation.top\n"
    default_a = prepare(sample, pruned=False)
    candidate_a = prepare(sample, pruned=True)
    assert FEATURE not in default_a
    assert candidate_a.count(FEATURE) == 1
    assert "site_dir: build/navigation-baseline-site" in default_a
    assert "site_dir: build/navigation-prune-site" in candidate_a

    # Same two outputs even after production adopts the pruning feature.
    sample_b = sample.replace("    - navigation.indexes\n",
                              "    - navigation.indexes\n" + FEATURE)
    assert prepare(sample_b, pruned=False) == default_a
    assert prepare(sample_b, pruned=True) == candidate_a
    assert sample_b.count(FEATURE) == 1
    for changed in (sample.replace("    - navigation.top\n",
                                   "    - navigation.expand\n"),
                    sample.replace("    - navigation.indexes\n", "")):
        try:
            prepare(changed, pruned=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsafe production navigation config accepted")
    print("OK: identical pruned/unpruned previews on either production default")


if __name__ == "__main__":
    run()
