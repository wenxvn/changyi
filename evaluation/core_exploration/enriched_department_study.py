"""Fixed existing-resource text enrichment; not verification of service claims."""
import argparse
import hashlib
import json
from pathlib import Path
from .semantic_department_study import load_cases, model_path, encode, measure, MODEL, REVISION
from .medjourney_readonly import ALIASES,write_new,digest

ROOT=Path(__file__).resolve().parent/'results/enriched-department-v1'
DATA=Path(__file__).resolve().parents[2]/'data'


def build_docs(labels, doctor_files):
    grouped={};sources={}
    for path in sorted(doctor_files):
        raw=path.read_bytes();sources[path.name]=hashlib.sha256(raw).hexdigest()
        payload=json.loads(raw)
        for row in payload['doctors']:
            dept=row.get('department')
            if not isinstance(dept,str):continue
            dept=ALIASES.get(dept,dept)
            terms=[]
            if isinstance(row.get('specialty'),str):terms.append(row['specialty'].strip())
            if isinstance(row.get('specialties'),list):terms.extend(x.strip() for x in row['specialties'] if isinstance(x,str))
            grouped.setdefault(dept,set()).update(x for x in terms if x)
    docs=[];metadata=[]
    for label in labels:
        terms=sorted(grouped.get(ALIASES.get(label,label),set()))
        full=label+('。资料条目自述相关领域：'+'；'.join(terms) if terms else '')
        text=full[:800]
        docs.append(text)
        metadata.append({'label':label,'distinct_resource_texts':len(terms),'full_chars':len(full),
                         'used_chars':len(text),'document_sha256':digest(text),'character_truncated':len(full)>800})
    return docs,metadata,sources


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['freeze','evaluate']);args=parser.parse_args()
    meta,cases=load_cases();labels=sorted({x for c in cases for x in c['labels']})
    docs,documents,sources=build_docs(labels,DATA.glob('doctors_h*.json'))
    protocol={'source_sha256':meta['source_sha256'],'model':MODEL,'revision':REVISION,'label_names':labels,
              'resource_files_sha256':sources,'documents':documents,'lookup':'existing_four_aliases_then_exact_department',
              'maximum_document_chars':800,'encoder_max_length':256,'views':['source_body','complaint_only'],
              'source_case_training':False,'resource_texts_are_unverified_claims_not_service_guarantees':True,
              'source_exposure':'used_for_development','clinical_validation':False}
    ROOT.mkdir(exist_ok=True)
    if args.mode=='freeze':
        write_new(ROOT/'protocol.json',protocol)
        print('FROZEN',sum(x['distinct_resource_texts']>0 for x in documents),'of',len(labels),'labels enriched')
        return
    frozen=(ROOT/'protocol.json').read_bytes()
    if json.loads(frozen)!=protocol:raise ValueError('Frozen resource text protocol changed')
    output=ROOT/'first-enriched-comparison.json'
    if output.exists():raise ValueError('Never overwrite enriched comparison')
    import torch
    from transformers import AutoTokenizer,AutoModel
    from sklearn.feature_extraction.text import TfidfVectorizer
    from threadpoolctl import threadpool_limits
    torch.set_num_threads(2);torch.set_num_interop_threads(2)
    local=model_path();tokenizer=AutoTokenizer.from_pretrained(local,local_files_only=True,trust_remote_code=False)
    model=AutoModel.from_pretrained(local,local_files_only=True,trust_remote_code=False,use_safetensors=True).to('cpu').eval()
    vectors=encode(model,tokenizer,docs)
    baseline_path=Path(__file__).resolve().parent/'results/medjourney-readonly-v1/first-source-comparison.json'
    baseline=json.loads(baseline_path.read_text(encoding='utf-8'));results=[]
    with threadpool_limits(limits=2):
        vectorizer=TfidfVectorizer(analyzer='char',ngram_range=(2,4),norm='l2');sparse_docs=vectorizer.fit_transform(docs)
        for view in protocol['views']:
            texts=[c[view] for c in cases];legacy={r['case_id']:r for v in baseline['results'] if v['view']==view for r in v['rows']}
            scores={'resource_char_tfidf':(vectorizer.transform(texts)@sparse_docs.T).toarray(),
                    'frozen_bge_resource_docs':encode(model,tokenizer,texts)@vectors.T}
            for method,matrix in scores.items():
                item=measure(cases,labels,matrix,legacy);item.update(method=method,view=view);results.append(item)
                print(method,view,json.dumps(item['summary']))
    write_new(output,{'protocol_sha256':hashlib.sha256(frozen).hexdigest(),'results':results,
                      'encoder_fits':0,'case_supervised_fits':0,'tfidf_document_vocabulary_fit':1,
                      'calibration_fits':0,'clinical_validation':False,'raw_cases_or_resource_identity_text_persisted':False,
                      'result_is_not_serving_triage_or_actual_service_availability':True})


if __name__=='__main__':main()
