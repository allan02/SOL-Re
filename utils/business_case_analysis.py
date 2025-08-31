import streamlit as st
import requests
import os
import pandas as pd
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    try:
        from langgraph.graph import Graph as StateGraph
        from langgraph.graph import END
    except ImportError:
        from langgraph import StateGraph, END
from typing import TypedDict, List, Dict, Any

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

excel_path = os.path.join(os.path.dirname(__file__), 'stablecoin_financial_institutions_with_roles_kor_renamed.xlsx')

@st.cache_data
def load_institutions_dataframe(path):
    return pd.read_excel(path, engine="openpyxl")

# State definition for LangGraph
class AnalysisState(TypedDict):
    company_name: str
    news_items: List[Dict[str, Any]]
    filtered_items: List[Dict[str, Any]]
    grouped_items: Dict[str, List[Dict[str, Any]]]
    group_analyses: Dict[str, str]
    issue_scores: Dict[str, int]
    current_step: str
    progress: int

def show_business_case_analysis():
    try:
        df = load_institutions_dataframe(excel_path)
        
        continent_col = "대륙"
        country_col = "국가"
        company_col = "회사"

        df = df[[continent_col, country_col, company_col]].dropna(how="all")
        df[continent_col] = df[continent_col].astype(str).str.strip()
        df[country_col] = df[country_col].astype(str).str.strip()
        df[company_col] = df[company_col].astype(str).str.strip()

        all_label = "선택 안 함"

        continents = [all_label] + sorted(df[continent_col].dropna().unique().tolist())
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_continent = st.selectbox("대륙", options=continents, index=0)

        filtered_by_continent = df if selected_continent == all_label else df[df[continent_col] == selected_continent]

        countries = [all_label] + sorted(filtered_by_continent[country_col].dropna().unique().tolist())
        with col2:
            selected_country = st.selectbox("국가", options=countries, index=0)

        filtered_by_country = (
            filtered_by_continent
            if selected_country == all_label
            else filtered_by_continent[filtered_by_continent[country_col] == selected_country]
        )

        companies = [all_label] + sorted(filtered_by_country[company_col].dropna().unique().tolist())
        with col3:
            selected_company = st.selectbox("금융사", options=companies, index=0)
        
        # 검색 버튼을 토글 목록 밑에 최대 폭으로 배치
        role_search_clicked = st.button("검색", key="role_search", use_container_width=True)
            
    except Exception as e:
        st.error(f"엑셀 파일을 불러오는 중 오류가 발생했습니다: {e}")

    # 역할 리스트 (스테이블 코인 시장 내 주요 역할)
    roles = [
        "발행",
        "준비금",
        "준비금 관리",
        "수탁",
        "결제",
        "결제 처리",
        "지갑",
        "거래소",
        "인프라",
        "블록체인",
        "온램프",
        "오프램프",
        "유동성",
        "유동성 공급",
        "리스크",
        "리스크 관리",
    ]

    def is_within_last_month(pub_date_str):
        try:
            dt = parsedate_to_datetime(pub_date_str)
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)
            return dt >= cutoff
        except Exception:
            return False

    def fetch_news_items(query_text):
        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            "X-Naver-Client-Id": "6nEOF04VFKYHVsqhgQ2I",
            "X-Naver-Client-Secret": "8_mjbLcEOy",
            "Content-Type": "plain/text"
        }
        params = {"query": query_text.strip(), "display": 5, "start": 1, "sort": "date"}
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception:
            return []

    # LangGraph 노드 함수들
    def fetch_news_node(state: AnalysisState) -> AnalysisState:
        """뉴스 검색 노드"""
        company_name = state["company_name"]
        merged_items = []
        seen_links = set()
        
        # 진행 상황 업데이트
        state["current_step"] = f"뉴스 검색 중... ({company_name})"
        state["progress"] = 5
        
        for i, role in enumerate(roles):
            # 각 역할별 검색 진행 상황 표시
            progress_per_role = 5 + (i / len(roles)) * 20
            state["progress"] = int(progress_per_role)
            state["current_step"] = f"뉴스 검색 중... {role} ({i+1}/{len(roles)})"
            
            query_text = f"{company_name} 스테이블 코인 {role}"
            items = fetch_news_items(query_text)
            for item in items:
                link = item.get("link")
                pub_date = item.get("pubDate")
                if link and link not in seen_links and pub_date and is_within_last_month(pub_date):
                    merged_items.append(item)
                    seen_links.add(link)
        
        # 최신순 정렬
        try:
            merged_items.sort(
                key=lambda x: parsedate_to_datetime(x.get("pubDate")) if x.get("pubDate") else datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
        except Exception:
            pass
        
        state["news_items"] = merged_items
        state["current_step"] = f"뉴스 검색 완료 - {len(merged_items)}건 발견"
        state["progress"] = 25
        return state

    def filter_relevance_node(state: AnalysisState) -> AnalysisState:
        """LLM 기반 관련성 필터링 노드"""
        company_name = state["company_name"]
        items = state["news_items"]
        
        # 진행 상황 업데이트
        state["current_step"] = f"관련성 필터링 시작 - {len(items)}건 분석 예정"
        state["progress"] = 25
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.warning("OPENAI_API_KEY가 설정되어 있지 않아 LLM 필터를 건너뜁니다.")
            state["filtered_items"] = items
            state["current_step"] = "LLM 필터링 건너뜀 - API 키 없음"
            state["progress"] = 50
            return state
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "너는 뉴스 기사와 회사명 간의 직접 관련성을 판단하는 필터다. \n"
                            "직접적으로 해당 회사의 스테이블 코인 활동(발행, 준비금, 결제, 지갑, 거래소, 인프라 등)과 관련된 기사만 'YES'로 응답하고, 그렇지 않으면 'NO'로 응답한다. \n"
                            "광범위한 업계 동향, 타사 중심 기사, 단순 언급은 'NO'로 분류한다. \n"
                            "반드시 대문자 YES 또는 NO 중 하나만 출력한다."),
                ("human", "회사: {company}\n제목: {title}\n내용: {description}")
            ])
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            chain = prompt | llm | StrOutputParser()
            
            filtered = []
            for i, item in enumerate(items):
                # 각 기사별 진행 상황 표시
                progress_per_item = 25 + (i / len(items)) * 25
                state["progress"] = int(progress_per_item)
                state["current_step"] = f"관련성 필터링 중... ({i+1}/{len(items)})"
                
                title = item.get("title", "")
                description = item.get("description", "")
                try:
                    verdict = chain.invoke({
                        "company": company_name,
                        "title": title,
                        "description": description,
                    }).strip().upper()
                except Exception:
                    verdict = "NO"
                if verdict == "YES":
                    filtered.append(item)
            
            state["filtered_items"] = filtered
            state["current_step"] = f"LLM 필터링 완료 - {len(filtered)}건 필터링됨"
            state["progress"] = 50
        except Exception:
            state["filtered_items"] = items
            state["current_step"] = "LLM 필터링 실패 - 오류 발생"
            state["progress"] = 50
        
        return state

    def group_issues_node(state: AnalysisState) -> AnalysisState:
        """LLM 기반 이슈 그루핑 노드"""
        company_name = state["company_name"]
        items = state["filtered_items"]
        
        # 진행 상황 업데이트
        state["current_step"] = f"이슈 그루핑 시작 - {len(items)}건 분류 예정"
        state["progress"] = 50
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            state["grouped_items"] = {"기타": items}
            state["current_step"] = "이슈 그루핑 건너뜀 - API 키 없음"
            state["progress"] = 75
            return state
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "너는 스테이블 코인 관련 기사들을 이슈(토픽)로 라벨링하는 분류기다.\n"
                 "다음 원칙을 따르라:\n"
                 "- 반드시 한 줄로 간결한 한국어 라벨만 출력한다 (예: '준비금 규제', '해외 결제 파트너십', '거래소 상장', '지갑 서비스 출시').\n"
                 "- 같은 이슈는 동일한 라벨을 사용해 일관성 있게 분류한다.\n"
                 "- 회사의 스테이블 코인 활동 맥락을 반영한다.\n"
                 "- 라벨 외 다른 텍스트는 출력하지 않는다."),
                ("human", "회사: {company}\n제목: {title}\n내용: {description}")
            ])
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            chain = prompt | llm | StrOutputParser()
            
            groups = {}
            for i, item in enumerate(items):
                # 각 기사별 진행 상황 표시
                progress_per_item = 50 + (i / len(items)) * 25
                state["progress"] = int(progress_per_item)
                state["current_step"] = f"이슈 그루핑 중... ({i+1}/{len(items)})"
                
                title = item.get("title", "")
                description = item.get("description", "")
                try:
                    label = chain.invoke({
                        "company": company_name,
                        "title": title,
                        "description": description,
                    }).strip()
                    if not label:
                        label = "기타"
                except Exception:
                    label = "기타"
                item["_group"] = label
                groups.setdefault(label, []).append(item)
            
            # 큰 그룹 우선으로 정렬된 dict 생성
            sorted_labels = sorted(groups.keys(), key=lambda k: len(groups[k]), reverse=True)
            state["grouped_items"] = {label: groups[label] for label in sorted_labels}
            state["current_step"] = f"이슈 그루핑 완료 - {len(groups)}개 그룹 생성"
            state["progress"] = 75
        except Exception:
            state["grouped_items"] = {"기타": items}
            state["current_step"] = "이슈 그루핑 실패 - 오류 발생"
            state["progress"] = 75
        
        return state

    def analyze_groups_node(state: AnalysisState) -> AnalysisState:
        """그룹별 통합 분석 노드"""
        company_name = state["company_name"]
        grouped_items = state["grouped_items"]
        
        # 진행 상황 업데이트
        state["current_step"] = f"그룹 분석 시작 - {len(grouped_items)}개 그룹 분석 예정"
        state["progress"] = 75
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            group_analyses = {}
            for label, items_in_group in grouped_items.items():
                group_analyses[label] = f"{label} 관련 기사 {len(items_in_group)}건 요약 제공 (API Key 없음으로 간단 표시)."
            state["group_analyses"] = group_analyses
            state["current_step"] = "그룹 분석 건너뜀 - API 키 없음"
            state["progress"] = 90
            return state
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                    "너는 스테이블 코인 관련 뉴스 기사들을 분석하여 신한금융그룹 입장에서의 종합적인 인사이트를 제공하는 전문가다. \n"
                    "다음 세 가지를 하나의 응답으로 작성해라: \n\n"
                    "**이슈 요약** (200자 이내)\n"
                    "1. 핵심 이슈: 무엇이 일어났는지\n"
                    "2. 주요 참여자: 누가 관련되어 있는지\n"
                    "3. 시장 영향: 이 이슈가 스테이블 코인 시장에 미치는 영향\n"
                    "4. 향후 전망: 앞으로 어떻게 될 것으로 예상되는지\n\n"
                    "**신한금융그룹 입장에서의 영향도 판단**\n"
                    "이 뉴스 이슈가 신한금융그룹에게 미치는 영향을 다음 중 하나로 판단:\n"
                    "- 매우 부정적: 신한금융그룹의 사업에 심각한 위협이나 손실을 가져올 수 있는 이슈\n"
                    "- 부정적: 신한금융그룹의 사업에 부정적 영향을 미칠 수 있는 이슈\n"
                    "- 중립: 신한금융그룹의 사업에 직접적인 영향이 미미하거나 불분명한 이슈\n"
                    "- 긍정적: 신한금융그룹의 사업에 긍정적 기회를 제공할 수 있는 이슈\n"
                    "- 매우 긍정적: 신한금융그룹의 사업에 큰 성장 기회나 이익을 가져올 수 있는 이슈\n\n"
                    "**신한금융그룹이 얻을 수 있는 구체적인 인사이트** (400자 이내)\n"
                    "1. 경쟁사 분석: 경쟁사들의 구체적인 움직임, 전략, 시장 포지셔닝\n"
                    "2. 위험 요소: 주의해야 할 구체적인 리스크, 규제 변화, 시장 불확실성\n"
                    "3. 시장 포지셔닝: 신한금융그룹이 차별화할 수 있는 영역과 핵심 역량\n\n"
                    "**추천 조사 질의** (최대 2개)\n"
                    "해당 뉴스 기사들의 어떠한 문구을 고려했을 떄, 신한금융그룹 입장에서 추가적으로 조사가 필요한 주제로 질문을 만들어라."
                    "질의는 완성된 한 개의 문장 형식으로 만들어라."
                    "질의는 구체적일 수록 좋다."
                    "각 섹션은 명확하게 구분하고, 신한금융그룹의 비즈니스 관점에서 실용적이고 실행 가능한 인사이트를 제공해라."),
                ("human",
                 "회사: {company}\n이슈 라벨: {label}\n기사 제목들: {titles}\n기사 요약들: {descriptions}\n위 내용을 종합 분석:")
            ])
            llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
            chain = prompt | llm | StrOutputParser()
            
            group_analyses = {}
            for i, (label, items_in_group) in enumerate(grouped_items.items()):
                # 각 그룹별 진행 상황 표시
                progress_per_group = 75 + (i / len(grouped_items)) * 15
                state["progress"] = int(progress_per_group)
                state["current_step"] = f"그룹 분석 중... {label} ({i+1}/{len(grouped_items)})"
                
                titles = " | ".join([(i.get("title") or "") for i in items_in_group])
                descriptions = " | ".join([(i.get("description") or "") for i in items_in_group])
                try:
                    analysis = chain.invoke({
                        "company": company_name,
                        "label": label,
                        "titles": titles,
                        "descriptions": descriptions,
                    }).strip()
                    group_analyses[label] = analysis
                except Exception:
                    group_analyses[label] = f"{label} 관련 기사 {len(items_in_group)}건."
            
            state["group_analyses"] = group_analyses
            state["current_step"] = f"그룹 분석 완료 - {len(group_analyses)}개 그룹 분석 완료"
            state["progress"] = 90
        except Exception:
            group_analyses = {}
            for label, items_in_group in grouped_items.items():
                group_analyses[label] = f"{label} 관련 기사 {len(items_in_group)}건."
            state["group_analyses"] = group_analyses
            state["current_step"] = "그룹 분석 실패 - 오류 발생"
            state["progress"] = 90
        
        return state

    def score_importance_node(state: AnalysisState) -> AnalysisState:
        """이슈 중요도 점수화 노드"""
        grouped_items = state["grouped_items"]
        
        # 진행 상황 업데이트
        state["current_step"] = f"중요도 점수화 시작 - {len(grouped_items)}개 그룹 평가 예정"
        state["progress"] = 90
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            issue_scores = {}
            for label, items_in_group in grouped_items.items():
                article_count = len(items_in_group)
                total_length = sum(len((i.get("title") or "")) + len((i.get("description") or "")) for i in items_in_group)
                heuristic_score = min(100, (article_count * 10) + (total_length // 100))
                issue_scores[label] = heuristic_score
            state["issue_scores"] = issue_scores
            state["current_step"] = "중요도 점수화 완료 - API 키 없음으로 휴리스틱 점수 사용"
            state["progress"] = 100
            return state
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "너는 스테이블 코인 이슈의 중요도를 0~100점으로 평가하는 심사위원이다.\n"
                 "평가 기준:\n"
                 "1) 최신 기사 및 정보일수록 (정보의 최신성)\n"
                 "2) 이슈에 포함된 기사 수가 많을수록 더 중요 (기사 수 비례)\n"
                 "3) 신한금융그룹에 미치는 영향이 클수록 더 중요 (직접 영향도)\n"
                 "4) 신한금융그룹이 벤치마킹할 여지가 많을수록 더 중요 (학습/적용 가능성)\n"
                 "5) 기사들의 총 길이가 길수록 더 중요 (정보량)\n"
                 "반드시 0~100 사이의 정수 하나만 출력한다. 다른 문자는 출력하지 마라."),
                ("human",
                 "이슈 라벨: {label}\n"
                 "기사 수: {article_count}\n"
                 "기사 제목들: {titles}\n"
                 "기사 요약들: {descriptions}\n"
                 "총 기사 길이(문자수): {total_length}\n"
                 "위 기준에 따라 이 이슈의 중요도를 0~100 정수로만 출력:")
            ])
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            chain = prompt | llm | StrOutputParser()
            
            issue_scores = {}
            for i, (label, items_in_group) in enumerate(grouped_items.items()):
                # 각 그룹별 진행 상황 표시
                progress_per_group = 90 + (i / len(grouped_items)) * 10
                state["progress"] = int(progress_per_group)
                state["current_step"] = f"중요도 점수화 중... {label} ({i+1}/{len(grouped_items)})"
                
                titles = " | ".join([(i.get("title") or "") for i in items_in_group])
                descriptions = " | ".join([(i.get("description") or "") for i in items_in_group])
                article_count = len(items_in_group)
                total_length = sum(len((i.get("title") or "")) + len((i.get("description") or "")) for i in items_in_group)
                try:
                    out = chain.invoke({
                        "label": label,
                        "article_count": str(article_count),
                        "titles": titles,
                        "descriptions": descriptions,
                        "total_length": str(total_length),
                    }).strip()
                    # 정수 파싱
                    score_val = int(''.join([c for c in out if c.isdigit()]) or 0)
                    score_val = max(0, min(score_val, 100))
                    issue_scores[label] = score_val
                except Exception:
                    heuristic_score = min(100, (article_count * 10) + (total_length // 100))
                    issue_scores[label] = heuristic_score
            
            state["issue_scores"] = issue_scores
            state["current_step"] = f"중요도 점수화 완료 - {len(issue_scores)}개 그룹 평가 완료"
            state["progress"] = 100
        except Exception:
            issue_scores = {}
            for label, items_in_group in grouped_items.items():
                article_count = len(items_in_group)
                total_length = sum(len((i.get("title") or "")) + len((i.get("description") or "")) for i in items_in_group)
                heuristic_score = min(100, (article_count * 10) + (total_length // 100))
                issue_scores[label] = heuristic_score
            state["issue_scores"] = issue_scores
            state["current_step"] = "중요도 점수화 실패 - 오류 발생으로 휴리스틱 점수 사용"
            state["progress"] = 100
        
        return state

    # LangGraph 구성
    def create_analysis_graph():
        """분석을 위한 LangGraph 생성"""
        workflow = StateGraph(AnalysisState)
        
        # 노드 추가
        workflow.add_node("fetch_news", fetch_news_node)
        workflow.add_node("filter_relevance", filter_relevance_node)
        workflow.add_node("group_issues", group_issues_node)
        workflow.add_node("analyze_groups", analyze_groups_node)
        workflow.add_node("score_importance", score_importance_node)
        
        # 엣지 연결
        workflow.set_entry_point("fetch_news")
        workflow.add_edge("fetch_news", "filter_relevance")
        workflow.add_edge("filter_relevance", "group_issues")
        workflow.add_edge("group_issues", "analyze_groups")
        workflow.add_edge("analyze_groups", "score_importance")
        workflow.add_edge("score_importance", END)
        
        return workflow.compile()

    # 실시간 진행 상황을 표시하는 함수
    def show_progress_bar(current_step, progress):
        """현재 진행 상황을 프로그레스 바로 표시"""
        st.progress(progress / 100)
        st.info(f"🔄 현재 처리 중: {current_step}")
        
    def show_step_details(step_name, details=""):
        """각 단계별 상세 정보 표시"""
        with st.expander(f"📋 {step_name} 상세 정보", expanded=True):
            if details:
                st.write(details)
            else:
                st.write("처리 중...")

    # 선택된 회사명 기준 역할별 검색 및 병합
    try:
        if role_search_clicked:
            if not selected_company or selected_company == "선택 안 함":
                st.warning("금융사를 선택해주세요.")
            else:
                # 진행 상황을 표시할 컨테이너 생성
                progress_container = st.container()
                
                with progress_container:
                    st.markdown("**분석 진행 상황**")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                # 초기 상태 설정
                initial_state = AnalysisState(
                    company_name=selected_company,
                    news_items=[],
                    filtered_items=[],
                    grouped_items={},
                    group_analyses={},
                    issue_scores={},
                    current_step="시작",
                    progress=0
                )
                
                # LangGraph 실행 (실시간 진행 상황 표시)
                graph = create_analysis_graph()
                
                # 각 노드 실행 후 진행 상황 업데이트
                current_state = initial_state
                
                # 1단계: 뉴스 검색
                current_state = fetch_news_node(current_state)
                with progress_container:
                    progress_bar.progress(current_state["progress"] / 100)
                    status_text.info(f"{current_state['current_step']}")
                
                # 2단계: 관련성 필터링
                current_state = filter_relevance_node(current_state)
                with progress_container:
                    progress_bar.progress(current_state["progress"] / 100)
                    status_text.info(f"{current_state['current_step']}")
                
                # 3단계: 이슈 그루핑
                current_state = group_issues_node(current_state)
                with progress_container:
                    progress_bar.progress(current_state["progress"] / 100)
                    status_text.info(f"{current_state['current_step']}")
                
                # 4단계: 그룹 분석
                current_state = analyze_groups_node(current_state)
                with progress_container:
                    progress_bar.progress(current_state["progress"] / 100)
                    status_text.info(f"{current_state['current_step']}")
                
                # 5단계: 중요도 점수화
                current_state = score_importance_node(current_state)
                with progress_container:
                    progress_bar.progress(current_state["progress"] / 100)
                    status_text.success(f"{current_state['current_step']}")
                
                # 최종 상태를 final_state로 설정
                final_state = current_state
                
                # 결과 추출
                merged_items = final_state["filtered_items"]
                grouped = final_state["grouped_items"]
                group_analyses = final_state["group_analyses"]
                issue_scores = final_state["issue_scores"]

                st.success(f"검색 결과 {len(merged_items)}건 (최근 1개월 내)")
                
                st.markdown("---")
                
                # Top 3 이슈만 노출
                top_3_labels = list(grouped.keys())[:3]
                
                for label in top_3_labels:
                    items_in_group = grouped[label]
                    importance_score = issue_scores.get(label, 0)
                    
                    st.subheader(f"이슈: {label}")
                    st.caption(f"중요도 점수: {importance_score}/100")
                    
                    # 왼쪽: 요약/인사이트/추천 조사, 오른쪽: 기사 목록
                    col_analysis, col_articles = st.columns([2, 1])
                    
                    with col_analysis:
                        # 통합 분석 결과 표시
                        analysis_text = group_analyses.get(label) or "분석을 생성할 수 없습니다."
                        st.markdown(analysis_text)
                    
                    with col_articles:
                        # 관련 기사 리스트
                        st.write("**관련 기사:**")
                        for item in items_in_group:
                            st.markdown(f"**{item.get('title', '')}**", unsafe_allow_html=True)
                            st.markdown(item.get('description', ''), unsafe_allow_html=True)
                            link = item.get('link', '')
                            if link:
                                st.markdown(f"[기사 보기]({link})")
                            pub_date = item.get('pubDate')
                            if pub_date:
                                try:
                                    dt = parsedate_to_datetime(pub_date)
                                    st.caption(dt.strftime('%Y-%m-%d %H:%M'))
                                except Exception:
                                    st.caption(pub_date)
                            st.divider()
    except Exception as e:
        st.error(f"역할별 검색 중 오류가 발생했습니다: {e}")