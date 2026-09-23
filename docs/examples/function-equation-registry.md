# Worked example: function → LaTeX contracts

Version 0.22 exposes the documentation mathematics as a small read-only public registry. This lets analysis code, notebooks, manuscripts, and documentation tooling identify the equation and scope attached to a scientific function without scraping Markdown.

## Inspect a contract

```python
from eyetrajectoriespy import get_mathematical_contract

contract = get_mathematical_contract("fit_mfpca")

print(contract.title)
print(contract.public_api)
print(contract.site_anchor)

for equation in contract.equations:
    print(equation)
```

The FPCA registry entry includes the weighted representation

$$
Z_{i,m,d}
=
\frac{G_{id}(t_m)-\widehat\mu_d(t_m)}{s_d}\sqrt{w_m},
$$

and the retained-component reconstruction

$$
\widehat{\mathbf G}^{(K)}_i(t)
=
\widehat{\boldsymbol\mu}(t)
+
\sum_{k=1}^{K}
\widehat\xi_{ik}\widehat{\boldsymbol\phi}_k(t).
$$

## Lookup by contract key

The same object can be retrieved by its stable contract key:

```python
assert get_mathematical_contract("fpca") is contract
```

Keys are documentation identifiers, while the function names connect the contract to the public package API.

## Build a tidy function table

```python
from eyetrajectoriespy import mathematical_contract_frame

frame = mathematical_contract_frame()
print(
    frame[
        ["contract_key", "function", "site_anchor", "scope"]
    ]
)
```

The table contains one row per registered public scientific function. The `latex` column contains the implementation-matched equation bodies, and `scope` records the main interpretive boundary.

## List all contracts

```python
from eyetrajectoriespy import list_mathematical_contracts

for item in list_mathematical_contracts():
    print(item.key, item.title)
```

The order is stable and is also used by the generated [function → equation index](../reference/function-equation-index.md).

## Why a registry instead of equations only in prose?

A single machine-readable registry allows CI to test that:

- every registered function exists and is public;
- keys and documentation anchors are unique;
- LaTeX equations are non-empty;
- generated GitHub and website indexes have not drifted from the registry;
- the expanded mathematical reference still contains the linked anchor;
- documentation tooling can reuse the same contract without retyping the formula.

The registry is **metadata only**. Looking up a contract does not fit a model, select an estimator, alter defaults, or change any numerical result.

## Related pages

- [Function → equation index](../reference/function-equation-index.md)
- [Expanded mathematical reference](../methods/mathematical-reference.md)
- [Workflow atlas](../methods/workflow-atlas.md)
- [Visual gallery](../methods/visual-gallery.md)
- [Public API](../reference/api.md)
