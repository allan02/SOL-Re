import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="신한금융그룹 스테이블코인 인텔리전스",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 메인 페이지
def main():
    # 신한금융그룹 브랜드 스타일 적용
    st.markdown("""
    <style>
    /* 신한금융그룹 브랜드 폰트 및 색상 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    .main-header {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a1a;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #0066cc 0%, #004499 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-top: 0px;
    }
    
    .sub-header {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 300;
    }
    
    .character-title {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: #0066cc;
        text-align: center;
        margin-bottom: 1.5rem;
        text-shadow: 0 2px 4px rgba(0, 102, 204, 0.1);
    }
    
    .character-description {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 1rem;
        color: #495057;
        text-align: center;
        margin-top: 1rem;
        line-height: 1.6;
        font-weight: 400;
    }
    
    .image-container {
        text-align: center;
        margin: 2rem 0;
        transition: all 0.3s ease;
    }
    
    .image-container:hover {
        transform: translateY(-5px);
    }
    
    .character-image {
        width: 60%;
        max-width: 300px;
        cursor: pointer;
        border: 3px solid #0066cc;
        border-radius: 15px;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(0, 102, 204, 0.2);
    }
    
    .character-image:hover {
        transform: scale(1.05);
        border-color: #004499;
        box-shadow: 0 12px 35px rgba(0, 102, 204, 0.3);
    }
    
    .brand-footer {
        text-align: center;
        margin-top: 3rem;
        padding: 1rem;
        color: #666;
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 0.9rem;
        border-top: 1px solid #e9ecef;
    }
    
    .logo-container {
        position: absolute;
        top: 20px;
        left: 20px;
        z-index: 1000;
        background: white;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .logo-image {
        width: 150px;
        height: auto;
        display: block;
    }
    
    .main-content {
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 로고와 제목을 같은 라인에 배치
    with st.container():
        col_logo, col_title, col_spacer = st.columns([2, 6, 2])
        with col_logo:
            st.image("images/logo.png", width=200)
        with col_title:
            st.markdown('<h2 class="main-header">Shinhan Stable Coin Intelligence Platform</h2>', unsafe_allow_html=True)
        with col_spacer:
            st.write("")  # 빈 공간
    
    # 메인 콘텐츠를 로고 아래로 이동
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # 헤더 섹션은 제거 (로고와 같은 라인에 배치했으므로)
    
    # 두 개의 캐릭터 섹션을 나란히 배치
    col1, col2 = st.columns(2)
    
    with col1:
        # 왼쪽 - 영업점 직원 (쏠 캐릭터)
        # 쏠(SOL) 캐릭터 이미지
        st.markdown("""
        <div class="image-container">
            <a href="?page=branch_employee" target="_self">
                <img src="data:image/png;base64,{}" class="character-image" alt="쏠(SOL) - 영업점 직원">
            </a>
        </div>
        """.format(get_image_base64("images/sol.png")), unsafe_allow_html=True)
        
        st.markdown('<h3 class="character-title">🏪 영업점</h3>', unsafe_allow_html=True)
        st.markdown('<p class="character-description">북극성의 여행 작가 쏠처럼,<br>영업점에서 고객과 함께하는 특별한 여행을 시작해보세요</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # 오른쪽 - 본부부서 직원 (몰리 캐릭터)
        # 몰리(MOLI) 캐릭터 이미지
        st.markdown("""
        <div class="image-container">
            <a href="?page=headquarters_employee" target="_self">
                <img src="data:image/png;base64,{}" class="character-image" alt="몰리(MOLI) - 본부부서 직원">
            </a>
        </div>
        """.format(get_image_base64("images/moli.png")), unsafe_allow_html=True)
        
        st.markdown('<h3 class="character-title">🏢 본부부서</h3>', unsafe_allow_html=True)
        st.markdown('<p class="character-description">식물 카페의 느긋한 사장님 몰리처럼,<br>본부에서 차분하게 전략을 세워보세요</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 브랜드 푸터
    st.markdown('<div class="brand-footer">', unsafe_allow_html=True)
    st.markdown('<p>© 2024 SHINHAN FINANCIAL GROUP. All Rights Reserved.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # main-content div 닫기
    st.markdown('</div>', unsafe_allow_html=True)
    
    # URL 파라미터에 따른 페이지 이동 처리
    query_params = st.query_params
    if "page" in query_params:
        page = query_params["page"]
        if page == "branch_employee":
            st.switch_page("pages/branch_employee.py")
        elif page == "headquarters_employee":
            st.switch_page("pages/headquarters_employee.py")

def get_image_base64(image_path):
    """이미지를 base64로 인코딩하는 함수"""
    import base64
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

if __name__ == "__main__":
    main()
