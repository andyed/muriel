# Wavefield proofs

Three deliberately different uses of `muriel.patterns.wavefield()`:

- `decorative-divider.svg` uses seeded harmonic synthesis. It carries mood and
  structure only; it must not be described as data.
- `semantic-signal.svg` maps one caller-supplied normalized series exactly.
  Its accessible description marks the values as illustrative.
- `uncertainty-slices.svg` maps five caller-supplied series on one shared
  normalized scale. They are scenario slices, not a confidence interval.

Regenerate all three from the repository root:

```bash
python3 plugins/muriel/skills/compose/examples/wavefield/generate.py
```

The primitive is a clean-room Muriel implementation. The idea of making
layered SVG waves approachable was inspired by
[anup-a/svgwave](https://github.com/anup-a/svgwave); no source code from that
project is copied or bundled.
