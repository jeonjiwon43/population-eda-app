import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Population Trends 데이터셋**

                - 설명: 대한민국의 연도별 지역 인구, 출생아 수, 사망자 수 등을 기록한 인구 통계 데이터  
                - 주요 변수:  
                  - `연도`: 데이터가 기록된 기준 연도  
                  - `지역`: 전국 및 시·도 단위 지역명  
                  - `인구`: 해당 연도와 지역의 전체 인구 수  
                  - `출생아수(명)`: 연도별 출생한 신생아 수  
                  - `사망자수(명)`: 연도별 사망자 수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide")
sns.set_style("whitegrid")

st.title("📊 Population Trends EDA")

uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
if not uploaded:
    st.info("Please upload the population_trends.csv file.")
    st.stop()

df = pd.read_csv(uploaded)

# ---------------------
# Preprocessing
# ---------------------
df.replace("-", np.nan, inplace=True)

sejong_mask = df['지역'] == '세종'
df.loc[sejong_mask] = df.loc[sejong_mask].fillna(0)

numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
df['연도'] = df['연도'].astype(int)

# Tabs
tabs = st.tabs(["Basic Stats", "Nationwide Trend", "Regional Change", "Top Growth", "Visualization"])

# ---------------------
# Tab 1: Basic Stats
# ---------------------
with tabs[0]:
    st.header("📋 Basic Statistics")
    st.subheader("Data Info")
    buffer = df.info(buf=None)
    st.text(str(buffer))

    st.subheader("Descriptive Statistics")
    st.dataframe(df.describe())

# ---------------------
# Tab 2: Nationwide Trend + Forecast
# ---------------------
with tabs[1]:
    st.header("📈 Nationwide Population Trend + Forecast")

    nationwide = df[df['지역'] == '전국'].copy()

    fig, ax = plt.subplots()
    ax.plot(nationwide['연도'], nationwide['인구'], marker='o', label='Actual')

    # Forecast 2035 using average delta of last 3 years
    recent = nationwide.tail(3)
    delta = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
    last_year = nationwide['연도'].max()
    last_pop = nationwide['인구'].iloc[-1]
    forecast_year = 2035
    years_ahead = forecast_year - last_year
    forecast_pop = last_pop + delta * years_ahead

    ax.plot(forecast_year, forecast_pop, 'ro', label='Forecast 2035')
    ax.annotate(f'{int(forecast_pop):,}', (forecast_year, forecast_pop), textcoords="offset points", xytext=(0,10), ha='center')

    ax.set_title("National Population Trend and Forecast")
    ax.set_xlabel("Year")
    ax.set_ylabel("Population")
    ax.legend()
    st.pyplot(fig)

# ---------------------
# Tab 3: Regional Change Analysis
# ---------------------
with tabs[2]:
    st.header("📊 Regional Population Change")

    recent_year = df['연도'].max()
    prev_year = recent_year - 5

    df_region = df[df['지역'] != '전국'].copy()
    df_recent = df_region[df_region['연도'].isin([prev_year, recent_year])]
    pivot = df_recent.pivot(index='지역', columns='연도', values='인구')
    pivot['Change'] = (pivot[recent_year] - pivot[prev_year]) / 1000
    pivot['Rate'] = ((pivot[recent_year] - pivot[prev_year]) / pivot[prev_year]) * 100
    pivot = pivot.sort_values('Change', ascending=False)

    # 지역명 영어로 번역
    region_map = {name: f"Region {i+1}" for i, name in enumerate(pivot.index)}
    pivot.index = pivot.index.map(region_map)

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.barplot(x='Change', y=pivot.index, ax=ax, palette='coolwarm')
    for i, v in enumerate(pivot['Change']):
        ax.text(v, i, f"{v:.1f}K", va='center')
    ax.set_title("5-Year Regional Population Change")
    ax.set_xlabel("Change (thousands)")
    ax.set_ylabel("Region")
    st.pyplot(fig)

    # 변화율 그래프
    st.subheader("📉 Population Change Rate")
    fig2, ax2 = plt.subplots(figsize=(10, 8))
    sns.barplot(x='Rate', y=pivot.index, ax=ax2, palette='vlag')
    for i, v in enumerate(pivot['Rate']):
        ax2.text(v, i, f"{v:.1f}%", va='center')
    ax2.set_title("5-Year Regional Change Rate")
    ax2.set_xlabel("Change Rate (%)")
    ax2.set_ylabel("Region")
    st.pyplot(fig2)

    st.markdown("> These charts highlight the absolute and percentage change in population by region over the last 5 years.")

# ---------------------
# Tab 4: Top Growth Regions
# ---------------------
with tabs[3]:
    st.header("📈 Top 100 Population Changes")

    df_region = df[df['지역'] != '전국'].copy()
    df_region['Diff'] = df_region.groupby('지역')['인구'].diff()
    df_top = df_region.sort_values('Diff', ascending=False).head(100).copy()
    df_top['Diff Comma'] = df_top['Diff'].apply(lambda x: f"{int(x):,}")

    def highlight_diff(val):
        color = 'background-color: lightcoral' if val < 0 else 'background-color: lightblue'
        return color

    st.dataframe(
        df_top[['연도', '지역', '인구', 'Diff', 'Diff Comma']].style
        .applymap(lambda v: 'background-color: lightcoral' if isinstance(v, (int, float)) and v < 0 else 'background-color: lightblue', subset=['Diff'])
        .format({'인구': '{:,}', 'Diff': '{:,}'})
    )

# ---------------------
# Tab 5: Visualization - Area Chart
# ---------------------
with tabs[4]:
    st.header("🌍 Population Heatmap / Area Chart")

    pivot_area = df[df['지역'] != '전국'].pivot(index='연도', columns='지역', values='인구')
    fig, ax = plt.subplots(figsize=(12, 6))
    pivot_area.plot.area(ax=ax, colormap='tab20')
    ax.set_title("Stacked Area Chart of Regional Populations")
    ax.set_xlabel("Year")
    ax.set_ylabel("Population")
    st.pyplot(fig)

    st.markdown("> This stacked area chart illustrates the relative population contributions of each region over time.")

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()