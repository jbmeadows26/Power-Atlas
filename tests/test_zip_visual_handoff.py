"""Regression checks for the mobile ZIP-to-visual-story handoff.

These source guards preserve the approved V6 journey; browser-level checks
are still needed when a publicly accessible deployment is available.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "platform" / "unified" / "my-life.html"
VISUAL = ROOT / "platform" / "unified" / "visual-story-v6.js"


def test_zip_submit_reaches_visual_snapshot_before_issue_picker():
    page = PAGE.read_text(encoding="utf-8")
    handler = page.split('$("zipForm").addEventListener("submit",e=>{', 1)[1].split("\n});", 1)[0]
    assert 'document.querySelector("main > .vs6-topic")' in handler
    assert "visualOverview.scrollIntoView" in handler
    assert 'scrollToSection("where","where")' in handler
    assert 'scrollToSection("what","what")' not in handler


def test_visual_zip_story_is_the_target_and_has_four_issues():
    visual = VISUAL.read_text(encoding="utf-8")
    assert '"my-life.html":["Your ZIP. Your everyday costs."' in visual
    assert 'main.prepend(section);' in visual
    assert 'attachZIPVisual(section);' in visual
    for metric in ('key:"housing"', 'key:"transport"', 'key:"groceries"', 'key:"health"'):
        assert metric in visual


def test_community_cover_uses_approved_v6_visual_design():
    """The ZIP results must not regress to the original full-width legacy hero."""
    for directory in (ROOT / "platform" / "unified", ROOT / "site"):
        script = (directory / "visual-story-v6.js").read_text(encoding="utf-8")
        stylesheet = (directory / "visual-story-v6.css").read_text(encoding="utf-8")
        assert 'const isPlaceStory=documentPath==="my-life.html";' in script
        assert 'section.classList.add("vs6-topic-cover")' in script
        assert "if(isPlaceStory)intro.append(cta)" in script
        assert "vs6-topic-cover>.vs6-intro" in stylesheet
        assert "grid-template-columns:minmax(0,.85fr) minmax(0,1.15fr)" in stylesheet
        assert "background:var(--vs6-cream)" in stylesheet
        assert ".vs6-topic-cover .vs6-zip-grid" in stylesheet
