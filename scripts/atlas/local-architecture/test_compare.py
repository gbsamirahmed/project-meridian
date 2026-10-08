"""Decision comparison tests; neither a runtime nor production SQL schema."""
import tempfile,unittest,sqlite3,subprocess,sys
from contextlib import closing
from pathlib import Path
import compare as C
class MetadataComparison(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows,cls.members,cls.edges,cls.geoms,cls.x,cls.sources=C.load_population()
  cls.temp=tempfile.TemporaryDirectory(dir=C.OUT);cls.path=Path(cls.temp.name)/'index.sqlite';C.build(cls.path,cls.rows,cls.members,cls.edges,cls.geoms,'fixture')
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_retained_cardinalities(self):
  self.assertEqual((len(self.rows),len(self.geoms),len(self.members),len(self.edges)),(250,38,1006,200))
 def test_all_queries_and_qualification_bodies(self):
  with closing(sqlite3.connect(self.path)) as c:
   byid={r['id']:r for r in self.rows}
   for q in C.cases(self.rows,self.members,self.edges,self.geoms,self.x):
    ids=C.sql(q,c,self.geoms);self.assertEqual(ids,C.scan(q,self.rows,self.members,self.edges,self.geoms))
    for i in ids:self.assertEqual(C.read_body(c,i),byid[i]['body'])
 def test_null_identity_is_preserved(self):
  with closing(sqlite3.connect(self.path)) as c:self.assertGreater(c.execute('SELECT count(*) FROM record WHERE feature IS NULL').fetchone()[0],0)
 def test_failed_transaction_has_no_partial_rows(self):
  with closing(sqlite3.connect(self.path)) as c:
   with self.assertRaises(sqlite3.IntegrityError):
    with c:
     c.execute("INSERT INTO record VALUES('partial','test',NULL,0,'{}')");c.execute("INSERT INTO record VALUES('partial','test',NULL,0,'{}')")
   self.assertEqual(c.execute("SELECT count(*) FROM record WHERE id='partial'").fetchone()[0],0)
 def test_process_interruption_rolls_back(self):
  code="import sqlite3,sys,os;c=sqlite3.connect(sys.argv[1]);c.execute('BEGIN IMMEDIATE');c.execute(\"INSERT INTO record VALUES('crash','test',NULL,0,'{}')\");os._exit(91)"
  p=subprocess.run([sys.executable,'-c',code,str(self.path)],capture_output=True);self.assertEqual(p.returncode,91)
  with closing(sqlite3.connect(self.path)) as c:self.assertEqual(c.execute("SELECT count(*) FROM record WHERE id='crash'").fetchone()[0],0)
 def test_missing_readonly_index_fails_without_creation(self):
  p=Path(self.temp.name)/'missing.sqlite'
  with self.assertRaises(sqlite3.OperationalError):sqlite3.connect('file:'+p.as_posix()+'?mode=ro',uri=True)
  self.assertFalse(p.exists())
 def test_wrong_binding_and_corruption_fail_on_actual_files(self):
  seal=C.digest(self.path)
  with self.assertRaises(AssertionError):C.open_verified(self.path,seal,'wrong-components')
  corrupt=Path(self.temp.name)/'corrupt.sqlite';corrupt.write_bytes(b'broken index')
  with self.assertRaises(AssertionError):C.open_verified(corrupt,seal,'fixture')
 def test_rtree_rounding_is_only_candidate_selection(self):
  with closing(sqlite3.connect(self.path)) as c:
   for f,g in self.geoms.items():
    b=g.bounds;q={'mode':'space','bounds':list(b)};self.assertEqual(C.sql(q,c,self.geoms),C.scan(q,self.rows,self.members,self.edges,self.geoms))
C.read_body=lambda c,i:__import__('json').loads(c.execute('SELECT body FROM record WHERE id=?',(i,)).fetchone()[0])
if __name__=='__main__':unittest.main()
