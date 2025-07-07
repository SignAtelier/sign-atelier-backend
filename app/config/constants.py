class MESSAGE:
    class ERROR:
        UNAUTHORIZED = "인증에 실패했습니다."
        DB_CONNECTION_FAILED = "DB 연결에 실패했습니다."
        NOT_FOUND = "데이터를 찾을 수 없습니다."
        SERVER_ERROR = "서버 내부 오류가 발생했습니다."
        SAVE_FAILED = "데이터 저장에 실패했습니다."

    class SUCCESS:
        SAVE_SUCCESS = "데이터 저장에 성공했습니다."
        SIGN_GENERATION_SUCCESS = "싸인 생성에 성공했습니다."


class CODE:
    class ERROR:
        NO_TOKEN = "NO_TOKEN"
        TOKEN_EXPIRED = "TOKEN_EXPIRED"
        TOKEN_INVALID = "TOKEN_INVALID"
        DB_CONNECTION_FAILED = "DB_CONNECTION_FAILED"
        NOT_FOUND = "NOT_FOUND"
        SERVER_ERROR = "SERVER_ERROR"
        SAVE_FAILED = "SAVE_FAILED"

    class SUCCESS:
        SAVE_SUCCESS = "SAVE_SUCCESS"
        SIGN_GENERATION_SUCCESS = "SIGN_GENERATION_SUCCESS"


class AUTH:
    class TOKEN:
        EXPIRE = 15


class S3:
    PresignedUrl = 15 * 60


class COOKIE:
    MAX_AGE = 15 * 60


class CLIENT:
    URL = "http://localhost:5173"
