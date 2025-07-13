class MESSAGE:
    class ERROR:
        UNAUTHORIZED = "인증에 실패했습니다."
        DB_CONNECTION_FAILED = "DB 연결에 실패했습니다."
        NOT_FOUND = "데이터를 찾을 수 없습니다."
        SERVER_ERROR = "서버 내부 오류가 발생했습니다."
        SAVE_FAILED = "데이터 저장에 실패했습니다."
        PRESIGNED_URL_FAILED = "접근 URL을 생성하지 못했습니다."
        MISSING_REFRESH_TOKEN = "로그인 정보가 만료되었습니다"
        INVALID_REFRESH_TOKEN = "유효하지 않은 리프레시 토큰입니다"
        MISSING_FIELD = "필수 필드가 누락되었습니다."
        PRCTICE_FAILED = "연습 기록 저장에 실패했습니다."
        DELETE_FAILED_DB = "DB 데이터 삭제에 실패했습니다."
        FORBIDDEN = "권한이 없습니다."
        NOT_DELETED = "삭제된 싸인이 아닙니다."
        GENERATE_FAILED = "AI가 싸인 생성에 실패했습니다."
        ALREADY_DELETED = "이미 삭제된 싸인입니다."

    class SUCCESS:
        SAVE_SUCCESS = "데이터 저장에 성공했습니다."
        SIGN_GENERATION_SUCCESS = "싸인 생성에 성공했습니다."
        PRCTICE_SAVED = "연습 기록 저장에 성공했습니다."
        DELETE_SUCCESS = "데이터를 삭제했습니다."
        HARD_DELETE = "데이터를 영구 삭제했습니다."


class CODE:
    class ERROR:
        NO_TOKEN = "NO_TOKEN"
        TOKEN_EXPIRED = "TOKEN_EXPIRED"
        TOKEN_INVALID = "TOKEN_INVALID"
        DB_CONNECTION_FAILED = "DB_CONNECTION_FAILED"
        NOT_FOUND = "NOT_FOUND"
        SERVER_ERROR = "SERVER_ERROR"
        SAVE_FAILED = "SAVE_FAILED"
        PRESIGNED_URL_FAILED = "PRESIGNED_URL_FAILED"
        MISSING_REFRESH_TOKEN = "MISSING_REFRESH_TOKEN"
        INVALID_REFRESH_TOKEN = "INVALID_REFRESH_TOKEN"
        MISSING_FIELD = "MISSING_FIELD"
        PRCTICE_FAILED = "PRCTICE_FAILED"
        DELETE_FAILED_DB = "DELETE_FAILED_DB"
        FORBIDDEN = "FORBIDDEN"
        NOT_DELETED = "NOT_DELETED"
        GENERATE_FAILED = "GENERATE_FAILED"
        ALREADY_DELETED = "ALREADY_DELETED"

    class SUCCESS:
        SAVE_SUCCESS = "SAVE_SUCCESS"
        SIGN_GENERATION_SUCCESS = "SIGN_GENERATION_SUCCESS"
        PRCTICE_SAVED = "PRCTICE_SAVED"
        DELETE_SUCCESS = "DELETE_SUCCESS"
        HARD_DELETE = "HARD_DELETE"


class TOKEN:
    class EXPIRE:
        ACCESS = 15
        REFRESH = 12


class S3:
    PresignedUrl = 60 * 60
    ResourceName = "s3"


class COOKIE:
    class MaxAge:
        REFRESH = 12 * 60 * 60


class CLIENT:
    URL = "http://localhost:5173"


class CleanupInterval:
    SECONDS = 60
