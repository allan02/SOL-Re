import streamlit as st
from pages import branch_employee, headquarters_employee

# 페이지 설정
st.set_page_config(
    page_title="신한금융그룹 스테이블코인 인텔리전스",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 메인 페이지
def main():
    st.title("🏦 신한금융그룹 스테이블코인 인텔리전스")
    st.markdown("---")
    
    # 사이드바에 페이지 선택 옵션 제공
    st.sidebar.title("📋 메뉴 선택")
    page = st.sidebar.selectbox(
        "직원 유형을 선택하세요:",
        ["🏢 본부부서 직원", "🏪 영업점 직원"]
    )
    
    # 선택된 페이지에 따라 해당 페이지 함수 호출
    if page == "🏪 영업점 직원":
        branch_employee.show_branch_employee_page()
    elif page == "🏢 본부부서 직원":
        headquarters_employee.show_headquarters_employee_page()

if __name__ == "__main__":
    main()
