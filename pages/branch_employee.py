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
    tab1, tab2 = st.tabs(["📚 용어 백과사전", "📰 뉴스 & QA"])
    
    with tab1:
        st.header("📚 스테이블코인 용어 백과사전")
        st.markdown("스테이블코인 관련 용어에 대해 질문하세요.")
        
        # 사용자 입력
        user_question = st.text_input(
            "질문을 입력하세요:",
            placeholder="예: 스테이블코인이란 무엇인가요?"
        )
        
        if st.button("🔍 검색", key="dictionary_search"):
            if user_question:
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
        st.header("📰 스테이블코인 뉴스 & QA")
        st.markdown("최신 스테이블코인 뉴스와 관련 질문에 답변합니다.")
        
        # 사용자 입력
        user_question = st.text_input(
            "뉴스 관련 질문을 입력하세요:",
            placeholder="예: 최근 스테이블코인 규제 동향은?",
            key="news_question"
        )
        
        if st.button("🔍 뉴스 검색", key="news_search"):
            if user_question:
                with st.spinner("뉴스를 검색하고 답변을 생성하고 있습니다..."):
                    try:
                        answer = simple_news_analysis.get_news_answer(user_question)
                        st.success("답변:")
                        st.write(answer)
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
            else:
                st.warning("질문을 입력해주세요.")