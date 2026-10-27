"""Run real executables on private synthetic profiles, never a user's DB."""
import hashlib,json,os,select,sqlite3,subprocess,sys,tempfile,time
from pathlib import Path
binary=Path(sys.argv[1]).resolve();mode=sys.argv[3] if len(sys.argv)>3 else 'candidate'
out=Path(tempfile.mkdtemp(prefix='feedback16-'+mode+'-',dir=sys.argv[2]));out.chmod(0o700)
env=dict(os.environ,OBSDOG_HOME=str(out/'profile'),OBSDOG_NO_UPDATE_NOTIFIER='1')
records=[]
def run(*args,ok=True):
 start=time.monotonic();p=subprocess.run([str(binary),*args],env=env,cwd=out,capture_output=True,text=True,timeout=45)
 entry=dict(args=args,exit=p.returncode,elapsed=time.monotonic()-start,stdout=p.stdout,stderr=p.stderr);records.append(entry);(out/'commands.json').write_text(json.dumps(records,indent=2))
 assert (p.returncode==0)==ok,entry
 j=json.loads(p.stdout);return j['data'] if ok else j
chosen=binary
if os.environ.get('OBSDOG_FEEDBACK16_SEED'):binary=Path(os.environ['OBSDOG_FEEDBACK16_SEED']).resolve()
space=run('space','default','--ensure','--format','json')['space_id']
binary=chosen
db=Path(env['OBSDOG_HOME'])/'spaces'/space/'obsdog.db'
def imp(name,text):
 f=out/(name+'.md');f.write_text(text);return run('document','import','--space',space,'--file',str(f),'--actor-type','agent','--actor','fixture','--format','json')
def read(id):return run('document','read','--space',space,'--id',id,'--with-block-ids','--format','json')
a=imp('first','# First\n\nquartzneedle exact original.\n\nSecond paragraph.\n')
b=imp('second','# Second\n\nAnother synthetic topic.\n')
observed=run('search','--space',space,'--query','quartzneedle','--actor-type','agent','--actor','fixture','--format','json')
runid=observed['retrieval_run_id'];assert runid and observed['hits']
with sqlite3.connect(db) as c:c.execute("UPDATE snapshot_supersessions SET superseded_at='2020-01-01T00:00:00.000000000Z'")
def facts():
 with sqlite3.connect(f'file:{db}?mode=ro',uri=True) as c:return c.execute('SELECT (SELECT COUNT(*) FROM documents),(SELECT COUNT(*) FROM revisions),(SELECT COUNT(*) FROM events),(SELECT COUNT(*) FROM retrieval_runs)').fetchone()
lock=sqlite3.connect(db);lock.execute('BEGIN IMMEDIATE')
try:
 before=facts()
 run('space','status','--space',space,'--format','json')
 probe=run('search','--space',space,'--query','quartzneedle','--no-observe','--format','json');assert not probe['retrieval_run_id']
 opened=run('search','open','--space',space,'--run',runid,'--rank','1','--actor-type','agent','--actor','fixture','--format','json',ok=mode!='baseline')
 if mode=='baseline':assert 'writer' in opened['error'].lower()
 else:
  assert opened['markdown']=='quartzneedle exact original.' and opened['observation']['persistence']=='not_recorded' and not opened['event_ids']
  assert opened['writer_reservation']['writer_owner']['pid']==os.getpid(),opened
  assert records[-1]['elapsed']<3,records[-1]
  target=opened['next_read'];exact=run('block','show','--space',space,'--id',target['block_id'],'--revision',target['revision_id'],'--format','json');assert exact['content']==opened['markdown']
  search=run('search','--space',space,'--query','quartzneedle','--actor-type','agent','--actor','fixture','--format','json');assert not search['retrieval_run_id'] and search['observation']['retry_safe']
  assert search['hits'][0]['next_read']['revision_id']==target['revision_id']
  used=run('search','use','--space',space,'--run',runid,'--rank','1','--actor-type','agent','--actor','fixture','--format','json',ok=False);assert 'opened' in used['error']
  run('space','compact','--space',space,'--format','json')
 if mode!='baseline':
  with (out/'mcp.stderr').open('w') as stderr:
   mcp=subprocess.Popen([str(binary),'mcp','--space',space],env=env,cwd=out,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True,bufsize=1)
   try:
    seq=0
    def rpc(method,params):
     global seq
     seq+=1;mcp.stdin.write(json.dumps(dict(jsonrpc='2.0',id=seq,method=method,params=params))+'\n');mcp.stdin.flush()
     deadline=time.monotonic()+8
     while True:
      remaining=deadline-time.monotonic();assert remaining>0 and select.select([mcp.stdout],[],[],remaining)[0],'MCP timed out'
      reply=json.loads(mcp.stdout.readline())
      if reply.get('id')==seq:
       assert 'error' not in reply,reply
       return reply['result']
    rpc('initialize',dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='feedback16-fixture',version='1')))
    mcp.stdin.write(json.dumps(dict(jsonrpc='2.0',method='notifications/initialized'))+'\n');mcp.stdin.flush()
    response=rpc('tools/call',dict(name='obsdog_search_open',arguments=dict(retrieval_run_id=runid,rank=1)))
    assert not response.get('isError') and response['_meta']['obsdog.ai/timings']['writer_admissions']
    mo=response['structuredContent']['result'];assert mo['observation']['persistence']=='not_recorded' and not mo['event_ids']
    t=mo['next_read'];exact=rpc('tools/call',dict(name='obsdog_block_read',arguments=dict(document_id=t['document_id'],block_id=t['block_id'],revision_id=t['revision_id'])))
    assert exact['structuredContent']['block']['content']==mo['markdown']
    ms=rpc('tools/call',dict(name='obsdog_search',arguments=dict(query='quartzneedle',limit=3)))['structuredContent']['result']
    assert ms['observation']['persistence']=='not_recorded' and not ms['retrieval_run_id']
    (out/'mcp-accepted.json').write_text(json.dumps(dict(open=mo,search=ms),indent=2))
    mcp.stdin.close();assert mcp.wait(timeout=8)==0
   finally:
    if mcp.poll() is None:mcp.terminate();mcp.wait(timeout=8)
 assert facts()==before
 # Force an actual supported three-block append to contend. Old35 fails in
 # unrelated snapshot_cleanup; candidate must identify its actual Care write.
 f=out/'append.md';f.write_text('## Supported append\n\nFirst new paragraph.\n\nSecond new paragraph.\n')
 args=('document','append','--space',space,'--id',a['document']['document_id'],'--base-revision',a['document']['current_revision_id'],'--file',str(f),'--reason','synthetic bounded append','--actor-type','agent','--actor','fixture','--format','json')
 failed=run(*args,ok=False)
 assert failed['diagnostics']['operation']==('snapshot_cleanup' if mode=='baseline' else 'care_append-document'),failed
 if mode!='baseline':
  assert failed['mutation_state']['expected_document_revision']==a['document']['current_revision_id']
  assert any('phase=' in x for x in records[-1]['stderr'].splitlines()),records[-1]
 assert facts()==before
finally:lock.rollback();lock.close()
if mode=='baseline':
 (out/'accepted.json').write_text(json.dumps({'baseline':'35','open_failure':'writer_admission','append_failure':'snapshot_cleanup','records':len(records)},indent=2));print(out);sys.exit(0)
# Retry the SAME exact append after release; no new import/draft/fork.
applied=run(*args);assert applied['status']=='applied'
after=read(a['document']['document_id']);assert len(after['blocks'])==len(a['blocks'])+3
opened=run('search','open','--space',space,'--run',runid,'--rank','1','--actor-type','agent','--actor','fixture','--format','json');assert opened['observation']['persistence']=='recorded' and len(opened['event_ids'])==2
# First-class whole-document retirement has no sink. Exact retry finds the
# original receipt even though active roots have disappeared.
target=b['document']['document_id'];base=b['document']['current_revision_id']
retire=('document','retire','--space',space,'--id',target,'--base-revision',base,'--reason','retire synthetic experiment','--actor-type','agent','--actor','fixture','--format','json')
before=facts();assert run(*retire,'--dry-run')['status']=='ready';assert facts()==before
retired=run(*retire);assert retired['status']=='applied'
replay=run(*retire);assert replay['replayed'] and replay['run_id']==retired['run_id']
assert target not in [x['document_id'] for x in run('document','list','--space',space,'--format','json')]
assert target in [x['document_id'] for x in run('document','list','--space',space,'--include-retired','--format','json')]
assert read(target)['document']['lifecycle_state']=='retired'
assert all(x['document_id']!=target for x in run('search','--space',space,'--query','Another synthetic topic','--include-deprecated','--no-observe','--format','json')['hits'])
# VACUUM may change physical rowids, but authored history/receipts/fences/pinned
# exact content and private capture drafts must remain identical.
def protected():
 with sqlite3.connect(f'file:{db}?mode=ro',uri=True) as c:
  tables=['documents','blocks','revisions','events','retrieval_runs','retrieval_hits','evaluations']
  data={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}
  data['schema']=c.execute("SELECT name,sql FROM sqlite_master WHERE name LIKE 'storage_writer_%' ORDER BY name").fetchall()
  return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
with sqlite3.connect(db) as c:c.executescript('CREATE TABLE synthetic_free(id INTEGER PRIMARY KEY,p BLOB);INSERT INTO synthetic_free(p) VALUES(zeroblob(2097152));DELETE FROM synthetic_free;DROP TABLE synthetic_free;')
prior=protected();drafts=run('document','drafts','--space',space,'--format','json')
assert drafts['drafts'] and all('title' in x and 'source_path' in x for x in drafts['drafts'])
preview=run('space','compact','--space',space,'--format','json');assert preview['before']['free_pages']>0
compacted=run('space','compact','--space',space,'--apply','--format','json');assert compacted['applied'] and compacted['after']['page_count']<preview['before']['page_count'];assert protected()==prior
assert run('document','drafts','--space',space,'--format','json')==drafts
assert run('search','open','--space',space,'--run',runid,'--rank','1','--actor-type','agent','--actor','fixture','--format','json')['markdown']==opened['markdown']
summary={'accepted':True,'mode':mode,'space_schema':sqlite3.connect(db).execute('SELECT MAX(version) FROM schema_migrations').fetchone()[0],'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'records':len(records),'compaction':compacted,'reporter_database_accessed':False}
(out/'accepted.json').write_text(json.dumps(summary,indent=2));print(out)
