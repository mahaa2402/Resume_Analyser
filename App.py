import subprocess
import sys

import streamlit as st
import nltk
import spacy

nltk.download('stopwords')


def _ensure_spacy_english():
    try:
        spacy.load('en_core_web_sm')
    except OSError:
        subprocess.check_call(
            [sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm']
        )
        spacy.load('en_core_web_sm')



import hashlib

import pandas as pd
import base64, random
import time, datetime
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io, random
from streamlit_tags import st_tags
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import plotly.express as px
import yt_dlp


def fetch_yt_video(link):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 20,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
        title = (info or {}).get('title')
        return title if title else 'Video'
    except Exception:
        return 'Video'


def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = (
        f'<a class="rs-btn-dl" href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    )
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def course_recommender(course_list, upload_id):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider(
        'Choose Number of Course Recommendations:',
        1, 10, 4,
        key=f'num_courses_{upload_id}',
    )
    course_list = list(course_list)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


def _init_mysql():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='root123',
            db='sra',
            connect_timeout=5,
        )
        return conn, conn.cursor()
    except Exception:
        return None, None


connection, cursor = _init_mysql()


def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses):
    if cursor is None or connection is None:
        return
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (
    name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills,
    courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


def _inject_ui_theme() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap');

html, body, .stApp { font-family: 'Instrument Sans', system-ui, sans-serif !important; }

[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {
    display: none !important;
}

.stApp {
    background: linear-gradient(165deg, #e0f2f1 0%, #ecfdf5 18%, #f0fdfa 38%, #f8fafc 65%, #e8eef5 100%) !important;
}

[data-testid="stAppViewContainer"] > .main {
    background: rgba(255, 255, 255, 0.45) !important;
}

.block-container {
    padding-top: 0.75rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 900px !important;
    background: rgba(255, 255, 255, 0.78) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(15, 118, 110, 0.14) !important;
    box-shadow: 0 8px 32px rgba(15, 23, 42, 0.06) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #134e4a 0%, #0f766e 45%, #115e59 100%) !important;
    border-right: none !important;
    box-shadow: 4px 0 24px rgba(15, 23, 42, 0.12) !important;
}

[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown strong,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label span {
    color: #ecfdf5 !important;
}

[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.12) !important;
    border: 1px solid rgba(167, 243, 208, 0.35) !important;
}

[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span {
    color: #f0fdfa !important;
}

.rs-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.85rem 1.25rem;
    margin: -0.35rem -0.5rem 1.25rem -0.5rem;
    background: linear-gradient(90deg, #0f766e 0%, #0d9488 50%, #14b8a6 100%);
    border-radius: 12px;
    border: 1px solid rgba(167, 243, 208, 0.35);
    box-shadow: 0 8px 28px rgba(13, 148, 136, 0.28);
}

.rs-brand {
    font-weight: 700;
    font-size: 1.15rem;
    letter-spacing: -0.03em;
    color: #ffffff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

.rs-topbar-meta {
    font-size: 0.75rem;
    color: #ccfbf1;
    font-weight: 500;
    opacity: 0.95;
}

.rs-landing {
    text-align: center;
    padding: 2rem 1rem 2.5rem 1rem;
    margin-bottom: 1.5rem;
    background: linear-gradient(180deg, #ffffff 0%, #f0fdfa 100%);
    border: 1px solid rgba(45, 212, 191, 0.25);
    border-radius: 14px;
    box-shadow: 0 6px 28px rgba(13, 148, 136, 0.12);
}

.rs-badge {
    display: inline-block;
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #0f766e;
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    margin-bottom: 1.25rem;
}

.rs-landing h1 {
    font-size: clamp(1.65rem, 4vw, 2.15rem);
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -0.035em;
    color: #0f172a !important;
    margin: 0 0 0.85rem 0;
    border: none !important;
}

.rs-lead {
    font-size: 1rem;
    line-height: 1.6;
    color: #64748b;
    max-width: 32rem;
    margin: 0 auto 1.75rem auto;
}

.rs-features {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 1rem 2rem;
    margin-bottom: 1.5rem;
    text-align: left;
}

.rs-feat {
    flex: 1 1 140px;
    max-width: 200px;
    padding: 0.85rem 1rem;
    background: linear-gradient(145deg, #f0fdfa 0%, #ecfeff 100%);
    border-radius: 10px;
    border: 1px solid rgba(13, 148, 136, 0.2);
}

.rs-feat strong {
    display: block;
    font-size: 0.8125rem;
    color: #0f172a;
    margin-bottom: 0.25rem;
}

.rs-feat span {
    font-size: 0.8125rem;
    color: #64748b;
    line-height: 1.45;
}

.rs-cta-hint {
    font-size: 0.8125rem;
    color: #94a3b8;
    font-weight: 500;
    margin: 0;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #0d9488, #14b8a6) !important;
}

a.rs-btn-dl {
    display: inline-block;
    margin-top: 0.5rem;
    padding: 0.45rem 1rem;
    border-radius: 8px;
    background: #0f766e;
    color: #fff !important;
    text-decoration: none !important;
    font-weight: 600;
    font-size: 0.875rem;
}

[data-testid="stExpander"] {
    border: 1px solid rgba(13, 148, 136, 0.22) !important;
    border-radius: 10px !important;
    background: linear-gradient(180deg, #ffffff 0%, #f8fffc 100%) !important;
}

[data-testid="stFileUploader"] {
    padding: 0.5rem 0;
}
</style>
        """,
        unsafe_allow_html=True,
    )


_LANDING_HTML = """
<section class="rs-landing">
  <div class="rs-badge">Résumé analysis</div>
  <h1>Clarity for your next career move</h1>
  <p class="rs-lead">Upload a PDF to extract skills, review common sections against a simple checklist,
  and receive focused course and video suggestions—no accounts, no clutter.</p>
  <div class="rs-features">
    <div class="rs-feat"><strong>Parse</strong><span>Skills and structure from your document</span></div>
    <div class="rs-feat"><strong>Score</strong><span>Quick pass on typical recruiter expectations</span></div>
    <div class="rs-feat"><strong>Learn</strong><span>Curated resources matched to detected focus</span></div>
  </div>
  <p class="rs-cta-hint">Choose a PDF file below to begin.</p>
</section>
"""


st.set_page_config(
    page_title="Resume Studio",
    page_icon='./Logo/SRA_Logo.ico',
    layout="wide",
    initial_sidebar_state="expanded",
)


def run():
    _inject_ui_theme()

    st.markdown(
        '<div class="rs-topbar"><span class="rs-brand">Resume Scout</span>'
        '<span class="rs-topbar-meta">Use the sidebar to switch to Admin</span></div>',
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("**Workspace**")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Mode", activities)

    if cursor is not None and connection is not None:
        db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
        cursor.execute(db_sql)
        connection.select_db("sra")

        DB_table_name = 'user_data'
        table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills TEXT NOT NULL,
                     Recommended_skills TEXT NOT NULL,
                     Recommended_courses TEXT NOT NULL,
                     PRIMARY KEY (ID));
                    """
        cursor.execute(table_sql)
        cursor.execute(
            """SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = 'Actual_skills'""",
            (DB_table_name,),
        )
        _col = cursor.fetchone()
        if _col and str(_col[0]).lower() == "varchar":
            cursor.execute(
                f"""ALTER TABLE {DB_table_name}
                   MODIFY Actual_skills TEXT NOT NULL,
                   MODIFY Recommended_skills TEXT NOT NULL,
                   MODIFY Recommended_courses TEXT NOT NULL"""
            )
            connection.commit()
    if choice == 'Normal User':
        landing_slot = st.empty()
        pdf_file = st.file_uploader("PDF résumé", type=["pdf"])
        if pdf_file is None:
            landing_slot.markdown(_LANDING_HTML, unsafe_allow_html=True)
        else:
            landing_slot.empty()
        if pdf_file is not None:
            upload_id = hashlib.md5(pdf_file.getvalue()).hexdigest()[:16]
            # with st.spinner('Uploading your Resume....'):
            #     time.sleep(4)
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            with st.expander("Document preview", expanded=True):
                show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' + resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                                unsafe_allow_html=True)

                st.subheader("**Skills Recommendation💡**")
                ## Skill shows
                skills_list = resume_data.get('skills') or []
                keywords = st_tags(
                    label='### Skills that you have',
                    text='See our skills recommendation',
                    value=skills_list,
                    key=f'skills_tags_{upload_id}',
                )

                ##  recommendation
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep Learning', 'flask',
                              'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = ''
                ## Courses recommendation
                for i in skills_list:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                              'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                              'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                              'Streamlit']
                        recommended_keywords = st_tags(
                            label='### Recommended skills for you.',
                            text='Recommended skills generated from System',
                            value=recommended_skills,
                            key=f'reco_ds_{upload_id}',
                        )
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course, upload_id)
                        break

                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                              'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(
                            label='### Recommended skills for you.',
                            text='Recommended skills generated from System',
                            value=recommended_skills,
                            key=f'reco_web_{upload_id}',
                        )
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(web_course, upload_id)
                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(
                            label='### Recommended skills for you.',
                            text='Recommended skills generated from System',
                            value=recommended_skills,
                            key=f'reco_and_{upload_id}',
                        )
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(android_course, upload_id)
                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        recommended_keywords = st_tags(
                            label='### Recommended skills for you.',
                            text='Recommended skills generated from System',
                            value=recommended_skills,
                            key=f'reco_ios_{upload_id}',
                        )
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course, upload_id)
                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                              'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(
                            label='### Recommended skills for you.',
                            text='Recommended skills generated from System',
                            value=recommended_skills,
                            key=f'reco_uiux_{upload_id}',
                        )
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course, upload_id)
                        break

                #
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'Objective' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',
                        unsafe_allow_html=True)

                if 'Declaration' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Declaration✍</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',
                        unsafe_allow_html=True)

                if 'Hobbies' in resume_text or 'Interests' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Hobbies⚽. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',
                        unsafe_allow_html=True)

                if 'Achievements' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>''',
                        unsafe_allow_html=True)

                if 'Projects' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>''',
                        unsafe_allow_html=True)

                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Writing Score: ' + str(score) + '**')
                st.warning(
                    "** Note: This score is calculated based on the content that you have added in your Resume. **")
                _bk = f"rs_balloons_{upload_id}"
                if st.session_state.get(_bk) != "done":
                    st.balloons()
                    st.session_state[_bk] = "done"

                insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                            str(resume_data['no_of_pages']), reco_field, cand_level, str(skills_list),
                            str(recommended_skills), str(rec_course))

                ## Resume writing video
                st.header("**Bonus Video for Resume Writing Tips💡**")
                vid_rng = random.Random(int(upload_id, 16))
                resume_vid = vid_rng.choice(resume_videos)
                res_vid_title = fetch_yt_video(resume_vid)
                st.subheader("✅ **" + res_vid_title + "**")
                st.video(resume_vid)

                ## Interview Preparation Video
                st.header("**Bonus Video for Interview👨‍💼 Tips💡**")
                interview_vid = vid_rng.choice(interview_videos)
                int_vid_title = fetch_yt_video(interview_vid)
                st.subheader("✅ **" + int_vid_title + "**")
                st.video(interview_vid)

                if connection is not None:
                    connection.commit()
            else:
                st.error('Something went wrong..')
    else:
        ## Admin Side
        st.subheader("Administrator")
        st.caption("View stored analyses and charts.")

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if cursor is None or connection is None:
                st.error(
                    "MySQL is not available in this environment (e.g. Streamlit Cloud has no localhost database). "
                    "Use the app in **Normal User** mode, or connect a hosted database via secrets."
                )
            elif ad_user == 'admin1' and ad_password == 'admin1':
                st.success("Welcome Mahaa")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)

                pf_col = "Predicted_Field"
                ul_col = "User_level"
                if pf_col in plot_data.columns and plot_data[pf_col].notna().any():
                    pf_counts = (
                        plot_data[pf_col]
                        .fillna("(empty)")
                        .value_counts()
                        .reset_index()
                    )
                    pf_counts.columns = ["field", "count"]
                    st.subheader("📈 **Pie-Chart for Predicted Field Recommendations**")
                    fig = px.pie(
                        pf_counts,
                        values="count",
                        names="field",
                        title="Predicted field (from parsed skills)",
                    )
                    st.plotly_chart(fig)
                else:
                    st.info("No predicted-field data to chart yet.")

                if ul_col in plot_data.columns and plot_data[ul_col].notna().any():
                    ul_counts = (
                        plot_data[ul_col]
                        .fillna("(empty)")
                        .value_counts()
                        .reset_index()
                    )
                    ul_counts.columns = ["level", "count"]
                    st.subheader("📈 **Pie-Chart for User's Experienced Level**")
                    fig = px.pie(
                        ul_counts,
                        values="count",
                        names="level",
                        title="Experience level (by resume length signal)",
                    )
                    st.plotly_chart(fig)
                else:
                    st.info("No experience-level data to chart yet.")


            else:
                st.error("Wrong ID & Password Provided")


run()
