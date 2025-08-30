import streamlit as st
from utils import dictionary, simple_news_analysis

def show_branch_employee_page():
    """
    영업점 직원을 위한 페이지
    두 개의 탭으로 구성:
    1. 스테이블 코인 용어 백과사전 RAG
    2. 스테이블 코인 관련 뉴스 조회 및 QA 서비스
    """
    st.title("🏪 영업점 직원 서비스")
    st.markdown("고객 상담에 필요한 스테이블코인 정보를 제공합니다.")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["📚 용어 백과사전", "📰 Q & A"])
    
    with tab1:
        st.header("📚 스테이블코인 용어 백과사전")
        st.markdown("스테이블코인 관련 용어에 대해 질문하세요.")
        
        # 사용자 입력
        user_question = st.text_input(
            "질문을 입력하세요:",
            placeholder="예: 스테이블코인"
        )
        
        if st.button("🔍 검색", key="dictionary_search"):
            if user_question:
                # KB 포함 여부를 먼저 판단하여 사용자에게 즉시 안내 표시
                try:
                    in_kb = dictionary.is_question_in_kb(user_question)
                except Exception:
                    in_kb = True  # 문제가 생기면 기본적으로 KB 경로로 처리
                
                if not in_kb:
                    st.info("웹 검색 중입니다...")
                
                with st.spinner("답변을 생성하고 있습니다..."):
                    try:
                        answer = dictionary.get_dictionary_answer(user_question)
                        st.success("답변:")
                        st.write(answer)
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
            else:
                st.warning("질문을 입력해주세요.")
    
    with tab2:
        st.header("📰 스테이블코인 Q & A")
        st.markdown("스테이블코인 관련 질문에 답변합니다.")
        
        # 2열 레이아웃으로 변경: 왼쪽에 기존 기능, 오른쪽에 자주 묻는 질문
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 기존 기능 그대로 유지
            user_question = st.text_input(
                "스테이블코인에 대한 질문을 입력하세요:",
                placeholder="예: 최근 스테이블코인 도입 은행에 대해 알려주세요.",
                value=st.session_state.get("auto_fill_qa_question", ""),
                key="news_question"
            )
            
            if st.button("🔍 검색", key="news_search"):
                if user_question:
                    with st.spinner("다양한 뉴스를 참고하여 답변을 생성하고 있습니다..."):
                        try:
                            answer = simple_news_analysis.get_news_answer(user_question)
                            st.success("답변:")
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
        
        with col2:
            # 오른쪽에 자주 묻는 질문 표시 - y축 위치를 Q&A 제목과 같은 높이로 맞춤
            st.subheader("❓ 자주 묻는 질문")
            top_questions = simple_news_analysis.get_top_questions(3)
            
            if top_questions:
                for i, q_data in enumerate(top_questions):
                    # 질문을 클릭하면 검색창에 자동 설정하고 검색까지 실행
                    if st.button(
                        f"Q{i+1}: {q_data['question'][:25]}{'...' if len(q_data['question']) > 25 else ''}",
                        key=f"faq_qa_btn_{i}",
                        help=f"클릭하면 검색창에 자동으로 설정되고 검색이 실행됩니다. (총 {q_data['count']}회 질문됨)",
                        use_container_width=True
                    ):
                        # 세션 상태에 질문 저장하여 검색창에 자동 설정하고 자동 검색 실행
                        st.session_state.auto_fill_qa_question = q_data['question']
                        st.session_state.auto_execute_search = True
                        st.rerun()
                
                # 질문 횟수 정보 표시
                st.markdown("---")
                st.caption("💡 위 질문을 클릭하면 검색창에 자동으로 입력되고 검색이 실행됩니다.")
            else:
                st.info("아직 자주 묻는 질문이 없습니다.")
                st.caption("질문을 해보세요!")
        
        # 자동 채워진 질문 초기화 - 검색 후에도 내용이 유지되도록 수정
        # 사용자가 직접 입력을 지우거나 새로운 질문을 입력할 때만 초기화
        if "auto_fill_qa_question" in st.session_state and not user_question and not st.session_state.get("news_question", ""):
            del st.session_state.auto_fill_qa_question