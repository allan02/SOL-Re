import os
import json
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class StablecoinDictionary:
    """
    스테이블코인 용어 백과사전 RAG 시스템
    자체 파일 기반으로 vector db를 구축하고 사용자 질문에 답변
    """
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.vector_store = None
        self.qa_chain = None
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """스테이블코인 용어 백과사전 지식베이스 초기화"""
        # 샘플 스테이블코인 용어 데이터 (실제로는 파일에서 로드)
        stablecoin_terms = [
            {
                "term": "스테이블코인",
                "definition": "스테이블코인은 가격 변동성을 최소화하기 위해 특정 자산이나 자산 바스켓에 가치를 고정(페깅)한 암호화폐입니다. 주로 법정화폐, 상품, 다른 암호화폐 등에 가치를 고정합니다.",
                "examples": ["USDT", "USDC", "DAI", "BUSD"]
            },
            {
                "term": "USDT (Tether)",
                "definition": "테더(USDT)는 가장 널리 사용되는 스테이블코인 중 하나로, 1 USDT = 1 USD로 고정되어 있습니다. 테더사에서 발행하며, 미국 달러에 1:1로 백업됩니다.",
                "examples": ["거래소 거래", "송금", "결제"]
            },
            {
                "term": "USDC (USD Coin)",
                "definition": "USD 코인(USDC)은 Circle과 Coinbase가 공동으로 개발한 스테이블코인입니다. 미국 달러에 1:1로 고정되며, 정기적인 감사를 통해 투명성을 보장합니다.",
                "examples": ["DeFi 프로토콜", "NFT 거래", "크로스체인 거래"]
            },
            {
                "term": "DAI",
                "definition": "DAI는 이더리움 블록체인 기반의 탈중앙화 스테이블코인입니다. MakerDAO 프로토콜을 통해 관리되며, 담보를 통해 가치가 유지됩니다.",
                "examples": ["DeFi 대출", "유동성 제공", "스마트 컨트랙트"]
            },
            {
                "term": "페깅 (Pegging)",
                "definition": "페깅은 스테이블코인의 가치를 특정 자산(보통 법정화폐)에 고정하는 메커니즘입니다. 이를 통해 가격 안정성을 유지합니다.",
                "examples": ["1:1 페깅", "부분 페깅", "알고리즘 페깅"]
            }
        ]
        
        # 문서 생성
        documents = []
        for term_data in stablecoin_terms:
            content = f"용어: {term_data['term']}\n정의: {term_data['definition']}\n예시: {', '.join(term_data['examples'])}"
            documents.append(Document(page_content=content, metadata={"term": term_data['term']}))
        
        # 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        # Vector DB 생성
        self.vector_store = FAISS.from_documents(splits, self.embeddings)
        
        # QA 체인 생성
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
    
    def get_answer(self, question: str) -> str:
        """사용자 질문에 대한 답변 생성"""
        try:
            # 프롬프트 템플릿
            prompt = f"""
            다음은 스테이블코인 용어 백과사전에 대한 질문입니다.
            질문: {question}
            
            제공된 정보를 바탕으로 정확하고 이해하기 쉬운 답변을 제공해주세요.
            답변은 한국어로 작성하고, 필요시 예시를 포함해주세요.
            """
            
            # QA 체인 실행
            result = self.qa_chain({"query": prompt})
            
            return result["result"]
            
        except Exception as e:
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"

# 전역 인스턴스
_dictionary_instance = None

def get_dictionary_answer(question: str) -> str:
    """스테이블코인 용어 백과사전에서 답변을 가져오는 함수"""
    global _dictionary_instance
    
    if _dictionary_instance is None:
        _dictionary_instance = StablecoinDictionary()
    
    return _dictionary_instance.get_answer(question)