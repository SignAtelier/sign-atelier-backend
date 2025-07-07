from datetime import datetime, timezone

from app.models.user import User


async def upsert_user(userinfo: dict, provider: str):
    now = datetime.now(timezone.utc)
    social_id = userinfo["sub"]

    user = await User.find_one(
        User.social_id == social_id, User.provider == provider
    )

    if user:
        user.profile = userinfo["picture"]
        user.updated_at = now

        await user.save()
    else:
        user = User(
            social_id=social_id,
            provider=provider,
            profile=userinfo["picture"],
            created_at=now,
            updated_at=now,
            deleted=False,
        )

        await user.insert()

    return {
        "social_id": user.social_id,
        "profile": user.profile,
        "provider": user.provider,
    }
