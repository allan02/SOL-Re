# -*- coding: utf-8 -*-
import streamlit as st
import sys
import os
from datetime import datetime

# utils 디렉토리를 Python 경로에 추가
from utils import regulation_analysis, business_case_analysis

# 페이지 설정
st.set_page_config(
    page_title="SSCI (본부부서용)",
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
            "menu2": "📊 비즈니스 모니터링",
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
        
        # 솔 페이지 이미지 추가
        st.image("images/moli_page.jpg", use_container_width="always")
    
    with col3:
        # 메뉴 선택에 따른 콘텐츠 표시
        if 'menu_selected' not in st.session_state:
            st.session_state.menu_selected = None
            
        if st.session_state.menu_selected == "menu1":
            # 규제 분석 인터페이스 - regulation_analysis.py의 함수 호출
            st.markdown("## 규제 분석")
            st.markdown("국가별 스테이블코인 규제 현황을 분석하고 리스크를 예측할 수 있습니다.")
            
            regulation_analysis.show_country_regulation_analysis()
        
        elif st.session_state.menu_selected == "menu2":
            # Quick FAQ 인터페이스
            st.markdown("## 비즈니스 모니터링")
            st.markdown("주요 금융사의 스테이블코인 전략과 잠재적 리스크를 분석합니다.")
            
            business_case_analysis.show_business_case_analysis()
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
                            <p>1. 왼쪽 사이드바에서 원하는 서비스를 선택하세요<br>2. 각 메뉴는 본부부서 업무에 필요한 기능을 제공합니다<br>3. 규제 분석, 비즈니스 모니터링 기능을 활용하세요</p>
                        </div>
                    </div>
                    """.format(""), unsafe_allow_html=True)

    # 브랜드 푸터
    st.markdown('<div class="brand-footer">', unsafe_allow_html=True)
    st.markdown('<p>© 2025 SHINHAN FINANCIAL GROUP. All Rights Reserved.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    headquarters_employee_main()
