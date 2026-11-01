"""Check tracked Markdown/image targets locally, without external requests."""
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def main():
    files = [ROOT / 'README.md', ROOT / 'AGENTS.md', ROOT / 'design-qa.md', *sorted((ROOT / 'docs').rglob('*.md'))]
    failures, count = [], 0
    for page in files:
        text = re.sub(r'```.*?```', '', page.read_text(), flags=re.S)
        links = re.findall(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)', text)
        links += re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)', text)
        for raw in links:
            url = urlsplit(raw.strip('<>'))
            if url.scheme or url.netloc or not url.path:
                continue
            target = (page.parent / unquote(url.path)).resolve()
            count += 1
            if not target.is_relative_to(ROOT) or not target.is_file():
                failures.append(f'{page.relative_to(ROOT)}: missing {raw}')
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f'Documentation: {len(files)} Markdown files, {count} local link/image targets verified.')


if __name__ == '__main__':
    main()
