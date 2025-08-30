import streamlit as st
import sys
import os

# utils 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

# dictionary 모듈 import
from dictionary import get_dictionary_answer, get_similar_terms, search_terms_by_category, get_all_categories
# simple_news_analysis 모듈 import
from simple_news_analysis import get_news_answer, get_top_questions

# 페이지 설정
st.set_page_config(
    page_title="영업점 직원 - 신한금융그룹 스테이블코인 인텔리전스",
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
        # 사이드바 메뉴 드롭다운
        menu_options = {
            "": "서비스를 선택하세요",
            "menu1": "🔍 용어 검색",
            "menu2": "❓ Quick FAQ"
        }
        
        selected_menu = st.selectbox(
            label="",  # 제목 숨김
            options=list(menu_options.keys()),
            format_func=lambda x: menu_options[x],
            key="menu_dropdown"
        )
        
        if selected_menu:
            st.session_state.menu_selected = selected_menu
        else:
            # 빈 값이 선택되면 솔 캐릭터 화면으로 되돌아감
            st.session_state.menu_selected = None
            st.success(f"현재 위치: 서비스 홈")
        
        # 솔 페이지 이미지 추가
        st.image("images/sol_page.png", use_container_width="always")
    
    with col3:
        # 메뉴 선택에 따른 콘텐츠 표시
        if 'menu_selected' not in st.session_state:
            st.session_state.menu_selected = None
            
        if st.session_state.menu_selected == "menu1":
            # 스테이블코인 용어 검색 인터페이스
            st.markdown("## 용어 검색")
            st.markdown("스테이블코인과 관련된 용어를 검색하고 자세한 설명을 확인할 수 있습니다.")
            
            # 검색 입력
            search_query = st.text_input("검색할 용어를 입력하세요:", placeholder="예: USDT, 블록체인...")
            
            if search_query:
                if st.button("검색", type="primary"):
                    with st.spinner("검색 중..."):
                        # dictionary.py의 get_dictionary_answer 함수 사용
                        answer = get_dictionary_answer(search_query)
                        st.markdown("### 검색 결과")
                        st.write(answer)
                        
                        # 유사한 용어도 함께 표시
                        similar_terms = get_similar_terms(search_query, top_k=3)
                        if similar_terms:
                            st.markdown("### 관련 용어")
                            for term_data in similar_terms:
                                with st.expander(f"{term_data['term']}"):
                                    st.write(term_data['content'])
        
        elif st.session_state.menu_selected == "menu2":
            # Quick FAQ 인터페이스
            st.markdown("## Quick FAQ")
            st.markdown("스테이블코인과 관련된 질문을 하고 최신 뉴스를 바탕으로 답변을 받을 수 있습니다.")
            
            # 자주 묻는 질문 표시
            top_questions = get_top_questions(top_k=3)
            if top_questions:
                st.markdown("### 자주 묻는 질문")
                for q_data in top_questions:
                    if st.button(f"Q: {q_data['question']} (조회수: {q_data['count']})", key=f"faq_{q_data['question']}"):
                        with st.spinner("답변 생성 중..."):
                            answer = get_news_answer(q_data['question'])
                            st.markdown("### 답변")
                            st.write(answer)
            
            # 새로운 질문 입력
            st.markdown("### 새로운 질문하기")
            faq_query = st.text_input("질문을 입력하세요:", placeholder="예: 스테이블코인 규제 현황은?")
            
            if faq_query:
                if st.button("질문하기", type="primary"):
                    with st.spinner("답변 생성 중..."):
                        # simple_news_analysis.py의 get_news_answer 함수 사용
                        answer = get_news_answer(faq_query)
                        st.markdown("### 답변")
                        st.write(answer)
        else:
            # 기본 이미지 표시
            col_left, col_center, col_right = st.columns([1, 2, 1])
            with col_center:
                # 컨테이너를 사용하여 세로 중앙 정렬
                container = st.container()
                with container:
                    # 이미지와 텍스트를 세로 중앙에 배치
                    st.markdown("""
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 250px;">
                        <div style="text-align: center;">
                            <p>1. 왼쪽 사이드바에서 원하는 메뉴를 선택하세요<br>2. 각 메뉴는 영업점 업무에 필요한 기능을 제공합니다<br>3. 용어 검색, Quick FAQ를 활용하세요</p>
                        </div>
                    </div>
                    """.format(""), unsafe_allow_html=True)

    # 브랜드 푸터
    st.markdown('<div class="brand-footer">', unsafe_allow_html=True)
    st.markdown('<p>© 2024 SHINHAN FINANCIAL GROUP. All Rights Reserved.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    branch_employee_main()
