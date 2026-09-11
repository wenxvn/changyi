"""Official local demo entry point.

The Flask composition and HTTP adapters live in ``backend.app.composition``.
This small compatibility module keeps ``python app.py`` and existing imports stable.
"""

from backend.app import composition as _runtime

# Preserve the historical import surface for tests and local integrations while
# keeping the executable entry point free of business implementation.
for _name, _value in vars(_runtime).items():
    if not _name.startswith("__"):
        globals()[_name] = _value

app = _runtime.app


if __name__ == "__main__":
    print("=" * 60)
    print("  常州市智能医疗推荐系统 - 演示版")
    print("  Smart Medical Recommendation System")
    print("  http://127.0.0.1:5002")
    print("=" * 60)
    app.run(debug=False, host="0.0.0.0", port=5002)
