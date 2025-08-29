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

class StablecoinRegulationAnalysis:
    """
    스테이블코인 규제 분석 시스템
    국가별 규제 동향과 우리나라에 미치는 영향을 분석
    """
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """규제 관련 기본 지식베이스 초기화"""
        # 샘플 규제 데이터 (실제로는 파일에서 로드)
        regulation_data = [
            {
                "country": "미국",
                "regulation": "미국 SEC는 스테이블코인을 증권으로 분류하고 규제를 강화하고 있습니다. 특히 USDT, USDC 등 주요 스테이블코인에 대한 감독을 강화하고 있습니다.",
                "impact": "글로벌 스테이블코인 시장에 큰 영향을 미치며, 다른 국가들의 규제 정책에 영향을 줍니다."
            },
            {
                "country": "EU",
                "regulation": "EU는 MiCA(Markets in Crypto-Assets) 규제를 통해 스테이블코인에 대한 포괄적인 규제 프레임워크를 구축했습니다.",
                "impact": "EU 시장에서의 스테이블코인 사용에 제한을 두며, 글로벌 표준으로 자리잡을 가능성이 있습니다."
            },
            {
                "country": "한국",
                "regulation": "한국은 가상자산업법을 통해 스테이블코인 거래를 규제하고 있으며, 은행의 스테이블코인 발행에 대한 가이드라인을 마련하고 있습니다.",
                "impact": "국내 금융기관의 스테이블코인 사업 진출에 영향을 미치며, 투자자 보호를 강화합니다."
            }
        ]
        
        # 문서 생성
        documents = []
        for reg_data in regulation_data:
            content = f"국가: {reg_data['country']}\n규제: {reg_data['regulation']}\n영향: {reg_data['impact']}"
            documents.append(Document(page_content=content, metadata={"country": reg_data['country']}))
        
        # 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        # Vector DB 생성
        self.vector_store = FAISS.from_documents(splits, self.embeddings)
    
    def get_analysis(self, question: str) -> str:
        """사용자 질문에 대한 규제 분석 생성"""
        try:
            # 규제 관련 검색어 생성
            search_query = f"스테이블코인 규제 {question}"
            
            # Tavily API로 규제 정보 검색
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
            다음은 스테이블코인 규제 분석을 위한 정보입니다.
            
            사용자 질문: {question}
            
            기본 규제 지식:
            {base_knowledge}
            
            최신 뉴스 정보:
            {news_text}
            
            위 정보를 바탕으로 스테이블코인 규제에 대한 분석을 한국어로 작성해주세요.
            특히 우리나라에 미치는 영향과 대응 방안을 포함해주세요.
            """
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            return f"규제 분석 중 오류가 발생했습니다: {str(e)}"

# 전역 인스턴스
_regulation_analysis_instance = None

def get_regulation_analysis(question: str) -> str:
    """스테이블코인 규제 분석에서 답변을 가져오는 함수"""
    global _regulation_analysis_instance
    
    if _regulation_analysis_instance is None:
        _regulation_analysis_instance = StablecoinRegulationAnalysis()
    
    return _regulation_analysis_instance.get_analysis(question)