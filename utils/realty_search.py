import os
import json
import urllib.request
import urllib.parse
import streamlit as st
import time
import re
from typing import List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 부동산 검색 이력 캐시 파일 경로
REALTY_SEARCH_CACHE_FILE = "realty_search_cache.json"

class RealtySearch:
    """
    네이버 부동산 매물 검색 챗봇
    네이버 부동산 사이트에서 매매, 전세, 월세 매물 정보를 검색하고 GPT로 답변 생성
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def _search_naver_realty(self, query: str) -> tuple:
        """네이버 부동산 정보 검색 (Tavily API 사용)
        
        Returns:
            tuple: (검색 결과 텍스트, 검색된 URL 리스트)
        """
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if not tavily_api_key:
                return "Tavily API 키가 설정되어 있지 않습니다. 환경 변수 TAVILY_API_KEY를 설정해주세요.", []
            
            # 검색 쿼리를 더 유연하게 만들기 (여러 변형 시도)
            search_queries = [
                f"{query} site:fin.land.naver.com",
                query.replace(" ", "") + " site:fin.land.naver.com",  # 공백 제거
                query + " 네이버 부동산"
            ]
            
            all_results = []
            all_urls = []
            
            for search_query in search_queries[:1]:  # 첫 번째 쿼리만 사용
                url = "https://api.tavily.com/search"
                payload = {
                    "api_key": tavily_api_key,
                    "query": search_query,
                    "search_depth": "advanced",
                    "max_results": 10,  # 더 많은 결과 가져오기
                    "include_answer": True,
                    "include_images": False
                }
                data = json.dumps(payload).encode("utf-8")
                
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=20) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                
                # 결과 정리
                sources = result.get("results", [])
                if sources:
                    for item in sources:
                        title = item.get("title", "") or item.get("url", "") or "출처"
                        url_src = item.get("url", "")
                        snippet = item.get("content", "")
                        if url_src and url_src not in all_urls:
                            all_urls.append(url_src)
                            all_results.append({
                                "title": title,
                                "url": url_src,
                                "content": snippet
                            })
            
            # 결과 포맷팅 (더 상세하게)
            parts = []
            if result.get("answer"):
                parts.append(f"검색 요약: {result.get('answer')}")
            
            if all_results:
                formatted_sources = []
                for item in all_results[:10]:
                    snippet = item["content"][:500] + ("..." if len(item["content"]) > 500 else "") if item["content"] else ""
                    formatted_sources.append(f"제목: {item['title']}\nURL: {item['url']}\n내용: {snippet}\n---")
                parts.append("\n검색된 매물 정보 (상세):\n" + "\n".join(formatted_sources))
            
            result_text = "\n\n".join(parts) if parts else "네이버 부동산에서 관련 매물 정보를 찾기 어려웠습니다."
            return result_text, all_urls
            
        except Exception as e:
            return f"네이버 부동산 검색 중 오류: {str(e)}", []
    
    def _extract_search_params(self, question: str) -> Dict[str, Any]:
        """질문에서 지역, 매물 유형(매매/전세/월세), 가격대 등을 추출"""
        prompt = f"""
        다음 부동산 매물 검색 질문을 분석하여 정보를 추출해주세요.
        질문: {question}
        
        다음 형식으로 JSON으로만 응답해주세요:
        {{
            "region": "지역명 (예: 서울 강남구, 경기 성남시 등)",
            "property_type": "매물 유형 (아파트, 빌라, 원룸, 투룸 등)",
            "transaction_type": "거래 유형 (매매, 전세, 월세 중 하나 또는 여러 개)",
            "price_range": "가격대 (있는 경우)",
            "keywords": "추가 키워드"
        }}
        
        거래 유형이 명시되지 않았으면 ["매매", "전세", "월세"] 모두 포함하세요.
        JSON만 출력하세요.
        """
        
        try:
            response = self.llm.invoke(prompt)
            result_text = response.content.strip()
            # JSON 추출 (마크다운 코드 블록 제거)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            params = json.loads(result_text)
            return params
        except Exception as e:
            print(f"파라미터 추출 오류: {e}")
            # 기본값 반환
            return {
                "region": "",
                "property_type": "",
                "transaction_type": ["매매", "전세", "월세"],
                "price_range": "",
                "keywords": ""
            }
    
    def _generate_naver_link(self, params: Dict[str, Any], question: str) -> str:
        """네이버 부동산 검색 링크 생성"""
        base_url = "https://fin.land.naver.com"
        
        # 질문에서 단지명이나 아파트명 추출 시도
        search_term = ""
        
        # 주요 단지명 패턴 매칭
        if "한진타운" in question or "한진" in question:
            search_term = "행당한진타운" if "행당" in question else "한진타운"
        elif "헬리오시티" in question or "헬리오" in question:
            search_term = "헬리오시티"
        elif params.get("keywords"):
            search_term = params["keywords"]
        elif params.get("region"):
            search_term = params["region"]
        
        if search_term:
            # 네이버 부동산 검색 URL 생성
            encoded_term = urllib.parse.quote(search_term)
            return f"{base_url}/search?query={encoded_term}"
        
        return f"{base_url}/?content=recent"
    
    def search_realty(self, question: str) -> tuple:
        """부동산 매물 검색 및 답변 생성
        
        Returns:
            tuple: (답변 문자열, 웹 검색 사용 여부 - 항상 True)
        """
        start_time = time.time()
        
        try:
            # 질문에서 검색 파라미터 추출
            params = self._extract_search_params(question)
            
            # 네이버 부동산 검색 쿼리 구성 (더 유연하게)
            search_query_parts = []
            
            # 질문에서 직접 단지명이나 키워드 추출
            if "한진타운" in question or "한진" in question:
                if "행당" in question:
                    search_query_parts.append("행당한진타운")
                else:
                    search_query_parts.append("한진타운")
            elif "헬리오시티" in question or "헬리오" in question:
                search_query_parts.append("헬리오시티")
            
            if params.get("region"):
                search_query_parts.append(params["region"])
            if params.get("property_type"):
                search_query_parts.append(params["property_type"])
            
            transaction_types = params.get("transaction_type", [])
            if isinstance(transaction_types, list) and transaction_types:
                if len(transaction_types) == 1:
                    search_query_parts.append(transaction_types[0])
            
            # 전용면적 정보 추가
            if "전용" in question or "59" in question or "㎡" in question:
                if "59" in question:
                    search_query_parts.append("전용59")
                elif "㎡" in question:
                    # 면적 추출
                    area_match = re.search(r'(\d+)\s*㎡', question)
                    if area_match:
                        area = area_match.group(1)
                        search_query_parts.append(f"전용{area}")
            
            if params.get("keywords") and params["keywords"] not in " ".join(search_query_parts):
                search_query_parts.append(params["keywords"])
            
            search_query = " ".join(search_query_parts) if search_query_parts else question
            
            # 네이버 부동산 검색
            search_results, found_urls = self._search_naver_realty(search_query)
            
            # 네이버 부동산 링크 생성
            naver_link = self._generate_naver_link(params, question)
            
            # GPT로 답변 생성
            answer_prompt = f"""
            다음은 네이버 부동산 매물 검색 질문입니다.
            질문: {question}
            
            검색 파라미터:
            - 지역: {params.get('region', '지정 안됨')}
            - 매물 유형: {params.get('property_type', '지정 안됨')}
            - 거래 유형: {', '.join(transaction_types) if isinstance(transaction_types, list) else transaction_types}
            - 가격대: {params.get('price_range', '지정 안됨')}
            
            네이버 부동산 검색 결과:
            {search_results}
            
            네이버 부동산 직접 검색 링크: {naver_link}
            
            위 정보를 바탕으로 다음을 포함하여 답변해주세요:
            
            **매우 중요한 지시사항:**
            
            1. **거래 유형 구분 (반드시 엄격하게 구분):**
               - **매매**: 집을 사고 파는 것. 가격은 "매매 XX억" 형식으로 표시됨
               - **전세**: 전세금을 주고 집을 빌리는 것. 가격은 "전세 XX억" 형식으로 표시됨
               - **월세**: 월세를 내고 집을 빌리는 것. 가격은 "월세 XX억" 또는 "보증금 XX억 / 월 XX만원" 형식으로 표시됨
            
            2. **검색 결과에서 가격 정보 추출 시 주의사항:**
               - 검색 결과의 "내용" 부분을 매우 주의 깊게 읽어야 합니다
               - "매매 31억", "전세 8억", "월세 8억" 같은 형식으로 명확히 표시된 가격만 사용
               - 가격이 명확하지 않거나 이상하면 추측하지 말고, 네이버 부동산에서 직접 확인하도록 안내
               - 서울 아파트 매매 가격이 3억원 미만이면 명백히 잘못된 정보입니다
            
            3. **답변 형식 (반드시 이 형식으로 작성):**
               ```
               ## [단지명/아파트명] 매물 정보
               
               ### 매매 (사고 파는 것)
               - [동호수] 매매 XX억
               - [동호수] 매매 XX억
               (매매 매물이 여러 개면 모두 나열)
               
               ### 전세
               - [동호수] 전세 XX억
               - [동호수] 전세 XX억
               (전세 매물이 여러 개면 모두 나열)
               
               ### 월세
               - [동호수] 월세 XX억 / 월 XX만원
               - [동호수] 월세 XX억 / 월 XX만원
               (월세 매물이 여러 개면 모두 나열)
               
               ⚠️ **중요**: 검색 결과의 가격 정보는 참고용입니다. 정확한 가격과 최신 정보는 네이버 부동산에서 직접 확인해주세요.
               
               [네이버 부동산에서 직접 확인하기]({naver_link})
               ```
            
            4. **검색 결과 해석 시 주의:**
               - 검색 결과의 "내용" 부분에서 "매매", "전세", "월세" 키워드를 찾아서 정확히 구분
               - 가격 정보가 명확하지 않으면 추측하지 말고, "검색 결과에서 정확한 가격 정보를 찾기 어려웠습니다"라고 명시
               - 검색 결과에 매물이 없다고 나와도, 실제로는 네이버 부동산에 있을 수 있으므로 링크를 제공
            
            5. **예시 (헬리오시티의 경우):**
               - 검색 결과에 "매매 31억", "매매 29억"이 나오면 → 매매 가격으로 정확히 표시
               - 검색 결과에 "전세 8억"이 나오면 → 전세 가격으로 정확히 표시
               - 검색 결과에 "월세 8억"이 나오면 → 월세 가격으로 정확히 표시
            
            답변은 한국어로 작성하고, 위 형식을 정확히 따르세요.
            **검색 결과를 매우 주의 깊게 읽고, 매매/전세/월세를 정확히 구분하여 답변하세요.**
            """
            
            response = self.llm.invoke(answer_prompt)
            answer = response.content
            
            # 링크가 없으면 추가
            if naver_link not in answer:
                answer += f"\n\n[네이버 부동산에서 직접 확인하기]({naver_link})"
            
            response_time = time.time() - start_time
            print(f"부동산 매물 검색 완료 (응답시간: {response_time:.2f}초)")
            
            return answer, True  # 항상 웹 검색 사용
            
        except Exception as e:
            response_time = time.time() - start_time
            print(f"❌ 부동산 매물 검색 오류 (응답시간: {response_time:.2f}초)")
            return f"부동산 매물 검색 중 오류가 발생했습니다: {str(e)}", True

# 전역 인스턴스
_realty_search_instance = None

def load_realty_search_cache():
    """부동산 검색 이력 캐시 파일에서 데이터 로드"""
    try:
        if os.path.exists(REALTY_SEARCH_CACHE_FILE):
            with open(REALTY_SEARCH_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {"question_counts": {}, "searches": []}

def save_realty_search_cache(cache_data):
    """부동산 검색 이력 캐시 파일에 데이터 저장"""
    try:
        with open(REALTY_SEARCH_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def record_realty_search(question: str, answer: str):
    """부동산 검색 이력을 기록 (질문 전체를 저장)"""
    try:
        if not question or not question.strip():
            return
        
        question_clean = question.strip()
        
        # 답변에서 가격 정보 추출 (10자 이내)
        price_summary = ""
        price_patterns = [
            r'매매\s*(\d+억(?:\s*\d+[,\d]*)?)',
            r'전세\s*(\d+억(?:\s*\d+[,\d]*)?)',
            r'월세\s*(\d+억(?:\s*\d+[,\d]*)?)',
        ]
        
        found_prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, answer)
            if matches:
                found_prices.extend(matches[:2])  # 최대 2개 가격만
        
        if found_prices:
            if len(found_prices) == 1:
                price_summary = found_prices[0]
            else:
                price_summary = f"{found_prices[0]} ~ {found_prices[-1]}"
            
            # 10자 이내로 제한
            if len(price_summary) > 10:
                price_summary = price_summary[:10] + "..."
        
        # 현재 날짜 가져오기
        from datetime import datetime
        current_date = datetime.now().strftime("%Y.%m.%d")
        
        cache_data = load_realty_search_cache()
        question_counts = cache_data.get("question_counts", {})
        
        # 질문 카운트 증가 및 정보 업데이트
        if question_clean in question_counts:
            question_counts[question_clean]["count"] = question_counts[question_clean].get("count", 0) + 1
            question_counts[question_clean]["last_date"] = current_date
            if price_summary:
                question_counts[question_clean]["price_summary"] = price_summary
        else:
            question_counts[question_clean] = {
                "count": 1,
                "last_date": current_date,
                "price_summary": price_summary
            }
        
        cache_data["question_counts"] = question_counts
        save_realty_search_cache(cache_data)
    except Exception as e:
        print(f"검색 이력 기록 중 오류: {e}")

def get_recent_searches(top_k=5):
    """최근 검색 이력 상위 k개 반환 (하위 호환성)"""
    return get_top_questions(top_k)

def get_top_questions(top_k=5):
    """가장 많이 검색한 질문 상위 k개 반환"""
    try:
        if not isinstance(top_k, int) or top_k < 1:
            top_k = 5
        
        cache_data = load_realty_search_cache()
        if not isinstance(cache_data, dict):
            cache_data = {"question_counts": {}}
        
        question_counts = cache_data.get("question_counts", {})
        if not isinstance(question_counts, dict):
            question_counts = {}
        
        # 많이 검색한 순서로 정렬 (count 기준)
        sorted_questions = sorted(
            question_counts.items(), 
            key=lambda x: x[1].get("count", 0) if isinstance(x[1], dict) else (x[1] if isinstance(x[1], int) else 0), 
            reverse=True
        )
        
        result = []
        for question, data in sorted_questions[:top_k]:
            if question and question.strip():
                if isinstance(data, dict):
                    result.append({
                        'question': question.strip(),
                        'count': data.get("count", 1),
                        'last_date': data.get("last_date", ""),
                        'price_summary': data.get("price_summary", "")
                    })
                else:
                    # 하위 호환성 (이전 형식)
                    result.append({
                        'question': question.strip(),
                        'count': data if isinstance(data, int) else 1,
                        'last_date': "",
                        'price_summary': ""
                    })
        
        return result
    except Exception as e:
        print(f"get_top_questions 오류: {e}")
        return []

def get_realty_search_answer(question: str) -> tuple:
    """부동산 매물 검색 답변을 가져오는 함수
    
    Returns:
        tuple: (답변 문자열, 웹 검색 사용 여부)
    """
    global _realty_search_instance
    
    if _realty_search_instance is None:
        _realty_search_instance = RealtySearch()
    
    answer, used_web_search = _realty_search_instance.search_realty(question)
    
    # 검색 이력 기록
    record_realty_search(question, answer)
    
    return answer, used_web_search

