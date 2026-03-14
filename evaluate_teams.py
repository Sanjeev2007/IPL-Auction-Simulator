import csv
from collections import defaultdict

scores = {}
with open('data/enriched/derived_scores.csv') as f:
    for row in csv.DictReader(f):
        scores[row['Player_ID']] = row

names = {}
name_to_id = {}
with open('data/enriched/players_master.csv') as f:
    for row in csv.DictReader(f):
        names[row['Player_ID']] = row
        name_to_id[row['Player Name'].lower()] = row['Player_ID']

def find_player(pname):
    pname_l = pname.lower()
    for n in name_to_id:
        if pname_l in n or n in pname_l:
            return name_to_id[n]
    if 'shikhar' in pname_l: return name_to_id['shikhar dhawan']
    if 'vk' in pname_l: return name_to_id['virat kohli']
    if 'saha' in pname_l: return name_to_id['wriddhiman saha']
    if 'klaasen' in pname_l: return name_to_id['heinrich klaasen']
    if 'pandya' in pname_l and 'h.' in pname_l: return name_to_id['hardik pandya']
    if 'nabi' in pname_l: return name_to_id['mohammed nabi']
    if 'tewatia' in pname_l: return name_to_id['rahul tewatia']
    if 'starc' in pname_l: return name_to_id['mitchell starc']
    if 'avesh' in pname_l: return name_to_id['avesh khan']
    if 'sandeep' in pname_l: return name_to_id['sandeep sharma']
    if 'shami' in pname_l: return name_to_id['mohammed shami']
    if 'sai' in pname_l: return name_to_id['sai sudharsan']
    if 'powell' in pname_l: return name_to_id['rovman powell']
    if 'sky' in pname_l: return name_to_id['sky']
    if 'david' in pname_l and 'tim' in pname_l: return name_to_id['tim david']
    if 'brevis' in pname_l: return name_to_id['dewald brevis']
    if 'marsh' in pname_l: return name_to_id['mitchell marsh']
    if 'nissanka' in pname_l: return name_to_id['pathum nissanka']
    if 'buttler' in pname_l: return name_to_id['jos buttler']
    if 'jagadeesan' in pname_l: return name_to_id['narayana jagadeesan']
    if 'krunal' in pname_l: return name_to_id['krunal pandya']
    if 'axar' in pname_l: return name_to_id['axar patel']
    if 'nkr' in pname_l: return name_to_id['nkr']
    if 'ashwani' in pname_l: return name_to_id['ashwani kumar']
    if 'siraj' in pname_l: return name_to_id['mohammed siraj']
    if 'wadhera' in pname_l: return name_to_id['nehal wadhera']
    if 'smith' in pname_l: return name_to_id['steve smith']
    if 'rahane' in pname_l: return name_to_id['ajinkya rahane']
    if 'gill' in pname_l: return name_to_id['shubman gill']
    if 'shashank' in pname_l: return name_to_id['shashank singh']
    if 'mhatre' in pname_l: return name_to_id['ayush mhatre']
    if 'r. sharma' in pname_l: return name_to_id['rohit sharma']
    if 'faf' in pname_l: return name_to_id['faf du plessis']
    if 'dhoni' in pname_l: return name_to_id['msd']
    if 'maxwell' in pname_l: return name_to_id['glenn maxwell']
    if 'pollard' in pname_l: return name_to_id['kieron pollard']
    if 'jadeja' in pname_l: return name_to_id['ravindra jadeja']
    if 'arshdeep' in pname_l: return name_to_id['arshdeep singh']
    if 'badoni' in pname_l: return name_to_id['ayush badoni']
    if 'ashutosh' in pname_l: return name_to_id['ashutosh sharma']
    if 'head' in pname_l: return name_to_id['travis head']
    if 'stubbs' in pname_l: return name_to_id['tristan stubbs']
    if 'tilak' in pname_l: return name_to_id['tilak varma']
    if 'samad' in pname_l: return name_to_id['abdul samad']
    if 'patidar' in pname_l: return name_to_id['rajat patidar']
    if 'pooran' in pname_l: return name_to_id['nicolas pooran']
    if 'samson' in pname_l: return name_to_id['sanju samson']
    if 'pant' in pname_l: return name_to_id['rishabh pant']
    if 'narine' in pname_l: return name_to_id['sunil narine']
    if 'russel' in pname_l: return name_to_id['andre russell']
    if 'khaleel' in pname_l: return name_to_id['khaleel ahmed']
    if 'harshit' in pname_l: return name_to_id['harshit rana']
    if 'boult' in pname_l: return name_to_id['trent boult']
    if 'miller' in pname_l: return name_to_id['david miller']
    if 'rizvi' in pname_l: return name_to_id['sameer rizvi']
    if 'abhi' in pname_l: return name_to_id['abhishek sharma']
    if 'finn' in pname_l: return name_to_id['finn allen']
    if 'bethell' in pname_l: return name_to_id['jacob bethell']
    if 'd. devdutt' in pname_l or 'padikkal' in pname_l: return name_to_id['devdutt padikkal']
    if 'p shaw' in pname_l: return name_to_id['prithvi shaw']
    if 'parag' in pname_l: return name_to_id['riyan parag']
    if 'rahul' in pname_l: return name_to_id['kl rahul']
    if 'holder' in pname_l: return name_to_id['jason holder']
    if 'sundar' in pname_l: return name_to_id['washy sundar']
    if 'cummins' in pname_l: return name_to_id['pat cummins']
    if 'dayal' in pname_l: return name_to_id['yash dayal']
    if 'sant' in pname_l: return name_to_id['mitch santner']
    if 'jitesh' in pname_l: return name_to_id['jitesh sharma']
    if 'boom' in pname_l: return name_to_id['boom boom']
    if 'rutu' in pname_l: return name_to_id['ruturaj gaikwad']
    if 'urvil' in pname_l: return name_to_id['urvil patel']
    if 'short' in pname_l: return name_to_id['mathew short']
    if 'sarfraz' in pname_l: return name_to_id['sarfaraz khan']
    if 'rutherford' in pname_l: return name_to_id['sherfane rutherford']
    if 'dhawan' in pname_l: return name_to_id['shikhar dhawan']
    if 'mcgurk' in pname_l: return name_to_id['fraser mcgurk']
    if 'markram' in pname_l: return name_to_id['markram']
    if 'shreyas' in pname_l: return name_to_id['shreyas iyer']
    if 'suryavanshi' in pname_l: return name_to_id['vaibhav suryavanshi']
    if 'ishan' in pname_l: return name_to_id['ishan kishan']
    if 'dube' in pname_l: return name_to_id['shivam dube']
    if 'vipraj' in pname_l: return name_to_id['vipraj nigam']
    if 'jansen' in pname_l: return name_to_id['marco jansen']
    if 'archer' in pname_l: return name_to_id['jofra archer']
    if 'bhuvi' in pname_l: return name_to_id['bhuvneshwar kumar']
    return None

teams = {
    'BI (You)': ['kane williamson', 'rilee rossouw', 'priyansh arya', 'yashasvi jaiswal', 'vk', 's. hetmyer', 'w. saha', 'h. klaasen', 'h. pandya', 'm. nabi', 'r. tewatia', 'm. starc', 'avesh khan', 'sandeep sharma'],
    'RKL': ['shami', 'sai', 'powell', 'sky', 'tim david', 'brevis', 'marsh', 'nissanka', 'buttler', 'jagadeesan', 'krunal', 'axar', 'nkr', 'ashwani', 'siraj'], # Removed 'narayan' for now
    'DD': ['wadhera', 'smith', 'rahane', 'gill', 'shashank', 'mhatre', 'r. sharma', 'faf', 'dhoni', 'maxwell', 'pollard', 'jadeja', 'arshdeep'],
    'PR': ['badoni', 'ashutosh', 'head', 'stubbs', 'tilak', 'samad', 'patidar', 'pooran', 'samson', 'pant', 'narine', 'russel', 'khaleel', 'harshit', 'boult'],
    'RC': ['miller', 'rizvi', 'abhi', 'finn', 'bethell', 'padikkal', 'p shaw', 'parag', 'rahul', 'holder', 'sundar', 'cummins', 'dayal', 'santner', 'jitesh', 'boom'],
    'SK': ['rutu', 'urvil', 'short', 'sarfraz', 'rutherford', 'dhawan', 'mcgurk', 'markram', 'shreyas', 'suryavanshi', 'ishan', 'dube', 'vipraj', 'jansen', 'archer', 'bhuvi']
}

def evaluate(team_players):
    pids = []
    for p in team_players:
        pid = find_player(p)
        if pid:
            pids.append(pid)
    if not pids: return 0, 0, 0, 0, []
    
    avg_bat = sum(float(scores[p]['bat_rating']) for p in pids)/len(pids)
    avg_bowl = sum(float(scores[p]['bowl_rating']) for p in pids)/len(pids)
    avg_ovr = sum(float(scores[p]['overall_rating']) for p in pids)/len(pids)
    
    # Best XI logic (simplistic)
    sorted_p = sorted(pids, key=lambda x: float(scores[x]['overall_rating']), reverse=True)
    xi = sorted_p[:11]
    xi_ovr = sum(float(scores[p]['overall_rating']) for p in xi)/len(xi)
    
    # Bowling depth (bowl > 40)
    bd = sum(1 for p in pids if float(scores[p]['bowl_rating']) > 40)
    
    return avg_bat, avg_bowl, avg_ovr, xi_ovr, bd, pids

results = []
for t, plist in teams.items():
    bat, bowl, ovr, xi, bd, pids = evaluate(plist)
    results.append({
        'Team': t, 'Bat': bat, 'Bowl': bowl, 'Overall': ovr, 
        'XI_Ovr': xi, 'BowlDepth': bd, 'Count': len(pids)
    })

results.sort(key=lambda x: x['XI_Ovr'], reverse=True)

print(f'{"Team":<10} {"Size":<6} {"Avg Bat":<10} {"Avg Bowl":<10} {"Avg Ovr":<10} {"Best XI":<10} {"Bowl >40":<10}')
print('-'*70)
for r in results:
    print(f'{r["Team"]:<10} {r["Count"]:<6} {r["Bat"]:<10.1f} {r["Bowl"]:<10.1f} {r["Overall"]:<10.1f} {r["XI_Ovr"]:<10.1f} {r["BowlDepth"]:<10}')

