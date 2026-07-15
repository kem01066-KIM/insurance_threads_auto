import streamlit as st
import openai
import json

# --- 1. 가상 데이터베이스 초기화 (Streamlit Session State 활용) ---
if "db_initialized" not in st.session_state:
    st.session_state.users = [
        {"id": "planner_a", "name": "김설계", "tier": "Free", "credits": 3, "used": 1},
        {"id": "planner_b", "name": "이보장", "tier": "Pro", "credits": 9999, "used": 12},
        {"id": "planner_c", "name": "박실비", "tier": "Free", "credits": 3, "used": 3}, # 크레딧 모두 소진한 유저
    ]
    st.session_state.system_prompt = (
        "너는 보험 설계사를 위한 전문 Threads 마케팅 비서야.\n"
        "사용자가 프로필(경력, 철학, 주요 보장 상품)을 제공하면, 다음 규칙에 맞춰 3개의 카테고리 Threads 초안과 1개의 무료 자료(리드 마그넷) 원고를 한국어로 한 번에 작성해 줘.\n\n"
        "1. Threads 카테고리 1 (고객 사례):\n"
        "- 친근한 반말 어조('야, 너희들...'), 구체적인 사례, 마지막에 자료 배포용 CTA(댓글 유도) 필수.\n\n"
        "2. Threads 카테고리 2 (정보성 - 2026년 5세대 실손보험 개정 등 최신 트렌드 반영):\n"
        "- Q&A 형식으로 시작, 알기 쉽게 요약.\n\n"
        "3. Threads 카테고리 3 (설계사 철학):\n"
        "- 경력이 묻어나는 따뜻하고 전문적인 독백 어투.\n\n"
        "4. Companion 무료 자료 (리드 마그넷) 원고:\n"
        "- 카테고리 1 사례와 어울리는 '1가지 주제'의 실무 지침 가이드.\n"
        "- 어조: 상냥하고 존중하는 경어체(~셔요, ~해 드릴게요).\n"
        "- 큰 글씨를 위한 명확한 마크다운 헤더 사용, 텍스트 중간에 구체적인 [시각화/디자인 레이아웃 가이드라인] 서술 필수."
    )
    st.session_state.db_initialized = True

# --- UI 레이아웃 설정 ---
st.set_page_config(page_title="Threads 보험 자동화 플랫폼 MVP", layout="wide")

# --- 2. 사이드바: 권한 전환 및 API Key 입력 ---
st.sidebar.title("🛡️ 서비스 권한 제어")
app_mode = st.sidebar.selectbox("사용자 역할 선택", ["💼 보험 설계사 화면 (User)", "🔑 최고 관리자 화면 (Admin)"])

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ API 설정")
api_key = st.sidebar.text_input("OpenAI API Key 입력", type="password", help="콘텐츠 생성을 위해 OpenAI API Key를 입력하세요.")

if api_key:
    openai.api_key = api_key

# --- 3. 🔑 최고 관리자 화면 (Admin) ---
if app_mode == "🔑 최고 관리자 화면 (Admin)":
    st.title("🔑 플랫폼 관리자 어드민 대시보드")
    st.caption("회원들의 구독 요금제, 사용량 제어 및 AI 마스터 프롬프트를 조율할 수 있습니다.")
    
    # 지표 요약
    col1, col2, col3 = st.columns(3)
    total_users = len(st.session_state.users)
    pro_users = sum(1 for u in st.session_state.users if u["tier"] == "Pro")
    col1.metric("총 등록 설계사 수", f"{total_users}명")
    col2.metric("Pro 유료 구독자", f"{pro_users}명")
    col3.metric("전환율", f"{(pro_users/total_users)*100:.1f}%" if total_users > 0 else "0%")
    
    st.subheader("설계사(고객) 관리 리스트")
    
    # 유저 리스트 편집 및 사용량 충전 테이블
    for idx, user in enumerate(st.session_state.users):
        with st.container():
            col_name, col_tier, col_credit, col_used, col_action = st.columns([2, 2, 2, 2, 3])
            col_name.write(f"**{user['name']}** ({user['id']})")
            
            # 구독 플랜 변경
            new_tier = col_tier.selectbox(
                f"플랜 변경 ({user['id']})", 
                ["Free", "Pro"], 
                index=0 if user["tier"] == "Free" else 1, 
                key=f"tier_{user['id']}"
            )
            st.session_state.users[idx]["tier"] = new_tier
            
            # 크레딧 관리
            col_credit.write(f"보유 크레딧: {user['credits']}회")
            col_used.write(f"사용량: {user['used']}회")
            
            # 수동 관리 액션 (수동 입금 확인 후 크레딧 추가 기능 시뮬레이션)
            if col_action.button(f"⚡ 크레딧 충전 (+5)", key=f"btn_{user['id']}"):
                st.session_state.users[idx]["credits"] += 5
                st.success(f"{user['name']} 님의 크레딧이 5회 충전되었습니다!")
                st.rerun()
                
            st.markdown("---")
            
    # AI 마스터 프롬프트 설정 (어드민이 퀄리티 조율 가능)
    st.subheader("🤖 AI Generation Master Prompt")
    st.session_state.system_prompt = st.text_area(
        "전체 유저에게 적용되는 콘텐츠 생성 규칙", 
        st.session_state.system_prompt, 
        height=300
    )
    st.success("프롬프트 설정이 임시 저장되었습니다.")

# --- 4. 💼 보험 설계사 화면 (User) ---
else:
    st.title("💼 보험 설계사 전용 마케팅 센터")
    st.caption("매일 고품질의 Threads 스레드 원고와 함께 배포용 무료 소책자 원고를 한 번에 자동 생성합니다.")
    
    # 목업 로그인 처리 (설계사 선택)
    planner_options = {u["name"]: u for u in st.session_state.users}
    selected_planner_name = st.selectbox("테스트할 설계사 계정을 선택하세요", list(planner_options.keys()))
    current_user = planner_options[selected_planner_name]
    
    # 크레딧 잔여 표시 및 한도 초과(Paywall) 경험 시뮬레이션
    st.info(f"🏷️ 요금제: **{current_user['tier']} 플랜** | 🎟️ 잔여 생성 크레딧: **{current_user['credits']}회** (누적 사용: {current_user['used']}회)")
    
    if current_user["credits"] <= 0 and current_user["tier"] == "Free":
        st.error("🚨 보유하신 무료 크레딧을 모두 소진하셨습니다! 계속해서 콘텐츠와 무료 배포용 소책자를 생성하려면 'Pro 플랜'으로 업그레이드해 주셔요.")
        st.button("💎 월 29,000원에 Pro 플랜 구독하기 (카드/간편결제)")
    else:
        # 설계사 맞춤형 생성 프로필 입력
        st.subheader("📝 프로필 및 원하는 주제 입력")
        col_l, col_r = st.columns(2)
        
        experience = col_l.number_input("설계사 경력 (년)", min_value=1, max_value=40, value=10)
        philosophy = col_l.text_input("고객을 대하는 나의 신조/철학", value="환자의 입장에서 가장 합리적인 지출만 설계하자")
        
        key_topic = col_r.selectbox(
            "오늘 다루고 싶은 메인 보장 이슈",
            [
                "암 진단비의 현실적인 필요성과 생활비 공백 채우기",
                "2026년 신규 출시된 '5세대 실손보험' 달라진 핵심 내용 쉽게 풀기",
                "수술비/실비 청구 시 자칫 누락하고 놓치기 쉬운 필수 서류"
            ]
        )
        extra_desc = col_r.text_area("사례나 추가로 넣고 싶은 세부 정황 (선택사항)", placeholder="예: 40대 가장이 갑자기 암에 걸렸으나 미리 넉넉히 준비한 진단금으로 생활비 걱정 없이 위기를 넘긴 사례")

        # 생성 버튼
        if st.button("🚀 오늘의 콘텐츠 & 무료 소책자 초안 세트 생성하기"):
            if not api_key:
                st.warning("먼저 왼쪽 사이드바에 OpenAI API Key를 입력하셔야 정상 가동됩니다.")
            else:
                with st.spinner("AI가 고품질 스레드와 배포용 1페이지 소책자를 동시 집필 중입니다. 약 20초 정도 걸려요..."):
                    try:
                        # 사용자 입력 정보 조합
                        user_prompt = f"""
                        설계사 정보:
                        - 경력: {experience}년차
                        - 철학: {philosophy}
                        
                        오늘의 주제: {key_topic}
                        추가 정황: {extra_desc if extra_desc else "기본 가이드 기준 스토리 기반 자동 완성"}
                        """
                        
                        # API 호출
                        response = openai.chat.completions.create(
                            model="gpt-4o-mini",  # 속도 및 비용 최적화를 위해 미니 활용
                            messages=[
                                {"role": "system", "content": st.session_state.system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.75
                        )
                        
                        # 결과 파싱 및 표시
                        result_text = response.choices[0].message.content
                        
                        # 사용 완료 기록 차감
                        for u in st.session_state.users:
                            if u["id"] == current_user["id"]:
                                u["credits"] -= 1
                                u["used"] += 1
                                
                        st.session_state.generation_result = result_text
                        st.success("🎉 작성이 완료되었습니다! 아래 탭에서 복사하여 편리하게 배포해 보셔요.")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
                        
        # 생성된 결과가 있는 경우 화면에 노출
        if "generation_result" in st.session_state:
            st.markdown("---")
            st.subheader("🎁 AI가 완성한 오늘의 마케팅 패키지")
            
            # 탭 구조를 제공하여 복사하기 편리하게 배치
            tab1, tab2 = st.tabs(["📲 Threads 게시용 원고 (스레드 3종 세트)", "📄 무기(Lead Magnet)로 나눠줄 무료 배포용 소책자 원고"])
            
            with tab1:
                st.info("💡 팁: 아래 텍스트를 그대로 복사하여 Threads에 연결된 답글 형태로 게시해 보세요!")
                st.markdown(st.session_state.generation_result.split("Companion 무료 자료")[0])
                
            with tab2:
                st.info("💡 팁: 상냥한 말투로 작성된 원고입니다. 내용을 복사해 노션(Notion)에 붙여넣어 공유 링크를 주거나, PDF로 꾸며 고객 이메일로 즉시 전달하세요.")
                if "Companion 무료 자료" in st.session_state.generation_result:
                    st.markdown(st.session_state.generation_result.split("Companion 무료 자료")[-1])
                else:
                    st.markdown(st.session_state.generation_result)