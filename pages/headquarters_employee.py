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
        
        # 대화 기록 초기화
        if "regulation_chat_history" not in st.session_state:
            st.session_state.regulation_chat_history = []
        
        # 국가별 스테이블코인 규제 비교 분석 (expander 사용)
        with st.expander("🌍 국가별 스테이블코인 규제 비교 분석", expanded=False):
            st.markdown("2-3개 국가를 선택하여 스테이블코인 규제를 웹검색하고 비교 분석합니다.")
            
            # 국가 선택 (라이브러리 사용)
            import pycountry
            
            # 주요 국가 리스트 (pycountry 사용)
            major_countries = [
                "United States", "European Union", "United Kingdom", "Japan", "South Korea", 
                "China", "Singapore", "Switzerland", "Canada", "Australia", "Brazil", "India"
            ]
            
            # 국가 선택
            selected_countries = st.multiselect(
                "분석할 국가를 선택하세요 (2-3개 권장):",
                options=major_countries,
                default=["United States", "European Union", "Japan"],
                max_selections=3,
                help="최대 3개 국가까지 선택 가능합니다."
            )
            
            # 팁 문구
            st.markdown("💡 **팁**: 주요 금융 중심지 국가들을 선택하면 더 유용한 비교 분석을 얻을 수 있습니다!")
            
            # 분석 실행 버튼
            if st.button("🔍 국가별 규제 비교 분석 실행", key="country_comparison", type="primary"):
                if len(selected_countries) < 2:
                    st.error("⚠️ 최소 2개 국가를 선택해주세요.")
                elif len(selected_countries) > 3:
                    st.error("⚠️ 최대 3개 국가까지만 선택 가능합니다.")
                else:
                    # 국가별 규제 비교 분석 실행
                    with st.spinner(f"{', '.join(selected_countries)}의 스테이블코인 규제를 검색하고 비교 분석하고 있습니다..."):
                        try:
                            # regulation_analysis.py의 새로운 함수 호출
                            from utils.regulation_analysis import get_country_regulation_comparison
                            comparison_result = get_country_regulation_comparison(selected_countries)
                            
                            # 비교 분석 결과를 대화 기록에 추가
                            st.session_state.regulation_chat_history.append({
                                "role": "user", 
                                "content": f"{', '.join(selected_countries)}의 스테이블코인 규제를 비교 분석해주세요"
                            })
                            st.session_state.regulation_chat_history.append({
                                "role": "assistant", 
                                "content": comparison_result
                            })
                            
                            st.rerun()
                            
                        except Exception as e:
                            error_msg = f"국가별 규제 비교 분석 중 오류가 발생했습니다: {str(e)}"
                            st.error(error_msg)
        
        # 채팅 UI
        chat_container = st.container()
        
        with chat_container:
            # 기존 대화 기록 표시
            for message in st.session_state.regulation_chat_history:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
        
        # 새로운 질문 입력
        if prompt := st.chat_input("규제 관련 질문을 입력하세요 (예: 미국의 스테이블코인 규제 현황은?)"):
            # 사용자 메시지 추가
            st.session_state.regulation_chat_history.append({"role": "user", "content": prompt})
            
            # AI 답변 생성
            with st.chat_message("assistant"):
                with st.spinner("규제 정보를 분석하고 있습니다..."):
                    try:
                        answer = regulation_analysis.get_regulation_analysis(prompt)
                        st.write(answer)
                        
                        # AI 답변을 대화 기록에 추가
                        st.session_state.regulation_chat_history.append({"role": "assistant", "content": answer})
                        
                    except Exception as e:
                        error_msg = f"오류가 발생했습니다: {str(e)}"
                        st.error(error_msg)
                        st.session_state.regulation_chat_history.append({"role": "assistant", "content": error_msg})
            
            # 페이지 새로고침으로 대화 업데이트
            st.rerun()
        
        # 대화 초기화 버튼
        if st.button("🗑️ 대화 초기화", key="regulation_clear"):
            st.session_state.regulation_chat_history = []
            st.rerun()
    
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