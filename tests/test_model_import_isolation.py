from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_model_load_cannot_shadow_root_app_or_mutate_search_path():
    script = """
import sys
from pathlib import Path
from backend.app import composition
before = list(sys.path)
prediction = composition.predict_disease_name('咳嗽', details=True)
assert prediction['available'] and not prediction['abstained']
assert sys.path == before
import app
assert Path(app.__file__).resolve() == Path('app.py').resolve()
assert hasattr(app, 'SYMPTOM_DISEASE_MODEL_PATH')
assert not any(name in sys.modules for name in ('inference', 'labels', 'train'))
"""
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_model_cli_and_package_keep_symptom_parser_contract():
    for statement, cwd in (
        ("from inference import normalize_symptoms", ROOT / "data/symptom_disease_model"),
        ("from data.symptom_disease_model.inference import normalize_symptoms", ROOT),
    ):
        script = statement + "\nassert normalize_symptoms('cough')[0] == ['cough']"
        result = subprocess.run([sys.executable, "-c", script], cwd=cwd, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
