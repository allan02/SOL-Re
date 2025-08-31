import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import streamlit as st
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

@dataclass
class SearchItem:
    """웹 검색 결과 아이템"""
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None

@dataclass
class CountryRegulation:
    """국가별 규제 정보"""
    country: str
    regulation_name: str
    description: str
    effective_date: Optional[str] = None
    status: str = "active"  # "active", "proposed", "draft"
    key_requirements: List[str] = None
    source_url: str = ""

@dataclass
class CountryRisk:
    """국가별 리스크 정보"""
    country: str
    risk_level: str  # "low", "medium", "high"
    risk_category: str  # "regulatory", "operational", "reputation", "financial"
    description: str
    priority: int  # 1-3 (1: highest)
    mitigation_strategies: List[str]
    compliance_requirements: List[str]

class WebSearch:
    """Tavily 기반 웹 검색 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.client = None
        if TAVILY_AVAILABLE and self.api_key:
            try:
                self.client = TavilyClient(api_key=self.api_key)
            except Exception as e:
                pass
    
    def search(self, query: str, country: Optional[str] = None, max_results: int = 8) -> List[SearchItem]:
        """웹 검색 수행"""
        if not query or not query.strip() or not self.client:
            return []
        
        try:
            # 국가별 검색 쿼리 구성
            search_query = f"{query} {country} regulation" if country else query
            
            response = self.client.search(
                query=search_query,
                search_depth="basic",
                include_domains=[],
                exclude_domains=[],
                max_results=max_results
            )
            
            results = []
            for item in response.get("results", []):
                results.append(SearchItem(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    published_date=item.get("published_date")
                ))
            
            return results
            
        except Exception as e:
            return []

class RegulationAnalyzer:
    """OpenAI 기반 규제 분석 클래스"""
    
    def __init__(self, model: str = "gpt-4o-mini", client: Optional[OpenAI] = None):
        self.model = model
        self.client = client
        if not self.client and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
    
    def analyze(self, results: List[SearchItem]) -> List[CountryRegulation]:
        """검색 결과를 분석하여 규제 정보 추출"""
        if not results or not self.client:
            return []
        
        try:
            # 검색 결과를 프롬프트로 구성
            results_text = "\n".join([
                f"• {item.title}\n  URL: {item.url}\n  내용: {item.snippet}\n"
                for item in results[:8]  # 상위 8개만 사용
            ])
            
            system_prompt = """당신은 세계의 스테이블코인 규제에 대해 분석하는 전문가입니다. 다음 정책을 엄격히 따르세요:
1. 사실 위주로 분석하세요
2. 불확실한 정보는 공란으로 두거나 빈 배열을 사용하세요
3. 환각(hallucination)을 금지하세요
4. 정확한 JSON 리스트만 출력하세요
5. 각 규제에 대해 상세하고 풍성한 설명을 한국어로 제공하세요
6. 규제의 배경, 목적, 주요 내용, 주요 변화 내용, 시장에 미치는 영향 등을 한국어로 포함하세요
7. 모든 설명은 반드시 한국어로 작성하세요
8. 영어 설명이 나오면 한국어로 번역하여 제공하세요
9. 모든 답변은 문장이 끝나면 \n을 쳐서 구조화하여 답변하세요 
10. 출처 링크는 가장 작은 글자크기로 보여주세요

**중요한 규칙:**
- 사용자가 특정 국가나 지역에 대해 질문하면, 해당 국가/지역의 내용만 답변하세요
- 다른 국가나 지역의 정보는 포함하지 마세요
- 예: "싱가폴"에 대해 질문하면 싱가폴 관련 내용만, "미국"에 대해 질문하면 미국 관련 내용만 답변

**🚨 강제 구조화 가이드 (반드시 준수):**

**📋 규제 배경**
[규제가 도입된 배경과 이유 - 최소 3-4문장으로 상세하게 작성]

**🎯 규제 목적**
[규제의 주요 목표와 의도 - 최소 2-3문장으로 상세하게 작성]

**📋 주요 내용**
[규제의 핵심 내용과 요구사항 - 최소 4-5문장으로 상세하게 작성]

**🔄 주요 변화**
[기존 규제와의 차이점과 변화사항 - 최소 3-4문장으로 상세하게 작성]

**💡 시장 영향**
[스테이블코인 시장과 업계에 미치는 영향 - 구체적인 예시와 함께 최소 3-4문장으로 작성]

**⚠️ 준수 요구사항**
[업체들이 준수해야 할 구체적 요구사항 - 실행 가능한 방안을 최소 3-4문장으로 작성]

**🚨 최종 경고:** 위 형식을 정확히 따르지 않으면 답변이 무효화됩니다."""

            user_prompt = f"""다음 웹 검색 결과를 분석하여 국가별 스테이블코인 규제 정보를 추출하세요:

{results_text}

출력 형식 (JSON 리스트):
[
  {{
    "country": "국가명",
    "regulation_name": "규제명",
    "description": "규제 설명 (반드시 한국어로 상세하게 작성)",
    "effective_date": "시행일 (알 수 없는 경우 null)",
    "status": "active/proposed/draft",
    "key_requirements": ["요구사항1", "요구사항2"],
    "source_url": "출처 URL"
  }}
]

**중요: description 필드는 반드시 한국어로 작성하고, 다음 구조로 상세하게 설명하세요:**

**📋 규제 배경**
[규제가 도입된 배경과 이유 - 최소 3-4문장으로 상세하게 작성]

**🎯 규제 목적**
[규제의 주요 목표와 의도 - 최소 2-3문장으로 상세하게 작성]

**📋 주요 내용**
[규제의 핵심 내용과 요구사항 - 최소 4-5문장으로 상세하게 작성]

**🔄 주요 변화**
[기존 규제와의 차이점과 변화사항 - 최소 3-4문장으로 상세하게 작성]

**💡 시장 영향**
[스테이블코인 시장과 업계에 미치는 영향 - 구체적인 예시와 함께 최소 3-4문장으로 작성]

**⚠️ 준수 요구사항**
[업체들이 준수해야 할 구체적 요구사항 - 실행 가능한 방안을 최소 3-4문장으로 작성]

모든 설명은 구조화하여 답변하세요."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            
            # 응답 내용 검증
            if not content:
                return []
            
            # JSON 형식 검증 및 정리
            try:
                # 응답에서 JSON 부분만 추출 (```json ... ``` 형태일 수 있음)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[1].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                
                regulations = json.loads(content)
            except json.JSONDecodeError as e:
                return []
            
            # 데이터 검증 및 변환
            validated_regulations = []
            for reg in regulations:
                if isinstance(reg, dict) and "country" in reg and "regulation_name" in reg:
                    validated_regulations.append(CountryRegulation(
                        country=reg.get("country", ""),
                        regulation_name=reg.get("regulation_name", ""),
                        description=reg.get("description", ""),
                        effective_date=reg.get("effective_date"),
                        status=reg.get("status", "active"),
                        key_requirements=reg.get("key_requirements", []),
                        source_url=reg.get("source_url", "")
                    ))
            
            return validated_regulations
            
        except json.JSONDecodeError as e:
            return []
        except Exception as e:
            return []

class RiskPredictor:
    """OpenAI 기반 리스크 예측 클래스"""
    
    def __init__(self, model: str = "gpt-4o-mini", client: Optional[OpenAI] = None):
        self.model = model
        self.client = client
        if not self.client and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
    
    def predict(self, regs: List[CountryRegulation], scenario_hint: Optional[str] = None) -> List[CountryRisk]:
        """규제 정보를 바탕으로 리스크 예측"""
        if not regs:
            return []
        
        if not self.client:
            return []
        
        try:
            # 규제 정보를 JSON으로 변환
            regs_json = json.dumps([{
                "country": reg.country,
                "regulation_name": reg.regulation_name,
                "description": reg.description,
                "status": reg.status,
                "key_requirements": reg.key_requirements
            } for reg in regs], ensure_ascii=False)
            
            system_prompt = """당신은 한국 대형 금융그룹(신한금융그룹) 스테이블코인 규제관련 애널리스트, 스테이블코인 규제 관련 리스크·컴플라이언스 전략가입니다.
과신을 금지하고 현실적인 리스크 평가를 제공하세요. 

중요: JSON 출력에서 다음 필드들을 반드시 포함하되, 사용자에게는 보이지 않게 하세요:
- risk_level: "high", "medium", "low 중 하나
- priority: 1, 2, 3 중 하나 (1이 최고 우선순위)

사용자에게는 리스크 수준과 우선순위를 이모지와 간단한 표현으로만 표시하고, 국가이름 앞에 숫자를 붙이지 마세요:
- 🔴 높은 리스크 (우선순위 1)
- 🟡 중간 리스크 (우선순위 2)  
- 🟢 낮은 리스크 (우선순위 3)

모든 설명은 한국어로 작성하세요.
모든 답변은 ***구조화하여*** 답변하고 출처는 가장 작은 글자크기로 보여주세요.

**리스크 설명 구조화 가이드:**

**📋 리스크 개요:** [리스크의 기본적인 내용과 성격]

**🎯 발생 원인:** [해당 리스크가 발생하는 주요 원인들]

**💡 시장 영향:** [신한금융그룹과 시장에 미치는 영향]

**⚠️ 대응 전략:** [리스크 완화를 위한 구체적 전략]

**🔍 준수 요구사항:** [규제 준수를 위한 상세 요구사항]

**중요:** 각 섹션 사이에 명확한 줄바꿈을 사용하여 시각적으로 구조화된 답변을 제공하세요.

엄격한 JSON 리스트만 출력하세요."""

            user_prompt = f"""다음 규제 정보를 바탕으로 신한금융그룹이 직면할 수 있는 리스크를 분석하세요:

규제 정보:
{regs_json}

{scenario_hint if scenario_hint else ""}

출력 형식 (JSON 리스트):
[
  {{
    "country": "국가명",
    "risk_level": "low/medium/high",
    "risk_category": "regulatory/operational/reputation/financial",
    "description": "리스크 설명",
    "priority": 1-3 (1: 최고 우선순위),
    "mitigation_strategies": ["대응 전략1", "대응 전략2"],
    "compliance_requirements": ["준수 요구사항1", "준수 요구사항2"]
  }}
]"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            
            # 응답 내용 검증
            if not content:
                return []
            
            # JSON 형식 검증 및 정리
            try:
                # 응답에서 JSON 부분만 추출 (```json ... ``` 형태일 수 있음)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[1].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                
                risks = json.loads(content)
            except json.JSONDecodeError as e:
                return []
            
            # 데이터 검증 및 변환
            validated_risks = []
            for risk in risks:
                if isinstance(risk, dict) and "country" in risk and "description" in risk:
                    priority = risk.get("priority", 3)
                    if not isinstance(priority, int) or priority < 1 or priority > 3:
                        priority = 3
                    
                    validated_risks.append(CountryRisk(
                        country=risk.get("country", ""),
                        risk_level=risk.get("risk_level", "medium"),
                        risk_category=risk.get("risk_category", "regulatory"),
                        description=risk.get("description", ""),
                        priority=priority,
                        mitigation_strategies=risk.get("mitigation_strategies", []),
                        compliance_requirements=risk.get("compliance_requirements", [])
                    ))
            
            return validated_risks
            
        except json.JSONDecodeError as e:
            return []
        except Exception as e:
            return []

class QAAgent:
    """OpenAI 기반 Q&A 에이전트 클래스"""
    
    def __init__(self, model: str = "gpt-4o-mini", client: Optional[OpenAI] = None):
        self.model = model
        self.client = client
        self.history = []
        if not self.client and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
    
    def ask(self, question: str, regs: List[CountryRegulation], risks: List[CountryRisk]) -> str:
        """질문에 대한 답변 생성"""
        if not self.client:
            return "OpenAI API 키가 설정되지 않았습니다."
        
        try:
            # 대화 히스토리 관리
            if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
                if "reg_qa_history" not in st.session_state:
                    st.session_state.reg_qa_history = []
                if "reg_context" not in st.session_state:
                    st.session_state.reg_context = {"regs": [], "risks": []}
                history = st.session_state.reg_qa_history
                stored_regs = st.session_state.reg_context["regs"]
                stored_risks = st.session_state.reg_context["risks"]
            else:
                history = self.history
                stored_regs = getattr(self, 'stored_regs', [])
                stored_risks = getattr(self, 'stored_risks', [])
            
            # 새로운 규제/리스크 정보가 있으면 저장
            if regs:
                if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
                    st.session_state.reg_context["regs"] = regs
                else:
                    self.stored_regs = regs
                stored_regs = regs
            
            if risks:
                if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
                    st.session_state.reg_context["risks"] = risks
                else:
                    self.stored_risks = risks
                stored_risks = risks
            
            # 최근 6턴만 유지
            if len(history) > 6:
                history = history[-6:]
            
            # 컨텍스트 구성 (저장된 정보 사용)
            context = ""
            if stored_regs:
                context += "규제 정보:\n"
                for reg in stored_regs:
                    context += f"- {reg.country}: {reg.regulation_name}\n"
            
            if stored_risks:
                context += "\n리스크 정보:\n"
                for risk in stored_risks:
                    context += f"- {risk.country} ({risk.risk_level}): {risk.description}\n"
            
            # 컨텍스트가 없고 첫 번째 질문인 경우
            if not context and not history:
                return "안녕하세요! 신한금융그룹의 스테이블코인 규제 분석 전문가입니다. 규제 분석을 실행하거나 직접 질문해주세요. 예시: '스테이블코인 규제의 전반적인 동향을 설명해주세요' 또는 '신한금융그룹이 주목해야 할 주요 규제 이슈는 무엇인가요?'"
            
            # 컨텍스트가 없지만 대화 히스토리가 있는 경우 (이전 대화 기반 질문)
            if not context and history:
                context = "이전 대화 내용을 참고하여 답변하세요."
            
            # 컨텍스트가 없고 대화 히스토리도 없는 경우 (일반적인 질문)
            if not context:
                context = "스테이블코인 규제와 관련된 일반적인 질문에 답변하겠습니다."
            
            system_prompt = """당신은 신한금융그룹의 해외 스테이블코인 규제 분석 전문가입니다. 
제공된 컨텍스트(규제/리스크)와 이전 대화 내용을 종합하여 답변하세요.
컨텍스트가 없는 경우에도 스테이블코인 규제 전반에 대한 전문적인 지식을 바탕으로 답변하세요.
창의적인 아이디어나 추가 분석이 요청되는 경우, 기존 정보를 바탕으로 새로운 관점을 제시하세요.
불확실한 경우 명시하고 다음 확인 과제를 제안하세요.
한국말로 답변하세요.

**🚨 강제 구조화 규칙 (반드시 준수):**
- 반드시 아래 형식을 정확히 따라 답변하세요
- 각 섹션은 반드시 줄바꿈으로 구분하세요
- 섹션 제목은 반드시 **굵은 글씨**로 표시하세요
- 섹션 내용은 반드시 구체적이고 상세하게 작성하세요

**📋 핵심 요약**
[질문에 대한 핵심 답변 요약 - 최소 2-3문장으로 상세하게 작성]

**🔍 상세 분석**
[규제/리스크에 대한 구체적 분석 또는 이전 대화 기반 창의적 아이디어 - 최소 4-5문장으로 상세하게 작성]

**💡 시장 영향**
[신한금융그룹과 시장에 미치는 영향 - 구체적인 예시와 함께 최소 3-4문장으로 작성]

**⚠️ 주의사항**
[특별히 주의해야 할 점들 - 구체적인 리스크나 주의점을 최소 2-3문장으로 작성]

**🎯 권장사항**
[구체적인 대응 방안과 권장사항 - 실행 가능한 전략을 최소 3-4문장으로 작성]

**❓ 추가 확인사항**
[더 정확한 답변을 위해 확인이 필요한 사항들 - 구체적인 질문이나 확인점을 최소 2-3문장으로 작성]

**💡 창의적 아이디어**
[사용자의 요청에 따라 추가적인 창의적 아이디어나 분석 - 혁신적인 관점을 최소 3-4문장으로 작성]

**중요한 규칙:**
- 사용자가 특정 국가나 지역에 대해 질문하면, 해당 국가/지역의 내용만 답변하세요
- 다른 국가나 지역의 정보는 포함하지 마세요
- 예: "싱가폴"에 대해 질문하면 싱가폴 관련 내용만, "미국"에 대해 질문하면 미국 관련 내용만 답변

**🚨 최종 경고:** 위 형식을 정확히 따르지 않으면 답변이 무효화됩니다."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"컨텍스트:\n{context}\n\n질문: {question}\n\n**🚨 강제 지시사항:**\n1. 반드시 위의 system_prompt 형식을 정확히 따라 답변하세요\n2. 각 섹션은 반드시 줄바꿈으로 구분하세요\n3. 섹션 제목은 반드시 **굵은 글씨**로 표시하세요\n4. 질문에서 언급된 특정 국가나 지역에 대해서만 답변하세요\n5. 다른 국가나 지역의 정보는 포함하지 마세요\n6. 형식을 따르지 않으면 답변이 무효화됩니다"}
            ]
            
            # 대화 히스토리 추가
            for h in history:
                messages.append({"role": "user", "content": h["question"]})
                messages.append({"role": "assistant", "content": h["answer"]})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=1
            )
            
            answer = response.choices[0].message.content
            
            # 히스토리 업데이트
            history.append({"question": question, "answer": answer})
            if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
                st.session_state.reg_qa_history = history
            else:
                self.history = history
            
            return answer
            
        except Exception as e:
            return "질문 처리 중 오류가 발생했습니다."

def run_pipeline(query: str, country: Optional[str] = None, scenario_hint: Optional[str] = None, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """전체 파이프라인 실행"""
    try:
        # 1. 웹 검색
        searcher = WebSearch()
        search_results = searcher.search(query, country)
        
        if not search_results:
            return {
                "search_results": [],
                "regulations": [],
                "risks": [],
                "message": "검색 결과가 없습니다."
            }
        
        # 2. 규제 분석
        analyzer = RegulationAnalyzer(model=model)
        regulations = analyzer.analyze(search_results)
        
        # 3. 리스크 예측
        predictor = RiskPredictor(model=model)
        risks = predictor.predict(regulations, scenario_hint)
        
        # 4. Q&A 에이전트 초기화 (대화를 위해)
        qa_agent = QAAgent(model=model)
        
        return {
            "search_results": search_results,
            "regulations": regulations,
            "risks": risks,
            "qa_agent": qa_agent,
            "message": "분석이 완료되었습니다."
        }
        
    except Exception as e:
        return {
            "search_results": [],
            "risks": [],
            "message": f"오류가 발생했습니다: {str(e)}"
        }

def get_regulation_analysis(question: str) -> str:
    """기존 코드와의 호환성을 위한 함수 (deprecated)
    
    이 함수는 기존 코드와의 호환성을 위해 유지됩니다.
    새로운 코드에서는 run_pipeline() 함수를 사용하는 것을 권장합니다.
    """
    try:
        # 간단한 규제 분석을 위한 기본 파이프라인 실행
        result = run_pipeline(question, model="gpt-4o-mini")
        
        if not result["regulations"]:
            return """## 📋 규제 분석 결과

## ❌ 분석 실패
규제 정보를 찾을 수 없습니다. 더 구체적인 검색어를 사용해보세요.

### 💡 검색 팁
• 국가명을 포함한 검색어 사용 (예: "미국 스테이블코인 규제")
• 구체적인 규제명 사용 (예: "MiCA 규제")
• 최신 날짜 포함 (예: "2024년 스테이블코인 정책")"""
        
        # 구조화된 규제 분석 결과 반환
        summary = f"""# 📋 규제 분석 결과

#### 🔍 검색 질문
**질문:** {question}

#### 📊 규제 정보 요약
"""
        
        for i, reg in enumerate(result["regulations"], 1):
            summary += f"""### {i}. {reg.country} - {reg.regulation_name}



"""
            # 설명을 구조화된 형태로 출력
            if reg.description:
                # 규제 배경, 규제 목적 등의 제목을 굵은 글씨로 출력
                if "규제 배경" in reg.description:
                    summary += "**📋 규제 배경**\n"
                    background_start = reg.description.find("규제 배경")
                    background_end = reg.description.find("규제 목적") if "규제 목적" in reg.description else len(reg.description)
                    background_text = reg.description[background_start:background_end].replace("규제 배경:", "").strip()
                    # 이모티콘 제거 및 깔끔하게 정리
                    background_text = background_text.replace("📋", "").replace("🎯", "").replace("📋", "").replace("🔄", "").replace("💡", "").replace("⚠️", "").strip()
                    if background_text:
                        summary += f"  ◦ {background_text}\n"
                    summary += "\n"
                
                if "규제 목적" in reg.description:
                    summary += "**🎯 규제 목적**\n"
                    purpose_start = reg.description.find("규제 목적")
                    purpose_end = reg.description.find("주요 내용") if "주요 내용" in reg.description else len(reg.description)
                    purpose_text = reg.description[purpose_start:purpose_end].replace("규제 목적:", "").strip()
                    # 이모티콘 제거 및 깔끔하게 정리
                    purpose_text = purpose_text.replace("📋", "").replace("🎯", "").replace("📋", "").replace("🔄", "").replace("💡", "").replace("⚠️", "").strip()
                    if purpose_text:
                        summary += f"  ◦ {purpose_text}\n"
                    summary += "\n"
                
                if "주요 내용" in reg.description:
                    summary += "**📋 주요 내용**\n"
                    content_start = reg.description.find("주요 내용")
                    content_end = reg.description.find("주요 변화") if "주요 변화" in reg.description else len(reg.description)
                    content_text = reg.description[content_start:content_end].replace("주요 내용:", "").strip()
                    # 이모티콘 제거 및 깔끔하게 정리
                    content_text = content_text.replace("📋", "").replace("🎯", "").replace("📋", "").replace("🔄", "").replace("💡", "").replace("⚠️", "").strip()
                    if content_text:
                        summary += f"  ◦ {content_text}\n"
                    summary += "\n"
                
                if "주요 변화" in reg.description:
                    summary += "**🔄 주요 변화**\n"
                    change_start = reg.description.find("주요 변화")
                    change_end = reg.description.find("시장 영향") if "시장 영향" in reg.description else len(reg.description)
                    change_text = reg.description[change_start:change_end].replace("주요 변화:", "").strip()
                    # 이모티콘 제거 및 깔끔하게 정리
                    change_text = change_text.replace("📋", "").replace("🎯", "").replace("📋", "").replace("🔄", "").replace("💡", "").replace("⚠️", "").strip()
                    if change_text:
                        summary += f"  ◦ {change_text}\n"
                    summary += "\n"
                
                if "시장 영향" in reg.description:
                    summary += "**💡 시장 영향**\n"
                    impact_start = reg.description.find("시장 영향")
                    impact_end = reg.description.find("준수 요구사항") if "준수 요구사항" in reg.description else len(reg.description)
                    impact_text = reg.description[impact_start:impact_end].replace("시장 영향:", "").strip()
                    # 이모티콘 제거 및 깔끔하게 정리
                    impact_text = impact_text.replace("📋", "").replace("🎯", "").replace("📋", "").replace("🔄", "").replace("💡", "").replace("⚠️", "").strip()
                    if impact_text:
                        summary += f"  ◦ {impact_text}\n"
                    summary += "\n"
                
                if "준수 요구사항" in reg.description:
                    summary += "**⚠️ 준수 요구사항**\n"
                    compliance_start = reg.description.find("준수 요구사항")
                    compliance_text = reg.description[compliance_start:].replace("준수 요구사항:", "").strip()
                    # 이모티콘 제거 및 깔끔하게 정리
                    compliance_text = compliance_text.replace("📋", "").replace("🎯", "").replace("📋", "").replace("🔄", "").replace("💡", "").replace("⚠️", "").strip()
                    if compliance_text:
                        summary += f"  ◦ {compliance_text}\n"
                    summary += "\n"
                
                # 위의 구조화된 형태가 없는 경우 기본 출력
                if not any(keyword in reg.description for keyword in ["규제 배경", "규제 목적", "주요 내용", "주요 변화", "시장 영향", "준수 요구사항"]):
                    description_sentences = reg.description.split('. ')
                    for sentence in description_sentences:
                        if sentence.strip():
                            summary += f"  ◦ {sentence.strip()}\n"
                    summary += "\n"
            
            if reg.effective_date:
                summary += f"**📅 시행 정보**\n"
                summary += f"• **시행일:** {reg.effective_date}\n\n"
            
            if reg.key_requirements:
                summary += "**📋 주요 요구사항**\n"
                for req in reg.key_requirements:
                    summary += f"  ◦ {req}\n"
                summary += "\n"
            
            summary += f"###### 🔗 출처: {reg.source_url}\n"
            summary += "---\n\n"
        
        if result["risks"]:
            summary += """### ⚠️ 리스크 분석
"""
            # 우선순위별로 정렬
            sorted_risks = sorted(result["risks"], key=lambda x: x.priority)
            for i, risk in enumerate(sorted_risks, 1):
                priority_emoji = {1: "🔴", 2: "🟡", 3: "🟢"}.get(risk.priority, "⚪")
                risk_level_text = {1: "높은 리스크", 2: "중간 리스크", 3: "낮은 리스크"}.get(risk.priority, "알 수 없음")
                summary += f"""### {priority_emoji} {i}. {risk.country} - {risk.risk_category}

**📊 리스크 정보**
• **리스크 수준:** {risk_level_text}

**📝 상세 설명**
"""
                # 설명을 문장 단위로 나누어 구조화
                if risk.description:
                    description_sentences = risk.description.split('. ')
                    for sentence in description_sentences:
                        if sentence.strip():
                            summary += f"  ◦ {sentence.strip()}\n"
                    summary += "\n"

                summary += "**🛡️ 대응 전략**\n"
                for strategy in risk.mitigation_strategies:
                    summary += f"  ◦ {strategy}\n"
                
                summary += "\n**📋 준수 요구사항**\n"
                for req in risk.compliance_requirements:
                    summary += f"  ◦ {req}\n"
                summary += "\n---\n\n"
        
        # 신한금융그룹에 영향을 미칠 수 있는 가상 시나리오 추가
        summary += """### 🎯 해당 검색결과가 신한금융그룹에 영향을 미칠 수 있는 시나리오

#### 📈 시나리오 1: 규제 변화 기반 사업 기회 창출
• **상황**: """
        
        # 검색 결과에서 발견된 국가들을 기반으로 시나리오 생성
        countries_found = list(set([reg.country for reg in result["regulations"]]))
        if countries_found:
            summary += f"{', '.join(countries_found[:3])} 등 주요 국가들의 스테이블코인 규제 변화"
        else:
            summary += "글로벌 스테이블코인 규제 환경 변화"
        
        summary += """로 인한 새로운 시장 진출 기회 발생

• **영향**: 신한금융그룹의 해외 스테이블코인 사업 확장 가능성 증가

• **대응 방안**: 현지 파트너십 구축 및 규제 준수 체계 마련

#### 🌍 시나리오 2: 규제 표준화를 통한 글로벌 경쟁력 강화
• **상황**: """
        
        if countries_found:
            summary += f"{countries_found[0] if len(countries_found) > 0 else '주요 국가'}의 규제 프레임워크가 글로벌 표준으로 자리잡음"
        else:
            summary += "국제 규제 협력을 통한 표준화 움직임"
        
        summary += """

• **영향**: 신한금융그룹이 글로벌 규제 표준을 선도할 수 있는 기회

• **대응 방안**: 글로벌 규제 모니터링 체계 강화 및 국제 협력 주도

#### 💼 시나리오 3: 혁신 기술 기반 시장 선점 전략
• **상황**: """
        
        if result["regulations"]:
            regulation_names = [reg.regulation_name for reg in result["regulations"][:2]]
            summary += f"{', '.join(regulation_names)} 등 새로운 규제 요구사항에 대응한 기술 혁신 필요성 증가"
        else:
            summary += "규제 변화에 따른 기술적 요구사항 증가"
        
        summary += """

• **영향**: 신한금융그룹의 기술 경쟁력과 시장 점유율 확대 기회

• **대응 방안**: 블록체인 기술 투자 확대 및 규제 준수 솔루션 개발 선도"""

        
        summary += """ 




 """
        
        return summary
        
    except Exception as e:
        return f"""# ❌ 규제 분석 오류

### 🚨 오류 내용
**오류 메시지:** {str(e)}

### 🔧 해결 방법

**📋 권장 조치**
• 잠시 후 다시 시도해주세요
• 검색어를 더 구체적으로 입력해주세요
• 시스템 관리자에게 문의해주세요

**💡 검색 팁**
• 국가명을 포함한 검색어 사용 (예: "미국 스테이블코인 규제")
• 구체적인 규제명 사용 (예: "MiCA 규제")
• 최신 날짜 포함 (예: "2024년 스테이블코인 정책")"""

def get_country_regulation_comparison(selected_countries: List[str]) -> str:
    """선택된 국가들의 스테이블코인 규제를 웹검색하여 비교 분석합니다.
    
    Args:
        selected_countries: 분석할 국가 리스트
        
    Returns:
        str: 국가별 규제 비교 분석 결과
    """
    try:
        # 각 국가별로 규제 정보 검색
        searcher = WebSearch()
        all_regulations = []
        
        for country in selected_countries:
            # 국가별 스테이블코인 규제 검색
            search_results = searcher.search(f"{country} stablecoin regulation cryptocurrency policy", max_results=6)
            
            if search_results:
                # OpenAI를 사용하여 규제 정보 분석
                try:
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    if client:
                        # 검색 결과를 텍스트로 구성
                        search_text = "\n\n".join([
                            f"제목: {item.title}\n내용: {item.snippet}\nURL: {item.url}"
                            for item in search_results
                        ])
                        
                        system_prompt = """당신은 국제 금융 규제 전문가입니다. 특정 국가의 스테이블코인 규제 현황을 분석하여 
구조화된 정보로 정리해주세요.

**🚨 강제 구조화 규칙 (반드시 준수):**
- 반드시 아래 형식을 정확히 따라 답변하세요
- 각 섹션은 반드시 줄바꿈으로 구분하세요
- 섹션 제목은 반드시 **굵은 글씨**로 표시하세요
- 섹션 내용은 반드시 구체적이고 상세하게 작성하세요
- 형식을 따르지 않으면 답변이 무효화됩니다
- **모든 내용은 반드시 한국어로 작성하세요**

**출력 형식 (JSON):**
{
  "country": "국가명",
  "regulation_overview": "규제 현황 개요 (한국어로 작성)",
  "key_regulations": ["주요 규제1 (한국어)", "주요 규제2 (한국어)"],
  "regulatory_approach": "규제 접근 방식 (한국어로 작성)",
  "compliance_requirements": ["준수 요구사항1 (한국어)", "준수 요구사항2 (한국어)"],
  "market_impact": "시장에 미치는 영향 (한국어로 작성)",
  "future_outlook": "향후 전망 (한국어로 작성)",
  "source_urls": ["출처URL1", "출처URL2"]
}

**중요한 규칙:**
- 사용자가 특정 국가나 지역에 대해 질문하면, 해당 국가/지역의 내용만 답변하세요
- 다른 국가나 지역의 정보는 포함하지 마세요
- 예: "싱가폴"에 대해 질문하면 싱가폴 관련 내용만, "미국"에 대해 질문하면 미국 관련 내용만 답변
- **모든 설명은 반드시 한국어로 작성하세요**
- **각 설명은 반드시 줄바꿈으로 구분하여 시각적으로 구조화하세요**

**🚨 최종 경고:** 위 형식을 정확히 따르지 않으면 답변이 무효화됩니다."""

                        user_prompt = f"""다음 {country}의 스테이블코인 규제 관련 뉴스를 분석하여 구조화된 정보로 정리해주세요:

{search_text}

위 뉴스들을 종합하여 {country}의 스테이블코인 규제 현황을 분석하고, 요청된 JSON 형식으로 답변해주세요.

**🚨 강제 구조화 지시사항:**
1. 반드시 위의 system_prompt 형식을 정확히 따라 답변하세요
2. JSON 형식으로만 답변하세요
3. 형식을 따르지 않으면 답변이 무효화됩니다
4. **모든 내용은 반드시 한국어로 작성하세요**
5. **각 설명은 반드시 줄바꿈으로 구분하여 시각적으로 구조화하세요**

**요구사항:**
1. 해당 국가의 규제 현황을 정확하게 파악하여 한국어로 설명
2. 주요 규제와 준수 요구사항을 구체적으로 정리하여 한국어로 작성
3. 시장 영향과 향후 전망을 분석하여 한국어로 설명
4. 출처 URL을 포함하여 정보의 신뢰성 확보
5. **모든 설명은 줄바꿈을 사용하여 시각적으로 구조화하세요**

**🚨 최종 경고:** 위 형식을 정확히 따르지 않으면 답변이 무효화됩니다."""

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.2
                        )
                        
                        content = response.choices[0].message.content.strip()
                        
                        # JSON 형식 검증 및 정리
                        try:
                            # 응답에서 JSON 부분만 추출
                            if "```json" in content:
                                content = content.split("```json")[1].split("```")[0].strip()
                            elif "```" in content:
                                content = content.split("```")[1].strip()
                            
                            regulation_data = json.loads(content)
                            
                            # 텍스트 필드들을 구조화 (줄바꿈으로 구분)
                            text_fields = ['regulation_overview', 'regulatory_approach', 'market_impact', 'future_outlook']
                            for field in text_fields:
                                if field in regulation_data and regulation_data[field]:
                                    # 문장 단위로 줄바꿈 추가
                                    text = regulation_data[field]
                                    sentences = text.split('. ')
                                    if len(sentences) > 1:
                                        regulation_data[field] = '.\n'.join(sentences)
                            
                            regulation_data["search_results"] = search_results
                            all_regulations.append(regulation_data)
                            
                        except json.JSONDecodeError as e:
                            # 기본 정보로 대체
                            all_regulations.append({
                                "country": country,
                                "regulation_overview": f"{country}의 스테이블코인 규제 정보를 분석할 수 없습니다.",
                                "key_regulations": ["정보 부족"],
                                "regulatory_approach": "정보 부족",
                                "compliance_requirements": ["정보 부족"],
                                "market_impact": "정보 부족",
                                "future_outlook": "정보 부족",
                                "source_urls": [],
                                "search_results": search_results
                            })
                        
                except Exception as e:
                    # 기본 정보로 대체
                    all_regulations.append({
                        "country": country,
                        "regulation_overview": f"{country}의 스테이블코인 규제 정보를 분석할 수 없습니다.",
                        "key_regulations": ["정보 부족"],
                        "regulatory_approach": "정보 부족",
                        "compliance_requirements": ["정보 부족"],
                        "market_impact": "정보 부족",
                        "future_outlook": "정보 부족",
                        "source_urls": [],
                        "search_results": search_results
                    })
        
        if not all_regulations:
            return "국가별 규제 정보를 검색할 수 없습니다. 잠시 후 다시 시도해주세요."
        
        # 비교 분석 결과 생성
        comparison_result = _generate_regulation_comparison_table(all_regulations)
        
        return comparison_result
        
    except Exception as e:
        return f"국가별 규제 비교 분석 중 오류가 발생했습니다: {str(e)}"


def _generate_regulation_comparison_table(regulations: List[Dict]) -> str:
    """규제 정보를 비교 표 형태로 생성합니다."""
    
    comparison_result = """### 🌍 국가별 스테이블코인 규제 비교 분석

#### 📊 비교 분석 결과

"""
    
    # 국가별 규제 개요 비교
    comparison_result += "##### 📋 규제 현황 개요 비교\n\n"
    comparison_result += "| 국가 | 규제 현황 |\n"
    comparison_result += "|:-----|:----------|\n"
    
    # 국가별로 규제 현황을 그룹화
    country_regulations = {}
    
    for reg in regulations:
        country = reg.get("country", "알 수 없음")
        overview = reg.get("regulation_overview", "정보 부족")
        
        # 국가명을 깔끔하게 정리 (더 정확한 추출)
        clean_country = ""
        if country and country != "알 수 없음":
            # 괄호나 추가 설명 제거
            if '(' in country:
                clean_country = country.split('(')[0].strip()
            elif ':' in country:
                clean_country = country.split(':')[0].strip()
            elif '의' in country:
                clean_country = country.split('의')[0].strip()
            else:
                clean_country = country.strip()
            
            # 일반적인 국가명 패턴 확인
            if len(clean_country) > 20:  # 너무 길면 기본값 사용
                clean_country = "알 수 없음"
        else:
            clean_country = "알 수 없음"
        
        # 내용이 없거나 "정보 부족"일 때 "-" 표시
        if not overview or overview == "정보 부족" or overview.strip() == "":
            if clean_country not in country_regulations:
                country_regulations[clean_country] = []
            country_regulations[clean_country].append("-")
        else:
            # 문장 단위로 분리하여 각각 별도 행으로 출력
            # 먼저 문장 끝을 명확하게 구분
            overview_clean = overview.replace('..', '.').replace('...', '.')
            
            # 문장 분리 (마침표, 느낌표, 물음표 기준)
            import re
            sentences = re.split(r'[.!?]+', overview_clean)
            numbered_sentences = []
            
            for i, sentence in enumerate(sentences, 1):
                sentence = sentence.strip()
                if sentence and len(sentence) > 5:  # 의미있는 문장만
                    # 문장 끝에 마침표 추가
                    if not sentence.endswith('.'):
                        sentence += '.'
                    numbered_sentences.append(f"{i}. {sentence}")
            
            if numbered_sentences:
                if clean_country not in country_regulations:
                    country_regulations[clean_country] = []
                # 각 문장을 추가
                for sentence in numbered_sentences:
                    # 너무 길면 적절한 길이로 제한 (문장이 끊기지 않도록)
                    if len(sentence) > 150:
                        # 마지막 마침표 위치를 찾아서 그 전까지만 자르기
                        last_period = sentence.rfind('.', 0, 150)
                        if last_period > 100:  # 적절한 길이면 마침표까지
                            sentence = sentence[:last_period+1]
                        else:  # 너무 짧으면 150자까지
                            sentence = sentence[:150] + "..."
                    
                    # 문장 끝을 ~합니다로 통일
                    sentence = sentence.replace('~함.', '~합니다.').replace('~함', '~합니다')
                    if sentence.endswith('함.'):
                        sentence = sentence[:-2] + '합니다.'
                    elif sentence.endswith('함'):
                        sentence = sentence[:-1] + '합니다'
                    
                    country_regulations[clean_country].append(sentence)
            else:
                if clean_country not in country_regulations:
                    country_regulations[clean_country] = []
                # 문장 분리가 안되면 원본을 그대로 사용
                if len(overview) > 150:
                    overview = overview[:150] + "..."
                country_regulations[clean_country].append(overview)
    
    # 그룹화된 규제 현황을 표로 출력
    for clean_country, regulations_list in country_regulations.items():
        if regulations_list:
            # 첫 번째 행에는 국가명 표시
            first_regulation = regulations_list[0]
            comparison_result += f"| {clean_country} | {first_regulation} |\n"
            
            # 나머지 행들은 국가명 없이 규제 현황만 표시
            for regulation in regulations_list[1:]:
                comparison_result += f"| | {regulation} |\n"
    
    comparison_result += "\n---\n\n"
    
    # 준수 요구사항 비교 (간단한 형태)
    comparison_result += "##### ⚠️ 준수 요구사항 비교\n\n"
    comparison_result += "| 국가 | 준수 요구사항 |\n"
    comparison_result += "|:-----|:----------|\n"
    
    # 국가별로 준수 요구사항을 그룹화
    country_compliance = {}
    
    for reg in regulations:
        country = reg.get("country", "알 수 없음")
        compliance = reg.get("compliance_requirements", [])
        
        # 국가명을 깔끔하게 정리 (더 정확한 추출)
        clean_country = ""
        if country and country != "알 수 없음":
            # 괄호나 추가 설명 제거
            if '(' in country:
                clean_country = country.split('(')[0].strip()
            elif ':' in country:
                clean_country = country.split(':')[0].strip()
            elif '의' in country:
                clean_country = country.split('의')[0].strip()
            else:
                clean_country = country.strip()
            
            # 일반적인 국가명 패턴 확인
            if len(clean_country) > 20:  # 너무 길면 기본값 사용
                clean_country = "알 수 없음"
        else:
            clean_country = "알 수 없음"
        
        if compliance and len(compliance) > 0 and compliance[0] != "정보 부족":
            # 첫 번째 요구사항만 표시하고 길이 제한
            comp_text = compliance[0]
            if len(comp_text) > 100:
                comp_text = comp_text[:100] + "..."
            
            # 문장 끝을 ~합니다로 통일
            comp_text = comp_text.replace('~함.', '~합니다.').replace('~함', '~합니다')
            if comp_text.endswith('함.'):
                comp_text = comp_text[:-2] + '합니다.'
            elif comp_text.endswith('함'):
                comp_text = comp_text[:-1] + '합니다'
        else:
            comp_text = "-"
        
        if clean_country not in country_compliance:
            country_compliance[clean_country] = []
        country_compliance[clean_country].append(comp_text)
    
    # 그룹화된 준수 요구사항을 표로 출력
    for clean_country, compliance_list in country_compliance.items():
        if compliance_list:
            # 첫 번째 행에는 국가명 표시
            first_compliance = compliance_list[0]
            comparison_result += f"| {clean_country} | {first_compliance} |\n"
            
            # 나머지 행들은 국가명 없이 준수 요구사항만 표시
            for compliance in compliance_list[1:]:
                comparison_result += f"| | {compliance} |\n"
    
    comparison_result += "\n---\n\n"
    
    # 원본 검색 결과 링크 (간단한 형태로)
    comparison_result += "#### 📰 원본 뉴스 링크\n\n"
    
    # 국가별로 뉴스 링크를 그룹화
    country_news = {}
    
    for reg in regulations:
        country = reg.get("country", "알 수 없음")
        search_results = reg.get("search_results", [])
        
        # 국가명을 깔끔하게 정리 (더 정확한 추출)
        clean_country = ""
        if country and country != "알 수 없음":
            # 괄호나 추가 설명 제거
            if '(' in country:
                clean_country = country.split('(')[0].strip()
            elif ':' in country:
                clean_country = country.split(':')[0].strip()
            elif '의' in country:
                clean_country = country.split('의')[0].strip()
            else:
                clean_country = country.strip()
            
            # 일반적인 국가명 패턴 확인
            if len(clean_country) > 20:  # 너무 길면 기본값 사용
                clean_country = "알 수 없음"
        else:
            clean_country = "알 수 없음"
        
        if search_results:
            if clean_country not in country_news:
                country_news[clean_country] = []
            country_news[clean_country].extend(search_results[:2])  # 상위 2개만
    
    # 그룹화된 뉴스 링크를 출력
    for clean_country, news_list in country_news.items():
        if news_list:
            comparison_result += f"**{clean_country} 관련 뉴스:**\n"
            for i, item in enumerate(news_list, 1):
                title = item.title[:80] + "..." if len(item.title) > 80 else item.title
                comparison_result += f"• {i}. [{title}]({item.url})\n"
            comparison_result += "\n"
    
    comparison_result += "---\n\n"
    comparison_result += "**💡 팁**: 위 비교 분석 결과를 바탕으로 특정 국가나 규제에 대해 더 자세한 질문을 해보세요!"
    
    return comparison_result


def show_country_regulation_analysis():
    """국가별 스테이블코인 규제 분석 UI를 표시합니다."""
    
    # Streamlit 세션 상태 초기화
    if "regulation_chat_history" not in st.session_state:
        st.session_state.regulation_chat_history = []
    
    if "regulation_processing" not in st.session_state:
        st.session_state.regulation_processing = False
    
    if "regulation_last_prompt" not in st.session_state:
        st.session_state.regulation_last_prompt = ""
    
    if "analysis_started" not in st.session_state:
        st.session_state.analysis_started = False
    
    # 주요 국가 리스트
    major_countries = [
        "United States", "European Union", "United Kingdom", "Japan", "South Korea", 
        "China", "Singapore", "Switzerland", "Canada", "Australia", "Brazil", "India"
    ]
    
    # 국가 선택
    selected_countries = st.multiselect(
        "국가:",
        options=major_countries,
        default=["United States", "European Union", "Japan"],
        max_selections=3,
        help="최대 3개 국가까지 선택 가능합니다. 주요 금융 중심지 국가들을 선택하면 더 유용한 비교 분석을 얻을 수 있습니다."
    )
    
    # 분석 실행 버튼
    if st.button("비교분석 실행", key="country_comparison", type="secondary", use_container_width=True):
        if len(selected_countries) < 2:
            st.error("최소 2개 국가를 선택해주세요.")
        elif len(selected_countries) > 3:
            st.error("최대 3개 국가까지만 선택 가능합니다.")
        else:
            # 분석 시작 플래그 설정
            st.session_state.analysis_started = True
            
            # 처리 상태 설정
            st.session_state.regulation_processing = True
            
            # 국가별 규제 비교 분석 실행
            with st.spinner(f"{', '.join(selected_countries)}의 스테이블코인 규제를 검색하고 비교 분석하고 있습니다..."):
                try:
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
                    
                    # 처리 완료
                    st.session_state.regulation_processing = False
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"국가별 규제 비교 분석 중 오류가 발생했습니다: {str(e)}"
                    st.error(error_msg)
                    st.session_state.regulation_processing = False
    
    # 채팅 UI (분석이 시작된 후에만 표시)
    if st.session_state.analysis_started:
        
        # 기존 대화 기록 표시
        for message in st.session_state.regulation_chat_history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])
            
        # 새로운 질문 입력 (처리 중이 아닐 때만)
        if not st.session_state.regulation_processing:
            if prompt := st.chat_input("규제 관련 질문을 입력하세요 (예: 미국의 스테이블코인 규제 현황은?)"):
                # 중복 처리 방지
                if prompt != st.session_state.regulation_last_prompt:
                    st.session_state.regulation_last_prompt = prompt
                    st.session_state.regulation_processing = True
                        
                    # 사용자 메시지 추가
                    st.session_state.regulation_chat_history.append({"role": "user", "content": prompt})
                    
                    # AI 답변 생성
                    with st.chat_message("assistant"):
                        with st.spinner("규제 정보를 분석하고 있습니다..."):
                            try:
                                answer = get_regulation_analysis(prompt)
                                st.write(answer)
                                    
                                # AI 답변을 대화 기록에 추가
                                st.session_state.regulation_chat_history.append({"role": "assistant", "content": answer})
                                
                            except Exception as e:
                                error_msg = f"오류가 발생했습니다: {str(e)}"
                                st.error(error_msg)
                                st.session_state.regulation_chat_history.append({"role": "assistant", "content": error_msg})
                    
                    # 처리 완료
                    st.session_state.regulation_processing = False
                    st.rerun()
        
        # 대화 초기화 버튼
        if st.button("대화 초기화", key="regulation_clear", use_container_width=True):
            st.session_state.regulation_chat_history = []
            st.session_state.regulation_processing = False
            st.session_state.regulation_last_prompt = ""
            st.rerun()


# 데모 UI (__main__ 실행 시)
if __name__ == "__main__":
    pass