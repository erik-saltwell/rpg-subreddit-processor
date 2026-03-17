"""Arctic Shift Reddit Comment data format.

This module defines the Pydantic model for Reddit comments in the Arctic Shift format.
Based on the Arctic Shift specification, this represents the nodes in the Reddit graph
where conversations unfold.

Key characteristics:
- JSONL format with one comment per line
- Fields sorted alphabetically
- UTF-8 encoding for international content
- Temporal data includes both creation time and retrieval time
"""

from typing import Any

from pydantic import BaseModel, Field


class ArcticShiftMeta(BaseModel):
    """Metadata about the archival process.

    This object provides provenance information about when and how
    the data was retrieved by the Arctic Shift archiver.
    """

    retrieved_2nd_on: int | None = Field(
        default=None,
        description="Secondary retrieval timestamp, used to distinguish original ingestion from updates",
    )


class ArcticShiftComment(BaseModel):
    """Arctic Shift Reddit Comment model.

    Represents a Reddit comment in the Arctic Shift archive format.
    This model includes all essential fields as documented in the Arctic Shift
    specification, with optional fields for extended metadata.
    """

    # === Core Identity ===
    author: str = Field(
        description="Username of the comment author",
    )
    author_flair_css_class: str | None = Field(
        description="Author flair CSS class",
    )
    author_flair_text: str | None = Field(
        description="Author flair text",
    )
    id: str = Field(
        description="Local Base36 ID, unique within comments",
    )
    name: str = Field(
        description="Fullname with t1_ prefix for comments",
    )

    # === Temporal Metadata ===
    created: int | None = Field(
        default=None,
        description="Unix timestamp for comment creation (legacy field)",
    )
    created_utc: int = Field(
        description="Unix timestamp when user submitted the comment",
    )
    retrieved_on: int | None = Field(
        default=None,
        description="Timestamp when archiver collected this data (some dumps use this field)",
    )
    retrieved_utc: int | None = Field(
        default=None,
        description="Timestamp when archiver collected this data (some dumps use this field)",
    )

    # === Subreddit Context ===
    subreddit: str = Field(
        description="Name of the community (e.g., AskReddit)",
    )
    subreddit_id: str = Field(
        description="Unique subreddit ID with t5_ prefix",
    )
    subreddit_name_prefixed: str | None = Field(
        default=None,
        description="Subreddit name prefixed with r/",
    )
    subreddit_type: str | None = Field(
        default=None,
        description="Subreddit type (public, restricted, private)",
    )

    # === Comment Threading ===
    link_id: str = Field(
        description="Fullname of the linked post (t3_ prefix)",
    )
    parent_id: str = Field(
        description="Fullname of the parent thing (t1_ or t3_ prefix)",
    )
    nest_level: int | None = Field(
        default=None,
        description="Depth of the comment in the thread",
    )
    replies: str | None = Field(
        default=None,
        description="Replies placeholder (often empty string)",
    )

    # === Content Payload ===
    body: str = Field(
        description="Raw Markdown comment text",
    )
    body_html: str | None = Field(
        default=None,
        description="HTML-rendered comment body",
    )
    body_sha1: str | None = Field(
        default=None,
        description="SHA1 hash of the comment body",
    )
    media_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Media metadata for embeds",
    )
    permalink: str = Field(
        description="Permalink path for the comment",
    )

    # === Engagement Metrics ===
    controversiality: int = Field(
        description="Controversiality score",
    )
    downs: int | None = Field(
        default=None,
        description="Downvote count",
    )
    score: int = Field(
        description="Score at retrieval time",
    )
    score_hidden: bool | None = Field(
        default=None,
        description="True if score is hidden",
    )
    ups: int = Field(
        description="Upvote count",
    )

    # === Moderation & Flags ===
    approved_at_utc: int | None = Field(
        default=None,
        description="Timestamp when approved by moderators",
    )
    approved_by: str | None = Field(
        default=None,
        description="Moderator username who approved the comment",
    )
    archived: bool | None = Field(
        default=None,
        description="True if comment is archived",
    )
    banned_at_utc: int | None = Field(
        default=None,
        description="Timestamp when comment was removed",
    )
    banned_by: str | None = Field(
        default=None,
        description="Moderator username who removed the comment",
    )
    can_gild: bool | None = Field(
        default=None,
        description="True if comment can be gilded",
    )
    can_mod_post: bool | None = Field(
        default=None,
        description="True if user can moderate the post",
    )
    collapsed: bool | None = Field(
        default=None,
        description="True if comment is collapsed",
    )
    collapsed_because_crowd_control: bool | None = Field(
        default=None,
        description="True if collapsed due to crowd control",
    )
    collapsed_reason: str | None = Field(
        default=None,
        description="Reason for comment collapse",
    )
    collapsed_reason_code: str | None = Field(
        default=None,
        description="Machine-readable collapse reason",
    )
    comment_type: str | None = Field(
        default=None,
        description="Comment type indicator",
    )
    distinguished: str | None = Field(
        description="Moderator/admin distinction",
    )
    editable: bool | None = Field(
        default=None,
        description="True if comment is editable",
    )
    edited: bool | int = Field(
        description="Edited flag or edit timestamp",
    )
    gilded: int = Field(
        description="Gild count",
    )
    is_submitter: bool | None = Field(
        default=None,
        description="True if author is the post submitter",
    )
    locked: bool | None = Field(
        default=None,
        description="True if comment is locked",
    )
    mod_note: str | None = Field(
        default=None,
        description="Moderator note",
    )
    mod_reason_by: str | None = Field(
        default=None,
        description="Moderator username who provided the removal reason",
    )
    mod_reason_title: str | None = Field(
        default=None,
        description="Moderator-provided removal reason title",
    )
    mod_reports: list[Any] | None = Field(
        default=None,
        description="Moderator reports",
    )
    no_follow: bool | None = Field(
        default=None,
        description="True if links are marked nofollow",
    )
    num_reports: int | None = Field(
        default=None,
        description="Number of reports",
    )
    quarantined: bool | None = Field(
        default=None,
        description="True if comment is quarantined",
    )
    removal_reason: str | None = Field(
        default=None,
        description="Removal reason text",
    )
    report_reasons: list[Any] | None = Field(
        default=None,
        description="User report reasons",
    )
    rte_mode: str | None = Field(
        default=None,
        description="Rich text editor mode",
    )
    saved: bool | None = Field(
        default=None,
        description="True if comment is saved by the user",
    )
    send_replies: bool | None = Field(
        default=None,
        description="True if replies are sent to inbox",
    )
    steward_reports: list[Any] | None = Field(
        default=None,
        description="Steward reports",
    )
    stickied: bool = Field(
        default=False,
        description="True if comment is stickied",
    )
    user_reports: list[Any] | None = Field(
        default=None,
        description="User reports",
    )

    # === Awards ===
    all_awardings: list[dict[str, Any]] | None = Field(
        default=None,
        description="Awarding metadata",
    )
    associated_award: dict[str, Any] | None = Field(
        default=None,
        description="Associated award metadata",
    )
    awarders: list[Any] | None = Field(
        default=None,
        description="Awarder user IDs",
    )
    gildings: dict[str, Any] | None = Field(
        default=None,
        description="Gilding breakdown",
    )
    top_awarded_type: str | None = Field(
        default=None,
        description="Top award type",
    )
    total_awards_received: int | None = Field(
        default=None,
        description="Total awards received",
    )

    # === Author Metadata ===
    author_cakeday: bool | None = Field(
        default=None,
        description="True if comment was posted on the author's cake day",
    )
    author_created_utc: int | None = Field(
        default=None,
        description="Author account creation timestamp",
    )
    author_flair_background_color: str | None = Field(
        default=None,
        description="Author flair background color",
    )
    author_flair_richtext: list[dict[str, Any]] | None = Field(
        default=None,
        description="Author flair richtext",
    )
    author_flair_template_id: str | None = Field(
        default=None,
        description="Author flair template ID",
    )
    author_flair_text_color: str | None = Field(
        default=None,
        description="Author flair text color",
    )
    author_flair_type: str | None = Field(
        default=None,
        description="Author flair type",
    )
    author_fullname: str | None = Field(
        default=None,
        description="Fullname of author with t2_ prefix",
    )
    author_is_blocked: bool | None = Field(
        default=None,
        description="True if author is blocked",
    )
    author_patreon_flair: bool | None = Field(
        default=None,
        description="True if author has Patreon flair",
    )
    author_premium: bool | None = Field(
        default=None,
        description="True if author has Reddit Premium",
    )

    # === Misc ===
    likes: bool | None = Field(
        default=None,
        description="Like state for the authenticated user",
    )
    treatment_tags: list[Any] | None = Field(
        default=None,
        description="Treatment tags",
    )
    unrepliable_reason: str | None = Field(
        default=None,
        description="Reason the comment is unrepliable",
    )

    # === Arctic Shift Metadata ===
    meta: ArcticShiftMeta | None = Field(
        default=None,
        alias="_meta",
        description="Arctic Shift archival metadata",
    )

    model_config = {
        "populate_by_name": True,  # Allow both field name and alias
    }
