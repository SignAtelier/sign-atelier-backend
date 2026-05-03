import io


class SignGenerationProvider:
    name = "base"

    def generate(
        self, name: str, style: str = "luxury", seed: int | None = None
    ) -> io.BytesIO:
        raise NotImplementedError
