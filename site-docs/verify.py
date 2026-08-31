"""Headless verification of the muriel docs prototype via system Chrome.

Loads the served site, asserts structure, and computes the *rendered* WCAG
contrast ratio for body text, nav links, and in-content links against their
actual composited backgrounds. Run with the prototype venv:

    site-docs/.venv/bin/python3 site-docs/verify.py
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8753"

# WCAG relative-luminance contrast, computed on rendered rgb() values.
CONTRAST_JS = r"""
() => {
  function parseRGB(s){
    const m = s.match(/rgba?\(([^)]+)\)/);
    if(!m) return null;
    const p = m[1].split(',').map(x=>parseFloat(x.trim()));
    return {r:p[0], g:p[1], b:p[2], a:(p.length>3?p[3]:1)};
  }
  function lin(c){ c/=255; return c<=0.03928 ? c/12.92 : Math.pow((c+0.055)/1.055,2.4); }
  function lum(c){ return 0.2126*lin(c.r)+0.7152*lin(c.g)+0.0722*lin(c.b); }
  // Walk up the box tree compositing background-color over the page bg.
  function effectiveBg(el){
    let r=10,g=10,b=15; // page base #0a0a0f as the floor
    const chain=[];
    let n=el;
    while(n && n.nodeType===1){ chain.push(n); n=n.parentElement; }
    chain.reverse();
    for(const node of chain){
      const bg=parseRGB(getComputedStyle(node).backgroundColor);
      if(bg && bg.a>0){
        const a=bg.a;
        r=Math.round(bg.r*a + r*(1-a));
        g=Math.round(bg.g*a + g*(1-a));
        b=Math.round(bg.b*a + b*(1-a));
      }
    }
    return {r,g,b,a:1};
  }
  function ratio(el){
    const cs=getComputedStyle(el);
    const fg=parseRGB(cs.color);
    if(!fg) return null;
    const op=parseFloat(cs.opacity||'1');
    const bg=effectiveBg(el);
    // fold text opacity over its bg (the muriel "no opacity on text" trap)
    const f={r:Math.round(fg.r*op+bg.r*(1-op)),
             g:Math.round(fg.g*op+bg.g*(1-op)),
             b:Math.round(fg.b*op+bg.b*(1-op))};
    const L1=lum(f), L2=lum(bg);
    const hi=Math.max(L1,L2), lo=Math.min(L1,L2);
    return (hi+0.05)/(lo+0.05);
  }
  function minOver(sel, label){
    const els=[...document.querySelectorAll(sel)].filter(e=>{
      const t=(e.textContent||'').trim();
      const r=e.getBoundingClientRect();
      // Exclude Material's decorative permalink pilcrow (.headerlink ¶) — it is
      // a hover-reveal glyph affordance, not readable body/link text.
      if(e.classList && e.classList.contains('headerlink')) return false;
      return t.length>0 && r.width>0 && r.height>0;
    });
    let lo=Infinity, worst='';
    for(const e of els){
      const c=ratio(e);
      if(c!==null && c<lo){ lo=c; worst=(e.textContent||'').trim().slice(0,40); }
    }
    return {label, sel, count:els.length, min:lo===Infinity?null:Math.round(lo*100)/100, worst};
  }
  return [
    minOver('.md-content .md-typeset p', 'body paragraph'),
    minOver('.md-content .md-typeset li', 'body list item'),
    minOver('.md-content .md-typeset td', 'table cell'),
    minOver('.md-nav--primary .md-nav__link', 'left nav link'),
    minOver('.md-content .md-typeset a', 'in-content link'),
    minOver('.md-content .md-typeset h1, .md-content .md-typeset h2', 'heading'),
    minOver('.md-content .md-typeset code', 'inline code'),
  ];
}
"""

DEMO_CONTRAST_JS = r"""
() => {
  function parseRGB(s){
    const m = s && s.match(/rgba?\(([^)]+)\)/);
    if(!m) return null;
    const p = m[1].split(',').map(x=>parseFloat(x.trim()));
    return {r:p[0], g:p[1], b:p[2], a:(p.length>3?p[3]:1)};
  }
  function lin(c){ c/=255; return c<=0.03928 ? c/12.92 : Math.pow((c+0.055)/1.055,2.4); }
  function lum(c){ return 0.2126*lin(c.r)+0.7152*lin(c.g)+0.0722*lin(c.b); }
  function effectiveBg(el){
    let r=5,g=8,b=14;
    const chain=[];
    let n=el;
    while(n && n.nodeType===1){ chain.push(n); n=n.parentElement; }
    chain.reverse();
    for(const node of chain){
      const bg=parseRGB(getComputedStyle(node).backgroundColor);
      if(bg && bg.a>0){
        r=Math.round(bg.r*bg.a + r*(1-bg.a));
        g=Math.round(bg.g*bg.a + g*(1-bg.a));
        b=Math.round(bg.b*bg.a + b*(1-bg.a));
      }
    }
    return {r,g,b};
  }
  const els=[...document.querySelectorAll(
    'h1,h2,p,button,dt,dd,.eyebrow,.readout-label,.mode-state,.micro,.kbd-help,.plane-key,.drag-note,.metric span,.metric strong,.footer span,.segment-label,.radial-text,.contact-code,.contact-meta,.contact-state,.status-word')]
    .filter(el=>{
      const r=el.getBoundingClientRect();
      return r.width>0 && r.height>0 && getComputedStyle(el).visibility!=='hidden';
    });
  let min=Infinity, worst='';
  for(const el of els){
    const cs=getComputedStyle(el);
    const fg=parseRGB(el.matches('.segment-label') ? cs.fill : cs.color);
    if(!fg) continue;
    const bg=effectiveBg(el);
    const a=fg.a * parseFloat(cs.opacity||'1');
    const painted={r:fg.r*a+bg.r*(1-a),g:fg.g*a+bg.g*(1-a),b:fg.b*a+bg.b*(1-a)};
    const L1=lum(painted),L2=lum(bg);
    const ratio=(Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
    if(ratio<min){ min=ratio; worst=(el.textContent||el.className.baseVal||'').trim().slice(0,60); }
  }
  return {count:els.length,min:Math.round(min*100)/100,worst};
}
"""

def main():
    results = {"ok": True, "errors": [], "contrast": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        # --- Home page ---
        page.goto(f"{BASE}/", wait_until="networkidle")
        title = page.title()
        if "muriel" not in title.lower():
            results["errors"].append(f"home title unexpected: {title!r}")
        if "8:1" not in page.content():
            results["errors"].append("home page missing the 8:1 rule text")

        body_bg = page.eval_on_selector(
            "body", "el => getComputedStyle(el).backgroundColor")
        results["body_bg"] = body_bg
        if "10, 10, 15" not in body_bg.replace(" ", ", ").replace(",,", ","):
            # tolerant check
            if "rgb(10, 10, 15)" not in body_bg:
                results["errors"].append(f"body bg not OLED near-black: {body_bg}")

        # Search box present?
        results["search_present"] = page.locator("input.md-search__input").count() > 0
        if not results["search_present"]:
            results["errors"].append("search input not found")

        # Repository action: visible in the desktop header, then repeated in
        # Material's mobile drawer so GitHub stays close at hand at every size.
        repo_url = "https://github.com/andyed/muriel"
        header_repo = page.locator(".md-header__source a.md-source")
        results["github_header_present"] = header_repo.count() == 1
        results["github_header_href"] = (
            header_repo.get_attribute("href") if header_repo.count() else None)
        results["github_header_label"] = (
            header_repo.inner_text() if header_repo.count() else None)
        repo_box = header_repo.bounding_box() if header_repo.count() else None
        results["github_header_visible"] = bool(
            repo_box
            and repo_box["x"] >= 0
            and repo_box["y"] >= 0
            and repo_box["x"] + repo_box["width"] <= 1440
            and repo_box["y"] + repo_box["height"] <= 1000
            and repo_box["width"] >= 40
            and repo_box["height"] >= 40)
        if not results["github_header_present"]:
            results["errors"].append("desktop header missing GitHub repository action")
        elif results["github_header_href"] != repo_url:
            results["errors"].append(
                f"desktop GitHub action has wrong target: {results['github_header_href']!r}")
        if "andyed/muriel" not in (results["github_header_label"] or ""):
            results["errors"].append("desktop GitHub action has no visible repository label")
        if not results["github_header_visible"]:
            results["errors"].append("desktop GitHub action is not visibly tappable")

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(f"{BASE}/", wait_until="networkidle")
        mobile.locator(".md-header label[for='__drawer']").click()
        mobile.wait_for_timeout(400)  # let the drawer's transform settle
        mobile_repo = mobile.locator(".md-nav__source a.md-source")
        mobile_repo_box = mobile_repo.bounding_box() if mobile_repo.count() else None
        results["github_mobile_present"] = mobile_repo.count() == 1
        results["github_mobile_href"] = (
            mobile_repo.get_attribute("href") if mobile_repo.count() else None)
        results["github_mobile_label"] = (
            mobile_repo.inner_text() if mobile_repo.count() else None)
        results["github_mobile_visible"] = bool(
            mobile_repo_box
            and mobile_repo_box["x"] >= 0
            and mobile_repo_box["y"] >= 0
            and mobile_repo_box["x"] + mobile_repo_box["width"] <= 390
            and mobile_repo_box["y"] + mobile_repo_box["height"] <= 844
            and mobile_repo_box["width"] >= 40
            and mobile_repo_box["height"] >= 40)
        if not results["github_mobile_present"]:
            results["errors"].append("mobile drawer missing GitHub repository action")
        elif results["github_mobile_href"] != repo_url:
            results["errors"].append(
                f"mobile GitHub action has wrong target: {results['github_mobile_href']!r}")
        if "andyed/muriel" not in (results["github_mobile_label"] or ""):
            results["errors"].append("mobile GitHub action has no visible repository label")
        if not results["github_mobile_visible"]:
            results["errors"].append("mobile GitHub action is not visibly tappable")
        mobile.close()

        # Left-nav must list channels + vocabularies
        nav_text = page.inner_text(".md-nav--primary")
        for needle in ["Spatial", "Charts", "Infographics", "Science",
                       "Visible Language", "FUI", "muriel brand", "Dimensions"]:
            if needle not in nav_text:
                results["errors"].append(f"nav missing entry: {needle}")
        results["nav_has_channels"] = "Spatial" in nav_text and "Charts" in nav_text
        results["nav_has_vocab"] = "Visible Language" in nav_text and "FUI" in nav_text

        # External gallery link in Reference
        gallery = page.locator("a", has_text="Live demos").count()
        results["gallery_link_present"] = gallery > 0

        # Home contrast
        results["contrast"].append({"page": "home",
                                    "rows": page.evaluate(CONTRAST_JS)})

        # --- Spatial channel page ---
        page.goto(f"{BASE}/channels/spatial/", wait_until="networkidle")
        spatial_body = page.inner_text(".md-content")
        results["spatial_rendered"] = len(spatial_body) > 500
        # heading present?
        results["spatial_h1"] = page.locator(".md-content h1").count() > 0
        if not results["spatial_rendered"]:
            results["errors"].append("spatial page body too short / not rendered")
        results["contrast"].append({"page": "channels/spatial",
                                    "rows": page.evaluate(CONTRAST_JS)})

        # --- A vocabulary page ---
        page.goto(f"{BASE}/vocabularies/visible-language/", wait_until="networkidle")
        results["vocab_rendered"] = len(page.inner_text(".md-content")) > 500
        results["contrast"].append({"page": "vocabularies/visible-language",
                                    "rows": page.evaluate(CONTRAST_JS)})

        # --- Home: featured "Start here" + gallery links resolve to real targets ---
        page.goto(f"{BASE}/", wait_until="networkidle")
        # Collect hrefs of the in-content links (the Start-here block + buttons).
        hrefs = page.eval_on_selector_all(
            ".md-content .md-typeset a",
            "els => els.map(e => e.getAttribute('href'))")
        results["home_links_to_gallery"] = any(
            h and "gallery" in h for h in hrefs)
        results["home_links_to_spatial"] = any(
            h and "channels/spatial" in h for h in hrefs)
        results["home_links_to_skill"] = any(
            h and ("SKILL" in h or "skill" in h) for h in hrefs)
        if not results["home_links_to_gallery"]:
            results["errors"].append("home has no link into /gallery/")
        if not results["home_links_to_spatial"]:
            results["errors"].append("home Start-here missing Spatial channel link")

        # --- Gallery index present ---
        gpage = browser.new_page(viewport={"width": 1440, "height": 1000})
        gallery_console = []
        gpage.on("console", lambda m: gallery_console.append((m.type, m.text)))
        gpage.on("pageerror", lambda e: gallery_console.append(("pageerror", str(e))))
        resp = gpage.goto(f"{BASE}/gallery/", wait_until="networkidle")
        results["gallery_index_status"] = resp.status if resp else None
        results["gallery_index_rendered"] = len(gpage.content()) > 500
        if not (resp and resp.status == 200):
            results["errors"].append(
                f"/gallery/ did not return 200 (got {resp.status if resp else None})")

        # --- A live demo loads with no console errors ---
        demo_console = []
        dpage = browser.new_page(viewport={"width": 1440, "height": 1000})
        dpage.on("console", lambda m: demo_console.append((m.type, m.text)))
        dpage.on("pageerror", lambda e: demo_console.append(("pageerror", str(e))))
        dresp = dpage.goto(f"{BASE}/gallery/perspective-wall/",
                           wait_until="networkidle")
        results["demo_status"] = dresp.status if dresp else None
        dpage.wait_for_timeout(1500)  # let the spatial render settle
        errs = [t for (typ, t) in demo_console
                if typ in ("error", "pageerror")]
        results["demo_console_errors"] = errs
        results["demo_loaded"] = bool(dresp and dresp.status == 200)
        if not results["demo_loaded"]:
            results["errors"].append(
                f"/gallery/perspective-wall/ did not 200 (got {results['demo_status']})")
        if errs:
            results["errors"].append(
                f"demo console errors: {errs[:5]}")

        # --- Orbital Sunburst: shared geometry + input + responsive fallback ---
        orbital_console = []
        opage = browser.new_page(viewport={"width": 1440, "height": 1000})
        opage.on("console", lambda m: orbital_console.append((m.type, m.text)))
        opage.on("pageerror", lambda e: orbital_console.append(("pageerror", str(e))))
        oresp = opage.goto(f"{BASE}/gallery/orbital-sunburst/",
                           wait_until="networkidle")
        opage.wait_for_timeout(250)
        orbital_audit = opage.evaluate("window.__orbitalSunburstAudit()")
        results["orbital_status"] = oresp.status if oresp else None
        results["orbital_geometry"] = bool(
            orbital_audit["nodeCount"] == 17
            and orbital_audit["pathCount"] == 17
            and orbital_audit["uniquePathCount"] == 17
            and orbital_audit["rootDiscClosed"]
            and orbital_audit["branchCount"] == 4
            and orbital_audit["leafCount"] == 12)
        results["orbital_depth_stack"] = bool(
            orbital_audit["annularPlateCount"] == 2
            and orbital_audit["corePlateCount"] == 1
            and not orbital_audit["textDepthViolations"])
        results["orbital_controls_44"] = orbital_audit["controlsAtLeast44"]
        results["orbital_pretext"] = bool(
            orbital_audit["textFixture"] == "psychodeli"
            and orbital_audit["textCarrier"] == "adaptive"
            and orbital_audit["textCarriers"].get("upright") == 16
            and orbital_audit["textGlyphCount"] >= 16
            and orbital_audit["commandGlyphCount"] == 12
            and orbital_audit["textTiers"].get("1") >= 16
            and orbital_audit["textTiers"].get("2") >= 16
            and orbital_audit["textMinPhysical"] >= 16
            and not orbital_audit["textFailures"]
            and not orbital_audit["textOverflow"]
            and orbital_audit["textOverlapCount"] == 0)
        orbital_paths_before = opage.eval_on_selector_all(
            ".segment", "els => els.map(el => el.getAttribute('d'))")

        # Every placement carrier must compose the production menu corpus at
        # the physical type floor. Local tiers allow long commands to fall back
        # to an outer run while shorter commands exercise the requested rail.
        opage.locator("#textTierMode").select_option("local")
        carrier_audits = {}
        for carrier in ["upright", "bow", "arc", "spoke", "outer"]:
            opage.locator("#textCarrier").select_option(carrier)
            opage.wait_for_timeout(150)
            carrier_audits[carrier] = opage.evaluate(
                "window.__orbitalSunburstAudit()")
        results["orbital_carrier_matrix"] = {
            carrier: {
                "counts": audit["textCarriers"],
                "min": audit["textMinPhysical"],
                "failures": audit["textFailures"],
                "overflow": audit["textOverflow"],
            }
            for carrier, audit in carrier_audits.items()
        }
        results["orbital_carriers"] = all(
            not audit["textFailures"]
            and audit["textMinPhysical"] >= 16
            and audit["commandGlyphCount"] == 12
            and audit["textCarriers"].get(carrier, 0) > 0
            for carrier, audit in carrier_audits.items())

        # Fill and direction are orthogonal controls; exercise them on the
        # curved rail, where traversal and per-letter turn are observable.
        opage.locator("#textCarrier").select_option("arc")
        fill_audits = {}
        for fill in ["natural", "balanced", "space"]:
            opage.locator("#textFill").select_option(fill)
            opage.wait_for_timeout(120)
            fill_audits[fill] = opage.evaluate(
                "window.__orbitalSunburstAudit()")
        results["orbital_fill_modes"] = all(
            audit["textFill"] == fill
            and not audit["textFailures"]
            and audit["textMinPhysical"] >= 16
            for fill, audit in fill_audits.items())
        opage.locator("#textDirection").select_option("counter")
        opage.locator("#textCurve").fill("68")
        opage.locator("#textTurn").fill("18")
        opage.wait_for_timeout(180)
        tuned_text = opage.evaluate("window.__orbitalSunburstAudit()")
        results["orbital_text_direction"] = bool(
            tuned_text["textDirection"] == "counter"
            and tuned_text["textCurve"] == 0.68
            and tuned_text["textTurn"] == 0.18
            and tuned_text["textFill"] == "space"
            and tuned_text["textGlyphCount"] >= 50
            and tuned_text["maxLetterRotation"] <= 18.0)

        # Complex scripts stay whole: no grapheme-by-grapheme Arabic/CJK
        # shaping damage, and emoji/combining marks survive fixture projection.
        opage.locator("#textFixture").select_option("scripts")
        opage.locator("#textCarrier").select_option("adaptive")
        opage.locator("#textTierMode").select_option("shared")
        opage.locator("#textFill").select_option("natural")
        opage.wait_for_timeout(180)
        script_audit = opage.evaluate("window.__orbitalSunburstAudit()")
        script_runs = opage.locator(".radial-text-run").all_text_contents()
        results["orbital_script_canaries"] = bool(
            script_audit["textFixture"] == "scripts"
            and script_audit["rtlRunCount"] == 4
            and script_audit["textMinPhysical"] >= 16
            and script_audit["commandGlyphCount"] == 12
            and not script_audit["textFailures"]
            and not script_audit["textOverflow"]
            and all(text in script_runs for text in [
                "العربية", "الصوت", "الكاميرا", "المزيد",
                "日本語", "視覚", "音声入力", "Launch 🚀", "éclat"])
        )

        # Return to the production corpus for interaction tests.
        opage.locator("#textFixture").select_option("psychodeli")
        opage.wait_for_timeout(150)
        # Pointer commit on the stable 3-D view, then keyboard depth movement.
        # View transitions are verified separately below so their animation does
        # not turn this into a timing test instead of an input-path test.
        opage.locator("#sector-science").click()
        pointer_audit = opage.evaluate("window.__orbitalSunburstAudit()")
        results["orbital_pointer_state"] = pointer_audit["selectedId"]
        results["orbital_pointer_selection"] = (
            pointer_audit["selectedId"] == "science")
        opage.locator("#scene").focus()
        opage.keyboard.press("ArrowDown")
        results["orbital_state_separation"] = bool(
            opage.locator("#sector-science").evaluate(
                "el => el.classList.contains('is-selected')")
            and opage.locator("#sector-evidence").evaluate(
                "el => el.classList.contains('is-active')")
            and not opage.locator("#sector-evidence").evaluate(
                "el => el.classList.contains('is-selected')"))
        opage.keyboard.press("ArrowRight")
        opage.keyboard.press("Enter")
        keyboard_audit = opage.evaluate("window.__orbitalSunburstAudit()")
        results["orbital_keyboard_state"] = keyboard_audit["selectedId"]
        results["orbital_keyboard_selection"] = (
            keyboard_audit["selectedId"] == "media")
        results["orbital_active_descendant"] = (
            opage.locator("#scene").get_attribute("aria-activedescendant")
            == "treeitem-media")

        opage.locator("#modeToggle").click()
        opage.wait_for_timeout(750)
        orbital_paths_after = opage.eval_on_selector_all(
            ".segment", "els => els.map(el => el.getAttribute('d'))")
        results["orbital_path_stability"] = orbital_paths_before == orbital_paths_after
        results["orbital_top_view"] = (
            opage.locator("#stagePanel").get_attribute("data-mode") == "sunburst")
        orbital_contrast = opage.evaluate(DEMO_CONTRAST_JS)
        results["orbital_contrast"] = orbital_contrast
        results["orbital_contrast_8"] = orbital_contrast["min"] >= 8.0

        opage.set_viewport_size({"width": 390, "height": 844})
        opage.reload(wait_until="networkidle")
        mobile_orbital = opage.evaluate("window.__orbitalSunburstAudit()")
        results["orbital_mobile_fallback"] = bool(
            mobile_orbital["compact"]
            and mobile_orbital["mode"] == "sunburst"
            and mobile_orbital["controlsAtLeast44"]
            and opage.locator("#scene").get_attribute("tabindex") == "-1"
            and opage.locator("#modeToggle").is_disabled())
        orbital_errs = [t for (typ, t) in orbital_console
                        if typ in ("error", "pageerror")]
        results["orbital_console_errors"] = orbital_errs
        for key, message in [
                ("orbital_geometry", "orbital sunburst geometry contract failed"),
                ("orbital_depth_stack", "orbital annular depth/occlusion contract failed"),
                ("orbital_controls_44", "orbital desktop controls fell below 44 px"),
                ("orbital_pretext", "orbital Pretext ring composition failed"),
                ("orbital_carriers", "orbital text carrier matrix failed"),
                ("orbital_fill_modes", "orbital text filling modes failed"),
                ("orbital_text_direction", "orbital text-direction controls failed"),
                ("orbital_script_canaries", "orbital script/glyph canaries failed"),
                ("orbital_path_stability", "orbital sector paths moved across view state"),
                ("orbital_top_view", "orbital top-view toggle failed"),
                ("orbital_pointer_selection", "orbital SVG sector pointer commit failed"),
                ("orbital_state_separation", "orbital focus/selection states collapsed"),
                ("orbital_keyboard_selection", "orbital keyboard hierarchy navigation failed"),
                ("orbital_active_descendant", "orbital active-descendant state drifted"),
                ("orbital_contrast_8", "orbital rendered text fell below 8:1 contrast"),
                ("orbital_mobile_fallback", "orbital phone fallback contract failed")]:
            if not results[key]:
                results["errors"].append(message)
        if orbital_errs:
            results["errors"].append(
                f"orbital demo console errors: {orbital_errs[:5]}")

        # --- Annular FUI: second circular case with declared polar semantics ---
        annular_console = []
        apage = browser.new_page(viewport={"width": 1440, "height": 1100})
        apage.on("console", lambda m: annular_console.append((m.type, m.text)))
        apage.on("pageerror", lambda e: annular_console.append(("pageerror", str(e))))
        aresp = apage.goto(f"{BASE}/examples/annular-fui-console.html",
                           wait_until="networkidle")
        apage.wait_for_timeout(200)
        annular_audit = apage.evaluate("window.__annularFuiAudit()")
        results["annular_status"] = aresp.status if aresp else None
        results["annular_semantics"] = bool(
            annular_audit["case"] == "sensor-fusion-instrument"
            and annular_audit["angleMeaning"] == "bearing"
            and annular_audit["radiusMeaning"] == "range"
            and annular_audit["simulatedLabel"])
        results["annular_shared_records"] = bool(
            annular_audit["contactCount"] == 6
            and annular_audit["linearEquivalentCount"] == 6)
        results["annular_physical_floors"] = bool(
            annular_audit["targetMinPhysical"] >= 44
            and annular_audit["controlsAtLeast44"]
            and annular_audit["textMinPhysical"] >= 16)

        geometry_before = apage.eval_on_selector_all(
            ".contact", "els => els.map(el => el.dataset.geometry)")
        apage.locator("#reset").click()
        apage.locator("#instrument").focus()
        apage.keyboard.press("ArrowRight")
        apage.keyboard.press("Enter")
        annular_keyboard = apage.evaluate("window.__annularFuiAudit()")
        geometry_after = apage.eval_on_selector_all(
            ".contact", "els => els.map(el => el.dataset.geometry)")
        results["annular_keyboard"] = bool(
            annular_keyboard["activeId"] == "KITE-12"
            and annular_keyboard["pinnedId"] == "KITE-12")
        results["annular_geometry_stable"] = bool(
            annular_keyboard["geometryStable"]
            and geometry_before == geometry_after)

        apage.locator(".contact-button[data-id='EMBER-09']").click()
        annular_pointer = apage.evaluate("window.__annularFuiAudit()")
        results["annular_pointer"] = bool(
            annular_pointer["activeId"] == "EMBER-09"
            and annular_pointer["pinnedId"] == "EMBER-09")
        apage.locator("#pause").click()
        results["annular_pause"] = apage.evaluate(
            "window.__annularFuiAudit().scanPaused")
        annular_contrast = apage.evaluate(DEMO_CONTRAST_JS)
        results["annular_contrast"] = annular_contrast
        results["annular_contrast_8"] = annular_contrast["min"] >= 8.0

        apage.set_viewport_size({"width": 390, "height": 844})
        apage.reload(wait_until="networkidle")
        mobile_annular = apage.evaluate("window.__annularFuiAudit()")
        results["annular_mobile_fallback"] = bool(
            mobile_annular["responsiveLinearPrimary"]
            and mobile_annular["linearEquivalentCount"] == 6
            and mobile_annular["controlsAtLeast44"]
            and mobile_annular["textMinPhysical"] >= 16)
        annular_errs = [t for (typ, t) in annular_console
                        if typ in ("error", "pageerror")]
        results["annular_console_errors"] = annular_errs
        for key, message in [
                ("annular_semantics", "annular polar semantics were not declared"),
                ("annular_shared_records", "annular plot/list records drifted"),
                ("annular_physical_floors", "annular physical size floor failed"),
                ("annular_keyboard", "annular keyboard bearing navigation failed"),
                ("annular_geometry_stable", "annular data geometry moved across state"),
                ("annular_pointer", "annular pointer pinning failed"),
                ("annular_pause", "annular scan pause control failed"),
                ("annular_contrast_8", "annular rendered text fell below 8:1 contrast"),
                ("annular_mobile_fallback", "annular phone fallback contract failed")]:
            if not results[key]:
                results["errors"].append(message)
        if annular_errs:
            results["errors"].append(
                f"annular demo console errors: {annular_errs[:5]}")

        # --- Head asset / analytics presence on the rendered home ---
        home_head = page.eval_on_selector("head", "el => el.innerHTML")
        results["head_has_og"] = "og:image" in home_head and "og:url" in home_head
        results["head_has_favicon"] = "favicon-32.png" in home_head
        results["head_has_posthog"] = "posthog.init" in home_head
        for k, msg in [("head_has_og", "head missing OG tags"),
                       ("head_has_favicon", "head missing favicon link"),
                       ("head_has_posthog", "head missing PostHog snippet")]:
            if not results[k]:
                results["errors"].append(msg)

        browser.close()

    # ---- Report ----
    print("=== STRUCTURE ===")
    for k in ["body_bg", "search_present", "nav_has_channels", "nav_has_vocab",
              "github_header_present", "github_header_href", "github_header_label",
              "github_header_visible", "github_mobile_present", "github_mobile_href",
              "github_mobile_label", "github_mobile_visible",
              "gallery_link_present", "spatial_rendered", "spatial_h1",
              "vocab_rendered",
              "home_links_to_gallery", "home_links_to_spatial", "home_links_to_skill",
              "gallery_index_status", "gallery_index_rendered",
              "demo_status", "demo_loaded", "demo_console_errors",
              "orbital_status", "orbital_geometry", "orbital_depth_stack",
              "orbital_controls_44",
              "orbital_pretext", "orbital_carrier_matrix", "orbital_carriers",
              "orbital_fill_modes", "orbital_text_direction",
              "orbital_script_canaries",
              "orbital_path_stability", "orbital_top_view",
              "orbital_pointer_state", "orbital_pointer_selection",
              "orbital_state_separation",
              "orbital_keyboard_state", "orbital_keyboard_selection",
              "orbital_active_descendant", "orbital_contrast",
              "orbital_contrast_8", "orbital_mobile_fallback",
              "orbital_console_errors",
              "annular_status", "annular_semantics", "annular_shared_records",
              "annular_physical_floors", "annular_keyboard",
              "annular_geometry_stable", "annular_pointer", "annular_pause",
              "annular_contrast", "annular_contrast_8",
              "annular_mobile_fallback", "annular_console_errors",
              "head_has_og", "head_has_favicon", "head_has_posthog"]:
        print(f"  {k}: {results.get(k)}")

    print("\n=== CONTRAST (rendered, WCAG, opacity-folded) ===")
    global_min = float("inf")
    global_min_label = ""
    for blk in results["contrast"]:
        print(f"  [{blk['page']}]")
        for row in blk["rows"]:
            if row["min"] is None:
                print(f"      --     {row['label']:18s} (n={row['count']}, none visible)")
                continue
            flag = "OK " if row["min"] >= 8.0 else "!! FAIL "
            print(f"    {flag}{row['min']:6.2f}:1  {row['label']:18s} "
                  f"(n={row['count']})  worst: {row['worst']!r}")
            if row["min"] < global_min:
                global_min = row["min"]
                global_min_label = f"{blk['page']} / {row['label']}"
    print(f"\n  LOWEST OVERALL: {global_min:.2f}:1  @ {global_min_label}")
    if global_min < 8.0:
        results["errors"].append(
            f"contrast floor breached: {global_min:.2f}:1 @ {global_min_label}")

    print("\n=== ERRORS ===")
    if results["errors"]:
        for e in results["errors"]:
            print(f"  !! {e}")
        sys.exit(1)
    print("  none")

if __name__ == "__main__":
    main()
