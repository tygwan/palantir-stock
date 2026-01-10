# Palantir AIP 접근 권한 가이드

## 현재 상태

Palantir AIP 플랫폼이 활성화되어 있으나, 접근 권한이 부여되지 않은 상태입니다.

## 접근 권한 획득 절차

### 1단계: 플랫폼 관리자 승인 요청

Palantir MCP 사용을 위해 플랫폼 관리자에게 다음 내용을 포함한 승인 요청을 제출하세요:

```
제목: Palantir MCP 접근 권한 요청

요청 사항:
1. Control Panel → Code Repositories → Palantir MCP 활성화
2. 사용자/그룹에 대한 MCP 접근 권한 부여

사용 목적:
- AI 에이전트를 통한 기업 데이터 분석
- Ontology 기반 지식 그래프 구축
- 자동화된 데이터 파이프라인 개발

요청자: [이름/부서]
```

### 2단계: 사용자 토큰 생성

권한 승인 후:

1. Palantir Foundry에 로그인
2. Settings → Security → User Tokens 이동
3. "Generate New Token" 클릭
4. 토큰 이름과 만료 기간 설정
5. 생성된 토큰을 안전하게 저장

### 3단계: 환경 변수 설정

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export FOUNDRY_TOKEN="your_token_here"
export FOUNDRY_HOST="your-enrollment.palantirfoundry.com"

# 적용
source ~/.bashrc
```

### 4단계: Claude Code에 MCP 설치

```bash
claude mcp add palantir-mcp \
  --scope user \
  -e FOUNDRY_TOKEN=$FOUNDRY_TOKEN \
  -- npx "-y" "palantir-mcp" "--foundry-api-url" "https://$FOUNDRY_HOST"
```

### 5단계: 연결 테스트

Claude Code에서 다음을 시도:
- "Find me all object types in my ontology"
- "List available datasets in my project"

## 보안 참고 사항

- 토큰은 절대 코드에 하드코딩하지 마세요
- `.env` 파일은 `.gitignore`에 포함되어야 합니다
- Palantir MCP를 통해 접근한 데이터는 외부 시스템(LLM)으로 전송됩니다
- 민감한 데이터가 포함된 데이터셋 접근 시 주의하세요

## 대안: Palantir 없이 사용

Palantir AIP 접근 권한이 없어도 이 프로젝트의 핵심 기능은 사용 가능합니다:

1. **웹 검색 에이전트**: SerpAPI/Tavily 기반
2. **Graph RAG**: Neo4j 기반 자체 지식 그래프
3. **주식 데이터**: yfinance/Alpha Vantage API

Palantir 통합은 선택적 기능으로, 엔터프라이즈 데이터 소스와의 연동이 필요할 때만 활성화하면 됩니다.

## 참고 문서

- [Palantir MCP Overview](https://www.palantir.com/docs/foundry/palantir-mcp/overview)
- [Palantir MCP Installation](https://www.palantir.com/docs/foundry/palantir-mcp/installation)
- [Palantir MCP Security](https://www.palantir.com/docs/foundry/palantir-mcp/security)
- [Palantir MCP Setup Guide (Community)](https://dimethyl-pant.medium.com/palantir-mcp-setup-a-practical-companion-guide-510eba866bcc)
- [Palantir Developer Community](https://community.palantir.com/t/model-context-protocol-mcp/3265)
