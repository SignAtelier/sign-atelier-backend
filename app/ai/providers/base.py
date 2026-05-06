import io

from app.models.sign_style import SignatureStyle


class SignGenerationProvider:
    name = "base"

    def generate(
        self,
        name: str,
        style: SignatureStyle = SignatureStyle.LUXURY,
        seed: int | None = None,
    ) -> io.BytesIO:
        raise NotImplementedError
