import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_reason(read_books, behaviors, recommended_title, score):
    try:
        logger.info("[FLASK] 추천 이유 요청 수신 - recommended_title=%s", recommended_title)
        logger.info("[FLASK] read_books=%s", read_books)
        logger.info("[FLASK] behaviors=%s", behaviors)
        logger.info("[FLASK] score=%s", score)

        # 유효성 체크
        if not recommended_title:
            logger.warning("[generate_reason] recommended_title 누락됨")
            return "이 책은 사용자의 취향에 맞춰 추천되었습니다."

        # 읽은 책 제목 리스트 구성
        if not isinstance(read_books, list) or len(read_books) == 0:
            logger.warning("[generate_reason] read_books 비어 있음")
            read_titles = "읽은 책 정보 없음"
        else:
            read_titles = ", ".join([book.get("title", "제목 없음") for book in read_books])

        # 행동 정보 요약 (평균 체류 시간, 평균 스크롤 깊이)
        if not isinstance(behaviors, list) or len(behaviors) == 0:
            avg_stay = "정보 없음"
            avg_scroll = "정보 없음"
        else:
            stay_times = [b.get("stayTime", 0) for b in behaviors]
            scroll_depths = [b.get("scrollDepth", 0) for b in behaviors]
            avg_stay = round(sum(stay_times) / len(stay_times), 1)
            avg_scroll = round(sum(scroll_depths) / len(scroll_depths), 1)

        # NaN 또는 None 처리
        if score is None or (isinstance(score, float) and (score != score)):
            score = "알 수 없음"
        else:
            score = round(score, 4)

        # 프롬프트 구성
        prompt = f"""
        사용자가 읽은 책 제목들: {read_titles}
        사용자 평균 체류 시간: {avg_stay}초
        사용자 평균 스크롤 깊이: {avg_scroll}%
        추천 도서: {recommended_title}
        추천 점수: {score}

        위 정보를 기반으로, 사용자의 독서 성향과 행동 패턴을 반영하여 '{recommended_title}'을 추천하는 이유를 자연스럽게 2~3문장으로 설명해줘.
        감성적/논리적 이유를 혼합하고, 너무 단조롭지 않게 설명해줘.
        """

        # ChatGPT 호출
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 도서 추천 이유를 자연스럽게 설명하는 조언자야."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
            temperature=0.7
        )

        reason = response.choices[0].message.content.strip()
        return reason

    except Exception as e:
        logger.warning(f"[generate_reason] 추천 이유 생성 실패: {e}")
        return "이 책은 사용자의 취향에 맞춰 추천되었습니다."