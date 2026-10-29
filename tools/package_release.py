"""Build a portable release ZIP from the current source and runtime assets."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
ROOT=Path(__file__).resolve().parent.parent
DOCUMENT_IMAGES={
    "menu.png","levels.png","four-worlds.png","paused.png","settings.png",
    "checkpoint.png","complete.png","gameover.png","fire-warning.png",
    "mario-sheet.png","enemies-sheet.png","props-sheet.png","graphics-comparison.png",
    "enhanced-cave.png","enhanced-castle.png",
    *[f"world-{i}.png" for i in range(1,5)],
    *[f"intro-{i}.png" for i in range(1,5)],
}
def included(relative):
    if any(part in (".venv","__pycache__",".git") for part in relative.parts):
        return False
    if relative.parts[0]=="assets":
        return relative.parts[1] in ("sheets","generated") or relative.as_posix()=="assets/original/SuperMario256.ttf"
    if relative.parts[0]=="docs":
        return relative.suffix==".md" or relative.name in {"menu.png","four-worlds.png","paused.png","settings.png","graphics-settings.png","cosmetics.png","practice.png","records.png","secret-room.png","flagpole.png","complete.png","gameplay.gif","graphics-comparison.png","enhanced-cave.png","enhanced-castle.png","course-check.json","graphics-check.json","release-check.json"} or relative.name.startswith(("world-","intro-","ability-")) and relative.suffix==".png"
    return relative.suffix in (".py",".vert",".frag") or relative.name in ("README.md","requirements.txt","Play.command",".gitignore")

def main():
    archive=ROOT.parent/"Mario-Runner-Campaign.zip"
    files=[p for p in ROOT.rglob("*") if p.is_file() and included(p.relative_to(ROOT))]
    with ZipFile(archive,"w",ZIP_DEFLATED) as output:
        for path in sorted(files):
            output.write(path,Path("mario-runner")/path.relative_to(ROOT))
        error=output.testzip()
        if error:
            raise RuntimeError(f"Corrupt archive member: {error}")
    print(f"{archive}\n{len(files)} files / {archive.stat().st_size:,} bytes")

if __name__=="__main__":
    main()
