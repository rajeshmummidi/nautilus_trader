from pathlib import Path

import markdown


readme = Path("README.md").read_text(encoding="utf-8")
body = markdown.markdown(
    readme,
    extensions=["fenced_code", "tables", "toc"],
    output_format="html5",
)

html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NautilusTrader</title>
  <style>
    :root {{ font-family: system-ui, sans-serif; color: #24292f; background: #f6f8fa; }}
    body {{ margin: 0; line-height: 1.6; }}
    main {{ max-width: 980px; min-height: 100vh; margin: 0 auto; padding: 40px 24px 72px; background: #fff; }}
    img {{ max-width: 100%; height: auto; }}
    pre {{ overflow-x: auto; padding: 16px; background: #f6f8fa; border-radius: 6px; }}
    code {{ font-family: ui-monospace, monospace; }}
    table {{ border-collapse: collapse; display: block; overflow-x: auto; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 13px; }}
    blockquote {{ border-left: 4px solid #d0d7de; color: #57606a; margin-left: 0; padding-left: 16px; }}
    a {{ color: #0969da; }}
  </style>
</head>
<body><main>{body}</main></body>
</html>"""

output = Path("site")
output.mkdir(exist_ok=True)
(output / "index.html").write_text(html, encoding="utf-8")