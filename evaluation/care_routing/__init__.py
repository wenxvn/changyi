"""Independent care-routing experiments: uncertainty triage and adaptive inquiry.

These modules never import production Safety Gate rules into a decision path and
never modify the Flask composition root. They only reuse the repository-owned
symptom dataset and Multinomial NB trainer for offline evaluation.
"""
