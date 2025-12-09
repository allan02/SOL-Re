# -*- coding: utf-8 -*-
import streamlit as st
import sys
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# utils 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

# realty_search 모듈 import
import realty_search

# 페이지 설정
st.set_page_config(
    page_title="MOLI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 메인 페이지
def headquarters_employee_main():
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
        # 자주 검색하는 질문 표시 (예전 스테이블코인 방식)
        try:
            if hasattr(realty_search, 'get_top_questions'):
                top_questions = realty_search.get_top_questions(top_k=5)
                if top_questions:
                    st.caption("아래 자주 검색하는 질문을 클릭하면 검색창에 자동으로 입력되고 검색이 실행됩니다.")
                    for i, q_data in enumerate(top_questions):
                        question = q_data.get('question', '')
                        count = q_data.get('count', 1)
                        last_date = q_data.get('last_date', '')
                        price_summary = q_data.get('price_summary', '')
                        
                        # 질문이 너무 길면 줄임
                        display_question = question[:25] + "..." if len(question) > 25 else question
                        
                        # 컨테이너로 감싸서 표시
                        with st.container():
                            # 버튼 텍스트 구성 (Q, 질문)
                            button_text = f"Q{i+1}: {display_question}"
                            
                            # 버튼으로 표시 (클릭하면 검색창에 자동 입력 및 검색 실행)
                            if st.button(
                                button_text,
                                key=f"faq_qa_btn_{i}",
                                help=f"(총 {count}회 검색됨)",
                                use_container_width=True
                            ):
                                # 세션 상태에 질문 저장하여 검색창에 자동 설정하고 자동 검색 실행
                                st.session_state.auto_search_query = question
                                st.session_state.auto_search_execute = True
                                st.rerun()
                            
                            # 답변과 날짜를 버튼 아래에 작게 표시
                            if price_summary or last_date:
                                info_text = ""
                                if price_summary:
                                    info_text += f"A{i+1}: {price_summary}"
                                if last_date:
                                    if info_text:
                                        info_text += f"  •  {last_date}"
                                    else:
                                        info_text = last_date
                                st.caption(info_text)
            elif hasattr(realty_search, 'get_recent_searches'):
                # 하위 호환성
                recent_searches = realty_search.get_recent_searches(5)
                if recent_searches:
                    st.caption("아래 자주 검색하는 질문을 클릭하면 검색창에 자동으로 입력되고 검색이 실행됩니다.")
                    for i, search in enumerate(recent_searches):
                        question = search.get("question", "")
                        count = search.get("count", 1)
                        last_date = search.get("last_date", "")
                        price_summary = search.get("price_summary", "")
                        
                        if question:
                            display_question = question[:25] + "..." if len(question) > 25 else question
                            
                            # 컨테이너로 감싸서 표시
                            with st.container():
                                # 버튼 텍스트 구성 (Q, 질문)
                                button_text = f"Q{i+1}: {display_question}"
                                
                                if st.button(
                                    button_text,
                                    key=f"faq_qa_btn_{i}",
                                    help=f"(총 {count}회 검색됨)",
                                    use_container_width=True
                                ):
                                    st.session_state.auto_search_query = question
                                    st.session_state.auto_search_execute = True
                                    st.rerun()
                                
                                # 답변과 날짜를 버튼 아래에 작게 표시
                                if price_summary or last_date:
                                    info_text = ""
                                    if price_summary:
                                        info_text += f"A{i+1}: {price_summary}"
                                    if last_date:
                                        if info_text:
                                            info_text += f"  •  {last_date}"
                                        else:
                                            info_text = last_date
                                    st.caption(info_text)
        except Exception as e:
            # 에러 발생 시 무시하고 계속 진행
            pass
        
        # 몰리 페이지 이미지 추가
        st.image("images/moli_page.jpg", use_container_width="always")
    
    with col3:
        # 부동산 매물 검색 인터페이스
        st.markdown("## 부동산 매물 검색")
        st.markdown("부동산 매물 관련 다양한 질문 검색 가능합니다.")
        
        # 검색 입력 (자동 입력 지원)
        auto_query = st.session_state.get("auto_search_query", "")
        if auto_query:
            search_query = st.text_input("", value=auto_query, placeholder="답십리 래미안 위브 전용 84 매매 매물 가격 알려줘")
        else:
            search_query = st.text_input("", placeholder="답십리 래미안 위브 전용 84 매매 매물 가격 알려줘")
        
        # 검색 실행 (자동 또는 수동)
        should_search = False
        if st.session_state.get("auto_search_execute", False):
            should_search = True
            del st.session_state.auto_search_execute
        elif st.button("검색", type="secondary", use_container_width=True, key="main_search_btn"):
            should_search = True
        
        if should_search:
            if search_query:
                with st.spinner("네이버 부동산에서 매물 정보를 검색하고 있습니다..."):
                    try:
                        # 부동산 매물 검색
                        answer, used_web_search = realty_search.get_realty_search_answer(search_query)
                        
                        # 메시지 표시 (항상 웹 검색 사용)
                        st.warning("네이버 부동산에서 매물 정보를 검색했습니다.")
                        
                        st.write(answer)
                        
                        # 자동 검색 상태 초기화
                        if "auto_search_query" in st.session_state:
                            del st.session_state.auto_search_query
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
            else:
                st.warning("질문을 입력해주세요.")

    # 브랜드 푸터
    st.markdown('<div class="brand-footer">', unsafe_allow_html=True)
    st.markdown('<p>© 2025 SHINHAN FINANCIAL GROUP. All Rights Reserved.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    headquarters_employee_main()
