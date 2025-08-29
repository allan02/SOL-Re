import os
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA
from tavily import TavilyClient
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class StablecoinBusinessAnalysis:
    """
    메이저 금융사 스테이블코인 현황 분석 시스템
    주요 금융사의 스테이블코인 전략과 잠재적 리스크를 분석
    """
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """메이저 금융사 관련 기본 지식베이스 초기화"""
        # 샘플 금융사 데이터 (실제로는 파일에서 로드)
        financial_institutions = [
            {
                "company": "JP모건",
                "strategy": "JPM Coin을 통해 기업간 결제 시스템을 구축하고 있으며, 블록체인 기반의 금융 인프라를 선도하고 있습니다.",
                "risks": "규제 불확실성, 기술적 위험, 경쟁사 대응 등이 주요 리스크 요인입니다.",
                "opportunities": "기업 금융 시장에서의 선도적 위치 확보, 새로운 수익원 창출 가능성이 있습니다."
            },
            {
                "company": "골드만삭스",
                "strategy": "스테이블코인 거래소와의 파트너십을 통해 디지털 자산 서비스를 확장하고 있습니다.",
                "risks": "시장 변동성, 고객 신뢰도, 기술적 복잡성 등이 리스크 요인입니다.",
                "opportunities": "기존 고객 기반을 활용한 디지털 자산 서비스 확장이 가능합니다."
            },
            {
                "company": "바클레이즈",
                "strategy": "스테이블코인 결제 시스템을 통해 국제 송금 서비스를 개선하고 있습니다.",
                "risks": "국제 규제 환경의 복잡성, 환율 변동성 등이 주요 리스크입니다.",
                "opportunities": "글로벌 송금 시장에서의 경쟁력 강화, 수수료 수익 증대가 가능합니다."
            }
        ]
        
        # 문서 생성
        documents = []
        for fi_data in financial_institutions:
            content = f"회사: {fi_data['company']}\n전략: {fi_data['strategy']}\n리스크: {fi_data['risks']}\n기회: {fi_data['opportunities']}"
            documents.append(Document(page_content=content, metadata={"company": fi_data['company']}))
        
        # 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        # Vector DB 생성
        self.vector_store = FAISS.from_documents(splits, self.embeddings)
    
    def get_analysis(self, question: str) -> str:
        """사용자 질문에 대한 비즈니스 분석 생성"""
        try:
            # 금융사 관련 검색어 생성
            search_query = f"금융사 스테이블코인 {question}"
            
            # Tavily API로 비즈니스 정보 검색
            search_results = self.tavily_client.search(
                query=search_query,
                search_depth="basic",
                max_results=5
            )
            
            # 기본 지식베이스에서 관련 정보 검색
            base_knowledge = ""
            try:
                docs = self.vector_store.similarity_search(question, k=3)
                base_knowledge = "\n".join([doc.page_content for doc in docs])
            except Exception as e:
                base_knowledge = f"기본 지식 검색 오류: {str(e)}"
            
            # 검색 결과를 텍스트로 변환
            news_text = ""
            if search_results.get("results"):
                for result in search_results["results"]:
                    news_text += f"제목: {result.get('title', 'N/A')}\n"
                    news_text += f"내용: {result.get('content', 'N/A')}\n"
                    news_text += f"URL: {result.get('url', 'N/A')}\n\n"
            
            # LLM을 사용하여 답변 생성
            prompt = f"""
            다음은 메이저 금융사의 스테이블코인 비즈니스 분석을 위한 정보입니다.
            
            사용자 질문: {question}
            
            기본 비즈니스 지식:
            {base_knowledge}
            
            최신 뉴스 정보:
            {news_text}
            
            위 정보를 바탕으로 메이저 금융사의 스테이블코인 전략과 잠재적 리스크를 분석해주세요.
            특히 신한은행에 대한 시사점과 액션 아이템을 포함해주세요.
            """
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            return f"비즈니스 분석 중 오류가 발생했습니다: {str(e)}"

# 전역 인스턴스
_business_analysis_instance = None

def get_business_analysis(question: str) -> str:
    """스테이블코인 비즈니스 분석에서 답변을 가져오는 함수"""
    global _business_analysis_instance
    
    if _business_analysis_instance is None:
        _business_analysis_instance = StablecoinBusinessAnalysis()
    
    return _business_analysis_instance.get_analysis(question)