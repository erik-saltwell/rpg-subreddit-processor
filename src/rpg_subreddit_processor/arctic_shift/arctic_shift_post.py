"""Arctic Shift Reddit Post (Submission) data format.

This module defines the Pydantic model for Reddit submissions in the Arctic Shift format.
Based on the Arctic Shift specification, this represents the nodes of the Reddit graph
where communities gather to discuss topics.

Key characteristics:
- JSONL format with one post per line
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


class ArcticShiftPost(BaseModel):
    """Arctic Shift Reddit Post (Submission) model.

    Represents a Reddit submission in the Arctic Shift archive format.
    This model includes all essential fields as documented in the Arctic Shift
    specification, with optional fields for extended metadata.

    Core Identity Fields:
        - id: Local Base36 identifier
        - name: Fullname with t3_ prefix for submissions
        - author: Username (only ~2% deleted in Arctic Shift vs 23% in Pushshift)

    Temporal Fields:
        - created_utc: Immutable creation timestamp
        - retrieved_utc/retrieved_on: When the archiver captured the data

    Content Fields:
        - title: UTF-8 headline for topic modeling
        - selftext: Raw Markdown body (empty for link posts)
        - url: Destination URL (internal permalink for self-posts)
        - domain: Extracted hostname for source analysis

    Classification:
        - is_self: Text-only discussion (True) vs link aggregation (False)
        - over_18: NSFW flag
        - spoiler: Spoiler content flag
        - locked: Comments disabled by moderators
        - stickied: Pinned to subreddit top

    Note: Scores are "frozen" at retrieval time and may be systematically lower
    than Pushshift due to faster ingestion (often <36 hours after creation).
    """

    # === Core Identity ===
    id: str = Field(
        description="Local Base36 ID, unique within submissions",
    )
    name: str | None = Field(
        default=None,
        description="Fullname with t3_ prefix for submissions",
    )
    author: str = Field(
        description="Username of the post creator",
    )
    author_fullname: str | None = Field(
        default=None,
        description="Fullname of author with t2_ prefix",
    )

    # === Temporal Metadata ===
    created_utc: int = Field(
        description="Unix timestamp when user submitted the post",
    )
    retrieved_utc: int | None = Field(
        default=None,
        description="Timestamp when archiver collected this data (some dumps use this field)",
    )
    retrieved_on: int | None = Field(
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

    # === Content Payload ===
    title: str = Field(
        description="UTF-8 headline, primary field for topic modeling",
    )
    selftext: str = Field(
        default="",
        description="Raw Markdown body, empty for link posts",
    )
    url: str | None = Field(
        default=None,
        description="External link or internal Reddit permalink",
    )
    domain: str | None = Field(
        default=None,
        description="Hostname extracted from URL for source diversity analysis",
    )

    # === Engagement Metrics ===
    score: int = Field(
        description="Net votes, frozen at retrieval time (may be near zero for July-Nov 2023)",
    )
    ups: int | None = Field(
        default=None,
        description="Upvote count",
    )
    upvote_ratio: float | None = Field(
        default=None,
        description="Ratio of upvotes to total votes",
    )
    num_comments: int | None = Field(
        default=None,
        description="Number of comments at retrieval time",
    )

    # === Classification Flags ===
    is_self: bool | None = Field(
        default=None,
        description="True for text-only discussion, False for link aggregation",
    )
    over_18: bool = Field(
        default=False,
        description="NSFW content flag",
    )
    spoiler: bool = Field(
        default=False,
        description="Spoiler content requiring click-through",
    )
    locked: bool = Field(
        default=False,
        description="True if moderators disabled new comments",
    )
    stickied: bool = Field(
        default=False,
        description="True if pinned to subreddit top",
    )
    archived: bool | None = Field(
        default=None,
        description="True if post is archived (no new votes/comments)",
    )
    pinned: bool | None = Field(
        default=None,
        description="Alternative pinned flag",
    )

    # === Flair and Categorization ===
    link_flair_text: str | None = Field(
        default=None,
        description="Human-readable category tag (e.g., 'Politics', 'Meme')",
    )
    link_flair_css_class: str | None = Field(
        default=None,
        description="CSS styling class used by subreddit theme",
    )
    link_flair_richtext: list[dict[str, Any]] | None = Field(
        default=None,
        description="Rich text representation of flair",
    )
    link_flair_background_color: str | None = Field(
        default=None,
        description="Background color for flair",
    )
    link_flair_text_color: str | None = Field(
        default=None,
        description="Text color for flair",
    )
    link_flair_type: str | None = Field(
        default=None,
        description="Type of flair (text/richtext)",
    )

    # === Multimedia Metadata ===
    thumbnail: str | None = Field(
        default=None,
        description="URL to preview image (WARNING: subject to link rot)",
    )
    thumbnail_height: int | None = Field(
        default=None,
        description="Height of thumbnail in pixels",
    )
    thumbnail_width: int | None = Field(
        default=None,
        description="Width of thumbnail in pixels",
    )
    is_video: bool | None = Field(
        default=None,
        description="True for Reddit-native video uploads",
    )
    media: dict[str, Any] | None = Field(
        default=None,
        description="Nested object with media URLs (subject to link rot)",
    )
    media_embed: dict[str, Any] | None = Field(
        default=None,
        description="Embedded media metadata",
    )
    secure_media: dict[str, Any] | None = Field(
        default=None,
        description="Secure media URLs",
    )
    secure_media_embed: dict[str, Any] | None = Field(
        default=None,
        description="Secure embedded media metadata",
    )
    preview: dict[str, Any] | None = Field(
        default=None,
        description="Preview images and metadata (subject to link rot)",
    )
    media_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Full-resolution media metadata (subject to link rot)",
    )

    # === Author Metadata ===
    author_created_utc: int | None = Field(
        default=None,
        description="Unix timestamp when author account was created",
    )
    author_flair_text: str | None = Field(
        default=None,
        description="Author's flair text in this subreddit",
    )
    author_flair_css_class: str | None = Field(
        default=None,
        description="CSS class for author flair",
    )
    author_flair_richtext: list[dict[str, Any]] | None = Field(
        default=None,
        description="Rich text representation of author flair",
    )
    author_flair_background_color: str | None = Field(
        default=None,
        description="Background color for author flair",
    )
    author_flair_text_color: str | None = Field(
        default=None,
        description="Text color for author flair",
    )
    author_flair_type: str | None = Field(
        default=None,
        description="Type of author flair",
    )
    author_flair_template_id: str | None = Field(
        default=None,
        description="Template ID for author flair",
    )
    author_premium: bool | None = Field(
        default=None,
        description="True if author has Reddit Premium",
    )
    author_patreon_flair: bool | None = Field(
        default=None,
        description="True if author has Patreon flair",
    )

    # === Moderation and State ===
    distinguished: str | None = Field(
        default=None,
        description="Moderator/admin distinction (null, 'moderator', 'admin')",
    )
    edited: bool | int = Field(
        default=False,
        description="False if never edited, or Unix timestamp of last edit",
    )
    removed_by_category: str | None = Field(
        default=None,
        description="Reason for removal if post was removed",
    )
    hidden: bool | None = Field(
        default=None,
        description="True if hidden by user",
    )

    # === Awards and Gilding ===
    gilded: int | None = Field(
        default=None,
        description="Number of Reddit Gold awards",
    )
    gildings: dict[str, Any] | None = Field(
        default=None,
        description="Detailed gilding information",
    )
    total_awards_received: int | None = Field(
        default=None,
        description="Total count of all awards",
    )
    all_awardings: list[dict[str, Any]] | None = Field(
        default=None,
        description="Detailed list of all awards",
    )
    top_awarded_type: str | None = Field(
        default=None,
        description="Type of most prominent award",
    )

    # === Subreddit Metadata ===
    subreddit_subscribers: int | None = Field(
        default=None,
        description="Number of subreddit subscribers at retrieval time",
    )
    subreddit_type: str | None = Field(
        default=None,
        description="Type of subreddit (public, private, restricted, etc.)",
    )

    # === Permalink and Navigation ===
    permalink: str | None = Field(
        default=None,
        description="Relative URL path to the post",
    )

    # === Cross-posting ===
    num_crossposts: int | None = Field(
        default=None,
        description="Number of times this post was crossposted",
    )
    is_crosspostable: bool | None = Field(
        default=None,
        description="True if post can be crossposted",
    )

    # === Discussion and Chat ===
    discussion_type: str | None = Field(
        default=None,
        description="Type of discussion (e.g., 'CHAT')",
    )
    contest_mode: bool | None = Field(
        default=None,
        description="True if post is in contest mode",
    )
    suggested_sort: str | None = Field(
        default=None,
        description="Suggested comment sort order",
    )
    allow_live_comments: bool | None = Field(
        default=None,
        description="True if live comments are allowed",
    )

    # === Content Flags ===
    is_original_content: bool | None = Field(
        default=None,
        description="True if marked as original content",
    )
    is_meta: bool | None = Field(
        default=None,
        description="True if post is meta discussion",
    )
    is_reddit_media_domain: bool | None = Field(
        default=None,
        description="True if media is hosted on Reddit",
    )
    is_robot_indexable: bool | None = Field(
        default=None,
        description="True if robots can index this post",
    )
    media_only: bool | None = Field(
        default=None,
        description="True if subreddit is media-only",
    )

    # === Miscellaneous ===
    category: str | None = Field(
        default=None,
        description="Post category",
    )
    content_categories: list[str] | None = Field(
        default=None,
        description="List of content categories",
    )
    treatment_tags: list[str] | None = Field(
        default=None,
        description="Treatment tags for A/B testing",
    )
    can_gild: bool | None = Field(
        default=None,
        description="True if post can receive gilding",
    )
    send_replies: bool | None = Field(
        default=None,
        description="True if author receives reply notifications",
    )
    hide_score: bool | None = Field(
        default=None,
        description="True if score is hidden",
    )
    no_follow: bool | None = Field(
        default=None,
        description="True if links should have nofollow attribute",
    )
    quarantine: bool | None = Field(
        default=None,
        description="True if post is quarantined",
    )
    is_created_from_ads_ui: bool | None = Field(
        default=None,
        description="True if created from ads UI",
    )
    whitelist_status: str | None = Field(
        default=None,
        description="Whitelist status",
    )
    wls: int | None = Field(
        default=None,
        description="Whitelist status numeric",
    )
    parent_whitelist_status: str | None = Field(
        default=None,
        description="Parent whitelist status",
    )
    pwls: int | None = Field(
        default=None,
        description="Parent whitelist status numeric",
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
