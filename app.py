# Command prompt
# cd C:\Users\asus\OneDrive\Documents\Streamlit\venv\Scripts\activate.bat
# streamlit run app.py

# Initialization

import streamlit as st
import numpy as np
import pandas as pd
import re
import folium
from streamlit_folium import folium_static

st.set_page_config(layout = 'wide')

# Functions

def convert(schedule):
    ''' Converts a schedule in the form Day1-Day2-...-DayN Time1-Time2 into the appropriate numbered timeslots.'''

    days=schedule.split()[0] # the first 'word' in the schedule
    if days=='D': days='M-T-W-TH-F' #intersession
    dayset = days.split('-')
    daydict = {'M':0, 'T':1, 'W':2, 'WED':2, 'TH':3, 'F':4, 'S':5, 'SAT':5} #map the day abbreviation to the number
    dayset = [daydict[day] for day in dayset]

    time=schedule.split()[1] #the second 'word' in the schedule
    start=time.split('-')[0] #the starting time of the class
    end=time.split('-')[1][0:4] #the ending time of the class
    if int(start)%100==0: start_mod=(int(start)//100-7)*2+1 #starting is xx00
    else: start_mod=(int(start)//100-7)*2+2 #starting is xx30
    if int(end)%100==0: end_mod=(int(end)//100-7)*2+1 #ending is xx00
    else: end_mod=(int(end)//100-7)*2+2 #ending is xx30

    timeset = [i for i in range(start_mod, end_mod)] #every 30-minute slot from start to end
    daytimeset = [i*30+j for i in dayset for j in timeset] #each day times 30 + the time slot
    return daytimeset

def multiple(schedule_list):
    ''' Takes in a list of schedules and applies convert() on each of them; outputs the list of converted schedules.'''
    
    return_list = []
    for i in range(len(schedule_list)):
        x=schedule_list[i]
        if 'TUTORIAL' in x or 'TBA' in x:
            return_list.append([])
        elif ';' in x: #when the class has multiple schedules
            s1=x.split(';')[0] #first schedule
            s2=x.split(';')[1] #second schedule
            s3=convert(s1) + convert(s2)
            return_list.append(s3)
        else: #when the class only has one schedule
            return_list.append(convert(x))
    return return_list

# Importing Schedules, Concatenating, and Applying Functions

dept_csv = pd.read_csv('depts.csv')
dept_syl_link_names = dept_csv['syl_link_name']
dept_short_names = dept_csv['short_name']
dept_full_names = dept_csv['full_name']

df_list = []
for i in range(len(dept_short_names)):
    df = pd.read_csv("schedules/"+dept_short_names[i]+".csv")
    df['Department'] = dept_full_names[i]
    df_list.append(df)

complete_list = pd.concat(df_list, ignore_index = True)
complete_list['Modified Schedule'] = multiple(complete_list['Time'])
complete_list['Subject Code and Name'] = complete_list['Subject Code'] + ': ' + complete_list['Course Title']
complete_list['Display Schedule'] = complete_list['Subject Code'] + ' ' + complete_list['Section'] + ' (' + complete_list['Room'] + ')'
# st.dataframe(complete_list)

# Two Schedules Processing

two_schedules = pd.DataFrame()
for i in range(len(complete_list)):
    if ';' in complete_list['Room'][i]:
        two_schedules = pd.concat([two_schedules, complete_list.iloc[i, :]], axis = 1)
        two_schedules = pd.concat([two_schedules, complete_list.iloc[i, :]], axis = 1)
two_schedules = two_schedules.transpose().reset_index().drop(columns = ['index'])

for i in range(len(two_schedules)):
    two_schedules['Time'][i] = two_schedules['Time'][i].split('(')[0].split(';')
    two_schedules['Room'][i] = two_schedules['Room'][i].split(';')
    two_schedules['Time'][i] = two_schedules['Time'][i][i%2].strip()
    two_schedules['Room'][i] = two_schedules['Room'][i][i%2].strip()
two_schedules['Subject Code and Name'] = two_schedules['Subject Code'] + ': ' + two_schedules['Course Title']
two_schedules['Display Schedule'] = two_schedules['Subject Code'] + ' ' + two_schedules['Section'] + ' (' + two_schedules['Room'] + ')'
two_schedules['Modified Schedule'] = multiple(two_schedules['Time'])
# st.dataframe(two_schedules)

# Buildings Processing

complete_rooms = pd.Series(complete_list['Room'].unique()).sort_values()\
                     .reset_index().rename(columns = {0 : 'Room'}).drop(columns = ['index'])
complete_rooms['Building'] = complete_rooms['Room']

bldg_dict = {
    'Arete' : ['ABS CBN CORPORATION INNOVATION CLASSROOM', 'ART GAL',
               'BLACK BOX THEATER FA', 'BRAZIER KITCHEN',
               'CO BUN TING AND PO TY LEE CO MAC LAB', "COLLEGE '66 CO-LAB", 'FA DEPT',
               'INNOVATION 201', 'INNOVATION 202', 'JOSEPH AND GEMMA TANBUNTIONG STUDIO',
               'NATIONAL BOOKSTORE ATELIER', 'YAO SIU LUN MAC LAB'],
    'PE Complex' : ['COV COURTS', 'DANCE AREA', 'LS POOL', 'MARTIAL ARTS CE',
                    'MARTIAL ARTS RM', 'MULTI-PUR RM', 'TAB TEN AREA', 'TENNIS CRT', 'WEIGHTS GYM'],
    'LH' : ['DS DEPT', 'EC DEPT', 'EU DEPT', 'JSP OFFICE', 'POS DEPT'],
    'SS' : ['COM STUD', 'CORD TRNG RM', 'GROUP THERAPY RM', 'PSY COMP RM'],
    'DLC' : ['EN DEPT', 'FIL DEPT', 'IS DEPT', 'PH DEPT'],
    'F' : ['PS DEPT'],
    'C' : ['CH DEPT'],
    'CTC' : ['HSC DEPT'],
    'SOM' : ['L&S DEPT', 'QMIT OFFICE']
}

complete_bldg_dict = {}
for key, value in bldg_dict.items():
    for room in value:
        complete_bldg_dict[room] = key
# st.write(complete_bldg_dict)

complete_rooms = complete_rooms.replace({'Building' : complete_bldg_dict})    
for i in range(len(complete_rooms)):
    for bldg in ['B', 'BEL', 'C', 'F', 'G', 'K']: # Bldg-Room
        complete_rooms['Building'][i] = re.sub(f'^{bldg}-.+', f'{bldg}', complete_rooms['Building'][i])
    for char in ['A', 'B', 'C']: # SEC-XRoom
        complete_rooms['Building'][i] = re.sub(f'^SEC-{char}.+', f'SEC-{char}', complete_rooms['Building'][i])
    for bldg in ['BEL', 'CTC', 'LH', 'SOM', 'SS']: # Bldg Room; BEL 211 is anomalous
        complete_rooms['Building'][i] = re.sub(f'^{bldg}.+', f'{bldg}', complete_rooms['Building'][i])
# st.write(complete_rooms)

complete_bldgs = pd.Series(complete_rooms['Building'].unique()).sort_values()\
                 .reset_index().rename(columns = {0 : 'Building'}).drop(columns = ['index'])
# st.write(complete_bldgs)

st.write('FACILE: Free Assistance for Class Indices in the Luck-Based Enlistment')
st.write('Version 5, Last updated: 9 January 2024')

# Tabs

tab1, tab2, tab3, tab4 = st.tabs(['Main', 'Schedule', 'Extra Info', 'Help'])

# Input Departments, Subjects, and Sections

with tab1:
    df_input = pd.DataFrame(columns=['Department', 'Subject', 'Section'])
    nsubjs = st.number_input('Number of Subjects', 1, 10,
                             help = 'Input the number of subjects you have, from 1 to 10.')
    
    depts, subjs, sects, mod_scheds, rooms, subj_codes, profs, raw_scheds, display_scheds = [], [], [], [], [], [], [], [], []
    
    with st.container():
        col0, col1, col2, col3 = st.columns([0.05, 0.30, 0.45, 0.1])
        with col0: 'No.'
        with col1: st.markdown('Department', help = 'The department that offers the subject you want to take.')
        with col2: st.markdown('Subject', help = '''The subject that you want to take.
    You have to pick the department first before you pick the subject.''')
        with col3: st.markdown('Section', help = '''The section of a particular subject you want to take.
    You have to pick the department and subject first before you pick the section.''')
    for i in range(nsubjs):
        with st.container():
            col0, col1, col2, col3 = st.columns([0.05, 0.30, 0.45, 0.1])
            with col0: st.write(i+1)
            with col1:
                dept = st.selectbox(f'Department {i+1}', dept_full_names,
                                    index = None, label_visibility = 'collapsed')
                depts.append(dept)
            with col2:
                subj = st.selectbox(f'Subject {i+1}', complete_list[complete_list['Department'] == dept]['Subject Code and Name'].unique(),
                                    index = None, label_visibility = 'collapsed')
                subjs.append(subj)
            with col3:
                sect = st.selectbox(f'Section {i+1}', complete_list[(complete_list['Subject Code and Name'] == subj) &
                                                                (complete_list['Department'] == dept)]['Section'],
                                    index = None, label_visibility = 'collapsed')
                sects.append(sect)

        condition = (complete_list['Department'] == dept) & (complete_list['Subject Code and Name'] == subj) & (complete_list['Section'] == sect)
        index = complete_list[condition].index
        
        mod_sched = complete_list.iloc[index]['Modified Schedule']
        mod_scheds.append(mod_sched)
        room = complete_list.iloc[index]['Room']
        rooms.append(room)
        subj_code = complete_list.iloc[index]['Subject Code']
        subj_codes.append(subj_code)
        prof = complete_list.iloc[index]['Instructor']
        profs.append(prof)
        raw_sched = complete_list.iloc[index]['Time']
        raw_scheds.append(raw_sched)
        display_sched = complete_list.iloc[index]['Display Schedule']
        display_scheds.append(display_sched)
        
    mod_scheds = [mod_sched.iloc[0] if len(mod_sched) > 0 else [] for mod_sched in mod_scheds]
    rooms = [room.iloc[0] if len(room) > 0 else '' for room in rooms]
    subj_codes = [subj_code.iloc[0] if len(subj_code) > 0 else '' for subj_code in subj_codes]
    profs = [prof.iloc[0] if len(prof) > 0 else '' for prof in profs]
    raw_scheds = [raw_sched.iloc[0] if len(raw_sched) > 0 else '' for raw_sched in raw_scheds]
    display_scheds = [display_sched.iloc[0] if len(display_sched) > 0 else '' for display_sched in display_scheds]

    summary = pd.DataFrame({'Department' : depts,
                            'Subject Code and Name' : subjs,
                            'Section' : sects,
                            'Modified Schedule' : mod_scheds,
                            'Room' : rooms,
                            'Subject Code' : subj_codes,
                            'Professor(s)' : profs,
                            'Raw Schedule' : raw_scheds,
                            'Display Schedule' : display_scheds},
                           index = np.arange(1, nsubjs + 1))
    # st.dataframe(summary)

    # Checking for Overlaps

    all_mod_scheds = [timeslot for mod_sched in mod_scheds for timeslot in mod_sched]
    all_mod_scheds.sort()
    # st.write(all_mod_scheds)
    if len(all_mod_scheds) != len(set(all_mod_scheds)):
        duplicates = True
        st.write('There are overlaps in your schedule.')
    else:
        duplicates = False
        st.write('There are no overlaps in your schedule.')

    # Departments / Subjects to Filter By

    filter_list = []
    filter_cat = []
    for i in range(nsubjs):
        if depts[i] == None:
            filter_list.append(None)
            filter_cat.append(None)
        elif subjs[i] == None:
            filter_list.append(depts[i])
            filter_cat.append('Department')
        elif sects[i] == None:
            filter_list.append(subjs[i])
            filter_cat.append('Subject')
        else:
            filter_list.append(None)
            filter_cat.append('Section')
    filter_df = pd.DataFrame({'Filter By' : filter_list, 'Filter Category' : filter_cat},
                             index = np.arange(1, nsubjs + 1))
    # st.dataframe(filter_df)

    # Active Department / Subject

    active_list = st.multiselect('Active Department / Subject', filter_df['Filter By'].dropna(), filter_df['Filter By'].dropna(),
                                 help = '''If you mark a department as active, you can see the subjects they offer that are compatible
    with your schedule. (This is helpful for PE and Major Electives, for example.)
    If you mark a subject as active, you can see the sections for it that are compatible with your schedule.''')

    def create_status_list(input_df):
        statuses = []
        for subject in input_df.values:
            mod_sched = subject[15]
            if len(all_mod_scheds + mod_sched) == len(set(all_mod_scheds + mod_sched)):
                status = 'Open'
            else: status = 'Closed'
            statuses.append(status)
        return statuses

    def display_subjects(input_dept):
        # st.write(f'Here are all the subjects offered by the Department of {input_dept}:')
        all_subjects = complete_list[complete_list['Department'] == input_dept]
        # st.dataframe(all_subjects)

        all_subjects['Status'] = create_status_list(all_subjects)
        st.write(f'Here are the subjects offered by the Department of {input_dept} that have no conflicts with your schedule:')
        filtered_subjects = all_subjects[all_subjects['Status'] == 'Open']
        st.dataframe(filtered_subjects)

    def display_sections(input_subj):
        # st.write(f'Here are all the sections for {input_subj}:')
        index = summary[summary['Subject Code and Name'] == input_subj].index
        dept_of_subj = summary['Department'].iloc[index-1].iloc[0]
        all_sections = complete_list[(complete_list['Department'] == dept_of_subj) &
                                 (complete_list['Subject Code and Name'] == input_subj)]
        # st.dataframe(all_sections)

        all_sections['Status'] = create_status_list(all_sections)
        st.write(f'Here are the sections for {input_subj} that have no conflicts with your schedule:')
        filtered_sections = all_sections[all_sections['Status'] == 'Open']
        st.dataframe(filtered_sections)

    for deptsubj in active_list:
        if deptsubj not in list(dept_full_names): display_sections(deptsubj)
        else: display_subjects(deptsubj)
    
with tab2:
    if duplicates:
        st.write('Please remove overlaps from your schedule first before proceeding to this tab.')
    else:
        st.subheader('Schedule Summary')
        display_summary = summary.drop(['Department', 'Subject Code', 'Modified Schedule', 'Display Schedule'], axis = 1)
        st.dataframe(display_summary, use_container_width = True)
                
        # st.dataframe(summary)

        hidden_summary = summary
        for i in range(1, nsubjs + 1):
            if ';' in hidden_summary['Raw Schedule'][i]:
                add_rows = two_schedules[(two_schedules['Department'] == depts[i-1]) &
                                         (two_schedules['Subject Code and Name'] == subjs[i-1]) &
                                         (two_schedules['Section'] == sects[i-1])
                                        ]
                hidden_summary = pd.concat([hidden_summary, add_rows])

        # st.write(hidden_summary)

        schedule_dict = {timeslot : row[8] for row in hidden_summary.values for timeslot in row[3]}
        # st.write(schedule_dict)

        schedule_vector = pd.Series(np.arange(1, 181)).replace(schedule_dict)
        schedule_vector = ["" if type(schedule_vector[i]) == int else schedule_vector[i] for i in range(180)]
        # st.write(schedule_vector)

        schedule_table = pd.DataFrame(pd.Series(schedule_vector).values.reshape(6, 30).T)
        # st.write(schedule_table)

        start_time = 700
        start_times = [start_time]
        for i in range(29):
            if start_times[-1] % 100 == 0:
                start_times.append(start_times[-1] + 30)
            else:
                start_times.append(start_times[-1] + 70)
        for i in range(30):
            start_times[i] = str(start_times[i])
            if len(start_times[i]) == 3: start_times[i] = '0' + start_times[i]

        end_times = start_times[1:]
        start_times = start_times[:-1]
        timeslots = [start_times[i] + '-' + end_times[i] for i in range(29)]

        schedule_table = schedule_table.iloc[:29]
        schedule_table.rename(columns = {0 : 'Monday',
                                         1 : 'Tuesday',
                                         2 : 'Wednesday',
                                         3 : 'Thursday',
                                         4 : 'Friday',
                                         5 : 'Saturday'},
                              index = pd.Series(timeslots), inplace = True)

        st.subheader('Schedule Table')
        st.table(schedule_table)

with tab3:
    st.subheader('Map')
    bldg_coords = [
        ['Arete', 14.6415, 121.0754],
        ['Bellarmine (BEL)', 14.6416, 121.0797],
        ['Berchmans (B)', 14.63945, 121.0785],
        ['PLDT-Convergent Technologies Center (CTC)', 14.6382, 121.0764],
        ['De La Costa (DLC)', 14.6399, 121.0768],
        ['Faura (F)', 14.6395, 121.0767],
        ['Gonzaga (G)', 14.6390, 121.0780],
        ['Kostka (K)', 14.6397, 121.0781],
        ['Leong (LH)', 14.6407, 121.0763],
        ['PE Complex', 14.6370, 121.0785],
        ['Schmitt (C)', 14.6391, 121.0774],
        ['Science Education Complex A (SEC A)', 14.6379, 121.0777],
        ['Science Education Complex B (SEC B)', 14.6379, 121.0772],
        ['Science Education Complex C (SEC C)', 14.6379, 121.0768],
        ['School of Management (SOM)', 14.6384, 121.0763],
        ['Social Sciences (SS)', 14.6405, 121.0768],
    ]
    
    bldg_coords_df = pd.DataFrame(bldg_coords, columns = ['Building', 'Latitude', 'Longitude'])

    # Create a Folium map
    m = folium.Map(location=[bldg_coords_df['Latitude'].mean(), bldg_coords_df['Longitude'].mean()], zoom_start=17, min_zoom=15, max_zoom=20)

    # Add markers for each city
    for i, row in bldg_coords_df.iterrows():
        folium.Marker([row['Latitude'], row['Longitude']], popup=f"{row['Building']}").add_to(m)

    # Display the map using streamlit's st.map
    st.write("Ateneo Buildings")
    folium_static(m)

with tab4:

    st.subheader('Input')
    st.write('''1. Refer to your IPS to input the departments and subjects.
2. Input the departments, subjects, and sections by the dropdown menus from left to right.
3. If you already have a section for one or more classes, input the section first
before checking the available schedules of other subjects.
4. It may be advisable to start with your major subjects, because these
have more limited schedules.''')

    st.subheader('Department')
    st.write('''1. Here are the departments that offer the core subjects:''')
    subjects_regular_depts = ['ENGL 11, ENLIT 12', 'FILI 11, FILI 12', 'HISTO 11, HISTO 12', 'ArtAp 10, DLQ 10',
                              'MATH 10', 'NSTP 11, NSTP 12 (ROTC - for those who signed up for it)',
                              'NSTP 11, NSTP 12 (CWTS - default program)', 'PHILO 12, PHILO 13', 'PHYED 1xx', 'STS 10',
                              'SocSc 11, SocSc 12, SocSc 13, SocSc 14',
                              'THEO 11, THEO 12, THEO 13']
    regular_depts_df = pd.DataFrame({'Department' : ['English', 'Filipino', 'History', 'Humanities', 'Mathematics',
                                                     'National Service Training Program (ADAST)',
                                                     'National Service Training Program (OSCI)',
                                                     'Philosophy', 'Physical Education',
                                                     'Science Block', 'Social Sciences', 'Theology'],
                                     'Subjects Offered' : subjects_regular_depts},
                                    index = np.arange(1,13))
    st.table(regular_depts_df)
    
    st.write('''2. The majority of the departments in the dropdown menu correspond to the
departments in AISIS, except for the elective core subjects shown below.
These subjects will not appear under the original departments anymore''')
    subjects_irregular_depts = ['ENE 13.03, 13.04, 13.05, 13.06',
                                'CSP 11, FRE 11, GER 11, ITA 11, JPN 11, KRN 11, RUSS 11, SPA 11',
                                '''BIO 10.01, BIO 11.01, BIO 12.01, CHEM 10.01, ENVI 10.01, PHYS 10.01
and the corresponding lab classes''',
                                'PHILO 11.03, 11.04, 11.05, 11.06']
    irregular_depts_df = pd.DataFrame({'Department' : ['IE 1', 'FLC', 'NatSc', 'PHILO 11'],
                                       'Subjects Offered' : subjects_irregular_depts},
                                      index = np.arange(1,5))
    st.table(irregular_depts_df)

    #misc
    # dept_filter = st.multiselect('Department', dept_full_names)
    # st.dataframe(complete_list[complete_list['Department'].isin(dept_filter)])

