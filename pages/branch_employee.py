import streamlit as st
import sys
import os

# utils 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

# dictionary 모듈 import
import dictionary
# simple_news_analysis 모듈 import
import simple_news_analysis

# 페이지 설정
st.set_page_config(
    page_title="SSCI (영업점용)",
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
            "menu2": "❓ Quick FAQ",
            "home": "🏠 홈으로 돌아가기",
        }
        
        selected_menu = st.selectbox(
            label="",  # 제목 숨김
            options=list(menu_options.keys()),
            format_func=lambda x: menu_options[x],
            key="menu_dropdown"
        )
        
        if selected_menu:
            if selected_menu == "home":
                # 홈으로 돌아가기
                st.switch_page("app.py")
            else:
                st.session_state.menu_selected = selected_menu
        else:
            # 빈 값이 선택되면 솔 캐릭터 화면으로 되돌아감
            st.session_state.menu_selected = None
        
        # 자주 묻는 질문을 사이드바에 표시
        if st.session_state.menu_selected == "menu2":
            st.caption("아래 자주 묻는 질문을 클릭하면 검색창에 자동으로 입력되고 검색이 실행됩니다.")
            top_questions = simple_news_analysis.get_top_questions(3)
            
            if top_questions:
                for i, q_data in enumerate(top_questions):
                    # 질문을 클릭하면 검색창에 자동 설정하고 검색까지 실행
                    if st.button(
                        f"Q{i+1}: {q_data['question'][:25]}{'...' if len(q_data['question']) > 25 else ''}",
                        key=f"faq_qa_btn_{i}",
                        help=f"(총 {q_data['count']}회 질문됨)",
                        use_container_width=True
                    ):
                        # 세션 상태에 질문 저장하여 검색창에 자동 설정하고 자동 검색 실행
                        st.session_state.auto_fill_qa_question = q_data['question']
                        st.session_state.auto_execute_search = True
                        st.rerun()
            else:
                st.info("아직 자주 묻는 질문이 없습니다.")
                st.caption("질문을 해보세요!")
        
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
            search_query = st.text_input("용어:", placeholder="예: 스테이블 코인, USDT...")
            
            if st.button("검색", type="secondary", use_container_width=True):
                if search_query:
                    # KB 포함 여부를 먼저 판단하여 사용자에게 즉시 안내 표시
                    with st.spinner("내부 지식 데이터 확인 중입니다..."):
                        try:
                            in_kb = dictionary.is_question_in_kb(search_query)
                        except Exception:
                            in_kb = True  # 문제가 생기면 기본적으로 KB 경로로 처리
                    
                    if in_kb:
                        st.success("내부 지식 데이터를 찾았습니다.")
                    if not in_kb:
                        st.warning("내부 지식 데이터가 없습니다. 인터넷 검색을 시작하겠습니다.")
                        
                    with st.spinner("답변을 생성하고 있습니다..."):
                        try:
                            answer = dictionary.get_dictionary_answer(search_query)
                            st.write(answer)
                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {str(e)}")
                else:
                    st.warning("질문을 입력해주세요.")
        
        elif st.session_state.menu_selected == "menu2":
            # Quick FAQ 인터페이스
            st.markdown("## Quick FAQ")
            st.markdown("스테이블코인과 관련된 질문을 하고 최신 뉴스를 바탕으로 답변을 받을 수 있습니다.")
            
            # 기존 기능 그대로 유지
            user_question = st.text_input(
                "질문:",
                placeholder="예: 최근 스테이블코인 도입 은행에 대해 알려주세요.",
                value=st.session_state.get("auto_fill_qa_question", ""),
                key="news_question"
            )
            
            if st.button("검색", key="news_search", use_container_width=True):
                if user_question:
                    with st.spinner("다양한 뉴스를 참고하여 답변을 생성하고 있습니다..."):
                        try:
                            answer = simple_news_analysis.get_news_answer(user_question)
                            st.write(answer)
                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {str(e)}")
                else:
                    st.warning("질문을 입력해주세요.")
            
            # 자동 검색 답변을 검색창 아래에 표시
            if st.session_state.get("auto_execute_search", False) and st.session_state.get("auto_fill_qa_question"):
                # 자동 검색 실행
                auto_question = st.session_state.auto_fill_qa_question
                with st.spinner("다양한 뉴스를 참고하여 답변을 생성하고 있습니다..."):
                    try:
                        answer = simple_news_analysis.get_news_answer(auto_question)
                        st.success("답변:")
                        st.write(answer)
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
                
                # 자동 검색 상태 초기화
                del st.session_state.auto_execute_search
            
            # 자동 채워진 질문 초기화 - 검색 후에도 내용이 유지되도록 수정
            # 사용자가 직접 입력을 지우거나 새로운 질문을 입력할 때만 초기화
            if "auto_fill_qa_question" in st.session_state and not user_question and not st.session_state.get("news_question", ""):
                del st.session_state.auto_fill_qa_question
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
                            <p>1. 왼쪽 사이드바에서 원하는 서비스를 선택하세요<br>2. 각 메뉴는 영업점 업무에 필요한 기능을 제공합니다<br>3. 용어 검색, Quick FAQ를 활용하세요</p>
                        </div>
                    </div>
                    """.format(""), unsafe_allow_html=True)

    # 브랜드 푸터
    st.markdown('<div class="brand-footer">', unsafe_allow_html=True)
    st.markdown('<p>© 2025 SHINHAN FINANCIAL GROUP. All Rights Reserved.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    branch_employee_main()
