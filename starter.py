import streamlit as st
import hashlib
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import ChatMessage

from dotenv import load_dotenv

load_dotenv()

# 내장 라이브러리만 사용한 웹 API 클래스
class BuiltinWebAPI:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def make_request(self, url, headers=None, params=None):
        """urllib을 사용한 HTTP 요청"""
        try:
            # URL에 파라미터 추가
            if params:
                url += '?' + urllib.parse.urlencode(params)
            
            # 요청 객체 생성
            req = urllib.request.Request(url)
            req.add_header('User-Agent', self.user_agent)
            
            # 추가 헤더 설정
            if headers:
                for key, value in headers.items():
                    req.add_header(key, value)
            
            # 요청 실행
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
                
        except Exception as e:
            return {'error': str(e)}
    
    def get_weather_info(self, city="서울"):
        """날씨 정보 조회 (공개 API)"""
        try:
            # OpenWeatherMap API (무료)
            api_key = "your_api_key"  # 실제 사용시 API 키 필요
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': city,
                'appid': api_key,
                'units': 'metric',
                'lang': 'kr'
            }
            
            # API 키가 없으면 시뮬레이션 데이터 반환
            if api_key == "your_api_key":
                return {
                    'success': True,
                    'city': city,
                    'temperature': '22°C',
                    'description': '맑음',
                    'humidity': '65%',
                    'source': '시뮬레이션 데이터'
                }
            
            return self.make_request(url, params=params)
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_exchange_rate(self):
        """환율 정보 조회 (공개 API)"""
        try:
            # 무료 환율 API
            url = "https://api.exchangerate-api.com/v4/latest/KRW"
            data = self.make_request(url)
            
            if 'error' not in data:
                return {
                    'success': True,
                    'rates': data.get('rates', {}),
                    'base': data.get('base', 'KRW'),
                    'date': data.get('date', ''),
                    'source': '실시간 API'
                }
            else:
                # API 오류시 시뮬레이션 데이터
                return {
                    'success': True,
                    'rates': {'USD': 0.00075, 'EUR': 0.00069, 'JPY': 0.11},
                    'base': 'KRW',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'source': '시뮬레이션 데이터'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_news_info(self, keyword="부동산"):
        """뉴스 정보 조회 (시뮬레이션)"""
        try:
            # 실제로는 뉴스 API 사용 가능
            news_data = {
                "부동산": [
                    {"title": "서울 아파트 가격 상승세", "summary": "서울 아파트 가격이 전월 대비 0.5% 상승"},
                    {"title": "부동산 정책 변화", "summary": "정부, 부동산 규제 완화 검토"}
                ],
                "경제": [
                    {"title": "금리 인하 기대감", "summary": "한국은행 금리 인하 가능성 높아짐"},
                    {"title": "주식시장 상승", "summary": "코스피 지수 상승세 지속"}
                ]
            }
            
            return {
                'success': True,
                'keyword': keyword,
                'news': news_data.get(keyword, news_data["부동산"]),
                'source': '시뮬레이션 데이터'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_market_data(self, region="서울"):
        """부동산 시장 데이터 (시뮬레이션)"""
        try:
            market_data = {
                "서울": {
                    "avg_price": "1,200만원/㎡",
                    "trend": "상승",
                    "volume": "증가",
                    "interest_rate": "3.5%"
                },
                "부산": {
                    "avg_price": "800만원/㎡",
                    "trend": "안정",
                    "volume": "유지",
                    "interest_rate": "3.2%"
                },
                "대구": {
                    "avg_price": "700만원/㎡",
                    "trend": "하락",
                    "volume": "감소",
                    "interest_rate": "3.3%"
                }
            }
            
            return {
                'success': True,
                'region': region,
                'data': market_data.get(region, market_data["서울"]),
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'source': '시뮬레이션 데이터'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# 전역 API 인스턴스
if 'builtin_api' not in st.session_state:
    st.session_state.builtin_api = BuiltinWebAPI()

# Q&A 전용 캐시 시스템
class QACache:
    def __init__(self):
        self.qa_cache = {}  # Q&A 쌍 저장
        self.stats = {
            'hits': 0,      # 캐시 히트 횟수
            'misses': 0,    # 캐시 미스 횟수
            'saves': 0      # 캐시 저장 횟수
        }
    
    def get(self, question, context_id=None):
        """질문과 컨텍스트 ID로 답변 조회"""
        cache_key = self._generate_key(question, context_id)
        
        if cache_key in self.qa_cache:
            data, expire_time = self.qa_cache[cache_key]
            if datetime.now() < expire_time:
                self.stats['hits'] += 1
                return data
            else:
                del self.qa_cache[cache_key]
        
        self.stats['misses'] += 1
        return None
    
    def set(self, question, answer, context_id=None, expire_seconds=3600):
        """질문-답변 쌍을 캐시에 저장"""
        cache_key = self._generate_key(question, context_id)
        expire_time = datetime.now() + timedelta(seconds=expire_seconds)
        
        cache_data = {
            'question': question,
            'answer': answer,
            'context_id': context_id,
            'timestamp': str(datetime.now()),
            'expire_time': str(expire_time)
        }
        
        self.qa_cache[cache_key] = (cache_data, expire_time)
        self.stats['saves'] += 1
    
    def _generate_key(self, question, context_id=None):
        """질문과 컨텍스트를 기반으로 캐시 키 생성"""
        key_data = {
            'question': question.lower().strip(),
            'context_id': context_id or 'default'
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def clear_expired(self):
        """만료된 캐시 정리"""
        current_time = datetime.now()
        expired_keys = [key for key, (_, expire_time) in self.qa_cache.items() 
                       if current_time >= expire_time]
        for key in expired_keys:
            del self.qa_cache[key]
    
    def get_stats(self):
        """캐시 통계 반환"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'saves': self.stats['saves'],
            'hit_rate': round(hit_rate, 2),
            'cache_size': len(self.qa_cache)
        }
    
    def clear_all(self):
        """모든 캐시 삭제"""
        self.qa_cache.clear()
        self.stats = {'hits': 0, 'misses': 0, 'saves': 0}

# 전역 Q&A 캐시 인스턴스
if 'qa_cache' not in st.session_state:
    st.session_state.qa_cache = QACache()

# 메모리 기반 캐시 (Redis 대신)
class MemoryCache:
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        if key in self.cache:
            data, expire_time = self.cache[key]
            if datetime.now() < expire_time:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value, expire_seconds=3600):
        expire_time = datetime.now() + timedelta(seconds=expire_seconds)
        self.cache[key] = (value, expire_time)
    
    def clear_expired(self):
        current_time = datetime.now()
        expired_keys = [key for key, (_, expire_time) in self.cache.items() 
                       if current_time >= expire_time]
        for key in expired_keys:
            del self.cache[key]

# 전역 캐시 인스턴스
if 'memory_cache' not in st.session_state:
    st.session_state.memory_cache = MemoryCache()

# Query Rewriting 클래스
class QueryRewriter:
    def __init__(self):
        self.rewriting_patterns = {
            # 일반적인 질문 패턴
            "괜찮아": "이 계약의 주요 조건과 위험 요소는 무엇인가요?",
            "어때": "이 계약의 장단점과 주의사항은 무엇인가요?",
            "좋아": "이 계약의 유리한 점과 불리한 점은 무엇인가요?",
            
            # 가격 관련
            "비싸": "이 계약의 가격이 시장 가격 대비 적정한가요?",
            "싸": "이 계약의 가격이 시장 가격 대비 저렴한가요?",
            "가격": "이 계약의 가격 조건과 시장 비교는 어떠한가요?",
            
            # 조건 관련
            "조건": "이 계약의 주요 조건들을 분석해주세요",
            "기간": "이 계약의 기간 조건이 적절한가요?",
            "보증금": "보증금 조건이 합리적인가요?",
            
            # 위험 관련
            "위험": "이 계약의 주요 위험 요소는 무엇인가요?",
            "주의": "이 계약에서 주의해야 할 점은 무엇인가요?",
            "문제": "이 계약의 잠재적 문제점은 무엇인가요?"
        }
        
        # 부동산 전문 용어 매핑
        self.real_estate_terms = {
            "월세": "월세 조건",
            "전세": "전세 조건", 
            "매매": "매매 조건",
            "임대": "임대 조건",
            "등기": "등기부등본",
            "특약": "특약사항",
            "중개": "중개수수료",
            "등록": "등록세",
            "취득": "취득세"
        }
    
    def rewrite_query(self, original_query: str) -> dict:
        """질문을 재구성하여 더 정확한 검색을 위한 쿼리 생성"""
        try:
            # 1. 기본 정보 추출
            query_info = {
                'original': original_query,
                'rewritten': original_query,
                'keywords': [],
                'intent': 'general',
                'confidence': 1.0
            }
            
            # 2. 키워드 추출
            query_info['keywords'] = self._extract_keywords(original_query)
            
            # 3. 의도 파악
            query_info['intent'] = self._detect_intent(original_query)
            
            # 4. 질문 재구성
            rewritten = self._rewrite_question(original_query)
            query_info['rewritten'] = rewritten
            
            # 5. 신뢰도 계산
            query_info['confidence'] = self._calculate_confidence(original_query, rewritten)
            
            return query_info
            
        except Exception as e:
            return {
                'original': original_query,
                'rewritten': original_query,
                'keywords': [],
                'intent': 'general',
                'confidence': 0.5,
                'error': str(e)
            }
    
    def _extract_keywords(self, query: str) -> list:
        """질문에서 키워드 추출"""
        keywords = []
        
        # 부동산 전문 용어 검색
        for term, meaning in self.real_estate_terms.items():
            if term in query:
                keywords.append(meaning)
        
        # 일반적인 키워드 검색
        common_keywords = ["계약", "부동산", "임대", "매매", "가격", "조건", "기간", "보증금", "월세", "전세"]
        for keyword in common_keywords:
            if keyword in query:
                keywords.append(keyword)
        
        return list(set(keywords))  # 중복 제거
    
    def _detect_intent(self, query: str) -> str:
        """질문의 의도 파악"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["가격", "비싸", "싸", "얼마"]):
            return "price_analysis"
        elif any(word in query_lower for word in ["위험", "주의", "문제", "괜찮아"]):
            return "risk_analysis"
        elif any(word in query_lower for word in ["조건", "기간", "보증금"]):
            return "condition_analysis"
        elif any(word in query_lower for word in ["비교", "다른", "시장"]):
            return "comparison"
        elif any(word in query_lower for word in ["요약", "정리", "핵심"]):
            return "summary"
        else:
            return "general"
    
    def _rewrite_question(self, query: str) -> str:
        """질문 재구성"""
        query_lower = query.lower()
        
        # 패턴 매칭을 통한 재구성
        for pattern, replacement in self.rewriting_patterns.items():
            if pattern in query_lower:
                return replacement
        
        # 의도별 기본 재구성
        intent = self._detect_intent(query)
        if intent == "price_analysis":
            return f"이 계약의 가격 조건과 시장 비교 분석: {query}"
        elif intent == "risk_analysis":
            return f"이 계약의 위험 요소와 주의사항 분석: {query}"
        elif intent == "condition_analysis":
            return f"이 계약의 주요 조건 분석: {query}"
        elif intent == "comparison":
            return f"이 계약의 시장 비교 분석: {query}"
        elif intent == "summary":
            return f"이 계약의 핵심 요약: {query}"
        else:
            return f"이 계약에 대한 종합 분석: {query}"
    
    def _calculate_confidence(self, original: str, rewritten: str) -> float:
        """재구성 신뢰도 계산"""
        # 간단한 신뢰도 계산 (0.0 ~ 1.0)
        if original == rewritten:
            return 0.5  # 변경 없음
        
        # 키워드 기반 신뢰도
        keywords = self._extract_keywords(original)
        if len(keywords) > 0:
            return min(0.9, 0.5 + len(keywords) * 0.1)
        
        return 0.7  # 기본 신뢰도

# 전역 Query Rewriter 인스턴스
if 'query_rewriter' not in st.session_state:
    st.session_state.query_rewriter = QueryRewriter()

# 간단한 Re-ranking 클래스
class SimpleReranker:
    def __init__(self):
        # 키워드 가중치 설정
        self.keyword_weights = {
            '계약': 2.0,
            '임대': 1.8,
            '매매': 1.8,
            '보증금': 1.5,
            '월세': 1.5,
            '전세': 1.5,
            '기간': 1.3,
            '가격': 1.3,
            '조건': 1.2,
            '특약': 1.2,
            '등기': 1.1,
            '중개': 1.1
        }
        
        # 위치 가중치 (문서 내 위치에 따른 중요도)
        self.position_weights = {
            'title': 3.0,      # 제목 영역
            'header': 2.0,     # 헤더 영역
            'body': 1.0,       # 본문 영역
            'footer': 0.5      # 푸터 영역
        }
    
    def rerank_documents(self, query: str, documents: list, top_k: int = 3) -> list:
        """문서들을 재정렬하여 상위 k개 반환"""
        try:
            if not documents:
                return []
            
            # 각 문서에 점수 계산
            scored_docs = []
            for i, doc in enumerate(documents):
                score = self._calculate_document_score(query, doc, i)
                scored_docs.append((doc, score))
            
            # 점수 기준으로 내림차순 정렬
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # 상위 k개 문서 반환
            reranked_docs = [doc for doc, score in scored_docs[:top_k]]
            
            # 디버깅 정보 (개발 모드에서만)
            if st.session_state.get('debug_mode', False):
                st.sidebar.info(f"🔍 Re-ranking 결과:")
                for i, (doc, score) in enumerate(scored_docs[:3]):
                    st.sidebar.write(f"{i+1}. 점수: {score:.2f}")
            
            return reranked_docs
            
        except Exception as e:
            st.error(f"Re-ranking 오류: {str(e)}")
            return documents[:top_k]  # 오류시 원본 순서 반환
    
    def _calculate_document_score(self, query: str, document, original_rank: int) -> float:
        """문서의 점수를 계산"""
        try:
            content = document.page_content.lower()
            query_lower = query.lower()
            
            # 1. 키워드 매칭 점수 (40%)
            keyword_score = self._calculate_keyword_score(query_lower, content)
            
            # 2. 텍스트 길이 점수 (20%)
            length_score = self._calculate_length_score(content)
            
            # 3. 위치 점수 (20%)
            position_score = self._calculate_position_score(content)
            
            # 4. 원본 순위 점수 (20%)
            rank_score = self._calculate_rank_score(original_rank)
            
            # 가중 평균 계산
            final_score = (
                keyword_score * 0.4 +
                length_score * 0.2 +
                position_score * 0.2 +
                rank_score * 0.2
            )
            
            return final_score
            
        except Exception as e:
            return 0.0
    
    def _calculate_keyword_score(self, query: str, content: str) -> float:
        """키워드 매칭 점수 계산"""
        score = 0.0
        
        # 쿼리에서 키워드 추출
        query_words = query.split()
        
        for word in query_words:
            if word in content:
                # 키워드 가중치 적용
                weight = self.keyword_weights.get(word, 1.0)
                score += weight
        
        # 정규화 (0~1 범위)
        return min(score / 10.0, 1.0)
    
    def _calculate_length_score(self, content: str) -> float:
        """텍스트 길이 점수 계산 (적당한 길이가 높은 점수)"""
        length = len(content)
        
        # 100~500자 정도가 적당
        if 100 <= length <= 500:
            return 1.0
        elif 50 <= length <= 1000:
            return 0.8
        else:
            return 0.5
    
    def _calculate_position_score(self, content: str) -> float:
        """위치 기반 점수 계산"""
        # 간단한 위치 추정 (실제로는 더 정교한 분석 필요)
        lines = content.split('\n')
        
        if len(lines) <= 3:  # 짧은 텍스트는 제목으로 간주
            return self.position_weights['title']
        elif len(lines) <= 10:  # 중간 길이는 헤더로 간주
            return self.position_weights['header']
        else:  # 긴 텍스트는 본문으로 간주
            return self.position_weights['body']
    
    def _calculate_rank_score(self, original_rank: int) -> float:
        """원본 순위 점수 계산 (높은 순위가 높은 점수)"""
        # 역순으로 점수 계산 (1위가 1.0, 2위가 0.9, ...)
        return max(0.1, 1.0 - (original_rank * 0.1))

# 전역 Re-ranker 인스턴스
if 'reranker' not in st.session_state:
    st.session_state.reranker = SimpleReranker()

# 필수 session_state 초기화
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'raw_text' not in st.session_state:
    st.session_state.raw_text = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'upload_time' not in st.session_state:
    st.session_state.upload_time = None

# 캐시 키 생성 함수
def generate_cache_key(query, vectorstore_id=None):
    """쿼리와 벡터스토어 ID를 기반으로 캐시 키 생성"""
    key_data = {
        'query': query,
        'vectorstore_id': vectorstore_id
    }
    return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

# 캐시에서 응답 가져오기
def get_cached_response(cache_key):
    """캐시에서 응답을 가져옴"""
    # 만료된 캐시 정리
    st.session_state.memory_cache.clear_expired()
    
    cached_data = st.session_state.memory_cache.get(cache_key)
    if cached_data:
        return cached_data
    return None

# 응답을 캐시에 저장
def cache_response(cache_key, response, expire_time=3600):
    """응답을 캐시에 저장 (기본 1시간)"""
    cache_data = {
        'response': response,
        'timestamp': str(datetime.now())
    }
    st.session_state.memory_cache.set(cache_key, cache_data, expire_time)


# handle streaming conversation
class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

# Function to extract text from an PDF file
from pdfminer.high_level import extract_text

def get_pdf_text(filename):
    raw_text = extract_text(filename)
    return raw_text

# document preprocess
def process_uploaded_file(uploaded_file):
    # Load document if file is uploaded
    if uploaded_file is not None:
        # loader
        raw_text = get_pdf_text(uploaded_file)
        # splitter
        text_splitter = CharacterTextSplitter(
        separator = "\n\n",
        chunk_size = 1000,
        chunk_overlap  = 200,
        )
        all_splits = text_splitter.create_documents([raw_text])
        print("총 " + str(len(all_splits)) + "개의 passage")        
        # storage
        vectorstore = FAISS.from_documents(all_splits, OpenAIEmbeddings())
        return vectorstore, raw_text
    return None

# generate response using RAG technic with caching
def generate_response(query_text, vectorstore, callback):

    # Query Rewriting 적용
    query_info = st.session_state.query_rewriter.rewrite_query(query_text)
    rewritten_query = query_info['rewritten']
    
    # Query Rewriting 정보 표시 (신뢰도가 높을 때만)
    if query_info['confidence'] > 0.7 and query_info['original'] != query_info['rewritten']:
        st.info(f"🔍 질문 재구성: '{query_info['original']}' → '{query_info['rewritten']}' (신뢰도: {query_info['confidence']:.1%})")
    
    # 컨텍스트 ID 생성 (파일 기반)
    context_id = f"{st.session_state.get('file_name', 'unknown')}_{st.session_state.get('upload_time', '')}"
    
    # Q&A 캐시에서 응답 확인 (재구성된 쿼리로)
    cached_result = st.session_state.qa_cache.get(rewritten_query, context_id)
    if cached_result:
        st.success(f"💾 캐시된 답변을 사용합니다! (히트율: {st.session_state.qa_cache.get_stats()['hit_rate']}%)")
        return cached_result['answer']

    # retriever (재구성된 쿼리 사용)
    docs_list = vectorstore.similarity_search(rewritten_query, k=5)  # 더 많은 문서 검색
    
    # Re-ranking 적용
    reranked_docs = st.session_state.reranker.rerank_documents(rewritten_query, docs_list, top_k=3)
    
    docs = ""
    for i, doc in enumerate(reranked_docs):
        docs += f"'문서{i+1}':{doc.page_content}\n" 
    
    # 내장 API 정보 수집
    api_info = ""
    
    # 시장 데이터 조회
    if any(keyword in query_text for keyword in ["시세", "가격", "시장", "경제", "금리"]):
        market_data = st.session_state.builtin_api.get_market_data("서울")
        if market_data['success']:
            api_info += f"\n[시장 정보]\n"
            api_info += f"평균 가격: {market_data['data']['avg_price']}\n"
            api_info += f"시장 동향: {market_data['data']['trend']}\n"
            api_info += f"거래량: {market_data['data']['volume']}\n"
            api_info += f"금리: {market_data['data']['interest_rate']}\n"
    
    # 뉴스 정보 조회
    if any(keyword in query_text for keyword in ["뉴스", "소식", "정책", "변화"]):
        news_data = st.session_state.builtin_api.get_news_info("부동산")
        if news_data['success']:
            api_info += f"\n[최신 뉴스]\n"
            for i, news in enumerate(news_data['news'][:2], 1):
                api_info += f"{i}. {news['title']}\n"
                api_info += f"   {news['summary']}\n"
    
    # 환율 정보 조회
    if any(keyword in query_text for keyword in ["환율", "달러", "외화", "해외"]):
        exchange_data = st.session_state.builtin_api.get_exchange_rate()
        if exchange_data['success']:
            api_info += f"\n[환율 정보]\n"
            rates = exchange_data['rates']
            api_info += f"USD: {rates.get('USD', 0):.4f} KRW\n"
            api_info += f"EUR: {rates.get('EUR', 0):.4f} KRW\n"
            api_info += f"JPY: {rates.get('JPY', 0):.2f} KRW\n"
    
    # 날씨 정보 조회
    if any(keyword in query_text for keyword in ["날씨", "기후", "환경"]):
        weather_data = st.session_state.builtin_api.get_weather_info("서울")
        if weather_data['success']:
            api_info += f"\n[날씨 정보]\n"
            api_info += f"온도: {weather_data['temperature']}\n"
            api_info += f"날씨: {weather_data['description']}\n"
            api_info += f"습도: {weather_data['humidity']}\n"
        
    # generator
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, streaming=True, callbacks=[callback])
    
    # chaining (내장 API 정보 포함)
    rag_prompt = [
        SystemMessage(
            content="너는 부동산 계약서를 분석하는 전문가 '부동산 계약서 분석 봇'이야. 주어진 계약서를 참고하여 사용자의 질문에 답변을 해줘. 추가로 제공되는 실시간 시장 정보, 뉴스, 환율, 날씨 정보도 함께 활용해서 더 정확하고 유용한 답변을 제공해줘. 계약서에 내용이 정확하게 나와있지 않으면 '해당 내용은 계약서에 명시되어 있지 않습니다.'라고 대답해줘."
        ),
        HumanMessage(
        content=f"질문:{query_text}\n\n[계약서 내용]\n{docs}\n\n[실시간 정보]\n{api_info}"
        ),
    ]

    response = llm.invoke(rag_prompt)
    
    # Q&A 캐시에 저장
    st.session_state.qa_cache.set(query_text, response.content, context_id)
    st.sidebar.info(f"💾 Q&A가 캐시에 저장되었습니다! (캐시 크기: {st.session_state.qa_cache.get_stats()['cache_size']})")
    
    return response.content


def generate_summarize(raw_text, callback):

    # 요약용 컨텍스트 ID
    text_hash = hashlib.md5(raw_text.encode()).hexdigest()
    context_id = f"summary_{text_hash}"
    
    # Q&A 캐시에서 요약 확인
    cached_result = st.session_state.qa_cache.get("요약", context_id)
    if cached_result:
        st.success(f"💾 캐시된 요약을 사용합니다! (히트율: {st.session_state.qa_cache.get_stats()['hit_rate']}%)")
        return cached_result['answer']

    # generator 
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, streaming=True, callbacks=[callback])
    
    # prompt formatting
    rag_prompt = [
        SystemMessage(
            content="다음 나올 부동산 계약서를 체계적으로 분석해서 요약해줘. 다음 항목들을 포함해서 정리해줘:\n\n1. 계약서 기본 정보 (계약 종류, 계약일)\n2. 계약 당사자 정보\n3. 부동산 정보 (주소, 면적, 용도 등)\n4. 계약 조건 (임대료/매매가격, 계약기간, 보증금 등)\n5. 주요 특약사항\n6. 주의사항 및 위험 요소\n7. 법적 검토 사항\n\n중요한 내용만 간결하게 정리해줘."
        ),
        HumanMessage(
            content=raw_text
        ),
    ]
    
    response = llm(rag_prompt)
    
    # Q&A 캐시에 요약 저장 (더 오래 보관)
    st.session_state.qa_cache.set("요약", response.content, context_id, expire_seconds=7200)
    st.sidebar.info(f"💾 요약이 Q&A 캐시에 저장되었습니다! (캐시 크기: {st.session_state.qa_cache.get_stats()['cache_size']})")
    
    return response.content


# page title
st.set_page_config(page_title='🏠 부동산 계약서 분석 챗봇')
st.title('🏠 부동산 계약서 분석 챗봇')

# 스마트 계약 분석 소개 (중앙 화면)
st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            border-radius: 15px; 
            padding: 30px; 
            color: white; 
            margin: 20px 0;
            text-align: center;">
    <h2 style="color: white; margin-bottom: 20px;">🏠 스마트 계약 분석</h2>
    <p style="font-size: 16px; line-height: 1.8; margin-bottom: 20px;">
        계약서 분석과 함께 <strong>실시간 경제 데이터</strong>를 활용하여 
        더욱 정확한 판단을 도와드립니다!
    </p>
    <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px;">
        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; min-width: 200px;">
            <h4 style="color: white; margin-bottom: 10px;">📊 실시간 시장 정보</h4>
            <p style="font-size: 14px;">부동산 시세, 금리, 거래량</p>
        </div>
        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; min-width: 200px;">
            <h4 style="color: white; margin-bottom: 10px;">🔍 스마트 질문 재구성</h4>
            <p style="font-size: 14px;">간단한 질문도 정확하게 변환</p>
        </div>
        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; min-width: 200px;">
            <h4 style="color: white; margin-bottom: 10px;">💾 지능형 캐싱</h4>
            <p style="font-size: 14px;">빠른 응답과 일관된 답변</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 질문 예시 (중앙 화면)
st.markdown("""
<div style="background: #f8f9fa; border-radius: 15px; padding: 25px; margin: 20px 0;">
    <h3 style="color: #333; margin-bottom: 20px;">💡 이런 질문도 가능해요</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
        <div style="background: white; padding: 20px; border-radius: 10px; border-left: 4px solid #667eea;">
            <h4 style="color: #667eea; margin-bottom: 15px;">🎯 가격 분석</h4>
            <ul style="color: #555; line-height: 1.6;">
                <li>"현재 경제 상황에서 내 계약 금액이 적정한가요?"</li>
                <li>"시장 동향을 고려했을 때 이 계약이 유리한가요?"</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 10px; border-left: 4px solid #764ba2;">
            <h4 style="color: #764ba2; margin-bottom: 15px;">📊 시장 비교</h4>
            <ul style="color: #555; line-height: 1.6;">
                <li>"같은 지역 다른 계약과 비교하면 어떤가요?"</li>
                <li>"금리 변동이 이 계약에 미치는 영향은?"</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 10px; border-left: 4px solid #ff9a9e;">
            <h4 style="color: #ff9a9e; margin-bottom: 15px;">🔍 리스크 분석</h4>
            <ul style="color: #555; line-height: 1.6;">
                <li>"현재 경제 상황에서 이 계약의 위험 요소는?"</li>
                <li>"환율 변동이 계약에 미치는 영향은?"</li>
            </ul>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 스마트 질문 재구성 예시 (중앙 화면)
st.markdown("""
<div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); 
            border-radius: 15px; 
            padding: 25px; 
            margin: 20px 0;">
    <h3 style="color: #333; margin-bottom: 20px; text-align: center;">🔍 스마트 질문 재구성</h3>
    <p style="text-align: center; font-size: 16px; color: #555; margin-bottom: 25px;">
        간단한 질문도 자동으로 더 정확하게 변환됩니다!
    </p>
    <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px;">
        <div style="background: rgba(255,255,255,0.3); padding: 20px; border-radius: 10px; text-align: center; min-width: 250px;">
            <h5 style="color: #333; margin-bottom: 10px;">간단한 질문</h5>
            <p style="color: #555; font-size: 14px;">"괜찮아?"</p>
            <p style="color: #333; font-weight: bold;">↓</p>
            <p style="color: #555; font-size: 14px;">"이 계약의 주요 조건과 위험 요소는?"</p>
        </div>
        <div style="background: rgba(255,255,255,0.3); padding: 20px; border-radius: 10px; text-align: center; min-width: 250px;">
            <h5 style="color: #333; margin-bottom: 10px;">가격 관련</h5>
            <p style="color: #555; font-size: 14px;">"비싸?"</p>
            <p style="color: #333; font-weight: bold;">↓</p>
            <p style="color: #555; font-size: 14px;">"이 계약의 가격이 시장 대비 적정한가요?"</p>
        </div>
        <div style="background: rgba(255,255,255,0.3); padding: 20px; border-radius: 10px; text-align: center; min-width: 250px;">
            <h5 style="color: #333; margin-bottom: 10px;">조건 관련</h5>
            <p style="color: #555; font-size: 14px;">"조건?"</p>
            <p style="color: #333; font-weight: bold;">↓</p>
            <p style="color: #555; font-size: 14px;">"이 계약의 주요 조건들을 분석해주세요"</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# file upload in sidebar
with st.sidebar:
    st.header("📄 계약서 업로드")
    uploaded_file = st.file_uploader('부동산 계약서 PDF를 업로드하세요', type=['pdf'])
    
    # file upload logic
    if uploaded_file:
        vectorstore, raw_text = process_uploaded_file(uploaded_file)
        if vectorstore:
            st.session_state['vectorstore'] = vectorstore
            st.session_state['raw_text'] = raw_text
            st.session_state['upload_time'] = str(uploaded_file.uploaded_at) if hasattr(uploaded_file, 'uploaded_at') else str(hash(raw_text))
            st.session_state['file_name'] = uploaded_file.name
            st.success("✅ 계약서가 성공적으로 업로드되었습니다!")
    
    # 캐시 통계 표시
    st.header("📊 캐시 통계")
    if 'qa_cache' in st.session_state:
        stats = st.session_state.qa_cache.get_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("히트", stats['hits'])
            st.metric("캐시 크기", stats['cache_size'])
        with col2:
            st.metric("미스", stats['misses'])
            st.metric("히트율", f"{stats['hit_rate']}%")
        
        if st.button("🗑️ 캐시 초기화"):
            st.session_state.qa_cache.clear_all()
            st.success("캐시가 초기화되었습니다!")
            st.rerun()
    
    # Re-ranking 정보 표시
    st.markdown("""
    <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                border-radius: 10px; 
                padding: 15px; 
                margin: 10px 0;">
        <h4 style="color: #333; margin-bottom: 10px;">🔄 스마트 재정렬</h4>
        <p style="font-size: 13px; color: #555; margin-bottom: 8px;">
            검색 결과를 더 정확하게 재정렬합니다!
        </p>
        <div style="font-size: 12px; color: #666;">
            <strong>재정렬 기준:</strong><br>
            • 키워드 매칭 (40%)<br>
            • 텍스트 길이 (20%)<br>
            • 위치 중요도 (20%)<br>
            • 원본 순위 (20%)
        </div>
    </div>
    """, unsafe_allow_html=True)
        
# chatbot greatings
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        ChatMessage(
            role="assistant", content="안녕하세요! 저는 부동산 계약서를 분석해드리는 전문 챗봇입니다. 📋\n\n계약서를 업로드하시면 다음과 같은 도움을 드릴 수 있습니다:\n• 계약서 요약 및 주요 내용 분석\n• 계약 조건 검토 및 위험 요소 파악\n• 법적 검토 사항 안내\n• 계약서 관련 질의응답\n\n'요약'이라고 입력하시면 계약서의 전체적인 내용을 분석해드리고, 다른 질문을 하시면 계약서에서 답을 찾아드리겠습니다! 🏠"
        )
    ]

# conversation history print 
for msg in st.session_state.messages:
    st.chat_message(msg.role).write(msg.content)
    
# message interaction
if prompt := st.chat_input("'요약' 또는 계약서 관련 질문을 입력하세요!"):
    st.session_state.messages.append(ChatMessage(role="user", content=prompt))
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        stream_handler = StreamHandler(st.empty())
        
        # vectorstore와 raw_text가 있는지 확인
        if 'vectorstore' not in st.session_state or 'raw_text' not in st.session_state:
            st.error("⚠️ 먼저 계약서를 업로드해주세요!")
            st.session_state["messages"].append(
                ChatMessage(role="assistant", content="계약서를 업로드한 후 질문해주세요.")
            )
        else:
            if prompt == "요약":
                response = generate_summarize(st.session_state['raw_text'], stream_handler)
                st.session_state["messages"].append(
                    ChatMessage(role="assistant", content=response)
                )
            else:
                response = generate_response(prompt, st.session_state['vectorstore'], stream_handler)
                st.session_state["messages"].append(
                    ChatMessage(role="assistant", content=response)
                )