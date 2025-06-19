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
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")

        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)
        df.replace("-", 0, inplace=True)
        df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric)
        df['연도'] = df['연도'].astype(int)

        # 지역명 변환 딕셔너리
        region_translation = {
            "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon",
            "광주": "Gwangju", "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong",
            "경기": "Gyeonggi", "강원": "Gangwon", "충북": "Chungbuk", "충남": "Chungnam",
            "전북": "Jeonbuk", "전남": "Jeonnam", "경북": "Gyeongbuk", "경남": "Gyeongnam",
            "제주": "Jeju"
        }

        tabs = st.tabs(["📋 데이터 개요", "📈 연도별 추이", "🏙️ 지역별 변화", "📉 증감량 상위 분석", "📊 누적 시각화"])

        # 1. 데이터 개요 및 품질 확인
        with tabs[0]:
            st.header("📋 데이터 개요 및 품질 점검")
            st.markdown("""
            **목적**: 데이터셋의 구조와 품질을 점검하여 분석 전 기초 정보를 확보합니다.
            - 결측치, 중복값, 데이터 타입 등을 확인합니다.
            """)
            st.subheader("Data Info")
            buf = io.StringIO()
            df.info(buf=buf)
            st.text(buf.getvalue())

            st.subheader("Descriptive Statistics")
            st.dataframe(df.describe())

            st.subheader("결측치 확인")
            st.bar_chart(df.isnull().sum())

            st.write(f"중복 행 개수: {df.duplicated().sum()}")

        # 2. 연도별 전체 인구 추이
        with tabs[1]:
            st.header("📈 연도별 전국 인구 추이")
            st.markdown("""
            **목적**: 전국 인구의 장기적인 증감 추세를 시각화하고,  
            최근 3년간 평균 순증가량을 바탕으로 2035년 인구를 예측해봅니다.
            """)
            nationwide = df[df['지역'] == '전국']
            fig, ax = plt.subplots()
            ax.plot(nationwide['연도'], nationwide['인구'], marker='o')
            ax.set_title("Total Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)

            # 예측
            recent = nationwide[nationwide['연도'] >= nationwide['연도'].max() - 2]
            net_change = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            future_year = 2035
            last_year = nationwide['연도'].max()
            future_population = nationwide[nationwide['연도'] == last_year]['인구'].values[0] + (future_year - last_year) * net_change

            ax.axhline(future_population, color='red', linestyle='--', label=f"Predicted 2035: {int(future_population):,}")
            ax.legend()
            st.pyplot(fig)

        # 3. 지역별 변화량 및 증감률 분석
        with tabs[2]:
            st.header("🏙️ 최근 5년간 지역별 인구 변화")
            st.markdown("""
            **목적**: 시도별 인구 변화량 및 성장률을 통해 어떤 지역이 성장하거나 감소하는지 파악합니다.
            """)
            latest_year = df['연도'].max()
            base_year = latest_year - 5
            df_filtered = df[(df['지역'] != '전국') & (df['연도'].isin([base_year, latest_year]))]
            pivot = df_filtered.pivot(index='지역', columns='연도', values='인구')
            pivot['change'] = pivot[latest_year] - pivot[base_year]
            pivot['percent'] = 100 * pivot['change'] / pivot[base_year]
            pivot.index = [region_translation.get(idx, idx) for idx in pivot.index]
            pivot = pivot.sort_values('change', ascending=False)

            st.subheader("절대 인구 변화량")
            fig1, ax1 = plt.subplots()
            sns.barplot(x='change', y=pivot.index, ax=ax1, palette='coolwarm')
            ax1.set_title("Population Change (5yrs)")
            st.pyplot(fig1)

            st.subheader("인구 변화율 (%)")
            fig2, ax2 = plt.subplots()
            sns.barplot(x='percent', y=pivot.index, ax=ax2, palette='coolwarm')
            ax2.set_title("Population Change Rate (%)")
            st.pyplot(fig2)

        # 4. 변화량 상위 지역 도출
        with tabs[3]:
            st.header("📉 연도별 지역 인구 증감 상위 Top 100")
            st.markdown("""
            **목적**: 연도별 인구 변화량 기준으로 상위 변동 사례를 분석하고 특이 지역을 파악합니다.
            """)
            df_region = df[df['지역'] != '전국'].copy()
            df_region['change'] = df_region.groupby('지역')['인구'].diff()
            top100 = df_region.sort_values('change', ascending=False).head(100)

            top100['지역'] = top100['지역'].map(region_translation)
            top100['인구'] = top100['인구'].apply(lambda x: f"{int(x):,}")
            top100['change'] = top100['change'].apply(lambda x: f"{int(float(x)):,}" if pd.notnull(x) else '-')

            styled = top100[['연도', '지역', '인구', 'change']].style \
                .background_gradient(subset='change', cmap='RdBu_r') \
                .format({'change': '{:,}', '인구': '{:,}'})

            st.dataframe(styled, use_container_width=True)

        # 5. 누적 시각화
        with tabs[4]:
            st.header("📊 연도별 지역별 인구 누적 영역 그래프")
            st.markdown("""
            **목적**: 전체 인구에서 각 지역이 차지하는 비중과 구성 변화 추세를 시각화합니다.
            """)
            df_area = df[df['지역'] != '전국'].copy()
            df_area['지역'] = df_area['지역'].map(region_translation)
            pivot_area = df_area.pivot(index='연도', columns='지역', values='인구')
            fig3, ax3 = plt.subplots(figsize=(12, 6))
            pivot_area.plot.area(ax=ax3, colormap='tab20')
            ax3.set_title("Population Stacked Area by Region")
            ax3.set_xlabel("Year")
            ax3.set_ylabel("Population")
            st.pyplot(fig3)

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