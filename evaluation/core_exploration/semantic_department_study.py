"""Frozen Chinese label retrieval research; no deployment or source-case training."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.request import urlopen
from .medjourney_readonly import SOURCE, source_cases, write_new, digest

ROOT = Path(__file__).resolve().parent / 'results/semantic-department-v1'
CACHE = Path(__file__).resolve().parent / 'embedding_cache'
MODEL = 'BAAI/bge-small-zh-v1.5'
REVISION = '7999e1d3359715c523056ef9478215996d62a620'


def load_cases():
    meta = json.loads(SOURCE.read_text(encoding='utf-8'))
    return meta, source_cases(urlopen(meta['source_url'], timeout=30).read(), meta['source_sha256'])


def model_path(download=False):
    from huggingface_hub import snapshot_download
    return snapshot_download(MODEL, revision=REVISION, cache_dir=str(CACHE), token=False,
                             local_files_only=not download, max_workers=2,
                             allow_patterns=['config.json', 'model.safetensors', 'tokenizer.json',
                                             'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt'])


def encode(model, tokenizer, texts):
    import numpy as np
    import torch
    batches = []
    with torch.inference_mode():
        for start in range(0, len(texts), 16):
            tokens = tokenizer(texts[start:start+16], padding=True, truncation=True,
                               max_length=256, return_tensors='pt')
            vectors = model(**tokens).last_hidden_state[:, 0].float()
            vectors = torch.nn.functional.normalize(vectors, p=2, dim=1)
            batches.append(vectors.cpu().numpy())
    return np.concatenate(batches)


def measure(cases, labels, scores, legacy):
    import numpy as np
    if scores.shape != (len(cases), len(labels)) or not np.isfinite(scores).all() or len(labels) < 3:
        raise ValueError('Complete finite score matrix required')
    rows = []
    for case, score in zip(cases, scores):
        order = np.argsort(-score, kind='stable')[:3]
        predicted = labels[int(order[0])] if float(score[order[0]]) > 0 else None
        status = legacy[case['case_id']]['status']
        ordinary = status in {'ROUTINE', 'URGENT'}
        rows.append({'case_id':case['case_id'], 'group':case['group'], 'has_suffix':case['has_suffix'],
                     'predicted_label':predicted, 'retrieval_abstained':predicted is None,
                     'top3':[labels[int(i)] for i in order] if predicted else [],
                     'similarity':float(score[order[0]]), 'margin':float(score[order[0]]-score[order[1]]),
                     'source_label_match':predicted in case['labels'],
                     'legacy_status':status, 'ordinary_scope':ordinary,
                     'ordinary_scope_match':bool(ordinary and predicted in case['labels'])})
    subset = [r for r in rows if not r['has_suffix']]
    return {'rows':rows, 'summary':{'full_rows':len(rows), 'input_groups':len({r['group'] for r in rows}),
            'closed_set_label_matches':sum(r['source_label_match'] for r in rows),
            'retrieval_abstentions':sum(r['retrieval_abstained'] for r in rows),
            'legacy_ordinary_scope_matches':sum(r['ordinary_scope_match'] for r in rows),
            'without_suffix_rows':len(subset), 'without_suffix_matches':sum(r['source_label_match'] for r in subset)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['freeze', 'download', 'evaluate'])
    args = parser.parse_args()
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    ROOT.mkdir(exist_ok=True)
    meta, cases = load_cases()
    labels = sorted({label for case in cases for label in case['labels']})
    if len(labels) != 111:
        raise ValueError('Source taxonomy changed')
    protocol = {'source_sha256':meta['source_sha256'], 'label_names':labels,
                'label_names_are_known_closed_set_taxonomy_not_case_supervision':True,
                'views':['source_body','complaint_only'], 'model':MODEL, 'revision':REVISION,
                'encoder':'CLS_L2_CPU_float32', 'threads':2,'batch':16,'max_length':256,
                'query_instruction':None,'char_tfidf_ngram':[2,4],
                'supervised_case_fits':0, 'calibration_fits':0, 'deployment':False,
                'source_exposure':'used_for_development_after_original_rule_baseline',
                'similarity_is_not_probability':True, 'risk_labels':None}
    if args.mode == 'freeze':
        write_new(ROOT/'protocol.json', protocol)
        print('PROTOCOL_FROZEN 111 labels; no predictions or source-case fits')
        return
    frozen = (ROOT/'protocol.json').read_bytes()
    if json.loads(frozen) != protocol:
        raise ValueError('Protocol changed')
    if args.mode == 'download':
        local = Path(model_path(download=True))
        hashes = {}
        for path in sorted(local.glob('*')):
            if path.is_file():
                h = hashlib.sha256()
                with path.open('rb') as f:
                    for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
                hashes[path.name] = h.hexdigest()
        if 'model.safetensors' not in hashes:
            raise ValueError('Safe weights unavailable')
        write_new(ROOT/'model-download.json', {'model':MODEL,'revision':REVISION,'files_sha256':hashes,
                                              'license':'MIT_model_card','model_inference_verified':False})
        print('SAFE_MODEL_DOWNLOAD_VERIFIED')
        return
    output = ROOT/'first-retrieval-comparison.json'
    if output.exists(): raise ValueError('Never overwrite study results')
    import numpy as np
    import torch
    from transformers import AutoTokenizer, AutoModel
    from sklearn.feature_extraction.text import TfidfVectorizer
    from threadpoolctl import threadpool_limits
    torch.set_num_threads(2); torch.set_num_interop_threads(2)
    local = model_path()
    tokenizer = AutoTokenizer.from_pretrained(local, local_files_only=True, trust_remote_code=False)
    model = AutoModel.from_pretrained(local, local_files_only=True, trust_remote_code=False,
                                     use_safetensors=True).to('cpu').eval()
    label_vectors = encode(model, tokenizer, labels)
    baseline_path = Path(__file__).resolve().parent/'results/medjourney-readonly-v1/first-source-comparison.json'
    baseline_raw = baseline_path.read_bytes(); baseline = json.loads(baseline_raw)
    results = []
    with threadpool_limits(limits=2):
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2,4), norm='l2')
        label_sparse = vectorizer.fit_transform(labels)
        for view in protocol['views']:
            texts = [c[view] for c in cases]
            legacy = {r['case_id']:r for v in baseline['results'] if v['view']==view for r in v['rows']}
            sparse_scores = (vectorizer.transform(texts) @ label_sparse.T).toarray()
            dense_scores = encode(model, tokenizer, texts) @ label_vectors.T
            for method, scores in [('label_char_tfidf',sparse_scores),('frozen_bge_label_names',dense_scores)]:
                item = measure(cases, labels, scores, legacy); item.update(method=method,view=view)
                results.append(item)
                print(method,view,json.dumps(item['summary']))
    write_new(output, {'protocol_sha256':hashlib.sha256(frozen).hexdigest(),
                      'baseline_sha256':hashlib.sha256(baseline_raw).hexdigest(),
                      'model_download_sha256':hashlib.sha256((ROOT/'model-download.json').read_bytes()).hexdigest(),
                      'encoder_device':'cpu','encoder_fits':0,'case_supervised_fits':0,
                      'tfidf_vocabulary_fit_only_on_label_names':True,'calibration_fits':0,
                      'clinical_validation':False,'raw_cases_or_embeddings_persisted':False,
                      'results_are_retrieval_not_serving_triage_or_service_availability':True,'results':results})


if __name__ == '__main__': main()
