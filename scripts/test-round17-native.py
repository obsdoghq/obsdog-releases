"""Executable-only synthetic acceptance. Never targets an existing user profile."""
import hashlib,json,os,select,sqlite3,subprocess,sys,tempfile,time
from pathlib import Path
binary=Path(sys.argv[1]).resolve();out=Path(tempfile.mkdtemp(prefix='feedback17-',dir=sys.argv[2]));out.chmod(0o700)
env=dict(os.environ,OBSDOG_HOME=str(out/'profile'),OBSDOG_NO_UPDATE_NOTIFIER='1');records=[]
def run(*args,ok=True):
 p=subprocess.run([str(binary),*args],cwd=out,env=env,capture_output=True,text=True,timeout=45)
 r=dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr);records.append(r);(out/'commands.json').write_text(json.dumps(records,indent=2));assert (p.returncode==0)==ok,r
 return json.loads(p.stdout)
chosen=binary
if os.environ.get('OBSDOG_FEEDBACK16_SEED'):binary=Path(os.environ['OBSDOG_FEEDBACK16_SEED']).resolve()
space=run('space','default','--ensure','--format','json')['data']['space_id'];binary=chosen
db=Path(env['OBSDOG_HOME'])/'spaces'/space/'obsdog.db'
def imp(name,text):
 f=out/(name+'.md');f.write_text(text);return run('document','import','--space',space,'--file',str(f),'--actor-type','agent','--actor','fixture','--format','json')['data']
def read(id):return run('document','read','--space',space,'--id',id,'--with-block-ids','--format','json')['data']
def facts():
 with sqlite3.connect(f'file:{db}?mode=ro',uri=True) as c:
  names=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
  rows={n:sorted(c.execute('SELECT * FROM "'+n.replace('"','""')+'"').fetchall(),key=repr) for n in names}
  return hashlib.sha256(repr(rows).encode()).hexdigest()
a=imp('drift','# Root\n\n## Later\n\nFirst paragraph.\n\nSecond paragraph.\n\nThird paragraph.\n\n## Clean\n\nClean body.\n');doc=a['document']['document_id'];base=a['document']['current_revision_id'];blocks=a['blocks']
with sqlite3.connect(db) as c:
 c.create_function("obsdog_shared_membership",0,lambda:13,deterministic=True)
 c.create_function("obsdog_stable_baseline",0,lambda:12,deterministic=True)
 for b in blocks[2:5]:c.execute('UPDATE blocks SET parent_id=? WHERE block_id=?',(blocks[0]['block_id'],b['block_id']))
# Fixture corruption simulates a legal earlier-heading stale parent, not a product repair.
d=run('doctor','--space',space,'--format','json')['data'];summary=d['markdown_layout_summary'];assert summary['structural_blocks']==3 and summary['affected_documents']==1 and summary['remaining_within_scanned_documents']==0,d
assert [x['block_id'] for x in d['markdown_layout_issues']]==[b['block_id'] for b in blocks[2:5]]
split=('document','split','--space',space,'--id',doc,'--base-revision',base,'--blocks',blocks[5]['block_id'],'--title','Clean','--reason','synthetic split check','--actor-type','agent','--actor','fixture','--format','json','--dry-run')
probe=run(*split);assert probe['data']['reason_class']=='parent_context_would_change' and len(probe['data']['offending_block_ids'])==3 and probe['care_diagnostics']['total']==3,probe
repair=('document','repair-parent-context','--space',space,'--id',doc,'--base-revision',base,'--reason','repair synthetic parent drift','--actor-type','agent','--actor','fixture','--format','json')
before=facts();lock=sqlite3.connect(db);lock.execute('BEGIN IMMEDIATE')
try:
 preview=run(*repair,'--dry-run')['data'];assert preview['status']=='ready' and facts()==before,preview
 # Ordinary update uses its own validator and identifies drift without writing.
 update=('document','update','--space',space,'--id',doc,'--base-revision',base,'--file',str(out/'drift.md'),'--reason','same-shape preview','--actor-type','agent','--actor','fixture','--format','json')
 upd=run(*update,'--dry-run');assert upd['data']['status']=='deferred' and facts()==before,upd
finally:lock.rollback();lock.close()
applied=run(*repair)['data'];assert applied['status']=='applied',applied
after=read(doc);fields=('block_id','current_revision_id','content','ordinal','block_type','depth')
for x,y in zip(blocks,after['blocks']):
 for k in fields:assert x.get(k)==y.get(k),(k,x,y)
assert len(after['blocks'])==len(blocks)
replay=run(*repair)['data'];assert replay['replayed'] and replay['run_id']==applied['run_id']
stale=list(repair);stale[stale.index('--reason')+1]='different intent';assert 'revision conflict' in run(*stale,ok=False)['error']
assert run(*split[:-1],ok=False)['ok']==False # original exact base is now stale
newsplit=list(split);newsplit[newsplit.index('--base-revision')+1]=after['document']['current_revision_id']
assert run(*newsplit)['data']['status']=='ready'
newsplit[newsplit.index('--blocks')+1]=blocks[2]['block_id']+','+blocks[4]['block_id'];gap=run(*newsplit);assert gap['data']['reason_class']=='extraction_requires_contiguous_range' and gap['care_diagnostics']['total']==3 and gap['care_diagnostics']['offenders'][1]['block_id']==blocks[3]['block_id'],gap
assert run('doctor','--space',space,'--format','json')['data']['markdown_layout_summary']['structural_blocks']==0
# Ordinary move/update previews succeed under a different active writer and leave all facts fixed.
m=imp('move','# Move\n\nFirst sibling.\n\nSecond sibling.\n\nThird sibling.\n');mb=m['blocks'];mid=m['document']['document_id'];mrev=m['document']['current_revision_id'];before=facts();lock=sqlite3.connect(db);lock.execute('BEGIN IMMEDIATE')
try:
 move=run('block','move','--space',space,'--id',mb[1]['block_id'],'--after',mb[3]['block_id'],'--base-document-revision',mrev,'--reason','preview reorder','--actor-type','agent','--actor','fixture','--dry-run','--format','json')['data'];assert move['dry_run'] and not move['operation']['operation_id'],move
 update=run('document','update','--space',space,'--id',mid,'--base-revision',mrev,'--title','Preview title','--reason','preview title','--actor-type','agent','--actor','fixture','--dry-run','--format','json')['data'];assert update['status']=='ready',update
 assert facts()==before
finally:lock.rollback();lock.close()
# Actual stdio: a failed tool contains a structured error, never the success result.
with (out/'mcp.stderr').open('w') as stderr:
 p=subprocess.Popen([str(binary),'mcp','--space',space],env=env,cwd=out,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True,bufsize=1);seq=0
 def rpc(method,params):
  global seq
  seq+=1;p.stdin.write(json.dumps(dict(jsonrpc='2.0',id=seq,method=method,params=params))+'\n');p.stdin.flush();deadline=time.monotonic()+25
  while True:
   remaining=deadline-time.monotonic();assert remaining>0 and select.select([p.stdout],[],[],remaining)[0],'stdio timeout';r=json.loads(p.stdout.readline())
   if r.get('id')==seq:assert 'error' not in r,r;return r['result']
 try:
  rpc('initialize',dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='feedback17-fixture',version='1')));p.stdin.write(json.dumps(dict(jsonrpc='2.0',method='notifications/initialized'))+'\n');p.stdin.flush()
  error=rpc('tools/call',dict(name='obsdog_block_read',arguments=dict(block_id='blk_absent',revision_id='rev_absent')));assert error['isError'] and error['structuredContent']['error_code']=='tool_execution_failed' and 'result' not in error['structuredContent'],error
  (out/'mcp-error.json').write_text(json.dumps(error,indent=2))
  observed=rpc('tools/call',dict(name='obsdog_search',arguments=dict(query='paragraph',limit=1)))['structuredContent']['result']
  lock=sqlite3.connect(db);lock.execute('BEGIN IMMEDIATE')
  try:
   busy=rpc('tools/call',dict(name='obsdog_search_page',arguments=dict(retrieval_run_id=observed['retrieval_run_id'],page=2)))
   assert busy['isError'] and busy['structuredContent']['error_code']=='space_writer_busy' and 'result' not in busy['structuredContent'],busy
   (out/'mcp-busy-error.json').write_text(json.dumps(busy,indent=2))
  finally:lock.rollback();lock.close()
  p.stdin.close();assert p.wait(timeout=8)==0
 finally:
  if p.poll() is None:p.terminate();p.wait(timeout=8)
(out/'accepted.json').write_text(json.dumps(dict(parent_offenders=3,repair='existing_structural_grammar',preserved=list(fields),readonly_previews=True,stdio_error=True,commands=len(records)),indent=2));print(out)
