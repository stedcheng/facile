# Initialization

import streamlit as st
import numpy as np
import pandas as pd
import re
import json
import folium
from streamlit_folium import folium_static
from pandas.errors import EmptyDataError

st.set_page_config(layout = 'wide')
st.title('FACILE Scheduler')

# Things to Edit
version = 'Version 5.4, Last updated: 20240704 2024 (for AY2425-S1)'
folder = 'schedules_2024-1_20240704_2024/'

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

# Importing Schedules, Concatenating, Applying Functions, and Changing Departments

dept_csv = pd.read_csv('depts.csv')
dept_syl_link_names = dept_csv['syl_link_name'][1:]
dept_short_names = dept_csv['short_name'][:-4]
dept_full_names = dept_csv['full_name'].sort_values()

df_list = []
for i in range(len(dept_short_names)):
    # edit this whenever changing the schedules
    try:
        df = pd.read_csv(folder+dept_short_names[i]+'.csv')
        df['Department'] = dept_full_names[i]
        df_list.append(df)
    except EmptyDataError:
        df = ''

complete_list = pd.concat(df_list, ignore_index = True)
complete_list['Modified Schedule'] = multiple(complete_list['Time'])
complete_list['Subject Code and Name'] = complete_list['Subject Code'] + ': ' + complete_list['Course Title']
complete_list['Display Schedule'] = complete_list['Subject Code'] + ' ' + complete_list['Section'] + ' (' + complete_list['Room'] + ')'
# st.dataframe(complete_list)

complete_list.loc[complete_list['Subject Code'].str.contains('PHILO 11.0'), 'Department'] = 'Philosophy: The Human Condition (PHILO 11)'
complete_list.loc[complete_list['Subject Code'].str.contains('ENE 13.0'), 'Department'] = 'Interdisciplinary Elective 1 - English (IE 1)'
complete_list.loc[complete_list['Subject Code'].isin(['BIO 10.01', 'BIO 10.02', 'BIO 11.01', 'BIO 11.02', 'BIO 12.01', 'BIO 12.02',
                                                      'CHEM 10.01', 'CHEM 10.02', 'ENVI 10.01', 'ENVI 10.02',
                                                      'PHYS 10.01', 'PHYS 10.02']), 'Department'] = 'Natural Science (NatSc 10)'
complete_list.loc[complete_list['Subject Code'].isin(['CSP 11', 'FRE 11', 'GER 11', 'ITA 11', 'JPN 11', 'KRN 11', 'RUSS 11', 'SPA 11']),
                  'Department'] = 'Foreign Language and Culture (FLC 11)'


early_list = [i for j in range(5) for i in range(30*j + 1, 30*j + 4)]
late_list = [i for j in range(5) for i in range(30*j + 21, 30*j + 30)]

is_early = [True if len(complete_list['Modified Schedule'][i]) + len(early_list) !=\
            len(set(complete_list['Modified Schedule'][i] + early_list))
            else False for i in range(len(complete_list))]
is_late = [True if len(complete_list['Modified Schedule'][i]) + len(late_list) !=\
            len(set(complete_list['Modified Schedule'][i] + late_list))
            else False for i in range(len(complete_list))]
complete_list['is_early'] = is_early
complete_list['is_late'] = is_late
# st.write(complete_list)

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

st.write('FACILE: Free Assistance for Class Indices in the Luck-Based Enlistment')
st.write(version)

# Tabs

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(['Main', 'Schedule', 'AIV (formerly Syllabus Viewer)', 'Help and Samples', 'Prof Locator', 'Classroom Checker', 'Map', 'About / Contact'])

# Input Departments, Subjects, and Sections

with tab1:
    df_input = pd.DataFrame(columns=['Department', 'Subject', 'Section'])
    depts, subjs, sects, mod_scheds, rooms, subj_codes, profs, raw_scheds, display_scheds = [], [], [], [], [], [], [], [], []
    nsubjs = 0
    save_checkbox = st.checkbox('Do you have an existing schedule?',
                                help = '''If you check this box, there will be a space for you to paste the information about\
the number of subjects you have, as well as your departments, subjects, and sections. In short, this avoids you having to manually input
everything. If this is your first time using FACILE, then uncheck the box.''')
    
    if save_checkbox:
        st.subheader('With Existing Schedule')
        save_str = st.text_input('Paste your existing schedule here, then press Enter:')
        try:
            save_dict = json.loads(save_str)
            nsubjs, depts, subjs, sects = save_dict['nsubjs'], save_dict['depts'], save_dict['subjs'], save_dict['sects']
            st.write('''Please proceed to the next tab entitled "Schedule" and confirm that the schedule displayed there is correct.
If there are errors, please check what you pasted, or you can also do the manual input again.''')
            for i in range(nsubjs):
                if subjs[i] == None:
                    condition = (complete_list['Department'] == depts[i])
                elif sects[i] == None:
                    condition = (complete_list['Department'] == depts[i]) & (complete_list['Subject Code and Name'] == subjs[i])
                else:
                    condition = (complete_list['Department'] == depts[i]) & (complete_list['Subject Code and Name'] == subjs[i]) & (complete_list['Section'] == sects[i])

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
        except:
            print('Please input your previously saved schedule. If the problem persists, message me.')
            
    else:
        st.subheader('Without Existing Schedule')
        nsubjs = st.number_input('Number of Subjects', 1, 10,
                             help = 'Input the number of subjects you have, from 1 to 10.')
        depts, subjs, sects = [], [], []
        
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
                col0, col1, col2, col3 = st.columns([0.05, 0.3, 0.45, 0.1])
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

    try:
        summary = pd.DataFrame({'Department' : depts,
                                'Subject Code and Name' : subjs,
                                'Section' : sects,
                                'Modified Schedule' : mod_scheds,
                                'Room' : rooms,
                                'Subject Code' : subj_codes,
                                'Professor(s)' : profs,
                                'Raw Schedule' : raw_scheds,
                                'Display Schedule' : display_scheds},
                               index = np.arange(1, nsubjs+1))
    except:
        st.write('Please ensure that your input is correct.')

    # st.write(summary)

    # Checking for Overlaps

    all_mod_scheds = [timeslot for mod_sched in mod_scheds for timeslot in mod_sched]
    all_mod_scheds.sort()
    # st.write(all_mod_scheds)
    st.subheader('Information Regarding Overlaps')
    if depts == [] or depts == [None for _ in range(nsubjs)]:
        duplicates = 'N/A'
        st.write('You have not inputted anything yet.')
    elif len(all_mod_scheds) != len(set(all_mod_scheds)):
        duplicates = True
        st.write('There are overlaps in your schedule.')
    else:
        duplicates = False
        st.write('There are no overlaps in your schedule.')

    # Departments / Subjects to Filter By
    
    st.subheader('Active Department / Subject')
    early_late_checkbox = st.checkbox('Do you want to highlight early and late classes? (Early - Maroon Text, Late - Orange Text)')
    fili_checkbox = st.checkbox('Do you want to highlight Filipino classes? (PHILO 11, 12, 13, and DLQ) (Light Blue Highlight)')

    def formatter(x):
        early_filipino = 'color:#AA336A;background-color:#ADD8E6'
        late_filipino = 'color:#FF8C00;background-color:#ADD8E6'
        early = 'color:#AA336A'
        late = 'color:#FF8C00'
        filipino = 'background-color:#ADD8E6'
        empty = ''

        mask1 = (x['is_early'] == True) & (x['Lang'] == 'FIL')
        mask2 = (x['is_late'] == True) & (x['Lang'] == 'FIL')
        mask3 = (x['is_early'] == True) & (x['Lang'] != 'FIL')
        mask4 = (x['is_late'] == True) & (x['Lang'] != 'FIL')
        mask5 = (x['is_early'] == False) & (x['is_late'] == False) & (x['Lang'] == 'FIL')
        mask6 = (x['is_early'] == True)
        mask7 = (x['is_late'] == True)
        mask8 = (x['Lang'] == 'FIL')
        # mask9 = (x['is_early'] == False) & (x['is_late'] == False) & (x['Lang'] != 'FIL')

        complete_list_styled = pd.DataFrame(empty, index = x.index, columns = x.columns)
        if early_late_checkbox and fili_checkbox:
            complete_list_styled.loc[mask1, :] = early_filipino
            complete_list_styled.loc[mask2, :] = late_filipino
            complete_list_styled.loc[mask3, :] = early
            complete_list_styled.loc[mask4, :] = late
            complete_list_styled.loc[mask5, :] = filipino
        elif early_late_checkbox:
            complete_list_styled.loc[mask6, :] = early
            complete_list_styled.loc[mask7, :] = late
        elif fili_checkbox:
            complete_list_styled.loc[mask8, :] = filipino

        return complete_list_styled
    
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
        filtered_subjects_display = filtered_subjects.drop(['Department', 'Modified Schedule',
                                                       'Subject Code and Name', 'Display Schedule', 'Status'], axis = 1).astype({'Units' : 'int'})
        st.dataframe(filtered_subjects_display.style.apply(formatter, axis = None))

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
        filtered_sections_display = filtered_sections.drop(['Department', 'Modified Schedule',
                                                       'Subject Code and Name', 'Display Schedule', 'Status'], axis = 1).astype({'Units' : 'int'})
        st.dataframe(filtered_sections_display.style.apply(formatter, axis = None))

    if depts == [] or depts == [None for _ in range(nsubjs)]:
        st.write('You have not inputted anything yet.')
    else:
        active_list = st.multiselect('Select the Active Department(s) / Subject(s)', filter_df['Filter By'].dropna(), filter_df['Filter By'].dropna(),
                                     help = '''If you mark a department as active, you can see the subjects they offer that are compatible
        with your schedule. (This is helpful for PE and Major Electives, for example.)
        If you mark a subject as active, you can see the sections for it that are compatible with your schedule.''')

        for deptsubj in active_list:
            if deptsubj not in list(dept_full_names): display_sections(deptsubj)
            else: display_subjects(deptsubj)

    st.subheader('Copy Paste')
    st.write('You can copy the box below, so that if you want to use FACILE next time, you can paste this information\
             instead of having to manually input each department, subject, and section.')
    copy = {'nsubjs' : nsubjs, 'depts' : depts, 'subjs' : subjs, 'sects' : sects}
    st.code(copy)
    
with tab2:
    if duplicates == 'N/A':
        st.write('Please input your schedule.')
    if duplicates == True:
        st.write('Please remove overlaps from your schedule first before proceeding to this tab.')
    else:
        st.subheader('Schedule Summary')
        if sects == [] or sects == [None for _ in range(nsubjs)]:
            st.write('Please input a section.')
        else:
            display_summary = summary.drop(['Department', 'Subject Code', 'Modified Schedule', 'Display Schedule'], axis = 1)
            st.dataframe(display_summary, use_container_width = True)     

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
            schedule_vector = ['' if type(schedule_vector[i]) == int else schedule_vector[i] for i in range(180)]
            # st.write(schedule_vector)

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

        st.subheader('Schedule Table')
        if sects == [] or sects == [None for _ in range(nsubjs)]:
            st.write('Please input a section.')
        else:
            schedule_table = pd.DataFrame(pd.Series(schedule_vector).values.reshape(6, 30).T)
            # st.write(schedule_table)

            schedule_table = schedule_table.iloc[:29]
            schedule_table.rename(columns = {0 : 'Monday',
                                             1 : 'Tuesday',
                                             2 : 'Wednesday',
                                             3 : 'Thursday',
                                             4 : 'Friday',
                                             5 : 'Saturday'},
                                  index = pd.Series(timeslots), inplace = True)

            st.table(schedule_table)

with tab3:
    st.header('I. Syllabus Viewer')
    code_csv = pd.read_csv('prefixes.csv', index_col = [0])
    code_dict = code_csv.to_dict()['syl_link_name']
    # st.write(code_dict)

    def view_syllabus(n):
        global code_dict, year, semester, dept_code, course_code, prof_full, prof_first, prof_last, section, link

        with st.container():
            col0, col1, col2, col3 = st.columns([0.05, 0.1, 0.1, 0.5])
            with col0: 'No.'
            with col1: st.markdown('Year', help = '''The school year when the class was conducted.
Note that Intersession is part of the next school year. Type 2022 for June 2022-May 2023, 2023 for June 2023-May 2024, etc.
Default value is the current school year 2023-2024, i.e., "2023".''')
            with col2: st.markdown('Semester', help = '''The semester when the class was conducted.
Type 0 for Intersession (June-July), 1 for First Semester (August-December), and 2 for Second Semester (January-May).
Default value is the current semester, i.e., "2".''')
            with col3: st.markdown('Whole Row in AISIS', help = '''The whole row, as displayed in AISIS, of the class whose syllabus
you want to access.''')

        links = []
        for i in range(n):
            with st.container():
                col0, col1, col2, col3 = st.columns([0.05, 0.1, 0.1, 0.5])
                with col0: st.write(i+1)
                with col1:
                    year = st.number_input('Year', 2018, 2025, value = 2024, label_visibility = 'collapsed', key = i*3+1)
                    year = str(year)
                with col2:
                    semester = st.number_input('Semester', 0, 2, value = 0, label_visibility = 'collapsed', key = i*3+2)
                    semester = str(semester)
                with col3:
                    row = st.text_input('Row', label_visibility = 'collapsed', key = i*3+3)
                    row = row.split('\t')
                    try:
                        if row[0] == 'NSTP 11(CWTS)' or row[0] == 'NSTP 12(CWTS)':
                            dept_code = 'NSTP (OSCI)'
                        elif row[0] == 'NSTP 11(ROTC)' or row[0] == 'NSTP 12(ROTC)':
                            dept_code = 'NSTP (ADAST)'
                        elif row[0].split()[0] in dept_syl_link_names:
                            dept_code = row[0].split()[0]
                        else:
                            dept_code = code_dict[row[0].split()[0]]

                        course_code_spaced = row[0].split()
                        course_code = ''
                        for i in range(len(course_code_spaced)):
                            course_code += course_code_spaced[i]

                        comma_count = 0
                        for i in range(len(row[6])):
                            if row[6][i] == ',': comma_count += 1
                        if comma_count == 1:
                            prof_last = row[6].split(', ')[0]
                            prof_first = row[6].split(', ')[1][0]
                            prof_full = prof_last + '_' + prof_first
                        elif comma_count == 2:
                            prof_full = row[6].split(", ")
                            if prof_full[1] in ['Jr.', 'JR.', 'Jr', 'JR', 'SJ', 'S.J.']:
                                prof_full[0] = prof_full[0] + ', ' + prof_full[1]
                                prof_full.remove(prof_full[1])
                            prof_last = prof[0]
                            prof_first = prof[1][0]
                            prof_full = prof_last + "_" + prof_first
                        elif comma_count % 2 == 1:
                            prof_count = comma_count // 2 + 1
                            profs_list = row[6].split(', ')
                            prof_full = ''
                            for i in range(prof_count):
                                prof_last = row[6].split(', ')[2*i]
                                prof_first = row[6].split(', ')[2*i+1][0]
                                prof_full += prof_last
                                prof_full += '_'
                                prof_full += prof_first
                                prof_full += '_'
                            prof_full = prof_full[:-1]
                        else:
                            print('This class likely has many professors, and at least one has Jr./SJ. Not supported as of now')
                        
                        section = row[1]
                        
                        if comma_count >=1 :
                            link = 'aisis.ateneo.edu/syllabi/{0}/{1}/CS-{2}-{3}-{4}-{5}-{0}-{1}.pdf'.format(
                                year,semester,dept_code,course_code,prof_full,section)
                        else:
                            link = "The link cannot be generated because there seems to be no professors."

                        links.append(link)

                    except:
                        st.write(f'Please input the whole row in AISIS for subject {i+1}')

        st.write('You can copy the processed links from here:')            
        return links

    nsubjs_syl = st.number_input('Number of Subjects', 1, 10,
                                 help = 'Input the number of subjects whose syllabus you want to check, from 1 to 10.')
    st.write(view_syllabus(nsubjs_syl))

    st.subheader('A. Steps for Automatic')
    url = 'https://chrome.google.com/webstore/detail/open-multiple-urls/oifijhaokejakekmnjmphonojcfkpbbh/related?hl=en'
    st.write('''1. Under "Number of Subjects", input the number of classes whose syllabi you want to check.
\n2. Go to aisis.ateneo.edu (the usual AISIS where we do our enlistment), log in, and click "Class Schedules".
\nIf the class whose syllabus you want to check was offered in a semester which is part of the options in the dropdown menu,
select the year/semester and department under which your desired class is, and scroll to the class. 
\nIf the class whose syllabus you want to check was offered in a semester which is not part of the options in the dropdown menu (i.e. too old),
scroll down to the second hack. Follow the instructions to be able to access the schedules.
\n3. After the links are outputted, you can copy and paste the links outputted by this syllabus viewer. 
\n(Optional: If you are checking for many classes, I recommend using an extension to open multiple links at once,
such as [this one](%s)).
\n4. If the syllabus loads, then it is likely the correct one.''' % url)

    st.subheader('B. Troubleshooting')
    st.write('''Troubleshooting: Despite my best efforts, it may be possible that the syllabus does not load correctly.
This may be due to a few reasons:
\n1. There are Jr.s or SJs in the name(s) of the professor(s), which may be misinterpreted as the last name.
Refer to Part E3 to resolve.
\n2. The number of professors is more than one and the order of their names in the output is incorrect.
Refer to Part E4 to resolve.
\n3. The professor / One of the professors used to be a TBA professor. Refer to Part E5 to resolve.
\nIf you try those methods and it still doesn't work, I don't have a solution as of the moment.
Please let me know about your situation.''')

    st.subheader('C. Steps for Manual')
    st.write('The link to the syllabus looks like this:')
    st.code('https://aisis.ateneo.edu/syllabi/[a]/[b]/CS-[c]-[d]-[e]_[f]-[g]-[a]-[b].pdf')
    st.write('''where
- a is the starting year of the school year (for the school year June 2021–May 2022, a = 2021)
- b is the semester number (1 or 2, intersession is 0)
- c is the old code of the department that offers the subject (refer to Part D)
- d is the subject code, without spaces
- e is the professor’s last name (refer to Part E)
- f is the professor’s first name’s initial (refer to Part E)
- g is the section (refer to Part F)
\nNote that everything from c to g should be in all capitals, and that CS most likely means “Course/Class Syllabus”.
Also, these links can all be opened in incognito.
''')

    st.subheader('D. On Departments and Corresponding Codes')
    st.write(dept_csv[['syl_link_name', 'full_name']][1:])

    st.subheader("E. On Professors' Names")
    st.write('''
1. If there is a space in the last name, use “%20” to substitute. Alternatively, you can also type the space as is in between the names, and when you hit enter, the “%20” will automatically appear.
\nExample: The link to the syllabus for INTACT 11, section S2 is''')
    st.code('https://aisis.ateneo.edu/syllabi/2021/1/CS-INTAC-INTACT11-CHAN%20SHIO_C-S2-2021-1.pdf')
    st.write('which is equivalent to')
    st.code('https://aisis.ateneo.edu/syllabi/2021/1/CS-INTAC-INTACT11-CHAN SHIO_C-S2-2021-1.pdf')
    st.write('''2. If there is a dash in the professor’s last name, type as is.
\nExample:''')
    st.code('https://aisis.ateneo.edu/syllabi/2021/1/CS-MA-MATH10-LEE-CHUA_Q-MM-2021-1.pdf')
    st.write('''3. If the professor has suffixes (Jr., II, III, SJ, etc.) in their name, they may use it in their first name or last name. Check the AISIS page for that. The note about the spacing also applies.
\nExamples:''')
    st.code('''https://aisis.ateneo.edu/syllabi/2022/1/CS-PS-PHYS23.01-SUGON,%20JR._Q-C-2022-1.pdf
https://aisis.ateneo.edu/syllabi/2022/1/CS-SOCSCI-SocSc12-TANGARA_A-F1-2022-1.pdf
https://aisis.ateneo.edu/syllabi/2021/1/CS-MA-MATH71.1-MUGA%20II_F-A-2021-1.pdf 
https://aisis.ateneo.edu/syllabi/2022/1/CS-EU-EURO21-ENVERGA%20III_M-C-2022-1.pdf
https://aisis.ateneo.edu/syllabi/2022/1/CS-CEPP-EDUC201-ALVAREZ,%20SJ_F-PQ-2022-1.pdf''')
    st.write('''Note that the professor in the second example also has a Jr. in his name, but it is written under his first name,
so it is not seen in the syllabus link.
4. If there are n professors, replace [e]\_[f] with [$e_1$]\_[$f_1$]\_…\_[$e_n$]\_[$f_n$]
\nwhere
$e_i =$ Last Name of Professor $i$, $f_i =$ Initial of First Name of Professor $i$, for $i = 1, 2, \ldots, n$
\nor in English,
- $e_1$ is the first professor’s last name
- $f_1$ is the first professor’s first name’s initial
- … (and so on)
- $e_n$ is the nth professor’s last name
- $f_n$ is the nth professor’s first name’s initial
\nExamples:''')
    st.code('''https://aisis.ateneo.edu/syllabi/2021/1/CS-SOCSCI-SocSc11-ACOSTA_I_REYES_J-PSY-E-2021-1.pdf
https://aisis.ateneo.edu/syllabi/2022/1/CS-MA-MATH199.11-TOLENTINO_M_DAVID_R_BENITO_D-T1-2022-1.pdf''')
    st.write('''Note that the order of professors is alphabetical in the first example, but not in the second.
Take note that AISIS arranges the professors alphabetically in the "Instructors" column.
However, this is not always how the names are arranged in the link.
You can try switching around the order of the names and checking if the syllabus loads.
5. If the professor is, or used to be, marked as TBA, their last name is "TBA" and their first name is "-".
(This corresponds to the professor’s name on AISIS, which is "TBA, -".)
\nExamples:''')
    st.code('''https://aisis.ateneo.edu/syllabi/2021/1/CS-MA-MATH71.1-TBA_-_TABARES_W-B-2021-1.pdf
https://aisis.ateneo.edu/syllabi/2022/1/CS-CH-CHEM171.42-TBA_-_ENRIQUEZ_E-LAB2-DEF1-2022-1.pdf
https://aisis.ateneo.edu/syllabi/2022/1/CS-CH-CHEM10.01-TBA_--CA-C-2022-1.pdf''')
    st.write('It may look weird that there are two dashes, but that is how it is.')

    st.subheader('F. On Sections')
    st.write('''On sections: The section should be exactly the same from AISIS. Take note of the following:
- "(MEN)" / "(WOMEN)" for PHYED courses
- "-Q1" etc. for AY 2020–2021 subjects (due to the quarterly system)
- dashes in NatSc, INTACT, and DLQ classes, among others
\nExamples:''')
    st.code('''https://aisis.ateneo.edu/syllabi/2021/1/CS-PE-PHYED114-MENDOZA_M-A(MEN)-2021-1.pdf 
https://aisis.ateneo.edu/syllabi/2021/1/CS-PE-PHYED122-ASAJAR_A-G(WOMEN)-2021-1.pdf
https://aisis.ateneo.edu/syllabi/2020/2/CS-PE-PHYED111-PUEN_D-N-Q4-2020-2.pdf
https://aisis.ateneo.edu/syllabi/2022/1/CS-ES-ENVI10.01-CABALLES_D-CA-C-2022-1.pdf
https://aisis.ateneo.edu/syllabi/2022/1/CS-SOHUM-DLQ10-SUAREZ_V-PH-A-2022-1.pdf''')
    st.write('''The syllabi from the school year 2020–2021 and earlier seemed to work before, but not as of 24 January 2024''')

    st.header('II. Old Schedule Viewer')
    st.write('''This is for classes not under the Dropdown menu of “School Year and Term”.
Credits to an anonymous faculty member.
1. Login to AISIS, click on Class Schedule, and pick the Department.
\n2. Right click on the dropdown menu for "School Year and Term", and click "Inspect".''')
    st.image('images/osv1.png')
    st.write('3. Click the black shaded triangle in the blue highlighted area.')
    st.image('images/osv2.png')
    st.write('''4. After the first <option> (which should be the most recent term), double click the value so that you can edit it.
Change it in the format yyyy-s, where yyyy is the year when the school year started,
and s is the semester number (0 for intersession, 1 for 1st semester, and 2 for 2nd semester). \nExamples:\n
- January–May 2021: 2020-2
- August–December 2019: 2019-1
- June–July 2017: 2017-0''')
    st.write('Before:')
    st.image('images/osv3.png')
    st.write('After I changed it to 2015-2, i.e. January–May 2016:')
    st.image('images/osv4.png')
    st.write('5. Click "Display Class Schedule"')
    st.image('images/osv5.png')

    st.header('III. Delisting from or Transferring Sections in a Preenlisted Class')
    st.write('''If there’s one thing good from the early enlistment, it gave me time to explore the "Enlist in Class" option of AISIS.
\n1. Login to AISIS and click "Enlist in Class".
\n2. Click the checkbox at the end and then click "Proceed".
\n3. Normally, if a course is preenlisted, the "Enlist/Delist" button will look different.
Take note of the ordinal position (in Filipino: pang-ilan) of the course from which you want to delist,
or the course where you want to change sections.
\n4. Click the "Enlist/Delist" class for any of your classes where you can enlist (e.g. PE, FLC, NatSc). The link should look like this:''')
    st.code('https://aisis.ateneo.edu/j_aisis/displayClasses.do?index=n')
    st.write('''where $n \in \mathbb{N} \cup \{0\}$, or in English, $n$ is 0, 1, 2, etc.
\n5. Change the n into the ordinal position of the course from which you want to delist,
or the course where you want to change sections, minus 1. (This is since the computer starts counting at 0, as you might know.)
The enlistment page for the desired course should be seen.
\n6. If you want to delist, click "Remove Me From This Class".
If you want to change sections, also click "Remove Me From This Class" and this should allow you to enlist in another section.
\n7. Disclaimer: If the section to which you want to move is restricted or has zero or negative slots,
you cannot enlist there. The trick only works if the new section has slots and is not restricted.''')

    st.header('IV. Appendix')

    st.subheader('A. Version with Login vs without Login')
    aisis_updates = pd.DataFrame({'Version with Login' : ['https://aisis.ateneo.edu/j_aisis/J_VCSC.do',
                                                          'Subject Code, Section, Course Title, Units, Time, Room, Instructor, Max No, Lang, Level, Free Slots, Remarks, S, P',
                                                          'No', 'No', 'No', 'Yes', 'Yes'],
                                  'Version without Login' : ['https://aisis.ateneo.edu/j_aisis/classSkeds.do',
                                                             'Subject Code, Section, Course Title, Units, Time, Room, Instructor, Lang, Level, Remarks',
                                                             'Yes', '10, 25, 50, or 100 entries at a time', 'Yes', 'No', 'No']},
                                 index = ['Link', 'Columns', 'Sortable Columns', 'Show Limited Entries', 'Searchable', 'Filter by Course', 'All IEs Department'])
    st.table(aisis_updates)

    st.subheader('B. Links for each part of the page')
    links_all = [['Landing Page', 'https://aisis.ateneo.edu/j_aisis/welcome.do'],
                 ['View Advisory Grades', 'https://aisis.ateneo.edu/j_aisis/J_VADGR.do'],
                 ['Online Tuition Payment', 'https://aisis.ateneo.edu/j_aisis/J_REASST.do'],
                 ['Google Account', 'https://aisis.ateneo.edu/j_aisis/J_GOOGLE.do'],
                 ['Enlist in Class', 'https://aisis.ateneo.edu/j_aisis/J_ENLC.do'],
                 ['My Individual Program of Study', 'https://aisis.ateneo.edu/j_aisis/J_VIPS.do'],
                 ['Print Tuition Receipt', 'https://aisis.ateneo.edu/j_aisis/J_PTR.do'],
                 ['Official Curriculum', 'https://aisis.ateneo.edu/j_aisis/J_VOFC.do'],
                 ['My Currently Enrolled Classes', 'https://aisis.ateneo.edu/j_aisis/J_VCEC.do'],
                 ['My Grades', 'https://aisis.ateneo.edu/j_aisis/J_VG.do'],
                 ['My Hold Orders', 'https://aisis.ateneo.edu/j_aisis/J_VHOR.do'],
                 ['Print Tuition Assessment', 'https://aisis.ateneo.edu/j_aisis/J_PASS.do'],
                 ['Update Student Information', 'https://aisis.ateneo.edu/j_aisis/J_STUD_INFO.do'],
                 ['My Class Schedule', 'https://aisis.ateneo.edu/j_aisis/J_VMCS.do'],
                 ['Change Password', 'https://aisis.ateneo.edu/j_aisis/J_CHPA.do'],
                 ['View Enlistment Summary', 'https://aisis.ateneo.edu/j_aisis/J_VENS.do'],
                 ['Class Schedule', 'https://aisis.ateneo.edu/j_aisis/J_VCSC.do']]
    links_df = pd.DataFrame(links_all, columns = ['Title', 'Link'])
    st.table(links_df)

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

    st.subheader('Sample Data')
    st.write('Here are some sample data you can use for testing FACILE and AIV (Syllabus Viewer). The copy button is at the right of the text to be copied.')
    st.write('For AIV (Syllabus Viewer) (Note that this class was/is offered in Year 2023, Semester 2:')
    st.code('''MATH 62.2	F	TIME SERIES AND FORECASTING	3	M-TH 1530-1700
(FULLY ONSITE)	SEC-A302A	BRIONES, JERIC C.	30	ENG	U	1	-	N	N''')
    st.write('For FACILE:')
    st.code('''{
  "nsubjs": 8,
  "depts": [
    "Economics",
    "Mathematics",
    "Mathematics",
    "Mathematics",
    "Mathematics",
    "Information Systems and Computer Science",
    "Philosophy",
    "Theology"
  ],
  "subjs": [
    "ECON 112: INTERMEDIATE MACROECONOMIC THEORY",
    "MATH 62.2: TIME SERIES AND FORECASTING",
    "MATH 72.1: ORDINARY DIFFERENTIAL EQUATIONS",
    "MATH 104.1: PROBABILISTIC MACHINE LEARNING I",
    "MATH 192: UNDERGRADUATE RESEARCH SEMINAR",
    "CSCI 113i: BUSINESS INTELLIGENCE",
    "PHILO 13: ETHICS",
    "THEO 13: A THEOLOGY OF MARRIAGE, FAMILY, AND VOCATION"
  ],
  "sects": [
    "A1",
    "F",
    "E",
    "M",
    "WXWB2",
    "J",
    "G4",
    "C4"
  ]
}
''')

with tab5:
    prof_unique = pd.Series(complete_list['Instructor'].unique()).sort_values().reset_index()\
                  .drop(columns = ['index']).rename(columns = {0 : 'Professor'})
    # st.write(prof_unique)
    prof_input = st.selectbox('Which professor\'s schedule do you want to find?', prof_unique, index = None,
                              help = '''Note that these subjects and rooms are only based on AISIS.
There may be anomalies here, such as a TBA classroom not being updated, or a class having been moved to a different room.
Please ask the department secretary for more accurate and timely information.''')
    
    st.subheader('Professor Schedule Summary')
    try:
        prof_summary = complete_list[complete_list['Instructor'].str.contains(prof_input)]
        # st.write(prof_summary)
        display_prof_summary = prof_summary[['Subject Code and Name', 'Section', 'Room', 'Instructor', 'Time']]
        st.write(display_prof_summary)
        prof_schedule_dict = {timeslot : row[17] for row in prof_summary.values for timeslot in row[15]}
        # st.write(prof_schedule_dict)
    except:
        st.write('You have not input anything, or your input is incorrect. Please try again.')

    st.subheader('Professor Schedule Table')
    try:
        if prof_schedule_dict == {}:
            st.write('This professor only teaches classes with no specific timeslots (e.g. thesis or graduate school classes).')
        else:
            prof_schedule_vector = pd.Series(np.arange(1, 181)).replace(prof_schedule_dict)
            prof_schedule_vector = ['' if type(prof_schedule_vector[i]) == int else prof_schedule_vector[i] for i in range(180)]
            # st.write(prof_schedule_vector)

            prof_schedule_table = pd.DataFrame(pd.Series(prof_schedule_vector).values.reshape(6, 30).T)
            prof_schedule_table = prof_schedule_table.iloc[:29]
            prof_schedule_table.rename(columns = {0 : 'Monday',
                                                  1 : 'Tuesday',
                                                  2 : 'Wednesday',
                                                  3 : 'Thursday',
                                                  4 : 'Friday',
                                                  5 : 'Saturday'},
                                       index = pd.Series(timeslots), inplace = True)
            st.table(prof_schedule_table)
        
    except:
        st.write('You have not input anything, or your input is incorrect. Please try again.')

    st.subheader('Subjects and Departments Taught By Professors')
    teaching_load = [complete_list[complete_list['Instructor'] == prof_unique['Professor'].iloc[i]]\
                     ['Subject Code'].value_counts().to_dict() for i in range(len(prof_unique))]
    prof_unique['Teaching Load'] = teaching_load

    subjs_taught = [complete_list[complete_list['Instructor'] == prof_unique['Professor'].iloc[i]]\
                     ['Subject Code'].unique() for i in range(len(prof_unique))]
    prof_unique['Subjects Taught'] = subjs_taught
    catalog_codes_taught = [set([subj.split()[0] for subj in subjs_taught[i]]) for i in range(len(prof_unique))]
    prof_unique['Catalog Codes Taught'] = catalog_codes_taught

    one_prof_only = prof_unique[prof_unique['Professor'].str.count(',') <= 2].reset_index().drop(columns = ['index'])

    code_dict['NSTP'] = 'NSTP'
    depts_taught = [set([code_dict[key] for key in one_prof_only['Catalog Codes Taught'][i]]) for i in range(len(one_prof_only))]
    one_prof_only['Departments Taught'] = depts_taught

    dept_full_name_dict = dept_csv[['syl_link_name', 'full_name']].set_index('syl_link_name').to_dict()['full_name']
    dept_full_name_dict['NSTP'] = 'National Service Training Program'
    depts_taught_full_name = [set([dept_full_name_dict[key] for key in one_prof_only['Departments Taught'][i]]) for i in range(len(one_prof_only))]
    one_prof_only['Departments Taught, Full Name'] = depts_taught_full_name
    st.write(one_prof_only)

    # more_than_one_prof = prof_unique[prof_unique['Professor'].str.count(',') > 2].reset_index().drop(columns = ['index'])
    # st.write(more_than_one_prof)

with tab6:
    room_multiple = complete_list['Room'].str.split(';', expand = True)
    room_unique = pd.DataFrame(pd.concat([room_multiple[col] for col in room_multiple.columns]).unique())
    room_unique['Room'] = room_unique[0].str.strip()
    room_unique = pd.Series(room_unique['Room'].unique()).sort_values().reset_index()\
                  .drop(columns = ['index']).rename(columns = {0 : 'Room'})
    room_unique = room_unique[room_unique['Room'] != 'TBA'].reset_index().drop(columns = ['index'])
    
    room_input = st.selectbox('Which room\'s schedule do you want to find?', room_unique, index = None,
                              help = '''Note that these subjects and rooms are only based on AISIS.
There may be anomalies here, such as a TBA classroom not being updated, or a class having been moved to a different room.
Please ask the department secretary for more accurate and timely information.''')

    st.subheader('Room Schedule Summary')
    try:
        room_summary = complete_list[complete_list['Room'].str.contains(room_input)]
        room_summary['Display Schedule'] = room_summary['Subject Code'] + ' ' + room_summary['Section']
        # st.write(room_summary)
        display_room_summary = room_summary[['Subject Code and Name', 'Section', 'Room', 'Instructor', 'Time']]
        st.write(display_room_summary)
        room_schedule_dict = {timeslot : row[17] for row in room_summary.values for timeslot in row[15]}
        # st.write(room_schedule_dict)
    except:
        st.write('You have not input anything, or your input is incorrect. Please try again.')

    st.subheader('Room Schedule Table')
    try:
        if room_schedule_dict == {}:
            st.write('This room is empty.')
        else:
            room_schedule_vector = pd.Series(np.arange(1, 181)).replace(room_schedule_dict)
            room_schedule_vector = ['' if type(room_schedule_vector[i]) == int else room_schedule_vector[i] for i in range(180)]
            # st.write(room_schedule_vector)

            room_schedule_table = pd.DataFrame(pd.Series(room_schedule_vector).values.reshape(6, 30).T)
            room_schedule_table = room_schedule_table.iloc[:29]
            room_schedule_table.rename(columns = {0 : 'Monday',
                                                  1 : 'Tuesday',
                                                  2 : 'Wednesday',
                                                  3 : 'Thursday',
                                                  4 : 'Friday',
                                                  5 : 'Saturday'},
                                       index = pd.Series(timeslots), inplace = True)
            st.table(room_schedule_table)
    except:
        st.write('You have not input anything, or your input is incorrect. Please try again.')

with tab7:
    # Buildings Processing

    complete_rooms = room_unique
    complete_rooms['Building'] = complete_rooms['Room']
    # st.write(complete_rooms)
    
    bldg_dict = {
        'Arete' : ['ABS CBN CORPORATION INNOVATION CLASSROOM', 'ART GAL',
                   'BLACK BOX THEATER FA', 'BRAZIER KITCHEN',
                   'CO BUN TING AND PO TY LEE CO MAC LAB', "COLLEGE '66 CO-LAB", 'FA DEPT',
                   'INNOVATION 201', 'INNOVATION 202', 'JOSEPH AND GEMMA TANBUNTIONG STUDIO',
                   'NATIONAL BOOKSTORE ATELIER', 'YAO SIU LUN MAC LAB'],  
        'C' : ['CH DEPT'],
        'CTC' : ['HSC DEPT'],
        'DLC' : ['EN DEPT', 'FIL DEPT', 'IS DEPT', 'PH DEPT', 'TH DEPT'],
        'F' : ['CS DEPT', 'PS DEPT'],
        'LH' : ['DS DEPT', 'EC DEPT', 'EU DEPT', 'JSP OFFICE', 'POS DEPT'],
        'MO' : ['ES DEPT'],
        'PE Complex' : ['COV COURTS', 'DANCE AREA', 'LS POOL', 'MARTIAL ARTS CE',
                        'MARTIAL ARTS RM', 'MULTI-PUR RM', 'TAB TEN AREA', 'TENNIS CRT', 'WEIGHTS GYM'],      
        'SEC-A' : ['BIO DEPT', 'MA DEPT'],
        'SOM' : ['L&S DEPT', 'QMIT OFFICE'],
        'SS' : ['COM STUD', 'CORD TRNG RM', 'GROUP THERAPY RM', 'PSY COMP RM']
    }

    complete_bldg_dict = {}
    for key, value in bldg_dict.items():
        for room in value:
            complete_bldg_dict[room] = key
    # st.write(complete_bldg_dict)

    complete_rooms = complete_rooms.replace({'Building' : complete_bldg_dict}).dropna(how = 'all')
    # st.write(complete_rooms)
    for i in range(len(complete_rooms)):
        for bldg in ['B', 'BEL', 'C', 'F', 'G', 'K']: # Bldg-Room
            complete_rooms['Building'][i] = re.sub(f'^{bldg}-.+', f'{bldg}', complete_rooms['Building'][i])
        for char in ['A', 'B', 'C']: # SEC-XRoom
            complete_rooms['Building'][i] = re.sub(f'^SEC-{char}.+', f'SEC-{char}', complete_rooms['Building'][i])
        for bldg in ['BEL', 'CTC', 'LH', 'SOM', 'SS']: # Bldg Room; BEL 211 is anomalous
            complete_rooms['Building'][i] = re.sub(f'^{bldg}.+', f'{bldg}', complete_rooms['Building'][i])
        complete_rooms['Building'][i] = re.sub(f'^FA ANNEX .+$', f'FA ANNEX', complete_rooms['Building'][i])
    st.subheader('Room & Buildling Shorcuts Table')
    st.write(complete_rooms)

    complete_bldgs = pd.Series(complete_rooms['Building'].unique()).sort_values()\
                     .reset_index().rename(columns = {0 : 'Building'}).drop(columns = ['index'])
    # st.table(complete_bldgs)
    
    bldg_coords = [
        ['Arete', 'Arete', 14.6415, 121.0754],
        ['Bellarmine', 'BEL', 14.6418, 121.0797],
        ['Berchmans', 'B', 14.6395, 121.0785],
        ['PLDT-Convergent Technologies Center' ,'CTC', 14.6383, 121.0764],
        ['De La Costa', 'DLC', 14.6401, 121.0766],
        ['Faura', 'F', 14.6397, 121.0766],
        ['Gonzaga', 'G', 14.6391, 121.0782],
        ['Kostka', 'K', 14.6398, 121.0781],
        ['Leong Hall', 'LH', 14.6408, 121.0763],
        ['Manila Observatory', 'MO', 14.6358, 121.0777],
        ['PE Complex', 'PE Complex', 14.6373, 121.0786],
        ['Schmitt', 'C', 14.6392, 121.0774],
        ['Science Education Complex A', 'SEC A', 14.6383, 121.0778],
        ['Science Education Complex B', 'SEC B', 14.6380, 121.0772],
        ['Science Education Complex C', 'SEC C', 14.6380, 121.0767],
        ['School of Management', 'SOM', 14.6385, 121.0762],
        ['Social Sciences', 'SS', 14.6407, 121.0767],
    ]
    
    bldg_coords_df = pd.DataFrame(bldg_coords, columns = ['Building', 'Abbreviation', 'Latitude', 'Longitude'])

    # Create a Folium map
    m = folium.Map(location=[bldg_coords_df['Latitude'].mean(), bldg_coords_df['Longitude'].mean()], zoom_start=17.25, min_zoom=16, max_zoom=20)

    # Add markers for each city
    for i, row in bldg_coords_df.iterrows():
        folium.Marker([row['Latitude'], row['Longitude']],
                      popup=row['Building'] + ' (' + row['Abbreviation'] + ')',
                      icon=folium.DivIcon(html = f'''<div><svg>
    <circle cx='20' cy='30' r='20' fill='#add8e6' opacity='1'/>
    <text x='15' y='30' fill='black'>{i+1}</text>
    </svg></div>''')).add_to(m)

    # Display the map using streamlit's st.map
    st.subheader('Ateneo Map')
    folium_static(m)

    bldg_details_display = bldg_coords_df[['Building', 'Abbreviation']]
    bldg_details_display['Number'] = np.arange(1, len(bldg_details_display)+1)
    bldg_details_display = bldg_details_display.set_index(bldg_details_display['Number'])
    bldg_details_display = bldg_details_display.drop(columns = ['Number'])
    st.table(bldg_details_display)

with tab8:
    st.subheader('About Me and the Project')
    st.write('''I am Sted Micah Cheng from 4 BS Applied Mathematics - Data Science.
\nThe first major project in this website is FACILE (Free Assistance for Class Indices in the Luck-Based Enlistment).
It started from a simple idea to avoid scrolling through lists of schedules, with only first and second year core elective subjects
(NatSc, PHILO 11, FLC, and PE) where one had to manually input the schedule (e.g. M-TH 0800-0930) to the Python code
that converts it to timeslot numbers (3 4 5 93 94 95).
It used to be in a Google Sheets file with over 800 columns, making it quite clunky.
\nThe other major project in this website is AIV (AISIS Information Viewer, formerly the Syllabus Viewer).
It started when I noticed patterns about the syllabus links, and around this time I also realized that they can all be
opened in incognito mode. The instructions are almost all copied and pasted from the Google Document where they all used to be.
\nThankfully, I was able to discover this website and integrate both of these into one platform.
Hopefully this gives you a more streamlined experience of using them, as well as the other side projects I have here.''')
    st.subheader('Problems, Questions, Suggestions?')
    fb = 'facebook.com/stedcheng'
    st.write('''Feel free to contact me via email (sted.cheng@student.ateneo.edu) or Facebook Messenger ([Sted Cheng](%s)).
             If your message is regarding a code error, please screenshot the error and inform me what you inputted in the website.''' % fb)
       
    #misc
    # dept_filter = st.multiselect('Department', dept_full_names)
    # st.dataframe(complete_list[complete_list['Department'].isin(dept_filter)])


