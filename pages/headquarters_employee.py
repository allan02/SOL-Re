import streamlit as st
from utils import regulation_analysis, business_case_analysis

def show_headquarters_employee_page():
    """
    본부부서 직원을 위한 페이지
    두 개의 탭으로 구성:
    1. 스테이블 코인 관련 국가별 규제 분석
    2. 메이저 금융사별 현황 분석 및 리스크 분석
    """
    st.title("🏢 본부부서 직원 서비스")
    st.markdown("전략적 의사결정을 위한 스테이블코인 분석 정보를 제공합니다.")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["🌍 규제 분석", "🏛️ 비즈니스 분석"])
    
    with tab1:
        st.header("🌍 스테이블코인 규제 분석")
        st.markdown("국가별 규제 동향과 우리나라에 미치는 영향을 분석합니다.")
        
        # 사용자 입력
        user_question = st.text_input(
            "규제 관련 질문을 입력하세요:",
            placeholder="예: 미국의 스테이블코인 규제 현황은?",
            key="regulation_question"
        )
        
        if st.button("🔍 규제 분석", key="regulation_search"):
            if user_question:
                with st.spinner("규제 정보를 분석하고 있습니다..."):
                    try:
                        answer = regulation_analysis.get_regulation_analysis(user_question)
                        st.success("분석 결과:")
                        st.write(answer)
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
            else:
                st.warning("질문을 입력해주세요.")
    
    with tab2:
        st.header("🏛️ 메이저 금융사 현황 분석")
        st.markdown("주요 금융사의 스테이블코인 전략과 잠재적 리스크를 분석합니다.")
        
        # 사용자 입력
        user_question = st.text_input(
            "비즈니스 분석 질문을 입력하세요:",
            placeholder="예: JP모건의 스테이블코인 전략은?",
            key="business_question"
        )
        
        if st.button("🔍 비즈니스 분석", key="business_search"):
            if user_question:
                with st.spinner("비즈니스 정보를 분석하고 있습니다..."):
                    try:
                        answer = business_case_analysis.get_business_analysis(user_question)
                        st.success("분석 결과:")
                        st.write(answer)
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
            else:
                st.warning("질문을 입력해주세요.")