import requests

headers = {'PRIVATE-TOKEN': 'glpat-QxlxWOSguat1v29LsOf_7G86MQp1OmgH.01.0w1a7iasg'}
r = requests.get('https://datahub-dev.ipk-gatersleben.de/api/v4/groups/55/projects', headers=headers)
projects = r.json()

print("Projects with 'physio' in path:")
for p in projects:
    if 'physio' in p['path'].lower():
        print(f"{p['id']}: {p['name']} ({p['path']})")
