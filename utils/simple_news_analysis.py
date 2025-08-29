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

class StablecoinNewsAnalysis:
    """
    스테이블코인 뉴스 조회 및 QA 서비스
    Tavily API를 활용하여 외부 뉴스를 조회하고 사용자 질문에 답변
    """
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    def get_answer(self, question: str) -> str:
        """사용자 질문에 대한 뉴스 기반 답변 생성"""
        try:
            # 스테이블코인 관련 검색어 생성
            search_query = f"스테이블코인 {question}"
            
            # Tavily API로 뉴스 검색
            search_results = self.tavily_client.search(
                query=search_query,
                search_depth="basic",
                max_results=5
            )
            
            if not search_results.get("results"):
                return "뉴스 검색 결과를 찾을 수 없습니다."
            
            # 검색 결과를 텍스트로 변환
            news_text = ""
            for result in search_results["results"]:
                news_text += f"제목: {result.get('title', 'N/A')}\n"
                news_text += f"내용: {result.get('content', 'N/A')}\n"
                news_text += f"URL: {result.get('url', 'N/A')}\n\n"
            
            # LLM을 사용하여 답변 생성
            prompt = f"""
            다음은 스테이블코인 관련 뉴스 검색 결과입니다.
            
            사용자 질문: {question}
            
            뉴스 내용:
            {news_text}
            
            위 뉴스 내용을 바탕으로 사용자 질문에 대한 답변을 한국어로 작성해주세요.
            답변은 객관적이고 정확해야 하며, 필요시 출처를 명시해주세요.
            """
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            return f"뉴스 분석 중 오류가 발생했습니다: {str(e)}"

# 전역 인스턴스
_news_analysis_instance = None

def get_news_answer(question: str) -> str:
    """스테이블코인 뉴스 분석에서 답변을 가져오는 함수"""
    global _news_analysis_instance
    
    if _news_analysis_instance is None:
        _news_analysis_instance = StablecoinNewsAnalysis()
    
    return _news_analysis_instance.get_answer(question)