import uuid

from app.core.exceptions import AppError, ErrorCode
from app.modules.auth.schemas import UserProfile
from app.modules.auth.service import AuthService
from app.modules.community.schemas import ProfileCounts
from app.modules.community.service import CommunityService
from app.modules.me.schemas import Me, MePatch
from app.modules.points.service import PointsService


class MeService:
    def __init__(
        self,
        auth: AuthService,
        points: PointsService,
        community: CommunityService,
    ) -> None:
        self._auth = auth
        self._points = points
        self._community = community

    async def get_me(self, user_id: uuid.UUID) -> Me:
        profile = await self._auth.get_profile(user_id)
        balance = await self._points.balance(user_id)
        counts = await self._community.profile_counts(user_id)
        return _present(profile, balance, counts)

    async def patch_me(self, user_id: uuid.UUID, patch: MePatch) -> Me:
        changes: dict[str, str | None] = {}
        if "nickname" in patch.model_fields_set:
            changes["nickname"] = _nickname(patch.nickname)
        if "avatar_url" in patch.model_fields_set:
            changes["avatar_url"] = patch.avatar_url
        profile = await self._auth.update_profile(user_id, changes)
        balance = await self._points.balance(user_id)
        counts = await self._community.profile_counts(user_id)
        return _present(profile, balance, counts)


def _nickname(value: str | None) -> str | None:
    if value is None:
        return None
    nickname = value.strip()
    if not nickname or len(nickname) > 16:
        raise AppError(ErrorCode.VALIDATION, "昵称须为 1–16 字", 400)
    return nickname


def _present(profile: UserProfile, balance: int, counts: ProfileCounts) -> Me:
    return Me(
        id=profile.id,
        nickname=profile.nickname,
        avatar_url=profile.avatar_url,
        points_balance=balance,
        post_count=counts.post_count,
        like_received_count=counts.like_received_count,
        following_count=counts.following_count,
        follower_count=counts.follower_count,
    )
