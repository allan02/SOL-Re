import os
import json
import urllib.request
import urllib.parse
import time
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class StablecoinDictionary:
    """
    스테이블코인 용어 백과사전 RAG 시스템
    stablecoin_book_2025_full.md 파일 기반으로 vector db를 구축하고 사용자 질문에 답변
    백과사전에 없는 내용은 인터넷 검색으로 보완
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
    
    def _load_markdown_content(self) -> List[Document]:
        """stablecoin_book_2025_full.md 파일을 구조화된 문서로 로드"""
        try:
            file_path = os.path.join(os.path.dirname(__file__), "stablecoin_book_2025_full.md")
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # 마크다운을 구조화된 섹션으로 분할
            documents = []
            
            # 섹션별로 분할 (## 기준)
            sections = content.split('## ')
            
            for i, section in enumerate(sections):
                if i == 0:  # 첫 번째 섹션 (제목)
                    if section.strip():
                        title = section.strip().replace('# ', '').replace('\n', ' ').strip()
                        documents.append(Document(
                            page_content=section.strip(),
                            metadata={
                                "source": "stablecoin_book_2025_full.md",
                                "section": "title",
                                "title": title,
                                "section_index": i
                            }
                        ))
                else:
                    # 섹션 제목과 내용 분리
                    lines = section.strip().split('\n')
                    if lines:
                        section_title = lines[0].strip()
                        section_content = '\n'.join(lines[1:]).strip()
                        
                        if section_content:
                            # 용어별로 추가 분할 (볼드 텍스트 기준)
                            terms = self._extract_terms_from_section(section_content)
                            
                            if terms:
                                # 각 용어를 개별 문서로 생성
                                for term_data in terms:
                                    documents.append(Document(
                                        page_content=f"섹션: {section_title}\n용어: {term_data['term']}\n정의: {term_data['definition']}\n예시: {term_data['examples']}",
                                        metadata={
                                            "source": "stablecoin_book_2025_full.md",
                                            "section": section_title,
                                            "term": term_data['term'],
                                            "section_index": i,
                                            "term_type": term_data.get('type', 'general')
                                        }
                                    ))
                            else:
                                # 용어가 없는 경우 섹션 전체를 문서로 생성
                                documents.append(Document(
                                    page_content=f"섹션: {section_title}\n내용: {section_content}",
                                    metadata={
                                        "source": "stablecoin_book_2025_full.md",
                                        "section": section_title,
                                        "section_index": i,
                                        "term_type": "section_content"
                                    }
                                ))
            
            return documents
            
        except Exception as e:
            print(f"마크다운 파일 로드 중 오류: {e}")
            return []
    
    def _extract_terms_from_section(self, section_content: str) -> List[Dict[str, Any]]:
        """섹션 내용에서 용어와 정의를 추출"""
        terms = []
        
        # 줄 단위로 처리
        lines = section_content.split('\n')
        current_term = None
        current_definition = []
        current_examples = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 볼드 텍스트로 된 용어 찾기
            if line.startswith('- **') and line.endswith('**'):
                # 이전 용어 저장
                if current_term and current_definition:
                    terms.append({
                        'term': current_term,
                        'definition': ' '.join(current_definition),
                        'examples': current_examples,
                        'type': 'definition'
                    })
                
                # 새 용어 시작
                current_term = line[4:-3].strip()  # - **용어** 에서 용어 부분 추출
                current_definition = []
                current_examples = []
                
            elif line.startswith('- **') and '**' in line:
                # 용어와 정의가 한 줄에 있는 경우
                parts = line.split('**')
                if len(parts) >= 3:
                    term = parts[1].strip()
                    definition = parts[2].strip()
                    if definition.startswith(':'):
                        definition = definition[1:].strip()
                    
                    terms.append({
                        'term': term,
                        'definition': definition,
                        'examples': [],
                        'type': 'inline_definition'
                    })
                    
            elif current_term and line.startswith('  - '):
                # 예시 항목
                example = line[4:].strip()
                current_examples.append(example)
                
            elif current_term and line.startswith('- '):
                # 정의 항목
                definition = line[2:].strip()
                current_definition.append(definition)
                
            elif current_term and not line.startswith('  - ') and not line.startswith('- '):
                # 일반 텍스트 (정의의 일부)
                current_definition.append(line)
        
        # 마지막 용어 저장
        if current_term and current_definition:
            terms.append({
                'term': current_term,
                'definition': ' '.join(current_definition),
                'examples': current_examples,
                'type': 'definition'
            })
        
        return terms
    
    def _initialize_knowledge_base(self):
        """스테이블코인 용어 백과사전 지식베이스 초기화"""
        print("🔄 스테이블코인 용어 백과사전 지식베이스 초기화 중...")
        
        # 마크다운 파일을 구조화된 문서로 로드
        documents = self._load_markdown_content()
        
        if not documents:
            print("⚠️ 마크다운 파일을 로드할 수 없습니다. 샘플 데이터를 사용합니다.")
            # 폴백: 샘플 데이터 사용
            sample_docs = [
                Document(
                    page_content="용어: 스테이블코인\n정의: 가격 변동성을 최소화하기 위해 특정 자산에 가치를 고정한 암호화폐\n예시: USDT, USDC, DAI",
                    metadata={"source": "sample", "term": "스테이블코인", "section": "기본 용어"}
                ),
                Document(
                    page_content="용어: USDT\n정의: 테더사에서 발행하는 1:1 USD 페깅 스테이블코인\n예시: 거래소 거래, 송금, 결제",
                    metadata={"source": "sample", "term": "USDT", "section": "기본 용어"}
                )
            ]
            documents = sample_docs
        
        print(f"📚 총 {len(documents)}개의 문서를 로드했습니다.")
        
        # 텍스트 분할 (더 작은 청크로 분할하여 정확도 향상)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # 더 작은 청크로 변경
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        splits = text_splitter.split_documents(documents)
        
        print(f"✂️ 텍스트를 {len(splits)}개의 청크로 분할했습니다.")
        
        # Vector DB 생성
        print("🔍 FAISS 벡터 데이터베이스 생성 중...")
        self.vector_store = FAISS.from_documents(splits, self.embeddings)
        
        # QA 체인 생성 (새로운 방식 사용)
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 8})
        
        # 프롬프트 템플릿 정의
        prompt_template = """
        다음은 스테이블코인 용어 백과사전에 대한 질문입니다.
        질문: {question}
        
        제공된 정보를 바탕으로 정확하고 이해하기 쉬운 답변을 제공해주세요.
        답변은 한국어로 작성하고, 필요시 예시를 포함해주세요.
        
        컨텍스트: {context}
        """
        
        # 새로운 체인 생성
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PromptTemplate.from_template(prompt_template)}
        )
        
        print("✅ 스테이블코인 용어 백과사전 지식베이스 초기화 완료!")
        
        # 통계 정보 출력
        self._print_statistics()
    
    def _print_statistics(self):
        """벡터 DB 통계 정보 출력"""
        try:
            if self.vector_store:
                # 카테고리별 용어 수 집계
                categories = {}
                sample_queries = ["스테이블코인", "블록체인", "규제", "기술", "시장", "DeFi", "CBDC"]
                
                for query in sample_queries:
                    docs = self.vector_store.similarity_search(query, k=10)
                    for doc in docs:
                        section = doc.metadata.get('section', '기타')
                        if section not in categories:
                            categories[section] = 0
                        if doc.metadata.get('term'):
                            categories[section] += 1
                
                print("\n📊 백과사전 통계:")
                for category, count in sorted(categories.items()):
                    if count > 0:
                        print(f"  • {category}: {count}개 용어")
                
                print(f"  • 총 문서 수: {len(self.vector_store.docstore._dict)}")
                
        except Exception as e:
            print(f"통계 정보 출력 중 오류: {e}")
    
    def _search_internet(self, query: str) -> str:
        """인터넷에서 스테이블코인 관련 정보 검색"""
        try:
            # Tavily 우선 사용 (유일한 외부 검색 API)
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                return self._tavily_search(query)
            
            # Tavily API 키 미설정 시 알림 반환
            return "Tavily API 키가 설정되어 있지 않습니다. 환경 변수 TAVILY_API_KEY를 설정해주세요."
            
        except Exception as e:
            return f"인터넷 검색 중 오류가 발생했습니다: {str(e)}"
    
    def _tavily_search(self, query: str) -> str:
        """Tavily Search API를 사용한 웹 검색"""
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if not tavily_api_key:
                return "Tavily API 키가 설정되어 있지 않습니다. 환경 변수 TAVILY_API_KEY를 설정해주세요."
            
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": tavily_api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True,
                "include_images": False
            }
            data = json.dumps(payload).encode("utf-8")
            
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            
            # 결과 정리
            parts = []
            if result.get("answer"):
                parts.append(result["answer"])
            sources = result.get("results", [])
            if sources:
                formatted_sources = []
                for item in sources[:5]:
                    title = item.get("title") or item.get("url") or "출처"
                    url_src = item.get("url", "")
                    snippet = item.get("content", "")
                    if snippet:
                        snippet = snippet[:180] + ("..." if len(snippet) > 180 else "")
                    formatted_sources.append(f"- {title} ({url_src})\n  요약: {snippet}")
                parts.append("\n참고 출처:\n" + "\n".join(formatted_sources))
            
            return "\n\n".join(parts) if parts else "웹 검색 결과를 찾기 어려웠습니다."
        except Exception as e:
            return f"Tavily 검색 중 오류: {str(e)}"
    
    def _check_knowledge_coverage(self, question: str, answer: str) -> bool:
        """답변이 지식베이스에서 충분히 도출되었는지 확인"""
        # 간단한 품질 체크: 답변이 너무 짧거나 일반적인 경우
        if len(answer) < 50:
            return False
        
        # 사과/정보부족 표현이 포함된 경우
        low_confidence_phrases = [
            "모르겠습니다", "찾을 수 없습니다", "정보가 부족합니다",
            "알 수 없습니다", "확실하지 않습니다",
            "제공된 정보에는", "제공받은 정보에는", "포함되어 있지 않습니다",
            "해당 정보를 제공할 수 없습니다"
        ]
        
        for phrase in low_confidence_phrases:
            if phrase in answer:
                return False
        
        return True
    
    def _is_in_knowledge_base(self, question: str) -> bool:
        """질문이 지식베이스에 있는 내용인지 빠르게 확인"""
        try:
            if not self.vector_store:
                return False
            
            # 빠른 검색으로 관련 문서 확인 (k=2로 줄여서 속도 향상)
            docs = self.vector_store.similarity_search(question, k=2)
            
            # 검색된 문서의 메타데이터 확인
            for doc in docs:
                metadata = doc.metadata
                # stablecoin_book_2025_full.md에서 온 문서인지 확인
                if (metadata.get('source') == 'stablecoin_book_2025_full.md' and 
                    metadata.get('term') and 
                    len(doc.page_content) > 100):  # 충분한 내용이 있는 문서
                    return True
            
            return False
            
        except Exception as e:
            print(f"지식베이스 확인 중 오류: {e}")
            return False
    
    def get_fast_answer(self, question: str) -> str:
        """빠른 답변을 위한 최적화된 함수 (DB에 있는 내용인 경우)"""
        start_time = time.time()
        
        try:
            # 지식베이스에 있는 내용인지 빠르게 확인
            is_in_kb = self._is_in_knowledge_base(question)
            
            if is_in_kb:
                # DB에 있는 내용인 경우 - 최적화된 프롬프트로 빠른 답변
                fast_prompt = f"""
                질문: {question}
                
                위 질문에 대해 백과사전의 정보를 바탕으로 간결하고 정확하게 답변해주세요.
                답변은 한국어로 작성하고, 핵심 내용 위주로 작성해주세요.
                """
                
                # 빠른 검색을 위해 k=3으로 제한
                result = self.qa_chain({"query": fast_prompt})
                answer = result["result"]
                
                response_time = time.time() - start_time
                print(f"⚡ 빠른 답변 완료 (응답시간: {response_time:.2f}초)")
                
                return answer
            else:
                # DB에 없는 내용인 경우 일반 함수 호출
                return self.get_answer(question)
                
        except Exception as e:
            response_time = time.time() - start_time
            print(f"❌ 빠른 답변 오류 (응답시간: {response_time:.2f}초)")
            return f"빠른 답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    def get_answer(self, question: str) -> str:
        """사용자 질문에 대한 답변 생성"""
        start_time = time.time()
        
        try:
            # 먼저 지식베이스에 있는 내용인지 빠르게 확인
            is_in_kb = self._is_in_knowledge_base(question)
            
            if not is_in_kb:
                # KB에 없으면 즉시 웹 검색 경로로 전환
                internet_result = self._search_internet(question)
                enhanced_prompt = f"""
                다음 질문에 대해 답변해주세요:
                질문: {question}
                
                인터넷 검색 결과: {internet_result}
                
                위 정보를 종합하여 사실 기반으로 명확하고 간결하게 답변하세요.
                답변은 한국어로 작성하고, 사과나 '정보가 없습니다'와 같은 표현은 사용하지 마세요.
                필요한 경우 핵심 출처 링크를 함께 제시하세요.
                """
                enhanced_result = self.qa_chain({"query": enhanced_prompt})
                response_time = time.time() - start_time
                print(f"🌐 인터넷 검색 기반 답변 완료 (응답시간: {response_time:.2f}초)")
                return enhanced_result['result']
            
            # 프롬프트 템플릿 (KB에 있는 경우)
            prompt = f"""
            다음은 스테이블코인 용어 백과사전에 대한 질문입니다.
            질문: {question}
            
            제공된 정보를 바탕으로 정확하고 이해하기 쉬운 답변을 제공해주세요.
            답변은 한국어로 작성하고, 필요시 예시를 포함해주세요.
            이 질문은 백과사전에 포함된 내용이므로 상세하고 정확한 답변을 제공해주세요.
            """
            
            # QA 체인 실행
            result = self.qa_chain({"query": prompt})
            answer = result["result"]
            
            # 지식베이스에서 충분한 정보를 얻었는지 확인
            if self._check_knowledge_coverage(question, answer):
                response_time = time.time() - start_time
                print(f"💾 DB 답변 완료 (응답시간: {response_time:.2f}초)")
                return answer
            else:
                # 인터넷 검색으로 보완
                internet_result = self._search_internet(question)
                enhanced_prompt = f"""
                다음 질문에 대해 답변해주세요:
                질문: {question}
                
                인터넷 검색 결과: {internet_result}
                
                위 정보를 종합하여 사실 기반으로 명확하고 간결하게 답변하세요.
                답변은 한국어로 작성하고, 사과나 '정보가 없습니다'와 같은 표현은 사용하지 마세요.
                필요한 경우 핵심 출처 링크를 함께 제시하세요.
                """
                enhanced_result = self.qa_chain({"query": enhanced_prompt})
                response_time = time.time() - start_time
                print(f"🌐 인터넷 검색 보완 답변 완료 (응답시간: {response_time:.2f}초)")
                return enhanced_result["result"]
            
        except Exception as e:
            response_time = time.time() - start_time
            print(f"❌ 답변 생성 오류 (응답시간: {response_time:.2f}초)")
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    def get_similar_terms(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """유사한 용어 검색"""
        try:
            if not self.vector_store:
                return []
            
            # 유사도 검색
            docs = self.vector_store.similarity_search(query, k=top_k)
            
            similar_terms = []
            for doc in docs:
                # 메타데이터에서 용어 정보 추출
                metadata = doc.metadata
                content = doc.page_content
                
                if metadata.get('term'):
                    # 용어가 있는 경우
                    similar_terms.append({
                        "term": metadata['term'],
                        "section": metadata.get('section', ''),
                        "content": content[:300] + "..." if len(content) > 300 else content,
                        "similarity_score": 0.9,
                        "term_type": metadata.get('term_type', 'general')
                    })
                elif "**" in content:
                    # 마크다운 볼드 텍스트에서 용어 추출
                    start = content.find("**") + 2
                    end = content.find("**", start)
                    if end > start:
                        term = content[start:end].strip()
                        similar_terms.append({
                            "term": term,
                            "section": metadata.get('section', ''),
                            "content": content[:300] + "..." if len(content) > 300 else content,
                            "similarity_score": 0.8,
                            "term_type": metadata.get('term_type', 'general')
                        })
            
            # 중복 제거 및 정렬
            unique_terms = []
            seen_terms = set()
            for term_data in similar_terms:
                if term_data['term'] not in seen_terms:
                    unique_terms.append(term_data)
                    seen_terms.add(term_data['term'])
            
            return unique_terms[:top_k]
            
        except Exception as e:
            print(f"유사 용어 검색 중 오류: {e}")
            return []
    
    def search_terms_by_category(self, category: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """카테고리별 용어 검색"""
        try:
            if not self.vector_store:
                return []
            
            # 카테고리 관련 검색
            query = f"섹션: {category}"
            docs = self.vector_store.similarity_search(query, k=top_k)
            
            category_terms = []
            for doc in docs:
                metadata = doc.metadata
                if metadata.get('section') == category and metadata.get('term'):
                    category_terms.append({
                        "term": metadata['term'],
                        "section": metadata['section'],
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "term_type": metadata.get('term_type', 'general')
                    })
            
            return category_terms
            
        except Exception as e:
            print(f"카테고리별 용어 검색 중 오류: {e}")
            return []
    
    def get_term_details(self, term: str) -> Dict[str, Any]:
        """특정 용어의 상세 정보 조회"""
        try:
            if not self.vector_store:
                return {}
            
            # 정확한 용어 검색
            query = f"용어: {term}"
            docs = self.vector_store.similarity_search(query, k=3)
            
            for doc in docs:
                metadata = doc.metadata
                if metadata.get('term') == term:
                    return {
                        "term": term,
                        "section": metadata.get('section', ''),
                        "definition": doc.page_content,
                        "term_type": metadata.get('term_type', 'general'),
                        "source": metadata.get('source', '')
                    }
            
            return {}
            
        except Exception as e:
            print(f"용어 상세 정보 조회 중 오류: {e}")
            return {}
    
    def get_all_categories(self) -> List[str]:
        """모든 카테고리(섹션) 목록 조회"""
        try:
            if not self.vector_store:
                return []
            
            # 모든 문서의 메타데이터에서 섹션 정보 수집
            categories = set()
            
            # 벡터 스토어에서 모든 문서의 메타데이터에 접근
            # FAISS는 직접적인 메타데이터 접근이 제한적이므로
            # 대신 샘플 검색을 통해 카테고리 정보 수집
            sample_queries = ["스테이블코인", "블록체인", "규제", "기술", "시장"]
            
            for query in sample_queries:
                docs = self.vector_store.similarity_search(query, k=5)
                for doc in docs:
                    if doc.metadata.get('section'):
                        categories.add(doc.metadata['section'])
            
            return sorted(list(categories))
            
        except Exception as e:
            print(f"카테고리 목록 조회 중 오류: {e}")
            return []

# 전역 인스턴스
_dictionary_instance = None

def get_dictionary_answer(question: str) -> str:
    """스테이블코인 용어 백과사전에서 답변을 가져오는 함수"""
    global _dictionary_instance
    
    if _dictionary_instance is None:
        _dictionary_instance = StablecoinDictionary()
    
    return _dictionary_instance.get_answer(question)

def get_fast_dictionary_answer(question: str) -> str:
    """스테이블코인 용어 백과사전에서 빠른 답변을 가져오는 함수 (DB에 있는 내용인 경우)"""
    global _dictionary_instance
    
    if _dictionary_instance is None:
        _dictionary_instance = StablecoinDictionary()
    
    return _dictionary_instance.get_fast_answer(question)

def get_similar_terms(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """유사한 용어를 검색하는 함수"""
    global _dictionary_instance
    
    if _dictionary_instance is None:
        _dictionary_instance = StablecoinDictionary()
    
    return _dictionary_instance.get_similar_terms(query, top_k)

def search_terms_by_category(category: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """카테고리별 용어를 검색하는 함수"""
    global _dictionary_instance
    
    if _dictionary_instance is None:
        _dictionary_instance = StablecoinDictionary()
    
    return _dictionary_instance.search_terms_by_category(category, top_k)

def get_term_details(term: str) -> Dict[str, Any]:
    """특정 용어의 상세 정보를 조회하는 함수"""
    global _dictionary_instance
    
    if _dictionary_instance is None:
        _dictionary_instance = StablecoinDictionary()
    
    return _dictionary_instance.get_term_details(term)

def get_all_categories() -> List[str]:
    """모든 카테고리 목록을 조회하는 함수"""
    global _dictionary_instance
    
    if _dictionary_instance is None:
        _dictionary_instance = StablecoinDictionary()
    
    return _dictionary_instance.get_all_categories()

def is_question_in_kb(question: str) -> bool:
    """질문이 KB(stablecoin_book_2025_full.md) 범위인지 공개 함수로 제공"""
    global _dictionary_instance
    if _dictionary_instance is None:
        _dictionary_instance = StablecoinDictionary()
    return _dictionary_instance._is_in_knowledge_base(question)