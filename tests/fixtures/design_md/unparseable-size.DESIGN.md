---
name: Unparseable Size
colors:
  surface: "#FFFFFF"
  text: "#111827"
typography:
  h1:
    fontFamily: "Playfair Display"
    fontSize: 2.5vw
  body-md:
    fontFamily: "Inter"
    fontSize: 16px
rounded:
  sm: 4px
  pill: 50%
---

## Overview

One viewport-relative size and one percentage radius: neither has a pixel
value without a viewport, so both must be dropped with a WARN.
