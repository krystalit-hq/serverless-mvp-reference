from pathlib import Path
import sys
import zipfile


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: python scripts/package_lambda.py <source_dir> <output_zip>"
        )

    source_dir = Path(sys.argv[1])
    output_zip = Path(sys.argv[2])

    if not source_dir.is_dir():
        raise SystemExit(f"source directory does not exist: {source_dir}")

    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        output_zip,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file() and path.name != ".gitkeep":
                archive.write(path, path.relative_to(source_dir))


if __name__ == "__main__":
    main()
