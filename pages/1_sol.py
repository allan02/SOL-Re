import streamlit as st
import sys
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# utils 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

# dictionary 모듈 import
import dictionary

# 페이지 설정
st.set_page_config(
    page_title="SOL",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 메인 페이지
def branch_employee_main():
    # 신한금융그룹 브랜드 스타일 적용
    st.markdown("""
    <style>
    /* 신한금융그룹 브랜드 폰트 및 색상 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    .brand-footer {
        text-align: center;
        margin-top: 3rem;
        padding: 1rem;
        color: #666;
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 0.9rem;
        border-top: 1px solid #e9ecef;
    }
    
    .divider {
        width: 2px;
        background: linear-gradient(180deg, #0066cc 0%, #004499 100%);
        margin: 0 2rem;
        border-radius: 1px;
        height: 400px;
    }
    
    .sidebar-container {
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    </style>
    """, unsafe_allow_html=True)
    
    # 로고와 버튼들을 같은 라인에 배치
    with st.container():
        col_logo, col_spacer, col_buttons = st.columns([2, 4, 4])
        with col_logo:
            st.image("images/logo.png", width=200)
        with col_spacer:
            st.write("")  # 빈 공간
        with col_buttons:
            st.write("")  # 빈 공간
    
    # 사이드바와 메인 화면을 분리한 레이아웃
    col1, col2, col3 = st.columns([2, 1, 7])
    
    with col1:
        # 솔 페이지 이미지 추가
        st.image("images/sol_page.png", use_container_width="always")
    
    with col3:
        # 용어 검색 인터페이스
        st.markdown("## 부동산 Q&A")
        st.markdown("부동산 관련 다양한 질문 검색 가능합니다.")
        
        # 검색 입력
        search_query = st.text_input("", placeholder="15억 이상 주택 대출 얼마 나오나요?")
        
        if st.button("검색", type="secondary", use_container_width=True):
            if search_query:
                with st.spinner("답변을 생성하고 있습니다..."):
                    try:
                        # KB 포함 여부를 먼저 확인
                        in_kb = dictionary.is_question_in_kb(search_query)
                        
                        # 답변 생성
                        answer, used_web_search = dictionary.get_dictionary_answer_with_info(search_query)
                        
                        # 메시지 표시 로직
                        if used_web_search:
                            # 웹 검색이 사용된 경우 (경고 색상 - 분홍/붉은색 계열)
                            if in_kb:
                                st.warning("내부 지식 데이터가 부족합니다. 인터넷 검색으로 보완했습니다.")
                            else:
                                st.warning("내부 지식 데이터가 없습니다. 인터넷 검색을 시작하겠습니다.")
                        else:
                            # 내부 데이터만 사용된 경우
                            st.success("내부 지식 데이터를 찾았습니다.")
                        
                        st.write(answer)
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
            else:
                st.warning("질문을 입력해주세요.")

    # 브랜드 푸터
    st.markdown('<div class="brand-footer">', unsafe_allow_html=True)
    st.markdown('<p>© 2025 SHINHAN FINANCIAL GROUP. All Rights Reserved.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    branch_employee_main()
