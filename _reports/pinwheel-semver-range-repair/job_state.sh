J=pinwheel-semver-range-repair-k3-20260926-213951
cd ~/tbruns
ps aux | grep -E 'harbor|stb' | grep -v grep | head
echo "--- console tail"
tail -15 "$J.console.log"
echo "--- trials"
ls "$J"
for t in "$J"/pinwheel*/; do
  echo "$t reward=$(cat "$t/verifier/reward.txt" 2>/dev/null) calls=$(wc -l < "$t/agent/api-calls.jsonl" 2>/dev/null)"
  [ -f "$t/result.json" ] && python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(' exc:',(d.get('exception_info') or {}).get('exception_type'))" "$t/result.json"
done
