# Three captured revisions, one inspectable critique

This example uses the existing local [jury case](../../../../../../assets/social/jury-case.md)
and its unchanged captures. It presents four selected threads, not the complete
ballots and not a new jury verdict. The dashboard data is synthetic; the saved
revision history and critiques are real artifacts. The final capture still has
unresolved period/provenance issues.

From the repository root:

```sh
python -m muriel redline plugins/muriel/skills/compose/examples/redline-review/review.json --output /tmp/muriel-redline-review.html
```

Open the resulting file. Select a finding, scrub the three revisions, compare
the original, then return. The axis endpoint annotation demonstrates a measured
6-capture-pixel discrepancy. At Actual pixels the image and redlines retain
their capture dimensions; use Fit capture to return to the overview.

The example references the existing `assets/social/jury-exhibit/` captures and
requires those local assets. It does not regenerate or modify the jury case.
The compiler itself works with any authored PNG review following the
[manifest contract](../../references/redline-review.md).
