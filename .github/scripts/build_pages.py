"""Build the GitHub Pages site: the repository's README.md as the front page.

The site is README.md, nothing else typed in: the Markdown is rendered by
GitHub's own renderer (POST /markdown, GitHub-flavoured, repository context)
so the page reads exactly as the repository view does. Relative links are
resolved so they work on the site: a link to a Markdown file or a directory
becomes its GitHub view; a link to a figure, a report or any other file that
exists in the checkout is copied into the site and kept relative. The dated
reports under docs/reports/ are copied whole so each is served at its path.

    python .github/scripts/build_pages.py OUT_DIR        # needs GITHUB_TOKEN
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = os.environ.get("GITHUB_REPOSITORY", "praneetdhoolia/city-digital-twin")
BRANCH = os.environ.get("PAGES_SOURCE_BRANCH", "main")
BLOB = f"https://github.com/{REPO}/blob/{BRANCH}/"
TREE = f"https://github.com/{REPO}/tree/{BRANCH}/"
COPY_DIRS = ("docs/reports",)
# Files a README link may point at that the site serves itself; anything else
# (Markdown, code, data) links to its GitHub view instead of being copied.
SERVED = {".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".html", ".pdf", ".css", ".js"}

def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()


def render_markdown(text: str, token: str) -> str:
    body = json.dumps({"text": text, "mode": "gfm", "context": REPO}).encode("utf-8")
    req = urllib.request.Request("https://api.github.com/markdown", data=body, method="POST")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def resolve_links(rendered: str, root: Path, out: Path) -> str:
    """Rewrite relative href/src targets so every link works on the site."""
    def fix(match: re.Match) -> str:
        attr, quote, target = match.group(1), match.group(2), match.group(3)
        if re.match(r"^(?:[a-z]+:|//|#|mailto:)", target, re.I):
            return match.group(0)
        path, _, fragment = target.partition("#")
        path = re.sub(r"^\./", "", path)
        src = root / path
        if not src.exists():
            return match.group(0)
        frag = f"#{fragment}" if fragment else ""
        if src.is_dir():
            return f'{attr}={quote}{TREE}{path}{quote}'
        if src.suffix.lower() in SERVED and not src.suffix.lower() in (".md", ".markdown"):
            dest = out / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            return match.group(0)
        return f'{attr}={quote}{BLOB}{path}{frag}{quote}'
    return re.sub(r'\b(href|src|srcset)=(["\'])([^"\']+)\2', fix, rendered)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    out = Path(argv[1])
    root = Path(sh("git", "rev-parse", "--show-toplevel"))
    sha = sh("git", "rev-parse", "--short", "HEAD")
    date = sh("git", "log", "-1", "--format=%cd", "--date=short")
    out.mkdir(parents=True, exist_ok=True)
    readme = (root / "README.md").read_text(encoding="utf-8")
    rendered = render_markdown(readme, os.environ.get("GITHUB_TOKEN", ""))
    rendered = resolve_links(rendered, root, out)
    for d in COPY_DIRS:
        src = root / d
        if src.exists():
            shutil.copytree(src, out / d, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("*.md"))
    title = html.escape(readme.splitlines()[0].lstrip("# ").strip() or REPO)
    page = f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="A city-agnostic digital twin of how a real city moves, MATSim end to end. Rendered from the repository's README.md.">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown.min.css">
<style>
body{{margin:0;background:#ffffff;color:#1f2328}}
@media (prefers-color-scheme:dark){{body{{background:#0d1117;color:#e6edf3}}}}
.wrap{{max-width:980px;margin:0 auto;padding:32px 24px 64px}}
.markdown-body{{box-sizing:border-box}}
.foot{{margin-top:48px;padding-top:12px;border-top:1px solid #d0d7de;font-size:12px;color:#59636e}}
@media (prefers-color-scheme:dark){{.foot{{border-top-color:#30363d;color:#8b949e}}}}
.foot a{{color:inherit}}
</style>
</head>
<body>
<div class="wrap">
<article class="markdown-body">
{rendered}
</article>
<p class="foot">Rendered from <a href="{BLOB}README.md">README.md</a> at commit <code>{sha}</code> ({date}) by <code>.github/workflows/pages.yml</code>. Dated whole-repository assessments are indexed at <a href="{BLOB}docs/reports/README.md">docs/reports/</a>; each report is served here at its path.</p>
</div>
</body>
</html>
"""
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    copied = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"built {out / 'index.html'} from README.md at {sha}; {copied} file(s) in the site")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
