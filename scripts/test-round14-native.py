"""Native CLI maintenance acceptance using only disposable synthetic profiles."""
import json,os,sqlite3,subprocess,tempfile,time
from pathlib import Path
import sys
BIN=Path(sys.argv[1]).resolve()
OLD=Path(sys.argv[2]).resolve()
OUT=Path(tempfile.mkdtemp(prefix='native-maintenance-',dir=sys.argv[3]))
PROFILE=OUT/'profile'
ENV=dict(os.environ,OBSDOG_HOME=str(PROFILE),OBSDOG_NO_UPDATE_NOTIFIER='1')
RECORDS=[]
def run(*args,ok=True,binary=BIN):
 start=time.monotonic();p=subprocess.run([str(binary),*args],cwd=OUT,env=ENV,capture_output=True,text=True,timeout=45)
 r=dict(args=args,code=p.returncode,elapsed=time.monotonic()-start,stdout=p.stdout,stderr=p.stderr)
 RECORDS.append(r);(OUT/'commands.json').write_text(json.dumps(RECORDS,indent=2))
 assert (p.returncode==0)==ok,r
 return json.loads(p.stdout)['data'] if p.returncode==0 and p.stdout.startswith('{') else r

def counts(db):
 with sqlite3.connect(f'file:{db}?mode=ro',uri=True) as c:
  return c.execute('SELECT (SELECT count(*) FROM documents),(SELECT count(*) FROM revisions),(SELECT count(*) FROM events),(SELECT count(*) FROM retrieval_runs)').fetchone()

def imported(name,body,binary=BIN):
 p=OUT/(name+'.md');p.write_text(body)
 return run('document','import','--file',str(p),'--format','json',binary=binary)
space=run('space','default','--ensure','--format','json')['space_id']
db=PROFILE/'spaces'/space/'obsdog.db'
imported('dedupe','# Dedupe\n\nSynthetic dedupe body.\n')
before=counts(db)
run('search','--format','json','dedupe','--space','spc_synthetic','--no-observe',ok=False)
assert counts(db)==before
run('doctor','--require-capability','capture_recovery_v1','--guidance-version','0.3.32','--minimum-cli','v0.2.34','--format','json')
assert counts(db)==before
for name,content in [('inline',"Use `Output['items'][number]`."),('fenced',"```ts\nOutput['items'][number]\n```"),('plain','Use indexed output items.')]:
 d=imported(name,'# Guide\n\nKeep.\n\n## Extract\n\n'+content+'\n')
 args=('document','split','--id',d['document']['document_id'],'--base-revision',d['document']['current_revision_id'],'--blocks',d['blocks'][2]['block_id'],'--title',name,'--reason','Synthetic acceptance','--format','json')
 frozen=counts(db)
 checked=run(*args,'--dry-run','--with-title-heading');assert checked['status']=='ready' and counts(db)==frozen
 applied=run(*args,'--with-title-heading');assert applied['status']=='applied'
 target=applied['after'][1];assert target['blocks'][0]['content']=='# '+name

# A distinct process holds the actual SQLite write lock. Read-only status and
# diagnostic search must still work; normal search may explicitly lose telemetry.
lock=sqlite3.connect(str(db));lock.execute('BEGIN IMMEDIATE')
try:
 frozen=counts(db)
 status=run('space','status','--format','json');assert counts(db)==frozen
 run('search','--no-observe','--query','dedupe','--format','json');assert counts(db)==frozen
 fallback=run('search','--query','dedupe','--format','json')
 assert fallback['observation_status']=='not_recorded_writer_busy' and not fallback.get('run_id')
 assert counts(db)==frozen
 drafts=run('document','drafts','--format','json')['drafts'];oldids={d['draft_id'] for d in drafts}
 f=OUT/'locked-capture.md';f.write_text('# Recover me\n\nPreserved unique synthetic knowledge.\n')
 failed=run('document','import','--file',str(f),'--format','json',ok=False)
 assert counts(db)==frozen and 'capture_' in failed['stdout']
 pending=[d for d in run('document','drafts','--format','json')['drafts'] if d['draft_id'] not in oldids]
 assert len(pending)==1 and pending[0]['status']=='pending_or_unknown'
 draft=pending[0]['draft_id']
finally:
 lock.rollback();lock.close()
original=run('document','drafts','--draft',draft,'--format','json')
f.unlink() # This newly created test source is disposable; recovery needs only draft.
recovered=run('document','recover','--draft',draft,'--actor-type',original['actor_type'],'--actor',original['actor_id'],'--format','json')
assert not recovered.get('replayed')
assert counts(db)[0]==frozen[0]+1
replayed=run('document','recover','--draft',draft,'--actor-type',original['actor_type'],'--actor',original['actor_id'],'--format','json')
assert replayed['replayed'] and replayed['document']['document_id']==recovered['document']['document_id']
assert counts(db)[0]==frozen[0]+1

# Isolate the new Care floor from the schema13 baseline: v0.2.32 creates schema12.
ENV['OBSDOG_HOME']=str(OUT/'legacy-profile')
run('space','default','--ensure','--format','json',binary=OLD)
d=imported('old-compatible','# Legacy\n\nKeep.\n\n## Section\n\nExtract this.\n',binary=OLD)
a=run('document','split','--id',d['document']['document_id'],'--base-revision',d['document']['current_revision_id'],'--blocks',d['blocks'][2]['block_id'],'--title','Section','--reason','Synthetic floor acceptance','--with-title-heading','--format','json')
assert a['status']=='applied'
p=OUT/'old-write.md';p.write_text('# Old writer\n\nMust refuse.\n')
old=run('document','import','--file',str(p),'--format','json',binary=OLD,ok=False)
assert 'care-capable writer required' in old['stdout'],old
(OUT/'accepted.json').write_text(json.dumps(dict(platform=os.uname().sysname,version=subprocess.check_output([str(BIN),'version'],text=True).strip(),checks=['strict_flags_before_space','doctor_no_observation','code_span_and_fence','dry_run_no_changes','atomic_h1','readonly_under_real_writer_lock','honest_fallback_no_run','failed_capture_no_commit','draft_recovers_missing_source','same_receipt_no_duplicate','actual_v0.2.32_writer_refusal']),indent=2))
print(OUT)
