"""Check the installed deployment artifact without importing the source checkout."""
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile


def verify(wheel: Path) -> None:
    with TemporaryDirectory() as directory:
        with ZipFile(wheel) as archive:
            if "web/dist/index.html" not in archive.namelist():
                raise SystemExit("Frontend ausente do pacote. Compile web/dist antes do deploy.")
            archive.extractall(directory)
        subprocess.run(
            [sys.executable, "-I", "-c", """
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from fastapi.testclient import TestClient
from api.app.main import app, dist

assert dist.is_relative_to(Path.cwd()), 'A API deve usar o frontend do pacote isolado.'
index = (dist / 'index.html').read_bytes()
assets = re.findall(r'(?:src|href)="(/assets/[^"?]+)"', index.decode('utf-8'))
assert any(path.endswith('.js') for path in assets), 'JavaScript ausente do build.'
assert any(path.endswith('.css') for path in assets), 'CSS ausente do build.'
with TestClient(app) as client:
    for path in ('/', '/teste'):
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code)
        assert response.headers['content-type'].startswith('text/html'), path
        assert response.content == index, path
    for path in assets:
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code)
        assert response.content == (dist / path.lstrip('/')).read_bytes(), path
    response = client.get('/api/health')
    assert response.status_code == 200 and response.json() == {'status': 'ok'}
print('Pacote validado: pagina inicial, navegacao, JavaScript, CSS e API.')
"""],
            cwd=directory,
            check=True,
            timeout=60,
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/verify-deploy.py caminho/do/pacote.whl")
    verify(Path(sys.argv[1]).resolve())
