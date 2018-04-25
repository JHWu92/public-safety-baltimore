# coding=utf-8
import pandas as pd


def similarity(a, b):
    import difflib
    if len(a) == 0 or len(b) == 0:
        return -1
    a, b = a.lower(), b.lower()
    match_size = sum([m.size for m in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks()]) * 1.0
    longer_size, shorter_size = (len(b), len(a)) if len(a) < len(b) else ((len(a), len(b)))
    longer_size = shorter_size if (longer_size / 1.5) <= shorter_size else longer_size / 1.5
    #     return match_size/(longer_size+shorter_size)*2
    return match_size / shorter_size


# field interview: https://bizfluent.com/info-8223154-field-interview.html
# false pretense: Under federal law, obtaining money or property through false pretenses as part of a scheme or artifice to defraud, and using means of interstate commerce such as a telephone, is illegal....
# aed nonbreathing: An automated external defibrillator (AED) is a portable electronic device that automatically diagnoses the life-threatening cardiac arrhythmias of ventricular fibrillation and pulseless ventricular tachycardia,
# intoxicated pers: intoxicated person? Intoxication. A state in which a person's normal capacity to act or reason is inhibited by alcohol or drugs.
# search & seizure: Search and Seizure is a procedure used in many civil law and common law legal systems by which police or other authorities and their agents, who, suspecting that a crime has been committed, commence a search of a person's property and confiscate any relevant evidence found in connection to the crime
# disorderly conduct: https://criminal.findlaw.com/criminal-charges/disturbing-the-peace.html
# protective/peach order: https://www.peoples-law.org/comparing-protective-and-peace-orders

DROP_IRRELEVANT = [
    # no info
    '911/no voice', '911/no  voice', 'see text', 'other', '911/hangup', 'trouble unknown', 'possible', 'mistake',
    # traffic related
    'transport', 'traffic stop', 'hit and run', 'auto accident', 'auto acc/injury',
    'private tow', 'prkg complaint', 'towed vehicle', 'dwi', 'disabled veh',
    'tow - do not use', 'traffic control', 'parking cmpt',
    # crime code?
    '7c', '6j', '5g',
    # other
    'lab request', 'ra police', 'unfounded', 'repo', 'police info', 'signal out', 'unauthorized use', 'notify',
    '56', 'closed call', 'dept accident', 'school/church', 'request service', 'personal relief'
]
TBD_IRRELEVANT = [
    # police related?
    'investigate', 'investigate auto', 'foot patrol',
    'check well being', 'check wellbeing', 'chk well being', 'ck well being',
    'business check', 'bank check', 'follow up',
    # lost and found
    'recovered veh', 'recover property', 'lost property', 'get belongings',
    # medical related
    'narcotics inside', 'narcoticsoutside', 'narcotics onview', 'aed nonbreathing', 'nonbreathing / a',
    # environment?
    'fire',
    # disturb
    'family disturb', 'animal disturb', 'vehicle disturb', 'dog bite', 'street disturb',
    # other
    'invest trouble', 'invest', 'supv complaint', 'sick case', 'unknown trouble', 'exparte',
    'behavior crisis', 'behaviorl crisis', 'court', 'ill/dump in prog']
DROP_NOISE = ['inv', 'ep', 'auto', 'p', 'j', 'car fire', 'gather belonging', 'violation', 'cds', 'pp', 'y', 'anon',
              'in person', 'n', 'scam', 'protect', 'o', 'looting', 'hold up', 'car', 'prot', 'missing', 'invst',
              'trepass']
WRONG_MATCH = {'arson': 'arson'}
CANDIDATE2CATEGORY = {'disorderly'      : 'disorderly conduct',
                      'common assault'  : 'assault',
                      'silent alarm'    : 'insecurity',
                      'repairs/service' : 'insecurity',
                      'burglary'        : 'burglary',
                      'suspicious pers' : 'insecurity',
                      'larceny'         : 'theft_larceny',
                      'field interview' : 'insecurity',
                      'auto theft'      : 'theft_larceny',
                      'wanted on warr'  : 'insecurity',
                      'destruct prop'   : 'insecurity',
                      'armed person'    : 'insecurity',
                      'foot  patrol'    : 'insecurity',
                      'loud music'      : 'disorderly conduct',
                      'aggrav assault'  : 'assault',
                      'missing person'  : 'missing person',
                      'juv disturbance' : 'disorderly conduct',
                      'warrant service' : 'insecurity',
                      'false pretense'  : 'other offense',
                      'robbery armed'   : 'robbery',
                      'mental case'     : 'mental case',
                      'dischrg firearm' : 'shooting',
                      'lying in street' : 'disorderly conduct',
                      'intoxicated pers': 'disorderly conduct',
                      'prostitution'    : 'other offense',
                      'audible alarm'   : 'insecurity',
                      'shooting'        : 'shooting',
                      'by threat'       : 'other offense',
                      'street obstruct' : 'disorderly conduct',
                      'holdup alarm'    : 'insecurity',
                      'subject stop'    : 'insecurity',
                      'injured person'  : 'insecurity',
                      'inv stop'        : 'insecurity',
                      'gambling'        : 'other offense',
                      'cutting'         : 'other offense',
                      'search&seizure'  : 'insecurity',
                      'escort'          : 'insecurity',
                      'protective order': 'abuse',
                      'peace order'     : 'abuse',
                      'car jacking'     : 'theft_larceny',
                      'animal cruelty'  : 'disorderly conduct',
                      'prowler'         : 'burglary',
                      'handgun violatio': 'shooting',
                      'protect order'   : 'abuse',
                      'arson'           : 'arson', 'bike larceny': 'theft_larceny',
                      'destruct propty' : 'insecurity',
                      'larcency'        : 'theft_larceny',
                      'larceny f/auto'  : 'theft_larceny',
                      'robbery unarmed' : 'robbery',

                      }


def main():
    df911 = pd.read_csv('../raw/911_Police_Calls_for_Service.csv', sep=';')
    df911['description_clean'] = df911.description.apply(lambda x: x.replace('*', ' ').strip().lower())
    raw2clean = {row.description: row.description_clean for _, row in df911.drop_duplicates('description').iterrows()}

    # get des_clean with > 5 records and not in DROP/TBD types
    description = df911.description_clean.value_counts().to_frame()
    description['percentage'] = description.description_clean / description.description_clean.sum()
    des_clean1 = description[description.description_clean > 5].drop(DROP_IRRELEVANT + TBD_IRRELEVANT).reset_index()
    # get candidates with >1000 records
    candidates = des_clean1[des_clean1.description_clean > 1000]['index'].tolist()

    # compute string similarity between each candidate and each description in des_clean1
    for can in candidates:
        #     print(can)
        des_clean1[can] = des_clean1['index'].apply(lambda x: similarity(can, x))

    # argmax similarity as the matched candidate for noise description
    des_clean1['max_simi'] = des_clean1[candidates].max(axis=1)
    des_clean1['arg_max'] = des_clean1[candidates].apply(lambda x: x.argmax(), axis=1)
    des_clean1.set_index('index', inplace=True)
    des_clean1 = des_clean1[des_clean1.max_simi > 0.84].copy()

    # the similarity result is not perfect, manually inspect and find wrong match
    for k, v in WRONG_MATCH.items():
        des_clean1.loc[k, 'arg_max'] = v

    # there are some noise can't be resolved, drop them
    des_clean1.drop(DROP_NOISE, inplace=True)
    # des_to_tag is used in manually tagging, get CLEAN2CATEGORY
    # des_to_tag = set(des_clean1.drop(candidates, axis=1).arg_max.unique().tolist() + candidates)

    # map clean description to category
    des_clean1['Category'] = des_clean1.arg_max.apply(lambda x: CANDIDATE2CATEGORY[x])
    clean2category = {clean: category for clean, category in des_clean1.Category.iteritems()}

    # get final mapping, drop undefined category
    raw2category = {raw: clean2category.get(clean, 'undefined') for raw, clean in raw2clean.items()}
    mapping = pd.DataFrame.from_dict(raw2category, 'index').reset_index()
    mapping.columns = ['description', 'Category']
    mapping = mapping.set_index('Category').drop('undefined').sort_index()
    mapping.to_csv('911_categories.csv')
    return


if __name__ == '__main__':
    main()
