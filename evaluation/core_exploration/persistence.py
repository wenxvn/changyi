"""Load locally generated study artifacts whose callbacks were saved by -m.

The -m entry point uses __main__ for top-level Python callbacks. Resolve those
known callbacks to the importable module and keep original model evidence intact.
"""
import sys
import joblib
from . import study


def load_study_model(path):
    main = sys.modules["__main__"]
    missing = object()
    names = ("binary_docs", "word_docs", "concat_docs", "canonical_docs", "segmented_tokens")
    old = {name: getattr(main, name, missing) for name in names}
    try:
        for name in names:
            setattr(main, name, getattr(study, name))
        return joblib.load(path)
    finally:
        for name, value in old.items():
            if value is missing:
                delattr(main, name)
            else:
                setattr(main, name, value)
