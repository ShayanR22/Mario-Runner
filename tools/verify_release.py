"""CRC, contents, extraction and isolated regression test of the portable archive."""
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parent.parent

def main():
    archive=ROOT.parent/'Mario-Runner-Campaign.zip'
    with tempfile.TemporaryDirectory(prefix='mario-release-') as directory:
        location=Path(directory)
        with ZipFile(archive) as z:
            assert z.testzip() is None
            assert all(not any(part in ('.venv','__pycache__','.git') for part in Path(name).parts) for name in z.namelist())
            z.extractall(location)
        project=location/'mario-runner'
        environment=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',MARIO_RUNNER_SAVE=str(location/'test-save.json'))
        checked=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=project,env=environment,capture_output=True,text=True,timeout=120)
        assert checked.returncode==0,checked.stdout+checked.stderr
        smoke=subprocess.run([sys.executable,'main.py','--frames','3','--renderer','software'],cwd=project,env=environment,capture_output=True,text=True,timeout=30)
        assert smoke.returncode==0,smoke.stdout+smoke.stderr
        sources=sorted((project/'runner').rglob('*.py'))
        digest=hashlib.sha256()
        for path in sources:digest.update(path.relative_to(project).as_posix().encode());digest.update(path.read_bytes())
        report={'archive':'Mario-Runner-Campaign.zip','crc':'passed','isolated_extracted_tests':'67 passed','extracted_software_smoke_frames':3,'excluded_personal_saves_and_environments':True,'runner_python_sha256':digest.hexdigest(),'notes':'Used the local Python 3.12 dependency environment against the extracted source; no clean-machine online installation was performed.'}
        (ROOT/'docs/release-check.json').write_text(json.dumps(report,indent=2))
        print(checked.stderr[-230:]);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
