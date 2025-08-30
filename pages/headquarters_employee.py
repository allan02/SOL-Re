# -*- coding: utf-8 -*-
import streamlit as st
import sys
import os
from datetime import datetime

# utils 디렉토리를 Python 경로에 추가
from utils import business_case_analysis

# 페이지 설정
st.set_page_config(
    page_title="본부 직원 - 신한금융그룹 스테이블코인 인텔리전스",
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
        # 사이드바 메뉴 드롭다운
        menu_options = {
            "": "서비스를 선택하세요",
            "menu1": '📋 규제 분석',
            "menu2": "📊 비즈니스 모니터링"
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
        st.image("images/moli_page.jpg", use_container_width="always")
    
    with col3:
        # 메뉴 선택에 따른 콘텐츠 표시
        if 'menu_selected' not in st.session_state:
            st.session_state.menu_selected = None
            
        # 세션 상태 초기화
        if 'regulation_chat_history' not in st.session_state:
            st.session_state.regulation_chat_history = []
            
        if st.session_state.menu_selected == "menu1":
            # 규제 분석 인터페이스
            st.markdown("## 규제 분석")
            st.markdown("국가별 스테이블코인 규제 현황을 분석하고 리스크를 예측할 수 있습니다.")
                    
            # 주요 국가 리스트 (pycountry 사용)
            major_countries = [
                "United States", "European Union", "United Kingdom", "Japan", "South Korea", 
                "China", "Singapore", "Switzerland", "Canada", "Australia", "Brazil", "India"
            ]
            
            # 국가 선택과 분석 실행 버튼을 가로로 배치
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_countries = st.multiselect(
                    "분석할 국가를 선택하세요 (2-3개 권장):",
                    options=major_countries,
                    default=["United States", "South Korea"],
                    max_selections=3,
                    help="💡 최대 3개 국가까지 선택 가능합니다.\n주요 금융 중심지 국가들을 선택하면 더 유용한 비교 분석을 얻을 수 있습니다!"
                )
            
            with col2:
                st.write("")  # 세로 정렬을 위한 여백
                st.write("")  # 세로 정렬을 위한 여백
                analyze_button = st.button("분석 실행", key="country_comparison", type="secondary")
            
            # 분석 실행 버튼 클릭 시 처리
            if analyze_button:
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
                            
                        except Exception as e:
                            error_msg = f"국가별 규제 비교 분석 중 오류가 발생했습니다: {str(e)}"
                            st.error(error_msg)
        
        elif st.session_state.menu_selected == "menu2":
            # Quick FAQ 인터페이스
            st.markdown("## 비즈니스 모니터링")
            st.markdown("주요 금융사의 스테이블코인 전략과 잠재적 리스크를 분석합니다.")
            
            business_case_analysis.show_business_case_analysis()

    # 브랜드 푸터
    st.markdown('<div class="brand-footer">', unsafe_allow_html=True)
    st.markdown('<p>© 2024 SHINHAN FINANCIAL GROUP. All Rights Reserved.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    headquarters_employee_main()
