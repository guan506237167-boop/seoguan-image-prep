"""Create static WebP derivatives in a new directory, with a provenance manifest."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError


def prepare(source, output, max_edge=1600, quality=82, prefix='image'):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_dir():
        raise ValueError('Input must be an existing directory')
    if output == source or source in output.parents:
        raise ValueError('Output must be outside the source directory')
    if not 1 <= max_edge <= 20000 or not 1 <= quality <= 100:
        raise ValueError('Invalid max-edge or quality')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,48}', prefix):
        raise ValueError('Prefix must use 1-49 letters, digits, _ or -')
    output.mkdir(exist_ok=False)
    entries = []
    for number, path in enumerate(sorted(source.iterdir(), key=lambda p: p.name), 1):
        if not path.is_file():
            continue
        row = {'original': path.name}
        entries.append(row)
        try:
            if path.is_symlink():
                row.update(status='skipped', reason='symlink')
                continue
            row['before_bytes'] = path.stat().st_size
            digest = hashlib.sha256()
            with path.open('rb') as source_file:
                for block in iter(lambda: source_file.read(1024 * 1024), b''):
                    digest.update(block)
            row['source_sha256'] = digest.hexdigest()
            with Image.open(path) as im:
                if getattr(im, 'n_frames', 1) != 1:
                    row.update(status='skipped', reason='animated or multi-page')
                    continue
                if im.mode not in ('RGB', 'RGBA', 'L', 'LA', 'P', '1'):
                    row.update(status='skipped', reason='unsupported color mode: ' + im.mode)
                    continue
                corrected = ImageOps.exif_transpose(im)
                transparent = 'A' in corrected.getbands() or 'transparency' in corrected.info
                result = corrected.convert('RGBA' if transparent else 'RGB')
                row['original_size'] = list(result.size)
                result.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
                name = f'{prefix}-{number:03d}.webp'
                dest = output / name
                kwargs = {'format': 'WEBP', 'quality': quality, 'method': 6}
                if im.info.get('icc_profile'):
                    kwargs['icc_profile'] = im.info['icc_profile']
                with dest.open('xb') as f:
                    result.save(f, **kwargs)
                row.update(status='created', output=name, output_size=list(result.size),
                           after_bytes=dest.stat().st_size, transparency=transparent)
                row['smaller'] = row['after_bytes'] < row['before_bytes']
        except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as e:
            row.update(status='failed', reason=str(e))
    manifest = {'entries': entries, 'max_edge': max_edge, 'quality': quality,
                'source_preserved': True, 'exif_preserved': False, 'icc_preserved_if_present': True}
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--max-edge', type=int, default=1600)
    p.add_argument('--quality', type=int, default=82)
    p.add_argument('--prefix', default='image')
    a = p.parse_args()
    try:
        result = prepare(a.input, a.output, a.max_edge, a.quality, a.prefix)
        failed = sum(r['status'] == 'failed' for r in result['entries'])
        print(json.dumps({'files': len(result['entries']), 'failed': failed}))
        if failed:
            p.exit(1, 'Partial failure; see manifest.json\n')
    except (OSError, ValueError) as e:
        p.exit(2, str(e) + '\n')


if __name__ == '__main__':
    main()
